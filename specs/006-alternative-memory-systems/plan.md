# Plan: Alternative long-term memory systems (006)

**Feature**: 006-alternative-memory-systems
**Spec**: [spec.md](./spec.md)
**Date**: 2025-05-21 (spec); recorded 2026-08-19

## 1. Architecture (escape hatch, not a second store)

Long-term memory already has a narrow seam. The graph and voice layer do not
import a second backend. Keep it that way until a **real** need appears.

```
get_agent(user_id)
        │
        ├── memory_injection  ──►  create_memory_tools(user_id)
        ├── call_llm (tools bound)         │
        └── execute_tools                  ▼
                              get_user_profile
                              recall_memories(query, limit)
                              store_memory(content, metadata)
                                           │
                                           ▼
                                      Supermemory
```

| Piece | Owner |
|-------|--------|
| Tool names + signatures | `src/thelab_langchain/agent/tools/memory.py` |
| Per-user scope | `user_id` → Supermemory `container_tag` |
| Graph / voice | Call the three tools only |
| Short-term turns | Spec 004 (caller-side list; no checkpointer). Not this spec. |

## 2. Tech choices (locked until a trigger fires)

| Concern | Choice | Why |
|---------|--------|-----|
| Long-term store | Supermemory | Already delivering profile + recall |
| Seam | The three tools above | Cheap swap later; no ABC yet |
| `MemoryBackend` protocol | **Do not add** | Protocol-for-one-impl is noise |
| Second adapter (Mem0, Zep, local vectors, …) | **Do not build** | No air-gap / cost / quality trigger yet |
| Default if we ever swap | Keep Supermemory as default | Household path stays the known UX |

Candidates in the spec (Zep, Mem0, LangGraph store, custom vector+graph,
SQLite+embeddings) stay a table of options. They are not a backlog to
implement in order.

## 3. Phases

### Phase 0 — Keep the interface narrow (now)

- Leave `create_memory_tools(user_id)` as the only factory.
- Do not introduce a protocol, registry, or dual-write.
- New graph nodes must not import a memory SDK except through those tools.

### Phase 1 — Adapter, only after a real need (not started)

Triggers that would justify Phase 1 (any one is enough; none are true today):

- Fully air-gapped deploy (no outbound memory calls).
- Cost of the current store is material at this scale.
- Measured recall/profile gap another system actually fixes.
- Need graph-shaped queries the current store cannot do.

Then, and only then:

1. Pick **one** second backend for that need (not a portfolio).
2. Extract a small protocol that matches the three methods we already use.
3. Make `create_memory_tools` pluggable; default remains Supermemory.

Do not start Phase 1 “so it will be ready.”

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Premature ABC | No protocol until a second impl is chosen |
| Dual-write / split brain | One store per deploy; no silent fan-out |
| Backend types leaking into graph nodes | Tools stay the only import surface |
| Confusing 004 checkpointers with 006 stores | Short-term ≠ long-term; do not merge them |

## 5. Success metrics

- Still one factory and three tool names.
- `graph.py` does not grow a second memory client.
- A second backend appears only after a trigger above is written down.

There is no success metric for “we have N adapters.”

## 6. What this plan is not

It is not a Mem0 or Zep port. It is not a local vector store. It is not
leaving Supermemory. It is not a LangGraph checkpointer (004). It is not
permission to add `MemoryBackend` “for cleanliness.”
