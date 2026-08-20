# Feature Spec: Reviewer quality gate

**Feature ID**: 013-reviewer-quality-gate
**Status**: Living practice (documented here; **not** a product feature of `thelab-langchain`)
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [009-architect-coder-handoff](../009-architect-coder-handoff/spec.md),
[010-worker-completion-protocol](../010-worker-completion-protocol/spec.md),
[012-fleet-dispatch-model](../012-fleet-dispatch-model/spec.md)

## Record-keeping note

This spec records the **reviewer quality gate**: how a review specialist judges
specs and pull requests, how findings are written, and how the gate may finish.

The practice is already used on the workstation fleet (Hermes reviewer
profile). This folder is the SDD trail in the brain repo so the rule is not
only a local profile note.

This package has **no reviewer bot**, no review LangGraph node, and no CI job
that posts a verdict. GitHub pull-request review on this repo is the **public
analog**: a human (or a forge reviewer) leaves structured comments; a human
still merges.

Do **not** copy a Hermes profile `SOUL.md`, skill body, or operating manual
into this tree. This document **distills** the gate.

## Overview

A **reviewer** reads the deliverable and the accepted packet. The reviewer does
not ship the fix. The job is a quality gate, not a second coder.

The gate applies to:

- **Specs / SDD** (durable directory): completeness, honesty, acceptance
  criteria, residual risks.
- **Pull requests / code** (git worktree): correctness, security, privacy,
  tests, and match to accepted acceptance criteria.

Every finding has a **severity**, a **location**, and **fix guidance**. The
reviewer always **completes** or **blocks** (spec 010). A quiet exit is a
protocol violation. Reviewer complete is not merge. A human merges.

## Goals

- Keep review and implementation in different roles.
- Make the gate’s lenses explicit: correctness, security, privacy, SDD
  completeness, tests, acceptance criteria.
- Make findings actionable: severity, location, what to change.
- Stop rubber-stamps on security-sensitive or user-facing work.
- Finish every review run with complete or block; keep human merge as done
  for code.

## Non-goals

- A reviewer service, bot, or module inside `thelab-langchain`.
- CI in this repo that assigns a reviewer profile or posts a verdict.
- Vendoring Hermes profile files, skill bodies, or the fleet operating manual.
- The architect ↔ coder packet language (that is spec 009).
- The complete/block terminal itself (that is spec 010). This spec says how
  the **reviewer** uses that terminal.
- Coverage percentages, latency SLOs, or invented pass rates.
- Permission for the reviewer to “just quickly” patch the branch.

## Roles

| Role | Does | Does not |
|------|------|----------|
| **Reviewer** | Reviews specs and PRs. Writes structured findings. Completes (approve) or blocks. Opens a follow-up card for the **coder** when a fix is required. | Implement the fix. Merge. Accept the design in place of the human. Rubber-stamp security-sensitive or user-facing changes. |
| **Coder** | Implements the accepted spec, including fixes the reviewer required. | Review their own PR as the quality gate. Merge. |
| **Architect** | Designs; names residual risks the reviewer will read. | Implement. Wear the reviewer hat on the same packet they just wrote without an independent pass. |
| **Human** | Accepts the design packet (009). Merges code (010). May also review. | Treat reviewer complete as ship. Skip the gate on security-sensitive or user-facing work because the coder was confident. |

The reviewer never implements. A required fix is a **coder** follow-up (same
PR / returned card for blocker and major; optional later card for minor).

## Domain terms (define once)

| Term | Meaning |
|------|---------|
| **Quality gate** | The review pass on a spec or PR before the next legal step (human accept of a spec is 009; human merge of code is 010). |
| **Finding** | One issue. It has severity, location, and fix guidance. |
| **Location** | Path and line, or spec section heading. Enough for a coder to open the artifact. |
| **Fix guidance** | What must change. Not a pasted patch from the reviewer. |
| **Blocker** | Must be fixed before merge (code) or before human accept / coder start (spec). |
| **Major** | Must be fixed in **this** PR (or this spec revision). Not a later card. |
| **Minor** | Nit. Follow-up card is allowed. Does not by itself block complete. |
| **Note** | Non-blocking observation. No fix required. |
| **Rubber-stamp** | Approve without applying the required lenses, especially on security-sensitive or user-facing changes. |
| **User-facing** | Anything a person at the desk sees or hears: CLI text, docs, spoken replies (011), UI. |
| **Security-sensitive** | Auth, secrets, privacy, untrusted input, tool/exec boundaries, network exposure. |
| **Public analog** | GitHub PR review: comments and approve / request-changes. Same gate, different surface. Not a bot in this package. |
| **Follow-up card** | Work for the **coder** that exists because review found a defect. The reviewer does not take that card. |

Do not call a chat “LGTM” a finding. Do not call reviewer complete “merged.”

## Severity scale

| Severity | Meaning | Effect on the gate |
|----------|---------|-------------------|
| **blocker** | Must fix before merge (code) or before the packet is ready (spec). | **Block.** Do not approve. |
| **major** | Must fix in this PR / this spec revision. | **Block.** Do not approve. Follow-up is the same change, not a later PR. |
| **minor** | Nit. Follow-up OK. | Complete is allowed. Optional coder follow-up card. |
| **note** | Non-blocking observation. | Complete is allowed. No fix required. |

If both a blocker and a note exist, the gate is **block**. The highest
severity present wins.

Residual risks named by the architect (009) are **not** automatic blockers.
Unstated scope, failed acceptance criteria, and new security/privacy defects
**are**.

## Finding shape

Each finding is structured. Missing any field is an incomplete finding.

1. **Severity** — blocker, major, minor, or note.
2. **Location** — `path:line` or spec section. No private board/chat
   identifiers required. No secret values.
3. **Issue** — one sentence. What is wrong. STE for this line.
4. **Fix guidance** — one or more sentences. What the coder (or architect,
   if the packet is wrong) must change. STE. Not the implementation.

Pass/fail lines are STE. The short verdict narrative may be ordinary prose
(009 default, now the rule here).

Do not paste keys, tokens, serials, or other secrets into a finding. Name the
class of leak and the location. Redact values.

## Check lenses

The reviewer applies all of these. Skipping a lens on security-sensitive or
user-facing work is a rubber-stamp.

### Correctness

- The change does what the accepted spec claims.
- Edge cases and error paths that the spec named are handled.
- Unstated work is fail (scope creep) or a new spec, not a silent extra.

### Security

- No secrets in the diff, specs, tests, comments, or board fields (010 FR-3).
- Untrusted input is not passed to shell, SQL, or path joins without a check.
- Authz and tool boundaries match the spec. Do not invent a threat model that
  the spec did not ask for; do report an obvious hole.

### Privacy

- No keys, serials, private chat/issue identifiers, family data, or host home
  paths as required layout in the change or in the review text.
- Findings themselves obey this rule.

### SDD completeness

- Specs under review have honest status, goals, non-goals, and binary
  acceptance criteria.
- Architect → coder packets still have the five artifacts (009).
- Related specs are cited; this package is not claimed to own out-of-tree
  work (008 honesty).

### Tests

- New behavior has tests, or the spec explicitly waived them.
- Tests assert behavior, not a snapshot of source text.
- Observed test counts only (010). Do not invent coverage.

### Acceptance criteria

- Each accepted criterion maps to evidence the reviewer actually inspected.
- A criterion with no evidence is not a pass.
- “Looks good” is not evidence.

## Verdicts

Exactly one terminal action (010):

| Verdict | When | Board | GitHub public analog |
|---------|------|-------|----------------------|
| **Complete** (approve) | No blocker, no major. Lenses applied. Evidence named. | Complete with a short summary and artifact list. | Approve, or comment if only minors/notes. |
| **Block** | Any blocker or major, failed lens on security-sensitive / user-facing work, missing evidence, or a human decision is required. | Block. Findings on the card. Follow-up for **coder** (or architect if the packet is wrong). | Request changes. Same findings as inline or summary comments. |

Reviewer complete **is not merge**. Human merge remains the definition of done
for code (010 FR-5).

A GitHub comment-only review with no board complete/block is still a
**protocol violation** when the work is on the durable board. The analog is
the comment shape, not permission to go silent.

## Functional requirements

### FR-1 Review only

- Reviewer output is findings and a verdict.
- Reviewer MUST NOT edit product code, specs under review, or tests to “help.”
- Required fixes go to a **coder** follow-up card (blocker/major: this change;
  minor: optional later card).

### FR-2 Lenses

- Every review of a spec or PR MUST consider correctness, security, privacy,
  SDD completeness, tests, and acceptance criteria.
- Security-sensitive or user-facing changes MUST NOT be completed unless those
  lenses were actually applied. Rubber-stamp is a failed review.

### FR-3 Structured findings

- Each finding MUST include severity, location, and fix guidance.
- Severity MUST be one of: blocker, major, minor, note.
- Findings MUST NOT contain secrets or private coordination identifiers.

### FR-4 Complete or block

- The reviewer run MUST end with **complete** or **block** (010 FR-1).
- Clean exit with neither is a protocol violation, not an implicit approve.

### FR-5 Human merge

- Reviewer approve does not land the PR.
- A human merges. That merge is done for code.

### FR-6 Spec vs PR

- Spec review: packet completeness and honesty; block if the five artifacts
  or binary acceptance criteria are missing when 009 applies.
- PR review: diff against the **accepted** spec; block if acceptance criteria
  fail or the coder redesigned in the PR.

## Non-functional requirements

- Practiced as the Hermes reviewer specialist on the workstation. This
  repository does not run that profile.
- Specs in `specs/` remain human-readable SDD. Finding *lines* on a card are
  STE; this folder is prose.
- No reviewer metrics theater (approval rate, mean time to review).
- Skill names `code-review` and `security-scan` may be used at dispatch.
  Do not vendor those skill bodies here.

## User stories

1. As reviewer, I only judge the artifact; I never become the coder on the
   same card.
2. As coder, I get findings I can open (path, severity, what to change), not
   “needs work.”
3. As human, I still merge; a green review card is not ship.
4. As human, security-sensitive and user-facing changes are not rubber-stamped.
5. As architect, residual risks I named are read, not silently “fixed” by the
   reviewer.

## Acceptance criteria (for this SDD record)

- [x] This folder contains `spec.md`, `plan.md`, and `tasks.md` that name
      review-only, the four severities, structured findings, the six lenses,
      complete-or-block, and human merge.
- [x] Status is “living practice,” not a `thelab-langchain` feature.
- [x] Honest that this package has no reviewer bot; GitHub PR review is the
      public analog.
- [x] No Hermes profile file or skill body is copied into this repo.
- [ ] CI or a bot in this package that runs the reviewer — **not done**
      (out of scope until a later spec).

## Relationship to other specs

- **009** — handoff language and packet. Reviewer ticks acceptance criteria
  and reads residual risks. Fail/pass lines in STE; narrative in prose
  (closes 009’s open question for reviewer output).
- **010** — terminal action, roster, workspace, human merge. Reviewer is on
  the closed roster and MUST complete or block. This spec is *how* that
  role reviews.
- **012** — who is dispatched and on which layer. Reviewer is a **durable
  board** specialist, not an in-process subagent and not the orchestrator.
  This spec is *how* that role reviews; 012 does not define severity or
  finding shape.
- **005** — tests and CI for this package’s Python. Reviewer checks test
  *gaps* against the accepted spec; 013 does not add a coverage gate.
- **007** — quality-critical roles. Model routing stays there / in Hermes,
  not in this spec.
- **011** — spoken replies are user-facing. A voice-facing change is not
  rubber-stamped.
- **008** — out-of-tree I/O spike. Review of that work still does not
  implement, and still does not pretend this package owns playback.

## Open questions

- Whether a later spec should add a GitHub Action that only *checks* “PR has
  a human review,” still not a reviewer bot. Default: **not in 013**.
- Whether minor-only GitHub reviews should be Approve or Comment. Default:
  **Approve or Comment is allowed; board complete is still required.**
