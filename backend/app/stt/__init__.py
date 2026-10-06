"""
Speech-to-Text (STT) module for Tasmeeʿ (Memorization) feature.

Pluggable STT architecture with a provider abstraction.

Default provider: ``huggingface`` — Whisper hosted on Hugging Face Inference
Providers (``HF_STT_MODEL``). No GPU or local model files are required.

Optional: ``faster-whisper`` — local CPU/GPU inference, only for self-hosters
who install the ``stt-local`` extra (``pip install -e ".[stt-local]"``).
"""

from .providers.base import STTProvider, STTResult, TranscriptionSegment
from .providers.huggingface import HuggingFaceSTTProvider

__all__ = [
    "STTProvider",
    "STTResult",
    "TranscriptionSegment",
    "HuggingFaceSTTProvider",
    "get_stt_provider",
]


def get_stt_provider(provider_name: str = None, **kwargs) -> STTProvider:
    """
    Factory function to get an STT provider instance.

    Args:
        provider_name: "huggingface" (default, from STT_PROVIDER) or "faster-whisper"
        **kwargs: Provider-specific configuration

    Raises:
        ValueError: If provider_name is not supported
    """
    if provider_name is None:
        from app.core.config import settings
        provider_name = settings.stt_provider

    if provider_name == "huggingface":
        return HuggingFaceSTTProvider(**kwargs)
    if provider_name == "faster-whisper":
        # Imported lazily: only available with the optional stt-local extra.
        from .providers.faster_whisper import FasterWhisperProvider
        return FasterWhisperProvider(**kwargs)

    raise ValueError(
        f"Unknown STT provider: {provider_name}. "
        "Available providers: huggingface, faster-whisper"
    )
