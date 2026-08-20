# Feature Spec: Testing Strategy, CI/CD, and Coverage

**Feature ID**: 005-testing-and-cicd  
**Status**: Partial (unit tests + CPU CI exist; coverage gates and image CI do not)  
**Related**: 001-voice-dgx-spark-agent, 003-deployment-infrastructure  
**Date**: 2025-05-21  
**Updated**: 2026-08-20

## Overview

The agent graph, config, and LLM factory need automated tests so changes do not rely on desk smoke only. This spec is the testing and delivery target. Some of it has shipped; some has not.

## Current State (2026-08-20)

- `tests/` exists: `test_agent_graph`, `test_chat`, `test_config`, `test_llm` (CPU, mocked externals).
- `pytest` + `pytest-asyncio` and `testpaths` are in `pyproject.toml`.
- GitHub Actions `.github/workflows/ci.yml` runs ruff + pytest with a CPU-only `--no-deps` install.
- No coverage measurement or coverage gate.
- No Docker image build in CI.
- No hardware-in-the-loop tests (and they stay out of every-PR CI).

## Goals

- Confidence that changes to the agent graph, tools, or voice layer do not break existing behavior.
- Fast feedback on pull requests.
- Ability to safely evolve the system on DGX Spark without constant manual smoke testing.
- Reasonable coverage targets without slowing down development.

## Testing Strategy

### Unit Tests
- Pure logic: config loading, LLM factory, memory tool helpers, prompt construction, state reducers.
- Mocked external services (Supermemory client, Riva client, LLM calls).
- Target: fast (< 30s total suite).

### Integration Tests
- Graph execution with real (or lightly mocked) tools.
- End-to-end voice loop with mocked audio/Riva (record → ASR → agent → TTS → play).
- Docker Compose smoke tests (does the stack start and report healthy?).
- These can be slower and may require GPU or specific services.

### Contract / Golden Tests (future)
- Snapshot testing of memory injection output for known user contexts.
- Regression tests for prompt formatting.

## CI/CD Pipeline (Proposed)

**Platform**: GitHub Actions (standard for this repo style)

**Workflows**:
1. **CI** (on push/PR to main and feature branches)
   - Lint + type check (`ruff`, `mypy`)
   - Unit tests + coverage
   - Build Docker image (multi-platform if needed)
   - Optional: integration tests (can be gated)

2. **Docker Build & Push** (on tags or manual)
   - Build agent image
   - Push to private container registry (user is acquiring credentials)
   - Tag with `git-sha` and semver when appropriate

3. **Deployment** (manual or protected branch)
   - Trigger on DGX (via webhook, SSH, or ArgoCD-style in the future)

**Coverage Target** (initial):
- Minimum 60% overall, with higher expectations on core agent logic (80%+ on `agent/` and `voice/` packages).
- Fail PRs only on significant drops, not on every new file.

## Tooling Recommendations

- **pytest** + `pytest-asyncio` (already partially declared)
- **coverage.py** or `pytest-cov`
- **ruff** + **mypy** (already in dev deps)
- GitHub Actions cache for pip and Docker layers
- Optional: `act` for local CI testing

## Out of Scope (initial wave)

- End-to-end hardware-in-the-loop tests on actual DGX (too slow/expensive for every PR)
- Mutation testing
- Performance benchmarking in CI

## Success Criteria

- Any developer can run the full test suite locally with `make test` (or `pytest`).
- Every PR gets automated feedback on lint, types, and coverage.
- We can confidently cut releases and push new agent images to the DGX registry.
- New contributors (or future agents) can understand how to add tests by looking at existing examples.

---

**Next Steps (when picked up)**: Create `tasks.md`, set up initial `tests/` structure + pytest config, add GitHub Actions workflow, wire coverage reporting, and update `Makefile`.