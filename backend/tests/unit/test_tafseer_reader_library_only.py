"""
The reader's tafsir comes from the licensed library only; nothing is proxied.

GET /tafseer/external/verse/26/40?edition=qurtubi used to fall back to
Quran.com and return its placeholder "لا يوجد تفسير لهذه الأية" under
al-Qurtubi's name and licence (100 ayat across qurtubi, ibn_kathir and
baghawi). A verse a seeded source has no passage for is now a bilingual 404
NO_PASSAGE_IN_SOURCE, a source that is not seeded is 404 EDITION_NOT_SEEDED,
and the Quran.com proxy route is closed.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.services.tafsir_api import ALLOWED_QURAN_COM_IDS, TAFSIR_EDITIONS
from app.services.tafsir_sources import TAFSIR_PLACEHOLDER_TEXTS, is_tafsir_placeholder

PLACEHOLDER = "لا يوجد تفسير لهذه الأية"


@pytest.mark.parametrize("value", [PLACEHOLDER, f" {PLACEHOLDER}. ", "لا يوجد تفسير لهذه الآية", "", "   ", None])
def test_placeholder_or_empty_is_not_tafsir(value):
    assert is_tafsir_placeholder(value)


def test_real_passage_is_not_a_placeholder():
    assert not is_tafsir_placeholder("قال أبو جعفر: لا يوجد تفسير لهذه الأية عند فلان ثم ذكر")
    assert PLACEHOLDER in TAFSIR_PLACEHOLDER_TEXTS


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def no_proxy(monkeypatch):
    from app.api.routes import tafseer as route

    async def boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("tafsir must not be proxied")

    for name in ("get_tafsir", "fetch_from_quran_com", "fetch_from_quran_tafseer",
                 "fetch_from_tafsir_one", "get_multiple_tafsirs"):
        monkeypatch.setattr(route.external_tafsir_service, name, boom)
    return route


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", sorted(TAFSIR_EDITIONS))
async def test_no_passage_is_a_bilingual_404_not_a_proxy(client, no_proxy, monkeypatch, edition):
    async def none(*a, **k):
        return None

    monkeypatch.setattr(no_proxy, "_local_licensed_passage", none)
    r = await client.get("/api/v1/tafseer/external/verse/26/40", params={"edition": edition})
    assert r.status_code == 404
    d = r.json()["detail"]
    info = TAFSIR_EDITIONS[edition]
    assert d["code"] == "NO_PASSAGE_IN_SOURCE"
    assert d["source_id"] == info.db_source_id and d["verse_key"] == "26:40"
    assert info.name_en in d["message"] and info.name_ar in d["message_ar"]
    assert PLACEHOLDER not in r.text


@pytest.mark.asyncio
async def test_unseeded_source_is_not_proxied(client, no_proxy, monkeypatch):
    async def unseeded(*a, **k):
        raise no_proxy._EditionNotSeeded("baghawi_ar")

    monkeypatch.setattr(no_proxy, "_local_licensed_passage", unseeded)
    r = await client.get("/api/v1/tafseer/external/verse/1/1", params={"edition": "baghawi"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "EDITION_NOT_SEEDED"
    assert r.json()["detail"]["message_ar"]


@pytest.mark.asyncio
async def test_database_failure_is_503_not_a_proxy(client, no_proxy, monkeypatch):
    async def down(*a, **k):
        raise ConnectionError("db down")

    monkeypatch.setattr(no_proxy, "_local_licensed_passage", down)
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": "tabari"})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "TAFSIR_UNAVAILABLE"


@pytest.mark.asyncio
@pytest.mark.parametrize("tafsir_id", sorted(ALLOWED_QURAN_COM_IDS))
async def test_quran_com_proxy_is_closed(client, no_proxy, tafsir_id):
    r = await client.get("/api/v1/tafseer/quran-com/verse/2/255", params={"tafsir_id": tafsir_id})
    assert r.status_code == 410
    assert r.json()["detail"]["code"] == "PROXY_DISABLED"


@pytest.mark.asyncio
async def test_compare_serves_library_passages_only(client, no_proxy, monkeypatch):
    async def fake(session, db_source_id, sura, ayah):
        if db_source_id == "tabari_ar":
            return {"text": "نص", "chunk_id": "c1"}
        if db_source_id == "qurtubi_ar":
            raise no_proxy._EditionNotServable(db_source_id)
        return None

    monkeypatch.setattr(no_proxy, "_local_licensed_passage", fake)
    r = await client.get("/api/v1/tafseer/external/compare/2/255",
                         params={"editions": "muyassar,tabari,qurtubi,unknown"})
    assert r.status_code == 200
    body = r.json()
    assert [t["source_id"] for t in body["tafsirs"]] == ["tabari_ar"]
    assert body["tafsirs"][0]["source"] == "tadabbur_library"
    assert body["editions_found"] == 1


# --- live database ----------------------------------------------------------------

async def _missing_verse(source_id: str):
    """A verse with no stored passage in source_id, or None."""
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            row = (await session.execute(text("""
                SELECT v.sura_no, v.aya_no FROM quran_verses v
                 WHERE NOT EXISTS (SELECT 1 FROM tafseer_chunks c
                                    WHERE c.source_id = :s AND c.sura_no = v.sura_no
                                      AND c.aya_start <= v.aya_no AND c.aya_end >= v.aya_no)
                 ORDER BY v.sura_no, v.aya_no LIMIT 1
            """), {"s": source_id})).first()
            seeded = (await session.execute(text(
                "SELECT 1 FROM tafseer_sources WHERE id = :s AND is_enabled = 1 AND license_verified = 1"
            ), {"s": source_id})).first()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    return row if seeded else None


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", ["qurtubi", "ibn_kathir", "baghawi"])
async def test_verse_without_passage_never_shows_placeholder(client, no_proxy, edition):
    missing = await _missing_verse(TAFSIR_EDITIONS[edition].db_source_id)
    if not missing:
        pytest.skip("no verse without a passage (or source not seeded) in this DB")
    sura, ayah = missing
    r = await client.get(f"/api/v1/tafseer/external/verse/{sura}/{ayah}", params={"edition": edition})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "NO_PASSAGE_IN_SOURCE"
    assert PLACEHOLDER not in r.text


@pytest.mark.asyncio
async def test_no_stored_passage_of_an_enabled_source_is_a_placeholder():
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            rows = (await session.execute(text("""
                SELECT c.chunk_id, coalesce(c.content_ar, c.content_en) AS t
                  FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id
                 WHERE s.is_enabled = 1 AND char_length(coalesce(c.content_ar, c.content_en, '')) < 60
            """))).all()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    assert [cid for cid, t in rows if is_tafsir_placeholder(t)] == []
