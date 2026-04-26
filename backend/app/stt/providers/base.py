"""
Base STT Provider abstraction for Tasmeeʿ feature.

This module defines the interface that all STT providers must implement.
The abstraction allows swapping between faster-whisper and Vosk (or other
providers) without changing the consuming code.

Design Goals:
1. Provider-agnostic interface
2. Support for streaming/incremental transcription
3. Word-level timestamps for alignment
4. Confidence scores for mistake detection
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Iterator, List, Optional, Union
import numpy as np


class TranscriptionState(str, Enum):
    """State of a transcription segment."""

    PARTIAL = "partial"  # Interim result, may change
    FINAL = "final"  # Finalized, won't change


@dataclass
class WordInfo:
    """Information about a single transcribed word."""

    word: str
    start_time: float  # Seconds from audio start
    end_time: float  # Seconds from audio start
    confidence: float  # 0.0 to 1.0

    # Normalized form for matching (no diacritics, etc.)
    normalized: str = ""

    def __post_init__(self):
        if not self.normalized:
            self.normalized = self.word


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing and word info."""

    text: str
    start_time: float
    end_time: float
    words: List[WordInfo] = field(default_factory=list)
    state: TranscriptionState = TranscriptionState.FINAL
    language: str = "ar"
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        """Duration of this segment in seconds."""
        return self.end_time - self.start_time


@dataclass
class STTResult:
    """Complete result from an STT transcription."""

    segments: List[TranscriptionSegment]
    full_text: str
    language: str = "ar"
    duration: float = 0.0  # Total audio duration
    processing_time: float = 0.0  # Time taken to process

    # Provider metadata
    provider: str = ""
    model: str = ""

    @property
    def word_count(self) -> int:
        """Total number of words across all segments."""
        return sum(len(seg.words) for seg in self.segments)

    def get_all_words(self) -> List[WordInfo]:
        """Flatten all words from all segments."""
        words = []
        for seg in self.segments:
            words.extend(seg.words)
        return words


class STTProvider(ABC):
    """
    Abstract base class for Speech-to-Text providers.

    All STT providers must implement this interface to be compatible
    with the Tasmeeʿ (Memorization) feature.

    Implementations:
    - FasterWhisperProvider: Uses faster-whisper with CTranslate2 (MIT)
    - VoskProvider: Uses Vosk for offline recognition (Apache-2.0)
    """

    def __init__(
        self,
        model_size: str = "base",
        language: str = "ar",
        device: str = "auto",
        compute_type: str = "auto",
    ):
        """
        Initialize the STT provider.

        Args:
            model_size: Size of the model (tiny, base, small, medium, large)
            language: Target language code (default: "ar" for Arabic)
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Compute precision ("int8", "float16", "float32", "auto")
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """List of supported language codes."""
        pass

    @abstractmethod
    def load_model(self) -> None:
        """
        Load the STT model into memory.

        This should be called before transcription. Loading is separate
        from __init__ to allow lazy loading and resource management.
        """
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """
        Unload the model from memory.

        Use this to free up memory when the provider is not in use.
        """
        pass

    @abstractmethod
    def transcribe(
        self,
        audio: Union[np.ndarray, bytes, str],
        sample_rate: int = 16000,
        word_timestamps: bool = True,
    ) -> STTResult:
        """
        Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32), bytes, or file path
            sample_rate: Sample rate of the audio (default: 16kHz)
            word_timestamps: Whether to include word-level timestamps

        Returns:
            STTResult with transcription, timing, and word information
        """
        pass

    @abstractmethod
    def transcribe_stream(
        self,
        audio_chunks: Iterator[np.ndarray],
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
    ) -> Iterator[TranscriptionSegment]:
        """
        Transcribe audio in streaming mode.

        This method yields TranscriptionSegment objects as audio chunks
        are processed, enabling real-time transcription feedback.

        Args:
            audio_chunks: Iterator yielding audio chunks as numpy arrays
            sample_rate: Sample rate of the audio
            chunk_duration: Target duration of each chunk in seconds

        Yields:
            TranscriptionSegment objects (partial and final)
        """
        pass

    async def transcribe_stream_async(
        self,
        audio_chunks: AsyncIterator[np.ndarray],
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
    ) -> AsyncIterator[TranscriptionSegment]:
        """
        Async version of transcribe_stream.

        Default implementation wraps the sync version. Providers may
        override for true async support.

        Args:
            audio_chunks: Async iterator yielding audio chunks
            sample_rate: Sample rate of the audio
            chunk_duration: Target duration of each chunk

        Yields:
            TranscriptionSegment objects asynchronously
        """
        import asyncio

        buffer = []
        async for chunk in audio_chunks:
            buffer.append(chunk)
            # Yield from sync implementation
            for segment in self.transcribe_stream(
                iter([chunk]), sample_rate, chunk_duration
            ):
                yield segment
                await asyncio.sleep(0)  # Allow other tasks to run

    def __enter__(self):
        """Context manager entry - load model."""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - unload model."""
        self.unload_model()
        return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model_size={self.model_size!r}, "
            f"language={self.language!r}, "
            f"device={self.device!r})"
        )
