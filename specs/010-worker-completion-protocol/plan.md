# Plan: Durable-board worker completion protocol (010)

**Feature**: 010-worker-completion-protocol
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-19

## 1. Protocol vs runtime

The spec is the durable contract. **Hermes Kanban is the current runtime** — an implementation detail, not the protocol.

```
Human
  └─ orchestrator (front door + dispatcher)
        └─ durable board
              ├─ architect / researcher / designer   (durable directory)
              ├─ coder                               (git worktree → PR)
              └─ reviewer                            (same tree as the change)
```

This Python package does not own that board, spawn workers, or persist cards. Do not add a board module here to “implement 010.”

## 2. Mapping table (Hermes today)

Abstract spec terms map onto the workstation fleet as follows. Profile *models* and how to start a gateway are out of scope; they live in the local Hermes operating manual and will change.

| Spec term | Hermes Kanban today |
|-----------|---------------------|
| Board | Durable Kanban (SQLite-backed). Cards outlive a chat turn. |
| **complete** | Worker terminal `kanban_complete` (or equivalent complete action). |
| **block** | Worker terminal `kanban_block`. Human later unblocks. |
| Protocol violation | Clean worker exit with neither action. Circuit breaker auto-blocks the card. Not success. |
| **scratch** | `scratch` workspace — deleted on complete. |
| **durable directory** | `dir:` workspace rooted at the repo or docs tree. |
| **git worktree** | `worktree` / `worktree:<repo>` workspace. |
| **orchestrator** | Default profile; owns dispatch (`kanban.orchestrator_profile`). |
| **architect** | Architect specialist profile (specs only). |
| **researcher** | Researcher specialist profile. |
| **coder** | Coder specialist profile. |
| **designer** | Designer profile (visual only). |
| **reviewer** | Reviewer profile (never implements). |
| Unknown assignee | Card stays **ready**; dispatcher does not spawn. |
| Done (code) | Human merge on the host Git forge. Worker complete ≠ merge. |

If the board product changes, keep the spec terms and rewrite this table. Do not fork a second protocol.

## 3. How a card is supposed to finish (runtime)

1. Dispatcher assigns a **roster** profile and a **workspace kind** that matches the deliverable.
2. Worker does the work in that workspace.
3. Worker calls **complete** (artifacts in the summary) or **block** (human question / gate).
4. Dependent cards stay unstarted until parents are **done** in board terms. For code, “done” in the *product* sense is still human merge (spec FR-5); parent-complete is only the board edge that unblocks the next specialist.

Standard shape, not a command sheet:

```
architect (durable directory, spec)
    → human accepts
    → coder (worktree, PR + tests)  →  reviewer (block or approve)
    → human merges
```

Research or design lanes may feed architect; they still complete or block, and they still do not land product code.

## 4. What Hermes is responsible for (not this repo)

- Persisting cards and comments.
- Spawning the assigned profile into the chosen workspace.
- Treating missing complete/block as a violation (circuit breaker).
- Leaving unknown assignees in ready.
- Deleting scratch on complete.
- Not running a second dispatcher beside the orchestrator’s.

Operator recovery (reclaim, reassign, unblock) is Hermes operations. This plan does not catalog those commands.

## 5. What this repo is responsible for

- Keep this SDD folder as the protocol source of truth in git.
- When fleet workers touch **this** tree, they obey the spec: durable directory for `specs/` and `docs/`, worktree for `src/` / tests, complete/block, no secrets on the card, human merge for code.
- Do **not** encode the protocol in pytest or GitHub Actions. Spec 005 CI is for this package’s Python, not for Hermes worker exits.

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Spec lives only in a local how-to and drifts | This folder; revise when the runtime mapping changes |
| Worker “succeeds” by exiting | Runtime circuit breaker; treat as violation; fix the worker, then reclaim |
| Spec/code written on scratch | Ban scratch for durable deliverables (spec FR workspace table) |
| Invented assignee | Closed roster; idle-in-ready is the failure mode |
| Coder complete treated as ship | Spec FR-5: human merge |
| Secrets in card comments | Spec FR-3; redact and re-complete/block if it happens |
| Building a board in `thelab_langchain` | Explicit non-goal |

## 7. Success (qualitative)

No invented metrics. The protocol is working when:

- Completed cards name artifacts a human can open.
- Blocked cards name the human action required.
- Silent exits are treated as violations, not green cards.
- Specs still exist after architect complete (durable directory).
- Merged PRs, not completed coder cards, are what landed in `main`.

## 8. What this plan is not

It is not a Hermes CLI cheat sheet. It is not Slack (or any messenger) delivery. It is not a model-routing or GPU-budget plan (see 007). It is not a request to vendor `~/.hermes/docs/agentic-workflow.md` into this tree — that file stays where Hermes expects it.
