# Plan: Workstation fleet dispatch model (012)

**Feature**: 012-fleet-dispatch-model
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20

## 1. What this plan is

A map of **which layer, which role, and which repo owns the runtime**. It is
not a plan to add a dispatcher to `thelab-langchain`. Success is a practiced
loop, not a merged feature flag.

Living practice sits in Hermes (profiles, board, gateway). This repo only
records the contract. Runtime CLI and gateway stay in Hermes. Do not vendor
that how-to here.

## 2. Protocol vs runtime

The spec is the durable contract (layers, roster, spec-first, human merge).
**Hermes is the current runtime** — an implementation detail, not the model.

```
Human
  └─ orchestrator (front door + dispatcher)
        ├─ conversation (this turn)
        ├─ in-process subagent (dies with this turn)
        └─ durable board
              ├─ architect / researcher / designer   (durable directory)
              ├─ coder                               (git worktree → PR)
              └─ reviewer                            (same tree as the change)
```

This Python package does not own that board, spawn workers, or persist cards.
Do not add a dispatch module here to “implement 012.”

## 3. Mapping table (Hermes today)

Abstract spec terms map onto the workstation as follows. How to start a
gateway, which binary flags exist, and profile *filenames* will change.
Keep the spec terms; rewrite this table if the runtime changes.

| Spec term | Hermes today |
|-----------|----------------|
| Conversation / front door | Default profile; human talks to one orchestrator |
| In-process subagent | Short-lived helper inside the parent turn; discarded when the turn ends |
| Durable board | Persistent Kanban; cards outlive a chat turn |
| **orchestrator** | Default profile; owns board dispatch |
| **architect** / **researcher** / **coder** / **designer** / **reviewer** | Specialist profiles spawned by the dispatcher (see [010 plan](../010-worker-completion-protocol/plan.md) §2 for the current filename map) |
| Unknown assignee | Card stays unstarted; dispatcher does not spawn |
| Done (code) | Human merge on the host Git forge |

Filenames in that 010 table are **runtime wiring**, not 012’s product names.
Do not treat a profile path as a roster role.

Workspace kinds, **complete** / **block**, and scratch-vs-durable stay in
010. This plan does not reprint them.

## 4. Dispatch flow

1. Human speaks to the orchestrator (conversation layer).
2. Orchestrator classifies:
   - small enough for this turn → answer (or a dying-with-the-turn helper);
   - must survive or needs a specialist gate → **task graph**, then board cards.
3. Board cards use roster roles only. Architect / researcher / designer get a
   durable directory. Coder gets a git worktree. Reviewer shares the change’s
   tree.
4. Non-trivial code waits on **human accept** of the architect packet (009).
5. Board workers **complete** or **block** (010).
6. Human merges. That is done for code.

The orchestrator proposes the graph **before** flooding the board. Children
stay unstarted until parents are done *on the board*. For product code, board
“done” is still not ship; ship is human merge (spec FR-6).

## 5. Who uses which model class (007)

Do not invent footprints. Slot policy lives in 007.

| Roles | Slot |
|-------|------|
| Orchestrator, architect, reviewer, designer | Hosted. Do not occupy the Spark’s single local generative LLM. |
| Coder, researcher | May use the one local ~30B-class slot, with hosted fallback if the slot is busy or the endpoint is down. |

One serious local LLM at a time. No 120B+ agent loops on one Spark. When the
slot is occupied, other work uses hosted models. 012 does not pick weights.

## 6. What Hermes is responsible for (not this repo)

- Persisting cards and comments.
- Spawning the assigned profile into the chosen workspace.
- Keeping a living dispatcher so board cards do not sit unstarted forever.
- Treating missing complete/block as a violation (010).
- Leaving unknown assignees unstarted.
- In-process helpers that die with the parent turn.
- CLI, gateway, and profile files.

Operator recovery (reclaim, reassign, unblock) is Hermes operations. This
plan does not catalog those commands.

## 7. What this repo is responsible for

- Keep this SDD folder as the dispatch-model source of truth in git.
- When fleet workers touch **this** tree, they obey 009, 010, and this spec:
  durable directory for `specs/` and `docs/`, worktree for `src/` / tests,
  accepted spec before non-trivial code, no secrets on the card, human merge
  for code.
- Do **not** encode dispatch in pytest or GitHub Actions. Spec 005 CI is for
  this package’s Python, not for Hermes process health.
- Spoken escalation remains 011’s problem. Do not add a ticket tool under 012.

## 8. Language and packets

| Concern | Where |
|---------|--------|
| Which layer / which role | This spec |
| How architect talks to coder (STE, five artifacts, human accept) | 009 |
| How a board worker stops (complete/block, workspace kinds) | 010 |
| Local vs hosted slot | 007 |
| Speakable replies / escalate instead of dumping a patch | 011 |

This SDD folder is human prose. Agent-consumed procedures stay STE per 009.

## 9. Risks

| Risk | Mitigation |
|------|------------|
| Chat replaces the board for multi-step work | Durability rule: inspect / pause / resume → board |
| Orchestrator implements or “reviews” in character | Role rule: decompose, do not impersonate |
| Invented assignee looks running | Closed roster; idle-unstarted is the failure mode |
| Spec/code on scratch | 010 workspace table |
| Coder complete treated as ship | FR-6: human merge |
| In-process helper used for a spec | Dies with the turn; promote to board |
| Building a dispatcher in `thelab-langchain` | Explicit non-goal |
| How-to copied into git | Distill here; CLI stays in Hermes |
| Two local LLMs / 120B loops | 007 slot policy |

## 10. Success (qualitative)

No invented metrics. The model is working when:

- The human uses one front door for small work.
- Multi-step work is on a board a human can open later.
- Architect / researcher / designer cards have no product patches.
- Reviewer cards never contain the fix.
- Merged PRs, not completed coder cards, are what landed in `main`.
- Unknown names sit idle instead of spawning ghosts.
- This package still has no dispatcher.

## 11. What this plan is not

It is not a Hermes CLI cheat sheet. It is not a gateway runbook. It is not
messenger delivery. It is not a rewrite of 007, 009, or 010. It is not a
promise that CI will catch a mis-routed card.
