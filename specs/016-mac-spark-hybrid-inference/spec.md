# Feature Spec: Hybrid Apple Silicon + DGX Spark inference research

**Feature ID**: 016-mac-spark-hybrid-inference
**Status**: Specified / not executed. Human go required before Phase A.
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [007-dgx-hardware-optimization](../007-dgx-hardware-optimization/spec.md)
(one local generative slot),
[008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md)
(TTFA must not regress if hybrid decode is ever used)

Public sources (not our benches):
[antirez/ds4](https://github.com/antirez/ds4),
[danpacary](https://x.com/danpacary/status/2086851964261003615),
[ashxhart](https://x.com/ashxhart/status/2089749434087227672)

## Honest current state

This folder is a **research contract**, not a feature in `thelab_langchain`.

Nothing in this spec has been executed. There is no ds4 build, no disk-KV
handoff, and no Metal↔CUDA RDMA path in this lab. Do not read the folder as
“hybrid inference is running.”

| Surface | Today |
|---------|--------|
| Agent path | Unchanged: this repo `get_agent()`; hosted Grok default; optional local ~30B-class on the Spark (spec 007). |
| Voice I/O | Spec 008 sibling. STT/TTS on CPU. Spoken loop does **not** use ds4 or MCDMA. |
| Mac ↔ Spark agents | Ethernet / Tailscale already exists. That is the **agent** plane. |
| ds4 (DwarfStar) | Spike **plan** only. Not cloned, not built, not served. |
| MCDMA | **Watch** only. Closed source until the author publishes source and license. |

Ethernet/Tailscale stays the agent plane. MCDMA or a ds4 KV ship would be a
**second plane** (tensor / KV), if either ever goes green. They do not replace
the agent network.

## Overview

**North star:** evaluate hybrid local inference — Apple Silicon Mac in the lab
(Metal / MLX) plus DGX Spark (CUDA) — especially KV and tensor paths, not
chat-over-LAN.

Two independent tracks:

1. **MCDMA** (Metal CUDA Direct Memory Access) — public posts, 2026-08.
   Claimed USB-C RDMA between Metal unified memory and CUDA memory. **Watch.**
   Do not start an implementation repo until source and license are public.
2. **DwarfStar `ds4`** — public engine at [antirez/ds4](https://github.com/antirez/ds4).
   Optional file-based Spark-prefill → Mac-decode, in the shape of the Pacary
   experiment. **Plan a spike; do not execute until a human says go.**

`ds4` does **not** replace the Hermes / thelab agent path (Nemotron ~30B /
Grok). It is a parallel research engine for ds4-specific DeepSeek V4 (and
related) GGUFs.

## Goals

- Write down the north star so later work does not silently become “new default
  agent backend.”
- Keep MCDMA as watch-only until OSS + license.
- Specify a ds4 spike that is Spark-only first (Phase A), then optional
  file-based heterogeneous KV (Phase B).
- Require an identity gate (≥99% greedy token match) **before** any hybrid
  speed claim.
- Bind any `ds4-server` to loopback (`127.0.0.1`).
- Obey spec 007: one local generative LLM on the Spark; do not stack ds4 with
  a full local Nemotron.
- Protect spec 008: if hybrid decode is ever used on a spoken path, time to
  first audio must not regress.

## Non-goals

- 120B+ agent loops (spec 007).
- Multi-tenant serving.
- Implementing RDMA / MCDMA ourselves, or wrapping a closed binary.
- Two-Spark ConnectX-7 fabric (this lab is one Spark).
- Changing Hermes profile defaults in the spike.
- Vendoring `ds4` into this repo.
- Replacing Ethernet / Tailscale agent traffic with a KV plane.
- Treating author-reported or upstream README numbers as our benches.
- Wiring hybrid decode into the live 008 voice loop in this spec’s delivery.

## User stories

1. As the operator, I can tell a researcher: hybrid Metal/CUDA is a **watch +
   planned spike**, not production, and the agent still uses Grok / ~30B.
2. As the person who would run Phase A, I know Spark-only CUDA + disk KV +
   localhost server is the whole first gate, and I must not start without a
   human go.
3. As the person who might run Phase B, I know file copy of KV is the
   experiment, identity comes before speed, and Wi-Fi is first.
4. As a reviewer of git, I reject MCDMA implementation work, 007 slot stacking,
   Hermes default cutover, and pasted author benches labeled as ours.
5. As the 008 voice owner, I know this track must not worsen `tts_ttfa_ms` if
   it ever touches the spoken path.

## Two tracks (do not merge them)

```
existing agent plane
  Mac ── Ethernet / Tailscale ── Spark   (Hermes / get_agent(); already real)

research second plane (not green)
  (A) ds4 file KV:  Spark CUDA prefill → disk .kv → copy → Mac Metal decode
  (B) MCDMA:        Metal ↔ CUDA RDMA over USB-C     [watch; closed]
```

MCDMA is not “faster ds4.” File-based KV is not a substitute for RDMA. Prove
or reject each on its own evidence.

### Track 1 — MCDMA (watch)

Public posts describe:

- Registered memory and rkeys
- One-sided READ/WRITE
- Two-sided SEND/RECV with credit-based flow control
- Symmetric verbs (no master/slave)
- Transport: USB-C (author: USB3-class rates today; USB4 if a locked
  controller can train)

**Our topology if it ever opens:** one Spark + Apple Silicon Mac in the lab
over USB-C. The author’s two-Spark CX7 + dual USB-C Studio diagram is
**reference only**. We do not build that fabric.

Author-reported figures from the 2026-08 public post
([ashxhart](https://x.com/ashxhart/status/2089749434087227672)). **Unverified
here. Label as author-reported. Do not treat as our benches.**

| Metric (author-reported) | Value |
|--------------------------|-------|
| Single USB-C link | 939 MB/s |
| Mac → both Sparks, concurrent | 1.80 GB/s |
| Both Sparks → Mac, concurrent | 1.25 GB/s |
| Round-trip | 24 µs |
| Small-message rate | 41k msg/s |

“Every byte delivery verified” is the author’s claim. Reproduce only after
source + license are public.

**Standing rule:** do not start an implementation repo until source and
license are public. Prefer upstream integration (when it exists) over a
closed-source fork.

### Track 2 — ds4 spike (plan, not executed)

[antirez/ds4](https://github.com/antirez/ds4) is a narrow native engine
(Metal / CUDA / ROCm) for ds4-specific GGUFs — not a general llama.cpp zoo,
not a Nemotron loader. Spark target: `make cuda-spark`. Mac target: Metal
`make`. Surfaces: CLI, `ds4-server` (OpenAI- and Anthropic-style HTTP),
optional agent binary. First-class **disk KV** (content-addressed prefix
files) is why a file-based handoff is even thinkable.

Pacary’s public experiment
([danpacary](https://x.com/danpacary/status/2086851964261003615)): Spark
prefill, Mac decode, same byte-identical GGUF, ship disk KV, Wi-Fi then
10GbE. Shipping-time projections and tweet prefill rates in that post are
**author-reported, not our benches.** We adopt the **correctness gate**, not
the speed narrative:

> A handed-off cache must produce ≥99% token-identical greedy output vs
> prefilling locally. Correctness first, then speed.

Upstream `ds4` README GB10 vs Metal tables are **upstream-reported**, not
lab results. They motivate why Spark-prefill / Mac-decode is interesting
(CUDA prefill vs Metal decode asymmetry). They are not a substitute for
Phase A notes.

#### Phase A — Spark-only (must pass before any Mac work)

- CUDA build (`make cuda-spark`); record commit SHA.
- Flash q2 weights only for the first spike (skip PRO / MXFP4 / tensor-parallel).
- CLI greedy short prompt succeeds.
- Disk KV: cold prefill → process restart → warm prefix hit.
- `ds4-server` chat completion on **localhost**.
- Teardown: stop the server; restore the 007 agent slot (do not leave Flash
  resident next to Nemotron).

Spark is a **single-GPU** target. Do not pass CUDA multi-GPU tensor-parallel
flags on this box.

#### Phase B — optional file-based handoff (separate human go)

Only if Phase A is green **and** a human wants Mac time.

- Same commit and **byte-identical** GGUF on Mac and Spark (checksum).
- Mac Metal build.
- Spark writes KV for prefix P; file lands on the Mac; Mac decodes
  continuation **without** prefilling P.
- Identity: ≥99% greedy token match vs Mac-local full prefill of P
  (same prompt, temperature 0, fixed continuation length recorded in notes).
- Fail closed: if the gate fails, stop speed work. A negative result is
  still a result.
- Transfer timing on the existing network first; 10GbE tuning is deferred
  until identity passes.
- No “faster E2E” claim until identity **and** a timed comparison:
  `(Spark prefill + ship + Mac load)` vs `Mac-local prefill`, plus Mac decode.

Phase B is file copy. It is not MCDMA.

## Functional requirements

### FR-1 Status honesty

Docs, PRs, and commit messages **MUST** say specified / not executed until
Phase A notes exist. Do not imply a live hybrid path.

### FR-2 MCDMA is watch-only

- No implementation repo, bindings, or vendored blob while source or license
  is unpublished.
- Author-reported BW / RTT **MUST** stay labeled author-reported.
- Two-Spark CX7 + dual Mac links are out of scope.

### FR-3 ds4 does not replace the agent path

- Hermes / thelab defaults stay Grok (quality-critical) and ~30B-class local
  (optional worker).
- `get_agent()` is unchanged by this spec.
- A localhost `ds4-server`, if it ever stands, is a **named research/coding
  endpoint**, not a silent profile cutover.

### FR-4 One-slot rule (007)

- Do not load ds4 Flash and a full local Nemotron (or any second serious
  generative LLM) at the same time on the Spark.
- Sequential use: quiesce the occupied slot, run the spike, teardown, restore.
- No 120B+ loops.

### FR-5 Loopback bind

- `ds4-server` **MUST** bind `127.0.0.1` unless a later spec explicitly opens
  a firewalled bind (still not a public bind by default).
- Proposed research port if executed: `8090` on loopback. Not baked into this
  package.

### FR-6 Identity before speed

- Phase B **MUST NOT** publish speed comparisons until ≥99% greedy token
  identity vs the Mac-local prefill baseline.
- Tweet / README prefill and decode rates are citations, not results.

### FR-7 Voice TTFA (008)

- Live spoken path stays 008 until a later spec says otherwise.
- If hybrid decode is ever used on that path, `tts_ttfa_ms` / time-to-first-audio
  **MUST NOT** regress vs the then-current all-on-Spark (or hosted) loop.
- Fail the hybrid voice idea rather than ship a slower first chunk.

### FR-8 Execution is out of tree

- Clone and build `ds4` outside this repo. Do not submodule it here.
- Spike notes (commit, quant, pass/fail, identity %) stay out of git if they
  include prompts, transcripts, host identifiers, or hardware serials.
- This folder remains the SDD; it is not the run log.

### FR-9 Second plane

- Agent RPC stays on the existing Ethernet / Tailscale path.
- KV / tensor research, if green, is a second plane. Do not collapse the two.

## Non-functional requirements

- No secrets, serials, household identifiers, chat-product routing, lab IPs
  (including RFC1918), or required hostnames in this spec, plan, or tasks.
- Hardware in prose: “DGX Spark” and “Apple Silicon Mac in the lab.” Do not
  inventory a named personal Mac generation or a return date.
- Disk KV lives in a **dedicated on-host directory with a size cap**, not a
  path committed here.
- Beta engine: pin a commit after a green smoke; do not chase `main` mid-spike.
- Weights: only `download_model.sh` targets. First spike = Flash q2.
- Privacy: prompts used for identity tests stay on-host; do not commit them.

## Acceptance criteria

- [x] Spec states north star, two tracks, and honest “not executed” status.
- [x] MCDMA is watch-only; author-reported numbers labeled; no implementation
      repo until source + license.
- [x] ds4 Phase A (Spark-only) and Phase B (optional file KV) are specified
      with the ≥99% identity gate.
- [x] `ds4-server` loopback bind and 007 one-slot rule are written down.
- [x] ds4 does not replace Hermes / thelab (Nemotron ~30B / Grok).
- [x] 008 TTFA non-regression is named if hybrid decode is ever used.
- [x] Non-goals include 120B+, multi-tenant, implementing RDMA, two-Spark
      CX7, and Hermes default changes.
- [ ] Phase A executed — **not done** (human go required).
- [ ] Phase B executed — **not done**.
- [ ] MCDMA OSS evaluation — **not done** (blocked on public source + license).

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Unchanged. No ds4 or MCDMA side-effect. |
| Spec 007 slot | One local generative LLM; ds4 occupies it if loaded. |
| Spec 008 I/O | Still the spoken path; TTFA protected. |
| Agent network | Existing Ethernet / Tailscale. |
| `ds4-server` | Loopback only if/when executed; not this package. |

## Relationship to other specs

- **007** — one-slot policy. This spike **is** occupying the slot while Flash
  is loaded. Stacking with Nemotron is a 007 violation. 120B+ remains
  forbidden as a daily loop.
- **008** — live voice. Hybrid decode is not the desk loop. If it ever is,
  first-audio latency is a hard gate.
- **001** — long-term desktop voice. This research does not revive Riva/NIM
  compose as production.
- **012 / 009** — fleet roles and architect/coder handoff stay on Grok /
  existing local workers. Do not retarget profiles at ds4 in the spike.
- **015** — if any hybrid timings are exported later, they are content-free
  durations only. This spec does not add OTEL.

## Open questions (do not block specifying; do block speed claims)

- Exact `ds4` flags to **export** a KV file another backend will accept
  (confirm in `--help` / source during Phase A).
- Whether CLI session KV and server KV files are the same format for handoff.
- Whether CUDA-written KV is portable to Metal at all (that **is** Phase B).
- Standing localhost server after a green Phase A: optional, still not Hermes
  default, still loopback, still sequential with the 007 slot.
- MCDMA OSS date and license: unknown. Watch; do not schedule implementation.

## Citations

Use as **sources**. Do not claim this lab reproduced them.

- Engine: https://github.com/antirez/ds4
- Heterogeneous file-KV experiment (author-reported):
  https://x.com/danpacary/status/2086851964261003615
- MCDMA (author-reported):
  https://x.com/ashxhart/status/2089749434087227672
