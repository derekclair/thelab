# Plan: Architect ↔ coder inter-agent handoff (009)

**Feature**: 009-architect-coder-handoff
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-19

## 1. What this plan is

A map of **who writes what, in which language, and in which order**. It is not a plan to add modules to `thelab-langchain`. Success is a practiced loop, not a merged feature flag.

Living practice sits in Hermes profiles `dgx-architect` and `dgx-coder`. This repo only records the contract.

## 2. Handoff flow

```
architect writes packet
        │
        ▼
 human accept  ──reject──► architect revises packet
        │ accept
        ▼
 coder implements accepted spec only
        │
        ▼
 review against acceptance criteria
        │
        ├── pass → close work; residual risks stay documented
        └── fail or new blocker → architect (redesign) or coder (fix),
            only inside the accepted spec
```

### Step 1 — Spec (architect)

The architect writes the design. Human prose for goals, non-goals, and trade-offs. STE for any procedure the coder must run. The architect does not open an implementation branch as the architect.

### Step 2 — Human accept

A person reads the five artifacts. Accept means: the coder may implement **this** packet. Reject means: the architect revises. Chat agreement without the packet is not accept.

### Step 3 — Implement (coder)

The coder follows the kanban body and the spec. The coder does not add architecture. If the packet is wrong, the coder files a blocker and stops. The coder does not “fix the spec in the PR.”

### Step 4 — Review

A human (and optionally a reviewer agent) ticks acceptance criteria. Residual risks are not automatic fail. Unstated work is fail (scope creep) or a new spec, not a silent extra commit.

## 3. Where text is STE vs human prose

| Text | Language | Why |
|------|----------|-----|
| This SDD folder (`spec.md` / `plan.md` / `tasks.md`) | Human prose | Humans read rationale. STE is the wrong register for “why.” |
| Spec overview, goals, non-goals, relationships | Human prose | Design argument. |
| Spec procedures the coder must execute | STE | Agent-consumed. Skill `asd-ste100`. |
| Acceptance criteria | STE (one check per line) | Reviewer ticks; no synonyms. |
| Kanban body | STE | Primary coder input. Numbered lists for 3+ steps. |
| Blockers | STE facts | “X is missing.” Not “we should maybe wait.” |
| Residual risks | Human prose is allowed; names stay one-meaning | Risk needs context; do not hide it in hedges. |
| README / marketing / user docs | Human prose | STE is **not** marketing copy. |
| Review pass/fail lines | STE | “Criterion FR-2 fails. The factory is missing.” |
| Review narrative | Human prose | What was tried, what was out of scope. |
| Chat between humans | Human prose | Chat is not the packet. |

The skill **`asd-ste100`** (agents skill `~/.agents/skills/asd-ste100`, Grok skill `asd-ste100`) is the procedure reference. Do not paste the skill body or the ASD dictionary into the packet.

## 4. Packet shape (architect output)

The architect produces, in one place the coder can fetch:

1. **Spec** — design. Link or body. Seams named (`get_agent()`, editable install, env examples) without host home paths as required layout.
2. **Acceptance criteria** — tick list. No invented latency numbers.
3. **Kanban body** — STE steps. Points at (1) and (2).
4. **Blockers** — empty list is allowed if explicitly written as “none.”
5. **Residual risks** — empty list is allowed if explicitly written as “none.”

“None” written is complete. A missing section is not.

## 5. Coder constraints

- Implement **accepted** specs only.
- Do not implement from an architect draft, a voice transcript, or a chat summary.
- Do not copy Hermes profile files into the worktree.
- Stop at the spec’s edge. Out-of-tree work (as in spec 008) stays out of tree; this package keeps the brain seam only.

## 6. What this repo does and does not run

| Mechanism | Status |
|-----------|--------|
| Hermes profiles `dgx-architect` / `dgx-coder` | Practiced on the workstation (outside this repo) |
| SDD record in `specs/009-architect-coder-handoff/` | This folder |
| CI lint of STE | **Not done** |
| CI that requires an accepted packet | **Not done** |
| Runtime enforcement in `thelab-langchain` | Out of scope |

Do not add a STE linter, pre-commit hook, or GitHub Action under this spec. That would be a later spec, likely after 005, and it is not claimed here.

## 7. Relationship to 001 and 008

- Work **toward** spec 001 still uses this handoff. 009 does not pick Riva vs Parakeet vs Piper.
- Spec 008 already ran out of tree. New I/O-repo work should arrive as an accepted packet, not as a paste of a Hermes wiki.

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Chat replaces the packet | Human accept looks for the five artifacts. No packet → no implement. |
| Architect implements “a small fix” | Role rule: architect never implements. Small fixes still need a coder (or a human who is not wearing the architect role). |
| Coder redesigns in the PR | Review fails on unstated work. New design → architect + new accept. |
| STE used for README voice | Plan table: marketing and rationale stay prose. |
| Skill or dictionary copied into git | Spec forbids it. Reference `asd-ste100` by name. |
| This spec treated as a product feature | Status line: living practice only. |

## 9. What this plan is not

It is not a rewrite of spec 001. It is not the fleet operating manual. It is not a promise that CI will catch a missing handoff.
