# Feature Spec: Testing Strategy, CI/CD, and Coverage

**Feature ID**: 005-testing-and-cicd  
**Status**: Draft  
**Related**: 001-voice-dgx-spark-agent, 003-deployment-infrastructure  
**Date**: 2025-05-21

## Overview

The repository currently has almost no automated tests, no CI pipeline, and no coverage measurement. As the system grows (especially the agent brain, voice layer, and multi-service Docker stack), this becomes a major risk.

This spec defines the target testing and delivery infrastructure.

## Current State

- No `tests/` directory with meaningful coverage.
- No `pytest` configuration beyond a stub in `pyproject.toml`.
- No GitHub Actions or other CI workflow.
- No coverage reporting (codecov, etc.).
- Manual testing is the primary validation method.

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