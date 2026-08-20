# Plan: Voice-facing reply contract (011)

**Feature**: 011-voice-reply-contract
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-19
**Status**: Specified / not fully enforced in code

## 1. Where the text comes from

```
utterance ─► I/O repo (Parakeet)
                 │
                 ▼
           get_agent()     this repo
           memory_injection → LLM (+ optional memory tools)
                 │
                 ▼
           AIMessage.content   ← contract applies here
                 │
                 ▼
           I/O repo: sentence-chunk → Piper → aplay
                     (button stop_event cancels playback)
```

The I/O process does not re-implement the agent (spec 008). It also does not
rewrite the reply for speakability. Chunking splits on `.` `!` `?` so first
audio can start before the full reply is synthesized. That is playback
scheduling, not a markdown/code filter.

This plan is only about making `AIMessage.content` safe to speak. Latency
tables stay in the sibling repo README; this plan does not copy them.

## 2. Three ways to enforce (none locked)

### A. Prompt / system message on the graph (possible now)

Add a short voice-facing `SystemMessage` (or prepend to the memory-injection
message) so `get_agent()` asks for short speakable prose, no tables/code unless
asked, and escalation of multi-step work.

Facts that make this cheap:

- Live speakerphone already uses `get_agent()`. `thelab-chat` uses `MemoryChat`,
  not the graph. A graph-only instruction would not change the CLI path.
- No extra LLM call. Same turn, different instruction.
- 001 T4.2 already named this; it was never done.

Limits:

- Models ignore style instructions under tool-use or “be thorough” pressure.
- No unit-testable guarantee. A table can still come out.
- Must keep the text short so it does not fight memory context for attention.

### B. Thin deterministic formatter (not built)

A pure function on the reply string after the graph returns, before the I/O
process speaks it. Examples of mechanical rules (illustrative, not a shipped
list):

- Drop fenced code blocks or replace with “I have a code block; say if you want
  it read.”
- Drop markdown tables or summarize as “that is a table of N rows.”
- Strip heading hashes and collapse bullet markers into commas.
- Cap length (e.g. first N sentences) unless the user asked for more.

Where it could live:

- **This repo** — I/O keeps calling `get_agent()` / `invoke` and speaking
  whatever comes back. Better seam: one brain, one content policy.
- **I/O repo** — this package stays format-agnostic. Worse: every consumer
  reimplements the contract.

Limits:

- Easy to over-strip when the user *did* ask for a snippet.
- Heuristics are English-and-markdown-shaped; they will miss clever formatting.
- Still not a second model. Must not add an LLM rewrite pass (spec 007 / the
  existing “no extra round-trip per voice turn” rule in `graph.py`).

Status: **not built**. No module, no tests, no hook in `get_agent()`.

### C. Leave it to the voice-profile SOUL in Hermes

A Hermes voice profile already carries persona and tone for some sessions.
That file stays in Hermes. **Do not copy `SOUL.md` into this tree.**

Limits:

- The Lenovo Go loop (spec 008) invokes `get_agent()` with session
  `HumanMessage` / `AIMessage` history plus this package’s memory injection.
  It does not load a Hermes SOUL. Relying on SOUL alone does **not** cover the
  live speakerphone path.
- Same “models can ignore it” limit as option A, plus an extra repo to keep
  in sync.
- Useful as *additional* flavor if a Hermes-hosted session injects it; not a
  substitute for A or B on the 008 path.

## 3. Suggested sequence (if we implement)

Not a commitment; a default order if someone picks this up:

1. **Prompt-level on `get_agent()`** (option A). Smallest change, possible now,
   matches 001 T4.2. Keep the instruction to a handful of lines.
2. **Listen to real sessions.** If markdown/code still hits Piper, add option B
   in *this* repo as a post-`invoke` helper the I/O process can call — or fold
   it into `get_agent()` so the I/O import surface stays one function.
3. **Do not vendor SOUL.** If Hermes sessions need the same rules, point them
   at this spec rather than duplicating a second policy file here.

Mixes are allowed (A + B). C is optional flavor, not the desk-loop control.

## 4. Escalation (spoken turn vs board)

The spoken turn is the wrong place to implement a multi-step coding or research
job. Implementation of *how* work reaches the orchestrator / board is Hermes
fleet operations, not this package.

Until that wiring exists, option A can still say: if the ask is a multi-file
change or a research spike, reply with a short ack and do not dump the work
product. That is a content rule we can state now even if the handoff is
manual.

Do not add tools to `get_agent()` whose only job is “file a ticket” unless the
fleet spec asks for it. Scope creep.

## 5. What we will not do in this plan

- Copy or paraphrase Hermes `SOUL.md`.
- Move Piper/ALSA/button interrupt into this repo.
- Claim a formatter exists.
- Put measured TTS timings in this tree.
- Add an LLM-as-judge or rewrite node on the voice path.

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Prompt ignored; Piper reads a table | Option B later; do not mark A as “enforced” |
| Formatter strips a requested snippet | Opt-in exception when the user asked this turn; keep rules dumb |
| SOUL assumed to cover 008 | Document that the Go loop does not load SOUL |
| Extra LLM rewrite “to be safe” | Forbidden: extra round-trip per turn |
| I/O and brain both grow formatters | Prefer one helper in this package |

## 7. Success

- Developers reading this folder know the contract and that it is not a filter.
- If A ships: graph tests or a fixture show a voice system message exists.
- If B ships: unit tests on the formatter, no hardware required.
- I/O still owns stop-on-button and chunked playback.
