# Specs

Each numbered folder has **spec.md**, **plan.md**, and **tasks.md**. Status in
the spec is honest: living practice, executed out of tree, designed-not-built,
or partial.

| ID | Title | What it is |
|----|-------|------------|
| [001](001-voice-dgx-spark-agent/spec.md) | Voice-enabled agent on DGX Spark | Broader desktop-voice goal (Riva/NIM compose). Not the live path. |
| [002](002-multi-user-support/spec.md) | Multi-user support | Per-user `container_tag` / `thread_id`. Designed; not speaker ID. |
| [003](003-deployment-infrastructure/spec.md) | Deployment / Docker | Experimental compose; healthchecks and GPU limits still open. |
| [004](004-persistence-checkpointers/spec.md) | Persistence & checkpointers | Not wired. Caller (or in-memory process) holds turns. |
| [005](005-testing-and-cicd/spec.md) | Testing & CI | Unit tests + CPU GitHub Actions exist; no coverage gate or image CI. |
| [006](006-alternative-memory-systems/spec.md) | Alternative memory backends | Escape hatch. Supermemory stays default; do not build adapters yet. |
| [007](007-dgx-hardware-optimization/spec.md) | Spark hardware + inference slot | One local LLM; CPU STT/TTS; Grok for quality-critical roles. |
| [008](008-local-tts-lenovo-go-spike/spec.md) | Local-tts Lenovo Go spike | **Executed in** [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent). |
| [009](009-architect-coder-handoff/spec.md) | Architect ↔ coder handoff (STE) | Living practice. Not a library feature; not CI-enforced. |
| [010](010-worker-completion-protocol/spec.md) | Worker complete-or-block | Living practice. This package does not implement a board. |
| [011](011-voice-reply-contract/spec.md) | Voice-facing reply contract | Wanted speakability rules. No filter in code yet. |
| [012](012-fleet-dispatch-model/spec.md) | Fleet dispatch model | Conversation vs subagent vs durable board; closed roster. Not a dispatcher in this package. |
| [013](013-reviewer-quality-gate/spec.md) | Reviewer quality gate | Never implements; severity scale. No reviewer bot here. |
| [014](014-memory-injection-graph/spec.md) | Memory-injection graph | **Shipped** in `get_agent()`. Raw context; fail-open; no extra summarizer. |
| [015](015-content-free-telemetry/spec.md) | Content-free telemetry | Voice sibling implements turns; graph does not export OTEL. Hub is `lan-agent-otel`. |
| [016](016-mac-spark-hybrid-inference/spec.md) | Mac + Spark hybrid inference | Research contract. MCDMA watch-only; ds4 spike not executed. Not the agent path. |
| [017](017-mcp-runtime-trust-boundary/spec.md) | MCP runtime trust boundary | Tool processes are a host trust boundary. POC out of tree; not in `get_agent()`. |

Hermes **operating manual** (CLI, gateway, profile files) stays at
`~/.hermes/docs/agentic-workflow.md`. Specs 009–010 and 012–013 record
*protocol*, not that file.

### Research tracks not imported

Workspace research that is **not** SDD in this package (wrong product, client,
or a dump we will not vendor):

- Church captioning / ProPresenter pipelines
- Client marketing sites
- World-models / SITE-Bench eval clones (upstream academic bench)
- Skill-optimization bootstrap (no design locked)
- Multi-agent *literature* surveys (012 is our chosen dispatch model)
- CVE/KEV catalogs and cycle summaries (017 records the trust boundary only)
- Alternate observability compose experiments (015 points at `lan-agent-otel`)
