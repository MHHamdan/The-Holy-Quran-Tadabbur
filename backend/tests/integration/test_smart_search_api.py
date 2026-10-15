"""
GET /quran/search/smart against the seeded database.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, tuple_

from app.main import app
from app.db import database
from app.models.quran import QuranVerse

pytestmark = pytest.mark.asyncio(loop_scope="session")

URL = "/api/v1/quran/search/smart"


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _get(client, q, **params):
    r = await client.get(URL, params={"q": q, **params})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("q", ["2:255", "٢:٢٥٥", "2 255", "2.255", "سورة 2:255"])
async def test_reference_jump(client, q):
    body = await _get(client, q)
    assert body["intent"] == "reference"
    assert (body["jump"]["sura_no"], body["jump"]["aya_no"]) == (2, 255)
    assert body["verses"]["items"][0]["reference"] == "2:255"


async def test_reference_out_of_range(client):
    body = await _get(client, "2:300")
    assert body["jump"] is None
    assert body["reference_error"]["message_en"]
    assert body["reference_error"]["message_ar"]


async def test_bad_surah_number(client):
    body = await _get(client, "115:1")
    assert body["jump"] is None and body["reference_error"]


@pytest.mark.parametrize("q", [
    "البقرة", "سورة البقرة",
    "Baqarah", "al-baqara", "Al Baqarah",
])
async def test_surah_names(client, q):
    body = await _get(client, q)
    assert 2 in [s["number"] for s in body["surahs"]]


@pytest.mark.parametrize("q", ["آية الكرسي", "ayat al kursi"])
async def test_alias_ayat_al_kursi(client, q):
    body = await _get(client, q)
    assert body["intent"] == "alias"
    assert (body["alias"]["sura_no"], body["alias"]["aya_start"]) == (2, 255)
    assert body["verses"]["items"][0]["reference"] == "2:255"
    assert body["verses"]["items"][0]["match_type"] == "alias"


async def test_rahman_is_surah_chip_and_word(client):
    body = await _get(client, "الرحمن")
    assert 55 in [s["number"] for s in body["surahs"]]
    assert body["verses"]["total"] >= 48
    assert body["verses"]["items"][0]["match_type"] == "exact"


async def test_text_paging_and_ranking(client):
    first = await _get(client, "الصبر", limit=10)
    assert first["verses"]["total"] >= 19
    second = await _get(client, "الصبر", limit=10, offset=10)
    ids1 = {i["verse_id"] for i in first["verses"]["items"]}
    ids2 = {i["verse_id"] for i in second["verses"]["items"]}
    assert ids2 and not (ids1 & ids2)
    order = {"exact": 0, "prefix": 1, "normalized": 2}
    ranks = [order[i["match_type"]] for i in first["verses"]["items"]]
    assert ranks == sorted(ranks)


async def test_two_letter_query_whole_word(client):
    body = await _get(client, "يس")
    refs = [i["reference"] for i in body["verses"]["items"]]
    assert "36:1" in refs
    assert 36 in [s["number"] for s in body["surahs"]]
    # 'ليس' must not match
    assert "2:177" not in refs


async def test_moses_translation(client):
    body = await _get(client, "Moses", lang="en")
    assert body["translations"]["total"] > 100
    assert body["translations"]["editions"]
    assert body["translations"]["hits"][0]["translation"]["text"]


async def test_semantic_unavailable_without_hf(client):
    body = await _get(client, "patience", semantic="true")
    assert body["semantic"]["available"] is False


async def test_text_is_canonical(client):
    body = await _get(client, "الرحمه", limit=20)
    items = body["verses"]["items"]
    assert items
    refs = [(i["sura_no"], i["aya_no"]) for i in items]
    async with database.AsyncSessionLocal() as s:
        rows = (await s.execute(
            select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani)
            .where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(refs))
        )).all()
    db = {(a, b): t for a, b, t in rows}
    for i in items:
        assert i["text_uthmani"] == db[(i["sura_no"], i["aya_no"])]
        assert i["highlighted_text"].replace("【", "").replace("】", "") == i["text_uthmani"]
