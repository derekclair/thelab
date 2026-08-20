# Tasks: Testing strategy, CI/CD, and coverage (005)

**Feature**: 005-testing-and-cicd
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

The May 2025 spec said there was no `tests/` directory and no GitHub Actions.
That is outdated. Phase 0 is **done**. Coverage gates, GPU e2e, and Docker
image CI are **not**.

## Phase 0 — Unit tests + CPU CI (done)

- [x] `tests/` directory with meaningful unit tests
- [x] `tests/test_agent_graph.py` — graph routing + memory injection (mocked tools)
- [x] `tests/test_chat.py` — `MemoryContext.to_prompt_block`
- [x] `tests/test_config.py` — `Settings.validate_keys`
- [x] `tests/test_llm.py` — `get_chat_model` provider routing
- [x] pytest + pytest-asyncio in `[project.optional-dependencies] dev`
- [x] `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `asyncio_mode = auto`)
- [x] `.github/workflows/ci.yml` on push and pull_request
- [x] CI: ruff check
- [x] CI: pytest -q on ubuntu-latest
- [x] CI: CPU-only install (`pip install -e . --no-deps` + lightweight brain deps; no Riva / PortAudio)

## Phase 1 — Coverage, DX, types

- [ ] `pytest-cov` or coverage.py wired so `pytest` can emit a report
- [ ] Coverage **gate** (spec floor: 60% overall; 80%+ on `agent/` and `voice/` once measured honestly)
- [ ] Fail PRs on the gate (or on a significant drop) — not "coverage is printed but ignored"
- [ ] `make test` (Makefile currently has `lint`, not pytest)
- [ ] mypy in CI (local `make lint` already runs ruff + mypy; Actions does not)
- [ ] pip cache on the CI job

## Phase 2 — Docker image CI

- [ ] CI job that builds the agent image from the root `Dockerfile`
- [ ] Tag with `git-sha` (semver when tags exist)
- [ ] Optional push to a private registry via operator secrets — **no registry hostname in git**
- [ ] Multi-platform build only if we need amd64 CI → aarch64 Spark; do not assume it

## Phase 3 — Gated / heavier tests

- [ ] Integration: graph execution with lightly mocked tools beyond the current unit file
- [ ] Voice loop with mocked audio / Riva (this repo's `voice/` package)
- [ ] Compose smoke: stack starts and reports healthy (depends on [003](../003-deployment-infrastructure/tasks.md) probes actually meaning ready)
- [ ] GPU e2e on a Spark or GPU runner — **not** on every PR

## Out of scope (leave unchecked on purpose)

- [ ] Hardware-in-the-loop on the Lenovo Go in this repo's CI
- [ ] Mutation testing
- [ ] Performance benchmarking in CI
- [ ] Hosted coverage SaaS (optional; not required to close the gate)

## Traceability

Unit tests and the CPU workflow are in this repo today
(`.github/workflows/ci.yml`, `tests/`). Live spoken e2e belongs to
[`derekclair/conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent)
(spec 008), not this checklist.
