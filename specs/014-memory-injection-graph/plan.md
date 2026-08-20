# Plan: LangGraph memory-injection graph (014)

**Feature**: 014-memory-injection-graph
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20
**Status**: Implemented (graph)

This plan records the architecture that **already shipped**. It is not a
proposal to rewrite `graph.py`. Follow-on work is only checkpointer (004),
an eval harness, and a **measured** injection-vs-summarization comparison.

## 1. Architecture (as shipped)

This repo is the brain. Live voice I/O imports `get_agent()` and does not
fork the graph (spec 008).

```
Caller (voice I/O or tests)
  session messages + user_id
        │
        ▼
 get_agent(user_id)          graph.compile()   # no checkpointer (004)
        │
        ▼
 memory_injection            entry
   last HumanMessage
   create_memory_tools(state.user_id)
   get_user_profile          fail-open invoke → ""
   recall_memories(limit=3)  fail-open invoke → ""
   prepend SystemMessage     raw text; no summarization LLM
        │
        ▼
 call_llm                    tools bound at graph-build user_id
        │
        ├── tool_calls → execute_tools (ToolNode) → call_llm
        └── else END
```

| Piece | Owner |
|-------|--------|
| Graph, injection, tool loop | **this repo** (`src/thelab_langchain/agent/graph.py`) |
| Tool factory | `create_memory_tools(user_id)` (spec 006) |
| `user_id` → `container_tag` | spec 002 |
| Short-term turns | Caller list. No checkpointer (spec 004) |
| Live speakerphone | [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) calls `get_agent()` |
| Text CLI | `MemoryChat` — **not** this graph |

Two `create_memory_tools` call sites:

- `build_agent_graph(user_id)` binds tools for `call_llm` / `execute_tools`.
- `_memory_injection` rebuilds tools from `state.user_id`.

Callers must pass the same id both places. The graph does not reconcile them.

## 2. Tech choices (locked for what shipped)

| Concern | Choice | Why |
|---------|--------|-----|
| Graph type | Custom `StateGraph(AgentState)`, not `create_react_agent` | Control the injection node |
| Entry | `memory_injection` before `call_llm` | Context without a first tool-call |
| Recall depth on inject | `limit=3` | Small raw block; main LLM still has reactive `recall_memories` |
| Injection payload | Raw tool strings as `SystemMessage` | Skip a second model call per turn |
| “500-1000ms saved” | **Unmeasured** comment in `graph.py` | Design rationale only; not a result |
| Live n=3 timings | Sibling I/O README | Do not copy into this package |
| Fail-open | `except Exception: ""` on **invoke** | Empty context, not a dead turn |
| Factory errors | Not swallowed | Missing memory key still raises |
| Reactive tools | Same three names, `ToolNode`, loop to `call_llm` | Store / deeper recall when the model asks |
| Checkpointer | None | Spec 004 |
| Summarization node | **Forbidden** until measured and chosen | Extra round-trip is the thing this design skipped |

001’s older note about “optional LLM summarization of retrieved memories”
did **not** land. 014 supersedes that micro-iteration: raw injection is the
shipped path.

## 3. Phases

### Phase 0 — SDD record (this folder)

- Write spec / plan / tasks that match `graph.py` and
  `tests/test_agent_graph.py`.
- Label the in-code latency range unmeasured.
- Point at the I/O README for live spoken timings; do not paste that table.

### Phase 1 — Graph (shipped)

Already in the tree. Do not re-check these as future work:

- `memory_injection` → `call_llm` → optional `execute_tools` loop.
- Last `HumanMessage` as recall query; profile + `limit=3`.
- Fail-open invoke; empty combined → `{}`.
- Raw `SystemMessage`; unit test that `get_chat_model` is not used here.
- `get_agent(user_id)` compiled with no checkpointer.
- Public export: `thelab_langchain.get_agent`.

### Phase 2 — Not this graph (unchecked)

Do not mark 014 “complete including follow-ons” until these exist:

1. **Checkpointer** — spec 004. Not a 014 rewrite of injection.
2. **Eval harness** — injection quality with mocked (or gated live) memory.
   None in `tests/` today.
3. **Measured latency** — injection vs an extra summarization LLM, recorded
   as a measurement. Until then, keep the `graph.py` range labeled
   unmeasured and off the résumé.

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Treating “500-1000ms” as a result | Spec + tasks: unmeasured; live table stays in I/O README |
| Extra summarization “to improve quality” | Forbidden without a measured comparison |
| Injection `user_id` ≠ bound-tool `user_id` | Same id on `get_agent` and state (spec 002) |
| Factory raise vs invoke fail-open | Document: missing key is not empty context |
| Double-storing history if 004 lands | 004 plan: pick one owner of short-term turns |
| Copying transcripts / identifiers into eval fixtures | Privacy: no keys, serials, transcripts, household ids |
| I/O reimplementing injection | Spec 008: one import, `get_agent()` |

## 5. Success metrics

Shipped (graph):

- A compiled `get_agent()` turn always hits `memory_injection` before the
  LLM.
- Tests prove injection does not call `get_chat_model`.
- Empty / failed invoke does not require a summarization model to recover.

Not shipped (do not claim):

- Process restart keeps short-term turns (004).
- Eval scores for recall/profile usefulness.
- A measured delta for injection vs summarization.

## 6. What this plan is not

It is not a checkpointer. It is not a second memory backend. It is not
`MemoryChat`. It is not the I/O latency table. It is not permission to print
unmeasured milliseconds as a benchmark. It is not spec 011 speakability.
It does not replace spec 001’s broader desktop-voice goal.
