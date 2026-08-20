# Development Guide

## Environment Setup (Recommended)

We strongly prefer a project-local virtual environment to avoid dependency hell (especially on macOS with Homebrew Python).

```bash
# One-time setup
make install

# Activate (optional — most `make` targets work without it)
source .venv/bin/activate
```

After `make install` you should have a working `thelab-chat` command.

## Running the Text Agent

```bash
# Basic text chat (uses Grok by default via .env)
make chat

# Or directly
thelab-chat chat --user derek --thread morning-standup
```

## Running the Voice Agent (Local)

The voice path requires a running Riva server (and optionally a local Nemotron).

**Quick local test (mocked audio path coming soon):**

```bash
# Point at services running on your host (from inside Docker or natively)
HOST_IP=host.docker.internal thelab-chat voice --user derek
```

For full local voice development without Docker, you will need:
- A local Riva installation or the Riva Docker container
- A local LLM (Ollama, vLLM, or NVIDIA NIM) exposing an OpenAI-compatible endpoint

Set these environment variables:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:8000/v1
RIVA_URI=localhost:50051
```

## Environment Variables Reference

See `.env.example` for the current list. Key ones:

- `LLM_PROVIDER` — `xai` (Grok), `anthropic`, or `openai_compatible`
- `LLM_BASE_URL` — only needed for `openai_compatible` (e.g. your Nemotron NIM)
- `RIVA_URI` — address of the Riva gRPC server
- `SUPERMEMORY_API_KEY` — required
- `XAI_API_KEY` / `ANTHROPIC_API_KEY`

## Docker Development

See the root `docker-compose.yml` and the profiles it supports:

```bash
# Full stack (agent + Riva + Nemotron)
docker compose up

# Just the agent (talking to host services)
docker compose up agent
```

## Running on DGX Spark

See the deployment workflow in `specs/001-voice-dgx-spark-agent/plan.md` and `specs/003-deployment-infrastructure/spec.md`.

Typical flow:
1. Develop on Mac
2. `docker compose build`
3. Push image to your private registry
4. On the DGX: `docker compose pull && docker compose up`

## Adding New Tools or Memory Systems

1. Create the tool(s) in `src/thelab_langchain/agent/tools/`
2. Use the factory pattern (`create_xxx_tools(user_id)`) so they are user-scoped.
3. Wire them in `agent/graph.py` (either via proactive injection or by binding to the LLM).
4. Update the voice orchestrator if the new tools need special handling from the audio layer.

See the existing Supermemory tools as the reference implementation.

## Common Make Targets

- `make install` — create venv + install
- `make chat` / `make run` — text chat
- `make lint`
- `make clean` — remove venv and caches

Add new targets to the `Makefile` as the project grows.
