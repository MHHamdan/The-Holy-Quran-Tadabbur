"""
Phase T4 tests — NLI Emotion Classifier.

Tests the NLIEmotionClassifier service and its integration with
classify_emotion() in spiritual_guidance_service.py.

Test groups:
  1. Unit tests for NLIEmotionClassifier (mocked torch / transformers)
  2. is_arabic_dominant() language detection utility
  3. classify_emotion() integration — NLI path, Arabic path, fallback path
  4. API integration — /ask returns emotion_confidence field
  5. Live model smoke tests (skipped when model not loaded to keep CI fast)

Test count: 32 tests
"""
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

_DB_URL = "postgresql+asyncpg://tadabbur:tadabbur_dev@localhost:5432/tadabbur"


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
    """Unit tests using a mocked torch model and tokenizer."""

    def _make_mock_model(self, best_label_idx: int = 0, confidence: float = 0.99):
        """Build a mock model that returns high entailment for the given label index."""
        import torch

        # Build fake logits: entailment (col 2) high for best_label_idx
        n_labels = 11
        logits_data = [[0.0, 0.1, 0.1]] * n_labels
        # Entailment score artificially boosted for best_label_idx
        logits_data[best_label_idx] = [0.01, 0.01, 5.0]

        mock_output = MagicMock()
        mock_output.logits = torch.tensor(logits_data, dtype=torch.float32)

        mock_model = MagicMock()
        mock_model.return_value = mock_output
        mock_model.eval = MagicMock(return_value=mock_model)
        mock_model.to = MagicMock(return_value=mock_model)
        return mock_model

    def _make_mock_tokenizer(self):
        import torch
        mock_tok = MagicMock()
        # Return a fake batch encoding that has a .to() method
        fake_enc = MagicMock()
        fake_enc.to = MagicMock(return_value={
            "input_ids": torch.zeros(11, 5, dtype=torch.long),
            "attention_mask": torch.ones(11, 5, dtype=torch.long),
        })
        mock_tok.return_value = fake_enc
        return mock_tok

    def test_classify_returns_correct_emotion(self):
        from app.services.emotion_classifier import NLIEmotionClassifier, EMOTION_LABELS
        clf = NLIEmotionClassifier(confidence_threshold=0.4)

        mock_model = self._make_mock_model(best_label_idx=0)  # EMOTION_LABELS[0] = 'anxiety'
        mock_tok = self._make_mock_tokenizer()

        with (
            patch("app.services.emotion_classifier.os.environ", {"USE_TF": "0"}),
            patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tok),
            patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        ):
            clf._load()  # force load with mocked model
            emotion, confidence = clf.classify("I feel anxious today")

        assert emotion == EMOTION_LABELS[0]
        assert confidence > 0.4

    def test_classify_returns_empty_when_below_threshold(self):
        """When all entailment scores are low, returns ('', low_conf)."""
        import torch
        from app.services.emotion_classifier import NLIEmotionClassifier

        n = 11
        low_logits = torch.tensor([[0.1, 0.1, 0.1]] * n, dtype=torch.float32)
        mock_output = MagicMock()
        mock_output.logits = low_logits

        mock_model = MagicMock()
        mock_model.return_value = mock_output
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_tok = self._make_mock_tokenizer()

        clf = NLIEmotionClassifier(confidence_threshold=0.9)  # very high threshold
        with (
            patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tok),
            patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        ):
            clf._load()
            emotion, confidence = clf.classify("I feel somewhat off today")

        assert emotion == ""

    def test_load_failure_returns_empty(self):
        """Model load failure must return ('', 0.0) gracefully."""
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier(model_name="nonexistent-model-xyz")
        with patch("transformers.AutoTokenizer.from_pretrained", side_effect=OSError("not found")):
            emotion, confidence = clf.classify("I feel anxious today")

        assert emotion == ""
        assert confidence == 0.0
        assert not clf.is_ready

    def test_warmup_returns_true_on_success(self):
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier()
        mock_model = self._make_mock_model()
        mock_tok = self._make_mock_tokenizer()

        with (
            patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tok),
            patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        ):
            ok = clf.warmup()

        assert ok is True
        assert clf.is_ready

    def test_warmup_returns_false_on_failure(self):
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier(model_name="bad-model")
        with patch("transformers.AutoTokenizer.from_pretrained", side_effect=ValueError("bad")):
            ok = clf.warmup()

        assert ok is False
        assert not clf.is_ready

    def test_double_load_only_calls_from_pretrained_once(self):
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier()
        mock_model = self._make_mock_model()
        mock_tok = self._make_mock_tokenizer()

        with (
            patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tok) as mock_tok_call,
            patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        ):
            clf._load()
            clf._load()  # second call should be a no-op

        assert mock_tok_call.call_count == 1

    def test_inference_error_returns_empty(self):
        from app.services.emotion_classifier import NLIEmotionClassifier

        clf = NLIEmotionClassifier()
        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_model.side_effect = RuntimeError("GPU OOM")

        mock_tok = self._make_mock_tokenizer()

        with (
            patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tok),
            patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        ):
            clf._load()
            emotion, confidence = clf.classify("I feel anxious")

        assert emotion == ""


# ===========================================================================
# 2. Arabic detection utility
# ===========================================================================

class TestArabicDetection:
    def test_arabic_text_is_detected(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert is_arabic_dominant("أشعر بالقلق الشديد")

    def test_english_text_not_arabic(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert not is_arabic_dominant("I feel very anxious today")

    def test_mixed_text_below_threshold(self):
        from app.services.emotion_classifier import is_arabic_dominant
        # Short Arabic word in mostly English sentence
        assert not is_arabic_dominant("I feel قلق today but mostly English")

    def test_mixed_text_above_threshold(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert is_arabic_dominant("أشعر بالقلق الشديد وI feel worried")

    def test_empty_string_returns_false(self):
        from app.services.emotion_classifier import is_arabic_dominant
        assert not is_arabic_dominant("")

    def test_numbers_only_returns_false(self):
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

    def test_english_uses_nli_when_enabled(self):
        from app.services.spiritual_guidance_service import classify_emotion
        with self._mock_nli_result("grief"):
            result = classify_emotion("I am grieving the loss of my father")
        assert result == "grief"

    def test_arabic_bypasses_nli(self):
        """Arabic text routes directly to keyword classifier; NLI is not called."""
        from app.services.spiritual_guidance_service import classify_emotion
        mock_clf = MagicMock()
        with patch("app.services.emotion_classifier.get_classifier", return_value=mock_clf):
            result = classify_emotion("أشعر بالقلق الشديد")
        mock_clf.classify.assert_not_called()
        assert result in ["anxiety", "general"]

    def test_low_confidence_falls_back_to_keywords(self):
        from app.services.spiritual_guidance_service import classify_emotion
        mock_clf = MagicMock()
        mock_clf.classify.return_value = ("", 0.15)  # empty = below threshold
        with patch("app.services.emotion_classifier.get_classifier", return_value=mock_clf):
            result = classify_emotion("I feel very anxious and worried")
        assert result == "anxiety"

    def test_disabled_classifier_uses_keywords(self):
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

    def test_nli_general_falls_through_to_keywords(self):
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

@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_MODEL_TESTS") != "1",
    reason="Set RUN_LIVE_MODEL_TESTS=1 to run live model inference tests",
)
class TestLiveModelSmoke:
    """
    Smoke tests against the real facebook/bart-large-mnli model.
    Requires the model to be downloaded and RUN_LIVE_MODEL_TESTS=1.

    Run with:
        RUN_LIVE_MODEL_TESTS=1 pytest tests/unit/test_emotion_classifier_phase_t4.py::TestLiveModelSmoke -v
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

    def test_live_accuracy_above_90_percent(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        assert clf.warmup(), "Model failed to load"
        correct = 0
        for text, expected in self._CASES:
            pred, conf = clf.classify(text)
            if pred == expected:
                correct += 1
        accuracy = correct / len(self._CASES)
        assert accuracy >= 0.90, (
            f"Live model accuracy {accuracy:.0%} below 90% — "
            f"{correct}/{len(self._CASES)} correct"
        )

    def test_live_high_confidence_on_clear_text(self):
        from app.services.emotion_classifier import NLIEmotionClassifier
        clf = NLIEmotionClassifier()
        clf.warmup()
        _, conf = clf.classify("I feel very anxious and overwhelmed about everything")
        assert conf >= 0.90, f"Expected confidence ≥ 0.90, got {conf:.3f}"
