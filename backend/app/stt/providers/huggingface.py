"""
Speech-to-text via Hugging Face Inference Providers (Tasmeeʿ).

Default model: ``HF_STT_MODEL`` = ``openai/whisper-large-v3-turbo`` on the
``hf-inference`` provider, with word-level timestamps for alignment. Nothing
is loaded locally and no GPU is required.

Audio arrives as 16 kHz mono float32 (or 16-bit PCM bytes, or a file path);
it is wrapped in a WAV container and sent once per call. Streaming is
emulated by buffering windows, exactly like the previous local provider.
"""
from __future__ import annotations

import io
import logging
import time
import wave
from typing import Iterator, List, Optional, Union

import numpy as np

from app.ai.hf_client import HFErrorKind, HFInferenceError, classify_exception, hf_configured, task_client
from app.stt.providers.base import (
    STTProvider,
    STTResult,
    TranscriptionSegment,
    TranscriptionState,
    WordInfo,
)

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
# Whisper does not return per-word probabilities through the hosted pipeline.
DEFAULT_WORD_CONFIDENCE = 0.9


def pcm_to_wav_bytes(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Encode float32 [-1, 1] mono audio as a 16-bit PCM WAV file."""
    clipped = np.clip(audio.astype(np.float32), -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buf.getvalue()


class HuggingFaceSTTProvider(STTProvider):
    """Hosted Whisper transcription with word timestamps."""

    def __init__(
        self,
        model_size: str = "base",  # accepted for API compatibility; model comes from settings
        language: str = "ar",
        device: str = "auto",
        compute_type: str = "auto",
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        super().__init__(model_size=model_size, language=language, device=device, compute_type=compute_type)
        from app.core.config import settings

        self.model_id = model or settings.hf_stt_model
        self.timeout = timeout or max(settings.hf_timeout_seconds, 60.0)

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def supported_languages(self) -> List[str]:
        return ["ar", "en"]

    def load_model(self) -> None:
        """No local model. Fails fast when the server has no HF token."""
        if not hf_configured():
            raise HFInferenceError(HFErrorKind.NOT_CONFIGURED, "speech-to-text")
        self._is_loaded = True

    def unload_model(self) -> None:
        self._is_loaded = False

    def _to_wav(self, audio: Union[np.ndarray, bytes, str], sample_rate: int) -> Union[bytes, str]:
        if isinstance(audio, str):
            return audio  # file path; the client infers the content type
        if isinstance(audio, (bytes, bytearray)):
            audio = np.frombuffer(bytes(audio), dtype=np.int16).astype(np.float32) / 32768.0
        if not isinstance(audio, np.ndarray):
            raise ValueError(f"Unsupported audio type: {type(audio)}")
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return pcm_to_wav_bytes(audio, sample_rate)

    def _request(self, payload: Union[bytes, str], word_timestamps: bool):
        params = {"generate_kwargs": {"language": "arabic" if self.language == "ar" else self.language,
                                      "task": "transcribe"}}
        if word_timestamps:
            params["return_timestamps"] = "word"
        client = task_client("speech-to-text", timeout=self.timeout)
        try:
            return client.automatic_speech_recognition(payload, model=self.model_id, extra_body=params)
        except Exception as exc:  # noqa: BLE001
            raise classify_exception(exc, "speech-to-text") from None

    def transcribe(
        self,
        audio: Union[np.ndarray, bytes, str],
        sample_rate: int = SAMPLE_RATE,
        word_timestamps: bool = True,
    ) -> STTResult:
        if not self._is_loaded:
            self.load_model()

        start = time.time()
        duration = 0.0
        if isinstance(audio, np.ndarray):
            duration = len(audio) / float(sample_rate)
        elif isinstance(audio, (bytes, bytearray)):
            duration = len(audio) / 2 / float(sample_rate)

        output = self._request(self._to_wav(audio, sample_rate), word_timestamps)
        text = (getattr(output, "text", None) or "").strip()
        if not isinstance(text, str):
            raise HFInferenceError(HFErrorKind.MALFORMED, "speech-to-text")

        words: List[WordInfo] = []
        last_end = 0.0
        for chunk in getattr(output, "chunks", None) or []:
            word = (getattr(chunk, "text", "") or "").strip()
            if not word:
                continue
            ts = list(getattr(chunk, "timestamp", None) or [None, None]) + [None, None]
            begin = float(ts[0]) if ts[0] is not None else last_end
            end = float(ts[1]) if ts[1] is not None else max(begin, duration or begin)
            words.append(WordInfo(word=word, start_time=begin, end_time=end,
                                  confidence=DEFAULT_WORD_CONFIDENCE))
            last_end = end

        if word_timestamps and text and not words:
            # No timestamps returned: spread words evenly so alignment still works.
            tokens = text.split()
            step = (duration or len(tokens)) / max(len(tokens), 1)
            words = [WordInfo(word=t, start_time=i * step, end_time=(i + 1) * step,
                              confidence=DEFAULT_WORD_CONFIDENCE) for i, t in enumerate(tokens)]

        segments = []
        if text:
            segments.append(TranscriptionSegment(
                text=text,
                start_time=words[0].start_time if words else 0.0,
                end_time=words[-1].end_time if words else duration,
                words=words,
                state=TranscriptionState.FINAL,
                language=self.language,
                confidence=DEFAULT_WORD_CONFIDENCE,
            ))

        return STTResult(
            segments=segments,
            full_text=text,
            language=self.language,
            duration=duration,
            processing_time=time.time() - start,
            provider=self.name,
            model=self.model_id,
        )

    def transcribe_stream(
        self,
        audio_chunks: Iterator[np.ndarray],
        sample_rate: int = SAMPLE_RATE,
        chunk_duration: float = 2.0,
    ) -> Iterator[TranscriptionSegment]:
        """Buffer windows of ``chunk_duration`` seconds and transcribe each."""
        if not self._is_loaded:
            self.load_model()

        buffer: List[np.ndarray] = []
        buffered = 0
        offset = 0.0
        target = int(chunk_duration * sample_rate)

        def emit(audio: np.ndarray, state: TranscriptionState):
            result = self.transcribe(audio, sample_rate=sample_rate, word_timestamps=True)
            for seg in result.segments:
                yield TranscriptionSegment(
                    text=seg.text,
                    start_time=seg.start_time + offset,
                    end_time=seg.end_time + offset,
                    words=[WordInfo(word=w.word, start_time=w.start_time + offset,
                                    end_time=w.end_time + offset, confidence=w.confidence,
                                    normalized=w.normalized) for w in seg.words],
                    state=state,
                    language=seg.language,
                    confidence=seg.confidence,
                )

        for chunk in audio_chunks:
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32) / 32768.0
            buffer.append(chunk)
            buffered += len(chunk)
            if buffered >= target:
                audio = np.concatenate(buffer)
                yield from emit(audio, TranscriptionState.PARTIAL)
                offset += len(audio) / float(sample_rate)
                buffer, buffered = [], 0

        if buffer:
            audio = np.concatenate(buffer)
            if len(audio) > sample_rate * 0.5:
                yield from emit(audio, TranscriptionState.FINAL)
