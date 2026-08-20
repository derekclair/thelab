# Feature Spec: Multi-User Support for the Voice Agent

**Feature ID**: 002-multi-user-support
**Status**: Designed; not a shipped tenant model
**Related to**: [001-voice-dgx-spark-agent](../001-voice-dgx-spark-agent/spec.md)
**Created**: 2025-05-21
**Recorded here**: 2026-08-19
**Owner**: Derek Clair

## Current state (honest)

This spec is the **design** for per-user isolation. It is not a product multi-tenant system.

Code in this repo today is an identity **seam**, not speaker ID:

- `DEFAULT_USER_ID` in settings
- `user_id` on `get_agent()` / `build_agent_graph()` and `AgentState`
- Supermemory calls scoped with `container_tag=user_id`
- MemoryChat CLI `--user` and `/user <id>` (rebuilds the chat for that container)

There is no speaker diarization, no voice fingerprint, and no automatic “who is talking” path. A `/user` switch is an explicit container change.

## Overview

The voice agent should support multiple **household users** on the same deployment.

Each user is an opaque `user_id`. Long-term memory is isolated by a Supermemory `container_tag` (the same string as `user_id`). Short-term conversation state is isolated by `thread_id`. When someone speaks, the session must already be bound to a `user_id`, or the speaker must **declare** it.

This is a **cross-cutting concern**: identification, Supermemory container isolation, session/thread management, LangGraph state, and the voice loop.

## Goals

- Natural multi-user experience for household users.
- Strong long-term memory isolation per `user_id` (via Supermemory `container_tag`).
- Low-friction identification: explicit declaration first; do not require a login ritual every turn once the session is bound.
- Adding another `user_id` is configuration, not a rewrite.
- Privacy boundaries between users: no cross-container recall.

## Non-Goals (for v1)

- Speaker diarization / biometric voice fingerprinting (out of scope for v1; possible later).
- Remote multi-user access from outside the deployment.
- Roles, permissions, or an admin/RBAC model.
- Guest accounts with temporary memory (open question, not v1).
- Inferring household relationships from names or stories.

## User Stories

1. **As a household user**, I want memories, preferences, and ongoing work scoped to my `user_id` even if another household user spoke to the agent recently.
2. **As a household user**, I want my Supermemory `container_tag` isolated so another user’s facts are not injected into my turns.
3. **As a household user**, I want to identify myself explicitly (or start a session already bound to my `user_id`) so the agent uses the right container.
4. **As the operator**, I want adding or switching a `user_id` to be a low-effort config / command, not a new deployment.
5. **As a household user**, if the agent does not know which `user_id` is speaking, I want it to ask rather than guess.

## Functional Requirements

### FR-1: User Identity & Routing

- Every voice or text interaction must be associated with a specific `user_id`.
- Identification methods for v1, in priority order:
  1. Explicit declaration (e.g. “this is `<user_id>`”) or session start with `--user` / `/user <id>`
  2. Wake-word + declared-name patterns (same explicit idea; not voice biometrics)
  3. Heuristic / voice characteristics — **out of scope for v1**
  4. Device or room context — later, if multiple capture devices exist
- Speaker diarization is **out of scope for v1**.

### FR-2: Memory Isolation (Supermemory)

- Every `user_id` has its own `container_tag`.
- All `profile()`, `add()`, and `search` calls must be scoped to the identified `user_id`.
- Cross-user leakage must be prevented (no accidental recall of one container’s facts into another).

### FR-3: Session & Thread Management

- Each user has their own conversation threads (`thread_id`).
- Short-term memory (LangGraph checkpointer, when spec 004 lands) must be isolated per user.
- Parallel conversations for different household users must not share thread state.

### FR-4: Shared household container (optional)

- Individual profiles stay per `user_id` / `container_tag`.
- There may be a lightweight **shared** household `container_tag` for facts that are explicitly stored as shared — not a substitute for per-user isolation.
- The agent must not invent a household roster or infer private relationships.

### FR-5: Unknown speakers

- If the agent cannot bind a turn to a `user_id`, it asks for clarification (e.g. “Which `user_id` should I use for this session?”).
- It must not guess a container.

## Non-Functional Requirements

- **Privacy**: One user’s private memories or conversations must never leak to another `user_id`.
- **Low friction**: Identification should feel like a one-time bind for the session, not a login on every turn.
- **Scalability**: Design supports additional `user_id` values without major rewrites.
- **Auditability** (future): It should be possible to see which `user_id` a memory belongs to.

## Open Questions

- How do we bootstrap known `user_id` values? (Config file vs first-time “register this id” flow.)
- Is there a default `user_id` (`DEFAULT_USER_ID`) for single-user sessions, or must every session declare one?
- Do we want speaker diarization / voice embeddings later (local, on-box)? Not v1.
- How do we handle unknown / guest speakers? A generic `guest` container vs refuse until identified.
- Optional shared household `container_tag`: what is allowed to be written there, and who can read it?

## Relationship to Feature 001

This feature extends the single-user voice agent in 001.

001 already assumed `container_tag` per user and `thread_id` per session. This spec is the extra work to make that a real multi-user experience: explicit identification, isolation guarantees, and unknown-speaker handling. It does not replace 001 and does not implement spec 004 (checkpointers).

## Success Criteria (when implemented)

- Distinct household users can keep separate ongoing conversations with correct memory recall.
- The agent does not mix one `user_id`’s context into another’s.
- Adding a new `user_id` is a low-effort configuration task.
- Identification is explicit first; no biometric path is required for v1.

---

**Status**: Design captured for planning. **Not** a shipped tenant model. The identity seam (`DEFAULT_USER_ID`, `get_agent(user_id)`, MemoryChat `/user`) is in the tree; speaker ID and product isolation are not.

See [plan.md](./plan.md) and [tasks.md](./tasks.md) for the SDD record of what exists vs what remains.
