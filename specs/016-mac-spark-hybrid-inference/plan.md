# Plan: Hybrid Apple Silicon + DGX Spark inference research (016)

**Feature**: 016-mac-spark-hybrid-inference
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20
**Status**: Specified / not executed. Human go required before Phase A.

## 1. Two planes (do not mix them)

```
desk today
  Mac ── Ethernet / Tailscale ── Spark     agent plane (already real)
         get_agent() / Hermes
         Grok default; optional ~30B slot

research (not green)
  Spark CUDA ds4  ── disk .kv file ──►  Mac Metal ds4     Phase B, gated
  Mac Metal memory ⇄ USB-C RDMA ⇄ Spark CUDA memory       MCDMA, watch only
```

The agent plane does not wait on this research. KV / tensor work, if it ever
ships, is a **second** plane. Do not route Hermes over MCDMA. Do not treat
file copy as RDMA.

## 2. What already exists

- Spec 007 living slot: one local generative LLM on the Spark; CPU STT/TTS;
  hosted Grok for quality-critical roles; optional ~30B-class worker.
- Spec 008 spoken loop: I/O sibling + `get_agent()`. Sentence-chunked TTS and
  `tts_ttfa_ms` already exist **there**.
- Mac ↔ Spark agent use over Ethernet / Tailscale.

This plan does not re-tune those paths.

## 3. MCDMA — watch, do not implement

Public 2026-08 posts describe Metal↔CUDA RDMA over USB-C. Closed source until
the author publishes source and license.

**Do:**

- Watch the public account for OSS + license.
- Keep author-reported BW / RTT labeled **author-reported** (spec table).
- If source + license land: clone **their** tree, run **their** tests on
  one Spark + Apple Silicon Mac in the lab, write a decision memo. Still not
  a Hermes cutover.

**Do not:**

- Start an implementation repo, bindings layer, or “thin wrapper” while the
  code is closed.
- Build two-Spark CX7 fabric.
- Treat 939 MB/s / 24 µs (or any other author figure) as a lab result.
- Block ds4 Phase A on MCDMA. The tracks are independent.

On OSS drop the first honest work is a single-link bench, then a toy tensor
or KV shuttle — **after** a human go, **after** license review. Prefer
upstream hooks over a lab fork.

## 4. ds4 spike — plan only until go

Execution is **out of tree**. Do not vendor [antirez/ds4](https://github.com/antirez/ds4)
into `thelab`. This repo keeps SDD only.

### Human gates

| Gate | Who | Unlocks |
|------|-----|---------|
| Specify (this folder) | Done | Nothing executable |
| **Go Phase A** | Human | Spark-only CUDA + disk KV + loopback server |
| **Go Phase B** | Human, after A green | File-based Spark-prefill → Mac-decode + identity |
| Hermes default change | Out of scope for the spike | — |

An agent must not clone, download weights, or start `ds4-server` from this
card without the Phase A go.

### Phase A — Spark-only CUDA (must pass)

Goal: prove ds4 is usable on this Spark for Flash q2 with disk KV and a
localhost server. No Mac. No RDMA.

Suggested sequence after go:

1. **Quiesce the 007 slot.** Unload / stop the local Nemotron (or any other
   serious generative LLM). Sequential, not stacked. Do not delete models.
2. **Clone + pin.** `git clone https://github.com/antirez/ds4.git` outside
   this repo. Record `git rev-parse HEAD`. `make cuda-spark`. If the Spark
   target fails, capture the log; do not silently switch to a generic CUDA
   target without checking GB10 flags.
3. **Weights.** `./download_model.sh ds4f-q2` only. Skip PRO, MXFP4, and
   DSpark until CLI + disk KV are green. Engine loads **ds4 GGUFs only**.
4. **CLI smoke.** Load Flash q2 at a modest context (start around 8k).
   Greedy (`--temp 0`) short prompt. Pass = completes without OOM or driver
   crash; host stays interactive.
5. **Disk KV + server.** Dedicated on-host directory with an explicit size
   cap (`--kv-disk-dir`, `--kv-disk-space-mb`).  
   `./ds4-server ... --host 127.0.0.1 --port 8090`  
   Cold chat completion → restart process → same prefix should hit disk KV.
   Do not bind `0.0.0.0`.
6. **Notes + teardown.** Record commit, quant, pass/fail, blockers. Stop
   `ds4-server`. Restore the 007 agent path (Ollama / ~30B or hosted Grok).

Spark is single-GPU: no `--cuda-tensor-parallel`.

Phase A exit: all of the above, or an explicit fail with a blocker. Phase A
fail → no Phase B.

### Phase B — optional file-based handoff

Proceed only if Phase A is green, identical GGUF can live on both boxes, and
a human still wants the experiment.

1. **Same commit, same GGUF.** Metal `make` on the Apple Silicon Mac in the
   lab. Checksum the GGUF against Spark.
2. **Same-machine baselines** before handoff: greedy tokens for prompt P on
   Mac-only and Spark-only. Document backend delta so handoff noise is
   separable.
3. **Handoff.** Spark prefills P and writes disk KV. Copy the KV artifact
   over the existing network (Wi-Fi first). Mac loads KV and decodes
   **without** prefilling P.
4. **Identity gate.** ≥99% greedy token match vs Mac-local full prefill
   (temperature 0, continuation length N recorded in notes, e.g. 64 or 128).
   Fail closed on miss — that is a valuable negative result.
5. **Timing only after the gate.** Small contexts first (8k, 32k — not a
   500k safari). Compare time-to-first-decode-token:
   Spark prefill + ship + Mac load vs Mac-local prefill. Then Mac decode.
   Schedule 10GbE only if identity holds and ship time dominates.

Pacary shipping projections and tweet tok/s figures stay **author-reported**.
Upstream README GB10 / Metal tables stay **upstream-reported**. Our numbers
are whatever Phase A/B notes record after go.

### Decision tree after a real spike

```
Phase A fail            → document blocker; no Mac work
Phase A pass, no Mac    → optional loopback ds4-server for DeepSeek-shaped
                          research/coding only; still not Hermes default
Phase B identity fail   → keep Spark-only; negative result is the finding
Phase B identity pass
  + ship < Mac prefill  → interesting hybrid; write a follow-up spec
  + ship > Mac prefill  → interesting science; not a daily driver without
                          a faster second plane (still not MCDMA-by-hope)
```

## 5. Slot, voice, and defaults

| Rule | Plan consequence |
|------|------------------|
| 007 one local LLM | Flash q2 **is** the occupied slot while the spike runs |
| No 120B+ | Unchanged |
| No Hermes profile cutover | Do not point architect/coder/reviewer at ds4-server |
| 008 TTFA | Hybrid decode is not the spoken path in this plan. If a later spec
  proposes it, first-audio must not regress; measure `tts_ttfa_ms` before
  calling it a win |
| Second plane | Tailscale/Ethernet agents keep working if ds4 is down |

## 6. What we will not do in this plan

- Execute Phase A or B from this folder without a human go.
- Copy research-note trees, home-directory layouts, or cache paths into git.
- Implement RDMA, wrap a closed MCDMA binary, or start a lab MCDMA repo.
- Two-Spark CX7 fabric.
- Multi-tenant `ds4-server`.
- Stack ds4 + full local Nemotron.
- Change Hermes profile defaults.
- Vendor `ds4` as a submodule of `thelab`.
- Claim author or upstream benches as ours.
- Open `ds4-server` on a non-loopback bind as part of the spike.
- Use hybrid decode on the 008 loop “to try it” without a TTFA comparison.

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Unified-memory fight with the 007 slot | Sequential load; teardown restores agents |
| Closed MCDMA copied or wrapped | Watch-only until source + license |
| False hybrid speed claims | Identity ≥99% before any timing narrative |
| KV not portable CUDA → Metal | That is Phase B; fail closed |
| Beta `main` churn | Pin commit after green smoke |
| Policy leak into Hermes | Explicit non-goal; review rejects default edits |
| Voice first-audio regression | Hybrid is not the live I/O path; 008 gate if it ever is |
| Docs imply it already runs | Status line on every file in this folder |
| Disk fill from KV | Size-capped dedicated directory |
| Author numbers become “our” numbers | Citations section; labels on every borrowed figure |

## 8. Success

A developer reading this folder can say:

- Hybrid Metal/MLX + CUDA is the north star for **KV/tensor research**.
- MCDMA is watch-only; numbers in the spec are author-reported.
- ds4 is a planned spike, not executed, not the agent backend.
- Phase A is Spark-only; Phase B is file KV with an identity gate.
- 007 slot and 008 TTFA still constrain any future green light.
- Nothing here was committed as running code.

Phase A/B success criteria live in [spec.md](./spec.md) and
[tasks.md](./tasks.md). They stay unchecked until a human go and real notes.
