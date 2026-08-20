# Plan: Testing strategy, CI/CD, and coverage (005)

**Feature**: 005-testing-and-cicd
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-19 (SDD record; spec drafted 2025-05-21)

## 1. Architecture

Tests live in this repo. CI is GitHub Actions on a CPU runner. Live spoken I/O
and GPU voice loops are **not** in this workflow.

```
PR / push
    │
    ▼
.github/workflows/ci.yml     ubuntu-latest, no GPU
    ├── ruff check .
    └── pytest -q             tests/ only, mocked services
```

| Layer | Where | What it covers |
|-------|--------|----------------|
| Unit (shipped) | `tests/` | Graph routing, memory injection, config keys, LLM factory, prompt block |
| CI (shipped) | `.github/workflows/ci.yml` | Ruff + pytest, CPU-only install (`pip install -e . --no-deps` + lightweight deps) |
| Coverage gates | **not shipped** | spec target 60% overall / 80%+ on `agent/` and `voice/` |
| Docker image CI | **not shipped** | build (and later push) of the agent image |
| GPU / hardware e2e | **not shipped** | out of scope for every PR (spec) |

The May 2025 spec "current state" (`No tests/ directory`, `No GitHub Actions`) is
**wrong today**. Do not plan as if those are missing.

## 2. What is already in the tree

| Artifact | Notes |
|----------|--------|
| `tests/test_agent_graph.py` | `_should_continue` routing; `_memory_injection` with mocked tools; no extra summarization LLM |
| `tests/test_chat.py` | `MemoryContext.to_prompt_block` |
| `tests/test_config.py` | `Settings.validate_keys` per provider |
| `tests/test_llm.py` | `get_chat_model` routing with fake provider modules |
| `pyproject.toml` | `pytest` + `pytest-asyncio`; `[tool.pytest.ini_options]` `testpaths = ["tests"]`, `asyncio_mode = auto` |
| `ruff` / `mypy` | Dev deps. `make lint` runs both. **CI runs ruff only**, not mypy. |
| CI install | Skips `sounddevice` / `nvidia-riva-client` so a plain runner can import the brain |

There is **no** `make test` target (Makefile has `lint`, not pytest). There is
**no** `pytest-cov` / coverage config. There is **no** image-build job. There is
**no** GPU job.

## 3. Tech choices (locked for this spec)

| Concern | Choice | Why |
|---------|--------|-----|
| Runner | GitHub Actions `ubuntu-latest` | Matches the existing workflow |
| Unit suite | pytest, mocked Supermemory / LLM | Fast, no keys, no GPU, no PortAudio |
| Lint on PR | ruff (already) | Keep the current job; add mypy later, do not drop ruff |
| Coverage | `pytest-cov` / coverage.py when we add gates | Spec names these; do not invent a hosted-coverage vendor requirement |
| Image CI | Separate job or workflow, not on the CPU unit job | Unit job must stay lightweight |
| GPU e2e | Gated / manual / self-hosted later | Spec: not on every PR |
| Live voice | Sibling [`conversational-voice-agent`](https://github.com/derekclair/conversational-voice-agent) | Do not put ALSA / Parakeet / Piper in this repo's CI |

No API keys in workflow files. No registry hostname in workflow YAML committed
to this repo; if a later push job needs a registry, it reads from Actions
secrets / env that are not documented as literals here.

## 4. Phases

### Phase 0 — Unit + CPU CI (done)

Keep:

- `tests/` as the example for new tests (spec success: contributors copy these).
- CPU-only CI install so audio/GPU deps do not break the runner.
- Ruff + pytest on push and pull_request.

Do not delete or "bootstrap" a tests directory that already exists.

### Phase 1 — Coverage, DX, types in CI

- Add coverage measurement (`pytest-cov` or coverage.py) and a **gate** that
  matches the spec's intent: fail on significant drops / below the initial
  floor (60% overall; 80%+ on `agent/` and `voice/` once those packages are
  measured honestly — `voice/` is mostly untested Riva spike code).
- `make test` (and optionally `make test-cov`) so local DX matches CI.
- Add mypy to CI if we want the spec's "lint + type check" line; local
  `make lint` already runs it.
- Cache pip in Actions.

### Phase 2 — Docker image CI

- Build the agent image from the existing `Dockerfile` on tags and/or main.
- Tag with `git-sha` (and semver when we cut tags).
- Push is optional and operator-configured. Do not bake a registry URL into
  the workflow file in git.
- Multi-platform only if we prove we need it (Spark is aarch64; CI is amd64).

Compose stack smoke (`docker compose` healthy) is integration, not this unit
job. It stays gated.

### Phase 3 — Heavier tests (gated)

- Graph integration with real-ish tools (still no live Supermemory account in CI).
- Voice loop with mocked audio / Riva — this repo's `voice/` module, not 008.
- GPU e2e on a Spark or a GPU runner: **not** every PR.
- Hardware-in-the-loop with the Lenovo Go: out of scope for this package's CI.

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Planning as if `tests/` or CI do not exist | This plan; mark those tasks `[x]` |
| Coverage gate that punishes the untested `voice/` spike | Measure `agent/` first; do not fail the repo for Riva `NotImplementedError` paths until we test them |
| Pulling audio/GPU wheels on `ubuntu-latest` | Keep the CPU-only `--no-deps` install in CI |
| Image push leaking a registry hostname or credentials | Secrets only; SDD stays hostname-free |
| Treating Compose e2e as desk voice | Compose is experimental (003); live I/O is the sibling repo |

## 6. Success metrics

- `pytest` locally (ideally `make test`) runs the unit suite in well under 30s.
- Every PR gets ruff + unit results (already true).
- Coverage gate exists before we claim "CI enforces coverage."
- Image builds in CI before we claim "we can cut a Spark image from git."
- New tests follow `tests/test_*.py` patterns (mocked services, no keys).

## 7. What this plan is not

It is not a claim that the May 2025 spec current-state bullets are still true.
It is not GPU voice CI. It is not mutation testing or a performance bench in
Actions (spec out of scope). It is not the 008 hardware loop.
