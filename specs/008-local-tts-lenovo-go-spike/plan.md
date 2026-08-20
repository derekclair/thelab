# Plan: Local-tts Lenovo Go voice I/O spike (008)

**Feature**: 008-local-tts-lenovo-go-spike
**Spec**: [spec.md](./spec.md)
**Date**: 2026-06-12 (work); recorded 2026-08-20

## 1. Architecture

Two processes, two repos. This package is a library the I/O process imports.

```
Teams button (BTN_0)          Lenovo Go speaker (ALSA)
        │                              ▲
        ▼                              │
 button_listener ──pipe──► voice_loop ─┤
                       arecord → VAD → Parakeet (CPU)
                       text ──► get_agent()  [this repo]
                       reply ─► Piper → aplay (retry / settle)
                       LED via hidraw
                       telemetry JSONL (+ optional OTLP)
```

| Piece | Owner |
|-------|--------|
| Button, LED, ALSA, VAD, STT, TTS, telemetry | [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) (working name **local-tts**) |
| LangGraph, memory injection, provider factory | **this repo** (`thelab_langchain.agent.graph.get_agent`) |

`src/thelab_langchain/voice/` in *this* tree (Riva wrappers, streaming `NotImplementedError`) is **not** the live path for this spike.

## 2. Tech choices (locked for the spike)

| Concern | Choice | Why |
|---------|--------|-----|
| STT | Parakeet TDT 0.6B v3, NeMo, CPU | Fits Spark; no Riva GB10 image as a blocker |
| TTS | Piper `en_US-amy-medium`, then espeak-ng, then tone | Native aarch64; 30×-class CPU synth is a claim to *measure*, not to print unmeasured |
| Brain | Existing `get_agent()` | Do not fork memory/tools |
| LLM | Grok default; `make ollama` / `openai_compatible` for local | Spec 007: no 120B+ agent loops |
| Trigger | FIFO `/tmp/voice_trigger` | Same seam for button and `echo start` |
| Audio | ALSA `arecord`/`aplay`, name-based card discovery | USB card index moves on replug |
| VAD | RMS energy, not neural VAD | Enough for push-to-talk sessions |
| Interrupt | `stop_event` polled in playback; later also cancels agent wait | Button, not barge-in |
| Package layout | Separate git repo + isolated `.venv` | Matches basement-lab hygiene |

## 3. Phases

### Phase 0 — Brain seam (this repo)

- `get_agent()` importable via `pip install -e`.
- `.env.example` documents `LLM_PROVIDER`, `XAI_API_KEY`, `SUPERMEMORY_API_KEY`.
- `make` here only **preps** the package; it does not start ALSA.

### Phase 1 — Hardware loop (I/O package)

- Record → VAD → STT → agent → TTS on the Go.
- LED + Teams button + settle/retry for half-duplex.
- Smoke path with no keys.

### Phase 2 — Robustness (I/O package)

- USB hotplug re-discovery.
- Session transcripts on-host only.
- Content-free OTEL (opt-in).
- Sentence-chunked TTS + EOU / TTFA metrics (blueprint-informed, Option A).

Phase 2 is refinement of **this** spike, not a jump to spec 001 production voice.

## 4. Risks

| Risk | Mitigation |
|------|------------|
| USB “device busy” | Settle delay + `_robust_aplay` retries; `make audio-reset` |
| SIGINT swallowed while idle | Timed `Event.wait` + SIGINT/SIGTERM handlers (found after first public sessions) |
| Cross-repo drift | Document `get_agent()` as the only brain import; I/O does not copy graph.py |
| Over-claiming Riva/NIM | Keep this spec explicit: live path is ALSA + Parakeet + Piper |
| Secrets / serials in git | `.env` gitignored; no hardware serials in SDD or I/O git |

## 5. Success metrics

- One spoken session of several turns on the desk hardware.
- Smoke without this package.
- Per-turn latency table from real `turn_complete` events (n may be small; say so).
- Button interrupt of TTS.
- Hotplug recovery observed at least once.

## 6. What this plan is not

It is not a rewrite of spec 001. It is not a Hermes operating manual. Hermes wiki pages that describe `voice_loop.py` stay under `~/.hermes/wikis/local-tts/` and are not copied here.
