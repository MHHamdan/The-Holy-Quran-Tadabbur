"""
Reader tafsir editions are served only from sources with a recorded licence.

- Every edition in TAFSIR_EDITIONS (and in the reader / Mushaf lists) names a
  manifest source in db_source_id whose licence is recorded (not pending,
  verified_date set), listed in enabled_ids, and registered in
  sourceRegistry.ts without a display block.
- Tafsir as-Sa'di and the Arabic al-Jalalayn (no recorded licence) are gone
  from the backend, the reader panel, the Mushaf list and the quran-com proxy.
- /tafseer/external/verse serves the stored, licensed passage first
  (source "tadabbur_library" with source_id + chunk_id) and refuses an
  edition whose tafseer_sources row is disabled or unverified.
- Al-Muyassar's licence statement is the same (pending owner confirmation,
  non-commercial display under the distribution policy, not cleared) in the
  manifest, the registry and the DB migration.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.tafsir_api import ALLOWED_QURAN_COM_IDS, TAFSIR_EDITIONS

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((ROOT / "data" / "manifests" / "tafseer_sources.json").read_text(encoding="utf-8"))
REGISTRY = (ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts").read_text(encoding="utf-8")
EDITIONS_TSX = (ROOT / "frontend" / "src" / "components" / "quran" / "tafsirEditions.tsx").read_text(encoding="utf-8")
MUSHAF_TSX = (ROOT / "frontend" / "src" / "pages" / "MushafPage.tsx").read_text(encoding="utf-8")
MIGRATION = ROOT / "backend" / "alembic" / "versions" / "r3d1a2b3c4d5_tafsir_provenance_story_evidence.py"

UNLICENSED = ("saadi", "jalalayn")


def _registry_entry(source_id: str) -> str:
    m = re.search(r"\{\s*sourceId: '" + re.escape(source_id) + r"',.*?\n  \},", REGISTRY, re.S)
    assert m, f"{source_id} missing from sourceRegistry.ts"
    return m.group(0)


def _manifest_entry(source_id: str) -> dict:
    entry = next((s for s in MANIFEST["sources"] if s["id"] == source_id), None)
    assert entry, f"{source_id} missing from tafseer_sources.json"
    return entry


def _migration():
    spec = importlib.util.spec_from_file_location("r3d_migration", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- static checks -----------------------------------------------------------

@pytest.mark.parametrize("edition_id", sorted(TAFSIR_EDITIONS))
def test_every_edition_maps_to_a_recorded_licence(edition_id):
    info = TAFSIR_EDITIONS[edition_id]
    assert info.db_source_id, f"{edition_id} has no db_source_id"
    entry = _manifest_entry(info.db_source_id)
    lic = entry["license"]
    assert not str(lic["type"]).startswith("pending"), edition_id
    assert lic["verified_date"], edition_id
    assert info.db_source_id in MANIFEST["enabled_ids"], edition_id
    reg = _registry_entry(info.db_source_id)
    assert "licenseStatus: 'blocked'" not in reg
    assert "DO NOT DISPLAY" not in reg


def test_unlicensed_editions_removed_everywhere():
    for eid in UNLICENSED:
        assert eid not in TAFSIR_EDITIONS
        assert f"id: '{eid}'" not in EDITIONS_TSX
        assert f"id: '{eid}'" not in MUSHAF_TSX
    # Quran.com ids of Sa'di (91) are no longer proxied.
    assert 91 not in ALLOWED_QURAN_COM_IDS


def test_no_edition_offers_unconfirmed_tafsir_audio():
    assert not any(e.has_audio for e in TAFSIR_EDITIONS.values())


def test_frontend_editions_match_backend_with_same_db_source_ids():
    ids = re.findall(r"\n    id: '([a-z_]+)',\n(?:    db_source_id: '([a-z_]+)',\n)?", EDITIONS_TSX)
    assert {i for i, _ in ids} == set(TAFSIR_EDITIONS)
    for eid, db_id in ids:
        assert db_id == TAFSIR_EDITIONS[eid].db_source_id, eid
    mushaf_ids = set(re.findall(r"\{ id: '([a-z_]+)', translationKey: 'tafseer_", MUSHAF_TSX))
    assert mushaf_ids and mushaf_ids <= set(TAFSIR_EDITIONS)


def test_muyassar_statements_agree_and_are_not_cleared():
    entry = _manifest_entry("muyassar_ar")
    assert entry["status"] == "pending_owner_confirmation"
    assert entry["license"]["type"] == "publisher_terms_non_commercial"
    assert entry["license"]["commercial_use"] == "not_permitted"
    assert entry["license"]["license_url"] in (None, "")
    assert "distribution-policy.md" in entry["license"]["notes"]
    assert "Blocked until" not in entry["fallback"]["message"]
    reg = _registry_entry("muyassar_ar")
    assert "licenseStatus: 'cleared'" not in reg
    assert "pending owner confirmation" in reg
    assert "distribution-policy.md" in reg
    assert "no restrictive terms" not in reg
    lic = _migration().MUYASSAR_LICENSE
    assert "pending owner confirmation" in lic and "distribution-policy.md" in lic and len(lic) <= 200


def test_baghawi_manifest_records_dataset_provenance():
    prov = _manifest_entry("baghawi_ar")["provenance"]
    assert prov["dataset"] == "riotu-lab/Quran-Tafseers"
    assert re.fullmatch(r"[0-9a-f]{40}", prov["dataset_revision"])
    assert re.fullmatch(r"[0-9a-f]{64}", prov["file_sha256"])
    assert prov["dataset_license"] == "apache-2.0"


# --- API ---------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", UNLICENSED)
async def test_unlicensed_edition_404(client, edition):
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": edition})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_external_editions_expose_db_source_ids(client):
    r = await client.get("/api/v1/tafseer/external/editions")
    assert r.status_code == 200
    eds = r.json()["editions"]
    assert {e["id"] for e in eds} == set(TAFSIR_EDITIONS)


async def _source_row(source_id: str):
    from sqlalchemy import text

    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            row = (await session.execute(
                text("SELECT is_enabled, license_verified FROM tafseer_sources WHERE id = :i"), {"i": source_id}
            )).first()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        n = (await session.execute(
            text("SELECT count(*) FROM tafseer_chunks WHERE source_id = :i AND sura_no = 2 AND aya_start <= 255 AND aya_end >= 255"),
            {"i": source_id},
        )).scalar()
    return row, n


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", ["baghawi", "ibn_kathir"])
async def test_verse_served_from_licensed_library(client, edition):
    db_id = TAFSIR_EDITIONS[edition].db_source_id
    row, n = await _source_row(db_id)
    if not row or not n:
        pytest.skip(f"{db_id} not seeded in this DB")
    assert row == (1, 1)
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": edition})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "tadabbur_library"
    assert body["source_id"] == db_id and body["chunk_id"]
    assert body["text"]
    assert body["edition"]["db_source_id"] == db_id
    assert body["audio_url"] is None


@pytest.mark.asyncio
async def test_disabled_source_is_refused_not_proxied(client, monkeypatch):
    from app.api.routes import tafseer as route

    async def disabled(*a, **k):
        raise route._EditionNotServable("muyassar_ar")

    async def no_proxy(*a, **k):  # pragma: no cover - must not be reached
        raise AssertionError("a disabled source must not be proxied")

    monkeypatch.setattr(route, "_local_licensed_passage", disabled)
    monkeypatch.setattr(route.external_tafsir_service, "get_tafsir", no_proxy)
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": "muyassar"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "EDITION_NOT_LICENSED"


@pytest.mark.asyncio
async def test_baghawi_seeded_row_records_dataset_and_licence():
    from sqlalchemy import text

    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            row = (await session.execute(text(
                "SELECT is_enabled, license_verified, license_type, source_url, version_tag "
                "FROM tafseer_sources WHERE id = 'baghawi_ar'"
            ))).first()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    if row is None:
        pytest.skip("baghawi_ar not seeded in this DB")
    enabled, verified, ltype, source_url, version = row
    prov = _manifest_entry("baghawi_ar")["provenance"]
    assert (enabled, verified, ltype) == (1, 1, "public_domain_classical")
    assert source_url.startswith("https://huggingface.co/datasets/riotu-lab/Quran-Tafseers/")
    assert version == prov["dataset_revision"]


@pytest.mark.asyncio
async def test_every_tafseer_source_records_where_its_text_came_from():
    from sqlalchemy import text

    from app.db import database

    mod = _migration()
    async with database.AsyncSessionLocal() as session:
        try:
            await session.execute(text(mod.UPGRADE_SQL[0]))
            missing = (await session.execute(text(
                "SELECT id FROM tafseer_sources WHERE source_url IS NULL AND cdn_url IS NOT NULL"
            ))).scalars().all()
            await session.execute(text(mod.UPGRADE_SQL[1]))
            lic = (await session.execute(text(
                "SELECT license_type, license, is_enabled FROM tafseer_sources WHERE id = 'muyassar_ar'"
            ))).first()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        finally:
            await session.rollback()
    assert missing == []
    if lic:
        assert lic[0] == "publisher_terms_non_commercial"
        assert lic[1] == mod.MUYASSAR_LICENSE
        assert lic[2] == 1  # still displayed (owner decision); the migration never toggles it
