# Feature Spec: Multi-User Support for the Voice Agent

**Feature ID**: 002-multi-user-support  
**Status**: Draft / Future  
**Related to**: [001-voice-dgx-spark-agent](../001-voice-dgx-spark-agent/spec.md)  
**Created**: 2025-05-21

## Overview

The voice agent should gracefully support multiple users within the same household (initially: Derek, wife, two daughters, son, and occasional "other" guests or family members).

Each person should have their own persistent identity and long-term memory context. When someone speaks to the agent, it should correctly identify who they are (or be told) and recall the right history, preferences, ongoing projects, and relationships.

This is a **cross-cutting concern** that affects user identification, Supermemory container isolation, session/thread management, the LangGraph state, and the overall voice experience.

## Goals

- Natural multi-user experience in a family setting.
- Strong long-term memory isolation per person (via Supermemory `container_tag`).
- Reasonable accuracy in knowing "who is talking" without constant re-identification.
- Future-proof for adding more family members or occasional guests.
- Maintain privacy boundaries between users.

## Non-Goals (for initial version)

- Full biometric voice fingerprinting / speaker diarization (nice to have later).
- Remote multi-user access from outside the home.
- Complex household roles/permissions system.
- Guest accounts with temporary memory.

## User Stories

1. **As Derek**, I want the agent to remember my ongoing projects, preferences, and conversations even when other family members have spoken to it recently.
2. **As my wife**, I want the agent to remember things that are important to me (kids' schedules, our shared tasks, etc.) without mixing them up with Derek's work stuff.
3. **As a kid**, I want the agent to know who I am when I talk to it and remember things like my homework, favorite games, or ongoing stories.
4. **As a parent**, I want to be able to say "Hey Lab, this is Sarah talking" or have the system figure it out reasonably well.
5. **As the household**, we want the agent to understand family relationships ("my sister", "Dad", "the kids") when context is relevant.

## Functional Requirements

### FR-1: User Identity & Routing
- The system must be able to associate a voice interaction with a specific user identity.
- Supported identification methods (in rough priority order):
  1. Explicit declaration ("Hey Lab, it's Derek")
  2. Wake-word + name patterns
  3. Heuristic / voice characteristics (future)
  4. Device or room context (if multiple microphones are added later)

### FR-2: Memory Isolation (Supermemory)
- Every user must have their own `container_tag` in Supermemory.
- All `profile()`, `add()`, and `search` calls must be correctly scoped to the identified user.
- Cross-user leakage must be prevented (the agent should not accidentally recall one person's private facts to another).

### FR-3: Session & Thread Management
- Each user should have their own conversation threads (`thread_id`).
- Short-term memory (LangGraph checkpointer) must be isolated per user.
- It should be possible to have parallel conversations with different family members.

### FR-4: Relationship & Household Context
- The agent should be able to reason about family relationships when given the right context ("Tell my wife...", "What does Dad usually say about this?").
- There may be a lightweight "household" or "family" memory layer in addition to individual profiles.

### FR-5: Graceful Handling of Unknown Speakers
- If the agent cannot confidently identify the speaker, it should ask for clarification in a friendly way ("Sorry, I didn't catch who I'm speaking with — is this Derek, Sarah, or one of the kids?").

## Non-Functional Requirements

- **Privacy**: One family member's private memories or conversations must never leak to another.
- **Low Friction**: Identification should feel natural, not like logging into a system every time.
- **Scalability**: Design should support adding more users without major rewrites.
- **Auditability** (future): It should be possible to see which user a memory belongs to.

## Open Questions

- How do we initially bootstrap user identities? (Manual config file? First-time "register yourself" flow?)
- Should there be a concept of a "primary user" (Derek) who has elevated capabilities?
- Do we want speaker diarization / voice embedding models running locally on the DGX for passive identification?
- How do we handle "other" / guests? Temporary containers? A generic "guest" profile?
- Should the agent proactively learn voices over time ("You sound like Maya today")?

## Relationship to Feature 001

This feature is a natural evolution of the single-user voice agent defined in 001.

The core architecture decisions made in 001 (Supermemory `container_tag` per user, `thread_id` per session, LangGraph state) were intentionally designed to be multi-user friendly. This spec captures the additional work needed to make the experience truly multi-user in a family context.

## Success Criteria (for when we eventually implement)

- Derek, his wife, and both kids can have natural, separate ongoing conversations with the agent over weeks/months with correct memory recall.
- The agent rarely confuses one person's context with another's.
- Adding a new family member is a low-effort configuration task.
- The experience feels personal and "knows" each person without feeling creepy or overly technical.

---

**Status**: This spec is captured for future planning. It is **not** in scope for the current implementation wave.

Next time we pick up multi-user work, we should create a `plan.md` and `tasks.md` under this directory following the established SDD process.