# Technical Plan: DGX Spark Hardware Optimization & Sweet-Spot Discovery (007)

**Feature**: 007-dgx-hardware-optimization  
**Related Spec**: [spec.md](./spec.md)  
**Date**: 2025-05-22  
**Implementation Branch**: `feat/007-dgx-hardware-optimization-impl`

## 1. Goal

Execute the strategy defined in the spec with rigorous measurement:

- Capture an accurate **baseline** on the current production configuration (120B + full Riva on single DGX Spark).
- Run controlled experiments for the highest-leverage changes (lightweight English audio stack, 49B model swap).
- Quantify headroom, voice turn latency, concurrency limits, and memory behavior.
- Make a data-driven decision on the **sweet-spot configuration**.
- Document everything so future changes (including 2× node work) have a clear before/after reference.

Success = we have reproducible numbers and a locked "recommended daily driver" profile for the family voice agent.

## 2. High-Level Phases

### Phase 0 – Baseline Capture (Must Do First)
Establish the "as-is" numbers on the exact current stack before touching anything.

- Run on clean DGX Spark with current `docker-compose.yml` + nemotron-3-super-120b-a12b + full Riva.
- Instrument or manually measure the core metrics from the spec.
- Produce a `baseline-report.md` (or JSON + human summary) committed in the repo.

### Phase 1 – Audio Stack Reduction (Highest Leverage Quick Win)
Replace full Riva with a minimal English-only path (Parakeet CTC + high-quality English TTS NIM or equivalent).

- Create a lightweight audio service profile (new container or slimmed Riva config).
- Update `docker-compose` with profiles or separate override files.
- Re-run the benchmark harness.
- Compare delta vs baseline (memory saved, latency change, perceived voice quality).

**Decision gate**: If quality is acceptable and headroom improves significantly → adopt as new default.

### Phase 2 – Model A/B Testing (49B vs Current 120B)
Stand up `llama-3.3-nemotron-super-49b-v1.5` alongside the 120B.

- Add a second LLM service in compose (different port or profile).
- Make the agent configurable (env var or CLI flag) to point at different NIM endpoints.
- Run identical benchmark scenarios on both models (with the winning audio stack from Phase 1).
- Measure: latency (especially TTFT + full turn), memory headroom, subjective quality on memory-recall + household prompts, tool-calling reliability.

**Decision gate**: Choose primary model (likely 49B for daily use, 120B as optional "deep" mode).

### Phase 3 – Context & Memory Efficiency Tuning
With the chosen model + audio, optimize how we use the remaining headroom.

- Improve / implement aggressive yet high-quality summarization of long conversations before injection.
- Tune active context window size vs. KV cache cost.
- Measure impact on recall quality (via Supermemory) vs. memory usage and latency.
- Validate multi-user (2–4 concurrent simulated family members) stability.

### Phase 4 – Sweet-Spot Lock + Operationalization
- Update default `docker-compose.yml`, `.env` examples, and Makefile targets for the chosen configuration.
- Add documented "benchmark" and "profile" make targets.
- Update architecture docs and the 001 spec references.
- Create a "current sweet spot" section in the 007 directory with the final numbers and rationale.

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

- Keep the existing `docker-compose.yml` as the "current baseline" reference.
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

No optimization change lands in the default compose without passing through this measured gate.

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

**Ready to cut.** Once the spec PR is reviewed/merged, we will land the first pieces of the harness and capture the all-important baseline numbers on the actual DGX Spark hardware.