# Feature Spec: Content-free / privacy-tiered telemetry

**Feature ID**: 015-content-free-telemetry
**Status**: Specified. Turn telemetry is implemented in the voice sibling;
not implemented in this package’s graph.
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [008-local-tts-lenovo-go-spike](../008-local-tts-lenovo-go-spike/spec.md),
[011-voice-reply-contract](../011-voice-reply-contract/spec.md),
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent),
[`lan-agent-otel`](https://github.com/derekclair/lan-agent-otel)

## Honest current state

This is a **contract**, not a new exporter in `thelab_langchain`.

| Surface | Today |
|---------|--------|
| Voice I/O sibling | Emits per-turn durations locally as JSONL. Opt-in OTLP ships **durations and counts only**. Transcripts must not go on that wire. |
| `thelab_langchain` graph | **Does not** export OpenTelemetry. No meter, no tracer, no OTLP bootstrap in this package. |
| LAN hub | Lives in [`derekclair/lan-agent-otel`](https://github.com/derekclair/lan-agent-otel) (collector → Prometheus / Loki / Tempo / Grafana). This repo **points at** that hub. It does **not** vendor the compose stack, lab IPs, or hostnames. |

008 already named content-free opt-in OTEL as an I/O-repo concern. 011 forbids unspeakable reply dumps through Piper. This spec is the **workstation telemetry policy** those two sit under: same content must not leave the host as “observability.”

Do not read this folder as “the LangGraph brain now reports to Grafana.” It does not.

## Overview

The desk has two telemetry planes:

1. **On-host** — structured JSONL (and session transcripts, if kept). Operator debugging. Gitignored. May contain speech and replies because it never leaves the machine.
2. **Off-host / LAN hub** — opt-in OTLP to the collector in `lan-agent-otel`. **Content-free by construction**: durations, counts, and low-cardinality labels only.

Privacy is **tiered**. The default for this workstation’s voice path and for any future graph metrics is **tier A** (ops, no user content). Higher tiers exist so a future operator can name them; they are not the default and they are not implemented here.

The hub is a **push sink**. Agents fail open if the collector is down. This package does not run the hub.

## Goals

- State what may leave the host, and what must not, in one place.
- Record that voice-turn latency export is real in the sibling, and that this package’s graph has **no** OTEL today.
- Point at `lan-agent-otel` as the LAN hub without copying its compose, addressing, or inventory.
- Align with 008 (I/O owns ears/mouth/hands/telemetry) and 011 (do not dump unspeakable content — including into logs and OTLP).
- Restate git policy: no transcripts, prompts, tool bodies, keys, lab IPs, or hardware serials in this tree.

## Non-goals

- Implementing OTEL inside `thelab_langchain` in this spec’s delivery. Future graph metrics are **specified as a contract**, not shipped.
- Copying `lan-agent-otel` compose, collector YAML, Grafana dashboards, or scrape targets into this repo.
- Publishing lab IPs, RFC1918, Tailscale names, or hub hostnames. Example endpoints in this folder are loopback or a placeholder only.
- A SaaS default (LangSmith, cloud APM) that ships prompts off-LAN.
- Using telemetry as a transcript archive, a speakability dump (011), or a secrets store.
- Alert routing, Slack, PagerDuty, or household identifiers in this spec.
- Changing 008’s hardware loop or 011’s reply-shape rules except to bind them to this privacy policy.

## User stories

1. As the person at the desk, I can look at per-turn latency without anyone else seeing what I said.
2. As an operator, I point opt-in OTLP at the LAN collector and get durations/counts, never transcripts.
3. As a developer of this package, I know `get_agent()` does not emit OTEL today and must not grow content-bearing spans later without a spec change.
4. As a developer of the I/O sibling, I keep JSONL local and treat OTLP as a numeric allow-list.
5. As a reviewer of git, I reject commits that contain transcripts, prompts, tool args/results with user content, API keys, lab IPs, or hardware serials.

## Privacy tiers

Names match the hub’s baseline. This package’s **required default** is tier A.

| Tier | What | Default for voice + this graph | May leave the host? |
|------|------|--------------------------------|---------------------|
| **A — content-free ops** | Durations, counts, error/cancel counters, `service.name`, generic `host.id` | **Yes (only this)** | Yes, via opt-in OTLP |
| **B — usage** | Token counts, model ids, tool *names* (not args), cost counters | Not implemented here | Hub-only, explicit review, still no bodies |
| **C — content** | Transcripts, prompts, completions, tool args/results, raw API JSON | **Forbidden as default** | **No.** On-host JSONL/transcript files only, gitignored |

Tier C is not “OTLP with a flag.” If content is retained at all, it stays on the host. Shipping it to the collector is a policy violation unless a later spec explicitly opens a lab-only, default-off path — and even then it must not land in git or in a public dashboard.

## Functional requirements

### FR-1 Allowed off-host fields (tier A)

OTLP and any other remote export **MAY** include:

- Numeric durations (milliseconds).
- Counts (turns, errors, cancellations).
- Low-cardinality resource/labels: `service.name`, a **generic** host id (not a serial, not an IP).

Voice-turn duration keys already used by the sibling (the contract for turns):

`asr_ms`, `agent_ms`, `tts_ms`, `total_ms`, `eou_ms`, `tts_ttfa_ms`

Future graph metrics, **if** this package ever exports, are the same shape: stage durations (for example memory-injection / LLM / tools), turn counts, error counts. Not message text.

### FR-2 Forbidden off-host fields

Remote export **MUST NOT** include:

- Transcripts (user speech, STT text)
- Prompts, system messages, memory-injection text
- Completions / `AIMessage.content`
- Tool arguments or tool results that contain user content (including 011 unspeakable dumps: tables, fenced code, diffs, JSON/YAML, path/URL soup)
- API keys, tokens, `.env` values, OTLP bearer material
- Lab IPs (including RFC1918), Tailscale/CGNAT addresses, hub hostnames that identify the site
- Hardware serials, MAC addresses, GPU/CPU/disk identifiers

A content-free exporter is an **allow-list of numeric keys**, not a redaction regex. Unknown payload keys are ignored.

### FR-3 On-host JSONL and transcripts

- Local JSONL **MAY** hold richer events for debugging, including text.
- Session transcripts, if kept, stay on the host and are **gitignored** (008).
- On-host files are not a license to POST the same payload to a collector, custom ingest URL, or SaaS.
- Do not commit JSONL, transcript dumps, or Grafana screenshots that contain speech.

### FR-4 Opt-in and fail-open

- OTLP is **opt-in**. No collector endpoint in env → no export (no-op).
- Missing SDK or unreachable collector **MUST NOT** break the voice loop or `get_agent()`.
- Do not bake a hub URL into this package’s code or SDD. Documented examples:

  - `http://127.0.0.1:4318`
  - `http://collector-host:4318`

  Prefer OTLP/HTTP. `/v1/metrics` (and traces/logs if a future exporter adds them) are appended by the client; SDD shows the **base** URL only.

### FR-5 Hub ownership

- The LAN hub is [`derekclair/lan-agent-otel`](https://github.com/derekclair/lan-agent-otel).
- This repo **does not** copy that compose file, collector config, IPs, or hostnames.
- Operators configure the sibling (and any future graph exporter) with a local env var. They do not learn the hub topology from `thelab` git.

### FR-6 Honesty in this package

- Until a meter/tracer exists under `thelab_langchain`, docs **MUST NOT** claim graph OTEL.
- Do not add OpenInference / LangSmith / “capture prompts” flags as a default.
- `src/thelab_langchain/voice/` (Riva helpers) is not the live path (008) and is not an observability implementation.

### FR-7 Relation to 011 (unspeakable dumps)

011 says the spoken reply must not dump tables, fences, or runbooks unless the user asked. Telemetry is not a second mouth:

- Do not log those dumps to OTLP “for debugging.”
- Do not attach `AIMessage.content` to spans so Grafana can “show the turn.”
- On-host JSONL may retain the string; the wire must not.

## Non-functional requirements

- No secrets, serials, household identifiers, Slack, or real IPs in this spec, plan, or tasks.
- Example OTLP bases only: `http://127.0.0.1:4318` or `http://collector-host:4318`.
- Low cardinality: do not use user id, session id, or free-text as a metric label on the wire.
- Fail-open, non-blocking export (background; never stall STT/TTS or the graph).
- Same `get_agent(user_id)` seam as 008. Telemetry must not require a forked graph.

## Acceptance criteria

- [x] Spec states allowed vs forbidden fields and privacy tiers, with tier A as default.
- [x] Voice-turn duration keys are named; OTLP is opt-in and content-free.
- [x] Honest status: sibling implements turns; `thelab_langchain` does not export OTEL.
- [x] Hub is referenced as `lan-agent-otel` without copying compose, IPs, or hostnames.
- [x] Git policy restated (transcripts, prompts, tool content, keys, lab IPs, serials).
- [x] 011 dumps are explicitly out of remote logs.
- [ ] Graph-side metrics in this package — **not done** (see [tasks.md](./tasks.md)).

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Unchanged. No telemetry side-effect required for 008. |
| Voice sibling JSONL | Local `turn_complete` (and related) events; gitignored; may include text on host. |
| Voice sibling OTLP | Opt-in; allow-list of `*_ms` + counters; no transcripts. |
| Hub OTLP HTTP | Base `http://127.0.0.1:4318` or `http://collector-host:4318` (operator env). |
| Future graph exporter | If added: same FR-1/FR-2 allow-list. Not present today. |

## Relationship to other specs

- **008** — I/O spike owns telemetry emission for the desk loop. FR-6 there is the ancestor of this contract. 008’s open question (“LAN hub vs JSONL-only”) is answered here: JSONL always on-host; OTLP opt-in to `lan-agent-otel`.
- **011** — reply content contract. Unspeakable formatting is also unspeakable as a log line on the collector.
- **007** — Spark budget. Any future graph exporter stays fail-open and must not add an extra LLM call (same rule as memory injection).
- **004** — checkpointers. Session memory is not a telemetry sink.
- **010** — keep secrets off the board; same classes stay out of git and OTLP.

## Open questions

- If graph metrics are built later: wrap `get_agent()` internally, or let the I/O process time `invoke` only (sibling already has `agent_ms`)? Default bias: do not duplicate `agent_ms`; only add stages the I/O process cannot see (memory injection, tool node).
- Tier B token/model counts for this package: useful, still content-free, but **not** required to call this spec done.
- Custom HTTP ingest besides OTLP: bound by FR-2. Prefer the hub’s OTLP path; do not grow a second content-bearing shipper.
