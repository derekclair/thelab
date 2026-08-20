# Tasks: Local-tts Lenovo Go voice I/O spike (008)

**Feature**: 008-local-tts-lenovo-go-spike
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes record what the spike actually did. This file was filled in when
the SDD record was added to this repo, not on the original 2026-06-12 day.

## Phase 0 — Brain seam (this repo)

- [x] Keep `get_agent()` as the public graph factory
- [x] Provider factory (`xai` / `anthropic` / `openai_compatible`)
- [x] `.env` gitignored; `.env.example` for keys
- [x] `make` / `make local` only preps the editable package
- [ ] LangGraph checkpointer for voice sessions (spec 004 — not required to call 008 done)

## Phase 1 — Hardware loop (I/O package, working name local-tts)

- [x] Named pipe trigger `/tmp/voice_trigger`
- [x] Teams button → pipe
- [x] HID LED on session / ready
- [x] Energy VAD record on the Go capture device
- [x] Parakeet TDT 0.6B v3 CPU STT
- [x] `get_agent()` + session message list
- [x] Piper TTS with espeak-ng / tone fallback
- [x] Half-duplex settle + aplay retry
- [x] `make smoke` without this package / without keys
- [x] Volume dial ticks (nice-to-have; shipped)

## Phase 2 — Robustness (same I/O package)

- [x] USB hotplug re-discovery (evdev + ALSA + hidraw)
- [x] On-host session transcripts (gitignored)
- [x] Content-free opt-in OTEL
- [x] Sentence-chunked Piper + `eou_ms` / `tts_ttfa_ms`
- [x] SIGINT/SIGTERM actually stop the idle loop
- [ ] Voice barge-in (talk over TTS) — out of scope; button cancel only
- [ ] Riva streaming ASR as primary — out of scope for 008

## Traceability

Implementation git history for Phase 1–2 lives in the I/O package, not in this
repo. This tasks file is the checklist view of that work. The second commit on
the spec branch names the public I/O repository.
