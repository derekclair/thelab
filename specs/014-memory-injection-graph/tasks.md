# Tasks: LangGraph memory-injection graph (014)

**Feature**: 014-memory-injection-graph
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)
**Status**: Implemented (graph)

Checkboxes record what is in this tree. Graph work is done. Checkpointer,
eval harness, and a **measured** injection-vs-summarization comparison are
not.

## Phase 0 — SDD record (this folder)

- [x] Write `spec.md` (shipped graph, fail-open, raw injection, no
      checkpointer, unmeasured latency comment)
- [x] Write `plan.md` (architecture as shipped; 001 summarization note
      superseded)
- [x] Write `tasks.md` (this file)
- [x] Point live n=3 spoken timings at the I/O README; do not copy the table
- [x] In this SDD, label the `graph.py` “500-1000ms” comment as unmeasured rationale, not a result (code comment unchanged)

## Phase 1 — Graph (shipped)

- [x] `StateGraph(AgentState)` with nodes `memory_injection`, `call_llm`,
      `execute_tools`
- [x] Entry point `memory_injection`; edge to `call_llm`
- [x] Pull last `HumanMessage` as the recall query
- [x] `create_memory_tools(user_id)` for injection (`state.user_id`)
- [x] `get_user_profile` + `recall_memories(limit=3)` on the injection path
- [x] Fail-open: invoke exceptions → `""`; empty combined → `{}`
- [x] Prepend raw context as `SystemMessage` (`## User Context (from
      long-term memory)`)
- [x] No extra summarization LLM in `_memory_injection`
- [x] `call_llm` binds the three memory tools from graph-build `user_id`
- [x] `ToolNode` when last `AIMessage` has `tool_calls`; else `END`
- [x] Loop `execute_tools` → `call_llm`
- [x] `get_agent(user_id)` → `graph.compile()` with **no** checkpointer
- [x] Export `get_agent` from `thelab_langchain`
- [x] Unit tests: `_should_continue` routing
- [x] Unit tests: injection prepends `SystemMessage`; `get_chat_model` not
      called (`tests/test_agent_graph.py`)
- [x] Unit test: empty profile+recall returns `{}`

## Phase 2 — Follow-ons (not done)

These are **not** required to call the graph implemented. Leave unchecked
until code or measurements exist.

- [ ] LangGraph checkpointer on `get_agent()` (spec 004 — factory, namespaced
      `thread_id`, tests that two threads do not share state)
- [ ] Eval harness for injection quality (fixtures; no transcripts or
      household identifiers in git)
- [ ] Measured latency of raw injection vs an extra summarization round-trip
      (record the method and the result; do **not** promote the in-code
      500-1000ms comment)

## Out of scope (stay unchecked here)

- [ ] Second memory backend / `MemoryBackend` ABC (spec 006)
- [ ] Speaker ID / tenant product (spec 002)
- [ ] Voice speakability filter (spec 011)
- [ ] Switching `MemoryChat` onto this graph
- [ ] Copying sibling-repo n=3 latency tables into this package
- [ ] Fail-open around `create_memory_tools` / missing API key (factory still
      raises; not a 014 bug-fix unless a later spec asks)

## Traceability

| Want | Code today |
|------|------------|
| Proactive memory before LLM | `_memory_injection` entry node |
| Raw context, no extra LLM | `SystemMessage` prepend; test asserts `get_chat_model` unused |
| Fail-open invoke | `except Exception: ""` on profile/recall invoke |
| Reactive store/recall | tools bound + `ToolNode` loop |
| Per-user scope | `create_memory_tools(user_id)` (spec 002 / 006) |
| Short-term persistence | **None** — spec 004 |
| Eval / measured injection latency | **Not in this tree** |

Code: `src/thelab_langchain/agent/graph.py`,
`src/thelab_langchain/agent/tools/memory.py`,
`src/thelab_langchain/agent/state.py`,
`tests/test_agent_graph.py`.

Live consume path: [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
calls `thelab_langchain.agent.graph.get_agent`.
