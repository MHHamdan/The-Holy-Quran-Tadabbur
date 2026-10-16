"""
/tafseer/{s}/{a} serves only allowlisted editions.

alquran.cloud lists ~130 editions; "ar.miqbas" returns Ibn Ashur's text under
the title of Tanwir al-Miqbas, and most others carry no recorded licence or
author. Anything outside ALLOWED_EDITIONS must be refused without an upstream
call, and a request whose editions are all refused gets 403
EDITION_NOT_LICENSED (not a misleading 404 VERSE_NOT_FOUND).

Nothing on the allowlist is proxied either: Arabic tafsir is read from
tafseer_chunks, and only while its tafseer_sources row is enabled and
licence-verified, so al-Muyassar (licence on hold, license_verified=0) is
refused like an unlisted edition. The default editions are a cleared tafsir
(al-Baghawi) and the licensed English translation.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import tafseer_api
from app.services.tafseer_api import (
    ALLOWED_EDITIONS,
    DEFAULT_EDITIONS,
    EDITION_NOT_LICENSED,
    LICENSED_DB_TAFSIR,
    AlQuranCloudClient,
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
    assert ALLOWED_EDITIONS == {
        "ar.baghawi", "ar.tabari", "ar.qurtubi", "ar.ibnkathir", "ar.muyassar",
        "en.sahih", "en.hilali",
    }
    for edition in REFUSED:
        assert not tafseer_api.is_allowed_edition(edition)


def test_default_editions_are_cleared():
    assert DEFAULT_EDITIONS == ["ar.baghawi", "en.sahih"]
    assert "ar.muyassar" not in DEFAULT_EDITIONS


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", REFUSED)
async def test_client_refuses_without_upstream_call(no_network, edition):
    c = AlQuranCloudClient(use_hybrid_cache=False)
    r = await c.get_tafseer(112, 1, [edition])
    assert not r.success and r.error == EDITION_NOT_LICENSED and r.tafasir == []
    assert await c.get_surah_tafseer(112, edition) == []


def _fake_library(licensed):
    """_db_tafsir stand-in: None (refuse) unless the source is licensed."""
    async def fake(surah, ayah, source_id):
        if source_id not in licensed:
            return None
        return [(ayah or 1, f"passage of {source_id}")]
    return fake


@pytest.mark.asyncio
async def test_mixed_request_keeps_only_allowed(monkeypatch, no_network):
    monkeypatch.setattr(tafseer_api, "_db_tafsir", _fake_library({"baghawi_ar"}))
    c = AlQuranCloudClient(use_hybrid_cache=False)
    r = await c.get_tafseer(112, 1, ["ar.miqbas", "ar.baghawi"])
    assert r.success and [t.edition for t in r.tafasir] == ["ar.baghawi"]
    assert r.tafasir[0].text == "passage of baghawi_ar"


@pytest.mark.asyncio
async def test_unverified_source_is_refused_not_proxied(monkeypatch, no_network):
    """ar.muyassar is allowlisted but its source is not licence-verified."""
    monkeypatch.setattr(tafseer_api, "_db_tafsir", _fake_library({"baghawi_ar"}))
    c = AlQuranCloudClient(use_hybrid_cache=False)
    r = await c.get_tafseer(112, 1, ["ar.muyassar"])
    assert not r.success and r.error == EDITION_NOT_LICENSED and r.tafasir == []
    assert await c.get_surah_tafseer(112, "ar.muyassar") == []


@pytest.mark.asyncio
async def test_default_request_never_serves_muyassar(monkeypatch, no_network):
    seen = []

    async def fake(surah, ayah, source_id):
        seen.append(source_id)
        return [(ayah, "x")]

    async def fake_translation(surah, ayah, key):
        return [(ayah, "Say, He is Allah, [who is] One,", "1.1.2")]

    monkeypatch.setattr(tafseer_api, "_db_tafsir", fake)
    monkeypatch.setattr(tafseer_api, "_db_translation", fake_translation)
    r = await AlQuranCloudClient(use_hybrid_cache=False).get_tafseer(112, 1)
    assert [t.edition for t in r.tafasir] == ["ar.baghawi", "en.sahih"]
    assert seen == ["baghawi_ar"]


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
async def test_editions_list_is_the_servable_allowlist(client, monkeypatch):
    async def licensed():
        return frozenset({"baghawi_ar", "tabari_ar"})

    monkeypatch.setattr(tafseer_api, "_licensed_tafsir_ids", licensed)
    r = await client.get("/api/v1/tafseer/editions")
    assert r.status_code == 200
    body = r.json()
    ids = {e["identifier"] for e in body["editions"]}
    assert ids == {"ar.baghawi", "ar.tabari", "en.sahih", "en.hilali"}
    assert ids <= ALLOWED_EDITIONS and body["total"] == len(ids)
    for e in body["editions"]:
        assert e["author_en"] and e["author_ar"]


@pytest.mark.asyncio
async def test_editions_list_language_filter(client, monkeypatch):
    async def licensed():
        return frozenset({"baghawi_ar"})

    monkeypatch.setattr(tafseer_api, "_licensed_tafsir_ids", licensed)
    r = await client.get("/api/v1/tafseer/editions", params={"language": "ar"})
    assert [e["identifier"] for e in r.json()["editions"]] == ["ar.baghawi"]


@pytest.mark.asyncio
async def test_surah_route_refuses_unverified_source(client, monkeypatch, no_network):
    async def licensed():
        return frozenset({"baghawi_ar"})

    monkeypatch.setattr(tafseer_api, "_licensed_tafsir_ids", licensed)
    r = await client.get("/api/v1/tafseer/surah/112", params={"edition": "ar.muyassar"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "EDITION_NOT_LICENSED"


@pytest.mark.asyncio
async def test_muyassar_is_not_servable_in_this_database():
    """Against the real DB: the licence hold keeps ar.muyassar out of the list."""
    try:
        servable = await tafseer_api.servable_editions()
    except Exception as e:  # pragma: no cover
        pytest.skip(f"database unavailable: {type(e).__name__}")
    assert "ar.muyassar" not in servable
    assert set(servable) <= ALLOWED_EDITIONS
    assert set(LICENSED_DB_TAFSIR) >= {e for e in servable if e.startswith("ar.")}


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
