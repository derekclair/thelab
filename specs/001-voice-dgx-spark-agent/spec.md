# Feature Spec: Voice-Enabled Agent for NVIDIA DGX Spark

**Feature ID**: 001-voice-dgx-spark-agent  
**Status**: Draft  
**Created**: 2025-05-21  
**Owner**: Derek  

## Overview

Build a production-grade, voice-first intelligent agent that runs locally on NVIDIA DGX Spark hardware. The system combines high-quality local speech-to-text (STT) and text-to-speech (TTS) with a powerful reasoning brain built on LangGraph + Supermemory + a local Nemotron model served via NVIDIA NIM (with Grok as a fallback option).

The goal is a natural, low-latency voice conversation experience with long-term memory and tool use, packaged as a clean, deployable Docker-based agent.

## Hardware Target & Scaling Strategy

**Primary Target (v1)**: NVIDIA DGX Spark used as a **personal desktop AI workstation** — a machine sitting on the desk with physical microphone and speakers for natural, hands-free voice interaction. This is not a headless server deployment. The agent is intended to feel like a high-quality personal AI companion running locally on the device the user is working at.

**Current Practical LLM**: On single-node DGX Spark, we target a responsive local model in the **~30B Nemotron class** (explicit requirement: no 120B+ models). Served via NVIDIA NIM or NeMo/NeuTTS local inference (see `conversational-voice-agent`). Grok (xAI) remains the convenient high-quality fallback when local is unavailable.

**Future Scaling (Phase 2+)**: Acquire additional DGX Spark units (target 2–3 total) and cluster them to run the **full Nemotron 4 340b** (or equivalent 300B+ class model) at high quality while preserving the exact same voice, agent, and Supermemory experience. The voice + orchestration + LangGraph harness is deliberately designed to be portable across single-node efficient inference and multi-node clustered serving.

**Why this approach?**
- The software architecture, voice experience, memory system, and tool use are the long-lived, hard parts.
- Raw inference scale (more GPUs, better model) can be added later once the harness proves valuable on real desktop workloads.
- This keeps iteration fast on a single machine while leaving a clear path to the highest-quality local model the user wants.

## Goals

- Deliver a high-quality, natural voice interface (mic + speakers) for the LangGraph + Supermemory agent on a personal DGX Spark desktop.
- Enable excellent local voice experience on single-node DGX Spark using the best practical local LLM that still feels responsive in conversation.
- Make the entire system easy to package, deploy, and run (Docker-first) as a personal desktop agent.
- Preserve (and enhance) the excellent long-term memory capabilities provided by Supermemory.
- Design the voice + agent harness so it can later scale to multi-node DGX Spark clusters running full 340b-class models without major changes to the upper layers.

## Non-Goals (for v1)

- Full multi-user / multi-tenant support
- Complex visual UI (terminal + voice is primary)
- Running the absolute largest possible model (340b-class) on a *single* DGX Spark in v1 — we accept the best responsive local model available (~120b-class) while designing the system to scale to 340b+ on clustered hardware later.

## User Stories

1. As a power user with a DGX Spark on my desk, I want to talk naturally to my personal agent (using the physical mic and speakers) so that I can have fluid, hands-free conversations while working.
2. As a developer, I want the agent to remember everything important about me and my projects across many sessions (via Supermemory).
3. As a user with sensitive data, I want the voice processing (STT/TTS) to happen locally on my DGX Spark so nothing leaves the machine except the reasoning calls I choose.
4. As an operator, I want to deploy the agent as a single Docker container (or small compose stack) on a personal DGX Spark desktop with minimal configuration.
5. As a long-term planner, I want the voice + agent architecture to be portable so that when I add more DGX Spark units I can run significantly larger local models (full 340b-class) without rewriting the upper layers.

## Functional Requirements

### FR-1: Voice Interface
- High-quality, low-latency Speech-to-Text using **NVIDIA NeMo** (Conformer / FastConformer family or Riva ASR).
- Natural, expressive Text-to-Speech using **NVIDIA NeMo** TTS models (FastPitch, RadTTS, or newer) served via Riva or optimized NeMo inference.
- Strong preference for streaming-capable ASR and TTS to minimize perceived latency.
- Support for push-to-talk and Voice Activity Detection (VAD) for natural turn-taking.
- Ability for the user to interrupt the agent mid-speech (barge-in support).

### FR-2: Agent Brain (LangGraph + Supermemory)
- The existing LangGraph agent architecture (with Supermemory tools) becomes the core reasoning engine.
- The agent must be able to use tools while in a voice conversation.
- Long-term memory via Supermemory must remain first-class (profile + semantic recall + storage).
- Session persistence across restarts using thread IDs.

### FR-3: Packaging & Deployment on DGX Spark
- The entire stack (STT + TTS + Agent + optional local LLM) must be containerized using Docker.
- Provide a `docker-compose.yml` (or equivalent) optimized for DGX Spark GPU usage.
- Clear documentation for running on DGX Spark hardware (GPU passthrough, model storage, etc.).
- Support for model caching / volume mounts for large STT/TTS models.

### FR-4: Configuration & Extensibility
- Configuration via environment variables + `.env` (consistent with current project).
- Pluggable STT and TTS backends (easy to swap models).
- Option to route reasoning to either Grok (API) or a local LLM served via vLLM / Ollama / TensorRT-LLM on the DGX.

### FR-5: Developer Experience
- The current CLI (`thelab-chat`) should evolve to support voice mode.
- Good logging and observability for the voice pipeline (latency, STT confidence, etc.).
- Health checks and graceful degradation if voice components fail.

## Non-Functional Requirements

- **Latency**: End-to-end voice turn (listen → think → speak) should feel responsive (< 2.5s target on DGX Spark class hardware for typical queries).
- **Resource Efficiency**: Must be able to run alongside other workloads on DGX Spark without monopolizing all GPUs.
- **Reliability**: STT/TTS failures should not crash the agent; graceful fallback to text mode.
- **Security**: Local STT/TTS means audio never leaves the machine unless explicitly sent to the reasoning LLM.
- **Maintainability**: Clear separation between voice layer and brain layer.

## Success Criteria

- User can have a natural back-and-forth voice conversation with the agent on DGX Spark.
- The agent correctly recalls and uses long-term memories from Supermemory during voice sessions.
- The system runs from a single `docker compose up` command (after initial model download).
- Switching between Grok and a local LLM for the brain is possible with minimal code/config changes.
- Audio quality is subjectively good (natural voice, accurate transcription).
- Button/DTMF test passes: Agent signals with a distinct new tone; correctly handles sequence of Microsoft Teams, Call Answer, Call End, Mute button presses with spoken continuity from user; mute is handled gracefully (hardware-level, no audio after).

## Button / DTMF Test Scenario (Call Control)

**Test Procedure** (to be executed in a telephony voice call with the local-tts service):

1. Agent generates a distinct "new tone" (special audio signal via local-tts / NeuTTS or tone generator) to indicate readiness.
2. User pushes buttons in order and speaks after each:
   - 1. Microsoft Teams button
   - 2. Call Answer
   - 3. Call End
   - 4. Mute (suspected hardware mute — agent should detect loss of audio)
3. After each press, user speaks a short phrase for continuity.
4. Agent should detect DTMF tones or call events via the telephony provider and respond appropriately (e.g., acknowledge, handle call state changes, log for audit).

**Requirements for local-tts + Voice Agent**:
- Support for DTMF detection and button event handling in the telephony webhook.
- Ability to generate distinct tones (new/custom tone for signaling).
- Graceful handling of mute (detect silence or a telephony call event, pause TTS, resume on unmute).
- Integration with a private VPN for secure webhook delivery.
- Observability via nv-monitor during the test (GPU/CPU during tone generation and call).

This test validates call control, hardware button integration, and robustness of the local TTS service exposure.

## Technology Decisions (Locked)

**Voice Layer (STT + TTS)**: **NVIDIA NeMo** (with Riva inference stack where appropriate) is the chosen technology.

Rationale:
- Native, best-in-class performance on DGX Spark / Blackwell hardware.
- Excellent support for low-latency streaming ASR and TTS.
- Consistent NVIDIA stack (easier optimization, TensorRT export, GPU utilization).
- Future-proofs us for fine-tuning custom voices or domain-specific ASR on the same hardware.

We will use NeMo models (e.g., Conformer / FastConformer for ASR, FastPitch + HifiGAN or newer NeMo TTS models) served via NVIDIA Riva or direct NeMo inference optimized with TensorRT-LLM / ONNX Runtime.

This decision was confirmed during spec review.

**Spike / Prototype Vehicle note (2026-06-12)**: The interim Lenovo Go hardware loop is specified in [008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md) and executed in [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent). Live path is ALSA + Parakeet (NeMo CPU) + Piper, calling `get_agent()` in this package. It is uncommitted to the Riva / telephony / NIM compose choices in this spec.

## Related Work

- Current spike lives on the `langchain` orphan branch (`src/thelab_langchain/agent/`)
- Supermemory + LangGraph memory tools already partially designed
- DGX Spark used as a personal desktop workstation (with physical voice I/O) is the primary target hardware for v1
- Future multi-node DGX Spark clusters are the explicit scaling path for full 340b-class local models

## Current Phase: Local High-Quality LLM on Single-Node DGX Spark (2026)

**Decision**: For the initial desktop deployment on a single DGX Spark, we use the official NVIDIA NIM container for the ~120b Nemotron model (`nvcr.io/nim/nvidia/nemotron-3-super-120b-a12b`) rather than raw Hugging Face weights served through vLLM or Docker Model Runner.

**Rationale**:
- The official NIM provides a stable, well-supported OpenAI-compatible endpoint with good performance on DGX Spark.
- It proved more reliable in practice than Docker Model Runner + vLLM for this class of model on the current hardware.
- The agent already supports the `openai_compatible` LLM provider, making integration straightforward.
- This approach keeps the voice + agent harness unchanged while giving us a high-quality local brain today.

**Endpoint**: The NIM exposes `http://localhost:8000/v1` (OpenAI chat completions compatible).

**Trade-offs accepted**:
- We accept a small amount of vendor lock-in to NVIDIA's NIM packaging for the local model (acceptable given the hardware target).
- Docker Model Runner is retained for lighter experimentation and smaller models, but is no longer the primary path for the main reasoning model.

This phase focuses on getting a rock-solid single-node experience with voice + 120b-class local LLM before scaling to multi-node 340b+.

---

**Next**: After review, generate `plan.md` (technical architecture) and `tasks.md`.
