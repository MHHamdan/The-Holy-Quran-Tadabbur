"""
Rolling Audio Buffer for Low-Latency Streaming.

This module provides a rolling window buffer for processing audio in
real-time with minimal latency. It's designed for use with the Tasmeeʿ
feature to enable progressive word reveal as the user recites.

Key Features:
- 1.2s window (19200 samples at 16kHz)
- 0.4s step (6400 samples) - process every 400ms
- 0.8s overlap - ensures word boundaries aren't missed
"""

from typing import Optional

import numpy as np


class RollingAudioBuffer:
    """
    Rolling window buffer for low-latency streaming audio processing.

    This buffer accumulates audio samples and returns windows ready for
    transcription at regular intervals, maintaining overlap between windows
    to ensure word boundaries are captured correctly.

    Example usage:
        buffer = RollingAudioBuffer(window_duration=1.2, step_duration=0.4)
        for chunk in audio_stream:
            window = buffer.add_chunk(chunk)
            if window is not None:
                transcription = stt.transcribe(window)
    """

    def __init__(
        self,
        window_duration: float = 1.2,
        step_duration: float = 0.4,
        sample_rate: int = 16000,
    ):
        """
        Initialize the rolling audio buffer.

        Args:
            window_duration: Duration of each processing window in seconds.
                Default 1.2s provides enough context for word boundaries.
            step_duration: Time between processing windows in seconds.
                Default 0.4s means we process every 400ms for low latency.
            sample_rate: Audio sample rate in Hz. Default 16kHz is standard
                for speech recognition.
        """
        self.sample_rate = sample_rate
        self.window_samples = int(window_duration * sample_rate)  # 19200
        self.step_samples = int(step_duration * sample_rate)  # 6400
        self.overlap_samples = self.window_samples - self.step_samples  # 12800

        # Internal state
        self.buffer = np.array([], dtype=np.float32)
        self.total_samples = 0
        self.last_process_pos = 0

    def add_chunk(self, chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        Add an audio chunk to the buffer.

        Returns a window array if enough samples have accumulated since
        the last processing, otherwise returns None.

        Args:
            chunk: Audio samples as float32 array (range -1.0 to 1.0)

        Returns:
            Window array ready for transcription, or None if not ready
        """
        # Ensure correct dtype
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)

        # Accumulate samples
        self.buffer = np.concatenate([self.buffer, chunk])
        self.total_samples += len(chunk)

        # Check if we have enough samples since last processing
        samples_since_last = self.total_samples - self.last_process_pos

        if samples_since_last >= self.step_samples and len(self.buffer) >= self.window_samples:
            # Extract window (last window_samples from buffer)
            window = self.buffer[-self.window_samples:]

            # Keep only overlap portion for next window
            self.buffer = self.buffer[-self.overlap_samples:]
            self.last_process_pos = self.total_samples

            return window

        return None

    def get_remaining(self) -> Optional[np.ndarray]:
        """
        Get any remaining audio in the buffer.

        Call this when the audio stream ends to process final samples.

        Returns:
            Remaining audio samples, or None if buffer is empty
        """
        if len(self.buffer) > 0:
            remaining = self.buffer.copy()
            self.buffer = np.array([], dtype=np.float32)
            return remaining
        return None

    def reset(self) -> None:
        """
        Reset the buffer state.

        Call this when starting a new audio stream.
        """
        self.buffer = np.array([], dtype=np.float32)
        self.total_samples = 0
        self.last_process_pos = 0

    @property
    def buffer_duration(self) -> float:
        """Get current buffer duration in seconds."""
        return len(self.buffer) / self.sample_rate

    @property
    def total_duration(self) -> float:
        """Get total audio duration received in seconds."""
        return self.total_samples / self.sample_rate

    @property
    def window_duration(self) -> float:
        """Get configured window duration in seconds."""
        return self.window_samples / self.sample_rate

    @property
    def step_duration(self) -> float:
        """Get configured step duration in seconds."""
        return self.step_samples / self.sample_rate


class VADBuffer(RollingAudioBuffer):
    """
    Voice Activity Detection aware rolling buffer.

    Extends RollingAudioBuffer to skip processing during silence,
    reducing CPU usage and preventing false transcriptions.
    """

    def __init__(
        self,
        window_duration: float = 1.2,
        step_duration: float = 0.4,
        sample_rate: int = 16000,
        vad_threshold: float = 0.01,
        min_speech_duration: float = 0.1,
    ):
        """
        Initialize the VAD-aware buffer.

        Args:
            vad_threshold: RMS threshold for speech detection (0.0-1.0)
            min_speech_duration: Minimum speech duration in seconds
        """
        super().__init__(window_duration, step_duration, sample_rate)
        self.vad_threshold = vad_threshold
        self.min_speech_samples = int(min_speech_duration * sample_rate)
        self.speech_samples = 0
        self.is_speaking = False

    def _detect_speech(self, chunk: np.ndarray) -> bool:
        """
        Detect if chunk contains speech using RMS energy.

        Args:
            chunk: Audio samples

        Returns:
            True if speech is detected
        """
        if len(chunk) == 0:
            return False

        # Calculate RMS energy
        rms = np.sqrt(np.mean(chunk**2))
        return rms > self.vad_threshold

    def add_chunk(self, chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        Add an audio chunk with VAD filtering.

        Only returns windows during detected speech.

        Args:
            chunk: Audio samples as float32 array

        Returns:
            Window array if speech detected and ready, otherwise None
        """
        # Check for speech in this chunk
        has_speech = self._detect_speech(chunk)

        if has_speech:
            self.speech_samples += len(chunk)
            if self.speech_samples >= self.min_speech_samples:
                self.is_speaking = True
        else:
            # Decay speech counter during silence
            self.speech_samples = max(0, self.speech_samples - len(chunk) // 2)
            if self.speech_samples == 0:
                self.is_speaking = False

        # Only process if speaking
        if self.is_speaking:
            return super().add_chunk(chunk)
        else:
            # Still accumulate for continuity, but don't process
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32)
            self.buffer = np.concatenate([self.buffer, chunk])
            self.total_samples += len(chunk)

            # Limit buffer size during silence
            max_buffer = self.window_samples * 2
            if len(self.buffer) > max_buffer:
                self.buffer = self.buffer[-self.overlap_samples:]

            return None

    def reset(self) -> None:
        """Reset buffer and VAD state."""
        super().reset()
        self.speech_samples = 0
        self.is_speaking = False
