# Feature Spec: Persistence & Checkpointers

**Feature ID**: 004-persistence-checkpointers  
**Status**: Draft  
**Related**: 001-voice-dgx-spark-agent  
**Date**: 2025-05-21

## Overview

The current LangGraph agent has no persistent checkpointer. All short-term conversation state lives only in memory. If the agent container restarts (or the DGX is rebooted), all in-progress conversations and recent context are lost.

For a voice agent that family members will talk to over days and weeks, we need reliable short-term memory persistence in addition to the long-term Supermemory store.

## Goals

- Conversations survive agent restarts and DGX reboots.
- Multiple family members can have independent, persistent threads.
- Easy to swap between different checkpointer backends (in-memory for dev, Postgres/Redis for production).
- Reasonable performance on DGX Spark.

## Current State

- Graph is built with `compile()` but no `checkpointer` argument is passed.
- `VoiceOrchestrator` passes `thread_id` but it is only used for logging / Supermemory `container_tag`.
- LangGraph's `MemorySaver` (in-memory) is the implicit default.

## Requirements

- The checkpointer must support the standard LangGraph checkpoint interface (`get`, `put`, `list`).
- It must be possible to configure the backend via environment variables.
- Thread IDs must be unique per user (`{user_id}:{thread_id}` or similar namespacing).
- The solution must work both locally (Mac dev) and on DGX Spark.

## Recommended Options

1. **In-memory** (`MemorySaver`) – great for local development and quick tests.
2. **SQLite** (via `langgraph-checkpoint-sqlite`) – simple, file-based, zero dependencies, good enough for single-DGX use.
3. **PostgreSQL** (via `langgraph-checkpoint-postgres`) – proper production choice, supports multiple agents, good concurrency.
4. **Redis** – fast, but more operational overhead.

For a home/DGX Spark deployment, **SQLite** is an excellent pragmatic default, with Postgres as an easy upgrade path.

## Proposed Design

- Add a `CHECKPOINTER_BACKEND` env var (`memory`, `sqlite`, `postgres`).
- Create a small factory `get_checkpointer()` in the agent package.
- When building the graph in `get_agent(user_id=...)`, pass the checkpointer.
- Namespacing strategy: use `{user_id}::{thread_id}` as the thread ID passed to LangGraph so isolation is natural.
- Store the SQLite file on a persistent Docker volume so it survives container restarts.

## Open Questions

- Should we also persist the most recent voice context / audio state? (Probably not — keep it lightweight.)
- Do we want automatic checkpoint cleanup (e.g., keep last N checkpoints per thread)?
- How do we handle migration if we change checkpointer backends later?

## Success Criteria

- Restarting the `agent` container does not lose active conversation threads.
- Different family members can interleave conversations without state corruption.
- Switching from SQLite to Postgres is a one-line config change + volume migration.

---

**Next Steps (when picked up)**: Create `tasks.md`, implement the checkpointer factory, wire it into `get_agent()`, update compose to mount a persistent volume for SQLite, and add basic documentation.