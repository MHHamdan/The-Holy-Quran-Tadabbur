"""
Search history privacy: one reader's queries never reach another reader.

Regression for the audit finding where search_history.get_search_suggestions
appended the global most_common queries to every session's suggestions and the
public /history/stats endpoint listed them as top_searches, even after the
author cleared their history.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.routes import quran as quran_routes
from app.main import app
from app.services import search_history as sh
from app.services.search_history import SearchHistoryService

SECRET = "auditprivate my divorce anxiety"


def _sid() -> str:
    return f"sess_{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_suggestions_never_include_other_sessions_queries():
    svc = SearchHistoryService()
    a, b = _sid(), _sid()
    await svc.record_search(a, SECRET, "text")
    await svc.record_search(b, "mercy", "text")

    for prefix in (None, "audit", "a", "m"):
        got = [s.query for s in await svc.get_search_suggestions(b, prefix=prefix, limit=50)]
        assert SECRET not in got
    assert [s.query for s in await svc.get_search_suggestions(b, limit=50)] == ["mercy"]
    # An empty session gets nothing at all, not a "popular" list
    assert await svc.get_search_suggestions(_sid(), limit=50) == []
    # The author still gets their own suggestion
    assert [s.query for s in await svc.get_search_suggestions(a, limit=50)] == [SECRET]


@pytest.mark.asyncio
async def test_stats_contain_no_query_text():
    svc = SearchHistoryService()
    await svc.record_search(_sid(), SECRET, "text")
    stats = svc.get_stats()
    assert "top_searches" not in stats
    assert "unique_queries" not in stats
    assert SECRET not in repr(stats)
    assert stats["total_searches"] == 1


@pytest.mark.asyncio
async def test_clear_session_removes_all_session_state():
    svc = SearchHistoryService()
    a, b = _sid(), _sid()
    await svc.record_search(a, SECRET, "text", themes=["patience"])
    await svc.add_bookmark(session_id=a, sura_no=2, aya_no=255, note="private note")
    await svc.set_study_goal(a, "reflection", themes=["hope"])
    await svc.record_similarity_feedback(a, "2:255", "3:18", True, notes="my private comment")
    await svc.record_similarity_feedback(b, "2:255", "3:18", False)

    await svc.clear_session_history(a)

    assert await svc.get_session_history(a) == []
    assert await svc.get_theme_interests(a) == {}
    assert await svc.get_bookmarks(a) == []
    assert await svc.get_bookmark_collections(a) == {}
    assert await svc.get_study_goal(a) is None
    assert await svc.get_session_feedback(a) == []
    remaining = await svc.get_pair_feedback("2:255", "3:18")
    assert [fb.session_id for fb in remaining] == [b]
    assert "my private comment" not in repr(remaining)
    # Other sessions are untouched
    assert len(await svc.get_session_feedback(b)) == 1


@pytest.mark.asyncio
async def test_history_entries_expire(monkeypatch):
    monkeypatch.setattr(sh, "SEARCH_HISTORY_TTL_DAYS", 30)
    svc = SearchHistoryService()
    a = _sid()
    await svc.record_search(a, "old query", "text")
    svc._session_history[a][0].timestamp = datetime.utcnow() - timedelta(days=31)
    await svc.record_search(a, "new query", "text")

    assert [e.query for e in await svc.get_session_history(a)] == ["new query"]
    assert [s.query for s in await svc.get_search_suggestions(a)] == ["new query"]
    assert [e.query for e in svc._session_history[a]] == ["new query"]


@pytest.mark.asyncio
async def test_per_session_state_is_bounded(monkeypatch):
    monkeypatch.setattr(sh, "MAX_SESSIONS", 3)
    svc = SearchHistoryService(max_history_per_session=5)
    for i in range(10):
        sid = f"s{i}"
        await svc.add_bookmark(session_id=sid, sura_no=1, aya_no=1)
        await svc.set_study_goal(sid, "reflection")
        for j in range(8):
            await svc.record_search(sid, f"q{j}", "text")
    assert len(svc._bookmark_collections) == 3
    assert len(svc._study_goals) == 3
    assert all(len(h) <= 5 for h in svc._session_history.values())


def test_api_suggestions_and_stats_do_not_leak_across_sessions(monkeypatch):
    svc = SearchHistoryService()
    monkeypatch.setattr(quran_routes, "search_history_service", svc)
    client = TestClient(app)
    a, b = _sid(), _sid()

    r = client.post("/api/v1/quran/history/search", params={"session_id": a},
                    json={"query": SECRET, "query_type": "text"})
    assert r.status_code == 200

    r = client.get("/api/v1/quran/history/suggestions", params={"session_id": b, "limit": 50})
    assert r.status_code == 200
    assert SECRET not in r.text

    r = client.get("/api/v1/quran/history/stats")
    assert SECRET not in r.text

    # Delete my data path: DELETE /history removes the author's copy too
    assert client.delete("/api/v1/quran/history", params={"session_id": a}).status_code == 200
    r = client.get("/api/v1/quran/history/suggestions", params={"session_id": a, "limit": 50})
    assert SECRET not in r.text
    r = client.get("/api/v1/quran/history", params={"session_id": a})
    assert r.json() == []


def test_global_recent_and_popular_query_lists_are_gone():
    client = TestClient(app)
    # The write endpoint that fed the global lists no longer exists
    assert client.post("/api/v1/search/record", params={"q": SECRET}).status_code in (404, 405)
    assert client.get("/api/v1/search/recent").status_code in (404, 405)
    r = client.get("/api/v1/search/trending")
    assert r.status_code == 200
    assert "popular_searches" not in r.json()
    assert SECRET not in r.text
