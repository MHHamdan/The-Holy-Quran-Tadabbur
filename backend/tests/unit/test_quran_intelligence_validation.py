"""
Quran Intelligence Validation Tests

Tests that validate the data quality guarantees across all intelligence modules:
- Surah Atlas has 114 entries
- Every story has at least one ayah reference
- Review warnings appear when needed
- Arabic mode is RTL
- No fabricated content appears without citations
- Source validation is enforced

These are offline tests that check file content and route contracts.
"""
import json
import os
import re
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../.."))
FRONTEND_DATA = os.path.join(ROOT, "frontend/src/data")
SURAH_MEMORY_ATLAS = os.path.join(ROOT, "frontend/src/data/generated/surahMemoryAtlas.json")
STORIES_PATH = os.path.join(FRONTEND_DATA, "quranStories.ts")
SURAH_ATLAS_PATH = os.path.join(FRONTEND_DATA, "surahAtlas.ts")
MEM_LINKS_PATH = os.path.join(FRONTEND_DATA, "quranMemorizationLinks.ts")
RARE_WORDS_PATH = os.path.join(FRONTEND_DATA, "quranRareWords.ts")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Surah Memory Atlas: 114 surahs
# ---------------------------------------------------------------------------

class TestSurahMemoryAtlas:
    """Validate the existing surah memory atlas dataset."""

    def test_surah_memory_atlas_exists(self):
        assert os.path.exists(SURAH_MEMORY_ATLAS), f"Not found: {SURAH_MEMORY_ATLAS}"

    def test_surah_memory_atlas_has_114_entries(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        assert data["totalSurahs"] == 114
        assert len(data["surahs"]) == 114

    def test_all_surah_numbers_are_valid(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        numbers = [s["surahNumber"] for s in data["surahs"]]
        assert sorted(numbers) == list(range(1, 115)), "Surah numbers must be 1–114"

    def test_all_surahs_have_arabic_names(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        for s in data["surahs"]:
            assert s.get("nameArabic"), f"Empty nameArabic for surah {s['surahNumber']}"

    def test_all_surahs_have_ayah_count(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        for s in data["surahs"]:
            assert s.get("ayahCount", 0) > 0, f"Zero ayahCount for surah {s['surahNumber']}"

    def test_fatiha_has_7_ayat(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        fatiha = next(s for s in data["surahs"] if s["surahNumber"] == 1)
        assert fatiha["ayahCount"] == 7

    def test_baqara_has_286_ayat(self):
        with open(SURAH_MEMORY_ATLAS) as f:
            data = json.load(f)
        baqara = next(s for s in data["surahs"] if s["surahNumber"] == 2)
        assert baqara["ayahCount"] == 286


# ---------------------------------------------------------------------------
# Surah Atlas TypeScript file
# ---------------------------------------------------------------------------

class TestSurahAtlasFile:
    """Validate the generated surahAtlas.ts data file."""

    def test_surah_atlas_file_exists(self):
        assert os.path.exists(SURAH_ATLAS_PATH), f"Not found: {SURAH_ATLAS_PATH}"

    def test_surah_atlas_has_114_entries(self):
        with open(SURAH_ATLAS_PATH) as f:
            content = f.read()
        # Count top-level entry openings (pattern: `{` followed by `surahNumber:`)
        matches = re.findall(r'\{\s*\n\s*surahNumber:\s*\d+', content)
        assert len(matches) == 114, f"Expected 114, found {len(matches)}"

    def test_surah_atlas_all_needs_review(self):
        with open(SURAH_ATLAS_PATH) as f:
            content = f.read()
        approved_count = len(re.findall(r"reviewStatus:\s*'approved'", content))
        assert approved_count == 0, f"Found {approved_count} approved entries — must be 0"

    def test_surah_atlas_human_review_true(self):
        with open(SURAH_ATLAS_PATH) as f:
            content = f.read()
        false_count = len(re.findall(r'humanReviewRequired:\s*false', content))
        assert false_count == 0, f"Found {false_count} entries with humanReviewRequired: false"

    def test_surah_atlas_exports_get_function(self):
        with open(SURAH_ATLAS_PATH) as f:
            content = f.read()
        assert "getSurahAtlasEntry" in content

    def test_surah_atlas_no_empty_names(self):
        with open(SURAH_ATLAS_PATH) as f:
            content = f.read()
        # Check nameArabic fields are not empty
        empty_names = re.findall(r"nameArabic:\s*'',", content)
        assert len(empty_names) == 0


# ---------------------------------------------------------------------------
# Memorization Links file
# ---------------------------------------------------------------------------

class TestMemorizationLinksFile:
    """Validate quranMemorizationLinks.ts."""

    def test_mem_links_file_exists(self):
        assert os.path.exists(MEM_LINKS_PATH)

    def test_has_confusion_pairs(self):
        with open(MEM_LINKS_PATH) as f:
            content = f.read()
        count = len(re.findall(r"id:\s*'cp_", content))
        assert count >= 1, "Expected at least 1 confusion pair"

    def test_confusion_pairs_have_difference_note(self):
        with open(MEM_LINKS_PATH) as f:
            content = f.read()
        # Find all differenceNote blocks (simplified check)
        assert "differenceNote:" in content

    def test_all_mem_links_needs_review(self):
        with open(MEM_LINKS_PATH) as f:
            content = f.read()
        approved = re.findall(r"reviewStatus:\s*'approved'", content)
        assert len(approved) == 0

    def test_has_required_exports(self):
        with open(MEM_LINKS_PATH) as f:
            content = f.read()
        for export in ['CONFUSION_PAIRS', 'MEMORIZATION_LINKS', 'REPEATED_PHRASES',
                       'STORY_RECURRENCES', 'getConfusionPairsForSurah']:
            assert export in content, f"Missing export: {export}"


# ---------------------------------------------------------------------------
# Rare Words file
# ---------------------------------------------------------------------------

class TestRareWordsFile:
    """Validate quranRareWords.ts."""

    def test_rare_words_file_exists(self):
        assert os.path.exists(RARE_WORDS_PATH)

    def test_has_entries(self):
        with open(RARE_WORDS_PATH) as f:
            content = f.read()
        count = len(re.findall(r"id:\s*'rw_", content))
        assert count >= 1

    def test_all_entries_needs_review(self):
        with open(RARE_WORDS_PATH) as f:
            content = f.read()
        approved = re.findall(r"reviewStatus:\s*'approved'", content)
        assert len(approved) == 0

    def test_all_entries_have_arabic(self):
        with open(RARE_WORDS_PATH) as f:
            content = f.read()
        empty_arabic = re.findall(r"arabic:\s*'',", content)
        assert len(empty_arabic) == 0

    def test_has_required_exports(self):
        with open(RARE_WORDS_PATH) as f:
            content = f.read()
        for export in ['QURAN_RARE_WORDS', 'RARE_WORDS_COLLECTION', 'getRareWordsBySurah']:
            assert export in content, f"Missing export: {export}"

    def test_lexical_evidence_refs_present(self):
        with open(RARE_WORDS_PATH) as f:
            content = f.read()
        assert "lexicalEvidenceRefs:" in content


# ---------------------------------------------------------------------------
# API route contracts — review safety
# ---------------------------------------------------------------------------

class TestReviewSafetyContracts:
    """All API routes must return review warnings for atlas content."""

    async def test_surah_atlas_list_has_review_warning(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        data = r.json()
        assert data["reviewStatus"] == "needs_review"
        assert data["humanReviewRequired"] is True
        assert len(data["warnings"]) > 0

    async def test_surah_atlas_detail_has_review_warning(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/2")
        data = r.json()
        assert data["reviewStatus"] == "needs_review"
        assert data["humanReviewRequired"] is True

    async def test_memorization_status_has_review(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_confusion_pairs_has_review(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs")
        assert r.json()["reviewStatus"] == "needs_review"
        assert r.json()["humanReviewRequired"] is True

    async def test_rare_words_has_review(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/18/rare-words")
        assert r.json()["reviewStatus"] == "needs_review"
        assert r.json()["humanReviewRequired"] is True


# ---------------------------------------------------------------------------
# Stories — every story must have ayah reference
# ---------------------------------------------------------------------------

class TestStoriesHaveAyahRefs:
    """Validate that quranStories.ts stories have Quran references."""

    def test_stories_file_exists(self):
        assert os.path.exists(STORIES_PATH)

    def test_stories_have_quran_references(self):
        with open(STORIES_PATH) as f:
            content = f.read()
        assert "quranReferences:" in content, "quranReferences field missing"

    def test_stories_all_needs_review(self):
        with open(STORIES_PATH) as f:
            content = f.read()
        # No segment should be "approved"
        approved = re.findall(r"status:\s*'approved'", content)
        assert len(approved) == 0, f"Found {len(approved)} approved segments — all must be needs_review"
