"""
Phase T5-C tests — Emotionally Adaptive AI Tone.

Tests the tone_adapter service and its integration with the /ask and /chat
therapy endpoints.

Test groups:
  1. get_severity() — correct tier for every emotion + confidence combination
  2. get_tone_profile() — correct ToneProfile fields returned
  3. tone_directive() — correct language selection
  4. Integration: /ask returns correct tone_profile label
  5. Integration: /chat returns correct tone_profile label
  6. RAG pipeline build_user_prompt tone injection

Test count: 26 tests
"""
import asyncio

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
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
# 1. get_severity()
# ===========================================================================

class TestGetSeverity:
    async def test_hopelessness_always_distress(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("hopelessness", 0.0) == EmotionSeverity.DISTRESS

    async def test_hopelessness_high_conf_still_distress(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("hopelessness", 0.99) == EmotionSeverity.DISTRESS

    async def test_grief_high_conf_is_distress(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("grief", 0.70) == EmotionSeverity.DISTRESS

    async def test_grief_low_conf_is_moderate(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("grief", 0.50) == EmotionSeverity.MODERATE

    async def test_fear_high_conf_is_distress(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("fear", 0.80) == EmotionSeverity.DISTRESS

    async def test_fear_keyword_fallback_is_moderate(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("fear", 0.0) == EmotionSeverity.MODERATE

    async def test_gratitude_is_positive(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("gratitude", 0.95) == EmotionSeverity.POSITIVE

    async def test_general_is_mild(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("general", 0.0) == EmotionSeverity.MILD

    async def test_empty_emotion_is_mild(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("", 0.0) == EmotionSeverity.MILD

    async def test_anxiety_is_moderate(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("anxiety", 0.92) == EmotionSeverity.MODERATE

    async def test_stress_is_moderate(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("stress", 0.85) == EmotionSeverity.MODERATE

    async def test_doubt_is_moderate(self):
        from app.services.tone_adapter import get_severity, EmotionSeverity
        assert get_severity("doubt", 0.78) == EmotionSeverity.MODERATE


# ===========================================================================
# 2. get_tone_profile()
# ===========================================================================

class TestGetToneProfile:
    async def test_distress_profile_label(self):
        from app.services.tone_adapter import get_tone_profile
        profile = get_tone_profile("hopelessness", 0.0)
        assert profile.label == "gentle"

    async def test_moderate_profile_label(self):
        from app.services.tone_adapter import get_tone_profile
        profile = get_tone_profile("anxiety", 0.90)
        assert profile.label == "supportive"

    async def test_positive_profile_label(self):
        from app.services.tone_adapter import get_tone_profile
        profile = get_tone_profile("gratitude", 0.95)
        assert profile.label == "celebratory"

    async def test_mild_profile_label(self):
        from app.services.tone_adapter import get_tone_profile
        profile = get_tone_profile("general", 0.0)
        assert profile.label == "welcoming"

    async def test_all_profiles_have_both_directives(self):
        from app.services.tone_adapter import get_tone_profile
        for emotion, conf in [
            ("hopelessness", 0.0), ("grief", 0.80), ("anxiety", 0.85),
            ("gratitude", 0.95), ("general", 0.0),
        ]:
            p = get_tone_profile(emotion, conf)
            assert p.directive_en
            assert p.directive_ar
            assert "TONE INSTRUCTION" in p.directive_en
            assert "تعليمات النبرة" in p.directive_ar


# ===========================================================================
# 3. tone_directive() language selection
# ===========================================================================

class TestToneDirective:
    async def test_english_returns_en_directive(self):
        from app.services.tone_adapter import tone_directive
        d = tone_directive("anxiety", 0.85, "en")
        assert "TONE INSTRUCTION" in d
        assert "تعليمات" not in d

    async def test_arabic_returns_ar_directive(self):
        from app.services.tone_adapter import tone_directive
        d = tone_directive("anxiety", 0.85, "ar")
        assert "تعليمات النبرة" in d
        assert "TONE INSTRUCTION" not in d

    async def test_unknown_language_returns_en(self):
        from app.services.tone_adapter import tone_directive
        d = tone_directive("anxiety", 0.85, "fr")
        assert "TONE INSTRUCTION" in d


# ===========================================================================
# 4. /ask endpoint — tone_profile field
# ===========================================================================

class TestAskToneProfile:
    _ids: list[str] = []

    async def test_hopelessness_returns_gentle(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel completely hopeless", "emotion_override": "hopelessness"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "gentle"

    async def test_gratitude_returns_celebratory(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I am so grateful today", "emotion_override": "gratitude"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "celebratory"

    async def test_general_returns_welcoming(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I need some guidance today", "emotion_override": "general"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "welcoming"

    async def test_anxiety_returns_supportive(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel anxious", "emotion_override": "anxiety"},
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "supportive"

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 5. /chat endpoint — tone_profile field
# ===========================================================================

class TestChatToneProfile:
    _ids: list[str] = []

    async def test_chat_grief_override_returns_gentle_when_high_conf(self, client):
        """emotion_override = grief → confidence = 1.0 ≥ 0.65 → distress → gentle."""
        r = await client.post(
            "/api/v1/therapy/chat",
            json={
                "message": "I am grieving",
                "language": "en",
                "emotion_override": "grief",
            },
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "gentle"

    async def test_chat_gratitude_returns_celebratory(self, client):
        r = await client.post(
            "/api/v1/therapy/chat",
            json={
                "message": "Alhamdulillah I feel so blessed",
                "language": "en",
                "emotion_override": "gratitude",
            },
        )
        assert r.status_code == 200
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["tone_profile"] == "celebratory"

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 6. RAG prompt injection — build_user_prompt includes tone directive
# ===========================================================================

class TestBuildUserPromptToneInjection:
    async def test_tone_directive_appears_in_prompt(self):
        from app.rag.prompts import build_user_prompt
        prompt = build_user_prompt(
            question="How does the Quran address grief?",
            context="[source context here]",
            language="en",
            include_scholarly_debate=False,
            is_fiqh=False,
            tone_directive="TONE INSTRUCTION: Lead with unconditional presence.",
        )
        assert "TONE INSTRUCTION: Lead with unconditional presence." in prompt

    async def test_empty_tone_directive_leaves_no_artifact(self):
        from app.rag.prompts import build_user_prompt
        prompt = build_user_prompt(
            question="What is tawakkul?",
            context="[source]",
            language="en",
            include_scholarly_debate=False,
            is_fiqh=False,
            tone_directive="",
        )
        assert "TONE INSTRUCTION" not in prompt

    async def test_arabic_tone_directive_appears_in_arabic_prompt(self):
        from app.rag.prompts import build_user_prompt
        arabic_directive = "تعليمات النبرة: ابدأ بالحضور الكامل."
        prompt = build_user_prompt(
            question="كيف يتحدث القرآن عن الحزن؟",
            context="[مصادر]",
            language="ar",
            include_scholarly_debate=False,
            is_fiqh=False,
            tone_directive=arabic_directive,
        )
        assert arabic_directive in prompt
