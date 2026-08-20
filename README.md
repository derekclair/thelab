# thelab-langchain

A small, memory-aware **LangGraph agent brain**. This is a personal learning project that pairs a LangGraph reasoning graph with [Supermemory](https://supermemory.ai) for long-term recall, and can talk to **Grok (xAI)**, **Claude (Anthropic)**, or any OpenAI-compatible local model (e.g. a Nemotron NIM on a DGX Spark). It is meant to be a clean, readable reference for wiring memory into an agent — not a production framework, so expect rough edges.

What it demonstrates:

- Long-term user memory and automatic profiling via [Supermemory](https://supermemory.ai)
- A LangGraph graph that proactively injects relevant memory, then lets the model call memory tools when it wants them
- Pluggable LLM providers behind a single factory (Grok by default — no OpenAI dependency required)
- A simple interactive CLI

> **Used by:** the companion [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) repo — a local voice front-end (STT/TTS on a DGX Spark) that uses this package as its agent brain.
>
> **Fleet ops:** the workstation's multi-profile fleet (orchestrator, architect,
> researcher, coder, reviewer) is documented in local Hermes docs at
> `~/.hermes/docs/agentic-workflow.md`. That file stays there — Hermes expects
> it in place — and is not vendored into this repo.

## Prerequisites

- Python ≥ 3.11
- API keys for:
  - **Supermemory**: https://console.supermemory.ai
  - **Grok (xAI)**: https://console.x.ai/   (recommended)
  - or **Anthropic**: https://console.anthropic.com

## Quick Start (venv enforced)

**We use a project-local `.venv` only.** This prevents dependency collisions with anything else on your machine (especially important with Homebrew Python, other projects, etc.).

1. (Optional but recommended) Copy the example env and fill your keys:

   ```bash
   cp .env.example .env
   # Then edit .env with your SUPERMEMORY_API_KEY and XAI_API_KEY (or ANTHROPIC)
   ```

2. One command to rule them all:

   ```bash
   make install
   ```

   This will:
   - Create a fresh `.venv/` in the project root
   - Install the package + dev tools in complete isolation
   - Never touch your global Python environment

3. Run the chat (still using the venv automatically):

   ```bash
   make chat
   # or
   make run
   ```

   Or with a named user/container (Supermemory isolates by `container_tag`):

   ```bash
   make run   # then inside the chat:  /user alice
   ```

   You can also activate the venv the normal way if you prefer:

   ```bash
   source .venv/bin/activate
   thelab-chat chat --user derek
   ```

**Important**: `.env` is gitignored and should **never** be committed. Your new dedicated Supermemory key will stay local.

   ```bash
   thelab-chat chat --user alice
   ```

### Special Commands (inside the chat)

| Command       | Effect |
|---------------|--------|
| `/profile`    | Show current Supermemory profile + facts |
| `/clear`      | Reset local conversation buffer (long-term memory stays) |
| `/user <id>`  | Switch to a different user/container |
| `/quit`       | Exit |
| `/help`       | List commands |

Everything else is sent to the LLM together with rich memory context pulled from Supermemory.

## How It Works

On every turn the agent:

1. Calls `memory.profile(container_tag=user_id, q=message)` — Supermemory returns:
   - `static` facts (long-term profile)
   - `dynamic` context (recent activity)
   - Semantically relevant past memories

2. Injects a nicely formatted context block into the system prompt.

3. Calls the chosen LLM (`ChatXAI` or `ChatAnthropic`).

4. Stores the turn via `memory.add(...)` so future conversations remember it.

This pattern gives you excellent personalization and continuity without managing your own vector store or prompt engineering for memory.

## About the Official Supermemory + LangChain Guide

The official docs at https://supermemory.ai/docs/integrations/langchain currently show this as the "next step":

```python
from langchain_openai import ChatOpenAI
from supermemory import Supermemory

memory = Supermemory()
llm = ChatOpenAI(model="gpt-4o")
...
```

**This is just an example**, not a requirement.

Supermemory is a standalone memory service. The `Supermemory()` client is completely decoupled from which LLM provider you use. You can (and we do) pair it with `ChatXAI`, `ChatAnthropic`, or any other LangChain chat model.

See [examples/official_guide_style.py](examples/official_guide_style.py) for a drop-in version of the exact snippet from the guide, but using Grok instead of OpenAI.

## Switching to Anthropic / Claude

In `.env`:

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-7-sonnet-20250219
ANTHROPIC_API_KEY=sk-ant-...
```

Then install the optional extra (the import is lazy) — best done via the venv:

```bash
make install   # already includes dev tools
# or after venv exists:
.venv/bin/pip install -e ".[anthropic]"
```

## Project Layout

```
.
├── src/thelab_langchain/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings + validation
│   ├── llm.py              # LLM provider factory (Grok / Anthropic / OpenAI-compatible)
│   ├── chat.py             # MemoryChat core (profile → LLM → store)
│   ├── cli.py              # Typer + Rich interactive shell
│   ├── agent/              # LangGraph agent brain
│   │   ├── graph.py        # Reasoning graph (memory injection + tool calls)
│   │   ├── state.py        # Graph state definitions
│   │   └── tools/          # Agent tools (e.g. Supermemory memory tool)
│   └── voice/              # Optional voice front-end (STT/TTS orchestration)
│       ├── orchestrator.py
│       ├── audio.py
│       └── riva.py
├── examples/               # Runnable, non-interactive usage examples
├── .env.example
├── pyproject.toml
└── README.md
```

## Documentation & Getting Started

- **[Development Guide](docs/development.md)** — How to set up your environment, run text vs voice mode, and common commands.
- **[Architecture Overview](docs/architecture.md)** — Layering, key components, and how everything fits together.
- `specs/` — Feature specifications and design decisions (read these to understand *why* things are built the way they are).
- Workstation fleet operating manual: local `~/.hermes/docs/agentic-workflow.md` (not in this tree).

## Development

### Local (Mac) Development

All commands go through the local venv via Make:

```bash
make install          # first time / after clean
make lint             # ruff + mypy
make chat             # text chat demo
make run              # same as chat
```

### Docker + DGX Spark Deployment (Recommended for Voice)

The canonical way to run the full stack (agent + Riva + Nemotron) is via Docker Compose on the DGX Spark:

```bash
# 1. Develop on Mac
# 2. Build the agent image
docker compose build

# 3. On the DGX (ssh dgx)
docker compose pull          # or build
docker compose up -d
```

See `docker-compose.yml` for the current services (`agent`, `riva`, `nemotron`).

The agent can be pointed at either Grok or the local Nemotron NIM at runtime via environment variables.

(Full observability is deferred for now.)

## Next Steps / Ideas

- Add proper LangGraph agent with tools + Supermemory as a tool
- Persistent local conversation history + summarization
- Metadata filtering examples (`memory.search.memories(filters=...)`)
- Evaluation harness against MemoryBench
- Expose as a FastAPI service or Discord/Slack bot
- Store documents (not just chat turns) via `memory.add(url=...)` or raw content

## References

- Supermemory LangChain guide: https://supermemory.ai/docs/integrations/langchain
- langchain-xai docs: https://python.langchain.com/docs/integrations/chat/xai
- xAI API: https://docs.x.ai/
