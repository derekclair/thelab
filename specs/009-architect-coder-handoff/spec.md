# Feature Spec: Architect ↔ coder inter-agent handoff (STE)

**Feature ID**: 009-architect-coder-handoff
**Status**: Living practice (documented here; **not** a product feature of `thelab-langchain`)
**Created**: 2026-08-19
**Owner**: Derek
**Related**: [001-voice-dgx-spark-agent](../001-voice-dgx-spark-agent/spec.md), [008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md)

## Record-keeping note

This spec records a **workstation practice**: two Hermes profiles (`dgx-architect` and `dgx-coder`) hand work to each other through written artifacts. The practice is already in use. This folder is the SDD trail in the brain repo so later specs (and humans) can see the contract.

It is **not** a library, CLI flag, LangGraph node, or CI gate in this package. Spec 008’s spike ran out of tree; this protocol is how design and implementation stay split when that kind of work happens again. Spec 001 remains the long-term voice-agent goal. This spec does not change 001’s stack.

Do **not** treat Hermes profile files, skill bodies, or an ASD dictionary as part of this repo. Those live outside git. This document **distills** the design.

## Overview

An **architect** agent designs. A **coder** agent implements. A **human** accepts the design before code is written. The packet that crosses the gap is a small, named set of artifacts. Procedure text that an agent must follow is written in Simplified Technical English (ASD-STE100 **principles** — see rules of thumb below). Rationale, trade-offs, and user-facing prose stay in ordinary English.

The full controlled-language skill is **`asd-ste100`**. It lives outside this repo (`~/.agents/skills/asd-ste100`, and the Grok skill of the same name). Reference the skill by name. Do not paste the skill body or the ASD dictionary into specs, PRs, or kanban text.

## Goals

- Keep design and implementation in different roles so the coder does not invent architecture.
- Make the handoff packet complete enough that a coder can start without a chat transcript.
- Put agent-consumed procedures in STE so instructions have one meaning.
- Leave a human accept gate between “designed” and “implement this.”
- Document residual risk instead of hiding it in chat.

## Non-goals

- A product feature, API, or runtime mode inside `thelab-langchain`.
- CI that lints STE, blocks merges, or assigns Hermes profiles (see [tasks.md](./tasks.md) — **not done**).
- The full workstation fleet manual (orchestrator, researcher, reviewer, kanban-vs-chat). That stays in Hermes docs, not this spec.
- Copying profile `SOUL.md`, Hermes env files, or the ASD-STE100 dictionary into git.
- Marketing copy, README voice, or human design rationale written as STE.
- Telephony, hosted voice, or unpublished-company product framing.

## Roles

| Role | Does | Does not |
|------|------|----------|
| **Architect** (`dgx-architect`) | Designs. Writes the spec, acceptance criteria, kanban body, blockers, and residual risks. Names seams and out-of-scope work. | Implement. Open an implementation PR. “Just quickly” patch production code. Expand into researcher or reviewer work. |
| **Coder** (`dgx-coder`) | Implements **accepted** specs only. Follows the kanban body and acceptance criteria. Reports new blockers. Stops at the spec’s edge. | Redesign. Implement from chat only. Widen scope. Silently drop acceptance checks. |
| **Human** | Accepts or rejects the design packet. Resolves product calls the architect flagged. Reviews the result against acceptance criteria (alone or with a reviewer). | Skip the accept gate “because the architect was confident.” |

The architect never implements. The coder never treats an unaccepted draft as a build order.

## Domain terms (define once)

Use these words with one meaning in handoff artifacts:

| Term | Meaning |
|------|---------|
| **Spec** | The design document the architect writes. It states what to build, what not to build, and which seams stay stable. |
| **Acceptance criteria** | Binary checks. The implementation passes or it fails. No “should feel faster.” |
| **Kanban body** | The work-item text the coder **consumes**. Procedure, not a status emoji. |
| **Blocker** | A condition that prevents start or completion. Named, owned, and either cleared or carried. |
| **Residual risk** | A known remaining risk after the human accepts the design. Not a surprise at review. |
| **Handoff** | The packet: spec + acceptance criteria + kanban body + blockers + residual risks, in the accepted state. |
| **Human accept** | The gate. A person marks the packet accepted. Only then may the coder implement. |
| **STE** | Simplified Technical English using ASD-STE100 principles (rules of thumb in this spec). The `asd-ste100` skill is the procedure reference. |

Do not reuse these words for other meanings in the same packet (for example, do not call a brainstorm a “spec”).

## Handoff artifacts

Every architect → coder handoff includes all five. If one is missing, the packet is not ready for human accept.

### 1. Spec

- States goals, non-goals, seams, and the smallest change that meets the goal.
- Human prose is allowed for *why*.
- If the spec contains a procedure the coder must execute, that procedure is STE.

### 2. Acceptance criteria

- Written as checks a reviewer can tick.
- Each criterion is one testable outcome.
- No latent numbers, no invented latency targets, no “as before unless it is better.”

### 3. Kanban body

- The instruction the coder follows.
- STE. Numbered steps when there are three or more.
- Points at the spec and the acceptance criteria. Does not replace them.
- Does not embed secrets, tokens, host layout paths, or board/issue identifiers as required reading.

### 4. Blockers

- What must be true before implementation starts, or what will stop it mid-flight.
- Each blocker is a fact (missing seam, unaccepted dependency, out-of-tree repo not ready), not a mood.

### 5. Residual risks

- What remains wrong or fragile if the coder meets every acceptance criterion.
- The reviewer reads this list. The coder does not “fix” residual risk unless the accepted spec says so.

## STE rules of thumb

These are **principles** for agent-consumed procedures. They are not a substitute for the `asd-ste100` skill and not a copy of the ASD dictionary.

1. **One meaning per word.** Pick a term from the table above (or define a new domain term **once**) and keep it.
2. **Active voice.** “The coder writes the factory.” Not “the factory should be written.”
3. **Simple tense.** Give instructions in the present or imperative. Do not stack conditionals.
4. **One instruction per sentence.**
5. **Short sentences.** Split a long sentence.
6. **Numbered lists for 3+ steps.** Do not hide a sequence in a paragraph.
7. **Noun clusters ≤ 3 words.** Prefer “checkpointer factory” to “optional session persistence checkpointer factory helper.”
8. **Define domain terms once.** Then use the defined word.

STE is for **agent-consumed procedures** (kanban bodies, implementation steps, acceptance checks). It is **not** for marketing copy, README tone, or the “why we chose this” sections of a spec.

## Functional requirements

### FR-1 Role split

- Architect output is design artifacts only.
- Coder input is an **accepted** handoff packet.
- Unaccepted drafts are not implementation tasks.

### FR-2 Packet completeness

- Human accept is refused if any of the five artifacts is missing or is a placeholder.
- The kanban body must not be the only copy of the spec.

### FR-3 Language split

- Procedures the coder or another agent must follow: STE, skill `asd-ste100`.
- Human rationale, status notes, and this SDD folder: ordinary prose.

### FR-4 Stop conditions

- The coder stops when acceptance criteria are met or a new blocker appears.
- Scope not in the spec is out of scope, including “obvious” refactors.

### FR-5 Secrets and layout

- Handoff text must not require API keys, tokens, hardware serials, board/chat identifiers, or absolute home-directory paths as the layout of record.
- Point to gitignored env examples and documented seams (`get_agent()`, provider factory) instead.

## Non-functional requirements

- The protocol is practiced in Hermes profiles `dgx-architect` and `dgx-coder` on the workstation.
- This repository **does not** enforce the protocol in CI.
- Specs in `specs/` remain human-readable SDD. They may *describe* STE; they need not be written entirely in STE.
- No latency or throughput numbers unless a later spec measures them.

## User stories

1. As architect, I hand a complete packet to a human so the coder never has to reconstruct the design from chat.
2. As human, I accept or reject before anyone writes production code.
3. As coder, I implement only what the accepted spec and kanban body say, in STE steps I can follow without guessing synonyms.
4. As reviewer, I tick acceptance criteria and read residual risks instead of rediscovering them.

## Acceptance criteria (for this SDD record)

- [x] This folder contains `spec.md`, `plan.md`, and `tasks.md` that name the two roles, the five artifacts, the STE rules of thumb, and the `asd-ste100` skill **by name only**.
- [x] Status is “living practice,” not a `thelab-langchain` feature.
- [ ] CI in this repo lint-checks STE or blocks coder PRs that lack an accepted packet — **not done** (out of scope until a later spec).
- [x] No Hermes profile file, skill body, or ASD dictionary is copied into this repo.

## Relationship to other specs

- **001** — long-term voice agent. Handoffs for work *on* 001 follow this protocol. This spec does not revise 001’s ASR/TTS/NIM choices.
- **008** — Lenovo Go spike, **executed out of tree**. The spike is the example of implementation living outside this package while the brain seam stays here. Future out-of-tree work should still cross this handoff, not a chat paste.
- **004 / 005** — checkpointers and CI remain their own specs. 009 does not implement them and does not claim CI enforcement.

## Open questions

- Whether a later spec should add a lightweight “packet complete?” checklist in PR templates (still not CI).
- Whether reviewer-agent output must also be STE. Default until decided: **acceptance write-up in human prose; fail/pass lines in STE.**
