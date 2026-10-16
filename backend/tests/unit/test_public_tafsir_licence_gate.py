"""
Public /quran/* endpoints serve tafsir text only from servable sources.

The legacy /api/v1/quran tafsir endpoints selected tafseer_chunks with no
source filter, so they redistributed text from disabled sources (the English
Ibn Kathir and Jalalayn) and from a source on licence hold (al-Muyassar) even
though /tafseer and RAG excluded them. Every such query now filters on
app.models.tafseer.servable_source_ids() (is_enabled=1 AND license_verified=1).
"""
import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.models.tafseer import servable_source_ids

pytestmark = [pytest.mark.asyncio, pytest.mark.requires_data("tafsir_corpus")]

ENDPOINTS = [
    "/api/v1/quran/tafseer/2/255",
    "/api/v1/quran/tafsir/compare/2/255",
    "/api/v1/quran/tafsir/evolution/2/255",
    "/api/v1/quran/search/enhanced/الله/context/2/255",
    "/api/v1/quran/allah-names?include_verses=true",
]


async def _unservable_ids_with_text() -> list[str]:
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        rows = await session.execute(text(
            "SELECT DISTINCT s.id FROM tafseer_sources s JOIN tafseer_chunks c ON c.source_id = s.id "
            "WHERE s.is_enabled = 0 OR s.license_verified = 0"
        ))
        return [r[0] for r in rows]


def test_gate_is_enabled_and_licensed():
    sql = str(servable_source_ids())
    assert "is_enabled" in sql and "license_verified" in sql


@pytest.mark.parametrize("path", ENDPOINTS)
async def test_endpoint_serves_no_unservable_source(path):
    hidden = await _unservable_ids_with_text()
    if not hidden:
        pytest.skip("no disabled or unlicensed source with stored text in this database")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(path)
    assert r.status_code in (200, 404), r.text[:300]
    leaked = sorted({sid for sid in hidden if re.search(r'"' + re.escape(sid) + r'"', r.text)})
    assert not leaked, f"{path} serves text from non-servable sources {leaked}"
