"""Streaming alignment: correct recitation must not raise slip alerts.

The WebSocket used overlapping 1.2 s / 0.4 s windows, so every recognised word
was fed to the aligner up to three times and a perfect Al-Fatiha 1:2-7 produced
dozens of false "mistakes". Windows are now non-overlapping (3 s) and a slip is
reported only when the same expected word fails in 2 consecutive windows.

The expected text is read from the canonical Tanzil file, never typed here.
"""

import json
from pathlib import Path

import pytest

from app.api.routes.tasmee import WS_MISMATCH_WINDOW_PATIENCE, WS_WINDOW_SECONDS
from app.stt.alignment import MistakeType, RecitationAligner
from app.stt.arabic_normalizer import tokenize_with_positions
from app.stt.audio_buffer import RollingAudioBuffer
from app.stt.providers.base import TranscriptionSegment, WordInfo

TANZIL = Path(__file__).resolve().parents[4] / "data" / "raw" / "quran_tanzil.json"


def _ayat(sura: int, start: int, end: int) -> str:
    if not TANZIL.exists():
        pytest.skip("canonical data/raw/quran_tanzil.json not present")
    data = json.loads(TANZIL.read_text(encoding="utf-8"))
    return " ".join(
        v["aya_text"]
        for v in data["verses"]
        if int(v["sura_no"]) == sura and start <= int(v["aya_no"]) <= end
    )


def _windows(words, per_window: int):
    """Chunk recognised words like the production buffer: each word once."""
    out = []
    t = 0.0
    for i in range(0, len(words), per_window):
        chunk = words[i:i + per_window]
        infos = []
        for w in chunk:
            infos.append(WordInfo(word=w, start_time=t, end_time=t + 0.4, confidence=0.9))
            t += 0.4
        out.append(TranscriptionSegment(text=" ".join(chunk), start_time=infos[0].start_time,
                                        end_time=infos[-1].end_time, words=infos))
    return out


def _streaming_aligner(text: str) -> RecitationAligner:
    return RecitationAligner(text, mismatch_window_patience=WS_MISMATCH_WINDOW_PATIENCE)


def test_production_buffer_windows_do_not_overlap():
    import numpy as np

    buf = RollingAudioBuffer(window_duration=WS_WINDOW_SECONDS, step_duration=WS_WINDOW_SECONDS)
    assert buf.overlap_samples == 0
    n = int(WS_WINDOW_SECONDS * 16000)
    # Browser chunks never line up with the window: feed 4096-sample chunks of
    # a ramp and check every sample comes out exactly once, in order.
    signal = np.arange(n * 3, dtype=np.float32)
    emitted = []
    for i in range(0, len(signal), 4096):
        w = buf.add_chunk(signal[i:i + 4096])
        if w is not None:
            assert len(w) == n
            emitted.append(w)
    assert len(emitted) == 3
    assert np.array_equal(np.concatenate(emitted), signal)
    assert len(buf.buffer) == 0


def _foreign_word() -> str:
    """A word from another surah that matches nothing near Al-Fatiha 1:2-3."""
    return tokenize_with_positions(_ayat(112, 1, 1))[0].original


@pytest.mark.parametrize("per_window", [1, 3, 4, 7])
def test_correct_fatiha_2_7_has_no_mistakes(per_window):
    text = _ayat(1, 2, 7)
    expected = [w.original for w in tokenize_with_positions(text)]
    aligner = _streaming_aligner(text)
    for seg in _windows(expected, per_window):
        aligner.process_segment(seg)
    assert aligner.state.mistakes == []
    assert aligner.state.current_position == len(expected)


def test_skipped_word_yields_one_deletion():
    text = _ayat(1, 2, 7)
    expected = [w.original for w in tokenize_with_positions(text)]
    recited = expected[:5] + expected[6:]
    aligner = _streaming_aligner(text)
    for seg in _windows(recited, 4):
        aligner.process_segment(seg)
    deletions = [m for m in aligner.state.mistakes if m.type == MistakeType.DELETION]
    assert len(aligner.state.mistakes) == 1
    assert len(deletions) == 1
    assert deletions[0].position == 5
    assert aligner.state.current_position == len(expected)


def test_single_misheard_window_then_correct_word_is_not_a_mistake():
    text = _ayat(1, 2, 7)
    expected = [w.original for w in tokenize_with_positions(text)]
    aligner = _streaming_aligner(text)
    # Window 1: two correct words, then noise that matches nothing.
    aligner.process_segment(_windows(expected[:2] + [_foreign_word()], 3)[0])
    # Window 2: the reciter continues correctly.
    for seg in _windows(expected[2:], 4):
        aligner.process_segment(seg)
    assert aligner.state.mistakes == []
    assert aligner.state.current_position == len(expected)


def test_wrong_word_persisting_two_windows_is_reported_once():
    text = _ayat(1, 2, 7)
    expected = [w.original for w in tokenize_with_positions(text)]
    aligner = _streaming_aligner(text)
    aligner.process_segment(_windows(expected[:2] + [_foreign_word()], 3)[0])
    assert aligner.state.mistakes == []
    aligner.process_segment(_windows([_foreign_word()], 1)[0])
    assert len(aligner.state.mistakes) == 1
    assert aligner.state.mistakes[0].position == 2
    assert aligner.state.mistakes[0].type in (MistakeType.SUBSTITUTION, MistakeType.MISPRONUNCIATION)
