"""
Speech-to-Text (STT) module for Tasmeeʿ (Memorization) feature.

This module provides a pluggable STT architecture with provider abstraction.
Default provider: faster-whisper (MIT licensed, offline, free-forever)
Alternative: Vosk (Apache-2.0, offline)

License Justification:
- Whisper: MIT license (openai/whisper)
- faster-whisper: MIT license (SYSTRAN/faster-whisper)
- Vosk: Apache-2.0 (alphacep/vosk)

All providers are local/offline and cost-free per minute.
"""

from .providers.base import STTProvider, STTResult, TranscriptionSegment
from .providers.faster_whisper import FasterWhisperProvider

__all__ = [
    "STTProvider",
    "STTResult",
    "TranscriptionSegment",
    "FasterWhisperProvider",
    "get_stt_provider",
]


def get_stt_provider(provider_name: str = "faster-whisper", **kwargs) -> STTProvider:
    """
    Factory function to get an STT provider instance.

    Args:
        provider_name: Name of the provider ("faster-whisper" or "vosk")
        **kwargs: Provider-specific configuration

    Returns:
        An initialized STT provider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    providers = {
        "faster-whisper": FasterWhisperProvider,
        # "vosk": VoskProvider,  # Future implementation
    }

    if provider_name not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown STT provider: {provider_name}. "
            f"Available providers: {available}"
        )

    return providers[provider_name](**kwargs)
