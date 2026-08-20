# Architecture Overview

The system is deliberately layered so that the "brain" can evolve independently of the voice hardware and the deployment target (Mac dev vs DGX Spark personal desktop, with a clear future path to multi-node DGX Spark clusters for 340b-class models).

The personal workstation around this package is a **role-split agent fleet**
(orchestrator, architect, researcher, coder, reviewer) with a spec-first
gate and a one-local-LLM budget on the DGX Spark. That operating design is
[`specs/008-workstation-agent-fleet/spec.md`](../specs/008-workstation-agent-fleet/spec.md).
This document is the software layering of the LangGraph brain itself.

## High-Level Layers

```
User (Voice)
      │
      ▼
Voice Layer (Riva / NeMo ASR + TTS)
      │  (audio in → transcript, text out → audio)
      ▼
Orchestration Layer (VoiceOrchestrator)
      │  (turn management, barge-in, audio bridging)
      ▼
Agent Brain (LangGraph)
      │  (memory_injection + LLM with tools)
      │
      ├── Supermemory (long-term, user-scoped)
      ├── Configured LLM (Grok via XAI or Nemotron NIM locally)
      └── Future tools
```

## Key Components

- **`thelab_langchain.voice`** — Audio I/O + Riva client wrappers + turn management.
- **`thelab_langchain.agent`** — LangGraph graph, tools (currently Supermemory), state, and LLM factory.
- **`thelab_langchain.llm`** — Single place that returns the right chat model based on `LLM_PROVIDER`.
- **Supermemory** — Long-term memory store (profile + semantic search). Scoped per user via `container_tag`.
- **Riva** — NVIDIA's production ASR/TTS service (runs as separate container on DGX).
- **Nemotron** — Local LLM brain via NVIDIA NIM (OpenAI-compatible). Swappable at runtime with Grok.

## Multi-User Considerations

See `specs/002-multi-user-support/spec.md`. The architecture was designed with per-user `container_tag` (Supermemory) and per-user `thread_id` (LangGraph) from the beginning.

## Deployment Model

- **Development**: Mac + local `.venv` (or Docker with host networking).
- **Production / Voice**: Full Docker Compose stack on DGX Spark (`agent` + `riva` + `nemotron`).
- Images are built on the dev machine (or CI) and pushed to a private registry, then pulled on the DGX.

See `specs/003-deployment-infrastructure/spec.md` for current gaps and target state.

## Persistence

- **Long-term**: Supermemory (cloud, user-scoped).
- **Short-term / Conversation**: LangGraph checkpointer (planned — see `specs/004-persistence-checkpointers/spec.md`). Currently in-memory only.

## Extensibility

- New tools → add in `agent/tools/`, expose via factory, wire into graph.
- New memory backends → implement the same tool interface or extend the injection node.
- New LLM providers → extend `config.py` + `llm.py` (must be OpenAI-compatible or have a LangChain integration).

## Where to Start Exploring the Code

1. `src/thelab_langchain/cli.py` — entry points (`chat`, `voice`, etc.)
2. `src/thelab_langchain/voice/orchestrator.py` — how voice turns become agent calls
3. `src/thelab_langchain/agent/graph.py` — the current brain (memory injection + LLM + tools)
4. `src/thelab_langchain/agent/tools/memory.py` — how we talk to Supermemory
5. `docker-compose.yml` + `Dockerfile` — how everything runs on DGX
