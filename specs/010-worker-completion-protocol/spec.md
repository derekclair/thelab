# Feature Spec: Durable-board worker completion protocol

**Feature ID**: 010-worker-completion-protocol
**Status**: Living practice
**Created**: 2026-08-19
**Owner**: Derek Clair
**Related**: [009-architect-coder-handoff](../009-architect-coder-handoff/spec.md), [008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md)

## Record-keeping note

This is the workstation **fleet protocol**: how a durable-board worker is allowed to finish. It is already practiced on the desk. This folder is the SDD record in the brain repo so the rule is not only a local Hermes how-to.

It does **not** add a board to `thelab_langchain`. The current runtime is Hermes Kanban (see [plan.md](./plan.md)). The protocol outlives that runtime.

## Overview

Specialist workers (architect, researcher, coder, designer, reviewer) take durable cards from a board. Each run has exactly one legal finish:

1. **complete** — the card’s acceptance criteria are met, and the summary names concrete artifacts a human can open; or
2. **block** — the worker cannot proceed without a human (missing decision, failed gate, unsafe change).

A clean process exit with neither is a **protocol violation**. The card is not done. Downstream work must not treat silence as success.

## Goals

- Make terminal state unambiguous: complete or block, never “the process returned 0.”
- Make completed work inspectable: paths, PR URLs, test counts — not vibes.
- Keep secrets off the board (summaries, comments, metadata, artifact fields).
- Put durable work on durable workspaces; delete-on-complete scratch is only for throwaway probes.
- Dispatch only the real roster. Invented role names must not look like they are queued to run.
- Keep **human merge** as the definition of done for code.

## Non-goals

- A Kanban (or any board) implementation inside this Python package.
- CI in this repo that asserts complete/block (the fleet is not a thelab unit test).
- Vendoring the Hermes operating manual, CLI recipes, or chat/notification plumbing.
- Short in-conversation subagents (`delegate_task` and the like). Those die with the parent turn and are not this protocol.
- Changing spec 008’s hardware spike or this package’s `get_agent()` contract.

## User stories

1. As a worker, I finish by completing or blocking so the board never confuses a quiet exit with success.
2. As a human, I open a completed card and find artifacts I can verify (a spec path, a PR, a test count).
3. As a human, I never find keys, tokens, or env dumps in board fields.
4. As an architect, my spec still exists after the card completes because it was not on scratch.
5. As a dispatcher, I only assign names on the roster; a typo sits in ready instead of spawning a ghost worker.
6. As a coder, “I opened a PR” is not done — a human merges.

## Roster (closed)

Board dispatch uses **only** these roles:

| Role | Owns | Must not |
|------|------|----------|
| **orchestrator** | Decompose work, assign the roster, keep the board moving | Invent assignees; flood the board without a task graph |
| **architect** | Specs, architecture, plans | Product implementation |
| **researcher** | Sources, findings, comparisons | Product implementation |
| **coder** | Implementation from an accepted spec; branch, tests, PR | Merge; treat unreviewed work as done |
| **designer** | Visual / UI deliverables | Backend ownership |
| **reviewer** | Review only; approve or block with comments | Implement the fix |

Unknown role names are **not** dispatched. They remain in **ready** forever. That idle state is a routing bug, not a running worker.

Other chat profiles may exist on the workstation. They are not board assignees unless they are added to this table in a spec revision.

## Workspace kinds

| Kind | Use for | After **complete** |
|------|---------|-------------------|
| **scratch** | Throwaway probes only | **Deleted**. Never for durable specs, docs, or product code. |
| **durable directory** | Specs, plans, docs packages | Survives. This is where SDD lives. |
| **git worktree** | Code changes | Survives as a worktree / branch. Not a substitute for a PR + human merge. |

A card whose deliverable must be read later **must not** use scratch. Completing a spec card on scratch is a failed card even if the worker called complete.

## Functional requirements

### FR-1 Terminal action (non-negotiable)

- Every worker run **MUST** end with **complete** or **block**.
- Clean exit without either is a **protocol violation**.
- A violation MUST NOT be recorded as success. The runtime SHOULD trip a circuit breaker / auto-block so the card cannot look healthy.
- Reclaim and retry are operator actions after a violation; they do not rewrite history into “completed.”

### FR-2 Complete payload

On **complete**, the board-visible summary (and any artifact metadata) MUST include concrete, checkable items as they apply:

- Filesystem paths for specs/docs (durable directory).
- PR URL (and branch name if useful) for code.
- Test counts actually observed (e.g. `N passed` / `N failed`) — do not invent numbers.

Optional but useful: what was *not* done, if the accepted spec scoped it out.

### FR-3 Secrets stay off the board

Board fields (title, body, comments, complete summary, metadata, artifact lists) MUST NOT contain:

- API keys, tokens, OAuth material, `.env` contents
- Serials, phone numbers, personal IPs
- Chat/channel/DM identifiers
- Issue-tracker deep links that are private coordination, when a repo path or PR URL suffices

Secrets belong in the worker’s private environment, never in the card.

### FR-4 Block is a first-class finish

**block** is a legal, expected terminal action. The worker MUST say:

- what is blocked,
- what a human must decide or provide,
- what was already tried, if that is needed to unblock.

A reviewer who will not approve **blocks**. An architect who lacks a decision **blocks**. Stalling in-process hoping the parent notices is not a finish.

### FR-5 Definition of done (code)

For product code:

1. Architect spec accepted by a human.
2. Coder implements on a worktree / branch and opens a PR; coder **completes** with that PR and test evidence.
3. Reviewer **completes** (approve) or **blocks** (comments). Reviewer complete is not merge.
4. **A human merges.** That merge is the definition of done.

A completed coder card with an unmerged PR is *ready for review / merge*, not done.

For specs and docs on a durable directory, **complete** means the files are on disk at the named paths. Human review of the spec is still the gate before implementation (see FR-6).

### FR-6 Spec-first for non-trivial code

Non-trivial implementation is not assigned to coder until a human has accepted the spec. Reviewer does not write the product patch.

### FR-7 Handoff language

*What* to write in the card (tone, how to name artifacts, how to ask a human) is spec **009**. This spec is the *terminal action* and the workspace/roster rules. A well-worded silent exit still violates FR-1.

## Non-functional requirements

- Protocol is role- and runtime-agnostic: complete/block, workspace kinds, closed roster, human merge.
- Honest SDD: this package does not run the board; do not write tasks as if it will.
- No metrics theater: do not invent pass rates, latency, or fleet health numbers in this spec.

## Acceptance criteria

- [x] A worker that exits without complete or block is a protocol violation, not a successful card.
- [x] Complete summaries name artifacts (paths, PR URLs, and/or real test counts) and contain no secrets.
- [x] Scratch is never used for specs, docs, or product code that must survive the card.
- [x] Durable directory is the workspace for SDD; git worktree is the workspace for code.
- [x] Dispatch uses only orchestrator, architect, researcher, coder, designer, reviewer. Unknown names sit in ready.
- [x] Architect / researcher / reviewer / designer do not implement product code on their cards.
- [x] Code is done when a human merges, not when a worker completes.

## Relationship to other specs

- **009** — handoff *language* (how a worker talks on the card). This spec is the *protocol* (how a worker is allowed to stop).
- **008** — Lenovo Go voice I/O spike, executed in another repo. Same honesty rule: record where work actually lives; do not pretend this package owns it.
- **001 / 007** — product/hardware goals. This spec does not change them.

## What this spec is not

It is not a Hermes CLI manual. It is not a request to build `thelab_langchain.kanban`. It is not permission to treat chat-profile names as board roles.
