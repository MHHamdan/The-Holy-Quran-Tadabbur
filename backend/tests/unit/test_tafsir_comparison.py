"""
Multi-source tafsir comparison — live-DB tests.

Covers GET /api/v1/tafseer/compare/{surah}/{ayah} and its /sources companion,
which read the seeded corpus (six sources x 6,236 verses in tafseer_chunks)
rather than the external alquran.cloud API used by /external/compare.

Requires a seeded database: scripts/ingest/seed_tafseer.py must have run.

Tests cover:
  1.  Comparison returns every seeded source for a verse
  2.  Entries are ordered oldest author first
  3.  Each entry carries provenance (author, era, methodology, chunk_id)
  4.  chunk_id is present and unique — citations must resolve
  5.  Source filtering via ?sources=
  6.  Language filtering via ?language=
  7.  Input validation (surah range, ayah floor)
  8.  Missing verse returns a structured 404
  9.  Descriptive comparison block: methodology groups, length, overlap
  10. Lexical overlap never crosses languages
  11. Overlap disclaimer is always present (content-policy requirement)
  12. /sources omits text but keeps the metadata a picker needs
  13. Immutable data is cached
  14. Verse text accompanies the comparison
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")

# Ayat al-Kursi — the most heavily commented verse in the corpus, so every
# seeded source has substantial content for it.
AYAT_AL_KURSI = (2, 255)
FATIHA_FIRST = (1, 1)


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestComparisonRetrieval:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_returns_ok(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_returns_multiple_sources(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert r.json()["sources_returned"] >= 4

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_verse_key_matches_request(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert r.json()["verse_key"] == f"{s}:{a}"

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_includes_verse_text(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert r.json()["verse"]["text_uthmani"]

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_every_entry_has_text(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert all(e["text"].strip() for e in r.json()["entries"])

    @pytest.mark.requires_data("tafsir:1:1")
    async def test_works_for_first_verse(self, client: AsyncClient):
        s, a = FATIHA_FIRST
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert r.status_code == 200
        assert r.json()["sources_returned"] >= 1


class TestOrderingAndProvenance:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_ordered_oldest_author_first(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        years = [e["death_year_hijri"] or 9999 for e in entries]
        assert years == sorted(years), f"not chronological: {years}"

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_entries_carry_author(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        assert all(e["author_en"] or e["author_ar"] for e in entries)

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_entries_carry_methodology_label(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        assert all(e["methodology_label_en"] for e in entries)

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_entries_carry_chunk_id(self, client: AsyncClient):
        """Citations resolve to a chunk, so every entry must expose one."""
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        assert all(e["chunk_id"] for e in entries)

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_chunk_ids_unique(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        ids = [e["chunk_id"] for e in entries]
        assert len(ids) == len(set(ids))

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_tabari_is_narration_based(self, client: AsyncClient):
        """Spot-check that catalogue metadata is actually joined, not blank."""
        s, a = AYAT_AL_KURSI
        entries = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["entries"]
        tabari = next((e for e in entries if e["source_id"] == "tabari_ar"), None)
        if tabari is None:
            pytest.skip("tabari_ar not seeded")
        assert tabari["death_year_hijri"] == 310
        assert tabari["methodology"] == "bil_mathur"


class TestFiltering:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_source_filter_restricts_results(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(
            f"/api/v1/tafseer/compare/{s}/{a}", params={"sources": "tabari_ar"}
        )
        assert r.status_code == 200
        assert {e["source_id"] for e in r.json()["entries"]} == {"tabari_ar"}

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_language_filter_arabic(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}", params={"language": "ar"})
        assert all(e["language"] == "ar" for e in r.json()["entries"])

    @pytest.mark.requires_data("tafsir_en:2:255")
    async def test_language_filter_english(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}", params={"language": "en"})
        assert all(e["language"] == "en" for e in r.json()["entries"])

    async def test_invalid_language_rejected(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}", params={"language": "fr"})
        assert r.status_code == 422


class TestValidation:
    async def test_surah_above_range_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/tafseer/compare/115/1")
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "INVALID_SURAH"

    async def test_surah_zero_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/tafseer/compare/0/1")
        assert r.status_code == 400

    async def test_ayah_zero_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/tafseer/compare/2/0")
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "INVALID_AYAH"

    async def test_missing_verse_returns_structured_404(self, client: AsyncClient):
        r = await client.get("/api/v1/tafseer/compare/2/9999")
        assert r.status_code == 404
        body = r.json()["detail"]
        assert body["code"] == "NO_TAFSIR_FOUND"
        assert body["message_ar"], "error must be bilingual"


class TestDescriptiveComparison:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_methodology_groups_present(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        comp = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]
        assert comp["methodology_groups"]

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_length_summary_present(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        length = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]["length"]
        assert length["longest_word_count"] >= length["shortest_word_count"]

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_overlap_never_crosses_languages(self, client: AsyncClient):
        """Arabic-to-English token overlap is meaningless and must not appear."""
        s, a = AYAT_AL_KURSI
        body = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()
        langs = {e["source_id"]: e["language"] for e in body["entries"]}
        for pair in body["comparison"]["lexical_overlap"]:
            assert langs[pair["a"]] == langs[pair["b"]] == pair["language"]

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_overlap_within_unit_range(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        comp = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]
        assert all(0.0 <= p["jaccard"] <= 1.0 for p in comp["lexical_overlap"])

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_overlap_sorted_descending(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        comp = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]
        scores = [p["jaccard"] for p in comp["lexical_overlap"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_disclaimer_always_present(self, client: AsyncClient):
        """Content policy: an overlap figure must never ship without its caveat."""
        s, a = AYAT_AL_KURSI
        comp = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]
        assert comp["disclaimer_ar"] and comp["disclaimer_en"]

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_disclaimer_disavows_agreement_claim(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        comp = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["comparison"]
        assert "not a judgement" in comp["disclaimer_en"].lower()


class TestSourcesEndpoint:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_lists_sources(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}/sources")
        assert r.status_code == 200
        assert r.json()["total"] >= 4

    async def test_omits_text_payload(self, client: AsyncClient):
        """The picker must stay cheap — full text runs to thousands of words."""
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}/sources")
        assert all("text" not in src for src in r.json()["sources"])

    async def test_keeps_picker_metadata(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}/sources")
        for src in r.json()["sources"]:
            assert src["source_id"] and src["language"]
            assert "word_count" in src

    @pytest.mark.requires_data("tafsir:2:255")
    async def test_source_count_matches_comparison(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        listed = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}/sources")).json()["total"]
        full = (await client.get(f"/api/v1/tafseer/compare/{s}/{a}")).json()["sources_returned"]
        assert listed == full


class TestCaching:
    @pytest.mark.requires_data("tafsir:2:255")
    async def test_comparison_is_cacheable(self, client: AsyncClient):
        """Seeded tafsir is immutable once ingested, so it caches hard."""
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}")
        assert "max-age=86400" in r.headers.get("cache-control", "")

    async def test_sources_is_cacheable(self, client: AsyncClient):
        s, a = AYAT_AL_KURSI
        r = await client.get(f"/api/v1/tafseer/compare/{s}/{a}/sources")
        assert "max-age=86400" in r.headers.get("cache-control", "")
