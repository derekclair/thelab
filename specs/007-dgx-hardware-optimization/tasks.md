# Tasks: DGX Spark Hardware Optimization & Sweet-Spot Discovery (007)

**Feature**: 007-dgx-hardware-optimization  
**Related Spec**: [spec.md](./spec.md)  
**Related Plan**: [plan.md](./plan.md)  
**Status**: Ready for implementation  
**Branch**: `feat/007-dgx-hardware-optimization-impl`

This document breaks the work into small, dependency-ordered, checkable tasks. The first priority is always **capturing a trustworthy baseline** before any changes.

Mark tasks complete only after the work is committed and (where applicable) the corresponding benchmark report is added.

---

## Phase 0 – Baseline Capture (Highest Priority)

### T0.1 – Project Structure for Benchmarking
- [ ] Create `benchmarks/` directory at repo root with `__init__.py` and `README.md` explaining the harness.
- [ ] Add `benchmarks/reports/` (gitignored except for `.gitkeep` and example reports).
- [ ] Update `.gitignore` if needed for report artifacts.

### T0.2 – Benchmark Runner Skeleton
- [ ] Create `benchmarks/runner.py` (or `benchmarks/cli.py`) using Typer or argparse for a `thelab-bench` entry point.
- [ ] Support basic flags: `--scenario short|long|concurrent`, `--duration`, `--user`, `--output-dir`.
- [ ] Implement structured JSON logging of events (turn start, end-of-speech, transcript, agent response, first audio, errors).

### T0.3 – Instrumentation in Voice Layer
- [ ] Add optional timing / event hooks in `src/thelab_langchain/voice/orchestrator.py` (or a small `timing.py` helper).
  - Record: `end_of_speech_ts`, `transcript_ready_ts`, `agent_first_token_ts`, `first_audio_out_ts`.
- [ ] Make instrumentation toggleable via env var (`BENCHMARK_MODE=1`) so it doesn't affect normal runs.
- [ ] Ensure the existing voice loop still works cleanly when the hooks are disabled.

### T0.4 – Memory & System Metrics Collection
- [ ] Add a lightweight sampler (background thread or separate process) that records:
  - Docker container memory / CPU (via `docker stats` API or subprocess).
  - `nvidia-smi` output (memory, utilization, power).
  - System RAM / swap.
- [ ] Integrate sampling into the benchmark runner for the duration of a run.

### T0.5 – Baseline Run on DGX (Current Stack)
- [ ] On clean DGX Spark, pull the exact current images (120B + full Riva).
- [ ] Run the benchmark harness against the existing `docker-compose.yml`.
- [ ] Execute at least one "short turns" session and one "long household conversation" session.
- [ ] Capture full report (metrics, logs, nvidia-smi samples, container stats).
- [ ] Commit the report as `benchmarks/reports/2025-05-XX-baseline-120b-riva/` (with `summary.md` + `raw/`).

### T0.6 – Baseline Documentation
- [ ] Write `specs/007-dgx-hardware-optimization/results/phase-0-baseline.md` summarizing the measured numbers against the expectations in the spec.
- [ ] Update the decision matrix in the spec (or a living `decision-log.md`) with actual data.

---

## Phase 1 – Audio Stack Reduction

### T1.1 – Lightweight English Audio Service Definition
- [ ] Research and select the exact lighter image(s): Parakeet English CTC NIM (or equivalent small ASR) + English TTS.
- [ ] Create `docker-compose.light-audio.yml` (or profile) that replaces the full Riva service with the slimmed version.
- [ ] Document exact tags, ports, and healthcheck expectations in the compose file and a small `audio-profiles.md`.

### T1.2 – Agent / Orchestrator Compatibility
- [ ] Verify (or lightly adapt) the Riva gRPC client code to work with the new lighter service (same gRPC surface if possible).
- [ ] Add `AUDIO_PROFILE=light` (or `full`) env handling in config / compose.

### T1.3 – Light Audio Benchmark Run
- [ ] Deploy the light-audio profile on DGX.
- [ ] Re-run the same benchmark scenarios used in baseline.
- [ ] Produce report `benchmarks/reports/...-light-audio/`.

### T1.4 – Phase 1 Gate & Decision
- [ ] Compare memory headroom, voice turn latency (p50/p95), and subjective quality.
- [ ] Write `results/phase-1-audio-reduction.md`.
- [ ] Decision recorded: adopt light audio as new default (or keep full Riva).

---

## Phase 2 – Model Comparison (49B Candidate)

### T2.1 – Second LLM Service in Compose
- [ ] Add support for `llama-3.3-nemotron-super-49b-v1.5` (new service definition or override).
- [ ] Make the agent LLM endpoint configurable (`LLM_BASE_URL`, `LLM_MODEL` or similar) so we can point at different NIMs without code changes.
- [ ] Create `docker-compose.49b.yml` profile.

### T2.2 – 49B Benchmark Runs
- [ ] With the winning audio stack from Phase 1, run identical scenarios on the 49B model.
- [ ] Capture full metrics + at least one side-by-side human listening session for quality.
- [ ] Produce report and `results/phase-2-49b-comparison.md`.

### T2.3 – Phase 2 Gate
- [ ] Update decision matrix with real latency + headroom numbers.
- [ ] Lock primary model recommendation (49B daily driver + 120B optional deep mode is the current hypothesis).

---

## Phase 3 – Context & Efficiency Tuning

### T3.1 – Summarization / Context Window Experiments
- [ ] Enhance the memory injection logic (or add a summarizer node) to keep effective context while reducing KV cache pressure.
- [ ] Define 2–3 different context strategies as config options.
- [ ] Benchmark the impact on memory usage, recall quality (test prompts that rely on older memories), and latency.

### T3.2 – Concurrency / Multi-User Stability
- [ ] Add a concurrent benchmark mode that simulates 2–4 overlapping household conversations.
- [ ] Measure stability and headroom under load with the chosen model + audio.
- [ ] Document maximum comfortable concurrent users.

---

## Phase 4 – Sweet-Spot Operationalization

### T4.1 – Default Configuration Update
- [ ] Update the main `docker-compose.yml` (or make the winning profiles the easy defaults via env).
- [ ] Add high-level `make` targets: `make benchmark`, `make profile-sweet-spot`, etc.
- [ ] Update `docs/development.md` and any DGX runbooks with the new recommended command sequence.

### T4.2 – Final Results Package
- [ ] Write `results/final-sweet-spot.md` with the locked configuration, all key metrics, and rationale.
- [ ] Update the top-level spec with "Measured Sweet Spot" section (post-experiment).

### T4.3 – Cleanup & Polish
- [ ] Remove or clearly mark temporary instrumentation so normal runs have zero overhead.
- [ ] Ensure the benchmark harness is reusable and well-documented.

---

## Phase 5 – 2× DGX Spark Preparation (Stretch / Future)

- [ ] Document multi-node networking requirements (ConnectX-7 RDMA setup on the two Sparks).
- [ ] Create initial `docker-compose.2node.yml` skeleton or separate stack definitions.
- [ ] Optional spike: basic tensor-parallel or service-separation test on 2 nodes (if hardware available).
- [ ] Update the 007 spec with concrete multi-node headroom and latency expectations based on real data.

---

## Cross-Cutting / Ongoing

- [ ] Keep all benchmark reports committed with pinned image digests and exact compose/env used.
- [ ] Every significant change on this branch must be accompanied by a new report or clear "no measurement impact" note.
- [ ] Update the project tracker with the current phase as we progress.

---

**First actionable tasks**: T0.1 – T0.3 (get the harness skeleton + instrumentation in place) so that the very first DGX run (T0.5) produces trustworthy, comparable numbers.

Let's go get those baseline numbers!