# Tasks: Content-free / privacy-tiered telemetry (015)

**Feature**: 015-content-free-telemetry
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)
**Status**: Specified. Turns implemented in the voice sibling; graph OTEL not
in this package.

Checkboxes are honest. Spec-only work can be marked done. Do not mark graph
export done because the I/O process already times `invoke`.

## Phase 0 — Specify the contract (this folder)

- [x] Write `spec.md` (tiers, allow-list, forbidden fields, hub pointer,
      honesty about this package)
- [x] Write `plan.md` (two planes, sibling vs graph, no compose copy)
- [x] Write `tasks.md` (this file)
- [x] Restate git policy: no transcripts, prompts, tool content, keys, lab
      IPs, hardware serials
- [x] Example OTLP bases only: `http://127.0.0.1:4318`,
      `http://collector-host:4318`
- [x] Bind 008 (I/O telemetry) and 011 (do not log unspeakable dumps)

## Phase 1 — Voice-turn export (sibling; already executed)

Out of tree. Listed so this package does not re-build it.

Implementation:
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)

- [x] Local JSONL `turn_complete` with `asr_ms`, `agent_ms`, `tts_ms`,
      `total_ms`, `eou_ms`, `tts_ttfa_ms`
- [x] Opt-in OTLP/HTTP metrics of those durations + turn/error/cancel counts
- [x] OTLP path ignores text keys (allow-list, not redaction)
- [x] Fail-open if SDK missing or collector down
- [x] On-host transcripts gitignored (008)

Do **not** copy that exporter into `thelab_langchain` as a “port.”

## Phase 2 — Graph metrics in this package (not built)

Not built. Leave unchecked until a fail-open, content-free exporter exists
**in this tree** and tests prove text cannot leak.

- [ ] Decide whether graph-internal stages are worth emitting (memory
      injection / LLM / tools) vs keeping I/O-timed `agent_ms` only
- [ ] Opt-in via env; no baked hub URL; examples remain
      `http://127.0.0.1:4318` or `http://collector-host:4318`
- [ ] Allow-list numeric fields + `service.name` + generic host id
- [ ] Unit tests: payload with transcript/prompt/tool args does not appear on
      exported attributes (no collector required)
- [ ] Fail-open: missing SDK / down collector does not break `get_agent()`
- [ ] No OpenInference / LangSmith prompt capture; no extra LLM round-trip
- [ ] Do not treat sibling `agent_ms` as this checkbox

## Phase 3 — Hub (other repo; do not vendor)

- [x] Point operators at [`derekclair/lan-agent-otel`](https://github.com/derekclair/lan-agent-otel)
      (collector → Prometheus / Loki / Tempo / Grafana)
- [ ] **Out of this repo forever:** copy compose, collector YAML, lab IPs,
      hostnames, scrape targets, Grafana JSON

## Out of scope (stay unchecked here)

- [ ] SaaS default that ships prompts off-LAN
- [ ] Tier C content on the collector
- [ ] Alert routing to Slack or any chat product
- [ ] Speakability filter (011) — different contract; this spec only forbids
      logging those dumps remotely
- [ ] Hardware latency tables copied from the sibling README

## Traceability

| Want | Where it lives today |
|------|----------------------|
| Turn durations JSONL | Voice sibling, on-host |
| Opt-in content-free OTLP for turns | Voice sibling |
| LAN hub stack | `lan-agent-otel` (do not copy) |
| Graph OTEL | **Not in `thelab_langchain`** |
| Transcripts | On-host, gitignored; never OTLP |
| Unspeakable reply dumps | 011 content rule; 015: not on the wire |

Live consume path for turns:
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
calls `thelab_langchain.agent.graph.get_agent` and times the turn itself.
