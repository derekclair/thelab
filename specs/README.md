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

Hermes **operating manual** (CLI, gateway, profile files) stays at
`~/.hermes/docs/agentic-workflow.md`. Specs 009–010 record the *protocol*,
not that file.
