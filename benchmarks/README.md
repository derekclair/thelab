# Benchmark Harness for DGX Spark Voice Agent

This directory contains the measurement tooling for **Feature 007: DGX Hardware Optimization & Sweet-Spot Discovery**.

## Purpose

We need hard numbers, not vibes.

Every optimization (audio stack changes, model swaps, context tuning, etc.) must be validated against a reproducible baseline captured on the real DGX Spark hardware.

## Quick Start (on DGX)

```bash
# Make sure the agent + Riva/NIM services are up
docker compose up -d

# Run a short-turn benchmark session (records metrics + timing)
python -m benchmarks.runner --scenario short --user derek --output-dir benchmarks/reports/my-run

# Or after we add the entry point:
# thelab-bench --scenario short ...
```

## Directory Layout

```
benchmarks/
├── __init__.py
├── README.md
├── runner.py          # Main CLI / harness
├── reports/           # Timestamped result directories (committed)
│   └── 2025-05-22-baseline-120b-riva/
│       ├── summary.md
│       ├── metrics.json
│       └── raw/
└── (future) timing.py, metrics.py, comparators.py
```

## Reports

Each run creates a directory with:
- `summary.md` — human readable key metrics + notes
- `metrics.jsonl` or `metrics.json` — structured data for comparison scripts
- `events.jsonl` — detailed timestamped events from the orchestrator
- `nvidia-smi.log`, `docker-stats.log`, etc.
- `config.json` — exact image tags, env vars, compose profile used

## Instrumentation

The voice loop is lightly instrumented when `BENCHMARK_MODE=1` is set.

See `src/thelab_langchain/voice/orchestrator.py` for the event hooks.

## Scenarios

- `short`: Quick Q&A + memory recall turns (default for latency)
- `long`: Extended household conversation (tests context / KV pressure)
- `concurrent`: Multiple simulated users (future)

## Comparison

Later we will add `python -m benchmarks.compare report1 report2` to generate delta tables.

## Related

- [specs/007-dgx-hardware-optimization/spec.md](../specs/007-dgx-hardware-optimization/spec.md)
- [specs/007-dgx-hardware-optimization/plan.md](../specs/007-dgx-hardware-optimization/plan.md)
- [specs/007-dgx-hardware-optimization/tasks.md](../specs/007-dgx-hardware-optimization/tasks.md)

Let's measure what actually happens on the hardware. No guessing.