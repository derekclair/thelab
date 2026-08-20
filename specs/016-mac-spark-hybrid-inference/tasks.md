# Tasks: Hybrid Apple Silicon + DGX Spark inference research (016)

**Feature**: 016-mac-spark-hybrid-inference
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)
**Status**: Specified / not executed. Human go required before Phase A.

Checkboxes are honest. Spec-only work can be marked done. Do **not** mark
Phase A, Phase B, or MCDMA evaluation done because public posts or the ds4
README exist. Do not clone, build, or serve from this list without a human go.

## Phase 0 — Specify the contract (this folder)

- [x] Write `spec.md` (north star, two tracks, non-goals, 007/008 binds)
- [x] Write `plan.md` (watch vs spike, planes, decision tree, no execute)
- [x] Write `tasks.md` (this file)
- [x] Label MCDMA BW/RTT as author-reported; cite public posts without
      claiming we ran them
- [x] Cite [antirez/ds4](https://github.com/antirez/ds4) as the engine;
      Pacary post as the file-KV experiment shape
- [x] Bind `ds4-server` to `127.0.0.1`; 007 one-slot; no Hermes default change
- [x] Privacy: no lab IPs, RFC1918, serials, required hostnames, or cache
      paths in this folder

## Phase 1 — MCDMA watch (not an implementation)

Policy (specified):

- [x] Track is **watch only** until source **and** license are public
- [x] Do **not** start an implementation repo while closed
- [x] Do **not** implement RDMA ourselves
- [x] Two-Spark CX7 fabric is out of scope
- [x] Author-reported figures stay labeled; not our benches

Blocked on OSS (leave unchecked):

- [ ] Public source + license reviewed
- [ ] Human go to run **upstream** tests on one Spark + Apple Silicon Mac
      in the lab (USB-C)
- [ ] Independent single-link BW / RTT capture, labeled as *our* run
- [ ] Decision memo: keep watching vs toy tensor/KV shuttle vs drop
- [ ] Any Hermes or 008 wiring — **forbidden until** a later spec

Do not treat an OSS rumor as a checkbox.

## Phase 2 — ds4 Phase A (Spark-only; not started)

**Human go required.** Out of tree. Do not vendor into `thelab`.

- [ ] Explicit human go for Phase A
- [ ] Quiesce the 007 slot (no ds4 + full local Nemotron)
- [ ] Clone [antirez/ds4](https://github.com/antirez/ds4) outside this repo;
      record commit SHA
- [ ] `make cuda-spark` succeeds (Spark is single-GPU; no CUDA TP flags)
- [ ] `ds4f-q2` only (skip PRO / MXFP4 / DSpark on the first spike)
- [ ] CLI greedy short prompt OK (modest context first)
- [ ] Disk KV: cold prefill → restart → warm prefix hit, in a dedicated
      size-capped on-host directory (path not committed here)
- [ ] `ds4-server` chat completion on `127.0.0.1` (proposed port 8090)
- [ ] Notes: commit, quant, pass/fail, blockers (no secrets, no serials,
      no prompts in this git tree)
- [ ] Teardown: stop server; restore 007 agent path
- [ ] Decision: stop | optional loopback-only standing server (still not
      Hermes default) | ask for Phase B go

Phase A fail → do not start Phase B.

## Phase 3 — ds4 Phase B (optional file KV; gated)

**Separate human go** after Phase A green.

- [ ] Explicit human go for Phase B
- [ ] Same commit + byte-identical GGUF on Mac and Spark (checksum)
- [ ] Mac Metal build OK
- [ ] Same-machine greedy baselines recorded (Mac-only vs Spark-only)
- [ ] Spark writes KV; file copied over existing network (Wi-Fi first);
      Mac decodes without local prefill of that prefix
- [ ] Identity gate: ≥99% greedy token match vs Mac-local prefill
      (temp 0; continuation length N in notes)
- [ ] If gate fails: stop speed work; keep Spark-only; record negative result
- [ ] If gate passes: time Spark prefill + ship + Mac load vs Mac-local
      prefill (8k / 32k first). 10GbE only if identity holds and ship dominates
- [ ] No “faster E2E” claim until identity **and** that comparison exist
- [ ] Identity notes stay out of this git tree if they include prompts

Phase B is **file copy**. It is not MCDMA.

## Out of scope (stay unchecked here)

- [ ] Implementing MCDMA / RDMA / USB-C verbs
- [ ] Two-Spark ConnectX-7 fabric
- [ ] 120B+ agents
- [ ] Multi-tenant ds4 serve
- [ ] Hermes profile default cutover to ds4
- [ ] Stacking ds4 with a full local Nemotron
- [ ] Binding `ds4-server` off loopback as part of the spike
- [ ] Vendoring `ds4` into this repo
- [ ] Hybrid decode on the 008 spoken path
- [ ] Claiming author or upstream benches as lab results
- [ ] Changing 007 slot policy or 008 TTFA contract except to obey them

## Traceability

| Want | Where it lives |
|------|----------------|
| North star (Metal/MLX + CUDA KV/tensor) | This folder |
| Agent plane Mac ↔ Spark | Existing Ethernet / Tailscale; unchanged |
| One local LLM | Spec 007 |
| Spoken loop + TTFA | Spec 008 sibling |
| ds4 engine | Public `antirez/ds4` (not executed here) |
| File-KV experiment shape | Pacary public post (author-reported) |
| MCDMA | ashxhart public post (watch; author-reported) |
| Hybrid running in this lab | **Does not** |

Live consume path for agents remains
`get_agent()` (this package) plus the 008 I/O sibling. ds4 and MCDMA are not
on that path.
