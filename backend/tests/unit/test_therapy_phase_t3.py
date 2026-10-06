"""
Phase T3 tests — Personalization, Reinforcement Bank, Suggested Themes, Growth Prompts.

Covers:
  POST /api/v1/therapy/ask   — reinforcement_index cycling, previous_emotion callback,
                               suggested_theme, all 12 follow-up emotion sets
  POST /api/v1/therapy/insights — growth_prompt, suggested_next_theme

Test count: 27 tests
"""
import asyncio
import uuid
from unittest.mock import patch

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


_ALL_SESSIONS: list[str] = []


async def _ask(client: AsyncClient, message: str = "I feel anxious today", **extra) -> dict:
    r = await client.post(
        "/api/v1/therapy/ask",
        json={"message": message, "language": "en", **extra},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    _ALL_SESSIONS.append(data["session_id"])
    return data


# ===========================================================================
# 1. Reinforcement bank cycling
# ===========================================================================

class TestReinforcementBank:
    _ids: list[str] = []

    async def test_index_0_returns_first_alternative(self, client):
        d = await _ask(client, "I feel so anxious right now", reinforcement_index=0)
        self._ids.append(d["session_id"])
        assert len(d["reinforcement_en"]) > 10

    async def test_index_1_returns_different_message(self, client):
        d0 = await _ask(client, "I feel so anxious right now", reinforcement_index=0)
        d1 = await _ask(client, "I feel so anxious right now", reinforcement_index=1)
        self._ids += [d0["session_id"], d1["session_id"]]
        assert d0["reinforcement_en"] != d1["reinforcement_en"]

    async def test_index_2_returns_third_alternative(self, client):
        d0 = await _ask(client, "I feel so anxious right now", reinforcement_index=0)
        d2 = await _ask(client, "I feel so anxious right now", reinforcement_index=2)
        self._ids += [d0["session_id"], d2["session_id"]]
        assert d0["reinforcement_en"] != d2["reinforcement_en"]

    async def test_index_wraps_with_modulo(self, client):
        """index=3 should wrap to index=0 (bank size=3)."""
        d0 = await _ask(client, "I feel so anxious right now", reinforcement_index=0)
        d3 = await _ask(client, "I feel so anxious right now", reinforcement_index=3)
        self._ids += [d0["session_id"], d3["session_id"]]
        assert d0["reinforcement_en"] == d3["reinforcement_en"]

    async def test_index_9_is_valid(self, client):
        d = await _ask(client, "I feel very sad and lonely today", reinforcement_index=9)
        self._ids.append(d["session_id"])
        assert len(d["reinforcement_en"]) > 10

    async def test_index_10_is_rejected_422(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel anxious", "reinforcement_index": 10},
        )
        assert r.status_code == 422

    async def test_negative_index_is_rejected_422(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel anxious", "reinforcement_index": -1},
        )
        assert r.status_code == 422

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 2. Personalization callback note
# ===========================================================================

class TestPersonalizationNote:
    _ids: list[str] = []

    async def test_no_previous_emotion_no_note(self, client):
        d = await _ask(client, "I feel anxious today")
        self._ids.append(d["session_id"])
        assert d.get("personalization_note_en") is None

    async def test_same_previous_emotion_triggers_note(self, client):
        d = await _ask(
            client,
            "I feel anxious today again",
            previous_emotion="anxiety",
            emotion_override="anxiety",
        )
        self._ids.append(d["session_id"])
        assert d.get("personalization_note_en") is not None
        assert len(d["personalization_note_en"]) > 10

    async def test_same_emotion_note_bilingual(self, client):
        d = await _ask(
            client,
            "I feel sad again today",
            previous_emotion="sadness",
            emotion_override="sadness",
        )
        self._ids.append(d["session_id"])
        assert d.get("personalization_note_ar") is not None
        assert len(d["personalization_note_ar"]) > 10

    async def test_different_previous_emotion_no_note(self, client):
        """previous_emotion=anxiety but current is sadness — no callback note."""
        d = await _ask(
            client,
            "I feel deeply sorrowful and grieving",
            previous_emotion="anxiety",
            emotion_override="sadness",
        )
        self._ids.append(d["session_id"])
        assert d.get("personalization_note_en") is None

    async def test_invalid_previous_emotion_rejected(self, client):
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": "I feel anxious", "previous_emotion": "NOTAEMOTION"},
        )
        assert r.status_code == 422

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 3. Suggested theme in AskResponse
# ===========================================================================

class TestSuggestedTheme:
    _ids: list[str] = []

    async def test_suggested_theme_present(self, client):
        d = await _ask(client, "I feel very anxious about everything today")
        self._ids.append(d["session_id"])
        assert d.get("suggested_theme") is not None

    async def test_anxiety_suggests_trust(self, client):
        d = await _ask(client, "I cannot stop worrying about the future", emotion_override="anxiety")
        self._ids.append(d["session_id"])
        assert d["suggested_theme"] == "trust"

    async def test_sadness_suggests_hope(self, client):
        d = await _ask(client, "I feel so deeply sad about everything", emotion_override="sadness")
        self._ids.append(d["session_id"])
        assert d["suggested_theme"] == "hope"

    async def test_anger_suggests_forgiveness(self, client):
        d = await _ask(client, "I am furious and cannot let it go", emotion_override="anger")
        self._ids.append(d["session_id"])
        assert d["suggested_theme"] == "forgiveness"

    async def test_suggested_theme_reason_bilingual(self, client):
        d = await _ask(client, "I feel so lost and fearful", emotion_override="fear")
        self._ids.append(d["session_id"])
        assert d.get("suggested_theme_reason_en") is not None
        assert d.get("suggested_theme_reason_ar") is not None
        assert len(d["suggested_theme_reason_en"]) > 10
        assert len(d["suggested_theme_reason_ar"]) > 10

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 4. Follow-up prompts for all 12 emotions
# ===========================================================================

class TestFollowUpsAllEmotions:
    _ids: list[str] = []

    _EMOTION_MESSAGES = {
        "anxiety":      "I am overwhelmed by constant worry and anxiety",
        "sadness":      "I feel very deeply sad and cannot find joy",
        "grief":        "I am grieving the loss of someone I loved deeply",
        "fear":         "I am paralysed with fear about what might happen",
        "loneliness":   "I feel completely alone and isolated from everyone",
        "hopelessness": "I have lost all hope and see no way forward",
        "anger":        "I am burning with rage and cannot calm down",
        "stress":       "I am under enormous pressure and cannot cope",
        "guilt":        "I feel consumed by guilt about my past actions",
        "doubt":        "I am filled with doubt and questions about everything",
        "gratitude":    "I am deeply grateful for all the blessings in my life",
        "general":      "I just need some spiritual guidance today",
    }

    async def test_all_emotions_have_follow_ups(self, client):
        for emotion, message in self._EMOTION_MESSAGES.items():
            d = await _ask(client, message, emotion_override=emotion)
            self._ids.append(d["session_id"])
            assert len(d["follow_up_prompts_en"]) >= 1, f"No follow-up for emotion: {emotion}"
            assert len(d["follow_up_prompts_ar"]) >= 1, f"No AR follow-up for emotion: {emotion}"

    async def test_follow_ups_are_strings(self, client):
        d = await _ask(client, "I am stressed and overwhelmed", emotion_override="stress")
        self._ids.append(d["session_id"])
        for prompt in d["follow_up_prompts_en"]:
            assert isinstance(prompt, str) and len(prompt) > 5

    async def teardown_class(self):
        await _clean_sessions(self._ids)


# ===========================================================================
# 5. Growth prompts in Insights
# ===========================================================================

class TestGrowthPrompts:
    _ids: list[str] = []

    async def test_growth_prompt_present_when_sessions_exist(self, client):
        d = await _ask(client, "I feel very anxious today", emotion_override="anxiety")
        self._ids.append(d["session_id"])

        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["growth_prompt_en"] is not None
        assert len(data["growth_prompt_en"]) > 10

    async def test_growth_prompt_bilingual(self, client):
        d = await _ask(client, "I feel grief-stricken today", emotion_override="grief")
        self._ids.append(d["session_id"])

        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]]},
        )
        data = r.json()
        assert data["growth_prompt_ar"] is not None
        assert len(data["growth_prompt_ar"]) > 10

    async def test_suggested_next_theme_present(self, client):
        d = await _ask(client, "I feel hopeless about the future", emotion_override="hopelessness")
        self._ids.append(d["session_id"])

        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]]},
        )
        data = r.json()
        assert data["suggested_next_theme"] is not None
        assert data["suggested_next_theme"] == "hope"

    async def test_no_growth_prompt_when_no_sessions(self, client):
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [str(uuid.uuid4())]},
        )
        data = r.json()
        assert data["total_sessions"] == 0
        assert data["growth_prompt_en"] is None
        assert data["suggested_next_theme"] is None

    async def teardown_class(self):
        await _clean_sessions(self._ids)
