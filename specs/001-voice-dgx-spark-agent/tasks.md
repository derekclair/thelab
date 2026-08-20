# Tasks: Voice-Enabled Agent for NVIDIA DGX Spark (001)

**Feature**: 001-voice-dgx-spark-agent  
|**Status**: Phase 2 implementation in progress (core wiring + local-tts 30B NeuTTS service + nv-monitor observability) 
**Branch**: `spec/001-dgx-spark-voice-desktop-scaling` (implementation + docs evolution on the Phase 2 spec branch)

This document breaks the plan into dependency-ordered, actionable tasks. Each task should be small enough to be completed in one focused session.

---

## Phase 0 – Foundations (Current)

- [x] Commit existing LangGraph + Supermemory tools scaffolding (`src/thelab_langchain/agent/`)
- [x] Create SDD artifacts (`spec.md`, `plan.md`, `tasks.md`)

## Parallel Track A – Local High-Quality LLM + Voice on Single-Node DGX Spark Desktop

**Goal**: Get a reliable, high-quality local ~30B Nemotron running on the desktop DGX Spark with full voice support via the dedicated `local-tts` NeuTTS service, while cleaning up previous experimental paths. The `local-tts` service is the canonical TTS provider exposed to the stack.

**Current Status (as of 2026-06-12)**: Core agent + openai_compatible wiring + lazy voice imports complete and committed. `local-tts` 30B NeuTTS service initialized in dedicated repo with proper hygiene. nv-monitor observability tool integrated. Compose defaults to local-tts service.

The Lenovo Go spike checklist is [008/tasks.md](../008-local-tts-lenovo-go-spike/tasks.md). Code: [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent). Live ASR is Parakeet via NeMo on CPU, not `riva.client`.

Riva compatibility on current hardware and full production voice loop (telephony / main orchestrator) remain future items.

### T2.1 – Local LLM Serving (NVIDIA NIM)
- [x] Document and stabilize running the official NIM container (`nemotron-3-super-120b-a12b`) on DGX Spark (direct `docker run` + compose service defaulting to 120b image)
- [x] Decide on long-term approach (Docker Model Runner abandoned for 120b+; direct NIM container is the path for v1 single-node desktop)
- [ ] Add convenience scripts or Makefile targets for starting/stopping the local NIM (future polish)

### T2.2 – Agent Wiring to Local Endpoint
- [x] Make the agent (`MemoryChat` + CLI) cleanly support `openai_compatible` pointing at the local NIM (localhost:8000) via centralized `get_chat_model()` factory
- [x] Add sensible defaults / environment variable helpers for DGX Spark desktop use (.env.example block + compose defaults to 120b image + /opt/nim/.cache volume)
- [x] Update `thelab-chat env` / welcome screen to clearly show when using local model (Base URL display + openai_compatible warning)
- [ ] Ensure Supermemory + tool use works end-to-end with the local 120b model (pending full model load + test)

### TA.3 – Voice + Local LLM Integration
- [ ] Verify / fix the `voice` command so it uses the same LLM path as `chat`
- [ ] Test full voice loop (ASR → agent with local LLM → TTS) on the desktop
- [ ] Handle cases where local LLM is slower (streaming, barge-in implications)

### TA.4 – Cleanup & Code Health
- [ ] Reduce or remove reliance on the broken Docker Model Runner path for the main model
- [ ] Clean up related documentation, compose files, and old scripts
- [ ] Ensure all code changes are clean, well-tested where possible, and follow project conventions

**Spike Track – moved to spec 008.** Do not treat the checkboxes below as the live ASR story (`riva.client` was an early note; Parakeet CPU shipped). Canonical list: [008/tasks.md](../008-local-tts-lenovo-go-spike/tasks.md).

**Spike Track (historical 2026-06-12 notes, superseded by 008)**:
- [x] Teams button light feedback implemented (led_control.py + integration in voice_loop; light stays active while session runs).
- [x] Real streaming NeMo ASR integrated using riva.client (replaced mock; partial transcripts flow in real time from first chunk).
- [x] Agent callback wiring: partial results sent to `send_partial_to_agent()` as soon as they arrive.
- [x] Named pipe trigger + 4 s window + LED during sessions (already working at spike start).
- [x] Implement bidirectional reply path (`speak(text)` using same riva.client style + `/tmp/voice_speak` pipe + daemon) with tone fallback.
- [x] Wire physical Teams button (evdev) to write "start" to the (locked) `/tmp/voice_trigger` pipe.
- [x] E2E test: named pipe (or button) + streaming STT (live partials) + agent seam + playback on the Lenovo Go speaker (with mock or real existing agent reply).
- [x] Update local-tts README + create focused `specs/001-interim-lenovo-go-voice-spike.md`.
- [x] Light sync note + status update + spike track checkboxes in thelab 001 (this file + spec.md + plan.md), emphasizing reuse of existing Supermemory-enabled agent.

**Future Phase – Hardware Scaling (Post v1)**: Once the voice + agent harness is solid on a single DGX Spark desktop, add support for multi-node clustered inference to run full Nemotron 4 340b-class models while keeping the identical user experience. This will likely become its own follow-on spec (e.g. 007-multi-dgx-inference) that depends on 001.

---

## Phase 1 – Core Voice Loop (MVP)

### T1.1 – Project Structure & Dependencies
- [ ] Add new dependencies: `nvidia-riva-client`, `sounddevice`, `numpy`, `webrtcvad` or equivalent VAD
- [ ] Create `src/thelab_langchain/voice/` package
- [ ] Create `src/thelab_langchain/agent/graph.py` (initial StateGraph skeleton)
- [ ] Update `pyproject.toml` and `Makefile` as needed

### T1.2 – Riva Client Wrapper
- [ ] Implement a clean async wrapper around `riva.client.ASRService` for streaming transcription
- [ ] Implement a clean async wrapper around `riva.client.TTSService` (initially non-streaming)
- [ ] Add configuration for Riva server address / port / SSL (even if running locally in same compose)

### T1.3 – Basic Audio I/O
- [ ] Create microphone input loop using `sounddevice`
- [ ] Create speaker output using `sounddevice`
- [ ] Implement simple VAD to detect end of user utterance

### T1.4 – Minimal Voice Orchestrator
- [ ] Build `VoiceOrchestrator` class that can:
  - Listen until end of speech
  - Get transcript from Riva ASR
  - Send text to the LangGraph agent
  - Receive response text
  - Synthesize with Riva TTS and play audio
- [ ] Wire it to the existing `MemoryChat` or new graph as a first integration test

### T1.5 – CLI Voice Command
- [ ] Add `thelab-chat voice` subcommand (using Typer)
- [ ] Support `--user` and `--thread` flags
- [ ] Basic error handling and fallback to text mode if audio devices fail

---

## Phase 2 – Streaming & Natural Conversation

### T2.1 – Streaming ASR
- [ ] Switch ASR integration to true streaming mode (incremental transcripts + final)
- [ ] Implement partial transcript handling (optional: show live transcription)

### T2.2 – Streaming TTS + Early Audio
- [ ] Upgrade TTS to streaming synthesis (Riva supports chunked audio)
- [ ] Start playing audio as soon as first TTS chunks arrive (reduces perceived latency)

### T2.3 – Barge-in Support
- [ ] Detect user speech while TTS is playing
- [ ] Cancel current TTS synthesis
- [ ] Notify the agent that the previous response was interrupted
- [ ] Allow the agent to react appropriately ("Sorry, what were you saying?" or just listen)

### T2.4 – Improved Turn Management
- [ ] Robust state machine for conversation turns (Listening / Thinking / Speaking / Interrupted)
- [ ] Better handling of overlapping speech

---

## Phase 3 – Packaging & DGX Spark Deployment

### T3.1 – Docker Compose Stack (Mac → DGX Workflow)
- [ ] Create `Dockerfile` for the `agent` service (Python + our code + Riva client)
- [ ] Create root `docker-compose.yml` with at least three services:
  - `agent` (our voice + LangGraph app)
  - `riva` (official NVIDIA Riva container)
  - `nemotron` (NVIDIA NIM or vLLM serving Nemotron model, OpenAI-compatible)
- [ ] Support `docker compose --profile full-riva` or similar for different deployment sizes
- [ ] Add `.env.example` with all required variables for the compose stack (including `NEMOTRON_BASE_URL`, `RIVA_URI`, etc.)
- [ ] Document the "Develop on Mac → docker build/push → pull & `docker compose up` on DGX" workflow

### T3.2 – Nemotron Integration (Local LLM Brain)
- [ ] Make the agent able to use a local Nemotron NIM as drop-in replacement for Grok
  - Use `langchain-openai.ChatOpenAI` with custom `base_url` + `api_key`
- [ ] Add environment variable switching (`LLM_PROVIDER=nemotron` vs `grok`)
- [ ] Document recommended Nemotron models for DGX Spark (size vs quality tradeoffs)
- [ ] Create a small health-check / smoke test that the Nemotron endpoint is reachable from the agent service

### T3.3 – Riva as Separate Service
- [ ] Wire the agent container to talk to the `riva` service over the Docker network (usually `riva:50051`)
- [ ] Provide volume strategy for Riva model cache
- [ ] Document how to start just Riva for development/testing

### T3.4 – DGX Spark Documentation & Tooling
- [ ] Write `docs/dgx-spark-deployment.md`
- [ ] Cover: NVIDIA Container Toolkit, GPU device requests in compose, running alongside other workloads, SSH access patterns (`ssh dgx`)
- [ ] Add helper scripts (e.g. `scripts/push-to-dgx.sh` or instructions using `docker buildx` / registry)

### T3.3 – DGX Spark Documentation
- [ ] Write `docs/dgx-spark-deployment.md`
- [ ] Cover: NVIDIA Container Toolkit, GPU visibility, performance tuning, running alongside other workloads

### T3.4 – Health & Observability
- [ ] Add health endpoints (FastAPI or simple HTTP) for the agent
- [ ] Structured logging for voice pipeline latency (STT time, agent time, TTS time)
- [ ] Graceful degradation when voice hardware is unavailable

---

## Phase 4 – Agent Brain Evolution

### T4.1 – Proper LangGraph Agent
- [ ] Replace simple `MemoryChat` usage with a real `StateGraph`
- [ ] Implement memory injection node that calls Supermemory tools before thinking
- [ ] Bind the memory tools to the LLM
- [ ] Support `thread_id` + `checkpointer`

### T4.2 – Voice-Aware Behaviors
- [ ] Add special instructions / system prompt variations for voice (shorter responses, more conversational tone)
- [ ] Handle "interrupted" signals from the orchestration layer inside the graph

### T4.3 – Tool Surface Expansion (optional but recommended)
- [ ] At minimum keep the three Supermemory tools solid
- [ ] Consider adding a simple "clarify" tool or confirmation pattern for voice

---

## Cross-Cutting / Polish Tasks

- [ ] Comprehensive error handling and user-friendly messages in voice mode
- [ ] Configuration system for choosing between Riva and direct NeMo
- [ ] Unit + integration tests for the voice layer (mocked Riva)
- [ ] Update main README with voice capabilities and DGX Spark section
- [ ] Performance profiling run on actual DGX Spark hardware (latency numbers)

---

## Suggested Order of Implementation

1. **T1.1 → T1.4** (Get something that can talk and listen, even if clunky)
2. **T1.5** (Make it usable via CLI)
3. **T2.1 – T2.4** (Make it feel natural – this is where the magic happens)
4. **T4.1 – T4.2** (Upgrade the brain to a real graph while doing voice work)
5. **T3.1 – T3.4** (Packaging – do this once the core loop is stable)
6. Polish + documentation

---

**Ready to start?** The first concrete task is usually **T1.1 – Project Structure & Dependencies**.

Let me know when you want to begin implementation (I can start with T1.1 right now if desired).
