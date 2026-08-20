"""
Voice layer for the TheLab agent on DGX Spark.

This package handles:
- Local NVIDIA NeMo / Riva ASR (STT) and TTS
- Audio I/O (microphone / speakers)
- Turn management and barge-in
- Bridging between audio and the LangGraph agent brain
"""

from .audio import AudioConfig, play_audio, record_until_silence
from .orchestrator import VoiceOrchestrator
from .riva import RivaASR, RivaConfig, RivaTTS, get_riva_clients

__all__ = [
    "AudioConfig",
    "play_audio",
    "record_until_silence",
    "VoiceOrchestrator",
    "RivaASR",
    "RivaConfig",
    "RivaTTS",
    "get_riva_clients",
]
