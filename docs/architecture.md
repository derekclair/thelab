# Architecture Overview

The system is deliberately layered so that the "brain" can evolve independently of the voice hardware and the deployment target (Mac dev vs DGX Spark personal desktop).

How this brain is dispatched on the workstation (role-split fleet, spec-first
gate, one-local-LLM budget) lives in Hermes, not here:
`~/.hermes/docs/agentic-workflow.md`. This document is the software layering
of the LangGraph package itself.

## High-Level Layers

```
User (voice or text)
      │
      ├── conversational-voice-agent (live): Parakeet STT + Piper TTS + USB I/O
      │         │
      │         ▼
      └── thelab_langchain.agent (this repo)
                │  memory_injection → LLM (+ optional memory tools)
                ├── Supermemory (long-term, user-scoped)
                └── LLM: Grok / Claude / local OpenAI-compatible (NIM or Ollama)
```

`thelab_langchain.voice` is an older Riva-oriented spike in this tree.
Streaming recognize / barge-in there still raise `NotImplementedError`.

## Key Components

- **`thelab_langchain.agent`** — LangGraph graph, Supermemory tools, state, LLM factory.
- **`thelab_langchain.llm`** — Returns the chat model from `LLM_PROVIDER`.
- **`thelab_langchain.chat`** — Simpler non-graph MemoryChat loop for the CLI.
- **Supermemory** — Long-term memory (profile + semantic search), scoped per user via `container_tag`.
- **Live voice I/O** — [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent), not the Riva module in this repo.
- **Local NIM / Ollama** — Optional OpenAI-compatible brain on the Spark.

## Multi-User Considerations

See `specs/002-multi-user-support/spec.md`. The architecture was designed with per-user `container_tag` (Supermemory) and per-user `thread_id` (LangGraph) from the beginning.

## Deployment Model

- **Development**: local `.venv` (`make install` / `make chat`).
- **Spoken desktop**: sibling `conversational-voice-agent` editable-installs this package.
- **Compose in this repo**: experimental `agent` + `riva` + `nemotron`. Not the live voice path.

See `specs/003-deployment-infrastructure/spec.md` for current gaps and target state.

## Persistence

- **Long-term**: Supermemory (cloud, user-scoped).
- **Short-term / Conversation**: LangGraph checkpointer (planned — see `specs/004-persistence-checkpointers/spec.md`). Currently in-memory only.

## Extensibility

- New tools → add in `agent/tools/`, expose via factory, wire into graph.
- New memory backends → implement the same tool interface or extend the injection node.
- New LLM providers → extend `config.py` + `llm.py` (must be OpenAI-compatible or have a LangChain integration).

## Where to Start Exploring the Code

1. `src/thelab_langchain/agent/graph.py` — the brain (memory injection + LLM + tools)
2. `src/thelab_langchain/agent/tools/memory.py` — Supermemory tools
3. `src/thelab_langchain/llm.py` — provider factory
4. `src/thelab_langchain/cli.py` — text chat entry point
5. `specs/README.md` — design trail
