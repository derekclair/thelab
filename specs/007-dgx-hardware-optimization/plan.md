# Technical Plan: DGX Spark Hardware Optimization & Sweet-Spot Discovery (007)

**Feature**: 007-dgx-hardware-optimization  
**Related Spec**: [spec.md](./spec.md)  
**Date**: 2025-05-22 (living slot policy notes added 2026-08-19)  
**Implementation Branch**: `feat/007-dgx-hardware-optimization-impl`

## 1. Goal

Execute the strategy defined in the spec with rigorous measurement, **without** treating the 001 compose stack as live production.

- Keep the **living inference slot policy** (spec.md) aligned with the desk: one local generative LLM, CPU STT/TTS, hosted Grok for quality-critical fleet roles.
- Capture an accurate **live-path baseline** (spec 008 I/O + `get_agent()` + hosted Grok and/or one ~30B-class `openai_compatible` / Ollama worker). This is what actually runs.
- Treat **120B NIM + full Riva** (`docker-compose` in this repo) as an **optional experimental** capture — not “current production.” Do not invent GB figures; those runs stay unmeasured until a report exists.
- Run controlled experiments for high-leverage changes (lightweight English audio on the compose path if revived; ~30B vs 49B as the *single* occupied slot). **No 120B+ agent loops on one Spark** as a daily driver.
- Quantify headroom, voice turn latency, concurrency limits, and memory behavior.
- Make a data-driven decision on the **sweet-spot configuration**, or keep the living policy as practice-without-numbers, labeled unmeasured.
- Document everything so future changes (including 2× node work) have a clear before/after reference.

Success = the slot policy matches reality, and we have reproducible numbers (or an explicit “unmeasured” label) for a locked daily-driver profile for the household voice agent.

## 1.1 Inference slot policy (plan notes)

Matches [spec.md — Inference slot policy (living)](./spec.md#inference-slot-policy-living). This is how we schedule work on the GB10; the phases below are how we *measure*.

| Rule | Practice |
|------|----------|
| GB10 budget | ~128 GB unified, ~273 GB/s, **one serious local LLM at a time** |
| Live voice I/O | `conversational-voice-agent` (spec 008): Parakeet TDT 0.6B **CPU** STT + Piper **CPU** TTS |
| Brain | this repo `get_agent()` |
| Default LLM | hosted Grok |
| Local option | `openai_compatible` / Ollama ~30B-class, hosted fallback |
| This repo compose (`agent` + `riva` + `nemotron` 120b) | experimental; **not** the live spoken path |
| Quality-critical fleet | orchestrator, architect, reviewer, design → hosted Grok (do not fight the slot) |
| Local workers | coder, researcher → ~30B-class with hosted fallback |
| Forbidden on one Spark | 120B+ agent loops; a second large local LLM next to the occupied slot |
| Speech vs GPU | Prefer CPU STT/TTS so the unified/GPU slot stays with at most one generative LLM |

Harness work must label every report **live** vs **experimental-compose**. Phase 0 originally assumed compose 120B + Riva was the as-is stack; that assumption is **retired**.

## 2. High-Level Phases

### Phase 0 – Baseline Capture (Must Do First)
Establish numbers **before** changing the *experimental* compose stack — and, separately, sample the **live** path that already runs.

**0a. Live path (priority; this is as-is):**
- Spec 008 I/O (Parakeet CPU + Piper CPU) + `get_agent()` + hosted Grok, then the same with one ~30B-class local worker occupying the slot.
- Instrument or manually sample unified memory / CPU / (if a local LLM is up) GPU.
- Produce a live-path report. Do not invent GB figures if the sampler is not in place — leave TBD.

**0b. Experimental compose (optional; not production):**
- Clean DGX Spark with this repo’s `docker-compose.yml` + nemotron-3-super-120b-a12b + full Riva.
- Same metrics. Label the report experimental. NIM + Riva GB numbers remain **unmeasured** until this run exists.

Do not present 0b as “what we run today.”

### Phase 1 – Audio Stack Reduction (Compose experiment; live path already on CPU)

**Already practice (not a 007 deliverable):** live desk voice is Parakeet TDT 0.6B CPU + Piper CPU (spec 008). That was the high-leverage win for the spoken path. Do not plan this phase as if Riva is the live ASR.

**If compose/Riva is revived:** replace full Riva with a minimal English-only path (Parakeet CTC + high-quality English TTS NIM or equivalent).

- Create a lightweight audio service profile (new container or slimmed Riva config).
- Update `docker-compose` with profiles or separate override files.
- Re-run the benchmark harness.
- Compare delta vs the *experimental* compose baseline (memory saved, latency change, perceived voice quality). **Unmeasured** until that run exists.
- Prefer keeping speech off the GPU/unified generative slot.

**Decision gate**: Live default stays 008 CPU speech. Compose light-audio becomes the experimental default only if measured quality and headroom justify it.

### Phase 2 – Model A/B Testing (single occupied slot)

Living policy: **one** local generative LLM. Quality-critical fleet stays on hosted Grok. Local workers are ~30B-class with hosted fallback. Do **not** stand up 49B *alongside* 120B on one Spark.

A/B the **single** slot:

- Live option already: `openai_compatible` / Ollama ~30B-class vs hosted Grok (agent already routes via `LLM_PROVIDER` / `LLM_BASE_URL`).
- Optional experiment: `llama-3.3-nemotron-super-49b-v1.5` as the one loaded model (compose profile or override) — not a second concurrent NIM.
- 120B remains an optional labeled experiment, **not** a daily “deep mode” on one Spark (that *is* occupying the only slot with a forbidden-size loop).

Measure: latency (TTFT + full turn), memory headroom (**unmeasured** until sampled), subjective quality on memory-recall + household prompts, tool-calling reliability.

**Decision gate**: Confirm ~30B as the local-worker class, or promote 49B as the single-slot experiment winner. Do not lock 120B as optional always-on deep mode on one node.

### Phase 3 – Context & Memory Efficiency Tuning
With the chosen model + audio, optimize how we use the remaining headroom.

- Improve / implement aggressive yet high-quality summarization of long conversations before injection.
- Tune active context window size vs. KV cache cost.
- Measure impact on recall quality (via Supermemory) vs. memory usage and latency.
- Validate multi-user (2–4 concurrent simulated family members) stability.

### Phase 4 – Sweet-Spot Lock + Operationalization
- Do **not** make 120B + Riva the default compose “production” profile. Defaults must match the living slot policy (CPU speech lives in the I/O repo; this package is `get_agent()`; local LLM is optional ~30B-class).
- Update default `docker-compose.yml`, `.env` examples, and Makefile targets only for configurations we actually intend to run, and mark experimental profiles as such.
- Add documented "benchmark" and "profile" make targets.
- Update architecture docs and the 001 spec references so they do not re-introduce the old production framing.
- Create a "current sweet spot" section in the 007 directory with the final numbers and rationale — or an explicit unmeasured label.

### Phase 5 – 2× DGX Spark Preparation (Future, After Phase 4)
- Design multi-node compose / orchestration approach (tensor-parallel for 340B or service separation).
- Document networking (RDMA) requirements and expected gains.
- Optional: small spike to validate 2-node connectivity and basic sharding.

## 3. Benchmark Harness Design

We will build a lightweight, reproducible measurement system.

### 3.1 Core Components
- `benchmarks/` directory at repo root (or inside `scripts/benchmarks/`).
- `benchmark_runner.py` (or Typer CLI `thelab-bench`).
- Scenarios: 
  - Single-user short turns (typical Q&A + memory recall).
  - Multi-turn long-context household conversation.
  - Concurrent simulation (2–4 "users" via scripted or parallel processes).
- Metrics collection:
  - Voice turn latency (instrumented in VoiceOrchestrator or via external timing around the full loop).
  - LLM TTFT + generation speed (via callbacks or NIM metrics if exposed).
  - Peak / average memory (system + per-container via `docker stats`, `nvidia-smi`, or `psutil` + CUDA).
  - Error / OOM / swap events.
  - Thermals / power (optional, via `tegrastats` or similar on Grace).

### 3.2 Instrumentation Points (Temporary or Permanent)
- Add timing hooks in `src/thelab_langchain/voice/orchestrator.py` (end-of-speech → transcript ready → agent response start → first audio out).
- Expose a `--benchmark` mode that logs structured JSON lines.
- Sidecar measurement script that samples memory every 1–2 seconds during a run.

### 3.3 Reporting
- Each run produces a timestamped report directory: `benchmarks/reports/2025-05-22-baseline/`
- Contains: `metrics.json`, `summary.md`, raw logs, `nvidia-smi.log`, container stats.
- A small script to generate comparison tables between two reports.

### 3.4 Make Targets (for DX on DGX and Mac)
- `make benchmark-baseline`
- `make benchmark-light-audio`
- `make benchmark-49b`
- `make benchmark-report COMPARE=baseline,light-audio`

These will be thin wrappers that set the right compose profiles + env and invoke the harness.

## 4. Docker & Deployment Changes

- Keep the existing `docker-compose.yml` as the **experimental compose** reference (agent + riva + nemotron 120b). It is **not** the live spoken path and **not** the production baseline.
- Introduce compose profiles or override files:
  - `docker-compose.light-audio.yml`
  - `docker-compose.49b.yml`
  - Later: `docker-compose.2node.yml` (or separate stack)
- Make the LLM service tag and Riva vs light-audio configurable via environment (REGISTRY + MODEL_TAG + AUDIO_PROFILE).
- Ensure non-root, healthchecks, and easy `docker compose --profile` usage remain.

The agent code itself should require **minimal** changes for the experiments (mostly config + endpoint URLs).

## 5. Data-Driven Decision Process

After each major phase we will:
1. Run the benchmark harness (at least 3–5 representative sessions).
2. Commit the raw report + a human-readable `results-phase-N.md`.
3. Update the decision matrix in the spec (or a living `decision-log.md`).
4. Hold a quick "gate" discussion (even async via PR comment or the issue tracker) before proceeding to the next phase.

No optimization change lands in the default compose without passing through this measured gate. Do not land a 120B+ daily loop on one Spark even if a report looks flattering — that violates the living slot policy.

## 6. Risks & Mitigations

- **DGX access / iteration speed**: All heavy runs happen on the real hardware. Harness must be quick to launch and tear down.
- **Subjective voice quality**: Objective metrics + a small set of "golden" household-style prompts for human listening tests.
- **NIM model availability & download time**: Pre-pull images; document exact tags used in every report.
- **Reproducibility**: Pin exact image digests + compose files + env in every report.
- **Measurement overhead**: Keep the harness itself as lightweight as possible so it doesn't distort the numbers.

## 7. Deliverables

- Benchmark harness + reporting tooling (reusable for future experiments).
- 4–6 committed benchmark reports with clear deltas.
- Updated default deployment configuration for the chosen sweet spot.
- Living documentation (in `specs/007-.../` and `docs/`) that future team members (or future us) can follow.
- Clear go/no-go + resource numbers for moving to 2× DGX Spark.

## 8. Timeline Philosophy

We are not optimizing in the dark. Every day of work on this branch should produce either:
- A new measurement, or
- A concrete code/config change that is immediately measured against the previous baseline.

This keeps the loop tight and the excitement high.

---

**Ready to measure the live slot.** Harness work should start from the desk path (008 + `get_agent()`), not from a fictional 120B + Riva production stack. Experimental compose numbers stay optional and labeled unmeasured until captured.