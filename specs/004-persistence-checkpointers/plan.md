# Plan: Persistence & checkpointers (004)

**Feature**: 004-persistence-checkpointers
**Spec**: [spec.md](./spec.md)
**Date**: 2025-05-21 (spec); recorded 2026-08-19

## 1. Architecture (as shipped)

Short-term conversation state is **not** a LangGraph checkpoint. `get_agent()`
compiles with no `checkpointer` argument. Turns that survive a process only
do so because the **caller** keeps a message list.

```
Live voice I/O (sibling)                 this package
  session Human/AI list                  get_agent(user_id)
        │                                      │
        └── graph.invoke({messages}) ──►  graph.compile()   # no checkpointer
                                              │
                         memory_injection → call_llm → execute_tools
                                              │
                                              ▼
                                        Supermemory (long-term only)
```

| Piece | Owner today |
|-------|-------------|
| Per-turn history | Caller. Live path is [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent): accumulate `HumanMessage` / `AIMessage` for the session. |
| LangGraph checkpoint | **None.** `get_agent()` is `return graph.compile()`. |
| `thread_id` on state | Data field / log tag. Not `config["configurable"]["thread_id"]`. |
| In-tree `VoiceOrchestrator` | Invokes with **this turn only** (`[HumanMessage(text)]`). Does not accumulate. |
| Long-term facts | Supermemory tools (`create_memory_tools`). Out of scope for 004. |

`MemorySaver` is **not** implicit. Omitting `checkpointer` means no thread
memory inside the graph. Each `invoke` sees only the `messages` the caller
passed.

## 2. Tech choices

### Locked now (honest)

| Concern | Choice | Why |
|---------|--------|-----|
| Checkpointer | Not wired | Spec 008 does not require it; nothing here survives a restart |
| Session history | Caller-side list | Sibling already does this; do not double-store |
| Durable short-term | None | Process death / reboot drops in-flight turns |
| Long-term | Unchanged Supermemory | Spec 006 |

### If this spec is picked up later (not started)

| Concern | Intended choice | Why |
|---------|-----------------|-----|
| Dev | `MemorySaver` | In-process only |
| Default durable | SQLite (`langgraph-checkpoint-sqlite`) + volume | Single host, low ops |
| Upgrade | Postgres via env | Same factory |
| Factory | `get_checkpointer()` + `CHECKPOINTER_BACKEND` | `memory` / `sqlite` / `postgres` |
| Isolation | `{user_id}::{thread_id}` as LangGraph `thread_id` | Spec 002; do not confuse with `AgentState.thread_id` |

## 3. Phases

### Phase 0 — Document current in-memory behavior (this SDD)

- Record that `compile()` has no checkpointer.
- Record caller-side accumulation on the live voice path.
- Record that the in-tree orchestrator is single-turn per invoke.

### Phase 1 — Factory + wire (not started)

- `get_checkpointer()` in the agent package.
- Pass it into `graph.compile(checkpointer=...)`.
- Invoke with `configurable.thread_id` (namespaced).
- Decide whether the sibling still accumulates, or the graph becomes the source of history (do not do both blindly).

### Phase 2 — Durable backend (not started)

- SQLite file on a persistent volume.
- Postgres as a config change, not a second graph.
- Optional last-N checkpoint cleanup.

Phase 1–2 are **not** in this tree. Do not treat this plan as a claim they shipped.

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Double history (checkpointer + caller list) | Pick one owner of short-term turns before wiring |
| `AgentState.thread_id` vs LangGraph config `thread_id` | Namespacing lives in `configurable`; state field is not a checkpoint key |
| Spec text that called MemorySaver “implicit default” | This plan supersedes that: it is opt-in |
| Backend swap later | Factory + one env var; no graph fork |

## 5. Success metrics (only after Phase 1–2)

- Restarting the agent process does not drop an active thread.
- Two `user_id` values cannot read each other’s short-term state.
- SQLite → Postgres is env + volume, not a rewrite.

None of these hold today.

## 6. What this plan is not

It is not an implementation of `get_checkpointer()`. It is not a SQLite volume
in compose. It is not a requirement to call spec 008 done. It is not
persistence of audio / LED / VAD state. It is not a second long-term memory
store (that is 006, and 006 is also not building adapters).
