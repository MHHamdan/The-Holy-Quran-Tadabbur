"""
Phase T4 tests — NLI Emotion Classifier.

Tests the NLIEmotionClassifier service and its integration with
classify_emotion() in spiritual_guidance_service.py.

Test groups:
  1. Unit tests for NLIEmotionClassifier (mocked Hugging Face call)
  2. is_arabic_dominant() language detection utility
  3. classify_emotion() integration — NLI path, Arabic path, fallback path
  4. API integration — /ask returns emotion_confidence field
  5. Live model smoke tests (marked live_hf; run with `pytest -m live_hf`)
"""
import asyncio
import os
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.main import app
from app.core.rate_limit import therapy_rate_limit

pytestmark = pytest.mark.asyncio(loop_scope="module")

# Derived from settings so a port change in scripts/ports.env does not
# strand these tests on a stale port.
from app.core.config import settings as _settings
_DB_URL = _settings.database_url.replace("postgresql://", "postgresql+asyncpg://")


async def _clean_sessions(ids: list[str]) -> None:
    if not ids:
        return
    engine = create_async_engine(_DB_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM therapy_sessions WHERE session_id = ANY(:ids)"),
                {"ids": ids},
            )
    finally:
        await engine.dispose()


async def _no_rate_limit() -> None:
    pass


app.dependency_overrides[therapy_rate_limit] = _no_rate_limit


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ===========================================================================
# 1. NLIEmotionClassifier unit tests (mocked model)
# ===========================================================================

class TestNLIClassifierUnit:
    """Unit tests with the Hugging Face zero-shot call mocked (no network)."""

    @staticmethod
    def _scores(best: str, confidence: float = 0.99, others: float = 0.05):
        from app.services.emotion_classifier import EMOTION_LABELS
        return [(lbl, confidence if lbl == best else others) for lbl in EMOTION_LABELS]

    @staticmethod
    def _configured(value: bool = True):
        return patch("app.ai.hf_client.hf_configured", return_value=value)

    async def test_classify_returns_correct_emotion(self):
        from app.services.emotion_classifier import NLIEmotionClassifier, EMOTION_LABELS
        clf = NLIEmotionClassifier(confidence_threshold=0.4)
        with self._configured(), patch.object(clf, "_zero_shot", return_value=self._scores(EMOTION_LABELS[0])):
            emotion, confidence = clf.classify("I feel anxious today")
        assert emotion == EMOTION_LABELS[0]
        assert confidence > 0.4

    async def test_classify_returns_empty_when_below_threshold(self):
        """When all entailment scores are low, returns ('', low_conf)."""
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier(confidence_threshold=0.9)
        with self._configured(), patch.object(clf, "_zero_shot", return_value=self._scores("sadness", 0.3)):
            emotion, confidence = clf.classify("I feel somewhat off today")
        assert emotion == ""
        assert confidence == pytest.approx(0.3)

    async def test_not_configured_returns_empty(self):
        """No HF token → ('', 0.0) and the upstream is never called."""
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        with self._configured(False), patch.object(clf, "_zero_shot") as call:
            emotion, confidence = clf.classify("I feel anxious today")
        call.assert_not_called()
        assert (emotion, confidence) == ("", 0.0)
        assert not clf.is_ready

    async def test_warmup_returns_true_when_configured(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        with self._configured():
            assert clf.warmup() is True
        assert clf.is_ready

    async def test_warmup_returns_false_when_not_configured(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        with self._configured(False):
            assert clf.warmup() is False
        assert not clf.is_ready

    @pytest.mark.parametrize("kind", ["quota", "timeout", "network", "malformed", "auth"])
    async def test_upstream_failure_returns_empty(self, kind):
        from app.ai.hf_client import HFErrorKind, HFInferenceError
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        err = HFInferenceError(HFErrorKind(kind), "zero-shot")
        with self._configured(), patch.object(clf, "_zero_shot", side_effect=err):
            assert clf.classify("I feel anxious") == ("", 0.0)

    async def test_unknown_labels_are_ignored(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        with self._configured(), patch.object(clf, "_zero_shot", return_value=[("joy", 0.99)]):
            assert clf.classify("I feel great") == ("", 0.0)

    async def test_empty_text_short_circuits(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        with self._configured(), patch.object(clf, "_zero_shot") as call:
            assert clf.classify("   ") == ("", 0.0)
        call.assert_not_called()


# ===========================================================================
# 2. Arabic detection utility
# ===========================================================================

class TestArabicDetection:
    async def test_arabic_text_is_detected(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert is_arabic_dominant("أشعر بالقلق الشديد")

    async def test_english_text_not_arabic(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert not is_arabic_dominant("I feel very anxious today")

    async def test_mixed_text_below_threshold(self):
        from app.services.emotion_classifier import is_arabic_dominant
        # Short Arabic word in mostly English sentence
        assert not is_arabic_dominant("I feel قلق today but mostly English")

    async def test_mixed_text_above_threshold(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert is_arabic_dominant("أشعر بالقلق الشديد وI feel worried")

    async def test_empty_string_returns_false(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert not is_arabic_dominant("")

    async def test_numbers_only_returns_false(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert not is_arabic_dominant("12345 !@#$")


# ===========================================================================
# 3. classify_emotion() integration
# ===========================================================================

class TestClassifyEmotionIntegration:
    """Test that classify_emotion() routes correctly through NLI → keyword fallback."""

    def _mock_nli_result(self, emotion: str, confidence: float = 0.99):
        """Patch get_classifier at source so the local import inside classify_emotion sees it."""
        mock_clf = MagicMock()
        mock_clf.classify.return_value = (emotion, confidence)
        return patch(
            "app.services.emotion_classifier.get_classifier",
            return_value=mock_clf,
        )

    async def test_english_uses_nli_when_enabled(self):
        from app.services.spiritual_guidance_service import classify_emotion
        with self._mock_nli_result("grief"):
            result = classify_emotion("I am grieving the loss of my father")
        assert result == "grief"

    async def test_arabic_bypasses_nli(self):
        """Arabic text routes directly to keyword classifier; NLI is not called."""
        from app.services.spiritual_guidance_service import classify_emotion
        mock_clf = MagicMock()
        with patch("app.services.emotion_classifier.get_classifier", return_value=mock_clf):
            result = classify_emotion("أشعر بالقلق الشديد")
        mock_clf.classify.assert_not_called()
        assert result in ["anxiety", "general"]

    async def test_low_confidence_falls_back_to_keywords(self):
        from app.services.spiritual_guidance_service import classify_emotion
        mock_clf = MagicMock()
        mock_clf.classify.return_value = ("", 0.15)  # empty = below threshold
        with patch("app.services.emotion_classifier.get_classifier", return_value=mock_clf):
            result = classify_emotion("I feel very anxious and worried")
        assert result == "anxiety"

    async def test_disabled_classifier_uses_keywords(self):
        from app.services.spiritual_guidance_service import classify_emotion
        mock_clf = MagicMock()
        mock_settings = MagicMock()
        mock_settings.emotion_classifier_enabled = False
        with (
            patch("app.services.emotion_classifier.get_classifier", return_value=mock_clf),
            patch("app.core.config.get_settings", return_value=mock_settings),
        ):
            result = classify_emotion("I feel very anxious and worried")
        mock_clf.classify.assert_not_called()
        assert result == "anxiety"

    async def test_nli_general_falls_through_to_keywords(self):
        """NLI returning 'general' with high confidence should be accepted."""
        from app.services.spiritual_guidance_service import classify_emotion
        with self._mock_nli_result("general", 0.95):
            result = classify_emotion("I just need some guidance today")
        assert result == "general"


# ===========================================================================
# 4. API integration — emotion_confidence field in /ask response
# ===========================================================================

class TestApiEmotionConfidence:
    _ids: list[str] = []

    async def test_ask_response_has_emotion_confidence(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel very anxious today"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert "emotion_confidence" in data
        assert isinstance(data["emotion_confidence"], float)
        assert 0.0 <= data["emotion_confidence"] <= 1.0

    async def test_emotion_override_confidence_is_1(self, client):
        """An explicit emotion_override should yield confidence = 1.0."""
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel something", "emotion_override": "grief"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["emotion"] == "grief"
        assert data["emotion_confidence"] == 1.0

    async def test_arabic_message_returns_valid_confidence(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "أشعر بالقلق الشديد من كل شيء", "language": "ar"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        # Arabic → keyword fallback → confidence = 0.0
        assert data["emotion_confidence"] == 0.0
        assert data["emotion"] == "anxiety"

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 5. Live model smoke test (skipped if model not pre-loaded)
# ===========================================================================

@pytest.mark.live_hf
class TestLiveModelSmoke:
    """
    Smoke tests against the hosted zero-shot model (spends HF credit).

    Run with:
        pytest -m live_hf tests/unit/test_emotion_classifier_phase_t4.py
    """

    _CASES = [
        ("I feel anxious and overwhelmed about the future", "anxiety"),
        ("I am grieving the loss of my father who passed away", "grief"),
        ("I feel so guilty about my past mistakes", "guilt"),
        ("I am questioning my faith and full of doubt", "doubt"),
        ("I feel very lonely and isolated from everyone", "loneliness"),
        ("I am burning with rage and cannot calm down", "anger"),
        ("I feel no hope — everything seems pointless", "hopelessness"),
        ("I am deeply grateful for all the blessings in my life", "gratitude"),
        ("I feel enormous stress and pressure from work", "stress"),
        ("I am terrified of what might happen next", "fear"),
        ("I feel so deeply sad about everything in my life", "sadness"),
    ]

    @staticmethod
    def _live_classifier():
        from app.ai.hf_client import HFErrorKind, HFInferenceError
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier()
        if not clf.warmup():
            pytest.skip("HF_TOKEN not configured")
        # Measure model quality, not request-path latency: allow cold starts.
        clf.TIMEOUT_SECONDS = 60.0

        def predict(text):
            for attempt in range(3):
                try:
                    scored = clf._zero_shot(text)
                    return max(scored, key=lambda p: p[1])
                except HFInferenceError as err:
                    if err.kind == HFErrorKind.QUOTA:
                        pytest.skip(f"HF credits/rate limit: {err}")
                    if err.transient and attempt < 2:
                        continue  # 502/503/timeouts from shared inference
                    raise

        return predict

    async def test_live_accuracy_above_90_percent(self):
        predict = self._live_classifier()
        correct = 0
        for text, expected in self._CASES:
            pred, conf = predict(text)
            if pred == expected:
                correct += 1
        accuracy = correct / len(self._CASES)
        assert accuracy >= 0.90, (
            f"Live model accuracy {accuracy:.0%} below 90% — "
            f"{correct}/{len(self._CASES)} correct"
        )

    async def test_live_high_confidence_on_clear_text(self):
        predict = self._live_classifier()
        _, conf = predict("I feel very anxious and overwhelmed about everything")
        assert conf >= 0.90, f"Expected confidence ≥ 0.90, got {conf:.3f}"
