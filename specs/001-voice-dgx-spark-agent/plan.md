# Technical Plan: Voice-Enabled Agent for NVIDIA DGX Spark (001)

**Feature**: 001-voice-dgx-spark-agent  
**Related Spec**: [spec.md](./spec.md)  
**Date**: 2025-05-21

## 1. Architecture Overview

We will build a **layered voice agent** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    User (Voice)                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ Audio (mic/speaker)
┌───────────────────────▼─────────────────────────────────────┐
│  Voice Layer (NVIDIA NeMo + Riva)                           │
│  - Streaming ASR (STT)                                      │
│  - Streaming TTS                                            │
│  - VAD + Barge-in handling                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ Text (transcribed utterance)
┌───────────────────────▼─────────────────────────────────────┐
│  Orchestration Layer (Python)                               │
│  - Conversation Manager / Turn Manager                      │
│  - Interruption handling                                    │
│  - Audio ↔ Text bridging                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ Structured input + context
┌───────────────────────▼─────────────────────────────────────┐
│  Agent Brain (LangGraph)                                    │
│  - StateGraph with memory tools                             │
│  - Supermemory (long-term) + short-term conversation state  │
│  - Tool calling (memory + future tools)                     │
│  - LLM: Grok (default) or local model                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ Tool calls / final response
                        ▼
                Supermemory + Other Tools
```

**Key Principle**: The voice layer is "dumb but fast". The LangGraph agent is the intelligent brain that decides *what* to say and *when* to use memory/tools.

**Parallel lightweight spike (2026-06-12)**: Specified in [008](../008-local-tts-lenovo-go-spike/plan.md); implemented in [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent). ALSA + Parakeet CPU + Piper + HID LED; brain is `get_agent()`. Not `riva.client` as the live ASR. Uncommitted to this plan's Riva/NIM primary path.

**Serving Flexibility**: The LLM serving layer must be swappable. For v1, the target implementation uses the official NVIDIA NIM container (`nemotron-3-super-120b-a12b`) exposing an OpenAI-compatible endpoint at `http://localhost:8000/v1`. The agent is intended to use the existing `openai_compatible` provider for this deployment path. Future phases target clustered multi-node serving for full 340b-class models without changing the voice or agent code.

**Target v1 Stack (Single-Node Desktop)**:
- **LLM**: Local ~30B Nemotron class via the `local-tts` / NeuTTS service (or NIM container for the 30B variant). Agent uses `openai_compatible` provider for the local endpoint. Grok fallback via xAI.
- Agent: LangGraph + Supermemory, configured to talk via `openai_compatible` for the NIM-based target deployment
- Voice: NVIDIA Riva / NeMo (ASR + TTS) via the existing VoiceOrchestrator

## 2. Component Breakdown

### 2.1 Voice Layer – NVIDIA NeMo / Riva

**Recommended Stack**:
- **ASR (STT)**: NVIDIA NeMo Conformer or FastConformer (streaming) exported to TensorRT, served via **Riva ASR**.
- **TTS**: NVIDIA NeMo FastPitch + HiFi-GAN or RadTTS, served via **Riva TTS**.
- **Inference Server**: NVIDIA Riva (production-grade, gRPC + HTTP, excellent streaming support, optimized for DGX).
- **Alternative (lighter)**: Direct NeMo inference with TensorRT-LLM export if Riva overhead is undesirable for single-user setups.

**Why Riva?**
- Best latency and concurrency characteristics on DGX Spark.
- Built-in support for word timestamps, confidence scores, and end-of-utterance detection.
- Official NVIDIA support and containers for DGX-class systems.

**Integration Point**:
- The Python side will use the official `nvidia-riva-client` Python package (gRPC).
- We will implement an async audio streaming bridge.

### 2.2 Orchestration Layer

A new module `thelab_langchain.voice` (or `agent.voice`) responsible for:

- Managing microphone input + speaker output (using `sounddevice` or `pyaudio`).
- Running Riva ASR in streaming mode and emitting final transcripts.
- Receiving text from the agent and feeding it to Riva TTS (with support for streaming synthesis).
- Handling barge-in (user speaking while TTS is playing → cancel current synthesis + notify agent).
- Turn management and simple VAD.

This layer should feel like a "voice shell" around the existing agent.

### 2.3 Agent Brain (LangGraph)

We will evolve the current scaffolding in `src/thelab_langchain/agent/`:

- Use a **custom StateGraph** (preferred over pure `create_react_agent` for better control over memory injection and voice-specific behaviors).
- Core nodes:
  - `memory_injection` (pull relevant Supermemory context)
  - `think` (LLM with tools bound)
  - `act` (execute tools)
  - `respond` (generate final utterance text)
- Tools will include the Supermemory tools we already started (`recall_memories`, `store_memory`, `get_user_profile`).
- The graph will be callable from the orchestration layer with a `user_id` + `thread_id`.

**Important Design Decision**:
For voice, we want the agent to be able to produce **incremental / streaming text** so TTS can start early. This favors architectures where the LLM response is generated in chunks.

### 2.3.1 Memory Integration Approach (Current Iteration)

For the initial wiring of Supermemory:

- Tools are created via `create_memory_tools(user_id)` factory (see `agent/tools/memory.py`) so they are properly scoped. This replaces the earlier global `_current_user_id` pattern.
- A `memory_injection` node will run early in the graph. It will:
  - Call `get_user_profile(user_id)` to pull static facts + dynamic context.
  - Call `recall_memories(query=last_user_utterance)` to surface the most relevant past memories.
  - Inject the combined context into the system prompt or as a preceding message before the LLM step.
- In a follow-up pass, the three tools will be bound to the LLM via `.bind_tools()`, allowing the agent to proactively decide to call `store_memory(...)` or perform deeper recall.
- The `VoiceOrchestrator` will be responsible for creating the user-scoped tools and (later) passing them when constructing or invoking the graph.

This two-phase approach (proactive injection first, reactive tool use second) gives immediate value while keeping the graph simple.

**Current micro-iteration goals (both requested):**
- Improve the quality and conciseness of the injected memory context (better formatting + optional LLM summarization of retrieved memories).
- Begin binding the Supermemory tools to the LLM so the agent can call `store_memory`, `recall_memories`, or `get_user_profile` reactively when it decides it needs to.

### 2.4 Memory Strategy

- **Long-term**: Supermemory (via tools) — facts, preferences, project history, past conversations.
- **Short-term / Session**: LangGraph checkpointer (`MemorySaver` initially, later Postgres or Redis).
- The voice orchestration layer will pass the current `thread_id` on every turn.

## 3. Packaging & Deployment (DGX Spark)

### 3.1 Development & Deployment Workflow (Mac → DGX)

**Primary flow** (as requested):

1. **Develop locally** on Mac (this host).
2. **Dockerize** the application.
3. Build/push the image (or build directly on DGX).
4. On the DGX: `docker compose pull` (or build) → `docker compose up`.
5. Observe / interact with the running voice agent.

This keeps the Mac as the fast development environment while the heavy GPU workloads (Riva + Nemotron inference) run on the DGX Spark.

### 3.2 Docker Compose Architecture

We will use a **multi-service `docker-compose.yml`** as the canonical way to run on DGX Spark. The stack will include at minimum:

```yaml
services:
  agent:           # Our Python LangGraph + Supermemory voice agent
    build: .
    # ... GPU access, env vars, volumes ...

  riva:            # NVIDIA Riva (ASR + TTS)
    image: nvcr.io/nvidia/riva/riva-speech:...
    # ... GPU, ports 50051 (gRPC), model volumes ...

  nemotron:        # Local LLM brain (Nemotron NIM or vLLM)
    image: nvcr.io/nim/nvidia/nemotron-...   # or custom TRT-LLM engine
    # Exposes OpenAI-compatible endpoint (so agent can use ChatOpenAI(base_url=...))
    # GPU resources allocated here
```

**Service Responsibilities**:
- **agent**: Runs our `thelab-langchain` code. Talks to:
  - Riva (gRPC) for voice I/O
  - Nemotron (HTTP, OpenAI-compatible) or Grok (via XAI) for reasoning
  - Supermemory (cloud or future local)
- **riva**: Official NVIDIA Riva container(s) providing ASR and TTS.
- **nemotron**: NVIDIA NIM (or vLLM/TensorRT-LLM) serving a Nemotron model locally. This allows the agent to run fully on-DGX with no cloud LLM calls.

The agent service will support runtime switching of the LLM backend via environment variables (e.g. `LLM_PROVIDER=grok` vs `LLM_PROVIDER=nemotron`).

### 3.3 GPU & Resource Allocation on DGX Spark

- Use `deploy.resources.reservations.devices` (or the older `runtime: nvidia`) to give containers access to the GPUs.
- Riva and Nemotron are both GPU-heavy; careful partitioning will be needed.
- The agent service itself is mostly CPU + light GPU usage (for any local post-processing).

### 3.4 Model & Data Management

- Large model artifacts (Riva models, Nemotron weights/engines) will live on named Docker volumes or host bind mounts (`/models`, `/data`).
- First-run download scripts or `docker compose run --rm model-downloader` targets.

### 3.5 Observability Note

Full production observability (Prometheus, Grafana, tracing, log aggregation) is deferred for now, as noted by the user. We will focus on basic structured logging and health endpoints initially.

## 4. Implementation Phases

**Phase 0** (Current spike)
- LangGraph + Supermemory tools foundation (already in progress on `langchain` branch)

**Phase 1** – Core Voice Loop (MVP)
- Riva ASR + TTS integration (non-streaming first)
- Basic orchestration layer that can do: Listen → Transcribe → Agent → Synthesize → Speak
- CLI command: `thelab-chat voice`

**Phase 2** – Streaming & Polish
- True streaming ASR + streaming TTS
- Barge-in support
- Better turn management and VAD
- Latency tuning on DGX Spark

**Phase 3** – Productionization
- Docker + docker-compose optimized for DGX Spark
- Model caching and download scripts
- Health checks, logging, observability
- Optional local LLM backend (via vLLM + TensorRT-LLM)

**Phase 4** (Future)
- Wake word
- Multi-speaker / voice cloning
- Full offline mode (local LLM + Supermemory local alternative if needed)

## 5. Key Technical Risks & Mitigations

| Risk                              | Mitigation |
|-----------------------------------|----------|
| High latency on voice round-trip  | Prioritize streaming ASR + TTS from day one in Phase 2 |
| Riva complexity / container size  | Provide both "full Riva" and "light NeMo" paths |
| Barge-in is hard                  | Use Riva's streaming endpoints + audio cancellation logic |
| GPU memory contention             | Clear documentation + resource limits in compose file |
| Model download time on first run  | Pre-download scripts + volume mounts |

## 6. Interface Changes

- New CLI entry: `thelab-chat voice --user derek --thread daily-standup`
- The existing text `thelab-chat chat` remains unchanged (great for debugging the brain without audio).
- The `MemoryChat` simple class can stay as a reference implementation.

## 7. Success Metrics (Technical)

- End-to-end voice latency (speech end → first audio out) < 2.5s on DGX Spark for normal queries.
- Accurate transcription of technical speech (thelab domain).
- Natural-sounding TTS that users actually enjoy listening to for long responses.
- Agent correctly uses long-term memory in voice conversations.

## 8. Open Decisions to Resolve in Tasks

- Exact NeMo model variants to start with (e.g., `stt_en_fastconformer_hybrid_large_streaming` + specific TTS voice).
- Whether to run full Riva server as a separate compose service or embed inference in the agent container.
- How much of the voice logic lives in pure Python vs calling into Riva SDK.

---

**Next**: Generate `tasks.md` with dependency-ordered, actionable work items. Then begin implementation on the `langchain` branch.