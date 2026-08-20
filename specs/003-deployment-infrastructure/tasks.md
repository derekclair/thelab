# Tasks: Deployment infrastructure & Dockerization (003)

**Feature**: 003-deployment-infrastructure
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Checkboxes are the honest tree as of this SDD record, not the May 2025 spec
"current state". Compose here is **experimental**. Live voice I/O is
[`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent).

Do not commit secrets, serials, or a registry hostname in any of this work.

## Already in tree (do not redo as if missing)

- [x] Multi-stage `Dockerfile` (builder wheel → slim runtime, non-root user)
- [x] Root `docker-compose.yml` with `agent`, `riva`, `nemotron` services
- [x] Compose profiles keys (`full`, `agent`, `riva` / `riva-only`, `nemotron` / `nemotron-only`)
- [x] `restart: unless-stopped` on those services
- [x] Named volumes declared for Riva / NIM caches
- [x] `.env.example` for the Python app (provider + key *names*)
- [x] Makefile `docker-build` / `docker-push` taking `REGISTRY` + `TAG` from the environment

## Phase A — Reliability & DX

YAML stubs exist for health and GPU; they are **not** done.

- [ ] Real healthchecks: agent ready for traffic (not `import thelab_langchain`)
- [ ] Real healthchecks: Riva and NIM probes verified on the images we actually run
- [ ] Agent `depends_on` / startup order that waits on those probes when using `full`
- [ ] Compose-native GPU device requests that `docker compose up` honors (not Swarm-only `deploy.resources`)
- [ ] CPU and memory limits per service
- [ ] Light vs full GPU allocation profiles (documented, not just a comment)
- [ ] Bare `docker compose up` vs `--profile` behavior matches the file comments (today a bare up starts nothing)
- [ ] `.env.example` lists compose-relevant variables; required vs optional; **no secret values**
- [ ] Document hack-on-the-brain: `make install` / `make chat` with host or mocked LLM, no Riva
- [ ] Document that spoken I/O is the sibling repo, not this compose file

## Phase B — Volumes, registry, restarts

- [ ] First-run model download / cache helper (script or one-shot service)
- [ ] Document volume layout and how caches are shared; do not copy weights into the agent image
- [ ] Registry workflow in a runbook: build → tag `git-sha` (and optional semver) → push → pull on Spark
- [ ] Keep registry hostname out of git and out of this SDD (operator env only)
- [ ] Restart policy / backoff that survives model load and GPU OOM
- [ ] Basic structured logging configuration (no metrics stack)

## Phase C — Later

- [ ] Secrets mechanism other than plain env (Docker secrets or a vault)
- [ ] Observability stack (deferred with the spec)
- [ ] Automated image build in CI (tracked in [005](../005-testing-and-cicd/tasks.md); this spec only needs the image to stay buildable)

## Out of scope (leave unchecked on purpose)

- [ ] Kubernetes / Spark-specific cluster orchestration
- [ ] Canary / blue-green
- [ ] Multi-node cost / placement
- [ ] Replacing the live 008 voice path with Riva Compose

## Traceability

Implementation of the live spoken path is
[`derekclair/conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent).
This tasks file is the checklist for *this* repo's experimental Compose/Docker
gaps. Dockerfile + compose skeleton are already here; health, Compose GPU, and
registry hygiene are not.
