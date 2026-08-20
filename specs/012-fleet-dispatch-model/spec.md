# Feature Spec: Workstation fleet dispatch model

**Feature ID**: 012-fleet-dispatch-model
**Status**: Living practice (documented here; **not** a product feature of `thelab-langchain`)
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [009-architect-coder-handoff](../009-architect-coder-handoff/spec.md),
[010-worker-completion-protocol](../010-worker-completion-protocol/spec.md),
[007-dgx-hardware-optimization](../007-dgx-hardware-optimization/spec.md)

## Record-keeping note

This spec records **how work is routed** on the workstation: one front door, a
closed specialist roster, and three durability layers. The practice is already
in use. This folder is the SDD trail in the brain repo so later specs (and
humans) can see the model without opening a local operating manual.

It is **not** a dispatcher, CLI, gateway, LangGraph node, or CI gate in this
package. Runtime process control stays in Hermes. Do **not** copy Hermes
profile files, `SOUL.md`, or the fleet how-to into git. This document
**distills** the design.

Spec **009** is how architect and coder talk. Spec **010** is how a durable
worker is allowed to stop. Spec **007** is who may occupy the local inference
slot. This spec is **which layer** and **which role**.

## Overview

A human talks to **one orchestrator**. That agent answers small work itself,
spawns short-lived helpers that die with the turn, or decomposes larger work
onto a durable board for named specialists. The orchestrator does not pretend
to be every specialist.

Three layers:

1. **Conversation** — one orchestrator (front door). Questions, decisions,
   small one-shots.
2. **In-process subagent** — short parallel reasoning. Dies with the parent
   turn. Not inspectable later.
3. **Durable board** — specs, multi-lane work, review, anything a human may
   inspect, pause, or resume.

Rule of thumb: if a human might want to inspect, pause, or resume it later,
it belongs on the board. If it is a two-minute sub-question, answer it in
conversation or spawn an in-process subagent.

```
Human
  └─ orchestrator (conversation front door)
        ├─ answers / small one-shots
        ├─ in-process subagent  (dies with the parent turn)
        └─ durable board
              ├─ architect / researcher / designer
              ├─ coder
              └─ reviewer
Human accept (specs) and human merge (code) sit outside the roster.
```

## Goals

- Keep a single front door so the human is not picking specialists by filename.
- Route by durability: conversation vs in-process vs board.
- Dispatch only the closed roster. Invented names must not look queued to run.
- Keep the orchestrator as decomposer, not as a fake architect/coder/reviewer.
- Point non-trivial implementation at spec-first (009) and complete-or-block (010).
- Keep human merge as the definition of done for code.
- Stay honest: this package does not implement a dispatcher.

## Non-goals

- A dispatcher, board, worker runner, or gateway inside `thelab-langchain`.
- CI in this repo that asserts routing, roster names, or Hermes process health.
- Vendoring the Hermes operating manual, CLI recipes, gateway runbooks, or
  profile `SOUL.md`.
- Treating Hermes profile *filenames* as the product vocabulary. Roles are
  the product; filenames are a runtime mapping (see [plan.md](./plan.md)).
- Replacing 009 (handoff language), 010 (terminal action / workspace kinds),
  or 007 (inference slot / local vs hosted).
- Chat/notification plumbing, messenger delivery, or ticket-tracker IDs as
  required reading.
- Voice I/O, speakability, or a spoken ticket-filing tool (see 011 / 008).
- Inventing assignee names, latency numbers, or fleet health metrics.

## Domain terms (define once)

| Term | Meaning |
|------|---------|
| **Front door** | The single conversation the human uses day to day. The orchestrator. |
| **Orchestrator** | Role that answers small work, decomposes the rest, and assigns the roster. |
| **Layer** | One of: conversation, in-process subagent, durable board. |
| **Conversation** | The live turn with the orchestrator. Questions, decisions, small one-shots. |
| **In-process subagent** | A helper spawned inside the parent turn. Short parallel reasoning. Dies with that turn. Not a board worker. |
| **Durable board** | Cards that outlive a chat turn. Specs, multi-lane work, review, pause/resume. |
| **Roster** | The closed set of roles that may be assigned: orchestrator, architect, researcher, coder, designer, reviewer. |
| **Dispatch** | Choosing a layer and, for the board, a roster role plus a workspace kind (010). |
| **Task graph** | Named work with dependencies. Proposed before flooding the board. |
| **Assignee** | A roster role on a card. Not an invented string. Not a person’s family name. |
| **Spec-first** | Non-trivial implementation waits for a human-accepted spec (009). |
| **Complete-or-block** | Legal finishes for a board worker (010). Silent exit is a violation. |
| **Human merge** | Definition of done for product code. Worker complete is not merge. |

Do not reuse these words for other meanings in the same packet (for example,
do not call an in-process subagent a “board worker”).

## Roster (roles, not runtime filenames)

Board dispatch and specialist ownership use **only** these roles. Hermes
profile filenames are today’s wiring; they are not this spec’s names.

| Role | Owns | Must not |
|------|------|----------|
| **orchestrator** | Front door. Small one-shots. Decompose multi-step work. Assign the roster. Keep the board moving. | Pretend to be architect, coder, or reviewer. Invent assignees. Flood the board without a task graph. |
| **architect** | Specs, architecture, plans. | Ship product code. Open an implementation PR as the architect. |
| **researcher** | Sources, findings, comparisons. | Ship product code. Treat a research note as an accepted spec. |
| **coder** | Implementation from an **accepted** spec; branch, tests, PR. | Merge. Implement from chat only. Widen the spec. |
| **designer** | Visual / UI deliverables. | Backend ownership. Product implementation. |
| **reviewer** | Review only. Approve or block with comments. | Implement the fix. |

Unknown role names are **not** dispatched. They remain unstarted. That idle
state is a routing bug, not a running worker.

Other chat profiles may exist on the workstation (for example a spoken path).
They are not board assignees unless they are added to this table in a spec
revision.

The **human** is not a roster role and is not optional:

- Accepts or rejects the architect packet before code (009).
- Merges product code. That merge is done.
- Inspects, pauses, resumes, and unblocks board work.

## Layers

### 1. Conversation (orchestrator)

Use for questions, decisions, and small one-shots the orchestrator can finish
in the live turn. The human should not have to name a specialist filename to
get a straight answer.

The orchestrator may **propose** a task graph. Proposing is not the same as
doing the specialist work in chat. Long interactive sessions with a specialist
are the exception; auditable board handoffs are the default for multi-step work.

### 2. In-process subagent

Use for short parallel reasoning that only the parent turn needs. The helper
dies with that turn. It does not survive restart. It is not 010’s complete-or-block
protocol. It is not a place for specs, PRs, or review gates.

If a human might inspect, pause, or resume the work later, do **not** put it
here. Promote it to the board.

### 3. Durable board

Use for specs, multi-lane work, review, and anything that must outlive the
turn. Workers on this layer obey 010 (complete or block, workspace kinds,
secrets off the card). Architect → coder packets obey 009.

Standard shapes (not a command sheet):

**Spec → implement → review**

```
architect (durable directory, spec)
    → human accepts
    → coder (git worktree, PR + tests)
    → reviewer (approve or block)
    → human merges
```

**Research-heavy**

```
researcher (lane A)  ─┐
researcher (lane B)  ─┼─► architect (synthesize) ─► human accept ─► coder ─► reviewer ─► human merge
```

**Design + build**

```
designer ─┐
architect ─┴─► coder ─► reviewer ─► human merge
```

Research and design lanes still complete or block. They still do not land
product code.

## Decision table

| Request | Layer | Owner |
|---------|-------|--------|
| Quick question / small one-shot | Conversation | Orchestrator |
| Short parallel sub-question inside a turn | In-process subagent | Orchestrator-spawned helper; dies with the turn |
| What should we build / how? | Board | Architect → human accept |
| Look up / compare options (more than a glance) | Board | Researcher (architect synthesizes if it becomes a spec) |
| Implement the accepted spec | Board | Coder |
| Visual / UI deliverable | Board | Designer |
| Is this safe/correct to merge? | Board | Reviewer |
| Mix of the above | Conversation proposes a task graph → board | Orchestrator decomposes; specialists execute |

When in doubt, prefer the board over a long specialist chat.

## Functional requirements

### FR-1 Layer by durability

- Conversation: live, small, discarded with the turn except as ordinary chat history.
- In-process subagent: parallel, short, **dies with the parent turn**.
- Durable board: inspect / pause / resume / review / multi-lane.

### FR-2 Single front door

- Day-to-day human traffic hits the orchestrator.
- The orchestrator decomposes. It does not impersonate the rest of the roster.

### FR-3 Closed roster

- Dispatch uses only the six roles in the roster table.
- Invented assignee names are not dispatched. Idle-unstarted is the failure mode.

### FR-4 Spec-first for non-trivial code

- Non-trivial implementation is not assigned to coder until a human has accepted
  the spec (009).
- Architect, researcher, and designer do not ship product code.
- Reviewer never implements.

### FR-5 Board workers finish per 010

- Every board run ends **complete** or **block**.
- Clean exit with neither is a protocol violation, not success.
- Workspace kinds and secrets-off-the-card stay in 010. This spec does not
  restate the CLI.

### FR-6 Definition of done (code)

- Coder complete with a PR is *ready for review / merge*, not done.
- Reviewer complete is not merge.
- **A human merges.** That merge is done.

### FR-7 Model class follows 007

- Quality-critical roles (orchestrator, architect, reviewer, designer) use a
  **hosted** model so they do not occupy the Spark’s single local LLM slot.
- Coder and researcher **may** use the one local ~30B-class slot, with hosted
  fallback if the slot is busy or the local endpoint is down.
- Do not co-schedule a second serious local generative LLM. Do not run 120B+
  agent loops on one Spark. Numbers and harness work stay in 007.

### FR-8 This package does not dispatch

- `thelab-langchain` does not spawn specialists, persist cards, or own a
  gateway.
- Recording the model in `specs/012-fleet-dispatch-model/` is not
  implementing it.

## Non-functional requirements

- Protocol is role-first and runtime-agnostic. If the board product changes,
  keep the roles and layers; rewrite the runtime mapping in [plan.md](./plan.md).
- Honest SDD: practiced on Hermes; do not write tasks as if this package will
  grow a dispatcher.
- No metrics theater: do not invent pass rates, spawn latency, or fleet health
  numbers in this spec.
- No secrets, tracker IDs, or home-directory paths as the layout of record.

## User stories

1. As a human, I talk to one orchestrator for questions and small work.
2. As a human, I see multi-step work on a board I can inspect, pause, or resume.
3. As orchestrator, I decompose and assign the roster; I do not fake a code review.
4. As architect / researcher / designer, I deliver artifacts, not product patches.
5. As coder, I implement only an accepted spec and I do not merge.
6. As reviewer, I approve or block; I never implement the fix.
7. As a dispatcher, I never treat a typo as a worker.

## Acceptance criteria (for this SDD record)

- [x] This folder names the three layers and the closed roster as **roles**.
- [x] Status is “living practice,” not a `thelab-langchain` feature.
- [x] Spec-first points at 009; complete-or-block points at 010; local vs hosted
      points at 007.
- [x] Human merge is definition of done for code.
- [x] No Hermes how-to, CLI cheat sheet, `SOUL.md`, or profile file is copied here.
- [ ] A dispatcher, board, or gateway in this package — **not done** (out of scope).

## Relationship to other specs

- **009** — architect ↔ coder packet (spec, acceptance criteria, kanban body,
  blockers, residual risks, STE for procedures). 012 decides *that the work
  is a board architect card*, not how the packet is worded. 009’s non-goal of
  “the full fleet manual” is this spec.
- **010** — durable-board terminal action, workspace kinds, closed roster,
  human merge. 012 adds the conversation and in-process layers that 010
  explicitly excluded. Do not duplicate 010’s complete payload rules here.
- **007** — one local LLM slot; hosted models for quality-critical roles;
  coder/researcher may use the slot with hosted fallback. 012 does not pick
  weights or publish GB figures.
- **011** — voice-facing reply contract. Spoken multi-step coding/research
  escalates to this fleet (acknowledge; do not dump a patch through TTS).
  012 does not add a ticket tool to `get_agent()`.
- **008 / 001** — voice I/O spike and long-term voice-agent goal. Dispatch
  does not change their stacks.

## What this spec is not

It is not a Hermes CLI manual. It is not a request to build
`thelab_langchain.dispatch`. It is not permission to treat chat-profile
filenames as board roles. It is not a copy of `SOUL.md`.

## Open questions

- Whether a later spec should give the spoken path a **board escalation
  seam** in this package (011 Phase 3). Default until then: no ticket-filing
  tool on `get_agent()`.
- Whether conversation-layer “small one-shot” needs a hard size limit. Default:
  human judgment at the front door; when in doubt, board.
