#!/usr/bin/env python3
"""
Tasmeeʿ (Memorization) REAL Integration Tests

These tests use REAL audio files and the REAL faster-whisper STT model
to verify the complete pipeline works correctly for Quran memorization.

Prerequisites:
1. Download audio fixtures:
   cd backend/tests/fixtures/audio
   python download_fixtures.py

2. Install faster-whisper:
   pip install faster-whisper

3. Run tests:
   PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v

For CI/CD environments without GPU, use:
   STT_MODEL_SIZE=tiny PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v

To skip if model not available:
   PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v -k "not slow"
"""

import os
import sys
import wave
import pytest
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# =============================================================================
# Configuration
# =============================================================================

# Audio fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "audio"

# Model configuration from environment
MODEL_SIZE = os.environ.get("STT_MODEL_SIZE", "base")
DEVICE = os.environ.get("STT_DEVICE", "cpu")
COMPUTE_TYPE = os.environ.get("STT_COMPUTE_TYPE", "int8")

# Skip tests if fixtures not downloaded (check both WAV and MP3)
SKIP_IF_NO_FIXTURES = not (
    (FIXTURES_DIR / "001_001_bismillah.wav").exists() or
    (FIXTURES_DIR / "001_001_bismillah.mp3").exists()
)
SKIP_REASON = "Audio fixtures not found. Run: cd tests/fixtures/audio && python download_fixtures.py"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def stt_provider():
    """
    Create real faster-whisper STT provider.
    Module-scoped to avoid reloading model for each test.
    """
    try:
        from app.stt.providers.faster_whisper import FasterWhisperProvider

        print(f"\nLoading faster-whisper model: {MODEL_SIZE} on {DEVICE}")
        provider = FasterWhisperProvider(
            model_size=MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )
        provider.load_model()
        print(f"Model loaded successfully: {provider.name} ({provider.model_size})")
        return provider

    except ImportError as e:
        pytest.skip(f"faster-whisper not installed: {e}")
    except Exception as e:
        pytest.skip(f"Could not load STT model: {e}")


@pytest.fixture
def audio_loader():
    """Helper to load audio files (supports WAV and MP3)."""
    def load_audio(filename: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return (audio_data, sample_rate)."""
        # Try WAV first, then MP3
        wav_path = FIXTURES_DIR / filename
        mp3_path = FIXTURES_DIR / filename.replace(".wav", ".mp3")

        if wav_path.exists():
            filepath = wav_path
        elif mp3_path.exists():
            filepath = mp3_path
        else:
            pytest.skip(f"Audio file not found: {wav_path} or {mp3_path}")

        # Use faster-whisper's audio loading (handles WAV, MP3, etc.)
        try:
            from faster_whisper.audio import decode_audio
            audio = decode_audio(str(filepath), sampling_rate=16000)
            return audio, 16000
        except ImportError:
            # Fallback to wave module for WAV files only
            if filepath.suffix == ".wav":
                with wave.open(str(filepath), "rb") as wf:
                    sample_rate = wf.getframerate()
                    n_frames = wf.getnframes()
                    audio_bytes = wf.readframes(n_frames)
                    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0
                    return audio_float32, sample_rate
            else:
                pytest.skip("faster-whisper not installed, cannot load MP3 files")

    return load_audio


# =============================================================================
# Expected Verse Texts
# =============================================================================

VERSE_TEXTS = {
    "001_001_bismillah.wav": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    "001_002_alhamdulillah.wav": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
    "001_003_arrahman.wav": "الرَّحْمَٰنِ الرَّحِيمِ",
    "001_004_maliki.wav": "مَالِكِ يَوْمِ الدِّينِ",
    "001_005_iyyaka.wav": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
    "001_006_ihdina.wav": "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
    "001_007_sirat.wav": "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
    "112_001_ikhlas_1.wav": "قُلْ هُوَ اللَّهُ أَحَدٌ",
    "112_002_ikhlas_2.wav": "اللَّهُ الصَّمَدُ",
    "112_003_ikhlas_3.wav": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
    "112_004_ikhlas_4.wav": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
}

# Simplified (no diacritics) for matching
VERSE_TEXTS_SIMPLE = {
    "001_001_bismillah.wav": "بسم الله الرحمن الرحيم",
    "001_002_alhamdulillah.wav": "الحمد لله رب العالمين",
    "001_003_arrahman.wav": "الرحمن الرحيم",
    "001_004_maliki.wav": "مالك يوم الدين",
    "001_005_iyyaka.wav": "إياك نعبد وإياك نستعين",
    "001_006_ihdina.wav": "اهدنا الصراط المستقيم",
    "001_007_sirat.wav": "صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين",
    "112_001_ikhlas_1.wav": "قل هو الله أحد",
    "112_002_ikhlas_2.wav": "الله الصمد",
    "112_003_ikhlas_3.wav": "لم يلد ولم يولد",
    "112_004_ikhlas_4.wav": "ولم يكن له كفوا أحد",
}


# =============================================================================
# Real STT Transcription Tests
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
class TestRealSTTTranscription:
    """Test real STT transcription of Quran recitation."""

    def test_transcribe_bismillah(self, stt_provider, audio_loader):
        """Test transcription of Bismillah (1:1)."""
        audio, sample_rate = audio_loader("001_001_bismillah.wav")

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        assert result.full_text, "Should produce transcription"
        assert result.language == "ar", "Should detect Arabic"
        assert len(result.segments) > 0, "Should have segments"

        # Check key words are recognized
        from app.stt.arabic_normalizer import normalize_for_matching
        normalized = normalize_for_matching(result.full_text)

        # At least "الله" should be recognized
        assert "الله" in normalized or "اله" in normalized, \
            f"Should recognize 'الله' in: {result.full_text}"

        print(f"\nBismillah transcription: {result.full_text}")

    def test_transcribe_al_fatiha_verse_2(self, stt_provider, audio_loader):
        """Test transcription of Al-Fatiha verse 2 (الحمد لله)."""
        audio, sample_rate = audio_loader("001_002_alhamdulillah.wav")

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        assert result.full_text, "Should produce transcription"

        from app.stt.arabic_normalizer import normalize_for_matching
        normalized = normalize_for_matching(result.full_text)

        # Check key words
        assert "الحمد" in normalized or "حمد" in normalized, \
            f"Should recognize 'الحمد' in: {result.full_text}"

        print(f"\nAlhamdulillah transcription: {result.full_text}")

    def test_transcribe_surah_ikhlas(self, stt_provider, audio_loader):
        """Test transcription of Surah Al-Ikhlas verse 1."""
        audio, sample_rate = audio_loader("112_001_ikhlas_1.wav")

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        assert result.full_text, "Should produce transcription"

        from app.stt.arabic_normalizer import normalize_for_matching
        normalized = normalize_for_matching(result.full_text)

        # "قل" or "الله" or "أحد" should be recognized
        has_expected = any(word in normalized for word in ["قل", "الله", "احد", "اله"])
        assert has_expected, f"Should recognize Ikhlas words in: {result.full_text}"

        print(f"\nIkhlas transcription: {result.full_text}")

    def test_word_timestamps_present(self, stt_provider, audio_loader):
        """Test that word-level timestamps are provided."""
        audio, sample_rate = audio_loader("001_001_bismillah.wav")

        result = stt_provider.transcribe(audio, sample_rate=sample_rate, word_timestamps=True)

        assert result.segments, "Should have segments"

        # Check at least some segments have words with timestamps
        has_word_timestamps = False
        for segment in result.segments:
            if segment.words:
                for word in segment.words:
                    if word.start_time is not None and word.end_time is not None:
                        has_word_timestamps = True
                        break

        assert has_word_timestamps, "Should have word-level timestamps"


# =============================================================================
# Full Pipeline Tests (STT → Normalization → Alignment)
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
class TestRealFullPipeline:
    """Test the complete pipeline with real audio."""

    def test_pipeline_perfect_recitation_bismillah(self, stt_provider, audio_loader):
        """Test full pipeline with Bismillah recitation."""
        from app.stt.alignment import RecitationAligner

        audio, sample_rate = audio_loader("001_001_bismillah.wav")
        expected_text = VERSE_TEXTS["001_001_bismillah.wav"]

        # Transcribe
        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        # Align
        aligner = RecitationAligner(expected_text, match_threshold=0.7)
        for segment in result.segments:
            aligner.process_segment(segment)

        state = aligner.get_state()

        print(f"\nBismillah Pipeline Results:")
        print(f"  Expected: {expected_text}")
        print(f"  Transcribed: {result.full_text}")
        print(f"  Progress: {state['progress'] * 100:.0f}%")
        print(f"  Words matched: {state['current_position']}/{state['total_words']}")

        # Should make significant progress (at least 50% of words)
        assert state["progress"] >= 0.5, \
            f"Should recognize at least 50% of words, got {state['progress']*100:.0f}%"

    def test_pipeline_al_fatiha_verse_2(self, stt_provider, audio_loader):
        """Test full pipeline with Al-Fatiha verse 2."""
        from app.stt.alignment import RecitationAligner

        audio, sample_rate = audio_loader("001_002_alhamdulillah.wav")
        expected_text = VERSE_TEXTS["001_002_alhamdulillah.wav"]

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        aligner = RecitationAligner(expected_text, match_threshold=0.7)
        for segment in result.segments:
            aligner.process_segment(segment)

        state = aligner.get_state()

        print(f"\nAlhamdulillah Pipeline Results:")
        print(f"  Expected: {expected_text}")
        print(f"  Transcribed: {result.full_text}")
        print(f"  Progress: {state['progress'] * 100:.0f}%")

        assert state["progress"] >= 0.5

    def test_pipeline_highlighted_text_generation(self, stt_provider, audio_loader):
        """Test that highlighted text is generated correctly."""
        from app.stt.alignment import RecitationAligner

        audio, sample_rate = audio_loader("001_001_bismillah.wav")
        expected_text = VERSE_TEXTS_SIMPLE["001_001_bismillah.wav"]

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        aligner = RecitationAligner(expected_text, match_threshold=0.7)
        for segment in result.segments:
            aligner.process_segment(segment)

        highlighted = aligner.get_highlighted_text()

        print(f"\nHighlighted Text:")
        for h in highlighted:
            print(f"  {h['word']}: {h['status']}")

        assert len(highlighted) == 4, "Should have 4 words in بسم الله الرحمن الرحيم"

        # Check structure
        for h in highlighted:
            assert "word" in h
            assert "status" in h
            assert h["status"] in ["completed", "current", "pending", "error"]


# =============================================================================
# Streaming Pipeline Tests
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
class TestRealStreamingPipeline:
    """Test streaming transcription with real audio."""

    def test_streaming_chunks(self, stt_provider, audio_loader):
        """Test processing audio in chunks (simulating real-time)."""
        from app.stt.alignment import RecitationAligner

        audio, sample_rate = audio_loader("001_002_alhamdulillah.wav")
        expected_text = VERSE_TEXTS_SIMPLE["001_002_alhamdulillah.wav"]

        # Split audio into chunks (2 second chunks)
        chunk_size = sample_rate * 2  # 2 seconds
        chunks = [audio[i:i+chunk_size] for i in range(0, len(audio), chunk_size)]

        aligner = RecitationAligner(expected_text, match_threshold=0.7)
        progress_history = []

        print(f"\nStreaming chunks ({len(chunks)} chunks):")

        for i, chunk in enumerate(chunks):
            if len(chunk) < sample_rate * 0.5:  # Skip very short chunks
                continue

            result = stt_provider.transcribe(chunk, sample_rate=sample_rate)

            for segment in result.segments:
                aligner.process_segment(segment)

            state = aligner.get_state()
            progress_history.append(state["progress"])
            print(f"  Chunk {i+1}: {result.full_text[:50]}... Progress: {state['progress']*100:.0f}%")

        # Progress should generally increase or stay the same
        final_progress = aligner.get_state()["progress"]
        assert final_progress > 0, "Should make some progress"


# =============================================================================
# Mistake Detection Tests
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
class TestRealMistakeDetection:
    """Test mistake detection with real vs expected text mismatches."""

    def test_detect_wrong_expected_text(self, stt_provider, audio_loader):
        """Test mistake detection when expected text is different from audio."""
        from app.stt.alignment import RecitationAligner

        # Use Bismillah audio
        audio, sample_rate = audio_loader("001_001_bismillah.wav")

        # But expect Al-Fatiha verse 2 (wrong text)
        wrong_expected = VERSE_TEXTS_SIMPLE["001_002_alhamdulillah.wav"]

        result = stt_provider.transcribe(audio, sample_rate=sample_rate)

        aligner = RecitationAligner(wrong_expected, match_threshold=0.8, mismatch_patience=1)
        for segment in result.segments:
            aligner.process_segment(segment)

        mistakes = aligner.get_mistakes()
        state = aligner.get_state()

        print(f"\nMismatch Detection:")
        print(f"  Audio contains: Bismillah")
        print(f"  Expected: {wrong_expected}")
        print(f"  Transcribed: {result.full_text}")
        print(f"  Progress: {state['progress'] * 100:.0f}%")
        print(f"  Mistakes detected: {len(mistakes)}")

        # Should detect mismatches (low progress or mistakes)
        # Note: Exact behavior depends on STT accuracy and matching threshold
        assert state["progress"] < 0.8 or len(mistakes) > 0, \
            "Should detect mismatch between audio and expected text"


# =============================================================================
# Accuracy Benchmark Tests
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
@pytest.mark.slow
class TestAccuracyBenchmark:
    """Benchmark STT accuracy on Quran recitation."""

    def test_al_fatiha_accuracy(self, stt_provider, audio_loader):
        """Test accuracy across all Al-Fatiha verses."""
        from app.stt.arabic_normalizer import normalize_for_matching, word_similarity

        results = []
        al_fatiha_files = [f for f in VERSE_TEXTS_SIMPLE.keys() if f.startswith("001_")]

        print(f"\nAl-Fatiha Accuracy Benchmark:")
        print("=" * 60)

        for filename in sorted(al_fatiha_files):
            # Check for both WAV and MP3
            wav_file = filename
            mp3_file = filename.replace(".wav", ".mp3")
            if not (FIXTURES_DIR / wav_file).exists() and not (FIXTURES_DIR / mp3_file).exists():
                continue

            audio, sample_rate = audio_loader(filename)
            expected = VERSE_TEXTS_SIMPLE[filename]

            result = stt_provider.transcribe(audio, sample_rate=sample_rate)

            # Calculate word-level accuracy
            expected_words = normalize_for_matching(expected).split()
            transcribed_words = normalize_for_matching(result.full_text).split()

            # Count matched words
            matched = 0
            for exp_word in expected_words:
                for trans_word in transcribed_words:
                    if word_similarity(exp_word, trans_word) >= 0.8:
                        matched += 1
                        break

            accuracy = matched / len(expected_words) if expected_words else 0

            results.append({
                "verse": filename,
                "expected": expected,
                "transcribed": result.full_text,
                "accuracy": accuracy,
            })

            print(f"\n{filename}:")
            print(f"  Expected:    {expected}")
            print(f"  Transcribed: {result.full_text}")
            print(f"  Accuracy:    {accuracy * 100:.0f}%")

        # Calculate overall accuracy
        avg_accuracy = sum(r["accuracy"] for r in results) / len(results) if results else 0

        print("\n" + "=" * 60)
        print(f"Overall Accuracy: {avg_accuracy * 100:.0f}%")
        print(f"Verses tested: {len(results)}")

        # Minimum acceptable accuracy for production
        assert avg_accuracy >= 0.5, \
            f"Average accuracy should be at least 50%, got {avg_accuracy*100:.0f}%"

    def test_surah_ikhlas_accuracy(self, stt_provider, audio_loader):
        """Test accuracy on Surah Al-Ikhlas."""
        from app.stt.arabic_normalizer import normalize_for_matching, word_similarity

        ikhlas_files = [f for f in VERSE_TEXTS_SIMPLE.keys() if f.startswith("112_")]

        total_accuracy = 0
        count = 0

        print(f"\nSurah Al-Ikhlas Accuracy:")

        for filename in sorted(ikhlas_files):
            # Check for both WAV and MP3
            mp3_file = filename.replace(".wav", ".mp3")
            if not (FIXTURES_DIR / filename).exists() and not (FIXTURES_DIR / mp3_file).exists():
                continue

            audio, sample_rate = audio_loader(filename)
            expected = VERSE_TEXTS_SIMPLE[filename]

            result = stt_provider.transcribe(audio, sample_rate=sample_rate)

            expected_words = normalize_for_matching(expected).split()
            transcribed_words = normalize_for_matching(result.full_text).split()

            matched = 0
            for exp_word in expected_words:
                for trans_word in transcribed_words:
                    if word_similarity(exp_word, trans_word) >= 0.8:
                        matched += 1
                        break

            accuracy = matched / len(expected_words) if expected_words else 0
            total_accuracy += accuracy
            count += 1

            print(f"  {filename}: {accuracy * 100:.0f}%")

        avg = total_accuracy / count if count else 0
        print(f"\n  Average: {avg * 100:.0f}%")


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.skipif(SKIP_IF_NO_FIXTURES, reason=SKIP_REASON)
class TestPerformance:
    """Test performance characteristics."""

    def test_transcription_speed(self, stt_provider, audio_loader):
        """Test transcription speed (realtime factor)."""
        import time

        audio, sample_rate = audio_loader("001_001_bismillah.wav")
        audio_duration = len(audio) / sample_rate

        start = time.time()
        result = stt_provider.transcribe(audio, sample_rate=sample_rate)
        elapsed = time.time() - start

        realtime_factor = audio_duration / elapsed if elapsed > 0 else float("inf")

        print(f"\nTranscription Speed:")
        print(f"  Audio duration: {audio_duration:.2f}s")
        print(f"  Processing time: {elapsed:.2f}s")
        print(f"  Realtime factor: {realtime_factor:.1f}x")
        print(f"  Model: {stt_provider.name} ({stt_provider.model_size})")

        # Should be at least 0.5x realtime on CPU
        assert realtime_factor >= 0.5, \
            f"Should be at least 0.5x realtime, got {realtime_factor:.1f}x"


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    # Check if fixtures exist
    if SKIP_IF_NO_FIXTURES:
        print("Audio fixtures not found!")
        print(f"Run: cd {FIXTURES_DIR} && python download_fixtures.py")
        sys.exit(1)

    pytest.main([__file__, "-v", "-s"])
