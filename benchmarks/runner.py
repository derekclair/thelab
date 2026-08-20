"""
Benchmark runner for the thelab voice agent on DGX Spark.

This is the entry point for controlled measurement runs.

Usage (early skeleton):
    python -m benchmarks.runner --scenario short --user derek --output-dir benchmarks/reports/test-run

Later this will become `thelab-bench` and grow rich timing + metrics collection.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel

from .metrics import MetricsSampler, quick_peak_analysis

console = Console()
app = typer.Typer(
    name="thelab-bench",
    help="Benchmark harness for thelab-langchain voice agent (DGX Spark optimization)",
    add_completion=False,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_report_dir(base: Path, scenario: str) -> Path:
    """Create a timestamped report directory."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_dir = base / f"{ts}_{scenario}"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _write_config_snapshot(report_dir: Path, extra: dict[str, Any] | None = None) -> Path:
    """Capture environment and settings for reproducibility."""
    cfg = {
        "timestamp": _now_iso(),
        "scenario": extra.get("scenario") if extra else None,
        "user": extra.get("user") if extra else None,
        "env": {
            k: v
            for k, v in os.environ.items()
            if any(x in k.upper() for x in ("RIVA", "NIM", "LLM", "BENCHMARK", "USER"))
            or k in ("DOCKER_HOST",)
        },
        "python": sys.version,
        "cwd": str(Path.cwd()),
    }
    if extra:
        cfg.update(extra)

    path = report_dir / "config.json"
    path.write_text(json.dumps(cfg, indent=2, default=str))
    return path


def _log_event(report_dir: Path, event: dict[str, Any]) -> None:
    """Append a structured event line."""
    events_file = report_dir / "events.jsonl"
    event = {"ts": _now_iso(), **event}
    with events_file.open("a") as f:
        f.write(json.dumps(event) + "\n")


@app.command()
def run(
    scenario: Annotated[
        str,
        typer.Option("--scenario", "-s", help="Benchmark scenario: short | long | concurrent"),
    ] = "short",
    user: Annotated[
        str | None,
        typer.Option("--user", "-u", help="User ID (Supermemory container)"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Base directory for reports"),
    ] = Path("benchmarks/reports"),
    duration: Annotated[
        int | None,
        typer.Option("--duration", "-d", help="Max seconds to run (None = until Ctrl+C)"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Just set up the report dir and print what would happen"),
    ] = False,
) -> None:
    """
    Run a benchmark session and capture timing + system metrics.

    This is the primary entry point for Phase 0 baseline capture and all subsequent experiments.
    """
    user_id = user or os.getenv("DEFAULT_USER_ID", "grok-dgx-voice-agent")

    console.print(
        Panel.fit(
            f"[bold cyan]thelab-bench[/bold cyan]\n\n"
            f"Scenario : [green]{scenario}[/green]\n"
            f"User     : [cyan]{user_id}[/cyan]\n"
            f"Output   : [magenta]{output_dir}[/magenta]\n"
            f"Duration : {duration or 'until Ctrl+C'}s\n\n"
            "Setting BENCHMARK_MODE=1 for instrumentation.",
            title="Benchmark Run Starting",
            border_style="cyan",
        )
    )

    report_dir = _create_report_dir(output_dir, scenario)
    console.print(f"[green]Report directory:[/green] {report_dir}")

    # Capture starting state
    _write_config_snapshot(report_dir, {"scenario": scenario, "user": user_id})
    _log_event(report_dir, {"type": "benchmark_start", "scenario": scenario, "user_id": user_id})

    if dry_run:
        console.print("[yellow]Dry run complete. No voice session launched.[/yellow]")
        _log_event(report_dir, {"type": "dry_run_complete"})
        return

    # Set benchmark mode so the orchestrator emits timing events
    env = os.environ.copy()
    env["BENCHMARK_MODE"] = "1"
    env["BENCHMARK_REPORT_DIR"] = str(report_dir)
    if user_id:
        env["DEFAULT_USER_ID"] = user_id

    # Start background system/GPU metrics sampler (very valuable on DGX Spark)
    sampler = MetricsSampler(
        report_dir=report_dir,
        interval=2.0,
        containers=["riva", "nemotron", "agent", "thelab-agent"],
    )
    sampler.start()
    _log_event(report_dir, {"type": "metrics_sampler_started", "enabled": sampler.enabled})

    # For now, we invoke the existing thelab-chat voice command.
    # In a more advanced version we will call the orchestrator directly with hooks.
    cmd = [sys.executable, "-m", "thelab_langchain.cli", "voice", "--user", user_id]

    console.print(f"\n[bold]Launching voice session with BENCHMARK_MODE=1...[/bold]")
    console.print(f"[dim]Command:[/dim] {' '.join(cmd)}")
    console.print("[yellow]Speak normally. Press Ctrl+C when finished with the benchmark run.[/yellow]\n")

    start_time = time.time()

    try:
        proc = subprocess.Popen(cmd, env=env)
        if duration:
            try:
                proc.wait(timeout=duration)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait()
        else:
            proc.wait()
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark run interrupted by user.[/yellow]")
        if "proc" in locals():
            proc.terminate()
            proc.wait()
    finally:
        # Stop the metrics sampler first
        sampler.stop()
        _log_event(report_dir, {"type": "metrics_sampler_stopped"})

        elapsed = time.time() - start_time
        _log_event(
            report_dir,
            {
                "type": "benchmark_end",
                "elapsed_seconds": round(elapsed, 2),
                "returncode": getattr(proc, "returncode", None) if "proc" in locals() else None,
            },
        )

        # Quick automatic peak analysis (extremely useful for headroom decisions)
        peaks = quick_peak_analysis(report_dir)
        if peaks:
            _log_event(report_dir, {"type": "peak_analysis", **peaks})

        # Write a minimal summary
        summary = report_dir / "summary.md"
        summary.write_text(
            f"# Benchmark Run Summary\n\n"
            f"**Scenario**: {scenario}\n"
            f"**User**: {user_id}\n"
            f"**Started**: {_now_iso()}\n"
            f"**Duration**: {elapsed:.1f}s\n\n"
            f"**Peaks (auto-detected)**:\n"
            f"{json.dumps(peaks, indent=2) if peaks else '  (no peaks extracted - check nvidia-smi/docker availability)'}\n\n"
            f"See `events.jsonl`, `gpu_samples.jsonl`, `docker_stats.jsonl`, and `config.json` for full details.\n\n"
            f"---\n\n"
            f"Next step: run comparison tooling against baseline.\n"
        )

        console.print(f"\n[green]Benchmark complete.[/green] Report written to: {report_dir}")
        console.print(f"[dim]Key files: events.jsonl, gpu_samples.jsonl, docker_stats.jsonl, summary.md[/dim]")
        if peaks:
            console.print(f"[cyan]Auto-detected peaks:[/cyan] {peaks}")


if __name__ == "__main__":
    app()