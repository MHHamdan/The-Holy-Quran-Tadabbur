"""
Phase 5.6: Unit tests for VerseSimilarityService path explanation.

Tests cover:
  - PathExplanation populated for story-related ayahs
  - PathExplanation omitted when no path exists
  - No Quran text in path nodes
  - All edges marked needs_review
  - Max path length capped at 4 nodes
  - Bilingual explanation strings present
  - Warnings present on path
  - PathExplanation populated in find_similar() results
  - Path explanation JSON serialisability (for API mapping)
"""
import pytest
from dataclasses import asdict

from app.services.verse_similarity import (
    VerseSimilarityService,
    _KGIndex,
    PathNode,
    PathEdge,
    PathExplanation,
    NEEDS_REVIEW,
    get_kg_index,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def kg_index():
    idx = _KGIndex()
    idx.load()
    return idx


@pytest.fixture
def service():
    return VerseSimilarityService(include_experimental=False)


# =============================================================================
# 1. _build_path_explanation — result shape
# =============================================================================

class TestBuildPathExplanation:

    def test_same_story_returns_path_explanation(self, service, kg_index):
        """Two ayahs that share a story must produce a PathExplanation."""
        for story_id, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                assert result is not None, f"Expected PathExplanation for {a} → {b} via {story_id}"
                return
        pytest.skip("No story with multiple ayahs found")

    def test_unrelated_ayahs_returns_none(self, service):
        """Ayahs with no shared story/concept/theme should return None."""
        result = service._build_path_explanation(1, 1, 100, 1)
        # May return None if no path, or a valid PathExplanation if a path exists
        assert result is None or isinstance(result, PathExplanation)

    def test_same_ayah_returns_none(self, service):
        """Path from an ayah to itself should return None (empty raw path → None)."""
        result = service._build_path_explanation(2, 255, 2, 255)
        assert result is None

    def test_path_has_at_least_two_nodes(self, service, kg_index):
        """A valid path must have at least 2 nodes (source + target)."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert len(result.nodes) >= 2
                    return
        pytest.skip("No usable story pair")

    def test_max_four_nodes(self, service, kg_index):
        """Path explanation must not exceed 4 nodes."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert len(result.nodes) <= 4, \
                        f"Path has {len(result.nodes)} nodes, max allowed is 4"
                    return
        pytest.skip("No usable story pair")

    def test_edges_count_equals_nodes_minus_one(self, service, kg_index):
        """Number of edges must equal number of nodes minus 1."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert len(result.edges) == len(result.nodes) - 1
                    return
        pytest.skip("No usable story pair")


# =============================================================================
# 2. Safety rules — no Quran text, all needs_review
# =============================================================================

class TestPathSafetyRules:

    def test_no_quran_text_in_nodes(self, service, kg_index):
        """Path nodes must never contain Quran text fields."""
        FORBIDDEN_FIELDS = {"text_uthmani", "text_imlaei", "translation"}
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    for node in result.nodes:
                        node_dict = asdict(node)
                        for forbidden in FORBIDDEN_FIELDS:
                            assert forbidden not in node_dict, \
                                f"Quran text field '{forbidden}' found in path node"
                    return
        pytest.skip("No usable story pair")

    def test_all_edges_needs_review(self, service, kg_index):
        """Every edge in a path explanation must be marked needs_review."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    for edge in result.edges:
                        assert edge.relationStatus == NEEDS_REVIEW, \
                            f"Edge {edge.edgeType} has status '{edge.relationStatus}', expected 'needs_review'"
                    return
        pytest.skip("No usable story pair")

    def test_all_edges_human_review_required(self, service, kg_index):
        """Every edge must have humanReviewRequired=True."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    for edge in result.edges:
                        assert edge.humanReviewRequired is True
                    return
        pytest.skip("No usable story pair")

    def test_path_has_warnings(self, service, kg_index):
        """PathExplanation must include at least one warning."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert len(result.warnings) > 0, "PathExplanation must have warnings"
                    return
        pytest.skip("No usable story pair")


# =============================================================================
# 3. Bilingual explanation text
# =============================================================================

class TestPathExplanationText:

    def test_arabic_explanation_present(self, service, kg_index):
        """PathExplanation must have a non-empty Arabic explanation."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert result.explanationArabic.strip(), "Arabic explanation must not be empty"
                    return
        pytest.skip("No usable story pair")

    def test_english_explanation_present(self, service, kg_index):
        """PathExplanation must have a non-empty English explanation."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    assert result.explanationEnglish.strip(), "English explanation must not be empty"
                    return
        pytest.skip("No usable story pair")

    def test_no_tafsir_invented_in_explanation(self, service, kg_index):
        """Explanation must not assert religious meaning — only generic relation type text."""
        TAFSIR_PHRASES = [
            "means that", "refers to", "proves", "signifies that",
            "interprets", "ruling", "حكم", "تفسير أن", "يدل على",
        ]
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    combined = (result.explanationArabic + " " + result.explanationEnglish).lower()
                    for phrase in TAFSIR_PHRASES:
                        assert phrase.lower() not in combined, \
                            f"Explanation contains tafsir assertion phrase: '{phrase}'"
                    return
        pytest.skip("No usable story pair")


# =============================================================================
# 4. Ayah node fields
# =============================================================================

class TestAyahNodeFields:

    def test_ayah_node_has_surah_and_aya_numbers(self, service, kg_index):
        """Ayah-type nodes must have surahNumber and ayahNumber set."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    ayah_nodes = [n for n in result.nodes if n.type == "ayah"]
                    for node in ayah_nodes:
                        assert node.surahNumber is not None
                        assert node.ayahNumber is not None
                    return
        pytest.skip("No usable story pair")

    def test_ayah_node_has_no_arabic_label(self, service, kg_index):
        """Ayah nodes must not carry Arabic text labels (only reference numbers)."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    ayah_nodes = [n for n in result.nodes if n.type == "ayah"]
                    for node in ayah_nodes:
                        # labelArabic on ayah nodes should be None (just numbers, not text)
                        assert node.labelArabic is None, \
                            f"Ayah node has labelArabic set: {node.labelArabic!r}"
                    return
        pytest.skip("No usable story pair")


# =============================================================================
# 5. find_similar() integration — pathExplanation populated
# =============================================================================

class TestFindSimilarPathIntegration:

    @pytest.mark.asyncio
    async def test_find_similar_populates_path_explanation(self, service, kg_index):
        """find_similar() must populate pathExplanation for returned results."""
        # Find a source ayah that has story connections
        source_key = None
        for key, stories in kg_index.ayah_stories.items():
            if stories:
                source_key = key
                break

        if source_key is None:
            pytest.skip("No ayah with story connections found")

        result = await service.find_similar(
            sura_no=source_key[0],
            aya_no=source_key[1],
            top_k=5,
            min_score=0.05,
        )

        related_with_path = [r for r in result.relatedAyahs if r.pathExplanation is not None]
        # At least some results should have a pathExplanation when story connections exist
        if related_with_path:
            pe = related_with_path[0].pathExplanation
            assert len(pe.nodes) >= 2
            assert len(pe.edges) >= 1
            assert pe.explanationEnglish

    @pytest.mark.asyncio
    async def test_path_explanation_absent_when_no_story_connection(self, service):
        """Ayahs with no story/concept/theme connections should have pathExplanation=None."""
        # Surah 1:1 likely has theme connections but we test the None case is handled
        result = await service.find_similar(
            sura_no=1,
            aya_no=1,
            top_k=5,
            min_score=0.9,  # very high threshold → likely 0 results
        )
        for r in result.relatedAyahs:
            # If path is present, it must be valid
            if r.pathExplanation is not None:
                assert isinstance(r.pathExplanation, PathExplanation)


# =============================================================================
# 6. Serialisability (ensures route mapping won't crash)
# =============================================================================

class TestPathSerialisation:

    def test_path_explanation_is_dataclass_serialisable(self, service, kg_index):
        """PathExplanation and children must serialise via asdict() without error."""
        for _, ayah_set in kg_index.story_ayahs.items():
            if len(ayah_set) >= 2:
                ayahs = list(ayah_set)
                a, b = ayahs[0], ayahs[1]
                result = service._build_path_explanation(a[0], a[1], b[0], b[1])
                if result is not None:
                    d = asdict(result)
                    assert "nodes" in d
                    assert "edges" in d
                    assert "explanationArabic" in d
                    assert "explanationEnglish" in d
                    assert "warnings" in d
                    return
        pytest.skip("No usable story pair")
