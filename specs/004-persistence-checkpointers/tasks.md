# Tasks: Persistence & checkpointers (004)

**Feature**: 004-persistence-checkpointers
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes record what is actually in the tree. A LangGraph checkpointer is
**not** wired. Phase 0 is this SDD record. Leave Phase 1–2 unchecked until
code ships.

## Phase 0 — Document current in-memory behavior

- [x] Record that `get_agent()` is `graph.compile()` with no `checkpointer`
- [x] Record that live voice I/O accumulates `HumanMessage` / `AIMessage` caller-side
- [x] Record that in-tree `VoiceOrchestrator` invokes with the current turn only
- [x] Record that `AgentState.thread_id` is not LangGraph `configurable.thread_id`
- [x] Record that `MemorySaver` is opt-in, not an implicit default

## Phase 1 — Factory + wire (not started)

- [ ] Add `get_checkpointer()` in the agent package
- [ ] `CHECKPOINTER_BACKEND` env (`memory` / `sqlite` / `postgres`)
- [ ] Pass the checkpointer into `graph.compile(...)`
- [ ] Namespace LangGraph `thread_id` as `{user_id}::{thread_id}`
- [ ] Invoke with `config={"configurable": {"thread_id": ...}}`
- [ ] Choose one owner of short-term history (graph vs caller); do not double-store
- [ ] Tests that two thread ids do not share checkpoint state (in-memory backend)

## Phase 2 — Durable backend (not started)

- [ ] SQLite checkpointer + persistent volume
- [ ] Postgres path as the same factory, different env
- [ ] Document backend swap (env + volume; no graph fork)
- [ ] Optional last-N checkpoint cleanup per thread

## Out of scope (do not check as 004 done)

- [ ] LangGraph checkpointer required for spec 008
- [ ] Persist voice / audio / LED state
- [ ] Second long-term memory backend (spec 006)
- [ ] Multi-tenant product isolation (spec 002 is design-only)

## Traceability

`src/thelab_langchain/agent/graph.py` — `get_agent()` compiles with no
checkpointer. Live session lists live in
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent),
not in this graph.
