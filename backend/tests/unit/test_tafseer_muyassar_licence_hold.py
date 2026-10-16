"""
Al-Muyassar is on licence hold: not verified, not the default, not served.

The final release audit (P1) found tafseer_sources.muyassar_ar enabled with
license_verified=1 and used as the reader default, while its licence read
"KFGQPC terms pending owner confirmation, not cleared". Interim fix, pending
the owner's decision:

- alembic r5c1a2b3c4d5 sets license_verified=0 (row, is_enabled and text kept);
- the reader, Mushaf and API default edition is Tafsir al-Baghawi;
- every licensed-only path (reader /external/verse, /tafseer/compare, the AI
  tafsir assistant grounding, story-atlas evidence, /tafseer/{s}/{a}) treats
  it as unlicensed.

The DB checks apply the migration's SQL inside a transaction that is rolled
back, so the shared database is not changed by the test.
"""
import importlib.util
import inspect
import re
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import tafseer as route
from app.main import app
from app.services import tafseer_api

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "frontend" / "src"
MIGRATION = ROOT / "backend" / "alembic" / "versions" / "r5c1a2b3c4d5_muyassar_licence_not_verified.py"


def _migration():
    spec = importlib.util.spec_from_file_location("r5c_migration", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- defaults ----------------------------------------------------------------

def _query_default(fn, name):
    return inspect.signature(fn).parameters[name].default.default


def test_api_default_editions_are_cleared():
    assert _query_default(route.get_external_tafsir, "edition") == "baghawi"
    assert "muyassar" not in _query_default(route.compare_external_tafsirs, "editions")
    assert _query_default(route.get_surah_tafseer, "edition") == "ar.baghawi"
    assert tafseer_api.DEFAULT_EDITIONS[0] == "ar.baghawi"


def test_frontend_defaults_are_not_muyassar():
    editions = (FRONTEND / "components" / "quran" / "tafsirEditions.tsx").read_text(encoding="utf-8")
    first = re.search(r"TAFSIR_EDITIONS: TafsirEdition\[\] = \[\s*\{\s*id: '([a-z_]+)'", editions)
    assert first and first.group(1) == "baghawi"
    assert "id: 'muyassar'" not in editions

    mushaf = (FRONTEND / "pages" / "MushafPage.tsx").read_text(encoding="utf-8")
    assert "{ id: 'muyassar'" not in mushaf
    assert "useState('muyassar')" not in mushaf
    assert "useState(DEFAULT_TAFSIR_EDITION_ID)" in mushaf

    quran = (FRONTEND / "pages" / "QuranPage.tsx").read_text(encoding="utf-8")
    assert "edition=muyassar" not in quran and ":muyassar`" not in quran


def test_migration_is_additive_and_idempotent():
    mod = _migration()
    assert mod.down_revision == "r4a1b2c3d4e5"
    sql = " ".join(mod.UPGRADE_SQL)
    assert "license_verified = 0" in sql
    assert "IS DISTINCT FROM" in sql  # touches only a row that still needs it
    assert "DELETE" not in sql.upper() and "is_enabled" not in sql


# --- licensed-only paths against the database ----------------------------------

@pytest_asyncio.fixture
async def held_session():
    """Session with r5c applied in a transaction that is always rolled back."""
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            row = (await session.execute(text(
                "SELECT count(*) FROM tafseer_chunks WHERE source_id = 'muyassar_ar' "
                "AND sura_no = 2 AND aya_start <= 255 AND aya_end >= 255"
            ))).scalar()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        if not row:
            pytest.skip("muyassar_ar 2:255 not seeded in this DB")
        try:
            for sql in _migration().UPGRADE_SQL:
                await session.execute(text(sql))
            yield session
        finally:
            await session.rollback()


@pytest.mark.asyncio
async def test_row_is_kept_but_unverified(held_session):
    enabled, verified, n = (await held_session.execute(text(
        "SELECT s.is_enabled, s.license_verified, "
        "(SELECT count(*) FROM tafseer_chunks c WHERE c.source_id = s.id) "
        "FROM tafseer_sources s WHERE s.id = 'muyassar_ar'"
    ))).one()
    assert (enabled, verified) == (1, 0)
    assert n > 6000  # stored text kept


@pytest.mark.asyncio
async def test_compare_excludes_muyassar(held_session):
    from app.services.tafsir_comparison import tafsir_comparison_service

    result = await tafsir_comparison_service.compare_verse(held_session, surah=2, ayah=255)
    ids = {e["source_id"] for e in result["entries"]}
    assert "muyassar_ar" not in ids
    assert all(e["license_verified"] for e in result["entries"])


@pytest.mark.asyncio
async def test_reader_passage_refused(held_session):
    with pytest.raises(route._EditionNotServable):
        await route._local_licensed_passage(held_session, "muyassar_ar", 2, 255)


@pytest.mark.asyncio
async def test_ai_assistant_has_no_grounding(held_session):
    assert await route._load_grounding(held_session, 2, 255, "muyassar_ar") is None


@pytest.mark.asyncio
async def test_story_evidence_drops_muyassar(held_session):
    from app.services.story_atlas_evidence import filter_licensed_evidence

    kept = await filter_licensed_evidence(
        held_session, [[{"source_id": "muyassar_ar", "reference": "2:255"}]]
    )
    assert kept == [[]]


# --- live state of this database (after the SQL was applied to it) -------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _verified():
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            return (await session.execute(text(
                "SELECT license_verified FROM tafseer_sources WHERE id = 'muyassar_ar'"
            ))).scalar_one_or_none()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")


@pytest.mark.asyncio
async def test_reader_endpoint_refuses_muyassar_and_defaults_to_baghawi(client):
    verified = await _verified()
    if verified is None:
        pytest.skip("muyassar_ar not seeded in this DB")
    if verified:
        pytest.skip("r5c1a2b3c4d5 not applied to this DB")
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": "muyassar"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "EDITION_NOT_LICENSED"
    r = await client.get("/api/v1/tafseer/external/verse/2/255")
    if r.status_code == 404 and r.json()["detail"]["code"] == "EDITION_NOT_SEEDED":
        pytest.skip("baghawi_ar not seeded in this DB")
    assert r.status_code == 200
    assert r.json()["source_id"] == "baghawi_ar"
