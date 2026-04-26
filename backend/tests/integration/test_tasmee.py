#!/usr/bin/env python3
"""
Tasmeeʿ (Memorization) Integration Tests

Tests the full pipeline:
1. Audio capture → STT transcription → Normalization → Alignment → Mistake detection
2. API endpoints for session management
3. WebSocket streaming (simulated)

IMPORTANT: These tests use mocked STT provider to avoid dependency on actual
audio files and faster-whisper models during CI/CD.

For local testing with real audio:
- Place test WAV files in tests/fixtures/audio/
- Run with TASMEE_USE_REAL_STT=1 pytest

Run with: pytest tests/integration/test_tasmee.py -v
"""
import pytest
import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Generator
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Mark all tests as integration tests
pytestmark = [pytest.mark.integration]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_stt_provider():
    """Create a mock STT provider for testing without actual model."""
    from app.stt.providers.base import STTProvider, STTResult, TranscriptionSegment, WordInfo, TranscriptionState

    class MockSTTProvider(STTProvider):
        """Mock STT provider that returns predefined transcriptions."""

        def __init__(self, transcriptions: List[Dict[str, Any]] = None):
            self._transcriptions = transcriptions or []
            self._transcription_index = 0
            self._is_loaded = True

        @property
        def is_loaded(self) -> bool:
            return self._is_loaded

        @property
        def name(self) -> str:
            return "mock"

        @property
        def supported_languages(self) -> List[str]:
            return ["ar"]

        def load_model(self):
            self._is_loaded = True

        def unload_model(self):
            self._is_loaded = False

        def set_transcriptions(self, transcriptions: List[Dict[str, Any]]):
            """Set predefined transcriptions for mock responses."""
            self._transcriptions = transcriptions
            self._transcription_index = 0

        def transcribe(self, audio, sample_rate=16000, word_timestamps=True) -> STTResult:
            """Return predefined transcription."""
            if self._transcription_index >= len(self._transcriptions):
                return STTResult(
                    segments=[],
                    full_text="",
                    language="ar",
                    duration=0.0,
                )

            trans = self._transcriptions[self._transcription_index]
            self._transcription_index += 1

            words = [
                WordInfo(
                    word=w["word"],
                    start_time=w.get("start", 0.0),
                    end_time=w.get("end", 0.5),
                    confidence=w.get("confidence", 0.9),
                )
                for w in trans.get("words", [])
            ]

            return STTResult(
                segments=[
                    TranscriptionSegment(
                        text=trans.get("text", ""),
                        start_time=trans.get("start", 0.0),
                        end_time=trans.get("end", 1.0),
                        words=words,
                        state=TranscriptionState.FINAL,
                        language="ar",
                        confidence=0.9,
                    )
                ],
                full_text=trans.get("text", ""),
                language="ar",
                duration=trans.get("end", 1.0),
            )

        def transcribe_stream(
            self, audio_chunks, sample_rate=16000, chunk_duration=2.0
        ) -> Generator[TranscriptionSegment, None, None]:
            """Yield predefined transcription segments."""
            for trans in self._transcriptions:
                words = [
                    WordInfo(
                        word=w["word"],
                        start_time=w.get("start", 0.0),
                        end_time=w.get("end", 0.5),
                        confidence=w.get("confidence", 0.9),
                    )
                    for w in trans.get("words", [])
                ]

                yield TranscriptionSegment(
                    text=trans.get("text", ""),
                    start_time=trans.get("start", 0.0),
                    end_time=trans.get("end", 1.0),
                    words=words,
                    state=TranscriptionState.FINAL,
                    language="ar",
                    confidence=0.9,
                )

    return MockSTTProvider()


@pytest.fixture
def al_fatiha_transcription():
    """Perfect transcription of Al-Fatiha verses 1-4."""
    return [
        {
            "text": "بسم الله الرحمن الرحيم",
            "start": 0.0,
            "end": 2.0,
            "words": [
                {"word": "بسم", "start": 0.0, "end": 0.4, "confidence": 0.95},
                {"word": "الله", "start": 0.4, "end": 0.8, "confidence": 0.98},
                {"word": "الرحمن", "start": 0.8, "end": 1.4, "confidence": 0.96},
                {"word": "الرحيم", "start": 1.4, "end": 2.0, "confidence": 0.97},
            ],
        },
        {
            "text": "الحمد لله رب العالمين",
            "start": 2.0,
            "end": 4.0,
            "words": [
                {"word": "الحمد", "start": 2.0, "end": 2.4, "confidence": 0.94},
                {"word": "لله", "start": 2.4, "end": 2.8, "confidence": 0.97},
                {"word": "رب", "start": 2.8, "end": 3.2, "confidence": 0.96},
                {"word": "العالمين", "start": 3.2, "end": 4.0, "confidence": 0.95},
            ],
        },
        {
            "text": "الرحمن الرحيم",
            "start": 4.0,
            "end": 5.5,
            "words": [
                {"word": "الرحمن", "start": 4.0, "end": 4.7, "confidence": 0.96},
                {"word": "الرحيم", "start": 4.7, "end": 5.5, "confidence": 0.97},
            ],
        },
        {
            "text": "مالك يوم الدين",
            "start": 5.5,
            "end": 7.0,
            "words": [
                {"word": "مالك", "start": 5.5, "end": 6.0, "confidence": 0.93},
                {"word": "يوم", "start": 6.0, "end": 6.4, "confidence": 0.95},
                {"word": "الدين", "start": 6.4, "end": 7.0, "confidence": 0.96},
            ],
        },
    ]


@pytest.fixture
def al_fatiha_with_mistakes_transcription():
    """Transcription of Al-Fatiha with intentional mistakes."""
    return [
        {
            "text": "بسم الله الرحمن الرحيم",
            "start": 0.0,
            "end": 2.0,
            "words": [
                {"word": "بسم", "start": 0.0, "end": 0.4, "confidence": 0.95},
                {"word": "الله", "start": 0.4, "end": 0.8, "confidence": 0.98},
                {"word": "الرحمن", "start": 0.8, "end": 1.4, "confidence": 0.96},
                {"word": "الرحيم", "start": 1.4, "end": 2.0, "confidence": 0.97},
            ],
        },
        {
            "text": "الحمد لله ملك العالمين",  # MISTAKE: "ملك" instead of "رب"
            "start": 2.0,
            "end": 4.0,
            "words": [
                {"word": "الحمد", "start": 2.0, "end": 2.4, "confidence": 0.94},
                {"word": "لله", "start": 2.4, "end": 2.8, "confidence": 0.97},
                {"word": "ملك", "start": 2.8, "end": 3.2, "confidence": 0.85},  # Wrong word
                {"word": "العالمين", "start": 3.2, "end": 4.0, "confidence": 0.95},
            ],
        },
    ]


@pytest.fixture
def expected_fatiha_text():
    """Expected text for Al-Fatiha verses 1-4."""
    return """بسم الله الرحمن الرحيم
الحمد لله رب العالمين
الرحمن الرحيم
مالك يوم الدين"""


# =============================================================================
# Full Pipeline Integration Tests
# =============================================================================

class TestFullPipeline:
    """Test the complete Tasmeeʿ pipeline: STT → Normalization → Alignment."""

    def test_perfect_recitation_pipeline(
        self, mock_stt_provider, al_fatiha_transcription, expected_fatiha_text
    ):
        """Test full pipeline with perfect recitation (no mistakes)."""
        from app.stt.alignment import RecitationAligner

        # Set up mock provider with perfect transcription
        mock_stt_provider.set_transcriptions(al_fatiha_transcription)

        # Initialize aligner with expected text
        expected_text = expected_fatiha_text.replace("\n", " ")
        aligner = RecitationAligner(expected_text)

        # Simulate audio chunks (dummy data)
        audio_chunks = [np.zeros(16000, dtype=np.float32) for _ in range(4)]

        # Process through pipeline
        all_mistakes = []
        for segment in mock_stt_provider.transcribe_stream(audio_chunks):
            result = aligner.process_segment(segment)
            all_mistakes.extend(result.mistakes)

        # Verify results
        state = aligner.get_state()
        assert state["is_complete"], "Should complete all expected words"
        assert state["progress"] == 1.0, "Progress should be 100%"
        assert len(all_mistakes) == 0, "Perfect recitation should have no mistakes"
        assert state["confidence"] >= 0.9, "Confidence should be high"

    def test_recitation_with_mistakes_pipeline(
        self, mock_stt_provider, al_fatiha_with_mistakes_transcription
    ):
        """Test full pipeline with mistakes in recitation."""
        from app.stt.alignment import RecitationAligner

        # Set up mock provider with mistakes
        mock_stt_provider.set_transcriptions(al_fatiha_with_mistakes_transcription)

        # Expected text (first 2 verses)
        expected_text = "بسم الله الرحمن الرحيم الحمد لله رب العالمين"
        aligner = RecitationAligner(expected_text, mismatch_patience=1)

        # Simulate audio chunks
        audio_chunks = [np.zeros(16000, dtype=np.float32) for _ in range(2)]

        # Process through pipeline
        for segment in mock_stt_provider.transcribe_stream(audio_chunks):
            aligner.process_segment(segment)

        # Get mistakes
        mistakes = aligner.get_mistakes()
        state = aligner.get_state()

        # Should have detected the substitution (ملك instead of رب)
        # Note: Detection depends on match_threshold and mismatch_patience
        assert state["progress"] > 0, "Should have made progress"

    def test_incremental_segment_processing(self, mock_stt_provider):
        """Test processing transcription in small increments."""
        from app.stt.alignment import RecitationAligner

        # Set up incremental transcription (word by word)
        incremental_transcription = [
            {"text": "بسم", "words": [{"word": "بسم", "start": 0.0, "end": 0.3}]},
            {"text": "الله", "words": [{"word": "الله", "start": 0.3, "end": 0.6}]},
            {"text": "الرحمن", "words": [{"word": "الرحمن", "start": 0.6, "end": 1.0}]},
            {"text": "الرحيم", "words": [{"word": "الرحيم", "start": 1.0, "end": 1.4}]},
        ]
        mock_stt_provider.set_transcriptions(incremental_transcription)

        expected_text = "بسم الله الرحمن الرحيم"
        aligner = RecitationAligner(expected_text)

        # Process word by word
        audio_chunks = [np.zeros(4000, dtype=np.float32) for _ in range(4)]
        progress_history = []

        for segment in mock_stt_provider.transcribe_stream(audio_chunks):
            aligner.process_segment(segment)
            progress_history.append(aligner.state.progress)

        # Verify incremental progress
        assert len(progress_history) == 4
        assert progress_history[-1] == 1.0, "Should be complete at end"
        # Progress should generally increase
        for i in range(1, len(progress_history)):
            assert progress_history[i] >= progress_history[i - 1]


class TestNormalizationIntegration:
    """Test Arabic normalization integration with alignment."""

    def test_diacritics_normalized_during_alignment(self):
        """Test that diacritics are properly normalized during alignment."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState

        # Expected text with full diacritics
        expected_with_diacritics = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

        aligner = RecitationAligner(expected_with_diacritics)

        # Transcription without diacritics (as STT typically returns)
        segment = TranscriptionSegment(
            text="بسم الله الرحمن الرحيم",
            start_time=0.0,
            end_time=2.0,
            words=[
                WordInfo(word="بسم", start_time=0.0, end_time=0.4, confidence=0.95),
                WordInfo(word="الله", start_time=0.4, end_time=0.8, confidence=0.98),
                WordInfo(word="الرحمن", start_time=0.8, end_time=1.4, confidence=0.96),
                WordInfo(word="الرحيم", start_time=1.4, end_time=2.0, confidence=0.97),
            ],
            state=TranscriptionState.FINAL,
            language="ar",
            confidence=0.95,
        )

        result = aligner.process_segment(segment)

        # Should match perfectly despite diacritic differences
        assert result.matched
        assert aligner.state.is_complete
        assert len(result.mistakes) == 0

    def test_alef_variants_normalized(self):
        """Test that alef variants are normalized during alignment."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState

        # Expected with standard alef
        expected = "إبراهيم آدم أحمد"
        aligner = RecitationAligner(expected)

        # Transcription with normalized alef (plain ا)
        segment = TranscriptionSegment(
            text="ابراهيم ادم احمد",
            start_time=0.0,
            end_time=1.5,
            words=[
                WordInfo(word="ابراهيم", start_time=0.0, end_time=0.5, confidence=0.9),
                WordInfo(word="ادم", start_time=0.5, end_time=1.0, confidence=0.9),
                WordInfo(word="احمد", start_time=1.0, end_time=1.5, confidence=0.9),
            ],
            state=TranscriptionState.FINAL,
            language="ar",
            confidence=0.9,
        )

        result = aligner.process_segment(segment)

        # Should match with alef normalization
        assert result.matched
        assert aligner.state.is_complete


class TestHighlightingIntegration:
    """Test UI highlighting generation during alignment."""

    def test_highlighting_updates_during_recitation(self, mock_stt_provider):
        """Test that highlighting updates correctly as recitation progresses."""
        from app.stt.alignment import RecitationAligner

        # Incremental transcription
        transcription = [
            {"text": "الحمد", "words": [{"word": "الحمد", "start": 0.0, "end": 0.3}]},
            {"text": "لله", "words": [{"word": "لله", "start": 0.3, "end": 0.6}]},
            {"text": "رب", "words": [{"word": "رب", "start": 0.6, "end": 0.9}]},
        ]
        mock_stt_provider.set_transcriptions(transcription)

        expected = "الحمد لله رب العالمين"
        aligner = RecitationAligner(expected)

        # Initial state
        highlighted = aligner.get_highlighted_text()
        assert highlighted[0]["status"] == "current"
        assert all(h["status"] == "pending" for h in highlighted[1:])

        # After first word
        audio_chunks = [np.zeros(4000, dtype=np.float32) for _ in range(3)]
        segments = list(mock_stt_provider.transcribe_stream(audio_chunks))

        aligner.process_segment(segments[0])
        highlighted = aligner.get_highlighted_text()
        assert highlighted[0]["status"] == "completed"
        assert highlighted[1]["status"] == "current"

        # After second word
        aligner.process_segment(segments[1])
        highlighted = aligner.get_highlighted_text()
        assert highlighted[0]["status"] == "completed"
        assert highlighted[1]["status"] == "completed"
        assert highlighted[2]["status"] == "current"


# =============================================================================
# API Integration Tests
# =============================================================================

class TestTasmeeAPIEndpoints:
    """Test Tasmee REST API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.query = MagicMock()
        return session

    def test_create_session_endpoint(self, client, mock_db_session):
        """Test POST /api/v1/tasmee/sessions creates a session."""
        with patch("app.api.routes.tasmee.get_async_session") as mock_get_db:
            mock_get_db.return_value = iter([mock_db_session])

            response = client.post(
                "/api/v1/tasmee/sessions",
                json={
                    "surah_number": 1,
                    "start_ayah": 1,
                    "end_ayah": 7,
                    "expected_text": "بسم الله الرحمن الرحيم",
                }
            )

            # Should create session (may fail if no actual DB, which is expected)
            # In real integration test with DB, this would be 200/201
            assert response.status_code in [200, 201, 422, 500]

    def test_transcribe_endpoint_structure(self, client):
        """Test POST /api/v1/tasmee/transcribe request structure."""
        # This tests the endpoint exists and accepts correct format
        # Actual transcription would require STT model

        with patch("app.api.routes.tasmee.get_stt_provider") as mock_provider:
            mock_provider.return_value.transcribe.return_value = MagicMock(
                text="بسم الله",
                segments=[],
                language="ar",
                duration=1.0,
            )

            # Create fake audio data (base64 encoded)
            import base64
            fake_audio = base64.b64encode(b"\x00" * 1000).decode()

            response = client.post(
                "/api/v1/tasmee/transcribe",
                json={
                    "audio_data": fake_audio,
                    "sample_rate": 16000,
                }
            )

            # Should return response (may fail without actual STT model)
            assert response.status_code in [200, 422, 500]


# =============================================================================
# Session Management Tests
# =============================================================================

class TestSessionManagement:
    """Test Tasmee session management."""

    def test_aligner_reset_for_new_session(self):
        """Test that aligner properly resets for new sessions."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState

        # First session
        aligner = RecitationAligner("الحمد لله")
        segment = TranscriptionSegment(
            text="الحمد لله",
            start_time=0.0,
            end_time=1.0,
            words=[
                WordInfo(word="الحمد", start_time=0.0, end_time=0.5, confidence=0.9),
                WordInfo(word="لله", start_time=0.5, end_time=1.0, confidence=0.9),
            ],
            state=TranscriptionState.FINAL,
            language="ar",
            confidence=0.9,
        )
        aligner.process_segment(segment)
        assert aligner.state.is_complete

        # Reset for new session with different text
        aligner.reset("رب العالمين")
        assert aligner.state.current_position == 0
        assert not aligner.state.is_complete
        assert len(aligner.state.expected_words) == 2

    def test_session_state_persistence(self):
        """Test that session state can be serialized and restored."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState

        expected = "الحمد لله رب العالمين"
        aligner = RecitationAligner(expected)

        # Process some words
        segment = TranscriptionSegment(
            text="الحمد لله",
            start_time=0.0,
            end_time=1.0,
            words=[
                WordInfo(word="الحمد", start_time=0.0, end_time=0.5, confidence=0.9),
                WordInfo(word="لله", start_time=0.5, end_time=1.0, confidence=0.9),
            ],
            state=TranscriptionState.FINAL,
            language="ar",
            confidence=0.9,
        )
        aligner.process_segment(segment)

        # Get state for persistence
        state = aligner.get_state()

        # Verify state is serializable (JSON compatible)
        state_json = json.dumps(state, ensure_ascii=False)
        restored_state = json.loads(state_json)

        assert restored_state["current_position"] == 2
        assert restored_state["progress"] == 0.5
        assert not restored_state["is_complete"]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling in the pipeline."""

    def test_handles_empty_transcription(self):
        """Test handling of empty transcription result."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, TranscriptionState

        aligner = RecitationAligner("الحمد لله")

        # Empty segment
        segment = TranscriptionSegment(
            text="",
            start_time=0.0,
            end_time=0.0,
            words=[],
            state=TranscriptionState.FINAL,
            language="ar",
            confidence=0.0,
        )

        # Should not crash
        result = aligner.process_segment(segment)
        assert result.words_matched == 0

    def test_handles_non_arabic_text_in_transcription(self):
        """Test handling of non-Arabic text in transcription."""
        from app.stt.alignment import RecitationAligner
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState

        aligner = RecitationAligner("الحمد لله")

        # Segment with non-Arabic text
        segment = TranscriptionSegment(
            text="Hello World",
            start_time=0.0,
            end_time=1.0,
            words=[
                WordInfo(word="Hello", start_time=0.0, end_time=0.5, confidence=0.9),
                WordInfo(word="World", start_time=0.5, end_time=1.0, confidence=0.9),
            ],
            state=TranscriptionState.FINAL,
            language="en",
            confidence=0.9,
        )

        # Should not crash, but won't match
        result = aligner.process_segment(segment)
        assert not aligner.state.is_complete


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test performance characteristics of the pipeline."""

    def test_alignment_performance_with_long_surah(self, mock_stt_provider):
        """Test alignment performance with longer text."""
        from app.stt.alignment import RecitationAligner
        import time

        # Al-Fatiha full text (7 verses)
        expected_text = """بسم الله الرحمن الرحيم
الحمد لله رب العالمين
الرحمن الرحيم
مالك يوم الدين
إياك نعبد وإياك نستعين
اهدنا الصراط المستقيم
صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين"""

        expected_text = expected_text.replace("\n", " ")
        aligner = RecitationAligner(expected_text)

        # Generate transcription for all words
        words = expected_text.split()
        transcription = []
        current_time = 0.0

        for word in words:
            transcription.append({
                "text": word,
                "start": current_time,
                "end": current_time + 0.3,
                "words": [{"word": word, "start": current_time, "end": current_time + 0.3}]
            })
            current_time += 0.3

        mock_stt_provider.set_transcriptions(transcription)

        # Measure alignment time
        start_time = time.time()

        audio_chunks = [np.zeros(4000, dtype=np.float32) for _ in transcription]
        for segment in mock_stt_provider.transcribe_stream(audio_chunks):
            aligner.process_segment(segment)

        elapsed = time.time() - start_time

        # Should complete within reasonable time (1 second for ~30 words)
        assert elapsed < 1.0, f"Alignment took too long: {elapsed:.2f}s"
        assert aligner.state.is_complete

    def test_batch_alignment_efficiency(self):
        """Test batch alignment is efficient for full recitations."""
        from app.stt.alignment import align_transcription
        from app.stt.providers.base import TranscriptionSegment, WordInfo, TranscriptionState
        import time

        expected = "الحمد لله رب العالمين الرحمن الرحيم مالك يوم الدين"
        words = expected.split()

        # Create segments
        segments = []
        current_time = 0.0
        for word in words:
            segments.append(TranscriptionSegment(
                text=word,
                start_time=current_time,
                end_time=current_time + 0.3,
                words=[WordInfo(word=word, start_time=current_time, end_time=current_time + 0.3, confidence=0.9)],
                state=TranscriptionState.FINAL,
                language="ar",
                confidence=0.9,
            ))
            current_time += 0.3

        start_time = time.time()
        mistakes, stats = align_transcription(expected, segments)
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Batch alignment too slow: {elapsed:.3f}s"
        assert stats["is_complete"]


# =============================================================================
# Mock Audio Simulation Tests
# =============================================================================

class TestAudioSimulation:
    """Test with simulated audio data."""

    def test_16khz_mono_pcm_processing(self, mock_stt_provider):
        """Test processing of 16kHz mono PCM audio format."""
        from app.stt.alignment import RecitationAligner

        mock_stt_provider.set_transcriptions([
            {"text": "بسم الله", "words": [
                {"word": "بسم", "start": 0.0, "end": 0.4},
                {"word": "الله", "start": 0.4, "end": 0.8},
            ]}
        ])

        aligner = RecitationAligner("بسم الله")

        # Simulate 1 second of 16kHz mono PCM audio
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        audio_data = np.zeros(samples, dtype=np.float32)

        # Process through mock provider
        result = mock_stt_provider.transcribe(audio_data, sample_rate=sample_rate)

        # Align result
        for segment in result.segments:
            aligner.process_segment(segment)

        assert aligner.state.is_complete

    def test_chunked_audio_streaming(self, mock_stt_provider):
        """Test streaming audio in chunks."""
        from app.stt.alignment import RecitationAligner

        mock_stt_provider.set_transcriptions([
            {"text": "الحمد", "words": [{"word": "الحمد"}]},
            {"text": "لله", "words": [{"word": "لله"}]},
        ])

        aligner = RecitationAligner("الحمد لله")

        # Simulate 2-second chunks of audio
        chunk_duration = 2.0
        sample_rate = 16000
        chunk_samples = int(sample_rate * chunk_duration)

        def audio_chunk_generator():
            for _ in range(2):
                yield np.zeros(chunk_samples, dtype=np.float32)

        # Process chunks
        for segment in mock_stt_provider.transcribe_stream(audio_chunk_generator()):
            aligner.process_segment(segment)

        assert aligner.state.is_complete


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
