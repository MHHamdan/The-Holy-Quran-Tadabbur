"""
Search-history sessions: unguessable ids and bounded in-memory state.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.search_history import SearchHistoryService, _LRUDict

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("sid", ["abc", "sess_lq3k1_ab12cd34", "sess_" + "a" * 36, ""])
def test_weak_session_ids_rejected(sid):
    r = client.get("/api/v1/quran/history", params={"session_id": sid})
    assert r.status_code == 422


def test_uuid_session_id_accepted():
    r = client.get("/api/v1/quran/history", params={"session_id": f"sess_{uuid.uuid4()}"})
    assert r.status_code == 200


def test_bookmarks_require_strong_id():
    assert client.get("/api/v1/quran/bookmarks", params={"session_id": "x"}).status_code == 422


def test_lru_dict_evicts_oldest_and_keeps_recent():
    d = _LRUDict(3, list)
    for k in "abc":
        d[k].append(k)
    d["a"]  # touch: a becomes most recent
    d["d"].append("d")
    assert list(d.keys()) == ["c", "a", "d"]
    assert "b" not in d


@pytest.mark.asyncio
async def test_session_state_is_bounded(monkeypatch):
    import app.services.search_history as sh

    monkeypatch.setattr(sh, "MAX_SESSIONS", 5)
    svc = SearchHistoryService()
    for i in range(20):
        await svc.record_search(f"s{i}", "q", "text", themes=["t"])
        await svc.add_bookmark(session_id=f"s{i}", sura_no=1, aya_no=1)
    assert len(svc._session_history) == 5
    assert len(svc._theme_interests) == 5
    assert len(svc._bookmarks) == 5
