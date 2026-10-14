"""
Privacy of spiritual-guidance sessions.

- The user's own message is never stored server-side.
- A session (and any saved reflection) can be deleted by its id.
- Sessions older than the retention window are purged.
"""
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.routes.therapy import THERAPY_RETENTION_DAYS
from app.core.config import settings
from app.core.rate_limit import therapy_rate_limit
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")

_DB_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")


async def _sql(query: str, **params):
    engine = create_async_engine(_DB_URL)
    try:
        async with engine.begin() as conn:
            return (await conn.execute(text(query), params)).all() if query.lstrip().upper().startswith("SELECT") \
                else await conn.execute(text(query), params)
    finally:
        await engine.dispose()


async def _no_rate_limit() -> None:
    pass


@pytest_asyncio.fixture(scope="module")
async def client():
    previous = app.dependency_overrides.get(therapy_rate_limit)
    app.dependency_overrides[therapy_rate_limit] = _no_rate_limit
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    if previous is None:
        app.dependency_overrides.pop(therapy_rate_limit, None)
    else:
        app.dependency_overrides[therapy_rate_limit] = previous


async def _ask(client) -> str:
    r = await client.post("/api/v1/therapy/ask", json={"message": "I feel anxious about my exams tomorrow"})
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


async def test_message_is_not_stored(client):
    sid = await _ask(client)
    rows = await _sql("SELECT user_message, emotion FROM therapy_sessions WHERE session_id = :s", s=sid)
    assert rows and rows[0][0] is None and rows[0][1]
    await _sql("DELETE FROM therapy_sessions WHERE session_id = :s", s=sid)


async def test_delete_sessions_removes_reflection(client):
    sid = await _ask(client)
    r = await client.post("/api/v1/therapy/reflect", json={"session_id": sid, "reflection": "A private note"})
    assert r.status_code == 200, r.text
    r = await client.post("/api/v1/therapy/sessions/delete", json={"session_ids": [sid, "not-a-real-id"]})
    assert r.status_code == 200 and r.json() == {"deleted": 1}
    assert await _sql("SELECT 1 FROM therapy_sessions WHERE session_id = :s", s=sid) == []
    r = await client.post("/api/v1/therapy/reflections", json={"session_ids": [sid]})
    assert r.json()["reflections"] == []


async def test_delete_requires_ids(client):
    r = await client.post("/api/v1/therapy/sessions/delete", json={"session_ids": []})
    assert r.status_code == 422


async def test_expired_sessions_purged_on_next_write(client):
    old = "00000000-0000-4000-8000-00000000a1d0"
    await _sql(
        "INSERT INTO therapy_sessions (session_id, emotion, language, created_at) "
        "VALUES (:s, 'general', 'en', :t)",
        s=old, t=datetime.utcnow() - timedelta(days=THERAPY_RETENTION_DAYS + 1),
    )
    sid = await _ask(client)
    assert await _sql("SELECT 1 FROM therapy_sessions WHERE session_id = :s", s=old) == []
    await _sql("DELETE FROM therapy_sessions WHERE session_id = :s", s=sid)
