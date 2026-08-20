# Feature Spec: Local-tts Lenovo Go voice I/O spike

**Feature ID**: 008-local-tts-lenovo-go-spike
**Status**: Specified and executed.
**Implementation**: [`derekclair/conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
(historically the `local-tts` package). This repo stays the brain (`get_agent()`).
**Created**: 2026-06-12 (spike locked)
**Recorded here**: 2026-08-20
**Owner**: Derek Clair
**Parent**: [001-voice-dgx-spark-agent](../001-voice-dgx-spark-agent/spec.md)

## Record-keeping note

This spec is written **after** the spike was already running. The design was real; the SDD trail was not. Notes lived in a Hermes-generated wiki (`~/.hermes/wikis/local-tts/`, left in place — Hermes expects it) and in ad-hoc markdown in the I/O tree. This folder is the SDD record in the **brain** repo: what we asked the hardware loop to do, and what this package must expose so that loop does not re-implement the agent.

It does **not** replace spec 001. Spec 001 is the broader desktop-voice goal (Riva/NIM compose, streaming barge-in, larger local models). This spec is the **interim hardware spike**: get a natural button → listen → think → speak loop on a Lenovo Go attached to a DGX Spark, using the **existing** LangGraph brain.

## Overview

Build a small, isolated voice I/O process for the Lenovo Go Wired Speaker:

1. Teams button starts or ends a multi-turn session (LED on while the session is live).
2. Energy-based VAD captures an utterance from the Go microphone.
3. Local STT (NVIDIA Parakeet via NeMo, CPU path on this Spark) turns audio into text.
4. This repo’s `get_agent()` runs the turn (Supermemory injection + LLM + optional tools).
5. Local TTS speaks the reply on the same USB device (Piper primary; espeak-ng then a diagnostic tone as fallback).
6. The Go is half-duplex: capture and playback must not overlap; “device busy” must recover.

The spike owns **ears, mouth, hands, and telemetry**. This package owns **brain and memory**. Seams stay thin on purpose.

## Goals

- Prove the desk hardware can drive a real multi-turn conversation with the existing agent.
- Keep STT/TTS on-device. Reasoning may use Grok or a local OpenAI-compatible endpoint.
- Do not rebuild LangGraph, Supermemory, or provider routing in the I/O process.
- Survive USB unplug/replug without a full restart of the button path.
- Measure per-turn latency (ASR / agent / TTS / later EOU and time-to-first-audio) without shipping transcripts off-box.

## Non-goals

- Telephony, hosted STT/TTS, or a browser/WebRTC UI.
- Full Nemotron Voice Agent NIM compose as the primary desk UX.
- Voice barge-in (talking over the agent). Button interrupt of playback is in scope; speech-over-speech is not.
- Replacing `thelab_langchain.voice` Riva helpers as the live path (those remain a Phase-2 experiment in this tree).
- Multi-tenant product; unpublished-company / customer-service framing.

## User stories

1. As the person at the desk, I press the Teams button, hear “Ready.”, speak, and hear a spoken reply through the same speakerphone.
2. As that person, I press the button again to stop speech mid-utterance and end the session.
3. As a developer, I run a smoke path (LED + TTS) with **no** API keys and **no** this package installed.
4. As a developer, I install this package editable into the I/O venv and get the real agent + memory path.
5. As an operator, I unplug and replug the Go and the button/LED/ALSA card rebind without a manual service restart.

## Functional requirements

### FR-1 Trigger and session

- Named pipe `/tmp/voice_trigger` is the session seam (button listener writes `start`; the loop can also be kicked with `echo start > /tmp/voice_trigger`).
- First press starts a session; press during a session sets a stop event (cancel in-flight TTS; abandon the in-flight agent result when that is wired).
- LED (HID report on the Go) is solid while services are ready / a session is active; a short blink marks session end.

### FR-2 Capture and STT

- Record from the Go ALSA device (discover by name, not a frozen card index).
- End-of-utterance by energy VAD (configurable silence window; default on the order of 0.5 s once tuned).
- Transcribe with Parakeet TDT 0.6B v3 via NeMo on the CPU path for this Spark.
- Empty transcription is a spoken apology, not a crash.

### FR-3 Agent seam (this repo)

- I/O process calls `thelab_langchain.agent.graph.get_agent(user_id)` and `graph.invoke(...)`.
- Caller accumulates `HumanMessage` / `AIMessage` for the session (`thread_id` per session).
- No second copy of memory tools or provider factory in the I/O process.
- Missing keys or missing package → mock/fallback path so hardware bring-up can continue.

### FR-4 TTS and half-duplex audio

- Primary: Piper neural TTS. Fallback: espeak-ng, then a diagnostic tone.
- Retry `aplay` on “device busy” with a short settle between capture and playback.
- Stop event must terminate playback promptly.
- Later: sentence-chunked Piper so first audio does not wait on the full reply (time-to-first-audio).

### FR-5 Hotplug

- Button listener remains active if the Go is missing at start or is yanked.
- Re-discover evdev (Teams `BTN_0`, smallest keyset), ALSA card index, and hidraw LED device on udev add/remove.

### FR-6 Observability

- Local structured events (JSONL). Per-turn durations: `asr_ms`, `agent_ms`, `tts_ms`, `total_ms`, and later `eou_ms` / `tts_ttfa_ms`.
- Optional OTLP export is **opt-in** and **content-free** (durations and counts only). No transcripts on the wire.
- Transcripts, if kept, stay on the host and are gitignored.

## Non-functional requirements

- Python 3.11, project-local `.venv`, no global pip.
- aarch64 DGX Spark (CUDA present; do not require `nvidia-smi` or `torch.cuda.is_available()`).
- User in `audio` and `input`; udev so hidraw is writable without daily sudo.
- MIT; no secrets in git; no hardware serials in git.

## Acceptance criteria

- [ ] `make smoke` in the I/O package runs LED + TTS with no this-package import and no API keys.
- [ ] With this package editable-installed and keys present, a button-started session completes at least one STT → `get_agent()` → TTS turn.
- [ ] Half-duplex: a turn that records then plays does not stick on “device busy” without a retry/settle path.
- [ ] Button press during TTS stops playback.
- [ ] Unplug/replug recovers button + LED + ALSA without restarting the listener process.
- [ ] A `turn_complete` event includes numeric stage latencies. Transcripts are not required on any remote collector.

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Returns a compiled LangGraph. No checkpointer required for the spike. |
| `graph.invoke({"messages": ...})` | Accepts accumulated session messages. |
| `.env` / `LLM_*` | Same provider factory as `thelab-chat`. |
| Editable install | `pip install -e <this-repo>` from the I/O venv. |

## Relationship to other specs

- **001** — long-term voice agent (Riva/NIM/streaming). This spike is explicitly uncommitted to those choices.
- **007** — Spark memory budget. STT/TTS stay on CPU so the GPU slot can stay with a ~30B worker or stay free.
- I/O-repo specs (USB hotplug, session transcripts, blueprint-informed latency) refine *this* spike; they do not replace it.

## Open questions (left to the I/O repo)

- Exact Piper voice file location and fallback order.
- Whether OTEL goes to a LAN hub or stays JSONL-only.
- Whether to extract a modular pipeline later (spec 001 / blueprint Option B). Not required to call the spike done.
