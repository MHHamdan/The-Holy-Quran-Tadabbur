"""STT provider implementations."""

from .base import STTProvider, STTResult, TranscriptionSegment
from .huggingface import HuggingFaceSTTProvider

__all__ = [
    "STTProvider",
    "STTResult",
    "TranscriptionSegment",
    "HuggingFaceSTTProvider",
]
