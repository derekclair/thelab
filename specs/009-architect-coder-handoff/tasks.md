# Tasks: Architect ↔ coder inter-agent handoff (009)

**Feature**: 009-architect-coder-handoff
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes are honest. The protocol is **practiced in Hermes**. This repo **does not** enforce it in CI. This folder is the SDD record, not a `thelab-langchain` feature.

## Phase 0 — Record the practice (this repo)

- [x] Write `spec.md` with roles, five handoff artifacts, STE rules of thumb, and skill name `asd-ste100` (no skill body, no ASD dictionary)
- [x] Write `plan.md` with flow spec → human accept → implement → review, and STE vs human prose
- [x] Write `tasks.md` (this file)
- [x] State status as living practice, not a product feature
- [x] Point at related specs 001 and 008 without revising their stack choices

## Phase 1 — Workstation practice (Hermes, outside this repo)

- [x] Architect profile `dgx-architect` designs and does not implement (living practice)
- [x] Coder profile `dgx-coder` implements accepted specs only (living practice)
- [x] Handoff packet in use: spec, acceptance criteria, kanban body, blockers, residual risks
- [x] STE reserved for agent-consumed procedures via skill `asd-ste100` (agents skill and Grok skill; not vendored here)

Do not copy profile files, Hermes env files, or skill bodies into this tree to “complete” a checkbox.

## Phase 2 — Enforcement in this repo (**not done**)

- [ ] CI job that lints STE in kanban/spec procedures
- [ ] CI job that blocks implementation PRs without an accepted packet
- [ ] Pre-commit or ruff-like hook for noun-cluster / sentence rules
- [ ] Runtime or library support in `thelab-langchain` for architect/coder roles

Phase 2 is **out of scope** for 009. Leave the boxes empty. Do not implement them under this spec.

## Phase 3 — Optional later SDD hygiene (not required to call 009 done)

- [ ] PR template checklist that names the five artifacts (docs only; still not CI)
- [ ] Decision on reviewer-agent output language (plan default: fail/pass in STE, narrative in prose)

## Traceability

- Practice: Hermes profiles `dgx-architect` and `dgx-coder` on the workstation.
- Skill: `asd-ste100` outside this repo.
- Spike that already ran out of tree: [008](../008-local-tts-lenovo-go-spike/tasks.md).
- This tasks file is only the checklist view. It does not claim CI or package enforcement.
