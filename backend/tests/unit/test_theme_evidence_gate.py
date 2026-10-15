"""
Theme content is an analytical study aid, not tafsir: its claim text is only
served when it cites a real, enabled, licensed tafsir chunk.

- Segment summaries / reasons are withheld when the segment's evidence ids do
  not resolve; owner-review withholds stay in force regardless.
- Evidence "snippets" (hand-typed, some of them Qur'an text typed from
  memory) are never served.
- Divine-consequence statements without real evidence are not served.
- /themes/{id}/tafsir never returns text from a disabled source (the
  unlicensed English Ibn Kathir).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.routes.themes import SUMMARY_WITHHELD_SEGMENT_IDS, _public_optional_text, _public_summary
from app.main import app


def test_public_summary_gate():
    sourced = {"seg_a": 2}
    assert _public_summary("seg_a", "claim", sourced) == "claim"
    assert _public_summary("seg_b", "claim", sourced) == ""
    assert _public_optional_text("seg_b", "why", sourced) is None
    withheld = next(iter(SUMMARY_WITHHELD_SEGMENT_IDS))
    assert _public_summary(withheld, "claim", {withheld: 3}) == ""
    # Without an evidence map (legacy callers) only the owner withholds apply.
    assert _public_summary("seg_b", "claim") == "claim"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _segments(client, theme_id):
    r = await client.get(f"/api/v1/themes/{theme_id}/segments")
    if r.status_code != 200 or not r.json()["segments"]:
        pytest.skip(f"{theme_id} has no segments in this DB")
    return r.json()["segments"]


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_id", ["theme_tawheed", "theme_sabr", "theme_salah", "theme_birr_walidayn"])
async def test_summaries_only_with_resolvable_evidence(client, theme_id):
    for s in await _segments(client, theme_id):
        if s["summary_en"] or s["summary_ar"] or s["reasons_ar"]:
            assert s["evidence_count"] > 0, s["id"]
        if s["id"] in SUMMARY_WITHHELD_SEGMENT_IDS:
            assert s["summary_en"] == "" and s["summary_ar"] == ""


@pytest.mark.asyncio
async def test_segment_evidence_has_no_snippets(client):
    for s in await _segments(client, "theme_tawheed"):
        r = await client.get(f"/api/v1/themes/theme_tawheed/segments/{s['id']}/evidence")
        assert r.status_code == 200
        for src in r.json()["evidence_sources"]:
            assert "snippet" not in src


@pytest.mark.asyncio
async def test_unsourced_consequences_are_not_served(client):
    from sqlalchemy import text

    from app.db import database

    r = await client.get("/api/v1/themes/theme_tawheed/consequences")
    assert r.status_code == 200
    served = {c["id"] for c in r.json()}
    if not served:
        return
    async with database.AsyncSessionLocal() as session:
        ok = set((await session.execute(text("""
            SELECT DISTINCT tc.id FROM theme_consequences tc, unnest(tc.evidence_chunk_ids) x
              JOIN tafseer_chunks c ON c.chunk_id = x JOIN tafseer_sources s ON s.id = c.source_id
             WHERE s.is_enabled = 1 AND s.license_verified = 1
        """))).scalars())
    assert served <= ok


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_id", ["theme_tawheed", "theme_sabr"])
async def test_thematic_tafsir_serves_only_enabled_sources(client, theme_id):
    from sqlalchemy import text

    from app.db import database

    r = await client.get(f"/api/v1/themes/{theme_id}/tafsir")
    if r.status_code == 404:
        pytest.skip("theme not seeded")
    assert r.status_code == 200
    used = set(r.json()["sources_used"])
    async with database.AsyncSessionLocal() as session:
        enabled = set((await session.execute(text(
            "SELECT id FROM tafseer_sources WHERE is_enabled = 1 AND license_verified = 1"
        ))).scalars())
    assert used <= enabled
    assert "ibn_kathir_en" not in used
    # The disabled source cannot be requested explicitly either.
    r2 = await client.get(f"/api/v1/themes/{theme_id}/tafsir", params={"source_id": "ibn_kathir_en"})
    assert r2.status_code == 200
    assert all(not s["tafsir_entries"] for s in r2.json()["segments"])
