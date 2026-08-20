# Feature Spec: Voice-facing reply contract

**Feature ID**: 011-voice-reply-contract
**Status**: Specified / not fully enforced in code
**Created**: 2026-08-19
**Owner**: Derek Clair
**Related**: [008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md),
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
**Parent**: [001-voice-dgx-spark-agent](../001-voice-dgx-spark-agent/spec.md) (T4.2
voice-aware behaviors)

## Honest current state

This is a **contract we want**, not a shipped filter.

`get_agent()` in this repo produces the text that Piper speaks. The live I/O
loop ([008](../008-local-tts-lenovo-go-spike/spec.md), executed in
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent))
takes the last `AIMessage.content` and synthesizes it. Sentence chunking in that
repo is for time-to-first-audio, not for speakability.

This package does **not** post-process replies for speakability. There is no
graph node, wrapper, or test that strips markdown, caps length, or blocks
unspeakable formatting. `MemoryChat` (CLI text) has a generic “be concise but
warm” system prompt; the graph used by voice does not. Memory injection is a
`SystemMessage` of profile + recall, not a spoken-UX policy.

Button interrupt of TTS is an I/O concern (spec 008 / the sibling repo). This
spec is about **what** the model is allowed to emit, not how playback is
cancelled.

## Overview

Spoken UX constraints belong in the brain repo even though ALSA, Piper, and
the Teams button live next door.

When the consumer is a speakerphone, a good reply is short, speakable prose.
Markdown tables, fenced code, heading hashes, and other unspeakable formatting
are a failure of the contract unless the person at the desk asked for them in
that voice session.

Multi-step coding and research do not belong in the spoken turn. The desk loop
should acknowledge and escalate to the workstation orchestrator / board (Hermes
fleet operating manual, not vendored here). It should not narrate a long plan
or dump a patch through Piper.

## Goals

- Define what a voice-facing `get_agent()` reply may contain.
- Keep spoken answers short and listenable by default.
- Forbid unspeakable formatting unless the user asked for it in the voice session.
- Send multi-step coding / research work to the orchestrator / board instead of
  doing it in the spoken turn.
- Stay honest: specify the contract without claiming a filter exists in code.

## Non-goals

- ALSA, Piper, Parakeet, VAD, LED, USB hotplug, or button interrupt of playback
  (spec 008 / I/O repo).
- Inventing or copying TTS latency numbers. Measured stage times, if any, live
  in the sibling repo README; they are not this contract.
- Vendoring Hermes voice-profile SOUL or copying `SOUL.md` into this tree.
- Specifying the orchestrator / board / Kanban workflow (stays in Hermes).
- Changing `MemoryChat` / `thelab-chat` text UX, except to note it is a
  different consumer.
- Streaming barge-in, Riva, or rewriting spec 001’s long-term voice stack.
- A product “customer service” tone guide.

## User stories

1. As the person at the desk, I ask a short question over the speakerphone and
   hear a short spoken answer, not a markdown document.
2. As that person, I ask for a multi-file change or a research spike and hear
   that it is handed to the board, not a spoken walkthrough of the work.
3. As that person, I can still say “read me that snippet” or “say the table”
   and get what I asked for in that turn.
4. As a developer, I know this repo owns the reply *content* contract, and the
   I/O repo owns *playback* (chunking, stop-on-button).
5. As a developer, I can tell “prompt guidance we could add now” from “a
   deterministic speakability filter we have not built.”

## Functional requirements

### FR-1 Default spoken shape

- Default voice replies are short, speakable prose (a few sentences, one
  thought-group). Not an essay, not a blog post, not a README.
- Prefer words Piper can say. Avoid layout that only makes sense on a screen.
- Warm and direct is fine. Padding, recap-the-question, and “as an AI” throat-clearing
  are not.

### FR-2 Unspeakable formatting (opt-in, not default)

Unless the user **asked for it in this voice session**, do not emit:

- Markdown tables
- Fenced or indented code dumps
- Heading-hash outlines (`##`, `###`)
- Long bullet forests, numbered runbooks, or checkbox lists meant for a ticket
- Raw JSON / YAML / diff dumps
- Bare URLs or path dumps read aloud as punctuation soup

If the user did ask (e.g. “read the function”, “say the rows”), the model may
emit that content. The I/O layer still sentence-chunks for playback; that is
not a license to dump an unbounded file.

### FR-3 Escalate instead of doing the work in the spoken turn

- Multi-step coding, multi-file edits, and open-ended research are **out of
  band** for a voice turn.
- The spoken reply should confirm the ask and say it is going to the
  orchestrator / board. It should not start implementing, paste a patch, or
  narrate a long investigation.
- What “going to the board” means operationally lives in Hermes, not here.
  This spec only forbids doing that work *as the spoken answer*.

### FR-4 This spec vs I/O

| Concern | Owner |
|---------|--------|
| What text the model may emit | **this repo** (`get_agent()` output) |
| Sentence-chunked Piper / TTFA | I/O repo |
| Button interrupt of TTS | I/O repo (spec 008) |
| Half-duplex ALSA, STT, LED | I/O repo (spec 008) |
| Prompt / optional formatter that enforces FR-1–FR-3 | this repo (not built; see plan) |
| Voice-profile SOUL | Hermes (not copied here) |

### FR-5 Honesty in code

- Until a formatter or voice system message exists, consumers must assume
  `AIMessage.content` is unconstrained LLM text.
- Docs and tasks must not mark a speakability filter as done.
- Text CLI (`MemoryChat`) is out of this contract’s enforcement path; do not
  pretend a CLI “be concise” line covers the speakerphone.

## Non-functional requirements

- No secrets, serials, or household identifiers in this spec or in example
  utterances used for the contract.
- Do not bake measured TTS timings into this package. Point at the sibling
  README if someone needs hardware numbers.
- Same `get_agent(user_id)` seam as spec 008. Do not fork the graph for “voice
  vs text” unless the plan explicitly chooses a voice-only wrapper.
- Optional enforcement (prompt or formatter) must not add an extra LLM
  round-trip per turn. Memory injection already skipped summarization for that
  reason.

## Acceptance criteria

- [ ] Spec reviewed: voice replies are defined as short speakable prose with
      unspeakable formatting opt-in, not default.
- [ ] Escalation of multi-step coding/research is written as a requirement, not
      a suggestion.
- [ ] Boundary with spec 008 is explicit (content here, interrupt/playback there).
- [ ] Code in this repo still has **no** speakability post-process (honest until
      a later task ships one).
- [ ] Prompt-level guidance is identified as possible now; a deterministic
      filter is identified as not built (see [tasks.md](./tasks.md)).

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Compiled graph. Voice I/O invokes this; reply text is last AI content. |
| `graph.invoke({"messages": ...})` | Unchanged call shape from spec 008. |
| Reply string | Today: raw model text. Wanted: FR-1–FR-3. Not filtered. |
| Hermes SOUL | Optional persona for some sessions. Not an API of this package. |

## Relationship to other specs

- **001** — long-term desktop voice. T4.2 (“voice-aware behaviors / shorter
  responses”) is the historical checkbox; this folder is the actual contract.
- **008** — Lenovo Go I/O spike. Consumes the text this spec governs. Does not
  define speakability.
- **004** — checkpointers. Orthogonal; session memory is not reply shape.
- **007** — Spark budget. A speakability filter, if built, stays CPU-cheap
  (no second model call).
- Workstation fleet (orchestrator / architect / researcher / coder / reviewer)
  is not specified here.

## Open questions

- Enforce via prompt on the graph, a thin deterministic formatter, Hermes SOUL,
  or some mix? Options are in [plan.md](./plan.md); none is locked.
- How does the spoken turn *signal* escalation (a sentence of ack vs a tool vs
  a convention the orchestrator already watches)? Out of scope until fleet
  wiring is specified in Hermes.
- Should `get_agent()` always be voice-shaped, given the CLI uses `MemoryChat`?
  Probably yes if the only live graph consumer is the speakerphone — confirm
  before adding a system message.
