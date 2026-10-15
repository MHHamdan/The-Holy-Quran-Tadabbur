"""
Story evidence resolution + cross-story connection review gating.

A. resolve_story_evidence.py maps the manifest's legacy citations
   (ibn_kathir:S:A-B, source ids ibn_kathir/tabari/qurtubi/saadi) onto
   tafseer_chunks source ids. saadi has no corpus source and must be dropped,
   never substituted.
B. GET /stories/{id} exposes segment evidence with source title + author and
   every exposed chunk id exists in tafseer_chunks.
C. GET /stories/{id}/cross-connections hides connections flagged
   needs_review in the manifest, and returns verse refs + provenance.
"""
import importlib.util
import json
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

ROOT = Path(__file__).resolve().parents[3]
RESOLVER = ROOT / "backend" / "scripts" / "ingest" / "resolve_story_evidence.py"
MANIFEST = ROOT / "data" / "manifests" / "stories.json"


def _resolver():
    spec = importlib.util.spec_from_file_location("resolve_story_evidence", RESOLVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- A. resolver planning (no DB) --------------------------------------------

def test_parse_ref_variants():
    r = _resolver()
    assert r.parse_ref("ibn_kathir:2:30-33") == ("ibn_kathir", 2, 30, 33)
    assert r.parse_ref("2:30") == (None, 2, 30, 30)
    assert r.parse_ref("115:1") is None
    assert r.parse_ref("2:33-30") is None
    assert r.parse_ref("garbage") is None


def test_saadi_is_dropped_not_substituted():
    r = _resolver()
    manifest = {"stories": [{"id": "s", "segments": [{"id": "seg", "evidence": [
        {"source_id": "saadi", "ayah_ref": "2:30-33"},
        {"source_id": "ibn_kathir", "ayah_ref": "2:30-33"},
    ]}]}]}
    seg_plan, _, warnings = r.plan(manifest)
    assert seg_plan["seg"] == [("ibn_kathir", 2, 30, 33)]
    assert any("saadi" in w for w in warnings)
    assert r.corpus_sources_for("saadi", ["ibn_kathir_ar"]) == ()


def test_only_enabled_corpus_sources_are_used():
    r = _resolver()
    assert r.corpus_sources_for("ibn_kathir", ["ibn_kathir_ar"]) == ("ibn_kathir_ar",)
    assert r.corpus_sources_for("tabari", ["ibn_kathir_ar"]) == ()


def test_manifest_flags_the_five_doubtful_connections():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    flagged = {c["id"] for c in data["inter_story_connections"] if c.get("needs_review")}
    assert flagged >= {
        "conn_luqman_ibrahim",
        "conn_ibrahim_ismail_sacrifice",
        "conn_nuh_ibrahim_destruction",
        "conn_musa_sabbath",
        "conn_isa_muhammad_lineage",
    }


# --- B/C. API (shared dev DB; skips when stories are not seeded) --------------

pytestmark_api = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytestmark_api
async def test_story_segments_expose_attributed_evidence(client: AsyncClient):
    r = await client.get("/api/v1/stories/story_adam")
    if r.status_code == 404:
        pytest.skip("stories not seeded")
    assert r.status_code == 200
    segs = r.json()["segments"]
    with_evidence = [s for s in segs if s.get("evidence")]
    if not with_evidence:
        pytest.skip("story evidence not resolved in this DB (run resolve_story_evidence.py)")
    ev = with_evidence[0]["evidence"][0]
    assert ev["title"] and ev["author"] and ev["source_id"] and ev["chunk_id"]
    # never the tafsir text itself
    assert "content_ar" not in ev and "content_en" not in ev


@pytestmark_api
async def test_every_exposed_evidence_chunk_exists():
    from sqlalchemy import select

    from app.db.database import get_async_session_context
    from app.models.story import StorySegment
    from app.models.tafseer import TafseerChunk

    async with get_async_session_context() as session:
        ids = set()
        for (chunk_ids,) in (await session.execute(select(StorySegment.evidence_chunk_ids))).all():
            ids.update(chunk_ids or [])
        if not ids:
            pytest.skip("story evidence not resolved in this DB")
        found = set(
            (await session.execute(select(TafseerChunk.chunk_id).where(TafseerChunk.chunk_id.in_(ids)))).scalars()
        )
    assert ids - found == set()


@pytestmark_api
async def test_cross_connections_hide_needs_review(client: AsyncClient):
    r = await client.get("/api/v1/stories/story_luqman/cross-connections")
    assert r.status_code == 200
    rows = r.json()
    assert not any(
        {c["source_story_id"], c["target_story_id"]} == {"story_luqman", "story_ibrahim"} for c in rows
    )
    for c in rows:
        assert c["provenance"] == "analytical"
        assert "verse_refs" in c and "evidence_chunk_ids" in c


@pytestmark_api
async def test_cross_connections_review_flag_can_include(client: AsyncClient):
    r = await client.get("/api/v1/stories/story_luqman/cross-connections?include_needs_review=true")
    assert r.status_code == 200
