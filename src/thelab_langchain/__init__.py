"""thelab-langchain: LangChain + Supermemory integration with Grok (xAI) or Anthropic.

Includes a voice layer for NVIDIA NeMo / Riva on DGX Spark.
"""

from .agent.graph import get_agent
from .chat import MemoryChat, MemoryContext
from .config import Settings, settings


# Voice components are optional (require audio runtime libs like libportaudio2).
# They are imported on demand via `from thelab_langchain.voice import ...`
# or when the `thelab-chat voice` subcommand is used.
def __getattr__(name: str):
    if name == "VoiceOrchestrator":
        from .voice import VoiceOrchestrator as _VoiceOrchestrator
        return _VoiceOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "MemoryChat",
    "MemoryContext",
    "Settings",
    "settings",
    "VoiceOrchestrator",
    "get_agent",
]
__version__ = "0.1.0"
