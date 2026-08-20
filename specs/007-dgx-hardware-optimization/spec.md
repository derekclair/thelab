# Spec: DGX Spark Hardware Optimization & Sweet-Spot Strategy

**Feature ID**: 007-dgx-hardware-optimization  
**Status**: Draft / Strategy & Benchmarking Spec (living slot policy added 2026-08-19)  
**Related to**: 001-voice-dgx-spark-agent, 002-multi-user-support, 003-deployment-infrastructure, 008-local-tts-lenovo-go-spike  
**Created**: 2025-05-22  
**Branch**: `feat/007-dgx-hardware-optimization`

## Overview

We have reached the point where we need a deliberate, measurable optimization strategy for the voice-first LangGraph + Supermemory agent running on NVIDIA DGX Spark hardware (single node today, with an eye toward 2× DGX Spark).

**Honest live path (what actually runs on the desk today — not the 001 compose hypothesis):**
- Desk voice I/O: [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) (spec 008) — Parakeet TDT 0.6B CPU STT + Piper CPU TTS
- Brain: this repo’s `get_agent()`; default LLM is hosted Grok (xAI); local option is `openai_compatible` / Ollama ~30B-class with hosted fallback
- `docker-compose` in this repo (`agent` + `riva` + `nemotron` 120b) is **experimental**, not the live spoken path
- See [Inference slot policy (living)](#inference-slot-policy-living) for the one-local-LLM budget and fleet-role split

**Original 001 compose hypothesis (experimental / unmeasured on this Spark — do not read as “what we run today”):**
- LLM: `nvcr.io/nim/nvidia/nemotron-3-super-120b-a12b:latest` (120B hybrid MoE/Mamba, ~12B active params, 1M native context)
- Voice: Full NVIDIA Riva (NeMo ASR + TTS) via gRPC sidecar
- Agent: LangGraph StateGraph with proactive Supermemory injection + reactive memory tools
- Deployment: Docker on DGX Spark (single node)

The user wants:
- Formal expectations so we can **benchmark expected vs. actual** performance.
- Clear headroom calculations for Riva + Nemotron (current and future models).
- Evaluation of **dropping Riva entirely** for English-only household use (rely on lighter Nemotron-era audio paths or dedicated small speech models).
- Resource profile for the "big boi" Nemotron-4 340B-class model and what headroom remains for the rest of the application.
- Expected gains and architecture implications of a **2× DGX Spark** multi-node setup.
- Trade-off framework and a process for finding the **sweet spot** under real hardware constraints.

This spec establishes the measurement baseline, decision framework, and optimization levers. Implementation and concrete experiments will follow in subsequent plan/tasks once this spec is reviewed and locked.

## Hardware Reality: DGX Spark (Single Node)

Key characteristics that drive every optimization decision:

- **GB10 Grace Blackwell Superchip** (Blackwell GPU + 20-core Arm CPU: 10 performance + 10 efficiency cores)
- **128 GB unified LPDDR5X memory** (coherent between CPU and GPU, ~273 GB/s bandwidth). This is the single most important constraint: model weights, KV cache, activations, Riva models, agent process, OS, Docker overhead, and audio I/O all compete for the same pool. There is no separate "VRAM."
- High AI throughput (up to ~1 PFLOP FP4 on Tensor Cores) but memory-bound for large models + long context.
- Storage: 4 TB NVMe
- Networking: 10 GbE + dual 100/200 GbE ConnectX-7 (RDMA capable)
- Power/thermals: ~140 W SoC, ~240 W PSU, designed for quiet/home-lab operation

**Implication**: Every added service (Riva, larger model, longer context, multiple concurrent household conversations) directly reduces headroom for the "rest of the app" (LangGraph execution, Supermemory client calls, VAD, playback, future tools). **One serious local generative LLM at a time** on this chip; see the living slot policy below.

## Inference slot policy (living)

This section is the operating policy for the single GB10. It **corrects** earlier 007/001 wording that treated 120B NIM + full Riva as the live spoken path. That stack remains a valid *experiment* if we ever want numbers for it; it is not what we run today.

### Hardware budget (qualitative — no invented GB figures)

- GB10: ~128 GB unified LPDDR5X, ~273 GB/s, coherent CPU + GPU. There is no separate VRAM.
- **One serious local LLM at a time.** Do not run 120B+ agent loops on one Spark.
- Prefer keeping the GPU / unified slot for **at most one** local generative LLM.
- STT/TTS on CPU is a **deliberate** budget choice: Parakeet TDT 0.6B (CPU) and Piper (CPU) leave the slot free for a ~30B-class worker, or empty while hosted Grok does the turn.

Measured NIM + Riva footprints on this Spark are **still unmeasured**. Ranges elsewhere in this spec (40–70 GB, 10–25 GB, etc.) stay **engineering estimates / TBD**, not inventory.

### Honest live path

| Layer | What actually runs |
|-------|-------------------|
| Voice I/O | spec 008 / `conversational-voice-agent`: Parakeet TDT 0.6B CPU STT + Piper CPU TTS |
| Brain | this repo `get_agent()` |
| Default LLM | hosted Grok (xAI) |
| Local LLM option | `openai_compatible` / Ollama, ~30B-class, hosted fallback if the slot is busy or the local endpoint is down |
| This repo `docker-compose` (`agent` + `riva` + `nemotron` 120b) | experimental; **not** the live spoken path |

### Fleet roles vs the slot

Quality-critical roles **do not** occupy the local slot — they use hosted Grok so they never fight a worker for unified memory:

- orchestrator, architect, reviewer, design → hosted Grok

Local workers **may** occupy the single slot, with hosted fallback:

- coder, researcher → ~30B-class local (`openai_compatible` / Ollama)

When the slot is occupied, other work uses hosted models. Do not co-schedule a second large local LLM. Workstation fleet ops live in Hermes (`~/.hermes/docs/agentic-workflow.md`); this spec only owns the **memory-budget** rule.

### Policy rules

1. At most one local generative LLM loaded on the Spark.
2. No 120B+ (or 340B) agent loops on a single Spark.
3. Keep STT/TTS on CPU unless a measured experiment shows GPU speech still leaves the generative slot intact.
4. Treat compose 120B + full Riva as an optional harness target, not production.
5. Do not publish GB “we use X GB today” numbers until a 007 report lands them.

### What this spec still measures

The rest of 007 (baseline harness, light-audio vs full Riva, 49B vs 120B A/B, 2× Spark) remains useful **experiment design**. Those runs are gated on real hardware numbers. They are **not** a claim that the experimental stack is the daily driver.

## Current baseline (live vs experimental)

### Live desk path (practice today)

- **Voice**: Parakeet TDT 0.6B via NeMo on CPU + Piper CPU TTS (spec 008).
- **Brain**: `get_agent()` in this package.
- **LLM**: hosted Grok by default; optional local ~30B-class via `openai_compatible` / Ollama.
- **Slot**: CPU speech; GPU/unified reserved for at most one ~30B-class worker (or idle).

We do **not** yet have a committed 007 harness report for this live path’s unified-memory samples either. Latency and quality notes belong in 008 / the I/O repo until a 007 report exists.

### Experimental compose stack (001 hypothesis — unmeasured)

If we stand up this repo’s compose on the Spark, the intended services are:

- **LLM**: nemotron-3-super-120b-a12b (120B total / ~12–12.7B active per token via hybrid MoE + Mamba).
- **Context**: Native 1M tokens (practical NIM limits often 128K–256K depending on profile and KV precision).
- **Voice**: Full Riva stack (Parakeet-class ASR + high-quality TTS, multilingual capable).
- **Expected characteristics** (**unmeasured** on this Spark; exact TBD via NIM profile + `nvidia-smi` / container stats):
  - Model load + idle memory: Significant fraction of 128 GB (exact TBD).
  - Real-time voice turn latency (end-of-speech → first audio out): Target sub-second natural feel.
  - Concurrent household users: Originally designed for a single primary user; multi-user will increase memory pressure.

We do **not** have hard numbers on this exact DGX Spark + Docker + Riva + 120B combination. This spec still exists to create those numbers **if** we run that experiment. Do not treat the 120B + Riva row as the current daily driver.

## Model Comparison

| Model | Params (Total / Active) | Context | Architecture | Expected Footprint (Single Spark) | Strengths for Our Use Case | Weaknesses / Risks | Voice Latency Impact |
|-------|--------------------------|---------|--------------|-----------------------------------|----------------------------|--------------------|----------------------|
| **nemotron-3-super-120b-a12b** (experimental compose; **not** the live daily driver) | 120B / ~12B active | 1M native (NIM ~128–256K practical) | Hybrid Mamba + Transformer MoE | High (community reports; tight with Riva + long ctx). **Unmeasured** on this Spark. **Forbidden as a daily agent loop** on one Spark under the living slot policy. | Best agentic reasoning, tool use, long-horizon memory recall, retains large Supermemory context without constant re-fetch | Occupies the only local slot; fights voice/fleet workers; risk of swapping under load | Higher TTFT + decode latency vs lighter models |
| **llama-3.3-nemotron-super-49b-v1.5** (strong candidate) | 49B dense | 128K | NAS-optimized dense Transformer | Medium (comfortable headroom on single Spark) | Excellent accuracy/efficiency; fast tokens/s; proven on H100-class; lower latency, more room for Riva or concurrent users | Smaller context than 120B (may require more aggressive summarization) | Best-in-class for its size; fastest turn times of the three |
| **nemotron-4-340b-instruct** ("big boi") | 340B dense | 4K native (extendable) | Dense Transformer | Impractical on single node even heavily quantized; feasible on 2× via tensor-parallel | Maximum raw intelligence and instruction following; potential "reasoning brain" for hardest queries | Enormous memory (hundreds of GB raw); high latency even sharded; overkill for most voice turns | Significantly higher latency; best used selectively or for offline tasks |

**Recommendation for primary inference path (updated by the living slot policy)**: Live daily driver is **hosted Grok** for quality-critical work and **at most one ~30B-class local worker** (coder / researcher) when we want on-box generation. The 49B v1.5 remains a strong *experiment* if we measure a single-slot local voice/brain. The 120B is **not** an optional always-on “deep thinker” on one Spark — swapping it in *is* occupying the only local slot, and the policy forbids 120B+ agent loops on a single node. 340B stays multi-node-only.

## Audio Stack: Can We Axe Riva?

**Live path already did, on CPU.** Spec 008 / `conversational-voice-agent` uses Parakeet TDT 0.6B (NeMo, CPU) + Piper CPU TTS. That is the desk spoken loop. Full Riva in this repo’s compose is an experimental sidecar, not production audio.

The remainder of this section is still useful as an experiment design **if** we ever bring Riva (or a GPU speech NIM) onto the Spark next to a local LLM.

**Experimental compose “current”**: Full Riva (enterprise-grade, multi-language, multiple models for ASR + TTS).

For an **English-only household**, the multilingual enterprise features are mostly wasted.

**Lighter English-only alternatives**:
- Pin to **Parakeet 1.1B CTC English** (or smaller 0.6B variants) via dedicated lightweight ASR NIM or direct NeMo inference — typically 2–8 GB for real-time streaming.
- High-quality **English-only TTS** (single or a few voices) — another 4–8 GB.
- Total audio stack: **4–12 GB** instead of 10–25+ GB for full Riva.

**Benefits of dropping full Riva**:
- Reclaim 8–15+ GB of unified memory (**estimate, unmeasured**) → directly usable for larger KV cache (longer effective context), a higher-quality single local model, or leaving the slot free.
- Simpler deployment (fewer sidecars, smaller attack surface, faster startup).
- Lower CPU/GPU contention during voice turns.

**Risks / Trade-offs**:
- Lose easy future multilingual support (acceptable per current requirement).
- Must validate English quality and latency of the lighter path (Parakeet CTC is already very strong for English).
- Potential future desire for "voice cloning" or multiple family voices — still doable with lighter dedicated voices.

**Conclusion**: For the English-only household voice agent we already run a minimal CPU Parakeet + Piper path (spec 008). If the compose experiment is revived, prefer that same “light English audio” posture over full Riva so the unified slot stays with at most one generative LLM. GPU speech NIMs are an experiment, not a default, until measured.

## Headroom Analysis (Single DGX Spark, 128 GB Unified)

Rough engineering estimates (**unmeasured** on this Spark — to be replaced by harness reports; do not treat as live inventory):

**Always-present baseline**:
- OS + Docker + non-root agent container + Python + sounddevice + VAD + Supermemory client + LangGraph overhead + checkpointers: **8–15 GB**

**LLM (weights + typical KV for voice turns)**:
- 120B MoE (optimized NIM FP8/lower): **40–70 GB** depending on active context window and quantization profile. (Active ~12B helps enormously vs dense 120B.)
- 49B dense (optimized): **25–45 GB** — significantly more comfortable.
- 340B (even heavily quantized): **150+ GB** — impossible on single node without extreme measures.

**Audio (Riva vs lighter)**:
- Full Riva concurrent ASR+TTS: **10–25 GB**
- English-only Parakeet + TTS: **4–12 GB**

**Headroom for "the rest of the app"** (reactive tool calls, memory injection, future vision/tools, burst concurrency):
- Experimental 120B + full Riva: **Very tight** (estimate, often <10–15 GB free under load — **unmeasured**). Risk of OOM, swapping, or forced context truncation during long household conversations. **Not** the live daily driver.
- 49B + lighter audio: **Healthy headroom** (20–40+ GB free, **unmeasured**) → more room for longer context or future capabilities if that single slot is occupied by 49B rather than 120B.
- 120B + lighter audio: **Recoverable** vs full Riva (**unmeasured**) — still a 120B+ loop on one Spark, so **not** a living-policy daily driver even if headroom improves.

**Key insight (living policy)**: The biggest lever already in practice is **not occupying the GPU/unified slot with speech** (CPU Parakeet + Piper) and **not loading a second local LLM**. The next lever, if we revive compose experiments, is still **not running full Riva next to a large NIM**, then **model class** (~30B worker vs 49B experiment vs 120B — the last is forbidden as a daily loop on one Spark).

## Multi-Node (2× DGX Spark) Projections

Two nodes give us:
- 256 GB total unified memory (128 GB each)
- Excellent inter-node bandwidth via dual 200 GbE ConnectX-7 RDMA (theoretical very high; early community reports ~8 GB/s bidirectional practical)
- Official 2-node support from NVIDIA; community has run 3+ nodes

**What we gain**:
1. **Run the 340B "big boi"** via tensor-parallel / pipeline-parallel sharding across the two nodes. Each node holds ~half the weights + portion of KV. Feasible but higher latency than the 49B/120B on single node. Best used as an on-demand "deep reasoning" service rather than the primary voice responder.
2. **Scale the current 120B** with much larger effective context (or higher batch / concurrent sessions) without swapping.
3. **Separate concerns**: Node A = heavy LLM inference (120B or 340B shard); Node B = voice I/O + lighter agent orchestration + memory tools. Reduces contention on the voice path.
4. **Family concurrency**: Comfortably support 4–8+ simultaneous or overlapping household conversations.
5. **Redundancy / failover** for an always-on home device.
6. **Future headroom**: Add vision models, additional tools, or a second "specialist" LLM without immediate hardware purchase.

**What it costs**:
- Complexity: multi-node Docker Compose / Kubernetes or custom orchestration, RDMA networking setup, model sharding configuration.
- Latency: Cross-node communication for tensor-parallel adds some overhead (acceptable for the 340B case; less ideal for every voice turn).
- Power/heat/noise: Two units running.
- Cost and physical space.

**Expectation**: 2× setup moves us from "tight single-node optimization" to "comfortable production with room to grow." It is the natural next hardware step once we outgrow a well-tuned single Spark.

## Benchmarking Methodology & Expectations vs. Actuals

We will establish a repeatable benchmark harness before making major changes.

### Core Metrics (voice turn focus)
- **Voice turn latency**: Time from end-of-speech (VAD) to first audio chunk out (p50 / p95). Target: <800 ms feels natural; <1.2 s acceptable.
- **TTFT** (time to first token) + **tokens per second** during generation.
- **End-to-end perceived latency** including memory injection + tool use.
- **Memory usage at key points**: Idle after load, during active voice turn, peak during long-context recall + multiple tool calls.
- **Concurrency**: Max stable simultaneous family members before degradation.
- **Stability**: No OOM / swap over 30–60 min household usage sessions.
- **Thermals / power / noise**: Important for a living-room/home device.

### Baseline Capture (First Experiment on Current Stack)

Two different “baselines” — do not collapse them:

**A. Live path (practice; still needs a 007 report):** spec 008 I/O + `get_agent()` + hosted Grok and/or one ~30B-class `openai_compatible` worker. CPU STT/TTS. This is what the desk actually runs.

**B. Experimental compose (001 hypothesis; unmeasured):** single DGX Spark, this repo’s `docker-compose.yml` with 120B NIM + full Riva. Optional harness target only.

If we run **B**:
1. Clean boot, measure idle memory.
2. Run scripted voice sessions (single user, then 2–3 overlapping).
3. Capture all metrics above + full `nvidia-smi` / container memory + system logs.
4. Document exact NIM profiles, quantization settings, Riva config, and context management strategy used.
5. Label the report experimental — not “production baseline.”

### Subsequent Experiments (Compare Against Baseline)
- 120B + lighter English audio only
- 49B v1.5 + lighter English audio
- Same with aggressive memory summarization / context window tuning
- 2× node configurations (once hardware available)

Every change must be accompanied by before/after numbers against the baseline. "It feels faster" is not enough — we log hard data.

## Optimization Levers & Trade-off Framework

Primary levers (ranked by expected impact on single-node headroom + latency):

1. **Do not fight the slot** (living policy, already practice): one local generative LLM; STT/TTS on CPU; quality-critical fleet on hosted Grok.
2. **Audio stack reduction** (full Riva → English Parakeet + TTS): Highest immediate win *if* compose/Riva is revived; live path already uses CPU Parakeet + Piper.
3. **Model class** (~30B local worker vs 49B experiment vs 120B): 120B is not a daily loop on one Spark. 49B remains an A/B candidate for a *single* occupied slot.
4. **Context strategy** (aggressive summarization + proactive injection vs. raw long context): Reduces KV pressure and improves recall quality.
5. **Quantization / NIM profile tuning**: FP8, NVFP4, lower KV precision where quality allows.
6. **Concurrency limits & backpressure**: Limit parallel household sessions or queue intelligently.
7. **Process placement** (future): Move audio to a dedicated lightweight container or even separate node.
8. **2× node scaling**: When single-node sweet spot is exhausted — including when we want a second local LLM.

### Decision Matrix (Example)

| Configuration | Expected Headroom | Expected Voice Latency | Intelligence Level | Multi-User Comfort | Recommendation |
|---------------|-------------------|------------------------|--------------------|--------------------|----------------|
| Hosted Grok + CPU Parakeet/Piper (live) | Slot free or idle (**unmeasured** GB) | Dominated by network LLM + CPU speech | Highest for quality-critical roles | N/A (hosted) | **Live default** for orchestrator / architect / reviewer / design and for voice when no local worker is loaded |
| ~30B local worker + CPU Parakeet/Piper (live option) | Occupies the one local slot (**unmeasured** GB) | Local TTFT + CPU speech | Good for coder / researcher | One local LLM only | **Live local option** with hosted fallback; do not co-schedule a second LLM |
| 120B + Full Riva (experimental compose) | Low (**unmeasured**) | Medium-High | Highest | Poor | Experiment only; **not** live production; forbidden as a daily agent loop on one Spark |
| 120B + Light Audio | Medium (**unmeasured**) | Medium | Highest | Good | Experiment only; still a 120B+ loop on one Spark — policy says no |
| 49B + Light Audio | High (**unmeasured**) | Lowest | Very High | Excellent | Strong *single-slot* experiment; not claimed as measured sweet spot |
| 340B (2× sharded) | N/A (multi-node) | High | Maximum | Excellent | On-demand specialist brain; never a single-Spark daily loop |

## Recommended Path to Sweet Spot (Single Node First)

1. **Immediate (living policy — already practice, document it)**: Treat the live path as 008 CPU speech + `get_agent()` + hosted Grok / one ~30B local worker. Do not call 120B + Riva “production.”
2. **Measure the live slot** (still open): idle vs one ~30B worker vs CPU STT/TTS; no invented GB figures until a report exists.
3. **Optional compose experiment**: If we want numbers, capture a labeled *experimental* baseline on 120B + Riva — not a production baseline.
4. **High-leverage experiment (compose only)**: Replace Riva with minimal English audio; re-benchmark. Live path already did the CPU version.
5. **Model A/B**: ~30B worker vs 49B v1.5 as the *single* occupied slot; 120B is not a daily-driver candidate on one Spark.
6. **Context tuning**: summarization + injection; measure recall quality vs. KV usage on the chosen single local model.
7. **Decision gate**: confirm the living slot policy with measured numbers (or keep it as practice-without-numbers, labeled unmeasured).
8. **2× node phase**: Once the single-node slot is understood and we need more (concurrency, 340B, or a second local LLM), move to multi-node architecture.

## Success Criteria

- The living slot policy is written down and matches the desk (CPU speech, one local LLM, hosted Grok for quality-critical roles).
- We have a documented, reproducible benchmark baseline for the **live** stack, and (optionally) a clearly labeled experimental 120B + Riva report. Neither is claimed without a report.
- We have measured data (not guesses) for at least two alternative configurations (light audio, 49B model).
- We can articulate "the sweet spot" with numbers: model choice, audio stack, max comfortable context, max concurrent users, and expected voice turn latency.
- The chosen configuration leaves **measurable, comfortable headroom** (>15–20 GB) for the agent, memory system, and future features under typical household load.
- We have a clear, data-driven recommendation on whether/when to move to 2× DGX Spark and what that unlocks.

## Open Questions & Risks

- Exact real-world memory footprint of the 120B NIM on DGX Spark unified memory (with our Docker setup) — **unmeasured**; optional experiment, not a live-path unknown.
- Exact real-world footprint of one ~30B-class Ollama / `openai_compatible` worker plus CPU Parakeet + Piper — **unmeasured** (practice exists; 007 report does not).
- Quality delta between full Riva voices and lighter English TTS options for family members (subjective but important).
- Whether 128K context on the 49B is "enough" given our Supermemory + summarization strategy, or whether we will miss the 1M capability.
- Practical limits of 2-node RDMA tensor-parallel for the 340B in a home setting (latency, stability, complexity).
- Future desire for on-device voice cloning or multiple distinct family voices — does this push us back toward a heavier audio stack later?
- Energy / heat / noise profile of sustained operation (especially 2×) in a living space.

## Next Steps

1. Keep the living slot policy in sync with the desk (this section is the source of truth for “what occupies the Spark”).
2. `plan.md` / `tasks.md` in this folder already exist; extend them when adding harness work — do not re-open 120B + Riva as the implied production path.
3. Implement the benchmark harness and capture a **live-path** report (CPU speech + hosted Grok and/or one ~30B worker). NIM + Riva GB numbers stay `[ ]` until measured.
4. Optional: labeled experimental compose runs (audio reduction, 49B vs 30B). No 120B+ daily loops.
5. Iterate to a measured sweet spot; until then, practice follows the living policy and estimates stay labeled unmeasured.

---

**We are getting there.** This spec gives us the map, the measuring stick, and the decision framework so we can move from "it works" to "it is optimal under our real constraints" with confidence and excitement. The living slot policy is how we use the one local generative slot **today**; the rest of the document is how we measure experiments without pretending they are production.

**Status**: Living policy in effect. Benchmark numbers for NIM + Riva (and for the live 30B worker) remain unmeasured until a 007 report lands.