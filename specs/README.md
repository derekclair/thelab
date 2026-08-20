# Specs

Design and planning for this package. Status in each file is honest: several
are drafts or future work, not a claim that every spec is implemented.

| ID | Title | What it is |
|----|-------|------------|
| [001](001-voice-dgx-spark-agent/spec.md) | Voice-enabled agent on DGX Spark | Original desktop-voice goal; live I/O now lives in [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) |
| [002](002-multi-user-support/spec.md) | Multi-user support | Per-user `container_tag` / `thread_id` — designed, not a product multi-tenant system |
| [003](003-deployment-infrastructure/spec.md) | Deployment / Docker | Compose + NIM path; gaps called out in the spec |
| [004](004-persistence-checkpointers/spec.md) | Persistence & checkpointers | Planned LangGraph checkpointer; conversation state is still in-memory |
| [005](005-testing-and-cicd/spec.md) | Testing & CI | Direction; a CPU-only pytest + ruff workflow is in `.github/workflows/ci.yml` |
| [006](006-alternative-memory-systems/spec.md) | Alternative memory backends | Future consideration; Supermemory is the current store |
| [007](007-dgx-hardware-optimization/spec.md) | DGX Spark hardware budget | ~30B-class local models; no 120B+ agent loops on one Spark |

Workstation **fleet operations** (orchestrator / architect / researcher /
coder / reviewer, Kanban vs chat) are not specified here. That operating
manual stays in Hermes at `~/.hermes/docs/agentic-workflow.md`.
