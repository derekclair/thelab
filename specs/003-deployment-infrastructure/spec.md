# Feature Spec: Deployment Infrastructure & Dockerization (Gaps & Improvements)

**Feature ID**: 003-deployment-infrastructure  
**Status**: Draft  
**Related**: 001-voice-dgx-spark-agent  
**Date**: 2025-05-21

## Overview

The current Docker implementation (`Dockerfile` + `docker-compose.yml`) provides a basic skeleton for running the voice agent stack on DGX Spark. However, it has several gaps that would make real-world development, deployment, reliability, and operations painful — especially in a multi-GPU DGX environment shared with other workloads.

This spec captures the identified gaps and defines the target state for a production-capable deployment infrastructure.

## Current State (as of May 2025)

- Basic `Dockerfile` that installs the Python package in a slim image.
- `docker-compose.yml` with three services: `agent`, `riva`, `nemotron`.
- High-level deployment story documented in `plan.md` (Mac dev → build/push → DGX `docker compose up`).
- No healthchecks, limited resource controls, minimal volume strategy, no secrets management, weak networking documentation.

## Identified Gaps

### 1. Reliability & Operations
- No healthchecks on any service.
- No restart policies or restart backoff configuration.
- No readiness/liveness probes that the agent can use (especially important when Riva or Nemotron are still loading models).
- No graceful shutdown handling.

### 2. Resource Management on DGX Spark
- No explicit GPU device requests or limits per service (critical when multiple heavy services run on the same box).
- No CPU/memory limits.
- No support for different GPU allocation profiles (e.g., "light" vs "full" inference).

### 3. Model & Data Management
- Model volumes are declared but there is no clear strategy for:
  - First-time model download / initialization
  - Model versioning
  - Sharing models across containers efficiently
  - Backup/restore of important user data

### 4. Networking & Service Discovery
- Hardcoded service names (`riva`, `nemotron`) assume they are on the same Docker network.
- No clear documentation of required ports and protocols.
- No support for running the agent in "local dev" mode (talking to host-run Riva/Nemotron) vs full compose stack.

### 5. Configuration & Secrets
- Environment variables are passed through but there is no `.env` template or validation at compose time.
- No distinction between required vs optional variables.
- API keys (Supermemory, XAI, etc.) are treated as plain env vars with no secrets management story for DGX.

### 6. Image Build & Distribution
- No multi-stage optimization for smaller runtime images.
- No image tagging strategy (e.g., `git-sha`, `latest`, versioned releases).
- No documented path for using a private container registry (as the user is currently acquiring credentials for).

### 7. Development Experience
- Difficult to run just the agent code locally with mocked voice/LLM services.
- No `docker-compose.override.yml` or profiles for local development vs DGX production.
- No easy way to run tests inside the container.

### 8. Observability (Deferred per prior decision)
- No logging configuration.
- No metrics or tracing hooks (explicitly kicked for now).

## Requirements

- The deployment must be reliable enough to survive model loading delays and occasional GPU OOM situations on DGX.
- It must be possible for a new engineer (or future agent) to get the full stack running on a DGX Spark with reasonable effort.
- The same image built on a Mac (or CI) must run correctly on DGX.
- Clear separation between "I just want to hack on the agent logic" and "I want the full voice stack with real Riva + Nemotron".
- Support for the user's desired workflow: develop locally → dockerize → push to private registry → pull & run on DGX.

## Proposed Improvements (Prioritized)

### Phase A (High Value, Low Risk)
- Add healthchecks to all services.
- Add proper `deploy.resources` GPU reservations in compose.
- Create `.env.example` + validation.
- Improve `Dockerfile` (multi-stage, non-root user, smaller layers, better caching).
- Add Docker Compose profiles (`dev`, `full`, `riva-only`, etc.).
- Document local development with mocked services.

### Phase B (Medium)
- Robust volume strategy + model downloader helper service or script.
- Private registry push/pull workflow + credentials handling.
- Restart policies + resource limits.
- Basic structured logging configuration.

### Phase C (Later)
- Secrets management (Docker secrets, 1Password, Vault, etc.).
- Observability stack (when the team is ready).
- Automated image builds in CI.

## Success Criteria

- A new person can follow documented steps and have the full voice agent running on a DGX Spark in under 2 hours (assuming models are pre-cached or download is acceptable).
- The agent container can be updated independently of the heavy inference services.
- Switching between Grok and local Nemotron is a one-line environment variable change (already partially achieved).
- The stack is resilient to individual service restarts.

## Out of Scope (for this spec)

- Full production Kubernetes / DGX-specific orchestration (future).
- Advanced canary / blue-green deployments.
- Cost optimization across multiple DGX nodes.

---

**Next Steps (when we pick this up)**: Create `tasks.md` under this directory and begin closing the highest-impact gaps (healthchecks, resource requests, dev experience, registry workflow).