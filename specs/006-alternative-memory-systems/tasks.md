# Tasks: Alternative long-term memory systems (006)

**Feature**: 006-alternative-memory-systems
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes record what is actually in the tree. This spec is an escape hatch.
Do **not** build adapters or a second backend until a real need is written
down.

## Phase 0 — Keep the interface narrow

- [x] Long-term access only via `get_user_profile`, `recall_memories`, `store_memory`
- [x] Keep `create_memory_tools(user_id)` as the only factory
- [x] Scope tools with `user_id` (`container_tag`); graph does not pick a backend
- [x] Document this as an escape hatch, not a multi-backend project
- [x] Do not add a `MemoryBackend` protocol / ABC for a single implementation
- [x] Do not add a second memory client in `graph.py` or the voice layer

Standing rule: new code talks to long-term memory only through those three
tools.

## Phase 1 — One adapter, only after a real need (not started)

Do not schedule these. They unlock when a trigger in the plan is real.

- [ ] Write the trigger (air-gap, cost, measured recall gap, or graph queries)
- [ ] Choose **one** second store for that trigger
- [ ] Define a protocol that matches the three methods we already use
- [ ] Implement one adapter; keep Supermemory the default
- [ ] Make `create_memory_tools` pluggable without changing graph node shape
- [ ] Tests: graph still compiles when the default backend is the only one configured

## Out of scope (no second backend until a real need)

- [ ] Zep adapter
- [ ] Mem0 adapter
- [ ] LangGraph long-term memory store as a parallel backend
- [ ] Custom vector + graph store
- [ ] SQLite + embeddings as a second production path
- [ ] Dual-write to two stores
- [ ] Swap motivated only by “we might want it later”

## Traceability

`src/thelab_langchain/agent/tools/memory.py` is the seam.
`src/thelab_langchain/agent/graph.py` calls `create_memory_tools` for injection
and tool-calling. Short-term turns are spec 004 (still no checkpointer).
