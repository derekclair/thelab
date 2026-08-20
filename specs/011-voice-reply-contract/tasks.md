# Tasks: Voice-facing reply contract (011)

**Feature**: 011-voice-reply-contract
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)
**Status**: Specified / not fully enforced in code

Checkboxes are honest. Spec-only work can be marked done; enforcement is not.

## Phase 0 — Specify the contract (this folder)

- [x] Write `spec.md` (spoken shape, unspeakable formatting, escalate vs
      implement, I/O vs brain boundary)
- [x] Write `plan.md` (prompt vs thin formatter vs Hermes SOUL; SOUL not copied)
- [x] Write `tasks.md` (this file)
- [x] Record that this package does **not** post-process replies today

## Phase 1 — Prompt-level guidance (possible now)

Not done. Possible now because `get_agent()` is the live voice consumer and
`MemoryChat` is a separate CLI path. No new service, no extra LLM call.

- [ ] Add a short voice-facing system instruction on the graph (`get_agent()` /
      memory injection or a dedicated preamble)
- [ ] Cover: short speakable prose; no tables / code dumps / heading hashes
      unless the user asked this turn; escalate multi-step coding/research
      rather than doing it in the spoken answer
- [ ] Keep the instruction small so it does not drown memory context
- [ ] Unit test or fixture: compiled graph (or injection helper) includes the
      voice instruction — does **not** prove the model obeys it
- [ ] Do not treat this checkbox as “enforced speakability”

## Phase 2 — Deterministic speakability filter (not built)

Not built. Do not check these off until a pure helper exists and is wired.

- [ ] Pure formatter: strip or replace unspeakable markdown (tables, fences,
      heading hashes) without a second model call
- [ ] Length / sentence cap with an exception when the user asked for a dump
- [ ] Unit tests on strings only (no ALSA, no Piper, no keys)
- [ ] Wire through this package so I/O can keep a single brain import
- [ ] Decide with a review whether formatter lives inside `get_agent()` or as a
      sibling helper the I/O process calls
- [ ] Explicit non-goal until then: claiming Piper is “safe” because of chunking

## Phase 3 — Escalation seam (Hermes, not this repo)

Out of band. Listed so it is not silently implemented as a spoken dump.

- [ ] Spoken ack of “handed to the board” once fleet wiring exists (Hermes
      operating manual, not vendored)
- [ ] No `get_agent()` ticket-filing tool unless that fleet spec asks for it
- [ ] Do not copy voice-profile `SOUL.md` into this tree

## Out of scope (stay unchecked here)

- [ ] Button interrupt of TTS — I/O repo / spec 008
- [ ] Sentence-chunked Piper / TTFA — I/O repo
- [ ] Voice barge-in — out of scope for 008 and for this contract
- [ ] Copying sibling-repo latency tables into this package

## Traceability

| Want | Code today |
|------|------------|
| Speakable default | Unconstrained `AIMessage.content` |
| Prompt-level guidance | Possible now; **not** in `graph.py` |
| Deterministic filter | **Not built** |
| Button stop of playback | Sibling I/O repo |
| Hermes SOUL | Hermes only |

Live consume path: [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
calls `thelab_langchain.agent.graph.get_agent`. Historical 001 checkbox: T4.2
in [001/tasks.md](../001-voice-dgx-spark-agent/tasks.md).
