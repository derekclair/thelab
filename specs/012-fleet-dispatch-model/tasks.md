# Tasks: Workstation fleet dispatch model (012)

**Feature**: 012-fleet-dispatch-model
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

This model is **practiced on Hermes**. This Python package does not implement
a dispatcher. Runtime CLI and gateway stay in Hermes. There is **no CI** in
thelab for routing or roster names. Checkboxes below are a record of that
split, not a backlog to build dispatch here.

## Phase 0 — Model (living practice, not this package)

Practiced on the workstation fleet; not code in `src/thelab_langchain/`.

- [x] Three layers: conversation, in-process subagent, durable board
- [x] Single orchestrator as front door; decomposes; does not impersonate specialists
- [x] Closed roster only (orchestrator, architect, researcher, coder, designer, reviewer)
- [x] Unknown role names are not dispatched (idle-unstarted, not a ghost worker)
- [x] Architect / researcher / designer do not ship product code
- [x] Reviewer never implements
- [x] Coder implements accepted specs only
- [x] Spec-first for non-trivial work (009)
- [x] Board workers complete or block (010)
- [x] Human merge is definition of done for code
- [x] Quality-critical roles hosted; coder/researcher may use the one local slot (007)

## Phase 1 — SDD record (this repo)

- [x] `specs/012-fleet-dispatch-model/spec.md`
- [x] `specs/012-fleet-dispatch-model/plan.md` (Hermes as current runtime; roles not filenames)
- [x] `specs/012-fleet-dispatch-model/tasks.md` (this file)

Do not copy profile files, `SOUL.md`, or the Hermes operating manual into this
tree to “complete” a checkbox.

## Explicitly not tasks in thelab

Do not open work in this package for:

- A dispatcher, board, worker runner, or gateway under `thelab_langchain`
- Pytest or GitHub Actions that assert Hermes routing or process health
- Copying the local Hermes how-to, CLI recipes, or `SOUL.md` into git
- Chat/notification integration as part of 012
- A spoken ticket-filing tool on `get_agent()` (see 011 Phase 3)

If the board runtime is replaced, update [plan.md](./plan.md) mapping — do not
add a dispatcher here to “finish” 012.

## Traceability

| Concern | Record |
|---------|--------|
| Layers and roster | This folder |
| Handoff wording | [009](../009-architect-coder-handoff/tasks.md) |
| Complete-or-block / workspaces | [010](../010-worker-completion-protocol/tasks.md) |
| Local vs hosted slot | [007](../007-dgx-hardware-optimization/spec.md) |
| Runtime CLI / gateway | Hermes (not vendored) |

This tasks file is only the checklist view. It does not claim CI or package
enforcement.
