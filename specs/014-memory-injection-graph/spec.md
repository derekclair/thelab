# Feature Spec: LangGraph memory-injection graph

**Feature ID**: 014-memory-injection-graph
**Status**: Implemented (graph)
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [002-multi-user-support](../002-multi-user-support/spec.md) (`user_id`),
[004-persistence-checkpointers](../004-persistence-checkpointers/spec.md) (not wired),
[006-alternative-memory-systems](../006-alternative-memory-systems/spec.md) (narrow tool interface),
[008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md) (voice uses `get_agent()`)

This folder documents **what shipped** in this repo. It is not a redesign.

## Honest current state

This package’s distinctive code is the LangGraph in
`src/thelab_langchain/agent/graph.py`.

The compiled agent is `get_agent(user_id)`. Entry node is `memory_injection`.
It runs **before** `call_llm`. It pulls the last `HumanMessage`, then calls
`get_user_profile` and `recall_memories(limit=3)` from
`create_memory_tools(user_id)`. Tool **invoke** failures become empty strings
(fail-open). Non-empty raw profile + recall is prepended as a `SystemMessage`.
There is **no** extra LLM summarization pass.

The in-code comment that this avoids “500-1000ms of latency per voice turn”
is a **rationale, unmeasured**. Do not put that range on a résumé, in a
benchmark claim, or in this spec as a result. Live spoken-turn timings (n=3
table) live in the
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
README, not here. This spec does not copy that table and does not invent
numbers.

Then `call_llm` runs with the same three memory tools bound. If the model
emits `tool_calls`, `ToolNode` executes and the graph loops back to
`call_llm`. Otherwise it ends.

`get_agent()` is `graph.compile()` with **no checkpointer** (spec 004).
Callers that need a session keep a `HumanMessage` / `AIMessage` list
themselves. Text CLI (`MemoryChat`) is a **different** path: it does not use
this graph.

Unit tests in `tests/test_agent_graph.py` cover routing and injection with
mocked tools (including “no summarization LLM”). There is no eval harness and
no measured injection-vs-summarization latency in this tree.

## Overview

On every `get_agent()` turn, give the model user context **without waiting for
it to tool-call**, then still let it store or recall reactively.

Two memory modes, one factory:

1. **Proactive** — `memory_injection` fetches profile + a few recalled
   memories from the last user utterance and prepends them as raw context.
2. **Reactive** — `call_llm` has `get_user_profile`, `recall_memories`, and
   `store_memory` bound so the model can deepen recall or write a fact.

Long-term store is Supermemory, scoped by `user_id` as `container_tag`
(spec 002 / 006). Short-term turns are the caller’s message list (spec 004).
Live speakerphone I/O imports this graph and does not reimplement it
(spec 008).

## Goals

- Document the shipped graph: entry injection, LLM + tools, tool loop, no
  checkpointer.
- Keep injection raw (no extra summarization round-trip).
- Fail-open on memory **invoke** so a recall/profile error does not kill the
  turn.
- Keep the tool interface the three names in spec 006.
- Stay honest about latency: unmeasured comment in `graph.py`; live n=3 table
  is in the sibling I/O README, not this package.

## Non-goals

- Wiring a LangGraph checkpointer (spec 004).
- A second memory backend or `MemoryBackend` ABC (spec 006).
- Speaker ID / tenant product (spec 002).
- Speakability filter on `AIMessage.content` (spec 011).
- Copying or paraphrasing Hermes `SOUL.md`.
- Copying the sibling-repo live latency table into this tree.
- Inventing or reprinting millisecond numbers as if measured here.
- Changing `MemoryChat` / `thelab-chat` to use this graph.
- ALSA, Piper, Parakeet, LED, or button interrupt (spec 008 / I/O repo).

## User stories

1. As the person at the desk, I speak a turn and the model already has my
   profile and a few relevant memories, without a tool-call round-trip first.
2. As that person, I can still have the model store a new fact or search
   memory more deeply in the same turn.
3. As a developer, I know `get_agent(user_id)` is the brain seam the I/O
   process calls.
4. As a developer, I know injection is fail-open on tool invoke, and that
   missing context is a no-op (`{}`), not a crash of the node.
5. As a developer, I do not treat the “500-1000ms” comment as a benchmark.

## Functional requirements

### FR-1 Graph shape (shipped)

```
memory_injection  →  call_llm  →  execute_tools  →  call_llm  (loop)
                         │
                         └── END  (no tool_calls)
```

- Entry point is `memory_injection`.
- Unconditional edge: `memory_injection` → `call_llm`.
- Conditional: last message is `AIMessage` with `tool_calls` →
  `execute_tools`; otherwise `END`.
- `execute_tools` always returns to `call_llm`.
- Public factory: `get_agent(user_id="default-user")` compiles that graph.

### FR-2 Proactive injection (shipped)

`_memory_injection(state)`:

1. `user_id` from `state.user_id`, default `"default-user"`.
2. Last `HumanMessage` content, scanning `state.messages` from the end.
3. `create_memory_tools(user_id)` (same factory as the bound tools).
4. `get_user_profile.invoke({"query": last_user_msg or None})` if that tool
   exists.
5. `recall_memories.invoke({"query": last_user_msg, "limit": 3})` if that
   tool exists **and** there is a last user utterance.
6. Combine: profile text, then `## Relevant Long-term Memories` + recall.
7. If combined is empty, return `{}` (no injection).
8. Else prepend
   `SystemMessage("## User Context (from long-term memory)\n" + combined)`
   and return `{"messages": [injection] + list(state.messages)}`.

Do **not** call `get_chat_model()` in this node. Raw tool strings go to the
main LLM.

`AgentState.long_term_context` exists on the state model and is **not**
written by this node. Injection is the `SystemMessage` on `messages`.

### FR-3 Fail-open on invoke (shipped)

- Exceptions from `profile_tool.invoke` / `recall_tool.invoke` become `""`.
- Missing tools are skipped.
- Empty combined context → `{}`.
- **Not** fail-open: `create_memory_tools` itself (missing
  `SUPERMEMORY_API_KEY` still raises in the factory). Documented so operators
  do not confuse “empty context” with “missing key”.

### FR-4 LLM + reactive tools (shipped)

- `call_llm` binds `create_memory_tools(user_id)` from **graph build**
  (`get_agent(user_id)` / `build_agent_graph(user_id)`).
- Tools: `get_user_profile`, `recall_memories`, `store_memory` (spec 006).
- `execute_tools` is LangGraph `ToolNode(tools)`.
- Injection recreates tools from `state.user_id`. Callers should pass the
  same `user_id` to `get_agent` and in `AgentState` so the two scopes match
  (spec 002).

### FR-5 No checkpointer (shipped absence)

- `get_agent()` is `return graph.compile()` — no `checkpointer` argument.
- Spec 004 remains not wired. This spec does not pretend persistence exists.

### FR-6 Honesty about latency

- Design intent: skip a summarization LLM so a voice turn does not pay an
  extra model round-trip. That intent is in `graph.py` and in unit tests
  (`get_chat_model` must not be called from `_memory_injection`).
- The “500-1000ms” figure is **unmeasured in-code rationale**. Not a result.
- Measured spoken-path tables, if any, stay in the I/O repo README. Do not
  duplicate them here.

## Non-functional requirements

- No secrets, serials, transcripts, or household identifiers in this spec or
  in example utterances.
- No invented latency numbers.
- Same `get_agent(user_id)` seam as spec 008.
- Long-term access only through the three tools (spec 006).
- Privacy: `container_tag=user_id`; do not search across users.

## Acceptance criteria

- [x] Entry node is `memory_injection`; it runs before `call_llm`.
- [x] Injection uses last `HumanMessage` + `get_user_profile` +
      `recall_memories(limit=3)` via `create_memory_tools(user_id)`.
- [x] Invoke failures become empty strings; empty combined context returns
      `{}`.
- [x] Injection is a prepended `SystemMessage` of raw context (no extra LLM).
- [x] `call_llm` binds tools; `ToolNode` loops back when `tool_calls` exist.
- [x] `get_agent()` compiles with no checkpointer.
- [x] Unit tests: routing + injection without a summarization LLM
      (`tests/test_agent_graph.py`).
- [ ] Checkpointer wired (spec 004 — out of this graph’s shipped scope).
- [ ] Eval harness for injection quality.
- [ ] Measured latency of injection vs an extra summarization round-trip
      (do not treat the in-code range as that measurement).

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Compiled graph. Voice I/O (spec 008) invokes this. |
| `graph.invoke({"messages": ...})` | Caller supplies the turn (and any session history). |
| `create_memory_tools(user_id)` | Only long-term memory factory (spec 006). |
| `user_id` | Opaque string; Supermemory `container_tag` (spec 002). |
| Injection message | `SystemMessage` titled `## User Context (from long-term memory)`. |
| Checkpointer | None. Caller owns short-term turns (spec 004). |

## Relationship to other specs

- **002** — `user_id` on `get_agent` / `AgentState` / tools. Injection does
  not identify speakers.
- **004** — checkpointer not wired. This graph does not add one.
- **006** — three-tool interface; no second backend.
- **008** — live voice consumes `get_agent()`. I/O does not copy `graph.py`.
- **011** — reply speakability is a wanted contract, not this node.
- **001 / 007** — broader desktop-voice / Spark budget. This folder is the
  brain graph that actually shipped.

## Open questions

- Should `_memory_injection` close over the graph-build `user_id` instead of
  reading `state.user_id`, so the two tool sets cannot diverge?
- Should the node return only the new `SystemMessage` (rely on `add_messages`)
  instead of `[injection] + list(state.messages)`?
- Should `AgentState.long_term_context` be removed or actually used?
- How (and where) to measure injection vs summarization without putting
  unmeasured ranges in this package.
- Eval harness: offline fixtures with mocked tools, or a gated live-memory
  job? Neither exists.

---

**Status**: Graph implemented in this tree. Checkpointer, eval harness, and a
measured injection-vs-summarization comparison are **not** done.
