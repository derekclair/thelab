# Tasks: Reviewer quality gate (013)

**Feature**: 013-reviewer-quality-gate
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes are honest. The gate is **practiced in Hermes**. This package has
**no reviewer bot**. GitHub PR review is the public analog. This folder is the
SDD record, not a `thelab-langchain` feature.

## Phase 0 — Record the practice (this repo)

- [x] Write `spec.md` with review-only role, four severities, structured
      findings, six lenses, complete-or-block, human merge
- [x] Write `plan.md` with Hermes vs GitHub analog, follow-up routing, and
      “no bot in this package”
- [x] Write `tasks.md` (this file)
- [x] State status as living practice, not a product feature
- [x] Point at related specs 009, 010, and 012 (fleet dispatch) without vendoring profile files

## Phase 1 — Workstation practice (Hermes, outside this repo)

Practiced on the fleet; not code in `src/thelab_langchain/`.

- [x] Reviewer reviews specs and PRs; does not implement fixes
- [x] Fixes go to a coder follow-up (blocker/major on this change)
- [x] Lenses: correctness, security, privacy, SDD completeness, tests,
      acceptance criteria
- [x] Findings use severity, location, and fix guidance
- [x] Severity words: blocker, major, minor, note
- [x] No rubber-stamp of security-sensitive or user-facing changes
- [x] Reviewer always completes or blocks (010)
- [x] Human merge remains definition of done for code

Do not copy profile files or skill bodies into this tree to “complete” a
checkbox.

## Phase 2 — Public analog (this GitHub repo, not a bot)

- [x] Humans review pull requests on this repo (comments / approve /
      request-changes) as the public analog of the gate
- [ ] GitHub Action or app that posts a reviewer-profile verdict — **not done**

Phase 2’s empty box is out of scope for 013. Leave it empty.

## Phase 3 — Enforcement in this package (**not done**)

- [ ] Reviewer module or LangGraph node in `thelab-langchain`
- [ ] CI job that requires a reviewer assignee or lints finding shape
- [ ] Auto-approve or auto-merge on specialist complete

Phase 3 is **out of scope** for 013. Do not implement them under this spec.

## Explicitly not tasks in thelab

Do not open work in this package for:

- A reviewer bot, webhook, or forge app
- Pytest that asserts Hermes complete/block or finding markdown
- Copying the reviewer profile or `code-review` / `security-scan` skill
  bodies into git
- Changing 009 packet shape or 010 terminals

## Traceability

- Practice: Hermes reviewer specialist (outside this repo).
- Terminals and roster: spec 010.
- Packet language: spec 009.
- Dispatch layer: spec 012 (reviewer is a durable-board specialist).
- Public analog: GitHub pull-request review; human merge.
- This tasks file is only the checklist view. It does not claim a bot or
  package enforcement.
