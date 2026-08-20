# Plan: Content-free / privacy-tiered telemetry (015)

**Feature**: 015-content-free-telemetry
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20
**Status**: Specified. Turns implemented in the voice sibling; graph OTEL not
in this package.

## 1. Two planes (do not mix them)

```
desk loop (008)
  utterance → STT → get_agent() → TTS
                 │
                 ├─ on-host JSONL / transcripts   (gitignored; may contain text)
                 │
                 └─ opt-in OTLP metrics ──► lan-agent-otel
                      allow-list: asr/agent/tts/total/eou/ttfa ms
                                  + turn/error/cancel counts
                                  + service.name, generic host id
                      never: transcripts, prompts, tool bodies
```

`thelab_langchain` today sits only on the `get_agent()` box. It does not sit
on either telemetry arrow.

The LAN hub (`collector → Prometheus / Loki / Tempo / Grafana`) is a **different
git repo**. Point at [`derekclair/lan-agent-otel`](https://github.com/derekclair/lan-agent-otel).
Do not copy compose, collector YAML, IPs, or hostnames into this tree.

Example bases an operator may set in **local env** (not in git):

- `http://127.0.0.1:4318`
- `http://collector-host:4318`

## 2. What already exists (voice sibling)

Executed in [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent),
not here.

| Piece | Behavior |
|-------|----------|
| Local JSONL | Structured events, including `turn_complete` with stage durations |
| Duration keys | `asr_ms`, `agent_ms`, `tts_ms`, `total_ms`, `eou_ms`, `tts_ttfa_ms` |
| Opt-in OTLP | No-op unless an endpoint env is set; histograms of those keys + counters |
| Content rule | OTLP module reads **numeric keys only**; text keys are ignored |
| Fail-open | Missing SDK / down collector does not stop the loop |

008’s tasks already mark “content-free opt-in OTEL” done **in that repo**.
This plan does not re-implement it in `thelab`.

On-host JSONL may still hold speech for the operator. That is the on-host
plane. Remote export of that same payload is out of policy (spec FR-2 / FR-3).

## 3. What does not exist (this package)

No OpenTelemetry dependency, bootstrap, or span around the LangGraph graph.
`graph.py` injects memory and calls the LLM. It does not record histograms.

Honest consequence: Grafana cannot show “thelab graph stages” until someone
implements a later phase. Voice-turn `agent_ms` is wall time around `invoke`
in the I/O process. That is enough for 008 latency tables. It is not a graph
trace.

## 4. Privacy policy (restate; enforce in review)

**Forbidden in git** (tracked files, commit messages, PR bodies, CI logs,
example JSONL, screenshots):

- Transcripts and session dumps
- Prompts, system / memory-injection text, completions
- Tool args/results that carry user content (including 011 unspeakable dumps)
- API keys, tokens, `.env` contents, bearer headers
- Lab IPs (RFC1918 and any site-identifying address)
- Hardware serials, MACs, GPU/CPU/disk identifiers

**Allowed in git and on the wire (tier A):**

- Durations
- Counts
- Low-cardinality labels: `service.name`, generic host id

Do not use user id, session id, or free-text as an OTLP label.

## 5. Suggested sequence (if we implement graph metrics later)

Not a commitment. Default order if someone picks this up:

1. **Keep the sibling path as the live turn exporter.** Do not duplicate
   `agent_ms` inside `get_agent()` just to look busy.
2. **If graph-internal stages are needed**, add a tiny, fail-open recorder in
   *this* package that emits only numeric stage times (memory injection, LLM,
   tools). Same allow-list as FR-1. Opt-in via `OTEL_EXPORTER_OTLP_ENDPOINT`
   (or a package-specific alias). Example base still `http://127.0.0.1:4318`
   or `http://collector-host:4318`.
3. **Allow-list in code**, not redaction. Tests: a payload that includes
   `user_text` / `prompt` / tool args must not appear in the exported metric
   attributes.
4. **Do not** enable OpenInference prompt capture, LangSmith SaaS dual-export,
   or OTEL log-user-prompt flags.
5. **Do not** vendor the hub stack. Operators already have `lan-agent-otel`.

Tier B (token counts, model id, tool *names*) is optional later and still
must not include bodies. Tier C stays off.

## 6. 011 and logs

A markdown table or fenced dump that slips through Piper is already a 011
failure. Shipping that string to Loki “so we can see what Piper said” is a
015 failure on top. Debug on-host JSONL if needed; do not open a content
back-channel.

## 7. What we will not do in this plan

- Copy `lan-agent-otel` compose, IPs, or hostnames.
- Claim `thelab_langchain` exports OTEL.
- Put measured TTS timings in this tree (008 / sibling README).
- Add an extra LLM call to “summarize the turn for metrics.”
- Route alerts to Slack or any chat product from this spec.
- Check off graph implementation because the sibling already times `invoke`.

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Docs imply the brain already has Grafana series | Status line on every file in this folder |
| Hub compose copied “for convenience” | Point at the repo; no YAML here |
| JSONL text POSTed to a custom ingest | FR-2 applies to every remote path, not only OTLP |
| High-cardinality labels (`user_id`, session) | Forbidden on the wire |
| Prompt-capture instrumentation added with a tutorial | Explicit non-goal; default flags off |
| 011 dumps in Loki | Same allow-list; no message bodies on spans/logs |

## 9. Success

- A developer reading this folder can say: sibling does turns; this package
  does not; hub is the other repo; content never goes on the wire.
- Git history of `thelab` still has no transcripts, keys, lab IPs, or serials
  introduced by this work.
- If graph export ships later: unit tests prove text keys are dropped, no
  hardware and no live collector required.
