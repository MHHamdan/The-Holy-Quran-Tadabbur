"""STT provider implementations."""

from .base import STTProvider, STTResult, TranscriptionSegment
from .faster_whisper import FasterWhisperProvider

__all__ = [
    "STTProvider",
    "STTResult",
    "TranscriptionSegment",
    "FasterWhisperProvider",
]
