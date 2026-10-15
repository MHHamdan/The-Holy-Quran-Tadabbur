"""
Every tafsir passage the comparison API returns carries its attribution:
licence text, where the text came from, and its translator (translations).
The service never derives source_url from cdn_url on its own; the row's
source_url is set by the seeder (and, for older rows, by migration
r3d1a2b3c4d5) to the URL the stored text was really fetched from, which for
the development database's ibn_kathir_ar / tabari_ar / qurtubi_ar /
muyassar_ar rows is the spa5k CDN (see stored_copy in the manifest).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.tafsir_comparison import _manifest_urls, _source_url


def test_manifest_urls_point_at_real_provenance():
    urls = _manifest_urls()
    for sid in ("tabari_ar", "qurtubi_ar", "baghawi_ar", "ibn_kathir_ar"):
        assert urls[sid] == "https://huggingface.co/datasets/riotu-lab/Quran-Tafseers"


def test_row_source_url_wins_and_cdn_is_ignored():
    class Row:
        source_url = None
        cdn_url = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/x"

    assert "jsdelivr" not in (_source_url("tabari_ar", Row()) or "")
    Row.source_url = "https://example.org/own"
    assert _source_url("tabari_ar", Row()) == "https://example.org/own"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_compare_entries_carry_attribution(client):
    r = await client.get("/api/v1/tafseer/compare/2/255", params={"language": "ar"})
    if r.status_code == 404:
        pytest.skip("no seeded tafsir")
    for e in r.json()["entries"]:
        assert {"license", "source_url", "translator"} <= set(e)
        assert e["author_ar"] and e["name_ar"] and e["source_id"]
        assert e["source_url"] and e["source_url"].startswith("https://"), e["source_id"]


@pytest.mark.asyncio
async def test_compare_source_url_is_the_rows_recorded_origin(client):
    from sqlalchemy import text

    from app.db import database

    r = await client.get("/api/v1/tafseer/compare/2/255", params={"language": "ar"})
    if r.status_code == 404:
        pytest.skip("no seeded tafsir")
    async with database.AsyncSessionLocal() as session:
        rows = dict((await session.execute(text("SELECT id, source_url FROM tafseer_sources"))).all())
    for e in r.json()["entries"]:
        if rows.get(e["source_id"]):
            assert e["source_url"] == rows[e["source_id"]], e["source_id"]


@pytest.mark.asyncio
async def test_sources_listing_carries_attribution(client):
    r = await client.get("/api/v1/tafseer/compare/2/255/sources")
    for s in r.json()["sources"]:
        assert {"license", "source_url", "translator"} <= set(s)
