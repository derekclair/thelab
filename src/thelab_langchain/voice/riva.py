"""
NVIDIA Riva client wrappers for ASR (STT) and TTS.

This module provides a clean interface over the official `nvidia-riva-client`
so the rest of the voice layer doesn't have to know gRPC details.

Designed for local Riva / NeMo deployment on DGX Spark.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import riva.client
from riva.client import (
    ASRService,
    Auth,
    RecognitionConfig,
    SpeechSynthesisService,
)


@dataclass
class RivaConfig:
    """Configuration for connecting to a Riva server."""

    uri: str = "localhost:50051"
    ssl: bool = False
    language_code: str = "en-US"
    # ASR
    asr_model: str = ""  # leave empty for server default
    # TTS
    tts_voice: str = ""  # e.g. "English-US.Female-1" or leave empty for default


def _make_auth(cfg: RivaConfig) -> Auth:
    return Auth(uri=cfg.uri, use_ssl=cfg.ssl)


class RivaASR:
    """Wrapper around Riva ASR (speech-to-text)."""

    def __init__(self, config: RivaConfig | None = None):
        self.config = config or RivaConfig()
        auth = _make_auth(self.config)
        self._client = ASRService(auth)

    def recognize(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> str:
        """
        Transcribe a full audio buffer (non-streaming).

        Args:
            audio: 1D float32 numpy array in [-1.0, 1.0] or int16.
            sample_rate: Sample rate of the audio (Riva typically expects 16000).

        Returns:
            The transcribed text.
        """
        if audio.dtype != np.int16:
            # Convert float32 [-1,1] → int16
            audio = (audio * 32767).astype(np.int16)

        config = RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=sample_rate,
            language_code=self.config.language_code,
            model=self.config.asr_model or None,
            max_alternatives=1,
            enable_automatic_punctuation=True,
        )

        response = self._client.offline_recognize(audio, config)
        if response.results:
            return response.results[0].alternatives[0].transcript.strip()
        return ""

    # TODO (Phase 2): Add streaming_recognize() for real-time partial results


class RivaTTS:
    """Wrapper around Riva TTS (text-to-speech)."""

    def __init__(self, config: RivaConfig | None = None):
        self.config = config or RivaConfig()
        auth = _make_auth(self.config)
        self._client = SpeechSynthesisService(auth)

    def synthesize(
        self,
        text: str,
        sample_rate: int = 22050,
    ) -> np.ndarray:
        """
        Convert text to audio waveform.

        Returns:
            1D float32 numpy array normalized to [-1.0, 1.0]
        """
        response = self._client.synthesize(
            text=text,
            voice_name=self.config.tts_voice or None,
            language_code=self.config.language_code,
            sample_rate_hertz=sample_rate,
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
        )

        audio = np.frombuffer(response.audio, dtype=np.int16)
        # Normalize to float32 [-1.0, 1.0]
        return audio.astype(np.float32) / 32768.0


# Convenience factory
def get_riva_clients(
    uri: str | None = None,
) -> tuple[RivaASR, RivaTTS]:
    """Create both ASR and TTS clients from environment or defaults."""
    uri = uri or os.getenv("RIVA_URI", "localhost:50051")
    cfg = RivaConfig(uri=uri)
    return RivaASR(cfg), RivaTTS(cfg)
