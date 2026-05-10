"""
Phase T5-D — Reflection Journal & T5-A Arabic keyword expansion tests.

Coverage:
  - /ask returns reflection_prompt_en/ar for every emotion (dict-level)
  - _REFLECTION_PROMPTS covers all 12 emotions with bilingual content
  - Distress-tier empathy dict covers hopelessness/grief/fear
  - _EMPATHY_DISTRESS provides bilingual deeper empathy for DISTRESS emotions
  - Tone severity rules for distress/moderate/positive/mild
  - /reflections endpoint: rejects empty ids, returns records from DB
  - ReflectionRecord model structure
  - Arabic keyword expansion: T5-A colloquial/Islamic terms present
"""
import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.rate_limit import therapy_rate_limit

pytestmark = pytest.mark.asyncio(loop_scope="module")

_DB_URL = "postgresql+asyncpg://tadabbur:tadabbur_dev@localhost:5432/tadabbur"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


@pytest_asyncio.fixture(scope="function")
async def fclient():
    """Function-scoped client for tests that write to DB, to prevent event-loop leaks."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ===========================================================================
# TestReflectionPromptInAskResponse
# ===========================================================================

class TestReflectionPromptInAskResponse:
    """Verify _REFLECTION_PROMPTS covers every emotion with bilingual content."""

    EMOTIONS = [
        "anxiety", "sadness", "grief", "fear", "loneliness",
        "hopelessness", "anger", "stress", "guilt", "doubt",
        "gratitude", "general",
    ]

    @pytest.mark.parametrize("emotion", EMOTIONS)
    def test_reflection_prompt_present_for_emotion(self, emotion):
        from app.api.routes.therapy import _REFLECTION_PROMPTS, EmotionCategory
        key = getattr(EmotionCategory, emotion.upper(), EmotionCategory.GENERAL)
        prompts = _REFLECTION_PROMPTS.get(key, _REFLECTION_PROMPTS[EmotionCategory.GENERAL])
        assert prompts["en"], f"Missing EN reflection prompt for {emotion}"
        assert prompts["ar"], f"Missing AR reflection prompt for {emotion}"

    def test_all_12_emotions_covered(self):
        from app.api.routes.therapy import _REFLECTION_PROMPTS, EmotionCategory
        missing = []
        for emotion in self.EMOTIONS:
            key = getattr(EmotionCategory, emotion.upper(), None)
            if key and key not in _REFLECTION_PROMPTS:
                missing.append(emotion)
        assert not missing, f"Emotions missing from _REFLECTION_PROMPTS: {missing}"

    def test_reflection_prompts_bilingual(self):
        from app.api.routes.therapy import _REFLECTION_PROMPTS
        for emotion_key, prompts in _REFLECTION_PROMPTS.items():
            assert "en" in prompts, f"{emotion_key} missing EN prompt"
            assert "ar" in prompts, f"{emotion_key} missing AR prompt"
            assert len(prompts["en"]) > 20, f"{emotion_key} EN prompt too short"
            assert len(prompts["ar"]) > 10, f"{emotion_key} AR prompt too short"


# ===========================================================================
# TestDistressEmpathySelection
# ===========================================================================

class TestDistressEmpathySelection:
    """Verify severity-aware empathy selection (T5-C improvement)."""

    def test_distress_dict_covers_hopelessness_grief_fear(self):
        from app.api.routes.therapy import _EMPATHY_DISTRESS, EmotionCategory
        for emotion in [EmotionCategory.HOPELESSNESS, EmotionCategory.GRIEF, EmotionCategory.FEAR]:
            assert emotion in _EMPATHY_DISTRESS, f"{emotion} missing from _EMPATHY_DISTRESS"

    def test_distress_empathy_bilingual(self):
        from app.api.routes.therapy import _EMPATHY_DISTRESS
        for emotion_key, texts in _EMPATHY_DISTRESS.items():
            assert "en" in texts and "ar" in texts
            assert len(texts["en"]) > 30, f"{emotion_key} DISTRESS EN empathy too short"
            assert len(texts["ar"]) > 20, f"{emotion_key} DISTRESS AR empathy too short"

    def test_hopelessness_always_distress_severity(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("hopelessness", 0.0) == EmotionSeverity.DISTRESS
        assert get_severity("hopelessness", 1.0) == EmotionSeverity.DISTRESS

    def test_grief_distress_above_threshold(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("grief", 0.70) == EmotionSeverity.DISTRESS

    def test_grief_moderate_below_threshold(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("grief", 0.50) == EmotionSeverity.MODERATE

    def test_fear_distress_above_threshold(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("fear", 0.80) == EmotionSeverity.DISTRESS

    def test_fear_moderate_below_threshold(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("fear", 0.40) == EmotionSeverity.MODERATE

    def test_anxiety_never_distress(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("anxiety", 0.99) == EmotionSeverity.MODERATE

    def test_gratitude_always_positive(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("gratitude", 0.90) == EmotionSeverity.POSITIVE

    def test_general_always_mild(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("general", 0.99) == EmotionSeverity.MILD


# ===========================================================================
# TestReflectionsEndpoint
# ===========================================================================

class TestReflectionsEndpoint:
    """POST /therapy/reflections — retrieve saved reflections by session_ids."""

    async def test_empty_session_ids_rejected(self, fclient):
        resp = await fclient.post("/api/v1/therapy/reflections", json={"session_ids": []})
        assert resp.status_code == 422

    async def test_nonexistent_ids_return_empty(self, fclient):
        fake_id = str(uuid.uuid4())
        resp = await fclient.post("/api/v1/therapy/reflections", json={"session_ids": [fake_id]})
        assert resp.status_code == 200
        assert resp.json()["reflections"] == []

    async def test_returns_records_after_ask_and_save(self, fclient):
        ask_resp = await fclient.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel so anxious about everything", "emotion_override": "anxiety"},
        )
        assert ask_resp.status_code == 200
        sid = ask_resp.json()["session_id"]

        save_resp = await fclient.post(
            "/api/v1/therapy/reflect",
            json={"session_id": sid, "reflection": "Writing helps me calm down"},
        )
        assert save_resp.status_code == 200

        refl_resp = await fclient.post(
            "/api/v1/therapy/reflections",
            json={"session_ids": [sid]},
        )
        assert refl_resp.status_code == 200
        data = refl_resp.json()
        assert len(data["reflections"]) == 1
        rec = data["reflections"][0]
        assert rec["session_id"] == sid
        assert rec["emotion"] == "anxiety"
        assert rec["reflection"] == "Writing helps me calm down"

    async def test_record_includes_label_and_timestamp(self, fclient):
        ask_resp = await fclient.post(
            "/api/v1/therapy/ask",
            json={"message": "I am grieving", "emotion_override": "grief"},
        )
        assert ask_resp.status_code == 200
        sid = ask_resp.json()["session_id"]

        await fclient.post(
            "/api/v1/therapy/reflect",
            json={"session_id": sid, "reflection": "Feeling the loss"},
        )
        refl_resp = await fclient.post(
            "/api/v1/therapy/reflections",
            json={"session_ids": [sid]},
        )
        rec = refl_resp.json()["reflections"][0]
        assert "label_en" in rec and rec["label_en"]
        assert "label_ar" in rec and rec["label_ar"]
        # timestamp must be ISO-parseable
        datetime.fromisoformat(rec["timestamp"])

    async def test_sessions_without_reflection_excluded(self, fclient):
        ask_resp = await fclient.post(
            "/api/v1/therapy/ask",
            json={"message": "Just browsing", "emotion_override": "general"},
        )
        assert ask_resp.status_code == 200
        sid = ask_resp.json()["session_id"]

        refl_resp = await fclient.post(
            "/api/v1/therapy/reflections",
            json={"session_ids": [sid]},
        )
        assert refl_resp.status_code == 200
        assert refl_resp.json()["reflections"] == []

    async def test_exactly_200_ids_accepted(self, fclient):
        ids = [str(uuid.uuid4()) for _ in range(200)]
        resp = await fclient.post("/api/v1/therapy/reflections", json={"session_ids": ids})
        assert resp.status_code == 200
        assert resp.json()["reflections"] == []


# ===========================================================================
# TestArabicKeywordExpansion (T5-A)
# ===========================================================================

class TestArabicKeywordExpansion:
    """Verify T5-A Arabic keyword expansion in _EMOTION_KEYWORDS."""

    def _get_keywords(self):
        from app.services.spiritual_guidance_service import _EMOTION_KEYWORDS
        return _EMOTION_KEYWORDS

    def test_anxiety_has_colloquial_terms(self):
        kw = self._get_keywords()
        anxiety_kws = " ".join(kw.get("anxiety", []))
        assert "قلقان" in anxiety_kws or "متوتر" in anxiety_kws

    def test_anxiety_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("anxiety", [])) >= 10, "anxiety should have ≥10 Arabic keywords"

    def test_hopelessness_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("hopelessness", [])) >= 8

    def test_grief_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("grief", [])) >= 8

    def test_sadness_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("sadness", [])) >= 8

    def test_fear_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("fear", [])) >= 8

    def test_loneliness_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("loneliness", [])) >= 8

    def test_anger_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("anger", [])) >= 8

    def test_stress_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("stress", [])) >= 8

    def test_guilt_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("guilt", [])) >= 8

    def test_doubt_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("doubt", [])) >= 8

    def test_gratitude_has_minimum_keywords(self):
        kw = self._get_keywords()
        assert len(kw.get("gratitude", [])) >= 8

    def test_hopelessness_has_islamic_term(self):
        kw = self._get_keywords()
        hopeless_kws = " ".join(kw.get("hopelessness", []))
        # Should contain يأس or قنوط (classic Islamic term for hopelessness)
        assert "يأس" in hopeless_kws or "قنوط" in hopeless_kws

    def test_gratitude_has_shukr_variant(self):
        kw = self._get_keywords()
        gratitude_kws = " ".join(kw.get("gratitude", []))
        assert "شكر" in gratitude_kws or "امتنان" in gratitude_kws

    def test_all_core_emotions_present_in_keywords(self):
        kw = self._get_keywords()
        core = ["anxiety", "sadness", "grief", "fear", "loneliness",
                "hopelessness", "anger", "stress", "guilt", "doubt", "gratitude"]
        missing = [e for e in core if e not in kw]
        assert not missing, f"Missing from _EMOTION_KEYWORDS: {missing}"

    def test_each_emotion_has_arabic_terms(self):
        kw = self._get_keywords()
        # At least half the terms per emotion should be Arabic script
        for emotion, terms in kw.items():
            arabic_count = sum(
                1 for t in terms if any('؀' <= c <= 'ۿ' for c in t)
            )
            assert arabic_count >= len(terms) // 2, (
                f"{emotion}: only {arabic_count}/{len(terms)} terms are Arabic"
            )
