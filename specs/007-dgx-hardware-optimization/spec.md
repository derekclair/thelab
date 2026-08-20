# Spec: DGX Spark Hardware Optimization & Sweet-Spot Strategy

**Feature ID**: 007-dgx-hardware-optimization  
**Status**: Draft / Strategy & Benchmarking Spec  
**Related to**: 001-voice-dgx-spark-agent, 002-multi-user-support, 003-deployment-infrastructure  
**Created**: 2025-05-22  
**Branch**: `feat/007-dgx-hardware-optimization`

## Overview

We have reached the point where we need a deliberate, measurable optimization strategy for the voice-first LangGraph + Supermemory agent running on NVIDIA DGX Spark hardware (single node today, with an eye toward 2× DGX Spark).

Current production configuration (as of Feature 001):
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

**Implication**: Every added service (Riva, larger model, longer context, multiple concurrent family conversations) directly reduces headroom for the "rest of the app" (LangGraph execution, Supermemory client calls, VAD, playback, future tools).

## Current Baseline (What We Are Running Today)

- **LLM**: nemotron-3-super-120b-a12b (120B total / ~12–12.7B active per token via hybrid MoE + Mamba). Excellent agentic/tool-calling and long-context reasoning — ideal for our Supermemory injection + multi-turn household conversations.
- **Context**: Native 1M tokens (practical NIM limits often 128K–256K depending on profile and KV precision).
- **Voice**: Full Riva stack (Parakeet-class ASR + high-quality TTS, multilingual capable).
- **Expected characteristics** (to be validated on hardware):
  - Model load + idle memory: Significant fraction of 128 GB (exact TBD via NIM profile).
  - Real-time voice turn latency (end-of-speech → first audio out): Target sub-second natural feel.
  - Concurrent family users: Currently designed for single primary user; multi-user will increase memory pressure.

We do **not** yet have hard numbers on this exact DGX Spark + Docker + Riva + 120B combination. This spec exists to create those numbers systematically.

## Model Comparison

| Model | Params (Total / Active) | Context | Architecture | Expected Footprint (Single Spark) | Strengths for Our Use Case | Weaknesses / Risks | Voice Latency Impact |
|-------|--------------------------|---------|--------------|-----------------------------------|----------------------------|--------------------|----------------------|
| **nemotron-3-super-120b-a12b** (current) | 120B / ~12B active | 1M native (NIM ~128–256K practical) | Hybrid Mamba + Transformer MoE | High (but runnable per community reports; tight with Riva + long ctx) | Best agentic reasoning, tool use, long-horizon memory recall, retains large Supermemory context without constant re-fetch | Highest memory/latency of the three practical options; risk of swapping under load | Higher TTFT + decode latency vs lighter models |
| **llama-3.3-nemotron-super-49b-v1.5** (strong candidate) | 49B dense | 128K | NAS-optimized dense Transformer | Medium (comfortable headroom on single Spark) | Excellent accuracy/efficiency; fast tokens/s; proven on H100-class; lower latency, more room for Riva or concurrent users | Smaller context than 120B (may require more aggressive summarization) | Best-in-class for its size; fastest turn times of the three |
| **nemotron-4-340b-instruct** ("big boi") | 340B dense | 4K native (extendable) | Dense Transformer | Impractical on single node even heavily quantized; feasible on 2× via tensor-parallel | Maximum raw intelligence and instruction following; potential "reasoning brain" for hardest queries | Enormous memory (hundreds of GB raw); high latency even sharded; overkill for most voice turns | Significantly higher latency; best used selectively or for offline tasks |

**Recommendation for primary inference path**: Start with the 49B v1.5 as the default "daily driver" for voice responsiveness while keeping the 120B as an optional "deep thinker" that can be swapped in for complex multi-step planning or heavy memory synthesis.

## Audio Stack: Can We Axe Riva?

Current: Full Riva (enterprise-grade, multi-language, multiple models for ASR + TTS).

For an **English-only household** (Derek + family), the multilingual enterprise features are mostly wasted.

**Lighter English-only alternatives**:
- Pin to **Parakeet 1.1B CTC English** (or smaller 0.6B variants) via dedicated lightweight ASR NIM or direct NeMo inference — typically 2–8 GB for real-time streaming.
- High-quality **English-only TTS** (single or a few voices) — another 4–8 GB.
- Total audio stack: **4–12 GB** instead of 10–25+ GB for full Riva.

**Benefits of dropping full Riva**:
- Reclaim 8–15+ GB of unified memory → directly usable for larger KV cache (longer effective context), higher quality model, or concurrent family sessions.
- Simpler deployment (fewer sidecars, smaller attack surface, faster startup).
- Lower CPU/GPU contention during voice turns.

**Risks / Trade-offs**:
- Lose easy future multilingual support (acceptable per current requirement).
- Must validate English quality and latency of the lighter path (Parakeet CTC is already very strong for English).
- Potential future desire for "voice cloning" or multiple family voices — still doable with lighter dedicated voices.

**Conclusion**: Yes — for the English-only family voice agent we can (and probably should) replace full Riva with a minimal English Parakeet + English TTS profile (or emerging smaller NVIDIA speech NIMs). This is one of the highest-leverage single changes available today.

## Headroom Analysis (Single DGX Spark, 128 GB Unified)

Rough engineering estimates (to be replaced by measured data):

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
- Current 120B + full Riva: **Very tight** (often <10–15 GB free under load). Risk of OOM, swapping, or forced context truncation during long family conversations.
- 49B + lighter audio: **Healthy headroom** (20–40+ GB free) → room for 2–4 concurrent family members, longer context windows, or future capabilities.
- 120B + lighter audio: **Recoverable** — may be the pragmatic sweet spot for intelligence + responsiveness.

**Key insight**: The biggest single lever for headroom today is **replacing full Riva with an English-only lightweight audio path**. The second biggest is **model choice** (49B vs 120B MoE).

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
1. Single DGX Spark, current 120B + full Riva Docker Compose.
2. Clean boot, measure idle memory.
3. Run scripted voice sessions (single user, then 2–3 overlapping).
4. Capture all metrics above + full `nvidia-smi` / container memory + system logs.
5. Document exact NIM profiles, quantization settings, Riva config, and context management strategy used.

### Subsequent Experiments (Compare Against Baseline)
- 120B + lighter English audio only
- 49B v1.5 + lighter English audio
- Same with aggressive memory summarization / context window tuning
- 2× node configurations (once hardware available)

Every change must be accompanied by before/after numbers against the baseline. "It feels faster" is not enough — we log hard data.

## Optimization Levers & Trade-off Framework

Primary levers (ranked by expected impact on single-node headroom + latency):

1. **Audio stack reduction** (full Riva → English Parakeet + TTS): Highest immediate win.
2. **Model swap** (120B MoE → 49B dense): Large win on latency and headroom; acceptable quality trade for most turns.
3. **Context strategy** (aggressive summarization + proactive injection vs. raw long context): Reduces KV pressure and improves recall quality.
4. **Quantization / NIM profile tuning**: FP8, NVFP4, lower KV precision where quality allows.
5. **Concurrency limits & backpressure**: Limit parallel family sessions or queue intelligently.
6. **Process placement** (future): Move audio to a dedicated lightweight container or even separate node.
7. **2× node scaling**: When single-node sweet spot is exhausted.

### Decision Matrix (Example)

| Configuration | Expected Headroom | Expected Voice Latency | Intelligence Level | Multi-User Comfort | Recommendation |
|---------------|-------------------|------------------------|--------------------|--------------------|----------------|
| 120B + Full Riva | Low | Medium-High | Highest | Poor | Baseline only; optimize away |
| 120B + Light Audio | Medium | Medium | Highest | Good | Strong candidate if quality holds |
| 49B + Light Audio | High | Lowest | Very High | Excellent | Default daily driver target |
| 340B (2× sharded) | N/A (multi-node) | High | Maximum | Excellent | On-demand specialist brain |

## Recommended Path to Sweet Spot (Single Node First)

1. **Immediate (this branch / next sprint)**: Capture rigorous baseline on current 120B + Riva.
2. **High-leverage experiment**: Replace Riva with minimal English audio stack; re-benchmark.
3. **Model A/B**: Stand up 49B v1.5 side-by-side; measure latency + memory + subjective quality on household-style prompts + memory recall tasks.
4. **Context tuning**: Implement or improve summarization + injection strategy; measure impact on effective memory quality vs. KV usage.
5. **Decision gate**: Choose primary model + audio stack for the family deployment based on data.
6. **2× node phase**: Once single-node sweet spot is locked and we need more (concurrency, 340B, or future capabilities), move to multi-node architecture.

## Success Criteria

- We have a documented, reproducible benchmark baseline for the current stack.
- We have measured data (not guesses) for at least two alternative configurations (light audio, 49B model).
- We can articulate "the sweet spot" with numbers: model choice, audio stack, max comfortable context, max concurrent users, and expected voice turn latency.
- The chosen configuration leaves **measurable, comfortable headroom** (>15–20 GB) for the agent, memory system, and future features under typical household load.
- We have a clear, data-driven recommendation on whether/when to move to 2× DGX Spark and what that unlocks.

## Open Questions & Risks

- Exact real-world memory footprint of the 120B NIM on DGX Spark unified memory (with our Docker setup) — highest priority unknown.
- Quality delta between full Riva voices and lighter English TTS options for family members (subjective but important).
- Whether 128K context on the 49B is "enough" given our Supermemory + summarization strategy, or whether we will miss the 1M capability.
- Practical limits of 2-node RDMA tensor-parallel for the 340B in a home setting (latency, stability, complexity).
- Future desire for on-device voice cloning or multiple distinct family voices — does this push us back toward a heavier audio stack later?
- Energy / heat / noise profile of sustained operation (especially 2×) in a living space.

## Next Steps

1. Review and approve this spec (user + team).
2. Create `plan.md` and `tasks.md` under `specs/007-dgx-hardware-optimization/` following the established SDD process.
3. Implement the benchmark harness + first baseline capture.
4. Run the high-leverage experiments (audio reduction, model comparison).
5. Iterate to the sweet spot with data in hand.

---

**We are getting there.** This spec gives us the map, the measuring stick, and the decision framework so we can move from "it works" to "it is optimal under our real constraints" with confidence and excitement.

**Status**: Ready for review. Once approved, we will commit the spec and proceed to planning the concrete benchmarking and optimization work.