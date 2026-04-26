"""
Unit tests for Progressive Reveal feature in Tasmeeʿ.

Tests cover:
1. Pointer Advancement - tracking voice-driven position
2. Reveal Logic - auto, smart_tap, and hybrid modes
3. Audio Buffer - rolling window with overlap
4. Skip Detection - identifying jumps in recitation
"""

import numpy as np
import pytest

from app.stt.audio_buffer import RollingAudioBuffer, VADBuffer
from app.stt.alignment import (
    AlignmentResult,
    AlignmentState,
    MistakeType,
    RecitationAligner,
)
from app.stt.providers.base import TranscriptionSegment, WordInfo


class TestRollingAudioBuffer:
    """Tests for RollingAudioBuffer class."""

    def test_buffer_initialization(self):
        """Test buffer initializes with correct parameters."""
        buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )
        assert buffer.window_samples == 19200  # 1.2 * 16000
        assert buffer.step_samples == 6400  # 0.4 * 16000
        assert buffer.overlap_samples == 12800  # 19200 - 6400
        assert len(buffer.buffer) == 0
        assert buffer.total_samples == 0

    def test_buffer_accumulates_chunks(self):
        """Test buffer accumulates audio chunks."""
        buffer = RollingAudioBuffer()
        chunk = np.random.randn(1600).astype(np.float32)  # 100ms

        result = buffer.add_chunk(chunk)

        assert result is None  # Not enough data yet
        assert len(buffer.buffer) == 1600
        assert buffer.total_samples == 1600

    def test_buffer_returns_window_at_threshold(self):
        """Test buffer returns window when step threshold is reached."""
        buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )

        # Add exactly 1.2s of audio (19200 samples)
        chunk = np.random.randn(19200).astype(np.float32)
        result = buffer.add_chunk(chunk)

        assert result is not None
        assert len(result) == 19200  # Full window

    def test_buffer_maintains_overlap(self):
        """Test buffer keeps overlap after processing."""
        buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )

        # First window
        chunk1 = np.random.randn(19200).astype(np.float32)
        buffer.add_chunk(chunk1)

        # Buffer should keep overlap (12800 samples = 0.8s)
        assert len(buffer.buffer) == 12800

    def test_buffer_multiple_windows(self):
        """Test buffer produces multiple windows correctly."""
        buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )

        windows_received = 0

        # Add 3 seconds of audio in small chunks
        for _ in range(30):  # 30 * 100ms = 3s
            chunk = np.random.randn(1600).astype(np.float32)
            result = buffer.add_chunk(chunk)
            if result is not None:
                windows_received += 1

        # Should get roughly 5-6 windows (one at 1.2s, then every 0.4s)
        assert windows_received >= 4

    def test_buffer_reset(self):
        """Test buffer reset clears state."""
        buffer = RollingAudioBuffer()
        chunk = np.random.randn(1600).astype(np.float32)
        buffer.add_chunk(chunk)

        buffer.reset()

        assert len(buffer.buffer) == 0
        assert buffer.total_samples == 0
        assert buffer.last_process_pos == 0

    def test_buffer_get_remaining(self):
        """Test getting remaining samples from buffer."""
        buffer = RollingAudioBuffer()
        chunk = np.random.randn(1600).astype(np.float32)
        buffer.add_chunk(chunk)

        remaining = buffer.get_remaining()

        assert remaining is not None
        assert len(remaining) == 1600
        assert len(buffer.buffer) == 0

    def test_buffer_duration_properties(self):
        """Test buffer duration properties."""
        buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )

        assert buffer.window_duration == 1.2
        assert buffer.step_duration == 0.4

        chunk = np.random.randn(8000).astype(np.float32)  # 0.5s
        buffer.add_chunk(chunk)

        assert buffer.buffer_duration == 0.5
        assert buffer.total_duration == 0.5


class TestVADBuffer:
    """Tests for VAD-aware buffer."""

    def test_vad_detects_speech(self):
        """Test VAD detects speech in loud audio."""
        buffer = VADBuffer(vad_threshold=0.01)

        # Loud audio (speech-like)
        loud_chunk = np.random.randn(1600).astype(np.float32) * 0.5
        assert buffer._detect_speech(loud_chunk)

    def test_vad_detects_silence(self):
        """Test VAD detects silence in quiet audio."""
        buffer = VADBuffer(vad_threshold=0.01)

        # Very quiet audio (silence)
        quiet_chunk = np.random.randn(1600).astype(np.float32) * 0.001
        assert not buffer._detect_speech(quiet_chunk)

    def test_vad_skips_silence(self):
        """Test VAD buffer skips processing during silence."""
        buffer = VADBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
            vad_threshold=0.01,
        )

        # Add silent audio
        for _ in range(20):
            silent_chunk = np.random.randn(1600).astype(np.float32) * 0.0001
            result = buffer.add_chunk(silent_chunk)
            assert result is None  # Should not process silence


class TestPointerAdvancement:
    """Tests for alignment pointer tracking."""

    def test_pointer_starts_at_zero(self):
        """Test aligner starts at position 0."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")
        assert aligner.state.current_position == 0

    def test_pointer_advances_on_match(self):
        """Test pointer advances when word matches."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")

        # Create a segment with matching word
        segment = TranscriptionSegment(
            text="بسم",
            words=[WordInfo(word="بسم", start_time=0.0, end_time=0.5, confidence=0.9)],
            start_time=0.0,
            end_time=0.5,
            confidence=0.9,
        )

        result = aligner.process_segment(segment)

        assert result.position == 1  # Advanced to next word
        assert result.words_matched == 1

    def test_pointer_advances_multiple_words(self):
        """Test pointer advances for multiple matched words."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")

        segment = TranscriptionSegment(
            text="بسم الله",
            words=[
                WordInfo(word="بسم", start_time=0.0, end_time=0.3, confidence=0.9),
                WordInfo(word="الله", start_time=0.3, end_time=0.6, confidence=0.9),
            ],
            start_time=0.0,
            end_time=0.6,
            confidence=0.9,
        )

        result = aligner.process_segment(segment)

        assert result.position == 2
        assert result.words_matched == 2


class TestSkipDetection:
    """Tests for skip/jump detection in alignment."""

    def test_skip_detection_single_word(self):
        """Test skipping one word is detected but not marked as jump."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")

        # Skip first word, match second
        segment = TranscriptionSegment(
            text="الله",
            words=[WordInfo(word="الله", start_time=0.0, end_time=0.5, confidence=0.9)],
            start_time=0.0,
            end_time=0.5,
            confidence=0.9,
        )

        result = aligner.process_segment(segment)

        assert result.position == 2  # Jumped to after "الله"
        assert len(result.mistakes) == 1  # Deletion for "بسم"
        assert result.mistakes[0].type == MistakeType.DELETION
        assert not result.had_jump  # Single skip is not a "jump"

    def test_skip_detection_creates_deletions(self):
        """Test skipping 2+ words is marked as jump with deletions."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")

        # Skip first two words, match third
        segment = TranscriptionSegment(
            text="الرحمن",
            words=[WordInfo(word="الرحمن", start_time=0.0, end_time=0.5, confidence=0.9)],
            start_time=0.0,
            end_time=0.5,
            confidence=0.9,
        )

        result = aligner.process_segment(segment)

        assert result.position == 3  # Jumped to after "الرحمن"
        assert len(result.mistakes) == 2  # Deletions for "بسم" and "الله"
        assert result.had_jump  # 2+ words = jump
        assert len(result.skipped_positions) == 2
        assert 0 in result.skipped_positions
        assert 1 in result.skipped_positions

    def test_skip_detection_positions(self):
        """Test skipped positions are correctly tracked."""
        aligner = RecitationAligner("بسم الله الرحمن الرحيم")

        # Match first word
        segment1 = TranscriptionSegment(
            text="بسم",
            words=[WordInfo(word="بسم", start_time=0.0, end_time=0.3, confidence=0.9)],
            start_time=0.0,
            end_time=0.3,
            confidence=0.9,
        )
        aligner.process_segment(segment1)

        # Skip "الله" and "الرحمن", match "الرحيم"
        segment2 = TranscriptionSegment(
            text="الرحيم",
            words=[WordInfo(word="الرحيم", start_time=0.5, end_time=0.8, confidence=0.9)],
            start_time=0.5,
            end_time=0.8,
            confidence=0.9,
        )
        result = aligner.process_segment(segment2)

        assert result.had_jump
        assert result.skipped_positions == [1, 2]  # "الله" and "الرحمن"


class TestRevealLogic:
    """Tests for reveal mode logic (simulated frontend behavior)."""

    def simulate_reveal(
        self,
        mode: str,
        pointer: int,
        revealed_up_to: int,
        total_words: int,
        hybrid_threshold: float = 0.7,
    ) -> int:
        """Simulate reveal logic from frontend."""
        progress = pointer / total_words if total_words > 0 else 1.0

        if mode == "auto":
            return max(revealed_up_to, pointer)
        elif mode == "hybrid":
            if progress < hybrid_threshold:
                return max(revealed_up_to, pointer)
            return revealed_up_to
        else:  # smart_tap
            return revealed_up_to

    def test_auto_reveal_follows_pointer(self):
        """Test auto mode reveals all words up to pointer."""
        new_revealed = self.simulate_reveal(
            mode="auto",
            pointer=5,
            revealed_up_to=2,
            total_words=10,
        )
        assert new_revealed == 5

    def test_tap_reveal_does_not_auto_advance(self):
        """Test smart_tap mode doesn't auto-reveal."""
        new_revealed = self.simulate_reveal(
            mode="smart_tap",
            pointer=5,
            revealed_up_to=2,
            total_words=10,
        )
        assert new_revealed == 2  # Unchanged

    def test_tap_reveal_increments_by_count(self):
        """Test tap reveal increments by specified count."""
        revealed_up_to = 2
        tap_count = 3
        total_words = 10

        # Simulate tap reveal
        new_revealed = min(revealed_up_to + tap_count, total_words)
        assert new_revealed == 5

    def test_hybrid_auto_before_threshold(self):
        """Test hybrid mode auto-reveals before threshold."""
        new_revealed = self.simulate_reveal(
            mode="hybrid",
            pointer=5,
            revealed_up_to=2,
            total_words=10,
            hybrid_threshold=0.7,
        )
        # 5/10 = 50% < 70% threshold, should auto-reveal
        assert new_revealed == 5

    def test_hybrid_switches_at_threshold(self):
        """Test hybrid mode stops auto-reveal at threshold."""
        new_revealed = self.simulate_reveal(
            mode="hybrid",
            pointer=8,
            revealed_up_to=5,
            total_words=10,
            hybrid_threshold=0.7,
        )
        # 8/10 = 80% >= 70% threshold, should not auto-reveal
        assert new_revealed == 5


class TestAlignmentState:
    """Tests for AlignmentState properties."""

    def test_progress_calculation(self):
        """Test progress is calculated correctly."""
        from app.stt.arabic_normalizer import tokenize_with_positions

        words = tokenize_with_positions("بسم الله الرحمن الرحيم")
        state = AlignmentState(expected_words=words)
        state.current_position = 2

        assert state.progress == 0.5  # 2/4

    def test_is_complete(self):
        """Test completion detection."""
        from app.stt.arabic_normalizer import tokenize_with_positions

        words = tokenize_with_positions("بسم الله")
        state = AlignmentState(expected_words=words)

        assert not state.is_complete
        state.current_position = 2
        assert state.is_complete

    def test_current_word(self):
        """Test current word tracking."""
        from app.stt.arabic_normalizer import tokenize_with_positions

        words = tokenize_with_positions("بسم الله الرحمن")
        state = AlignmentState(expected_words=words)

        assert state.current_word.original == "بسم"
        state.current_position = 1
        assert state.current_word.original == "الله"
        state.current_position = 3
        assert state.current_word is None  # Past end

    def test_get_window(self):
        """Test lookahead window retrieval."""
        from app.stt.arabic_normalizer import tokenize_with_positions

        words = tokenize_with_positions("بسم الله الرحمن الرحيم")
        state = AlignmentState(expected_words=words)

        window = state.get_window(size=3)
        assert len(window) == 3
        assert window[0].original == "بسم"
        assert window[1].original == "الله"
        assert window[2].original == "الرحمن"

        state.current_position = 2
        window = state.get_window(size=5)
        assert len(window) == 2  # Only 2 words remaining
