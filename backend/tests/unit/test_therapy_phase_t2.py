"""
Phase T2 tests — QuranGPT Chat, Positive Reinforcement, Insights Dashboard.

New endpoints:
  POST /api/v1/therapy/chat     — RAG-grounded conversational mode (with fallback)
  POST /api/v1/therapy/insights — emotional journey stats
  POST /api/v1/therapy/ask      — now returns reinforcement_en / reinforcement_ar

Test count: 28 tests
"""
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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


# ---------------------------------------------------------------------------
# Mock RAG result — replicates the GroundedResponse that pipeline.query returns
# ---------------------------------------------------------------------------

def _make_rag_result(emotion: str = "anxiety", language: str = "en") -> MagicMock:
    citation = MagicMock()
    citation.source_id = "tafsir_ibn_kathir"
    citation.source_name = "Tafsir Ibn Kathir"
    citation.verse_reference = "2:286"
    citation.excerpt = "Allah does not burden a soul beyond that it can bear."

    rv = MagicMock()
    rv.verse_reference = "2:286"

    result = MagicMock()
    result.answer = (
        "The Quran offers profound guidance for those experiencing anxiety. "
        "Allah (SWT) reminds us in Surah Al-Baqarah (2:286) that He does not "
        "burden a soul beyond its capacity."
    ) if language == "en" else (
        "يقدم القرآن الكريم توجيهاً عميقاً لمن يعاني من القلق."
    )
    result.answer_language = language
    result.citations = [citation]
    result.related_verses = [rv]
    result.follow_up_suggestions = [
        "Would you like to explore verses on tawakkul?",
        "Shall we look at Surah Ad-Duha?",
    ]
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
# 1. Reinforcement messages in /ask (Phase T2 addition)
# ===========================================================================

class TestAskReinforcement:
    async def test_reinforcement_fields_present(self, client):
        data = await _ask(client)
        assert "reinforcement_en" in data
        assert "reinforcement_ar" in data

    async def test_reinforcement_non_empty_for_anxiety(self, client):
        data = await _ask(client, "I cannot stop worrying")
        assert len(data["reinforcement_en"]) > 10
        assert len(data["reinforcement_ar"]) > 10

    async def test_reinforcement_non_empty_for_sadness(self, client):
        data = await _ask(client, "I feel so sad and hopeless about everything")
        assert len(data["reinforcement_en"]) > 10
        assert len(data["reinforcement_ar"]) > 10

    async def test_reinforcement_non_empty_for_gratitude(self, client):
        data = await _ask(client, "I am so thankful for all the blessings in my life")
        assert len(data["reinforcement_en"]) > 10

    async def test_reinforcement_non_empty_for_general(self, client):
        data = await _ask(client, "I just need some guidance today")
        assert len(data["reinforcement_en"]) > 10

    async def test_reinforcement_en_no_arabic_script(self, client):
        data = await _ask(client)
        for ch in data["reinforcement_en"]:
            assert not ('؀' <= ch <= 'ۿ'), f"Arabic char in EN reinforcement: {ch}"

    async def test_reinforcement_ar_no_latin_words(self, client):
        import re
        data = await _ask(client, "I feel afraid")
        words = re.findall(r'[A-Za-z]{3,}', data["reinforcement_ar"])
        assert words == [], f"Latin words in AR reinforcement: {words}"

    async def test_reinforcement_distinct_per_emotion(self, client):
        anxiety_data = await _ask(client, "I feel very anxious all the time")
        grief_data = await _ask(client, "I am grieving the loss of someone I loved dearly")
        assert anxiety_data["reinforcement_en"] != grief_data["reinforcement_en"]

    async def teardown_class(self):
        await _clean_sessions(_ALL_SESSIONS)


# ===========================================================================
# 2. POST /chat — RAG path (mocked) and validation
# ===========================================================================

class TestChatFallback:
    _ids: list[str] = []

    @staticmethod
    def _rag_patches(result: Any = None):
        """Context manager that enables the RAG path and mocks the pipeline."""
        import contextlib

        @contextlib.asynccontextmanager
        async def _ctx():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_hc = AsyncMock()
            mock_hc.__aenter__ = AsyncMock(return_value=mock_hc)
            mock_hc.__aexit__ = AsyncMock(return_value=False)
            mock_hc.get = AsyncMock(return_value=mock_resp)

            rag_result = result or _make_rag_result()
            mock_inst = AsyncMock()
            mock_inst.query = AsyncMock(return_value=rag_result)

            # Patch httpx at the module level (import inside the function uses module-level httpx)
            with (
                patch("app.rag.pipeline.RAGPipeline", return_value=mock_inst),
                patch("httpx.AsyncClient", return_value=mock_hc),
            ):
                yield

        return _ctx()

    async def test_chat_returns_200(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel lost today"})
        assert r.status_code == 200

    async def test_chat_response_structure(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel lost today"})
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["ok"] is True
        for key in ("session_id", "emotion", "emotion_label_en", "emotion_label_ar",
                    "answer", "answer_language", "citations", "fallback_cards",
                    "used_rag", "disclaimer_en", "disclaimer_ar"):
            assert key in data, f"Missing key: {key}"

    async def test_chat_rag_used_when_available(self, client):
        async with self._rag_patches():
            r = await client.post(
                "/api/v1/therapy/chat",
                json={"message": "I feel anxious about the future"},
            )
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["used_rag"] is True
        assert isinstance(data["citations"], list)

    async def test_chat_answer_non_empty(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel very alone in this world"})
        data = r.json()
        self._ids.append(data["session_id"])
        assert len(data["answer"]) > 10

    async def test_chat_emotion_classified(self, client):
        async with self._rag_patches(_make_rag_result("sadness")):
            r = await client.post(
                "/api/v1/therapy/chat",
                json={"message": "I feel very sad and cannot stop crying"},
            )
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["emotion"] in ["sadness", "grief", "hopelessness", "general"]

    async def test_chat_emotion_override(self, client):
        async with self._rag_patches(_make_rag_result("fear")):
            r = await client.post(
                "/api/v1/therapy/chat",
                json={"message": "some spiritual message here", "emotion_override": "fear"},
            )
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["emotion"] == "fear"

    async def test_chat_language_ar(self, client):
        async with self._rag_patches(_make_rag_result(language="ar")):
            r = await client.post(
                "/api/v1/therapy/chat",
                json={"message": "أشعر بالقلق الشديد اليوم", "language": "ar"},
            )
        data = r.json()
        self._ids.append(data["session_id"])
        assert r.status_code == 200
        assert data["answer_language"] == "ar"

    async def test_chat_rag_exception_falls_back_gracefully(self, client):
        # Make health check succeed so RAG path is taken, then have query raise
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_hc = AsyncMock()
        mock_hc.__aenter__ = AsyncMock(return_value=mock_hc)
        mock_hc.__aexit__ = AsyncMock(return_value=False)
        mock_hc.get = AsyncMock(return_value=mock_resp)

        broken_inst = AsyncMock()
        broken_inst.query = AsyncMock(side_effect=RuntimeError("LLM unreachable"))

        with (
            patch("app.rag.pipeline.RAGPipeline", return_value=broken_inst),
            patch("httpx.AsyncClient", return_value=mock_hc),
        ):
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel a lot of stress today"})
        data = r.json()
        self._ids.append(data["session_id"])
        assert r.status_code == 200
        assert data["ok"] is True
        assert data["used_rag"] is False
        assert len(data["answer"]) > 5

    async def test_chat_citations_structure(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel overwhelmed by grief today"})
        data = r.json()
        self._ids.append(data["session_id"])
        if data["citations"]:
            c = data["citations"][0]
            for field in ("source_id", "source_name", "verse_reference", "excerpt"):
                assert field in c

    async def test_chat_follow_up_suggestions_list(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I feel fearful about the future"})
        data = r.json()
        self._ids.append(data["session_id"])
        assert isinstance(data["follow_up_suggestions"], list)

    async def test_chat_session_id_provided_reused(self, client):
        prior_sid = str(uuid.uuid4())
        async with self._rag_patches():
            r = await client.post(
                "/api/v1/therapy/chat",
                json={"message": "Tell me more about patience please", "session_id": prior_sid},
            )
        data = r.json()
        self._ids.append(data["session_id"])
        assert data["session_id"] == prior_sid

    async def test_chat_invalid_emotion_override_422(self, client):
        r = await client.post(
            "/api/v1/therapy/chat",
            json={"message": "hello there friend", "emotion_override": "INVALID_EMOTION"},
        )
        assert r.status_code == 422

    async def test_chat_message_too_short_422(self, client):
        r = await client.post("/api/v1/therapy/chat", json={"message": "hi"})
        assert r.status_code == 422

    async def test_chat_disclaimer_present(self, client):
        async with self._rag_patches():
            r = await client.post("/api/v1/therapy/chat", json={"message": "I am feeling overwhelmed by everything"})
        data = r.json()
        self._ids.append(data["session_id"])
        assert len(data["disclaimer_en"]) > 20
        assert len(data["disclaimer_ar"]) > 20


# ===========================================================================
# 3. POST /insights — emotional journey dashboard
# ===========================================================================

class TestInsights:
    _ids: list[str] = []

    async def test_insights_empty_session_list_422(self, client):
        r = await client.post("/api/v1/therapy/insights", json={"session_ids": []})
        # min_length=1 validation on session_ids
        assert r.status_code == 422

    async def test_insights_unknown_sessions_zero_total(self, client):
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [str(uuid.uuid4()), str(uuid.uuid4())]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["total_sessions"] == 0
        assert data["emotion_distribution"] == []
        assert data["top_emotion"] is None

    async def test_insights_reflects_ask_sessions(self, client):
        d1 = await _ask(client, "I feel very anxious today")
        d2 = await _ask(client, "I am so sad about everything")
        d3 = await _ask(client, "I feel anxious again about the future")
        session_ids = [d1["session_id"], d2["session_id"], d3["session_id"]]
        self._ids.extend(session_ids)

        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": session_ids},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["total_sessions"] == 3

    async def test_insights_emotion_distribution_structure(self, client):
        d = await _ask(client, "I feel guilty about my past mistakes and failures")
        self._ids.append(d["session_id"])
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]]},
        )
        data = r.json()
        if data["emotion_distribution"]:
            item = data["emotion_distribution"][0]
            assert "emotion" in item
            assert "label_en" in item
            assert "label_ar" in item
            assert "count" in item
            assert isinstance(item["count"], int)

    async def test_insights_top_emotion_matches_distribution(self, client):
        d1 = await _ask(client, "fear overwhelms me completely")
        d2 = await _ask(client, "I am scared of what might happen")
        ids = [d1["session_id"], d2["session_id"]]
        self._ids.extend(ids)
        r = await client.post("/api/v1/therapy/insights", json={"session_ids": ids})
        data = r.json()
        if data["top_emotion"] and data["emotion_distribution"]:
            assert data["top_emotion"] == data["emotion_distribution"][0]["emotion"]

    async def test_insights_language_ar(self, client):
        d = await _ask(client, "I feel overwhelmed with sadness")
        self._ids.append(d["session_id"])
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]], "language": "ar"},
        )
        assert r.status_code == 200

    async def test_insights_response_schema(self, client):
        d = await _ask(client, "I feel overwhelmed by all this stress at work")
        self._ids.append(d["session_id"])
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [d["session_id"]]},
        )
        data = r.json()
        required_keys = {
            "ok", "total_sessions", "emotion_distribution",
            "streak_days", "top_emotion",
            "top_emotion_label_en", "top_emotion_label_ar",
        }
        assert required_keys.issubset(data.keys())

    async def teardown_class(self):
        await _clean_sessions(self._ids)
