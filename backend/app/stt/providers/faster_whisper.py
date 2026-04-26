"""
Faster-Whisper STT Provider for Tasmeeʿ (Memorization) feature.

This provider uses faster-whisper (SYSTRAN/faster-whisper), which is a
CTranslate2-based reimplementation of OpenAI's Whisper model.

License: MIT (both faster-whisper and original Whisper)
Repository: https://github.com/SYSTRAN/faster-whisper

Key Features:
- 4x faster than original Whisper with similar accuracy
- CTranslate2 optimizations for CPU and GPU
- Word-level timestamps via cross-attention
- Low memory footprint
- Fully offline, no API costs

Audio Requirements:
- 16kHz mono PCM (will auto-resample if needed)
- Supported formats: numpy array, bytes, file path
"""

import logging
import time
from typing import Iterator, List, Optional, Tuple, Union

import numpy as np

from .base import (
    STTProvider,
    STTResult,
    TranscriptionSegment,
    TranscriptionState,
    WordInfo,
)

logger = logging.getLogger(__name__)


class FasterWhisperProvider(STTProvider):
    """
    Faster-Whisper based STT provider.

    This is the default and recommended provider for Tasmeeʿ due to:
    1. Free forever (MIT license, local processing)
    2. High accuracy for Arabic
    3. Word-level timestamps for alignment
    4. Streaming-like behavior with chunk processing
    """

    # Supported model sizes with approximate VRAM/RAM requirements
    MODEL_SIZES = {
        "tiny": {"params": "39M", "vram_fp16": "~1GB", "vram_int8": "~0.5GB"},
        "base": {"params": "74M", "vram_fp16": "~1GB", "vram_int8": "~0.5GB"},
        "small": {"params": "244M", "vram_fp16": "~2GB", "vram_int8": "~1GB"},
        "medium": {"params": "769M", "vram_fp16": "~5GB", "vram_int8": "~2.5GB"},
        "large-v2": {"params": "1.5B", "vram_fp16": "~10GB", "vram_int8": "~5GB"},
        "large-v3": {"params": "1.5B", "vram_fp16": "~10GB", "vram_int8": "~5GB"},
    }

    def __init__(
        self,
        model_size: str = "base",
        language: str = "ar",
        device: str = "auto",
        compute_type: str = "auto",
        download_root: Optional[str] = None,
        local_files_only: bool = False,
        vad_filter: bool = True,
        vad_parameters: Optional[dict] = None,
    ):
        """
        Initialize the Faster-Whisper provider.

        Args:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
            language: Target language code (default: "ar" for Arabic)
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Precision ("int8", "float16", "float32", "auto")
            download_root: Custom directory for model cache
            local_files_only: If True, only use locally cached models
            vad_filter: Enable Voice Activity Detection to skip silence
            vad_parameters: Custom VAD parameters (threshold, min_silence_duration_ms, etc.)
        """
        super().__init__(model_size, language, device, compute_type)

        self.download_root = download_root
        self.local_files_only = local_files_only
        self.vad_filter = vad_filter
        self.vad_parameters = vad_parameters or {
            "threshold": 0.5,
            "min_silence_duration_ms": 500,
            "min_speech_duration_ms": 250,
            "speech_pad_ms": 400,
        }

        # Streaming state
        self._audio_buffer: List[np.ndarray] = []
        self._buffer_duration: float = 0.0
        self._last_transcript: str = ""

    @property
    def name(self) -> str:
        return "faster-whisper"

    @property
    def supported_languages(self) -> List[str]:
        """Whisper supports 99 languages. Key ones for Quran memorization:"""
        return ["ar", "en", "ur", "fa", "tr", "id", "ms", "bn"]

    def _detect_device(self) -> Tuple[str, str]:
        """Auto-detect best device and compute type."""
        device = self.device
        compute_type = self.compute_type

        if device == "auto":
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if compute_type == "auto":
            if device == "cuda":
                compute_type = "float16"  # Best for GPU
            else:
                compute_type = "int8"  # Best for CPU

        return device, compute_type

    def load_model(self) -> None:
        """Load the Faster-Whisper model."""
        if self._is_loaded:
            logger.debug("Model already loaded")
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper"
            ) from e

        device, compute_type = self._detect_device()
        logger.info(
            f"Loading Faster-Whisper model: {self.model_size} "
            f"(device={device}, compute_type={compute_type})"
        )

        start_time = time.time()

        self._model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
            download_root=self.download_root,
            local_files_only=self.local_files_only,
        )

        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f}s")
        self._is_loaded = True

    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._is_loaded = False

            # Try to free GPU memory
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("Model unloaded")

    def _prepare_audio(
        self, audio: Union[np.ndarray, bytes, str], sample_rate: int
    ) -> np.ndarray:
        """
        Prepare audio for transcription.

        Converts various input formats to 16kHz mono float32 numpy array.
        """
        if isinstance(audio, str):
            # File path - let faster-whisper handle it
            return audio

        if isinstance(audio, bytes):
            # Raw PCM bytes (16-bit signed integers)
            audio = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

        if not isinstance(audio, np.ndarray):
            raise ValueError(f"Unsupported audio type: {type(audio)}")

        # Ensure float32
        if audio.dtype != np.float32:
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            else:
                audio = audio.astype(np.float32)

        # Ensure mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample if needed (faster-whisper expects 16kHz)
        if sample_rate != 16000:
            try:
                import librosa

                audio = librosa.resample(
                    audio, orig_sr=sample_rate, target_sr=16000
                )
            except ImportError:
                # Simple resampling fallback
                factor = 16000 / sample_rate
                indices = np.arange(0, len(audio), 1 / factor).astype(int)
                indices = indices[indices < len(audio)]
                audio = audio[indices]

        return audio

    def transcribe(
        self,
        audio: Union[np.ndarray, bytes, str],
        sample_rate: int = 16000,
        word_timestamps: bool = True,
    ) -> STTResult:
        """
        Transcribe audio to text with word-level timestamps.

        Args:
            audio: Audio data (numpy array, bytes, or file path)
            sample_rate: Sample rate (default 16kHz)
            word_timestamps: Include word-level timing (default True)

        Returns:
            STTResult with full transcription and word information
        """
        if not self._is_loaded:
            self.load_model()

        start_time = time.time()

        # Prepare audio
        prepared_audio = self._prepare_audio(audio, sample_rate)

        # Calculate duration
        if isinstance(prepared_audio, np.ndarray):
            duration = len(prepared_audio) / 16000
        else:
            # For file paths, duration will be calculated by faster-whisper
            duration = 0.0

        # Transcribe
        segments_iter, info = self._model.transcribe(
            prepared_audio,
            language=self.language,
            task="transcribe",
            word_timestamps=word_timestamps,
            vad_filter=self.vad_filter,
            vad_parameters=self.vad_parameters if self.vad_filter else None,
            beam_size=5,
            best_of=5,
            temperature=0.0,  # Deterministic for consistent results
        )

        # Collect segments
        segments: List[TranscriptionSegment] = []
        full_text_parts: List[str] = []

        for seg in segments_iter:
            words: List[WordInfo] = []

            if word_timestamps and seg.words:
                for w in seg.words:
                    words.append(
                        WordInfo(
                            word=w.word.strip(),
                            start_time=w.start,
                            end_time=w.end,
                            confidence=w.probability if hasattr(w, "probability") else 0.9,
                        )
                    )

            segment = TranscriptionSegment(
                text=seg.text.strip(),
                start_time=seg.start,
                end_time=seg.end,
                words=words,
                state=TranscriptionState.FINAL,
                language=self.language,
                confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else 0.0,
            )
            segments.append(segment)
            full_text_parts.append(seg.text.strip())

        processing_time = time.time() - start_time

        return STTResult(
            segments=segments,
            full_text=" ".join(full_text_parts),
            language=info.language if hasattr(info, "language") else self.language,
            duration=info.duration if hasattr(info, "duration") else duration,
            processing_time=processing_time,
            provider=self.name,
            model=self.model_size,
        )

    def transcribe_stream(
        self,
        audio_chunks: Iterator[np.ndarray],
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
    ) -> Iterator[TranscriptionSegment]:
        """
        Transcribe audio in streaming mode with incremental results.

        This simulates streaming by:
        1. Buffering audio chunks until we have enough data
        2. Transcribing the buffer
        3. Yielding partial results frequently
        4. Finalizing segments when we're confident

        Args:
            audio_chunks: Iterator yielding audio chunks
            sample_rate: Sample rate of the audio
            chunk_duration: Target buffer duration before transcribing

        Yields:
            TranscriptionSegment objects (partial and final)
        """
        if not self._is_loaded:
            self.load_model()

        buffer: List[np.ndarray] = []
        buffer_samples = 0
        target_samples = int(chunk_duration * sample_rate)
        last_text = ""
        cumulative_offset = 0.0

        for chunk in audio_chunks:
            # Prepare chunk
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32) / 32768.0

            buffer.append(chunk)
            buffer_samples += len(chunk)

            # Process when we have enough data
            if buffer_samples >= target_samples:
                # Concatenate buffer
                audio = np.concatenate(buffer)

                # Transcribe
                result = self.transcribe(
                    audio, sample_rate=sample_rate, word_timestamps=True
                )

                # Yield segments with adjusted timing
                for seg in result.segments:
                    # Check if this is new content
                    if seg.text != last_text:
                        # Adjust timestamps for cumulative offset
                        adjusted_seg = TranscriptionSegment(
                            text=seg.text,
                            start_time=seg.start_time + cumulative_offset,
                            end_time=seg.end_time + cumulative_offset,
                            words=[
                                WordInfo(
                                    word=w.word,
                                    start_time=w.start_time + cumulative_offset,
                                    end_time=w.end_time + cumulative_offset,
                                    confidence=w.confidence,
                                    normalized=w.normalized,
                                )
                                for w in seg.words
                            ],
                            state=TranscriptionState.PARTIAL,
                            language=seg.language,
                            confidence=seg.confidence,
                        )
                        yield adjusted_seg
                        last_text = seg.text

                # Keep last second of audio for continuity
                keep_samples = int(sample_rate)
                if len(audio) > keep_samples:
                    buffer = [audio[-keep_samples:]]
                    buffer_samples = keep_samples
                    cumulative_offset += (len(audio) - keep_samples) / sample_rate
                else:
                    buffer = []
                    buffer_samples = 0

        # Process remaining buffer
        if buffer:
            audio = np.concatenate(buffer)
            if len(audio) > sample_rate * 0.5:  # At least 0.5s
                result = self.transcribe(
                    audio, sample_rate=sample_rate, word_timestamps=True
                )

                for seg in result.segments:
                    yield TranscriptionSegment(
                        text=seg.text,
                        start_time=seg.start_time + cumulative_offset,
                        end_time=seg.end_time + cumulative_offset,
                        words=[
                            WordInfo(
                                word=w.word,
                                start_time=w.start_time + cumulative_offset,
                                end_time=w.end_time + cumulative_offset,
                                confidence=w.confidence,
                                normalized=w.normalized,
                            )
                            for w in seg.words
                        ],
                        state=TranscriptionState.FINAL,
                        language=seg.language,
                        confidence=seg.confidence,
                    )

    def transcribe_incremental(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        context: Optional[str] = None,
    ) -> TranscriptionSegment:
        """
        Transcribe a single audio chunk with optional context.

        This is useful for real-time scenarios where you want to transcribe
        small chunks incrementally.

        Args:
            audio: Audio chunk as numpy array
            sample_rate: Sample rate
            context: Previous transcription text for context

        Returns:
            Single TranscriptionSegment
        """
        if not self._is_loaded:
            self.load_model()

        # Prepare audio
        audio = self._prepare_audio(audio, sample_rate)

        # Transcribe with initial prompt for context
        segments_iter, info = self._model.transcribe(
            audio,
            language=self.language,
            word_timestamps=True,
            vad_filter=False,  # Don't filter short chunks
            initial_prompt=context,
            beam_size=3,  # Faster for incremental
            temperature=0.0,
        )

        # Get first segment
        segments = list(segments_iter)
        if not segments:
            return TranscriptionSegment(
                text="",
                start_time=0.0,
                end_time=len(audio) / 16000,
                words=[],
                state=TranscriptionState.PARTIAL,
                language=self.language,
                confidence=0.0,
            )

        seg = segments[0]
        words = []
        if seg.words:
            for w in seg.words:
                words.append(
                    WordInfo(
                        word=w.word.strip(),
                        start_time=w.start,
                        end_time=w.end,
                        confidence=w.probability if hasattr(w, "probability") else 0.9,
                    )
                )

        return TranscriptionSegment(
            text=seg.text.strip(),
            start_time=seg.start,
            end_time=seg.end,
            words=words,
            state=TranscriptionState.PARTIAL,
            language=self.language,
            confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else 0.0,
        )
