"""
System and GPU metrics sampler for benchmark runs.

Collects time-series data during voice agent runs so we can measure:
- Peak / average GPU memory usage (critical on 128 GB unified DGX Spark)
- Container memory (Riva, Nemotron, agent)
- CPU / power / thermals where available

Designed to be lightweight and safe to run alongside the voice loop.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional


def _now() -> float:
    return time.time()


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetricsSampler:
    """
    Background sampler that periodically collects system/GPU metrics
    and writes them as JSON lines into a report directory.
    """

    def __init__(
        self,
        report_dir: Path | str,
        interval: float = 2.0,
        containers: Optional[list[str]] = None,
        enabled: bool = True,
    ):
        self.report_dir = Path(report_dir)
        self.interval = interval
        self.containers = containers or ["riva", "nemotron", "agent", "thelab"]
        self.enabled = enabled and self._has_required_tools()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.gpu_file = self.report_dir / "gpu_samples.jsonl"
        self.docker_file = self.report_dir / "docker_stats.jsonl"
        self.system_file = self.report_dir / "system_samples.jsonl"

        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _has_required_tools(self) -> bool:
        """Check if we can actually collect useful data."""
        has_nvidia = shutil.which("nvidia-smi") is not None
        has_docker = shutil.which("docker") is not None
        return has_nvidia or has_docker

    def _sample_gpu(self) -> dict[str, Any]:
        """Sample NVIDIA GPU using nvidia-smi (works great on DGX Spark)."""
        if not shutil.which("nvidia-smi"):
            return {"available": False}

        try:
            # Query key fields in CSV for easy parsing
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,power.draw,temperature.gpu",
                "--format=csv,noheader,nounits",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {"error": result.stderr.strip()[:200]}

            lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 9:
                    gpus.append({
                        "index": int(parts[0]),
                        "name": parts[1],
                        "mem_total_mb": float(parts[2]),
                        "mem_used_mb": float(parts[3]),
                        "mem_free_mb": float(parts[4]),
                        "gpu_util_pct": float(parts[5]),
                        "mem_util_pct": float(parts[6]),
                        "power_w": float(parts[7]) if parts[7] else None,
                        "temp_c": float(parts[8]) if parts[8] else None,
                    })
            return {"available": True, "gpus": gpus}
        except Exception as e:
            return {"available": False, "error": str(e)}

    def _sample_docker(self) -> dict[str, Any]:
        """Sample memory/CPU for relevant containers."""
        if not shutil.which("docker"):
            return {"available": False}

        samples: dict[str, Any] = {}
        for name in self.containers:
            try:
                # Use docker stats once (non-streaming)
                cmd = [
                    "docker", "stats", name,
                    "--no-stream",
                    "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
                if result.returncode == 0 and result.stdout.strip():
                    line = result.stdout.strip().split("\n")[0]
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        samples[name] = {
                            "cpu_pct": parts[1],
                            "mem_usage": parts[2],
                            "mem_pct": parts[3] if len(parts) > 3 else None,
                        }
            except Exception:
                continue

        return {"available": bool(samples), "containers": samples}

    def _sample_system(self) -> dict[str, Any]:
        """Basic system memory (works on macOS and Linux/DGX)."""
        try:
            # Use vm_stat on mac, /proc/meminfo on Linux
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo") as f:
                    meminfo = f.read()
                # Very rough parse for MemTotal / MemAvailable
                total = None
                available = None
                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        total = int(line.split()[1])  # kB
                    if "MemAvailable:" in line:
                        available = int(line.split()[1])
                if total and available:
                    used = total - available
                    return {
                        "total_kb": total,
                        "used_kb": used,
                        "available_kb": available,
                        "used_pct": round(used / total * 100, 1),
                    }
            # Fallback: use psutil if available (not a hard dep)
            try:
                import psutil  # type: ignore
                vm = psutil.virtual_memory()
                return {
                    "total_bytes": vm.total,
                    "used_bytes": vm.used,
                    "available_bytes": vm.available,
                    "used_pct": vm.percent,
                }
            except ImportError:
                pass
        except Exception:
            pass
        return {"available": False}

    def _write_sample(self, filename: Path, data: dict[str, Any]) -> None:
        data = {"ts": _now(), "iso": _iso(), **data}
        with filename.open("a") as f:
            f.write(json.dumps(data, default=str) + "\n")

    def _sample_loop(self) -> None:
        """Main sampling loop."""
        while not self._stop_event.is_set():
            try:
                gpu = self._sample_gpu()
                if gpu.get("available"):
                    self._write_sample(self.gpu_file, {"type": "gpu", **gpu})

                docker = self._sample_docker()
                if docker.get("available"):
                    self._write_sample(self.docker_file, {"type": "docker", **docker})

                system = self._sample_system()
                if system.get("used_pct") is not None or system.get("available"):
                    self._write_sample(self.system_file, {"type": "system", **system})

            except Exception as e:
                # Never let the sampler crash the benchmark
                self._write_sample(
                    self.report_dir / "sampler_errors.jsonl",
                    {"type": "sampler_error", "error": str(e)},
                )

            self._stop_event.wait(self.interval)

    def start(self) -> None:
        """Start background sampling (no-op if disabled or already running)."""
        if not self.enabled or self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True, name="metrics-sampler")
        self._thread.start()

    def stop(self) -> None:
        """Stop the sampler cleanly."""
        if self._stop_event:
            self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def quick_peak_analysis(report_dir: Path | str) -> dict[str, Any]:
    """Very lightweight post-run analysis to extract peaks from collected samples."""
    report_dir = Path(report_dir)
    peaks: dict[str, Any] = {}

    # GPU peak memory
    gpu_file = report_dir / "gpu_samples.jsonl"
    if gpu_file.exists():
        max_used = 0.0
        for line in gpu_file.read_text().splitlines():
            try:
                data = json.loads(line)
                for g in data.get("gpus", []):
                    max_used = max(max_used, g.get("mem_used_mb", 0))
            except Exception:
                continue
        if max_used > 0:
            peaks["gpu_mem_peak_mb"] = round(max_used, 1)

    # System memory peak (rough)
    sys_file = report_dir / "system_samples.jsonl"
    if sys_file.exists():
        max_used_pct = 0.0
        for line in sys_file.read_text().splitlines():
            try:
                data = json.loads(line)
                pct = data.get("used_pct", 0)
                if isinstance(pct, (int, float)):
                    max_used_pct = max(max_used_pct, pct)
            except Exception:
                continue
        if max_used_pct > 0:
            peaks["system_mem_peak_pct"] = round(max_used_pct, 1)

    return peaks


if __name__ == "__main__":
    # Quick manual test
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        sampler = MetricsSampler(tmp, interval=1.0)
        print("Sampler enabled:", sampler.enabled)
        sampler.start()
        time.sleep(3)
        sampler.stop()
        print("Sample files created:", list(Path(tmp).glob("*.jsonl")))