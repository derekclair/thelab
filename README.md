# thelab

A small, memory-aware **LangGraph agent brain** for a personal NVIDIA DGX Spark
workstation. Package name on PyPI-style imports is `thelab-langchain`.

This is a learning project, not a production framework. It pairs a LangGraph
reasoning graph with [Supermemory](https://supermemory.ai) for long-term recall,
and talks to **Grok (xAI)**, **Claude (Anthropic)**, or any OpenAI-compatible
local model (Ollama / a Nemotron NIM).

What is actually in the tree:

- A LangGraph graph that **injects long-term memory as a graph node** before the
  LLM turn (no extra summarization round-trip), then still lets the model call
  memory tools when it wants them (`src/thelab_langchain/agent/graph.py`)
- A single provider factory for Grok / Anthropic / OpenAI-compatible endpoints
- A CLI for text chat (`thelab-chat`)
- Specs for the voice/desktop goal, Spark memory budget, and follow-on work
  (`specs/`)

> **Used by:** [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
> executes [spec 008](specs/008-local-tts-lenovo-go-spike/spec.md) (the Lenovo Go
> local-tts spike). This package is `get_agent()` only.
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
   thelab-chat chat --user alice
   ```

**Important**: `.env` is gitignored and should **never** be committed.

### Special Commands (inside the chat)

| Command       | Effect |
|---------------|--------|
| `/profile`    | Show current Supermemory profile + facts |
| `/clear`      | Reset local conversation buffer (long-term memory stays) |
| `/user <id>`  | Switch to a different user/container |
| `/quit`       | Exit |
| `/help`       | List commands |

Everything else is sent to the LLM together with rich memory context pulled from Supermemory.

## How the graph works

On each agent turn (`get_agent()` in `agent/graph.py`):

1. **`memory_injection` node** — pulls profile + a few recalled memories from
   Supermemory using the last user utterance, and prepends them as a
   `SystemMessage`. Raw context, not an LLM summary, so a voice turn does not
   pay for an extra round-trip.
2. **`call_llm`** — the chosen provider runs with memory tools bound.
3. **Tools (optional)** — if the model calls `store_memory` / `recall_memories`
   / `get_user_profile`, `ToolNode` runs and the graph loops; otherwise it ends.

Text chat (`MemoryChat` in `chat.py`) is a simpler profile → LLM → store loop
without the graph. The voice sibling uses `get_agent()`.

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

## Project layout

```
src/thelab_langchain/agent/graph.py   LangGraph brain (memory injection + tools)
src/thelab_langchain/llm.py           Provider factory
src/thelab_langchain/chat.py          Simpler text MemoryChat loop
src/thelab_langchain/voice/           Riva-oriented spike (streaming is Phase 2)
tests/                                CPU-only unit tests (CI)
specs/                                Design specs — see specs/README.md
docs/                                 Architecture + development notes
examples/                             Non-interactive snippets
```

## Documentation

- **[Architecture](docs/architecture.md)** — layering of this package
- **[Development](docs/development.md)** — venv, chat, common commands
- **[Specs index](specs/README.md)** — design and planning already in this repo
- **[Spec 008](specs/008-local-tts-lenovo-go-spike/spec.md)** — local-tts spike; implemented in [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
- **[Spec 014](specs/014-memory-injection-graph/spec.md)** — the shipped LangGraph (`get_agent()`)
- Workstation fleet operating manual (Hermes, not vendored):
  `~/.hermes/docs/agentic-workflow.md`

## Development

### Local development

All commands go through the local venv via Make:

```bash
make install          # first time / after clean
make lint             # ruff + mypy
make chat             # text chat demo
make run              # same as chat
```

### Voice on the DGX Spark

The **live** spoken path is the sibling
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
repo (Parakeet STT + Piper TTS + this package as `get_agent()`). Clone it next
to this repo as `../conversational-voice-agent`, then `make` here and `make`
there.

`docker-compose.yml` in *this* repo is a NIM + Riva experiment. Streaming ASR
in `src/thelab_langchain/voice/` is still `NotImplementedError` (Phase 2).
Do not treat that compose file as the production voice stack.

## Honest gaps

- Conversation checkpointers are specified (`specs/004`) but not wired; graph
  state is in-memory for a process lifetime.
- `specs/002` multi-user is a design, not a shipped tenant model.
- No eval harness / MemoryBench numbers in this tree.

## References

- Supermemory LangChain guide: https://supermemory.ai/docs/integrations/langchain
- langchain-xai docs: https://python.langchain.com/docs/integrations/chat/xai
- xAI API: https://docs.x.ai/
