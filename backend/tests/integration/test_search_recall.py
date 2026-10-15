"""
Search recall against the seeded database.

Every one of these returned 0 (or a capped page) before the shared normalizer
and the normalized imlaei column: الرحمن 1 of 48, enhanced الصبر 4 of 19,
الرحمه 0, 'من بعد' 1 of 126, الصلاه 0, analytics/phrase always 0, and the
intelligent total was capped at the page size. Minimum counts are floors
measured on the Tanzil text, so the test fails loudly on a regression.

Every Arabic text field returned must equal quran_verses.text_uthmani.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, tuple_

from app.main import app
from app.db import database
from app.models.quran import QuranVerse

pytestmark = pytest.mark.asyncio(loop_scope="session")

Q = "/api/v1/quran"


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _assert_canonical(items, text_key="text_uthmani"):
    refs = sorted({(i["sura_no"], i["aya_no"]) for i in items})
    if not refs:
        return
    async with database.AsyncSessionLocal() as s:
        rows = (await s.execute(
            select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani)
            .where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(refs))
        )).all()
    db = {(a, b): t for a, b, t in rows}
    for i in items:
        assert i[text_key] == db[(i["sura_no"], i["aya_no"])], (i["sura_no"], i["aya_no"])


# word -> minimum verses (smart search, Arabic text stage)
SMART_FLOORS = {
    "الرحمن": 48,        # الرحمن
    "الصبر": 19,              # الصبر
    "الرحمه": 6,         # الرحمه
    "الرحمة": 6,         # الرحمة
    "ابراهيم": 63,  # ابراهيم
    "موسى": 131,                   # موسى
    "من بعد": 120,            # من بعد
    "الصلاه": 50,        # الصلاه
}


@pytest.mark.parametrize("word, floor", list(SMART_FLOORS.items()))
async def test_smart_text_recall(client, word, floor):
    r = await client.get(f"{Q}/search/smart", params={"q": word, "limit": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["verses"]["total"] >= floor, (word, body["verses"]["total"])
    await _assert_canonical(body["verses"]["items"])


@pytest.mark.parametrize("word, floor", [
    ("الرحمن", 48),
    ("الصبر", 19),
    ("من بعد", 120),
])
async def test_enhanced_recall(client, word, floor):
    r = await client.get(f"{Q}/search/enhanced/{word}", params={"include_semantic": "false", "limit": 200})
    assert r.status_code == 200
    body = r.json()
    assert body["total_matches"] >= floor
    await _assert_canonical(body["matches"])


async def test_basic_search_ordered_with_total(client):
    r = await client.get(f"{Q}/search", params={"q": "الصبر"})
    body = r.json()
    assert body["total"] >= 19
    refs = [x["reference"] for x in body["results"]]
    assert refs.index("2:45") < refs.index("2:153") < refs.index("3:17")


async def test_basic_search_salah(client):
    r = await client.get(f"{Q}/search", params={"q": "الصلاه"})
    assert r.json()["total"] > 0


async def test_intelligent_total_and_paging(client):
    word = "الصبر"
    first = (await client.get(f"{Q}/search/intelligent", params={"query": word, "limit": 20})).json()
    assert first["total_matches"] >= 86
    assert len(first["verses"]) == 20
    second = (await client.get(f"{Q}/search/intelligent", params={"query": word, "limit": 20, "offset": 20})).json()
    a = {v["verse_id"] for v in first["verses"]}
    b = {v["verse_id"] for v in second["verses"]}
    assert len(b) == 20 and not (a & b)
    await _assert_canonical(first["verses"])


async def test_intelligent_exact_hits_rank_first(client):
    body = (await client.get(f"{Q}/search/intelligent", params={"query": "الرحمة", "limit": 30})).json()
    types = [v["match_type"] for v in body["verses"]]
    assert types[:5] == ["exact"] * 5
    # no exact hit after a concept-only hit
    if "concept_expansion" in types:
        assert "exact" not in types[types.index("concept_expansion"):]


async def test_intelligent_surah_alias_does_not_hijack(client):
    body = (await client.get(f"{Q}/search/intelligent", params={"query": "الرحمن"})).json()
    assert 55 in [s["sura_no"] for s in body["surahs"]]
    assert body["total_matches"] >= 48
    assert body["verses"][0]["match_type"] != "alias"


async def test_analytics_musa(client):
    body = (await client.get(f"{Q}/search/analytics/موسى")).json()
    assert body["total_occurrences"] >= 131
    assert body["by_sura"]


async def test_phrase_hayy_qayyum(client):
    body = (await client.get(f"{Q}/search/phrase", params={"phrase": "الحي القيوم"})).json()
    refs = {m["reference"] for m in body["matches"]}
    assert {"2:255", "3:2", "20:111"} <= refs


async def test_root_search_uses_derived_words(client):
    body = (await client.get(f"{Q}/search/root/صبر", params={"limit": 200})).json()
    assert body["total_matches"] >= 80
    await _assert_canonical(body["matches"])


async def test_moses_translation(client):
    body = (await client.get(f"{Q}/search/smart", params={"q": "Moses", "lang": "en"})).json()
    assert body["translations"]["total"] >= 100
    await _assert_canonical(body["translations"]["hits"])


async def test_reference_jump(client):
    body = (await client.get(f"{Q}/search/smart", params={"q": "2:255"})).json()
    assert body["jump"]["sura_no"] == 2 and body["jump"]["aya_no"] == 255
    await _assert_canonical(body["verses"]["items"])
