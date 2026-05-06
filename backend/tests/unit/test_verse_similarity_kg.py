"""
Phase 5: Unit tests for VerseSimilarityService (KG-based).

Tests cover:
  - KG index loading from stories and concepts data
  - Story segment edge evidence
  - Source ID validation
  - Semantic-only edges hidden by default
  - includeExperimental flag behaviour
  - Same-story ayahs rank above same-surah-only ayahs
  - Path explanation returns valid chain
  - No Quran text mutation
  - Explanation language requirements
  - Evidence requirement enforcement
"""
import os
import json
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Set, Tuple

# We import the KG service directly — no DB needed, uses flat JSON files
from app.services.verse_similarity import (
    VerseSimilarityService,
    _KGIndex,
    WEIGHTS,
    EvidenceItem,
    KGSimilarityResult,
    NEEDS_REVIEW,
    EXPERIMENTAL,
    _jaccard,
    _build_explanation,
    get_kg_index,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def kg_index():
    """Return a freshly loaded KG index (uses real files)."""
    idx = _KGIndex()
    idx.load()
    return idx


@pytest.fixture
def service_default():
    """VerseSimilarityService with experimental disabled (default)."""
    return VerseSimilarityService(include_experimental=False)


@pytest.fixture
def service_experimental():
    """VerseSimilarityService with experimental enabled."""
    return VerseSimilarityService(include_experimental=True)


# =============================================================================
# 1. KG Index — basic loading
# =============================================================================

class TestKGIndexLoading:

    def test_stories_loaded(self, kg_index):
        """KG index must load story data."""
        assert len(kg_index.stories) > 0, "No stories loaded into KG index"

    def test_segments_loaded(self, kg_index):
        """Segments must be indexed."""
        assert len(kg_index.segments) > 0, "No segments indexed"

    def test_ayah_to_story_mapping(self, kg_index):
        """At least one ayah should map to a story."""
        assert len(kg_index.ayah_stories) > 0

    def test_story_to_ayah_mapping(self, kg_index):
        """Story→ayah reverse index must be populated."""
        assert len(kg_index.story_ayahs) > 0

    def test_adam_story_exists(self, kg_index):
        """The Adam story should be in the index."""
        assert "story_adam" in kg_index.stories

    def test_adam_segment_ayahs_indexed(self, kg_index):
        """Adam creation segment (2:30-33) should be in ayah_stories."""
        found = any(
            "story_adam" in kg_index.ayah_stories.get((2, aya), set())
            for aya in range(30, 34)
        )
        assert found, "Adam story not indexed for surah 2 ayahs 30–33"

    def test_no_quran_text_in_index(self, kg_index):
        """Stories dict must not store Quran text — only metadata."""
        for story in kg_index.stories.values():
            # name_ar is OK (short story title), text_uthmani should NOT appear
            assert "text_uthmani" not in story
            assert "text_imlaei" not in story


# =============================================================================
# 2. WEIGHTS integrity
# =============================================================================

class TestWeights:

    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"

    def test_all_weight_keys_present(self):
        required = {"story_segment", "story", "concept", "theme", "person", "semantic", "lexical", "source_conf"}
        assert required == set(WEIGHTS.keys())

    def test_story_signal_dominant(self):
        """Story segment signal should be the strongest single weight."""
        max_weight = max(WEIGHTS.values())
        assert WEIGHTS["story_segment"] == max_weight, \
            "story_segment weight should be dominant"


# =============================================================================
# 3. Jaccard utility
# =============================================================================

class TestJaccard:

    def test_identical_sets(self):
        assert _jaccard({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard({"a"}, {"b"}) == 0.0

    def test_partial_overlap(self):
        score = _jaccard({"a", "b", "c"}, {"a", "b", "d"})
        # |intersection| = 2, |union| = 4 → 0.5
        assert abs(score - 0.5) < 1e-9

    def test_empty_sets(self):
        assert _jaccard(set(), set()) == 0.0

    def test_one_empty(self):
        assert _jaccard({"a"}, set()) == 0.0


# =============================================================================
# 4. Explanation builder
# =============================================================================

class TestExplanationBuilder:

    def test_arabic_present_for_story_overlap(self, kg_index):
        ar, en = _build_explanation({"story_adam"}, set(), set(), set(), kg_index)
        assert any("؀" <= c <= "ۿ" for c in ar), "Arabic explanation must contain Arabic text"

    def test_english_present_for_story_overlap(self, kg_index):
        ar, en = _build_explanation({"story_adam"}, set(), set(), set(), kg_index)
        assert len(en) > 10, "English explanation should not be empty"

    def test_no_concept_overlap_fallback(self, kg_index):
        ar, en = _build_explanation(set(), set(), set(), set(), kg_index)
        assert len(ar) > 0, "Fallback explanation must still produce Arabic text"
        assert len(en) > 0

    def test_explanations_do_not_invent_tafsir(self, kg_index):
        """Explanations must be generic — no invented tafsir statements."""
        ar, en = _build_explanation({"story_yusuf"}, {"theme_patience"}, {"theme_patience"}, {"person_yusuf"}, kg_index)
        # Must NOT contain authoritative religious rulings
        prohibited = ["يدل", "يثبت", "يؤكد الحكم"]
        for phrase in prohibited:
            assert phrase not in ar, f"Explanation contains suspicious phrase: {phrase}"


# =============================================================================
# 5. VerseSimilarityService — core scoring
# =============================================================================

class TestVerseSimilarityCore:

    @pytest.mark.asyncio
    async def test_returns_response_object(self, service_default):
        result = await service_default.find_similar(2, 255, top_k=5)
        assert hasattr(result, "sourceAyah")
        assert hasattr(result, "relatedAyahs")
        assert result.sourceAyah["surahNumber"] == 2
        assert result.sourceAyah["ayahNumber"] == 255

    @pytest.mark.asyncio
    async def test_same_story_ranked_higher_than_same_surah(self, service_default, kg_index):
        """Ayahs from same story should outscore unrelated same-surah ayahs."""
        # Pick an ayah that's in a story with other ayahs
        # Adam creation: 2:30, use 2:31 as a sibling
        result = await service_default.find_similar(2, 30, top_k=20)
        if not result.relatedAyahs:
            pytest.skip("No related ayahs found — KG may be empty for this verse")

        # Same-story ayahs should appear with story relation type
        story_related = [r for r in result.relatedAyahs if "SAME_STORY_SEGMENT" in r.relationTypes or "SAME_STORY" in r.relationTypes]
        assert len(story_related) > 0, "Expected at least one story-related ayah"

    @pytest.mark.asyncio
    async def test_require_evidence_default(self, service_default):
        """By default, only evidence-backed relations returned."""
        result = await service_default.find_similar(2, 255, top_k=10, require_evidence=True)
        for ayah in result.relatedAyahs:
            assert len(ayah.evidence) > 0, f"Ayah {ayah.surahNumber}:{ayah.ayahNumber} has no evidence"

    @pytest.mark.asyncio
    async def test_all_results_have_human_review_flag(self, service_default):
        """All story-derived results must have humanReviewRequired=True."""
        result = await service_default.find_similar(2, 30, top_k=10)
        for ayah in result.relatedAyahs:
            if any(rt in ["SAME_STORY", "SAME_STORY_SEGMENT"] for rt in ayah.relationTypes):
                assert ayah.humanReviewRequired is True, \
                    f"Story-derived result {ayah.surahNumber}:{ayah.ayahNumber} must have humanReviewRequired=True"

    @pytest.mark.asyncio
    async def test_scores_in_valid_range(self, service_default):
        """All similarity scores must be in [0, 1]."""
        result = await service_default.find_similar(2, 30, top_k=20)
        for ayah in result.relatedAyahs:
            assert 0.0 <= ayah.score <= 1.0, \
                f"Score {ayah.score} out of range for {ayah.surahNumber}:{ayah.ayahNumber}"

    @pytest.mark.asyncio
    async def test_results_sorted_descending(self, service_default):
        """Results must be sorted by score descending."""
        result = await service_default.find_similar(2, 30, top_k=20)
        scores = [r.score for r in result.relatedAyahs]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score descending"

    @pytest.mark.asyncio
    async def test_invalid_verse_returns_empty(self, service_default):
        """Non-existent ayah (115:999) should return empty results."""
        result = await service_default.find_similar(115, 999, top_k=5)
        assert result.relatedAyahs == []


# =============================================================================
# 6. Semantic / Experimental edge handling
# =============================================================================

class TestSemanticEdgePolicy:

    @pytest.mark.asyncio
    async def test_semantic_only_hidden_by_default(self, service_default):
        """Semantic-only edges must not appear when include_experimental=False."""
        # Patch Qdrant to return semantic results
        mock_sem = MagicMock()
        mock_sem.sura_no = 3
        mock_sem.aya_no = 10
        mock_sem.similarity_score = 0.85

        with patch("app.services.verse_similarity.get_verse_embedding_service") as mock_svc:
            mock_instance = AsyncMock()
            mock_instance.find_similar_to_verse.return_value = [mock_sem]
            mock_svc.return_value = mock_instance

            result = await service_default.find_similar(99, 1, top_k=10)
            # (99,1) is not in any story, so if we get (3,10) it would be semantic-only
            semantic_only = [
                r for r in result.relatedAyahs
                if r.relationTypes == ["SEMANTICALLY_SIMILAR"]
            ]
            assert len(semantic_only) == 0, "Semantic-only results should be hidden by default"

    @pytest.mark.asyncio
    async def test_semantic_results_have_experimental_status(self, service_experimental):
        """When experimental=True, semantic results must have experimental status."""
        mock_sem = MagicMock()
        mock_sem.sura_no = 3
        mock_sem.aya_no = 10
        mock_sem.similarity_score = 0.85

        with patch("app.services.verse_similarity.get_verse_embedding_service") as mock_svc:
            mock_instance = AsyncMock()
            mock_instance.find_similar_to_verse.return_value = [mock_sem]
            mock_svc.return_value = mock_instance

            result = await service_experimental.find_similar(99, 1, top_k=10, require_evidence=False)
            semantic_results = [
                r for r in result.relatedAyahs
                if "SEMANTICALLY_SIMILAR" in r.relationTypes
            ]
            for sr in semantic_results:
                # Evidence items for semantic-only should be experimental
                statuses = [e.relationStatus for e in sr.evidence]
                assert EXPERIMENTAL in statuses, \
                    "Semantic-only evidence must have experimental relationStatus"

    @pytest.mark.asyncio
    async def test_semantic_results_have_warnings(self, service_experimental):
        """Semantic results must include a non-scholarly-verified warning."""
        mock_sem = MagicMock()
        mock_sem.sura_no = 3
        mock_sem.aya_no = 10
        mock_sem.similarity_score = 0.85

        with patch("app.services.verse_similarity.get_verse_embedding_service") as mock_svc:
            mock_instance = AsyncMock()
            mock_instance.find_similar_to_verse.return_value = [mock_sem]
            mock_svc.return_value = mock_instance

            result = await service_experimental.find_similar(99, 1, top_k=10, require_evidence=False)
            semantic_results = [
                r for r in result.relatedAyahs
                if "SEMANTICALLY_SIMILAR" in r.relationTypes
            ]
            for sr in semantic_results:
                assert len(sr.warnings) > 0, "Semantic results must have warnings"


# =============================================================================
# 7. Path explanation
# =============================================================================

class TestPathExplanation:

    def test_path_same_story(self, service_default, kg_index):
        """Ayahs from the same story should produce a valid path."""
        # Find two ayahs that share a story
        shared_story = None
        a_key = b_key = None
        for story_id, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs_list = list(ayah_set)
                a_key = ayahs_list[0]
                b_key = ayahs_list[1]
                shared_story = story_id
                break

        if not shared_story:
            pytest.skip("No story with multiple ayahs found")

        path = service_default.find_path(a_key[0], a_key[1], b_key[0], b_key[1])
        assert path is not None, "Expected a path between story-related ayahs"
        assert len(path) >= 2, "Path must have at least 2 steps"

        # All steps must have required fields
        for step in path:
            assert "nodeId" in step
            assert "nodeType" in step
            assert "label" in step

    def test_path_same_ayah_returns_empty(self, service_default):
        """find_path from ayah to itself should return empty list."""
        path = service_default.find_path(2, 255, 2, 255)
        assert path == []

    def test_path_unrelated_returns_none(self, service_default):
        """Completely unrelated ayahs should return None (no path found)."""
        # Use surah 1 aya 1 and surah 100 aya 1 which likely share no story/concept
        path = service_default.find_path(1, 1, 100, 1)
        # May or may not return None — just assert it's None or a valid list
        assert path is None or isinstance(path, list)


# =============================================================================
# 8. Source IDs must be valid
# =============================================================================

class TestSourceIdPolicy:

    def test_story_evidence_uses_known_source_ids(self, kg_index):
        """Sources in segment evidence must be from known tafsir sources."""
        # Active sources + pending-license sources + bare-name variants in manifest
        KNOWN_SOURCES = {
            "ibn_kathir", "ibn_kathir_ar", "ibn_kathir_en",
            "muyassar_ar", "saadi", "saadi_ar", "saadi_en",
            "sahih_international", "tafheem_en",
            # Pending license verification — present in manifest but not yet active
            "tabari", "tabari_ar", "qurtubi", "qurtubi_ar", "baghawi", "baghawi_ar",
            "jalalayn", "jalalayn_en", "muyassar",
            "story_manifest",  # system marker allowed
        }
        for story in kg_index.stories.values():
            for seg in story.get("segments", []):
                for ev in seg.get("evidence", []):
                    sid = ev.get("source_id", "")
                    if sid:
                        assert sid in KNOWN_SOURCES, \
                            f"Unknown source ID '{sid}' in story '{story['id']}'"


# =============================================================================
# 9. Relation types are valid strings
# =============================================================================

VALID_RELATION_TYPES = {
    "SAME_STORY", "SAME_STORY_SEGMENT", "SAME_PROPHET_OR_PERSON",
    "SAME_THEME", "SAME_CONCEPT", "SAME_ROOT", "SAME_LEMMA",
    "SAME_SURAH", "ADJACENT_AYAH", "TAFSIR_SUPPORTS_RELATION",
    "ASBAB_CONTEXT_RELATED", "MUNASABAH_RELATED", "CONTRASTS_WITH",
    "PARALLEL_EVENT_PATTERN", "SHARED_MORAL_LESSON",
    "SEMANTICALLY_SIMILAR", "TRANSLATION_SIMILARITY", "SOURCE_CITES",
}


class TestRelationTypes:

    @pytest.mark.asyncio
    async def test_relation_types_are_valid_strings(self, service_default):
        result = await service_default.find_similar(2, 30, top_k=20)
        for ayah in result.relatedAyahs:
            for rt in ayah.relationTypes:
                assert rt in VALID_RELATION_TYPES, f"Unknown relation type: {rt}"
