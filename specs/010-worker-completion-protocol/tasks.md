# Tasks: Durable-board worker completion protocol (010)

**Feature**: 010-worker-completion-protocol
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

This protocol is **practiced on the Hermes Kanban runtime**. This Python package
does not implement a board. There is **no CI** in thelab for complete/block.
Checkboxes below are a record of that split, not a backlog to build Kanban here.

## Phase 0 — Protocol (living practice, not this package)

Practiced on the workstation fleet; not code in `src/thelab_langchain/`.

- [x] Workers end with **complete** or **block**
- [x] Clean exit without either is a protocol violation (not success)
- [x] Complete carries concrete artifacts (paths, PR URLs, observed test counts)
- [x] No secrets in board fields
- [x] Workspace: scratch deleted on complete; never for durable specs/code
- [x] Workspace: durable directory for specs/docs
- [x] Workspace: git worktree for product code
- [x] Closed roster only (orchestrator, architect, researcher, coder, designer, reviewer)
- [x] Unknown role names sit in ready; not dispatched
- [x] Human merge is definition of done for code
- [x] Architect / researcher / designer / reviewer do not implement product code on their cards

## Phase 1 — SDD record (this repo)

- [x] `specs/010-worker-completion-protocol/spec.md`
- [x] `specs/010-worker-completion-protocol/plan.md` (Hermes Kanban as current runtime)
- [x] `specs/010-worker-completion-protocol/tasks.md` (this file)

## Explicitly not tasks in thelab

Do not open work in this package for:

- A board, dispatcher, or worker runner under `thelab_langchain`
- Pytest or GitHub Actions that assert Hermes complete/block
- Copying the local Hermes operating manual into git
- Chat/notification integration as part of 010

If the board runtime is replaced, update [plan.md](./plan.md) mapping — do not add a board here to “finish” 010.

## Traceability

Runtime and recovery procedure: local Hermes docs (not vendored).
Handoff wording: spec 009.
This folder is only the protocol SDD.
