# Plan: Deployment infrastructure & Dockerization (003)

**Feature**: 003-deployment-infrastructure
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-19 (SDD record; spec drafted 2025-05-21)

## 1. Architecture

Two deployment stories. Only one of them is the live spoken path.

```
Live desk voice (NOT this compose)
  Lenovo Go (ALSA / HID)
        │
        ▼
  conversational-voice-agent   ← STT / TTS / button / LED
        │  get_agent()
        ▼
  this package (thelab_langchain)

Experimental compose in *this* tree
  agent  ──gRPC──►  riva
       ──HTTP──►  nemotron NIM
```

| Piece | Owner |
|-------|--------|
| Live STT, TTS, USB I/O | [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) ([spec 008](../008-local-tts-lenovo-go-spike/plan.md)) |
| LangGraph brain, provider factory | **this repo** |
| Experimental `agent` + `riva` + `nemotron` Compose | `docker-compose.yml` here — **not** production voice |
| Riva wrappers in `src/thelab_langchain/voice/` | Spike / Phase 2; streaming still `NotImplementedError` |

`docker compose up` of this file is an experiment toward spec 001's Riva/NIM stack. It is not how the desk currently talks.

## 2. What is already in the tree

Honest inventory — the May 2025 spec "current state" is stale.

| Artifact | What it actually is |
|----------|---------------------|
| `Dockerfile` | Multi-stage slim Python image, non-root `appuser`, PortAudio for `sounddevice`. Exists. |
| `docker-compose.yml` | Three services (`agent`, `riva`, `nemotron`) with Compose **profiles**, `restart: unless-stopped`, named model volumes. Experimental. |
| YAML `healthcheck:` blocks | Present on all three services. Agent probe is `import thelab_langchain` (import-ok, not readiness). Riva/NIM HTTP probes are unproven on this hardware. **Still a gap.** |
| YAML `deploy.resources` GPU reservations | Present. Swarm-style `deploy.devices` is not a verified `docker compose up` GPU story. No CPU/memory limits. No light-vs-full GPU profiles. **Still a gap.** |
| `.env.example` | Documents Python/app keys and provider flags. Not compose-time validation. |
| Makefile `docker-build` / `docker-push` | Local helpers. Tag and registry come from the operator's environment. This SDD does not name a registry host. |

There is no `docker-compose.override.yml`, no model-downloader service, no secrets driver, and no CI image build (see [005](../005-testing-and-cicd/plan.md)).

## 3. Tech choices (locked for this spec)

| Concern | Choice | Why |
|---------|--------|-----|
| Live voice I/O | Sibling `conversational-voice-agent` | Spec 008 already runs on the desk; do not pretend Compose is that path |
| Experimental GPU stack | Compose on a single DGX Spark | Spec out of scope: Kubernetes / multi-node |
| Agent image | Existing multi-stage `Dockerfile` | Same image should run on a laptop CI runner *or* Spark; no Mac-only layers |
| GPU in Compose | Compose-native device requests (`gpus` / device_requests), not Swarm-only `deploy` | `docker compose up` is the intended command |
| Secrets | Host `.env` (gitignored); never bake keys into compose YAML or this SDD | No secrets in compose docs |
| Private registry | Operator sets `REGISTRY` + `TAG`; push/pull is a documented workflow, not a hostname in git | Do not commit a registry URL |
| LLM switch | Existing `LLM_PROVIDER` / `openai_compatible` | One-line switch; Compose must not fork the factory |
| Observability | Deferred (spec Phase C) | Structured logs later; no metrics stack in this wave |

Do not put API keys, NGC tokens, or example secret values in compose comments or this directory.

## 4. Phases

### Phase A — Reliability & DX (high value)

Close the gaps that make the *experimental* stack start and fail loudly:

- Healthchecks that mean "ready for traffic", not "Python import succeeded". Agent should wait on real Riva/NIM readiness when those profiles are used.
- Compose-native GPU reservations that `docker compose up` honors; CPU/memory limits so one service cannot starve the box.
- `.env.example` fields the compose stack actually reads, with required vs optional called out (names only — no values).
- Compose profiles that match the comments (`full`, `agent`, `riva-only`, `nemotron-only`). Today every service has a profile, so a bare `docker compose up` starts nothing.
- A documented **hack-on-the-brain** path: venv + mocked / host LLM, no Riva container required. Live spoken testing stays in the sibling repo.

Dockerfile multi-stage + non-root is already done; do not redo it unless a probe or user change requires it.

### Phase B — Volumes, registry, restarts

- First-run model download / cache story for Riva and NIM volumes (script or one-shot service). Version the cache layout; do not copy weights into the agent image.
- Private registry workflow: build → tag (`git-sha` and optional semver) → push → pull on Spark. Registry hostname stays in the operator's environment, not in SDD.
- Restart backoff that survives model-load and GPU OOM without a tight crash loop.
- Basic structured logging (no Prometheus/Grafana yet).

### Phase C — Later

- Secrets management (Docker secrets / a vault) instead of plain env.
- Observability stack (when the team is ready).
- Automated image builds in CI — owned with spec 005; this spec only requires the image to *be* buildable.

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Treating `docker-compose.yml` as the live voice stack | This plan + README: live path is the sibling I/O repo; Compose is experimental |
| Riva `2.15.0` image vs current Spark GPU | Compose already notes GB10 may not run that tag; do not block desk voice on it |
| Large NIM as compose default vs spec 007 budget | Do not bless 120B-class agent loops on one Spark; keep NIM as an experiment |
| Swarm `deploy.resources` ignored by Compose | Move GPU requests to a Compose-native key and verify with `nvidia-smi` in-container |
| Import-only agent healthcheck | Replace with a real ready check; `depends_on: service_healthy` is useless until then |
| Secrets or a registry hostname landing in git | `.env` gitignored; SDD and compose comments stay hostname-free and key-free |

## 6. Success metrics

- A new person can follow a runbook and bring up the **experimental** full profile on a Spark in under two hours when models are cached (spec success criterion). This is not "desk voice works."
- Agent image rebuilds independently of Riva/NIM images.
- `LLM_PROVIDER` remains a one-line switch (already true in code).
- Individual experimental services can restart without taking the others down permanently.
- Live spoken sessions still go through [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent).

## 7. What this plan is not

It is not a rewrite of spec 001. It is not the Lenovo Go spike (008). It is not Kubernetes, canary deploys, or cost work across multiple Sparks (spec out of scope). It does not document a private registry hostname or any credentials.
