"""
Benchmark harness for the thelab-langchain voice agent on DGX Spark.

This package provides tools to measure:
- Voice turn latency (end-of-speech → first audio)
- LLM TTFT + generation speed
- Memory / VRAM usage under load
- Concurrency behavior
- etc.

All reports go under benchmarks/reports/ and are committed with pinned configs.

See specs/007-dgx-hardware-optimization/ for the overall plan and tasks.
"""

__version__ = "0.1.0"