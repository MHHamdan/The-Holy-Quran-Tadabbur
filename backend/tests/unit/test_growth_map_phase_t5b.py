"""
Phase T5-B tests — Emotional Growth Map.

Tests the growth-map helpers and the /insights endpoint's new fields:
  emotion_timeline, trend, streak_days.

Test groups:
  1. _compute_trend()  — trend derivation from emotion sequences
  2. _compute_streak() — consecutive-day streak logic
  3. API integration  — /insights returns timeline + trend + streak

Test count: 18 tests
"""
from datetime import date, timedelta

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
# 1. _compute_trend()
# ===========================================================================

class TestComputeTrend:
    def _make_timeline(self, emotions: list[str]):
        from app.api.routes.therapy import EmotionPoint
        from datetime import datetime
        return [
            EmotionPoint(
                session_id=f"sid-{i}",
                emotion=em,
                label_en=em.capitalize(),
                label_ar=em,
                theme=None,
                timestamp=datetime(2026, 5, i + 1).isoformat(),
            )
            for i, em in enumerate(emotions)
        ]

    async def test_improving_when_moving_from_hopeless_to_gratitude(self):
        from app.api.routes.therapy import _compute_trend
        tl = self._make_timeline(["hopelessness", "grief", "sadness", "anxiety", "doubt", "gratitude"])
        assert _compute_trend(tl) == "improving"

    async def test_challenging_when_moving_to_distress(self):
        from app.api.routes.therapy import _compute_trend
        tl = self._make_timeline(["gratitude", "general", "doubt", "grief", "hopelessness", "grief"])
        assert _compute_trend(tl) == "challenging"

    async def test_stable_when_no_significant_change(self):
        from app.api.routes.therapy import _compute_trend
        tl = self._make_timeline(["anxiety", "stress", "doubt", "anxiety", "stress", "general"])
        assert _compute_trend(tl) == "stable"

    async def test_stable_with_fewer_than_4_sessions(self):
        from app.api.routes.therapy import _compute_trend
        tl = self._make_timeline(["grief", "anxiety", "sadness"])
        assert _compute_trend(tl) == "stable"

    async def test_stable_with_empty_timeline(self):
        from app.api.routes.therapy import _compute_trend
        assert _compute_trend([]) == "stable"

    async def test_improving_single_large_jump(self):
        from app.api.routes.therapy import _compute_trend
        # grief (score 1), hopelessness (0), fear (1.5), then 3 gratitude (5) each
        tl = self._make_timeline(["grief", "hopelessness", "fear", "gratitude", "gratitude", "gratitude"])
        assert _compute_trend(tl) == "improving"


# ===========================================================================
# 2. _compute_streak()
# ===========================================================================

class TestComputeStreak:
    async def test_single_today(self):
        from app.api.routes.therapy import _compute_streak
        assert _compute_streak([date.today()]) == 1

    async def test_consecutive_3_days_ending_today(self):
        from app.api.routes.therapy import _compute_streak
        today = date.today()
        dates = [today - timedelta(days=2), today - timedelta(days=1), today]
        assert _compute_streak(dates) == 3

    async def test_streak_ending_yesterday(self):
        from app.api.routes.therapy import _compute_streak
        yesterday = date.today() - timedelta(days=1)
        dates = [yesterday - timedelta(days=1), yesterday]
        assert _compute_streak(dates) == 2

    async def test_gap_breaks_streak(self):
        from app.api.routes.therapy import _compute_streak
        today = date.today()
        dates = [today - timedelta(days=3), today - timedelta(days=1), today]
        # gap on day -2 breaks the backward streak; only day -1 and today consecutive
        assert _compute_streak(dates) == 2

    async def test_old_sessions_no_streak(self):
        from app.api.routes.therapy import _compute_streak
        today = date.today()
        dates = [today - timedelta(days=5), today - timedelta(days=4)]
        assert _compute_streak(dates) == 0

    async def test_empty_returns_zero(self):
        from app.api.routes.therapy import _compute_streak
        assert _compute_streak([]) == 0

    async def test_duplicate_dates_counted_once(self):
        from app.api.routes.therapy import _compute_streak
        today = date.today()
        yesterday = today - timedelta(days=1)
        # Multiple sessions on same day should still count as 1 day
        dates = [yesterday, yesterday, today, today]
        assert _compute_streak(dates) == 2


# ===========================================================================
# 3. API integration — /insights returns timeline + trend + streak
# ===========================================================================

class TestInsightsGrowthMap:
    _ids: list[str] = []

    async def _create_session(self, client, emotion: str) -> str:
        """Helper: create a session via /ask and return session_id."""
        r = await client.post(
            "/api/v1/therapy/ask",
            json={"message": f"I feel {emotion}", "emotion_override": emotion},
        )
        assert r.status_code == 200
        sid = r.json()["session_id"]
        self._ids.append(sid)
        return sid

    async def test_insights_returns_emotion_timeline(self, client):
        s1 = await self._create_session(client, "anxiety")
        s2 = await self._create_session(client, "gratitude")
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [s1, s2], "language": "en"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "emotion_timeline" in data
        assert isinstance(data["emotion_timeline"], list)
        assert len(data["emotion_timeline"]) == 2

    async def test_timeline_entries_have_required_fields(self, client):
        s1 = await self._create_session(client, "sadness")
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [s1], "language": "en"},
        )
        assert r.status_code == 200
        pt = r.json()["emotion_timeline"][0]
        assert pt["emotion"] == "sadness"
        assert "label_en" in pt
        assert "label_ar" in pt
        assert "timestamp" in pt

    async def test_insights_returns_trend_field(self, client):
        s1 = await self._create_session(client, "anxiety")
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [s1], "language": "en"},
        )
        assert r.status_code == 200
        assert r.json()["trend"] in ("improving", "stable", "challenging")

    async def test_insights_returns_streak_days(self, client):
        s1 = await self._create_session(client, "doubt")
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": [s1], "language": "en"},
        )
        assert r.status_code == 200
        assert isinstance(r.json()["streak_days"], int)
        assert r.json()["streak_days"] >= 1  # session was just created today

    async def test_empty_session_ids_returns_empty_timeline(self, client):
        r = await client.post(
            "/api/v1/therapy/insights",
            json={"session_ids": ["nonexistent-id-xyz"], "language": "en"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["emotion_timeline"] == []
        assert data["trend"] == "stable"

    async def teardown_class(self):
        await _clean_sessions(self._ids)
