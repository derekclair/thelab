# Dockerfile for the thelab-voice-agent service
# Target: DGX Spark (and general NVIDIA GPU environments)

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy everything needed for metadata + build
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Build the wheel (non-editable, clean)
RUN pip install --no-cache-dir build && \
    python -m build --wheel --outdir /wheels .

# ---- Runtime image ----
FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Audio runtime for sounddevice (used by the voice layer for mic/speakers on desktop DGX Spark).
# This is only required when running `thelab-chat voice`. The text `chat` command works without it.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Install the wheel + runtime deps only
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    chown -R appuser:appuser /app

USER appuser

# Default command (override in compose or at runtime)
# Example for voice: thelab-chat voice --user derek
ENTRYPOINT ["thelab-chat"]
CMD ["--help"]
