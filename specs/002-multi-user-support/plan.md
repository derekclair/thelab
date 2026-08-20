# Plan: Multi-user support (002)

**Feature**: 002-multi-user-support
**Spec**: [spec.md](./spec.md)
**Date**: 2025-05-21 (design); recorded 2026-08-19

Honest status: **designed**, not a shipped tenant model. The tree has an identity
seam. It does not identify speakers.

## 1. Architecture

Identity is a string. Memory isolation is that string used as a Supermemory
`container_tag`. Session isolation is `thread_id` (LangGraph checkpointer is
spec 004 — not required to call this design done).

```
household user (voice or text)
        │
        ▼
 identify → user_id          v1: explicit only
        │                    (--user, /user <id>, "this is <user_id>")
        ▼
 get_agent(user_id)  ──►  create_memory_tools(user_id)
        │                      profile / add / search
        │                      container_tag = user_id
        ▼
 AgentState.user_id + thread_id
        │
        ├── long-term:  Supermemory container_tag
        └── short-term: LangGraph thread (004, not in tree)
```

| Piece | Owner |
|-------|--------|
| `DEFAULT_USER_ID`, `get_agent(user_id)`, MemoryChat `/user` | **this repo** (`thelab_langchain`) |
| Supermemory `container_tag` scoping | `create_memory_tools` / `MemoryChat` |
| Speaker diarization / voice embeddings | **out of scope for v1** |
| Checkpointer per `thread_id` | spec 004 |

Live voice I/O (sibling package) must pass the bound `user_id` into `get_agent()`.
It must not invent a second identity model.

## 2. Tech choices (locked for v1)

| Concern | Choice | Why |
|---------|--------|-----|
| Identity | Opaque `user_id` string | No household roster in code or SDD |
| Long-term isolation | Supermemory `container_tag = user_id` | Already the memory API’s tenant key |
| Session isolation | `thread_id`, later `{user_id}::{thread_id}` | Prevents short-term mix when 004 lands |
| Who is talking (v1) | Explicit identification first | `/user`, `--user`, spoken declaration |
| Who is talking (not v1) | Speaker diarization | Out of scope; do not block v1 on it |
| Default session | `DEFAULT_USER_ID` | Single-user path stays one flag |
| Shared facts | Optional household `container_tag` | Only if explicitly stored as shared |
| Brain factory | Existing `get_agent(user_id)` | Do not fork the graph per person |

## 3. Phases

### Phase 0 — Identity seam (this repo; in the tree)

- `DEFAULT_USER_ID` from settings.
- `get_agent(user_id)` / `build_agent_graph(user_id)` bind tools to that id.
- `MemoryChat(user_id)` uses `container_tag=self.user_id`.
- CLI `--user` and `/user <id>` rebuild the chat for a different container.
- `AgentState` already has `user_id` and `thread_id` fields.

This is a **container switch**, not speaker ID.

### Phase 1 — Explicit identification (not shipped)

- Bind a session to a `user_id` at start, or parse an explicit declaration.
- If unbound / unknown, ask which `user_id` to use; do not guess.
- Voice I/O passes the bound id into `get_agent(user_id)` on every turn.
- Known ids come from config, not from a coded household list.

### Phase 2 — Isolation completeness (design; not a tenant product)

- Namespace threads `{user_id}::{thread_id}` once spec 004 has a checkpointer.
- Tests: container A must not recall container B.
- Optional shared household `container_tag` with an explicit write path.
- Still no diarization.

Phase 2 is finishing **this** isolation design. It is not multi-tenant SaaS.

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Calling this “multi-tenant” because `/user` exists | Spec and tasks state: seam only, not speaker ID |
| Cross-container recall via a shared client | Always pass `container_tag=user_id`; never a global search |
| Default `user_id` silently used for the wrong person | Unknown speaker → ask; do not fall back without saying so |
| Inventing a household roster in docs or config | Opaque `user_id` / `container_tag` only |
| Checkpointer mixing threads across users | Spec 004 namespacing; this plan does not fake persistence |
| Diarization scope creep | Keep v1 explicit-only; diarization stays a non-goal |

## 5. Success metrics

- Two `user_id` values, two containers: facts stored under A never appear in B’s profile/search.
- `/user <id>` (or `--user`) changes the container for subsequent turns.
- Unbound session asks for a `user_id` instead of guessing.
- Adding a user is a new id in config, not a code change.
- No speaker-ID model required for the above to be true.

## 6. What this plan is not

It is not a shipped tenant model. It is not speaker identification. It is not
spec 004 (checkpointers). It does not define a household of named people. It
does not replace spec 001.
