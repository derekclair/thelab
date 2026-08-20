# Tasks: DGX Spark Hardware Optimization & Sweet-Spot Discovery (007)

**Feature**: 007-dgx-hardware-optimization  
**Related Spec**: [spec.md](./spec.md)  
**Related Plan**: [plan.md](./plan.md)  
**Status**: Ready for implementation (living slot policy recorded 2026-08-19)  
**Branch**: `feat/007-dgx-hardware-optimization-impl`

This document breaks the work into small, dependency-ordered, checkable tasks. The first priority is always **capturing a trustworthy baseline** before any changes — and labeling **live** vs **experimental-compose**. Do not treat 120B NIM + full Riva as the production spoken path.

Mark tasks complete only after the work is committed and (where applicable) the corresponding benchmark report is added. Policy-practice items below may be `[x]` without a 007 report when they already match the desk; **memory-number** items stay `[ ]` until measured.

---

## Inference slot policy (living) — practice vs unmeasured

Canonical text: [spec.md — Inference slot policy (living)](./spec.md#inference-slot-policy-living).

### T-SLOT.1 – Honest live path (already practice)

- [x] Desk voice I/O is spec 008 / `conversational-voice-agent`: Parakeet TDT 0.6B CPU STT + Piper CPU TTS (not this repo’s Riva orchestrator).
- [x] Brain is this repo `get_agent()`; default LLM is hosted Grok; local option is `openai_compatible` / Ollama ~30B-class with hosted fallback.
- [x] This repo’s `docker-compose` (`agent` + `riva` + `nemotron` 120b) is documented as experimental, not the live spoken path.
- [x] Policy recorded: GB10 ~128 GB unified / ~273 GB/s; **one serious local LLM at a time**; no 120B+ agent loops on one Spark.
- [x] STT/TTS on CPU is an explicit budget choice so the GPU/unified slot stays with at most one generative LLM.

### T-SLOT.2 – Fleet vs slot (already practice)

- [x] Quality-critical roles (orchestrator, architect, reviewer, design) use hosted Grok and do not occupy the local slot.
- [x] Local workers (coder, researcher) use ~30B-class with hosted fallback.
- [x] Do not co-schedule a second large local LLM next to an occupied slot.

### T-SLOT.3 – Unmeasured NIM + Riva (and live-slot) memory numbers

Do **not** invent GB figures. Leave TBD until a harness report exists.

- [ ] Measured idle + load unified-memory footprint of the 120B NIM on this Spark (experimental compose).
- [ ] Measured full Riva ASR+TTS unified-memory footprint on this Spark (experimental compose).
- [ ] Measured peak for 120B NIM + full Riva + agent during a voice turn (experimental compose).
- [ ] Measured idle vs occupied-slot samples for one ~30B-class `openai_compatible` / Ollama worker plus CPU Parakeet + Piper (live path).
- [ ] Written 007 report that labels live vs experimental-compose and does not call 120B + Riva “production.”

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

### T0.5a – Live-path baseline (as-is desk; priority)
- [ ] On the Spark, sample the spec 008 I/O loop + `get_agent()` with hosted Grok (slot idle).
- [ ] Repeat with one ~30B-class local worker occupying the slot (hosted fallback still configured).
- [ ] Execute at least one short-turns session and one longer household conversation on the live voice path.
- [ ] Capture whatever metrics the harness can take (do not invent GB figures).
- [ ] Commit as `benchmarks/reports/YYYY-MM-DD-baseline-live-cpu-speech/` (with `summary.md` + `raw/`), labeled **live**.

### T0.5b – Experimental compose run (120B + Riva; not production)
- [ ] On clean DGX Spark, pull the compose images (120B NIM + full Riva). Optional experiment only.
- [ ] Run the benchmark harness against this repo’s `docker-compose.yml`.
- [ ] Execute at least one "short turns" session and one "long household conversation" session.
- [ ] Capture full report (metrics, logs, nvidia-smi samples, container stats).
- [ ] Commit as `benchmarks/reports/YYYY-MM-DD-experimental-120b-riva/` (with `summary.md` + `raw/`), labeled **experimental-compose**, never “production baseline.”

### T0.6 – Baseline Documentation
- [ ] Write `specs/007-dgx-hardware-optimization/results/phase-0-baseline.md` summarizing measured numbers against the spec. Separate live vs experimental. Leave NIM + Riva GB as **unmeasured** if T0.5b has not run.
- [ ] Update the decision matrix in the spec (or a living `decision-log.md`) with actual data, or keep estimates labeled unmeasured.

---

## Phase 1 – Audio Stack Reduction (compose experiment)

Live path already uses CPU Parakeet + Piper (T-SLOT.1). Phase 1 is only if we revive Riva/NIM speech in compose.

### T1.1 – Lightweight English Audio Service Definition
- [ ] Research and select the exact lighter image(s): Parakeet English CTC NIM (or equivalent small ASR) + English TTS. Prefer not occupying the generative GPU slot.
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
- [ ] Compare memory headroom, voice turn latency (p50/p95), and subjective quality (**unmeasured** until T1.3).
- [ ] Write `results/phase-1-audio-reduction.md`.
- [ ] Decision recorded: live default remains 008 CPU speech; compose light-audio vs full Riva is experimental only.

---

## Phase 2 – Model Comparison (single occupied slot)

Do not load 49B *and* 120B at once. Living policy: one local generative LLM.

### T2.1 – Alternate LLM as the one slot occupant
- [x] Agent LLM endpoint already configurable (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`) for hosted Grok vs `openai_compatible` / Ollama.
- [ ] Add support for `llama-3.3-nemotron-super-49b-v1.5` as an **alternate** single-slot occupant (new service definition or override — not a concurrent second NIM).
- [ ] Create `docker-compose.49b.yml` profile, marked experimental.

### T2.2 – 49B Benchmark Runs
- [ ] With the winning audio stack from Phase 1, run identical scenarios on the 49B model.
- [ ] Capture full metrics + at least one side-by-side human listening session for quality.
- [ ] Produce report and `results/phase-2-49b-comparison.md`.

### T2.3 – Phase 2 Gate
- [ ] Update decision matrix with real latency + headroom numbers, or keep **unmeasured**.
- [ ] Lock local-worker class (~30B with hosted fallback is the living-policy hypothesis). Do **not** lock 120B as optional always-on deep mode on one Spark.

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
- [ ] Do not default compose to 120B + Riva as “production.” Experimental profiles stay named experimental.
- [ ] Update the main `docker-compose.yml` (or make the winning profiles the easy defaults via env) only for stacks we intend to run.
- [ ] Add high-level `make` targets: `make benchmark`, `make profile-sweet-spot`, etc.
- [ ] Update `docs/development.md` and any DGX runbooks with the new recommended command sequence (live path = 008 I/O + `get_agent()`).

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

**First actionable tasks**: T-SLOT is recorded. Harness skeleton remains T0.1 – T0.3 so the first DGX run (T0.5a live path, optional T0.5b experimental compose) produces trustworthy, comparable numbers. NIM + Riva GB items in T-SLOT.3 stay `[ ]` until measured.

Let's go get those baseline numbers — and keep calling the live path the live path.