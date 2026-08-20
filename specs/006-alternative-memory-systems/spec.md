# Spec: Alternative Long-Term Memory Backends

**Feature ID**: 006-alternative-memory-systems  
**Status**: Draft / Future Consideration  
**Related**: 001-voice-dgx-spark-agent, 002-multi-user-support  
**Date**: 2025-05-21

## Motivation

Supermemory is currently our primary long-term memory store. It provides excellent automatic profiling and semantic search. However, there are reasons we may want to support (or migrate to) other systems in the future:

- Cost / latency (cloud round-trips)
- Privacy / air-gapped DGX deployments
- Different retrieval characteristics (graph memory, temporal, hierarchical, etc.)
- Vendor risk / lock-in

## Current Usage Pattern

All long-term memory access goes through three tools:

- `get_user_profile()`
- `recall_memories(query, limit)`
- `store_memory(content, metadata)`

These are the only places that talk to the underlying memory system. The rest of the agent (graph nodes, voice layer) is decoupled from the specific backend.

This is intentional and makes swapping backends relatively cheap.

## Candidate Alternative Systems

| System              | Strengths                              | Weaknesses                          | Fit for DGX Voice Agent |
|---------------------|----------------------------------------|-------------------------------------|-------------------------|
| **Zep**             | Strong session + long-term memory, good SDK | Cloud-first, newer                  | Good                    |
| **Mem0**            | Lightweight, self-hostable, user profiles | Less mature profiling than Supermemory | Promising               |
| **LangGraph Memory**| Native checkpoint + long-term stores   | Still evolving                      | Natural for this stack  |
| **Custom Vector + Graph** | Full control, can run entirely locally | High implementation cost            | Possible long-term      |
| **SQLite + embeddings** | Dead simple, local, no extra services | Limited recall quality              | Good for very constrained setups |

## Proposed Approach (when we decide to invest)

1. Define a small `MemoryBackend` protocol / abstract base class with the three methods we actually use.
2. Implement adapters for the systems we care about.
3. Make the tool factory (`create_memory_tools`) pluggable so different users or deployments can choose different backends.
4. Keep Supermemory as the default for the family voice agent (excellent UX today).

## When This Becomes Relevant

- We want a fully air-gapped DGX deployment (no outbound Supermemory calls).
- Cost of Supermemory becomes material at household scale.
- We discover specific recall quality problems that another system solves better.
- We want graph-based reasoning over memories (e.g., "who in the family knows about X?").

## Recommendation

Do **not** build this yet. The current Supermemory integration (with proactive injection + reactive tools) is already delivering strong value.

Treat this as an architectural "escape hatch" that we have deliberately kept open by using a narrow tool interface.

---

**When we pick this up**: Create tasks, define the `MemoryBackend` interface, and implement the first alternative adapter (probably Mem0 or a simple local vector store).