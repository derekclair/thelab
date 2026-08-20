"""
Basic audio I/O helpers using sounddevice.

Provides:
- Record audio from microphone until silence (simple energy VAD)
- Play audio to speakers
- Utility functions for normalization

This is intentionally simple for the Phase 1 MVP.
We can upgrade to webrtcvad or Silero VAD + proper streaming later.
"""

from __future__ import annotations

import numpy as np
import sounddevice as sd


class AudioConfig:
    """Audio settings for the voice pipeline."""

    sample_rate: int = 16000          # Good for both ASR and many TTS voices
    channels: int = 1
    dtype: str = "float32"            # We work in float32 [-1, 1]
    chunk_duration: float = 0.1       # How often we check for silence (seconds)
    silence_threshold: float = 0.01   # RMS energy below this = silence
    silence_duration: float = 0.8     # How long silence before we stop recording
    max_record_seconds: float = 30.0  # Safety cap


def record_until_silence(
    config: AudioConfig | None = None,
) -> np.ndarray:
    """
    Record from the default microphone until the user stops speaking.

    Uses a very simple energy-based VAD (RMS).

    Returns:
        1D float32 numpy array of the recorded audio (normalized [-1, 1]).
    """
    cfg = config or AudioConfig()

    print("[Audio] Listening... (speak now)")

    frames: list[np.ndarray] = []
    silence_counter = 0
    max_chunks = int(cfg.max_record_seconds / cfg.chunk_duration)

    stream = sd.InputStream(
        samplerate=cfg.sample_rate,
        channels=cfg.channels,
        dtype=cfg.dtype,
    )
    stream.start()

    try:
        for _ in range(max_chunks):
            audio_chunk, _ = stream.read(int(cfg.sample_rate * cfg.chunk_duration))
            audio_chunk = audio_chunk.flatten()

            # Simple RMS energy
            rms = np.sqrt(np.mean(audio_chunk**2))

            frames.append(audio_chunk)

            if rms < cfg.silence_threshold:
                silence_counter += 1
            else:
                silence_counter = 0

            if silence_counter * cfg.chunk_duration >= cfg.silence_duration:
                break
    finally:
        stream.stop()
        stream.close()

    if not frames:
        return np.array([], dtype=np.float32)

    full_audio = np.concatenate(frames)
    print(f"[Audio] Captured {len(full_audio) / cfg.sample_rate:.1f}s of audio")
    return full_audio


def play_audio(
    audio: np.ndarray,
    sample_rate: int = 16000,
    blocking: bool = True,
) -> None:
    """
    Play audio through the default output device.

    Args:
        audio: 1D float32 array in [-1.0, 1.0]
        sample_rate: Sample rate of the audio
        blocking: If True, wait until playback finishes
    """
    if len(audio) == 0:
        return

    print("[Audio] Playing response...")
    sd.play(audio, samplerate=sample_rate)
    if blocking:
        sd.wait()
    print("[Audio] Playback finished")


def get_default_devices() -> dict:
    """Return info about the current default input/output devices (useful for debugging)."""
    return {
        "input": sd.query_devices(kind="input"),
        "output": sd.query_devices(kind="output"),
    }
