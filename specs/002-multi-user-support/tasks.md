# Tasks: Multi-user support (002)

**Feature**: 002-multi-user-support
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes record what is in this tree today versus what remains design-only.
This file was filled in when the SDD record was completed, not when the
identity seam was first written. This is **not** a shipped tenant model.

## Phase 0 — Identity seam (this repo)

- [x] `DEFAULT_USER_ID` in settings (`thelab_langchain.config`)
- [x] `user_id` on `get_agent()` / `build_agent_graph()`
- [x] `AgentState.user_id` and `AgentState.thread_id` fields
- [x] `create_memory_tools(user_id)` scopes `profile` / `add` / `search` with `container_tag=user_id`
- [x] `MemoryChat(user_id)` uses the same `container_tag`
- [x] CLI `--user` and `/user <id>` (rebuilds MemoryChat for that container)
- [x] Voice orchestrator accepts `user_id` and passes it into `get_agent()`
- [ ] LangGraph checkpointer per thread (spec 004 — not required to call 002’s seam done)
- [ ] Speaker identification (not in tree; `/user` is not speaker ID)

## Phase 1 — Explicit identification (not shipped)

- [ ] Bind a session to a `user_id` at start (flag, config, or spoken declaration)
- [ ] Parse explicit “this is `<user_id>`” (or equivalent) and switch the bound id
- [ ] If the turn cannot be bound, ask which `user_id` to use; do not guess
- [ ] Known ids from config only — no coded household roster
- [ ] Voice I/O (sibling package) must pass the bound `user_id` into `get_agent()` every turn
- [ ] Document the bind/switch commands next to `/user` without treating them as speaker ID

## Phase 2 — Isolation completeness (design)

- [ ] Thread namespacing `{user_id}::{thread_id}` when spec 004 has a checkpointer
- [ ] Test: memories stored under `user_a` are not returned for `user_b`
- [ ] Test: `/user` (or equivalent) actually changes `container_tag` for the next turn
- [ ] Optional shared household `container_tag` with an explicit write path
- [ ] Guest / unknown policy (refuse vs generic `guest` container) — decide, then implement
- [ ] Speaker diarization / voice embeddings — out of scope for v1

## Traceability

Phase 0 lives in this package (`thelab_langchain.config`, `agent.graph.get_agent`,
`agent.tools.memory.create_memory_tools`, `chat.MemoryChat`, `cli` `/user`).
Phases 1–2 are not done. This tasks file is only the checklist view of the
design plus the identity seam that already exists.
