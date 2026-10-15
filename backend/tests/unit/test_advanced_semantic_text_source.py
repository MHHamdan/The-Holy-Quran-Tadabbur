"""
advanced_semantic_search_service must not hold Quran text as string literals.

It used to carry 12 hand-typed verse strings, several of them partial verses
filed under the full reference (3:103, 4:135, 13:28, 14:7), plus partial
quotes in every theme's sample_verses. The service now keeps references only
and the routes hydrate text_arabic from quran_verses.text_uthmani.
"""
import re
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, tuple_

from app.main import app
from app.db import database
from app.models.quran import QuranVerse

SERVICE = Path(__file__).resolve().parents[2] / "app/services/advanced_semantic_search_service.py"


def test_no_vowelled_arabic_literals_in_service():
    src = SERVICE.read_text(encoding="utf-8")
    assert '"text_arabic": "' not in src
    # A harakah directly after an Arabic letter inside a string literal means
    # verse text was typed into code.
    vowelled = re.findall(r'"[^"\n]*[\u0621-\u064A][\u064B-\u0652][^"\n]*"', src)
    assert vowelled == []


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


def _walk(node, out):
    if isinstance(node, dict):
        if isinstance(node.get("surah"), int) and isinstance(node.get("ayah"), int) and "text_arabic" in node:
            out.append(node)
        for v in node.values():
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


async def _assert_matches_db(body):
    items = []
    _walk(body, items)
    assert items, "no verse items in response"
    refs = sorted({(i["surah"], i["ayah"]) for i in items})
    async with database.AsyncSessionLocal() as s:
        rows = (await s.execute(
            select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani)
            .where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(refs))
        )).all()
    db = {(r[0], r[1]): r[2] for r in rows}
    for i in items:
        assert i["text_arabic"] == db[(i["surah"], i["ayah"])], (i["surah"], i["ayah"])


@pytest.mark.asyncio(loop_scope="session")
async def test_semantic_endpoint_text_equals_db(client):
    r = await client.get("/api/v1/quran/advanced-search/semantic?query=patience")
    assert r.status_code == 200
    body = r.json()
    refs = {(x["surah"], x["ayah"]) for x in body["results"]}
    assert (2, 153) in refs
    await _assert_matches_db(body)


@pytest.mark.asyncio(loop_scope="session")
async def test_theme_details_sample_verses_equal_db(client):
    r = await client.get("/api/v1/quran/advanced-search/themes/patience")
    assert r.status_code == 200
    await _assert_matches_db(r.json())


@pytest.mark.asyncio(loop_scope="session")
async def test_theme_verses_and_similar_equal_db(client):
    r = await client.get("/api/v1/quran/advanced-search/themes/patience/verses")
    assert r.status_code == 200
    await _assert_matches_db(r.json())
    r = await client.get("/api/v1/quran/advanced-search/similar-verses/2/153")
    assert r.status_code == 200
    await _assert_matches_db(r.json())
