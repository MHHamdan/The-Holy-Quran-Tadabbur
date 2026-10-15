"""
/tafseer/{s}/{a} serves only allowlisted editions.

alquran.cloud lists ~130 editions; "ar.miqbas" returns Ibn Ashur's text under
the title of Tanwir al-Miqbas, and most others carry no recorded licence or
author. Anything outside ALLOWED_EDITIONS must be refused without an upstream
call, and a request whose editions are all refused gets 403
EDITION_NOT_LICENSED (not a misleading 404 VERSE_NOT_FOUND).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import tafseer_api
from app.services.tafseer_api import (
    ALLOWED_EDITIONS,
    EDITION_NOT_LICENSED,
    AlQuranCloudClient,
    TafseerVerse,
)

REFUSED = ["ar.miqbas", "ur.maududi", "en.pickthall", "de.aburida", "fr.hamidullah"]


class _NoNetwork:
    """httpx.AsyncClient stand-in that fails the test if it is used."""

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        raise AssertionError("refused edition reached the upstream API")

    async def __aexit__(self, *a):
        return False


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(tafseer_api.httpx, "AsyncClient", _NoNetwork)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def test_allowlist_is_small_and_explicit():
    assert ALLOWED_EDITIONS == {"ar.muyassar", "en.sahih", "en.hilali"}
    for edition in REFUSED:
        assert not tafseer_api.is_allowed_edition(edition)


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", REFUSED)
async def test_client_refuses_without_upstream_call(no_network, edition):
    c = AlQuranCloudClient(use_hybrid_cache=False)
    r = await c.get_tafseer(112, 1, [edition])
    assert not r.success and r.error == EDITION_NOT_LICENSED and r.tafasir == []
    assert await c.get_surah_tafseer(112, edition) == []


@pytest.mark.asyncio
async def test_mixed_request_keeps_only_allowed(monkeypatch, no_network):
    c = AlQuranCloudClient(use_hybrid_cache=False)
    cached = TafseerVerse(surah=112, ayah=1, text="x", edition="ar.muyassar",
                          edition_name="التفسير الميسر", language="ar")

    async def fake_cached(key):
        return vars(cached) if "ar.muyassar" in key else None

    monkeypatch.setattr(c, "_get_cached", fake_cached)
    r = await c.get_tafseer(112, 1, ["ar.miqbas", "ar.muyassar"])
    assert r.success and [t.edition for t in r.tafasir] == ["ar.muyassar"]


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", ["ar.miqbas", "ur.maududi", "en.pickthall"])
async def test_route_returns_403_for_unlicensed(client, no_network, edition):
    r = await client.get("/api/v1/tafseer/112/1", params={"editions": edition})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "EDITION_NOT_LICENSED"


@pytest.mark.asyncio
async def test_surah_route_returns_403_for_unlicensed(client, no_network):
    r = await client.get("/api/v1/tafseer/surah/112", params={"edition": "ar.miqbas"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_editions_list_is_the_allowlist(client):
    r = await client.get("/api/v1/tafseer/editions")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] <= 3
    assert {e["identifier"] for e in body["editions"]} == ALLOWED_EDITIONS
    for e in body["editions"]:
        assert e["author_en"] and e["author_ar"]


@pytest.mark.asyncio
async def test_editions_list_language_filter(client):
    r = await client.get("/api/v1/tafseer/editions", params={"language": "ar"})
    assert [e["identifier"] for e in r.json()["editions"]] == ["ar.muyassar"]


@pytest.mark.asyncio
async def test_licensed_english_reads_db(monkeypatch, no_network):
    async def fake_db(surah, ayah, key):
        assert key == "english_saheeh"
        return [(1, "Say, He is Allah, [who is] One,", "1.1.2")]

    monkeypatch.setattr(tafseer_api, "_db_translation", fake_db)
    c = AlQuranCloudClient(use_hybrid_cache=False)
    r = await c.get_tafseer(112, 1, ["en.sahih"])
    assert r.success and r.tafasir[0].edition == "en.sahih"
    assert "v1.1.2" in r.tafasir[0].edition_name
