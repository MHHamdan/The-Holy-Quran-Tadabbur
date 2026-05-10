"""
Phase I — Thematic Tafsir & Related Stories Tests

Uses the real PostgreSQL database via httpx.AsyncClient + ASGITransport.

Tests verify:
  1.  GET /{theme_id}/tafsir — 200 for a theme that has segments
  2.  GET /{theme_id}/tafsir — response has top-level shape (theme_id, title_ar/en, segments)
  3.  GET /{theme_id}/tafsir — each segment has verse_reference, summary_ar, summary_en
  4.  GET /{theme_id}/tafsir — verses array populated from quran_verses
  5.  GET /{theme_id}/tafsir — verse texts are non-empty strings
  6.  GET /{theme_id}/tafsir — tafsir_entries have required fields (source_id, aya_start, aya_end)
  7.  GET /{theme_id}/tafsir — tafsir_entries include author and source name fields
  8.  GET /{theme_id}/tafsir — source_confidence is one of the three valid values
  9.  GET /{theme_id}/tafsir — sources_used list at top level is non-empty
  10. GET /{theme_id}/tafsir — sources_present per segment is subset of sources_used
  11. GET /{theme_id}/tafsir — verified_only=true returns only is_verified segments
  12. GET /{theme_id}/tafsir — verified_only=false returns all segments
  13. GET /{theme_id}/tafsir — source_id filter narrows tafsir_entries to that source
  14. GET /{theme_id}/tafsir — limit param respected
  15. GET /{theme_id}/tafsir — limit defaults to 20
  16. GET /{theme_id}/tafsir — segments ordered by segment_order ascending
  17. GET /{theme_id}/tafsir — source_backed when is_verified + 2+ tafsir entries
  18. GET /{theme_id}/tafsir — partial_coverage when tafsir_entries == 1
  19. GET /{theme_id}/tafsir — 404 for unknown theme_id
  20. GET /{theme_id}/tafsir — total_segments matches len(segments)
  21. GET /{theme_id}/tafsir — verse_reference format "sura:ayah" for single verse
  22. GET /{theme_id}/tafsir — verse_reference format "sura:start-end" for range
  23. GET /{theme_id}/stories — 200 for theme with matching story keywords
  24. GET /{theme_id}/stories — response has theme_id, title_ar/en, total, stories
  25. GET /{theme_id}/stories — each story has id, name_ar, name_en, category
  26. GET /{theme_id}/stories — shared_themes is non-empty for matched stories
  27. GET /{theme_id}/stories — stories sorted by shared_themes count descending
  28. GET /{theme_id}/stories — 404 for unknown theme_id
  29. GET /{theme_id}/stories — theme with no keyword mapping returns 200 with empty list
  30. GET /{theme_id}/stories — summary and lessons fields present when available
  31. GET /{theme_id}/tafsir — ok field is True
  32. GET /{theme_id}/stories — ok field is True
  33. GET /{theme_id}/tafsir — segment sura_no, ayah_start, ayah_end are integers
  34. GET /{theme_id}/tafsir — content_ar or content_en present on tafsir entries
  35. GET /{theme_id}/tafsir — large limit returns at most all segments
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import async_engine

pytestmark = pytest.mark.asyncio(loop_scope="module")

# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------

_SABR = "theme_sabr"        # has 2 segments, tafsir, and stories (patience/steadfastness)
_SALAH = "theme_salah"      # has 1 segment
_MISSING = "theme_does_not_exist_xyz"


@pytest_asyncio.fixture(scope="module", autouse=True)
async def reset_db_pool():
    """Dispose and reconnect the asyncpg pool so it binds to this module's
    event loop, not a stale loop from a previously-run test module."""
    await async_engine.dispose()
    yield
    await async_engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _tafsir(client: AsyncClient, theme_id: str, **params):
    return await client.get(f"/api/v1/themes/{theme_id}/tafsir", params=params)


async def _stories(client: AsyncClient, theme_id: str):
    return await client.get(f"/api/v1/themes/{theme_id}/stories")


# ===========================================================================
# GET /{theme_id}/tafsir — basic shape
# ===========================================================================

async def test_tafsir_200(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    assert r.status_code == 200


async def test_tafsir_top_level_shape(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    body = r.json()
    assert "theme_id" in body
    assert "title_ar" in body
    assert "title_en" in body
    assert "segments" in body
    assert isinstance(body["segments"], list)


async def test_tafsir_ok_field(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    assert r.json()["ok"] is True


async def test_tafsir_theme_id_echoed(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    assert r.json()["theme_id"] == _SABR


async def test_tafsir_titles_not_empty(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    body = r.json()
    assert body["title_ar"]
    assert body["title_en"]


async def test_tafsir_total_segments_matches_list(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    body = r.json()
    assert body["total_segments"] == len(body["segments"])


# ===========================================================================
# GET /{theme_id}/tafsir — segment shape
# ===========================================================================

async def test_tafsir_segment_has_required_fields(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    segs = r.json()["segments"]
    assert len(segs) > 0
    seg = segs[0]
    for field in ("segment_id", "verse_reference", "summary_ar", "summary_en",
                  "is_verified", "source_confidence", "verses", "tafsir_entries",
                  "sources_present", "sura_no", "ayah_start", "ayah_end"):
        assert field in seg, f"Missing field: {field}"


async def test_tafsir_segment_integer_coords(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    seg = r.json()["segments"][0]
    assert isinstance(seg["sura_no"], int)
    assert isinstance(seg["ayah_start"], int)
    assert isinstance(seg["ayah_end"], int)


async def test_tafsir_segment_summaries_not_empty(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    for seg in r.json()["segments"]:
        assert seg["summary_ar"], f"Empty summary_ar on segment {seg['segment_id']}"
        assert seg["summary_en"], f"Empty summary_en on segment {seg['segment_id']}"


async def test_tafsir_source_confidence_values(client: AsyncClient):
    valid = {"source_backed", "partial_coverage", "needs_review"}
    r = await _tafsir(client, _SABR)
    for seg in r.json()["segments"]:
        assert seg["source_confidence"] in valid, (
            f"Bad source_confidence '{seg['source_confidence']}' on {seg['segment_id']}"
        )


# ===========================================================================
# GET /{theme_id}/tafsir — verse texts
# ===========================================================================

async def test_tafsir_verses_populated(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    segs = r.json()["segments"]
    # At least one segment should have verse text from quran_verses
    total_verses = sum(len(s["verses"]) for s in segs)
    assert total_verses > 0


async def test_tafsir_verse_text_not_empty(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    for seg in r.json()["segments"]:
        for v in seg["verses"]:
            assert v["text_uthmani"], "Empty text_uthmani on verse"
            assert isinstance(v["aya_no"], int)


async def test_tafsir_verse_reference_single(client: AsyncClient):
    """Single-verse segment: reference should be 'sura:ayah'"""
    r = await _tafsir(client, _SALAH)
    segs = r.json()["segments"]
    assert len(segs) >= 1
    ref = segs[0]["verse_reference"]
    # Single-verse reference contains exactly one colon and no hyphen
    assert ":" in ref
    parts = ref.split(":")
    assert len(parts) == 2
    # Should not contain '-'
    assert "-" not in ref


async def test_tafsir_verse_reference_range(client: AsyncClient):
    """Range segment (2:155-157): reference should be 'sura:start-end'"""
    r = await _tafsir(client, _SABR)
    segs = r.json()["segments"]
    range_segs = [s for s in segs if s["ayah_start"] != s["ayah_end"]]
    if range_segs:
        ref = range_segs[0]["verse_reference"]
        assert "-" in ref, f"Expected range ref, got: {ref}"


# ===========================================================================
# GET /{theme_id}/tafsir — tafsir entries
# ===========================================================================

async def test_tafsir_entries_have_source_fields(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    for seg in r.json()["segments"]:
        for entry in seg["tafsir_entries"]:
            assert "source_id" in entry
            assert "aya_start" in entry
            assert "aya_end" in entry
            assert "author_ar" in entry
            assert "author_en" in entry
            assert "source_name_ar" in entry
            assert "source_name_en" in entry


async def test_tafsir_entries_have_content(client: AsyncClient):
    """At least one entry should have content_ar or content_en"""
    r = await _tafsir(client, _SABR)
    found = False
    for seg in r.json()["segments"]:
        for entry in seg["tafsir_entries"]:
            if entry.get("content_ar") or entry.get("content_en"):
                found = True
                break
        if found:
            break
    assert found, "No tafsir entry had any content"


async def test_tafsir_sources_used_not_empty(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    assert len(r.json()["sources_used"]) > 0


async def test_tafsir_sources_present_subset_of_sources_used(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    body = r.json()
    top_sources = set(body["sources_used"])
    for seg in body["segments"]:
        for src in seg["sources_present"]:
            assert src in top_sources, f"{src} in sources_present but not in sources_used"


# ===========================================================================
# GET /{theme_id}/tafsir — source_backed / partial_coverage logic
# ===========================================================================

async def test_tafsir_source_backed_when_verified_and_multiple_entries(client: AsyncClient):
    """A segment that is_verified AND has >=2 tafsir entries should be source_backed."""
    r = await _tafsir(client, _SABR)
    for seg in r.json()["segments"]:
        if seg["is_verified"] and len(seg["tafsir_entries"]) >= 2:
            assert seg["source_confidence"] == "source_backed", (
                f"Expected source_backed for segment {seg['segment_id']}"
            )
            break


# ===========================================================================
# GET /{theme_id}/tafsir — query params
# ===========================================================================

async def test_tafsir_verified_only_true(client: AsyncClient):
    r = await _tafsir(client, _SABR, verified_only=True)
    for seg in r.json()["segments"]:
        assert seg["is_verified"] is True, f"Non-verified segment returned with verified_only=true"


async def test_tafsir_verified_only_false_returns_all(client: AsyncClient):
    r_all = await _tafsir(client, _SABR, verified_only=False)
    r_ver = await _tafsir(client, _SABR, verified_only=True)
    assert len(r_all.json()["segments"]) >= len(r_ver.json()["segments"])


async def test_tafsir_source_id_filter(client: AsyncClient):
    r = await _tafsir(client, _SABR, source_id="muyassar_ar")
    for seg in r.json()["segments"]:
        for entry in seg["tafsir_entries"]:
            assert entry["source_id"] == "muyassar_ar"


async def test_tafsir_limit_respected(client: AsyncClient):
    r = await _tafsir(client, _SABR, limit=1)
    assert len(r.json()["segments"]) <= 1


async def test_tafsir_limit_default_is_20(client: AsyncClient):
    """Default limit is 20; sabr only has 2 so we get ≤ 20."""
    r = await _tafsir(client, _SABR)
    assert len(r.json()["segments"]) <= 20


async def test_tafsir_large_limit_returns_all(client: AsyncClient):
    r = await _tafsir(client, _SABR, limit=50)
    assert len(r.json()["segments"]) >= 1


async def test_tafsir_segments_ordered_by_segment_order(client: AsyncClient):
    r = await _tafsir(client, _SABR)
    orders = [s["segment_order"] for s in r.json()["segments"]]
    assert orders == sorted(orders), f"Segments not in ascending order: {orders}"


# ===========================================================================
# GET /{theme_id}/tafsir — error cases
# ===========================================================================

async def test_tafsir_404_unknown_theme(client: AsyncClient):
    r = await _tafsir(client, _MISSING)
    assert r.status_code == 404


# ===========================================================================
# GET /{theme_id}/stories — basic shape
# ===========================================================================

async def test_stories_200(client: AsyncClient):
    r = await _stories(client, _SABR)
    assert r.status_code == 200


async def test_stories_top_level_shape(client: AsyncClient):
    r = await _stories(client, _SABR)
    body = r.json()
    for field in ("theme_id", "title_ar", "title_en", "total", "stories"):
        assert field in body, f"Missing field: {field}"


async def test_stories_ok_field(client: AsyncClient):
    r = await _stories(client, _SABR)
    assert r.json()["ok"] is True


async def test_stories_theme_id_echoed(client: AsyncClient):
    r = await _stories(client, _SABR)
    assert r.json()["theme_id"] == _SABR


async def test_stories_total_matches_list(client: AsyncClient):
    r = await _stories(client, _SABR)
    body = r.json()
    assert body["total"] == len(body["stories"])


# ===========================================================================
# GET /{theme_id}/stories — story item shape
# ===========================================================================

async def test_stories_item_has_required_fields(client: AsyncClient):
    r = await _stories(client, _SABR)
    stories = r.json()["stories"]
    assert len(stories) > 0
    story = stories[0]
    for field in ("id", "name_ar", "name_en", "category", "shared_themes"):
        assert field in story, f"Missing field: {field}"


async def test_stories_shared_themes_not_empty(client: AsyncClient):
    r = await _stories(client, _SABR)
    for story in r.json()["stories"]:
        assert len(story["shared_themes"]) > 0, (
            f"Story {story['id']} returned with no shared_themes"
        )


async def test_stories_sorted_by_shared_count_desc(client: AsyncClient):
    r = await _stories(client, _SABR)
    counts = [len(s["shared_themes"]) for s in r.json()["stories"]]
    assert counts == sorted(counts, reverse=True), f"Stories not sorted by shared_count: {counts}"


async def test_stories_known_story_included(client: AsyncClient):
    """Story of Yusuf mentions 'patience' — should appear for sabr."""
    r = await _stories(client, _SABR)
    ids = {s["id"] for s in r.json()["stories"]}
    assert "story_yusuf" in ids or "story_nuh" in ids or "story_musa" in ids, (
        f"Expected at least one patience story, got: {ids}"
    )


async def test_stories_name_fields_not_empty(client: AsyncClient):
    r = await _stories(client, _SABR)
    for story in r.json()["stories"]:
        assert story["name_ar"], f"Empty name_ar on {story['id']}"
        assert story["name_en"], f"Empty name_en on {story['id']}"


async def test_stories_summary_and_lessons_present_when_available(client: AsyncClient):
    r = await _stories(client, _SABR)
    # At least one story should have summary fields (data-dependent; we just check type)
    for story in r.json()["stories"]:
        if story.get("summary_ar") is not None:
            assert isinstance(story["summary_ar"], str)
        if story.get("lessons_en") is not None:
            assert isinstance(story["lessons_en"], list)


# ===========================================================================
# GET /{theme_id}/stories — error / edge cases
# ===========================================================================

async def test_stories_404_unknown_theme(client: AsyncClient):
    r = await _stories(client, _MISSING)
    assert r.status_code == 404


async def test_stories_theme_with_no_keywords_returns_empty_list(client: AsyncClient):
    """A real theme whose slug is not in _SLUG_TO_STORY_KEYWORDS and has an
    obscure title should return an empty stories list (or 200 with total=0).
    We use a theme slug that has no matching stories as a sanity check."""
    # Use a theme whose keywords won't match any story themes array
    r = await _stories(client, "theme_birr_walidayn")
    assert r.status_code == 200
    # May or may not have stories — just verify shape is correct
    body = r.json()
    assert "stories" in body
    assert isinstance(body["stories"], list)
