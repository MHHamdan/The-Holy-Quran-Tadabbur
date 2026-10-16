"""
Public story evidence resolves only to enabled, licence-verified tafsir.

The Dhul-Qarnayn story graph cited the disabled English Ibn Kathir with
pseudo ids ("ibn_kathir_en:18:83-84") that resolved to nothing, and segment
and cross-story evidence still held chunk ids of disabled sources. The routes
now drop anything that is not a real chunk of an enabled, licensed source;
migration r3d1a2b3c4d5 re-derives the pseudo ids by verse reference from the
same work's enabled edition and prunes the disabled ids; the seed script no
longer carries the English source or hand-written "snippets".
"""
import importlib.util
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app

ROOT = Path(__file__).resolve().parents[3]
SEED = ROOT / "backend" / "scripts" / "ingest" / "seed_story_graphs.py"
MIGRATION = ROOT / "backend" / "alembic" / "versions" / "r3d1a2b3c4d5_tafsir_provenance_story_evidence.py"

ENABLED_IDS_SQL = """
SELECT c.chunk_id FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id
 WHERE c.chunk_id = ANY(:ids) AND s.is_enabled = 1 AND s.license_verified = 1
"""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_seed_cites_no_disabled_source_and_no_snippets():
    src = SEED.read_text(encoding="utf-8")
    assert "ibn_kathir_en" not in src
    assert '"snippet":' not in src
    seed = _load(SEED, "seed_story_graphs")
    for seg in seed.DHUL_QARNAYN_SEGMENTS:
        for ev in seg.get("evidence_sources", []):
            assert set(ev) == {"source_id", "reference"}, seg["id"]
    for conn in seed.DHUL_QARNAYN_CONNECTIONS:
        for ref in conn["evidence_chunk_ids"]:
            assert seed._REF_RE.match(ref), ref


ADD_MISSING_EVENTS = ROOT / "backend" / "scripts" / "ingest" / "add_missing_events.py"


def test_add_missing_events_cites_no_blocked_source_and_no_snippets():
    """The ingest script must not reintroduce blocked refs or translated snippets."""
    src = ADD_MISSING_EVENTS.read_text(encoding="utf-8")
    for blocked in ("ibn_kathir_en", "jalalayn_en", "ibn_abbas_en"):
        assert blocked not in src
    assert '"snippet":' not in src
    assert "resolve_seed_evidence_sync" in src
    mod = _load(ADD_MISSING_EVENTS, "add_missing_events")
    n = 0
    for events in mod.NEW_EVENTS.values():
        for event in events:
            for ev in event.get("evidence", []):
                assert set(ev) == {"source_id", "reference"}, event["id"]
                assert ev["source_id"] == "ibn_kathir_ar", event["id"]
                s, a = map(int, ev["reference"].split(":"))
                assert s == event["sura_no"], event["id"]
                n += 1
    assert n == 27


def test_migration_chains_after_story_prune():
    mod = _load(MIGRATION, "r3d_migration")
    assert mod.revision == "r3d1a2b3c4d5"
    # Chained after r3b1c2d3e4f5 when the round-3 migrations were linearised.
    assert mod.down_revision == "r3b1c2d3e4f5"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _enabled(ids):
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        return set((await session.execute(text(ENABLED_IDS_SQL), {"ids": list(ids)})).scalars())


@pytest.mark.asyncio
async def test_story_connections_expose_only_licensed_evidence(client):
    r = await client.get("/api/v1/stories/story_dhulqarnayn/connections")
    if r.status_code == 404:
        pytest.skip("story graph not seeded")
    assert r.status_code == 200
    ids = [cid for c in r.json() for cid in c["evidence_chunk_ids"]]
    assert not any(":" in cid for cid in ids), "pseudo ids must not be exposed"
    if ids:
        assert set(ids) <= await _enabled(ids)


@pytest.mark.asyncio
@pytest.mark.parametrize("story_id", ["story_adam", "story_musa", "story_ibrahim", "story_yusuf"])
async def test_cross_connections_expose_only_licensed_evidence(client, story_id):
    r = await client.get(f"/api/v1/stories/{story_id}/cross-connections")
    assert r.status_code == 200
    ids = [cid for c in r.json() for cid in c["evidence_chunk_ids"]]
    if not ids:
        pytest.skip("no cross-story evidence in this DB")
    assert set(ids) <= await _enabled(ids)


@pytest.mark.asyncio
async def test_story_segment_evidence_is_licensed(client):
    r = await client.get("/api/v1/stories/story_dhulqarnayn")
    if r.status_code == 404:
        pytest.skip("story not seeded")
    ids = [e["chunk_id"] for s in r.json()["segments"] for e in s["evidence"]]
    sources = {e["source_id"] for s in r.json()["segments"] for e in s["evidence"]}
    assert "ibn_kathir_en" not in sources
    if ids:
        assert set(ids) <= await _enabled(ids)


@pytest.mark.asyncio
async def test_migration_is_idempotent_and_leaves_no_disabled_evidence():
    from app.db import database

    mod = _load(MIGRATION, "r3d_migration")
    async with database.AsyncSessionLocal() as session:
        try:
            await session.execute(text("SELECT 1 FROM story_connections LIMIT 1"))
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        try:
            for sql in mod.UPGRADE_SQL:
                await session.execute(text(sql))
            # A second run changes nothing.
            changed = [(await session.execute(text(sql))).rowcount for sql in mod.UPGRADE_SQL]
            assert changed == [0] * len(mod.UPGRADE_SQL)
            disabled = (await session.execute(text("""
                SELECT count(*) FROM (
                  SELECT unnest(evidence_chunk_ids) x FROM story_segments
                  UNION ALL SELECT unnest(evidence_chunk_ids) FROM cross_story_connections
                ) u JOIN tafseer_chunks c ON c.chunk_id = u.x JOIN tafseer_sources s ON s.id = c.source_id
                WHERE NOT (s.is_enabled = 1 AND s.license_verified = 1)
            """))).scalar()
            assert disabled == 0
            en_refs = (await session.execute(text(
                "SELECT count(*) FROM story_segments WHERE evidence_sources::text LIKE '%ibn_kathir_en%' "
                "OR evidence_sources::text LIKE '%snippet%'"
            ))).scalar()
            assert en_refs == 0
        finally:
            await session.rollback()
