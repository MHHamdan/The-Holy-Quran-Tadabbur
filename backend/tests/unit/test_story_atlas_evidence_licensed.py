"""
Story-atlas evidence cites only enabled, licence-verified tafsir.

story_events.evidence pointed 62 events at the disabled, blocked English Ibn
Kathir, served by /api/v1/story-atlas/{cluster} as "In tafsir: Tafsir Ibn
Kathir (English)". Three layers now keep that out:

- StoryAtlasService filters every event's evidence at read time
  (app.services.story_atlas_evidence.filter_licensed_evidence);
- alembic r4a1b2c3d4e5 moves each pointer to the Arabic original of the same
  work (ibn_kathir_ar, same verse) when an enabled, licensed passage covers
  that verse, and drops it otherwise;
- seed_story_atlas.py cites ibn_kathir_ar and resolves every pointer against
  tafseer_chunks before writing it.

The sweep at the end crawls every public story, story-atlas, theme and
concept endpoint and asserts that no disabled or blocked source id appears in
any response.
"""
import asyncio
import importlib.util
import json
import re
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.services.story_atlas_evidence import (
    SAME_WORK_EDITION,
    _candidate,
    filter_licensed_evidence,
    parse_reference,
    remap_same_work,
)

ROOT = Path(__file__).resolve().parents[3]
SEED = ROOT / "backend" / "scripts" / "ingest" / "seed_story_atlas.py"
MIGRATION = ROOT / "backend" / "alembic" / "versions" / "r4a1b2c3d4e5_story_event_evidence_licensed.py"
MANIFEST = ROOT / "data" / "manifests" / "tafseer_sources.json"
REGISTRY = ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _enabled_ids() -> set:
    return set(json.loads(MANIFEST.read_text(encoding="utf-8"))["enabled_ids"])


def _blocked_registry_ids() -> set:
    src = REGISTRY.read_text(encoding="utf-8")
    out = set()
    for block in re.split(r"\n  \{\n", src):
        m = re.search(r"sourceId:\s*'([^']+)'", block)
        if m and (re.search(r"licenseStatus:\s*'blocked'", block) or re.search(r"notes:\s*'DO NOT DISPLAY", block)):
            out.add(m.group(1))
    return out


# --- pure helpers -------------------------------------------------------------

@pytest.mark.parametrize("ref,expected", [
    ("18:71", (18, 71, 71)),
    ("18:71-73", (18, 71, 73)),
    (" 2:255 ", (2, 255, 255)),
    ("0:1", None),
    ("115:1", None),
    ("18:73-71", None),
    ("ibn_kathir_en:18:71", None),
    ("", None),
    (None, None),
])
def test_parse_reference(ref, expected):
    assert parse_reference(ref) == expected


def test_candidate_keeps_only_public_pointer_keys():
    assert _candidate({"source_id": "tabari_ar", "reference": "18:71", "snippet": "paraphrase"}) == {
        "source_id": "tabari_ar", "reference": "18:71"}
    assert _candidate({"source_id": "tabari_ar", "reference": "nope"}) is None
    assert _candidate({"reference": "18:71"}) is None
    assert _candidate("ibn_kathir_en:18:71") is None


def test_remap_moves_only_the_same_work():
    ev = [
        {"source_id": "ibn_kathir_en", "reference": "18:71", "chunk_id": "x", "snippet": "y"},
        {"source_id": "jalalayn_en", "reference": "18:71"},
        {"source_id": "tabari_ar", "reference": "18:71"},
    ]
    assert remap_same_work(ev) == [
        {"source_id": "ibn_kathir_ar", "reference": "18:71"},
        {"source_id": "jalalayn_en", "reference": "18:71"},  # no same-work Arabic edition: left to the filter
        {"source_id": "tabari_ar", "reference": "18:71"},
    ]
    assert SAME_WORK_EDITION == {"ibn_kathir_en": "ibn_kathir_ar"}


# --- seed ---------------------------------------------------------------------

def test_seed_cites_only_enabled_sources_without_snippets():
    seed = _load(SEED, "seed_story_atlas_r4a")
    enabled = _enabled_ids()
    n = 0
    for cluster_id, events in seed.STORY_EVENTS.items():
        for ev in events:
            assert ev["evidence"], f"{ev['id']} cites no tafsir"
            for e in ev["evidence"]:
                n += 1
                assert set(e) == {"source_id", "reference"}, ev["id"]
                assert e["source_id"] in enabled, (ev["id"], e)
                assert parse_reference(e["reference"]), (ev["id"], e)
    assert n >= 62
    assert '"source_id": "ibn_kathir_en"' not in SEED.read_text(encoding="utf-8")


def test_seed_resolves_evidence_before_writing():
    src = SEED.read_text(encoding="utf-8")
    assert "resolve_seed_evidence_sync(session" in src


# --- migration ----------------------------------------------------------------

def test_migration_chains_after_r3d():
    mod = _load(MIGRATION, "r4a_migration")
    assert mod.revision == "r4a1b2c3d4e5"
    assert mod.down_revision == "r3d1a2b3c4d5"


@pytest.mark.asyncio
async def test_migration_is_idempotent_and_leaves_only_licensed_evidence():
    from app.db import database

    mod = _load(MIGRATION, "r4a_migration")
    async with database.AsyncSessionLocal() as session:
        try:
            await session.execute(text("SELECT 1 FROM story_events LIMIT 1"))
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        try:
            for sql in mod.UPGRADE_SQL:
                await session.execute(text(sql))
            changed = [(await session.execute(text(sql))).rowcount for sql in mod.UPGRADE_SQL]
            assert changed == [0] * len(mod.UPGRADE_SQL)
            bad = (await session.execute(text("""
                SELECT count(*) FROM story_events se, jsonb_array_elements(se.evidence) e
                 WHERE e ? 'snippet'
                    OR NOT EXISTS (
                       SELECT 1 FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id
                        WHERE s.id = e->>'source_id' AND s.is_enabled = 1 AND s.license_verified = 1
                          AND c.sura_no = split_part(e->>'reference', ':', 1)::int
                          AND c.aya_start <= split_part(split_part(e->>'reference', ':', 2), '-', 1)::int
                          AND c.aya_end >= split_part(split_part(e->>'reference', ':', 2), '-', 1)::int)
            """))).scalar()
            assert bad == 0
            en = (await session.execute(text(
                "SELECT count(*) FROM story_events WHERE evidence::text LIKE '%ibn_kathir_en%'"
            ))).scalar()
            assert en == 0
        finally:
            await session.rollback()


# --- read-time filter -----------------------------------------------------------

@pytest.mark.asyncio
async def test_filter_drops_disabled_unresolvable_and_snippets():
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            covered = (await session.execute(text(
                "SELECT c.sura_no, c.aya_start FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id "
                "WHERE s.id = 'ibn_kathir_ar' AND s.is_enabled = 1 AND s.license_verified = 1 "
                "ORDER BY c.sura_no, c.aya_start LIMIT 1"
            ))).first()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        if covered is None:
            pytest.skip("ibn_kathir_ar not seeded")
        ref = f"{covered[0]}:{covered[1]}"
        out = await filter_licensed_evidence(session, [
            [{"source_id": "ibn_kathir_ar", "reference": ref, "snippet": "not a quotation"}],
            [{"source_id": "ibn_kathir_en", "reference": ref}],
            [{"source_id": "jalalayn_en", "reference": ref}],
            [{"source_id": "ibn_kathir_ar", "reference": "not-a-ref"}],
            [{"source_id": "ibn_kathir_ar", "chunk_id": "0000000000000000"}],
            None,
            "garbage",
        ])
    assert out == [[{"source_id": "ibn_kathir_ar", "reference": ref}], [], [], [], [], [], []]


# --- API ------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=120) as c:
        yield c


async def _disabled_db_ids() -> set:
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            rows = await session.execute(text(
                "SELECT id FROM tafseer_sources WHERE NOT (is_enabled = 1 AND license_verified = 1)"
            ))
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        return set(rows.scalars())


@pytest.mark.asyncio
async def test_story_atlas_evidence_resolves_to_enabled_sources(client):
    r = await client.get("/api/v1/story-atlas", params={"limit": 100})
    assert r.status_code == 200
    clusters = r.json()["clusters"]
    if not clusters:
        pytest.skip("story atlas not seeded")
    enabled = _enabled_ids()
    for cl in clusters:
        detail = (await client.get(f"/api/v1/story-atlas/{cl['id']}")).json()
        graph = (await client.get(f"/api/v1/story-atlas/{cl['id']}/graph")).json()
        timeline = (await client.get(f"/api/v1/story-atlas/{cl['id']}/timeline")).json()
        lists = [e["evidence"] for e in detail["events"]]
        lists += [n["data"]["evidence"] for n in graph["nodes"] if n["type"] == "event"]
        lists += [s["evidence"] for s in timeline]
        for evidence in lists:
            for e in evidence:
                assert "snippet" not in e, (cl["id"], e)
                assert e["source_id"] in enabled, (cl["id"], e)


async def _crawl(client):
    """(url, body) for every public story / story-atlas / theme / concept GET."""
    out = []
    gate = asyncio.Semaphore(16)  # tests use NullPool: one connection per request

    async def get(url):
        async with gate:
            r = await client.get(url)
        out.append((url, r.text))
        return r

    async def get_all(urls):
        await asyncio.gather(*(get(u) for u in urls))

    lists = await asyncio.gather(
        get("/api/v1/story-atlas?limit=100"),
        get("/api/v1/stories/"),
        get("/api/v1/themes?limit=200"),
        get("/api/v1/concepts?limit=200"),
    )
    clusters = lists[0].json().get("clusters", [])
    stories = lists[1].json()
    stories = stories.get("stories", []) if isinstance(stories, dict) else stories
    themes = lists[2].json().get("themes", [])
    concepts = lists[3].json().get("concepts", [])
    urls = [
        "/api/v1/story-atlas/facets",
        "/api/v1/stories/categories",
        "/api/v1/stories/themes",
        "/api/v1/concepts/miracles/all",
        "/api/v1/concepts/miracles/tafsir-sources",
    ]
    urls += [f"/api/v1/story-atlas/{cl['id']}{s}" for cl in clusters
             for s in ("", "/graph", "/timeline", "/related", "/similar")]
    urls += [f"/api/v1/stories/{st['id']}{s}" for st in stories
             for s in ("", "/connections", "/graph", "/timeline", "/cross-connections")]
    urls += [f"/api/v1/themes/{th['id']}{s}" for th in themes
             for s in ("", "/segments", "/consequences", "/tafsir", "/stories", "/graph")]
    urls += [f"/api/v1/concepts/{co['id']}{s}" for co in concepts for s in ("", "/occurrences")]
    await get_all(urls)
    return out


@pytest.mark.asyncio
async def test_no_disabled_or_blocked_source_in_any_public_story_theme_concept_response(client):
    banned = (await _disabled_db_ids()) | _blocked_registry_ids()
    banned -= _enabled_ids()  # never ban a source the manifest enables
    assert "ibn_kathir_en" in banned
    pages = await _crawl(client)
    assert len(pages) > 10
    leaks = [(url, sid) for url, body in pages for sid in banned
             if re.search(rf"(?<![A-Za-z0-9_]){re.escape(sid)}(?![A-Za-z0-9_])", body)]
    assert leaks == []
