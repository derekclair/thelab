# Plan: Reviewer quality gate (013)

**Feature**: 013-reviewer-quality-gate
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20

## 1. What this plan is

A map of **who reviews what, how findings are written, and how the gate
finishes**. It is not a plan to add a reviewer bot to `thelab-langchain`.

Success is a practiced gate: structured findings, no reviewer patches, complete
or block, human merge. This repo only records the contract.

Living practice sits in the Hermes reviewer specialist. GitHub pull-request
review is the public analog for this repository.

## 2. Review flow

```
accepted packet (009) + coder deliverable (PR or spec files)
        │
        ▼
 reviewer applies lenses
   correctness · security · privacy
   SDD completeness · tests · acceptance criteria
        │
        ├── no blocker/major → complete (approve)
        │         residual risks stay documented
        │         minors/notes optional follow-up for coder
        │
        └── blocker or major, failed lens, or missing evidence
                  → block (findings + fix guidance)
                  → follow-up card for coder (or architect if packet is wrong)
                  → reviewer does not patch
        │
        ▼
 human merges code (010). Reviewer complete ≠ merge.
```

### Step 1 — Orient

The reviewer reads the accepted spec, acceptance criteria, residual risks, and
the actual artifact (diff or spec files). The implementer’s summary is a claim,
not proof.

### Step 2 — Apply lenses

All six lenses. Security-sensitive and user-facing changes cannot skip
security, privacy, or user-facing correctness. A pass with those lenses
unexamined is a rubber-stamp.

### Step 3 — Write findings

Each finding: severity, location, fix guidance. STE for pass/fail and fix
lines. Short prose for the verdict narrative. No secrets in the text.

### Step 4 — Finish

Complete or block (010). If a fix is required, the reviewer creates or returns
work to the **coder**. The reviewer does not implement.

### Step 5 — Human merge (code)

A human merges. That is done.

## 3. Hermes practice vs GitHub analog

Abstract spec terms map as follows. Profile models, CLI flags, and gateway
startup stay in the local Hermes manual (not vendored).

| Spec term | Hermes fleet (current runtime) | GitHub public analog |
|-----------|--------------------------------|----------------------|
| Reviewer | Reviewer specialist; never implements | PR reviewer (human). This package has **no** bot. |
| Workspace | Same tree as the change (010) | The PR branch |
| Finding | Card comment: severity, location, fix guidance | Inline or summary PR comment, same shape |
| **Complete** | Board complete + short evidence summary | Approve (or comment if only minors/notes) |
| **Block** | Board block + findings | Request changes |
| Follow-up | Card for **coder** | Same PR; coder addresses review |
| Done (code) | Human merge | Human merge |

If the board product changes, keep the spec terms and rewrite the Hermes
column. Do not fork a second severity scale.

GitHub review without a board is still a valid analog for public PRs on this
repo. When the work *is* on the board, 010 still requires complete or block;
a GitHub comment does not replace the terminal action.

## 4. What is STE vs human prose

| Text | Language |
|------|----------|
| This SDD folder | Human prose |
| Finding issue + fix guidance | STE |
| Severity and location labels | The four severity words; path or section |
| Verdict narrative (“what was inspected”) | Human prose, short |
| Complete/block summary evidence (paths, PR URL, observed test counts) | Facts; no vibes (010) |

Skill `asd-ste100` remains the procedure reference (009). Skills `code-review`
and `security-scan` may be named at dispatch. Do not paste skill bodies into
the packet or this repo.

## 5. Follow-up routing

| Highest finding | Reviewer does | Coder does |
|-----------------|---------------|------------|
| blocker or major | **Block.** Do not patch. | Fix **this** change; request review again. |
| minor only | **Complete** allowed. Optional follow-up card. | Optional later fix. |
| note only | **Complete.** | Nothing required. |
| Packet incomplete / design wrong | **Block.** Follow-up is **architect**, not a silent coder redesign. | Do not implement from a blocked packet. |

The reviewer never takes the follow-up card.

## 6. What this repo does and does not run

| Mechanism | Status |
|-----------|--------|
| Hermes reviewer specialist | Practiced on the workstation (outside this repo) |
| SDD record in `specs/013-reviewer-quality-gate/` | This folder |
| GitHub PR review by a human | Public analog; already how this repo merges |
| Reviewer bot / GitHub Action that posts a verdict | **Not done** |
| CI that lints finding shape or blocks merges without a reviewer assignee | **Not done** |
| Runtime enforcement in `thelab-langchain` | Out of scope |

Do not add a review agent, webhook, or “auto-approve” job under this spec.

## 7. Relationship to 009, 010, 012

- **009** supplies the packet the reviewer ticks. This plan does not change
  STE rules of thumb or the five artifacts.
- **010** supplies complete/block, roster, workspace kinds, and human merge.
  Reviewer workspace stays the same tree as the change.
- **012** routes the reviewer onto the durable board. This plan is the gate
  that specialist runs; it does not restate dispatch layers.

Work toward 001/008 still uses this gate. 013 does not pick ASR/TTS stacks.

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Reviewer implements “a small fix” | FR-1: review only; follow-up is coder |
| Rubber-stamp on security or user-facing work | FR-2: lenses required; complete without them is a failed review |
| Vague “needs work” | Finding shape: severity, location, fix guidance |
| Chat LGTM replaces the gate | 010: silent exit is a violation; human merge still required |
| Secrets copied into findings | Privacy lens; redact; never paste values |
| This spec treated as a bot to build | Status: living practice; no reviewer module here |
| Reviewer complete treated as ship | 010 FR-5: human merge |

## 9. Success (qualitative)

No invented metrics. The gate is working when:

- Findings a coder can open (path, severity, what to change).
- Blocked reviews name the human or coder action required.
- Approved reviews name what was actually inspected.
- Reviewer diffs contain no product patches from the reviewer role.
- Merged PRs, not completed review cards, are what landed in `main`.

## 10. What this plan is not

It is not a Hermes CLI cheat sheet. It is not a request to vendor a reviewer
profile into git. It is not spec 005’s pytest job. It is not permission to
skip human merge because a specialist approved.
