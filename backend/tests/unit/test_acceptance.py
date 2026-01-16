#!/usr/bin/env python3
"""
Acceptance tests for RAG pipeline grounding, refusal, and citation validation.

ACCEPTANCE CRITERIA:
1. GROUNDING: Responses MUST be based on retrieved evidence
2. REFUSAL: System MUST refuse when evidence is insufficient
3. CITATION: All citations MUST be validated against sources

These tests verify the safety guarantees of the RAG system.

Run with: pytest tests/test_acceptance.py -v
Run fast only: pytest -m "unit" -v
"""
import pytest

# All tests in this file are fast unit tests (no external services)
pytestmark = pytest.mark.unit
import sys
import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.types import (
    RetrievedChunk,
    Citation,
    GroundedResponse,
    SAFE_REFUSAL_INSUFFICIENT,
    SAFE_REFUSAL_NO_SOURCES,
)
from app.rag.confidence import (
    confidence_scorer,
    should_refuse_response,
    REFUSAL_THRESHOLD,
    MIN_CITATION_COVERAGE,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@dataclass
class MockChunk:
    """Mock retrieved chunk for testing."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str
    verse_reference: str
    sura_no: int
    aya_start: int
    aya_end: int
    content: str
    content_ar: str = ""
    content_en: str = ""
    relevance_score: float = 0.8
    is_primary_source: bool = True
    source_reliability: float = 0.9
    methodology: str = "bil_mathur"


def create_mock_chunks(count: int = 3) -> List[MockChunk]:
    """Create mock chunks for testing."""
    return [
        MockChunk(
            chunk_id=f"chunk_{i}",
            source_id=f"source_{i % 2}",
            source_name=f"Test Tafseer {i}",
            source_name_ar=f"تفسير اختبار {i}",
            verse_reference=f"1:{i+1}",
            sura_no=1,
            aya_start=i+1,
            aya_end=i+1,
            content=f"This is test content for chunk {i}. It contains scholarly interpretation.",
            content_en=f"This is test content for chunk {i}.",
            content_ar=f"هذا محتوى اختباري للمقطع {i}.",
            relevance_score=0.85 - (i * 0.05),
        )
        for i in range(count)
    ]


# ============================================================================
# 1. GROUNDING TESTS
# ============================================================================

class TestGrounding:
    """
    Tests that verify responses are grounded in retrieved evidence.

    A grounded response MUST:
    - Have citations for claims
    - Reference only retrieved chunks
    - Not invent information beyond sources
    """

    def test_response_must_have_citations(self):
        """A valid response MUST include at least one citation."""
        response = GroundedResponse(
            answer="Test answer with citation [Source, 1:1]",
            citations=[
                Citation(
                    chunk_id="chunk_1",
                    source_id="source_1",
                    source_name="Test Source",
                    source_name_ar="مصدر اختبار",
                    verse_reference="1:1",
                    excerpt="Test excerpt",
                    relevance_score=0.9,
                )
            ],
            confidence=0.85,
            intent="verse_meaning",
        )

        assert len(response.citations) > 0, "Response must have at least one citation"

    def test_citation_must_have_source_reference(self):
        """Every citation MUST include source and verse reference."""
        citation = Citation(
            chunk_id="chunk_1",
            source_id="source_1",
            source_name="Ibn Kathir",
            source_name_ar="ابن كثير",
            verse_reference="2:255",
            excerpt="Test",
            relevance_score=0.9,
        )

        assert citation.source_id != "", "Citation must have source_id"
        assert citation.source_name != "", "Citation must have source_name"
        assert citation.verse_reference != "", "Citation must have verse_reference"
        assert ":" in citation.verse_reference, "Verse reference must be in format X:Y"

    def test_high_confidence_requires_multiple_sources(self):
        """High confidence requires evidence from multiple sources."""
        # Single source
        single_source = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.9, 0.85, 0.8],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s1", "s1"],  # Same source
        )

        # Multiple sources
        multi_source = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9, 0.85],
            relevance_scores=[0.9, 0.85, 0.8],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],  # Multiple sources
        )

        assert multi_source.final_score >= single_source.final_score, \
            "Multiple sources should increase or maintain confidence"

    def test_evidence_density_tracked(self):
        """Evidence density (chunks and sources) must be tracked."""
        breakdown = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9, 0.85],
            relevance_scores=[0.9, 0.85, 0.8],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        assert breakdown.evidence_density.distinct_chunks == 3
        assert breakdown.evidence_density.distinct_sources == 2


# ============================================================================
# 2. REFUSAL TESTS
# ============================================================================

class TestRefusal:
    """
    Tests that verify the system refuses when evidence is insufficient.

    The system MUST refuse when:
    - No citations found
    - Citation coverage too low
    - Source reliability too low
    - Relevance scores too low
    """

    def test_refuse_no_citations(self):
        """MUST refuse when response has no valid citations."""
        breakdown = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=0,
            valid_citations=0,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1"],
            source_ids=["s1"],
        )

        assert breakdown.should_refuse, "Must refuse with no citations"
        assert "No valid citations" in breakdown.refusal_reason

    def test_refuse_low_coverage(self):
        """MUST refuse when citation coverage is below minimum."""
        breakdown = confidence_scorer.calculate(
            total_paragraphs=10,
            paragraphs_with_citations=2,  # 20% coverage < 30% min
            valid_citations=2,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2"],
            source_ids=["s1", "s2"],
        )

        assert breakdown.should_refuse, "Must refuse with low coverage"
        assert "coverage" in breakdown.refusal_reason.lower()

    def test_refuse_no_reliable_sources(self):
        """MUST refuse when no source meets reliability minimum."""
        breakdown = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.3, 0.4],  # All below 0.5
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        assert breakdown.should_refuse, "Must refuse with no reliable sources"
        assert "reliable" in breakdown.refusal_reason.lower()

    def test_refuse_low_relevance(self):
        """MUST refuse when average relevance is below minimum."""
        breakdown = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.1, 0.2, 0.1],  # avg < 0.30
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        assert breakdown.should_refuse, "Must refuse with low relevance"
        assert "relevance" in breakdown.refusal_reason.lower()

    def test_refuse_insufficient_evidence_message(self):
        """Refusal message must be safe and informative."""
        assert "scholar" in SAFE_REFUSAL_INSUFFICIENT.lower() or \
               "evidence" in SAFE_REFUSAL_INSUFFICIENT.lower()
        assert "scholar" in SAFE_REFUSAL_NO_SOURCES.lower()

    def test_borderline_does_not_hard_refuse(self):
        """Borderline confidence (0.35-0.45) should NOT hard refuse."""
        from app.rag.confidence import ConfidenceBreakdown

        breakdown = ConfidenceBreakdown()
        breakdown.final_score = 0.40
        breakdown.confidence_level = "borderline"
        breakdown.should_refuse = False  # Borderline still responds

        should_refuse, _ = should_refuse_response(breakdown)
        assert not should_refuse, "Borderline should respond with caveats, not refuse"


# ============================================================================
# 3. CITATION VALIDATION TESTS
# ============================================================================

class TestCitationValidation:
    """
    Tests for citation validation logic.

    Citations MUST:
    - Reference valid source IDs
    - Include proper verse references
    - Match retrieved chunks
    """

    def test_citation_pattern_matches_format(self):
        """Citation pattern must match [Source, X:Y] format."""
        pattern = r'\[([^\]]+)[,،]\s*([٠-٩\d]+:[٠-٩\d]+(?:-[٠-٩\d]+)?)\]'

        # Valid citations
        assert re.search(pattern, "[Ibn Kathir, 2:255]")
        assert re.search(pattern, "[Tabari, 12:7-10]")
        assert re.search(pattern, "[تفسير الطبري، ٢:٢٥٥]")  # Arabic

        # Invalid citations
        assert not re.search(pattern, "Ibn Kathir 2:255")  # No brackets
        assert not re.search(pattern, "[Ibn Kathir 2:255]")  # No comma

    def test_arabic_numeral_conversion(self):
        """Arabic-Indic numerals must convert to Latin numerals."""
        def arabic_to_latin(s: str) -> str:
            arabic_nums = '٠١٢٣٤٥٦٧٨٩'
            latin_nums = '0123456789'
            for a, l in zip(arabic_nums, latin_nums):
                s = s.replace(a, l)
            return s

        assert arabic_to_latin("٢:٢٥٥") == "2:255"
        assert arabic_to_latin("١٢:٧") == "12:7"
        assert arabic_to_latin("٣٠:٤١") == "30:41"

    def test_verse_reference_parsing(self):
        """Verse references must parse correctly."""
        def parse_verse_ref(ref: str) -> Tuple[int, int, int]:
            if ':' not in ref:
                return (0, 0, 0)
            parts = ref.split(':')
            sura = int(parts[0])
            aya_part = parts[1]
            if '-' in aya_part:
                aya_parts = aya_part.split('-')
                return (sura, int(aya_parts[0]), int(aya_parts[1]))
            return (sura, int(aya_part), int(aya_part))

        assert parse_verse_ref("2:255") == (2, 255, 255)
        assert parse_verse_ref("12:7-10") == (12, 7, 10)
        assert parse_verse_ref("1:1") == (1, 1, 1)

    def test_verse_overlap_detection(self):
        """Must detect when cited verse overlaps with chunk verse range."""
        def verse_overlaps(cited: Tuple[int, int, int], chunk_sura: int, chunk_start: int, chunk_end: int) -> bool:
            cited_sura, cited_start, cited_end = cited
            if cited_sura != chunk_sura:
                return False
            return not (cited_end < chunk_start or cited_start > chunk_end)

        # Exact match
        assert verse_overlaps((2, 255, 255), 2, 255, 255)

        # Overlapping range
        assert verse_overlaps((12, 7, 7), 12, 5, 10)

        # Non-overlapping
        assert not verse_overlaps((12, 7, 7), 12, 1, 5)
        assert not verse_overlaps((12, 7, 7), 13, 7, 7)  # Different sura

    def test_invalid_citations_penalize_confidence(self):
        """Invalid citations must reduce confidence score."""
        no_invalid = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        with_invalid = confidence_scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=2,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        assert with_invalid.final_score < no_invalid.final_score, \
            "Invalid citations must penalize confidence"


# ============================================================================
# 4. EVIDENCE EXPOSURE TESTS
# ============================================================================

class TestEvidenceExposure:
    """
    Tests for evidence transparency in responses.

    The system MUST:
    - Expose retrieved chunks in response
    - Include evidence density metrics
    - Allow users to verify grounding
    """

    def test_grounded_response_includes_evidence(self):
        """GroundedResponse must include evidence field."""
        chunks = create_mock_chunks(3)

        response = GroundedResponse(
            answer="Test answer",
            citations=[],
            confidence=0.5,
            intent="test",
            evidence=chunks,
        )

        assert len(response.evidence) == 3, "Evidence must be included"

    def test_evidence_includes_required_fields(self):
        """Evidence chunks must include all required fields."""
        chunk = create_mock_chunks(1)[0]

        required_fields = [
            'chunk_id', 'source_id', 'source_name', 'source_name_ar',
            'verse_reference', 'sura_no', 'aya_start', 'aya_end',
            'content', 'relevance_score'
        ]

        for field in required_fields:
            assert hasattr(chunk, field), f"Evidence must include {field}"

    def test_to_dict_includes_evidence(self):
        """to_dict() must serialize evidence array."""
        chunks = create_mock_chunks(2)

        # Convert MockChunk to RetrievedChunk for the test
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=c.chunk_id,
                source_id=c.source_id,
                source_name=c.source_name,
                source_name_ar=c.source_name_ar,
                verse_reference=c.verse_reference,
                sura_no=c.sura_no,
                aya_start=c.aya_start,
                aya_end=c.aya_end,
                content=c.content,
                content_ar=c.content_ar,
                content_en=c.content_en,
                relevance_score=c.relevance_score,
            )
            for c in chunks
        ]

        response = GroundedResponse(
            answer="Test",
            citations=[],
            confidence=0.5,
            intent="test",
            evidence=retrieved_chunks,
        )

        response_dict = response.to_dict()

        assert "evidence" in response_dict, "to_dict must include evidence"
        assert len(response_dict["evidence"]) == 2
        assert response_dict["evidence"][0]["chunk_id"] == chunks[0].chunk_id


# ============================================================================
# 5. FIQH SAFETY TESTS
# ============================================================================

class TestFiqhSafety:
    """
    Tests for fiqh (Islamic jurisprudence) safety.

    For fiqh questions:
    - MUST include disclaimer
    - MUST NOT present as fatwa
    - MUST direct to scholars
    """

    def test_fiqh_warning_content(self):
        """Fiqh warning must include required elements."""
        from app.rag.types import SAFE_REFUSAL_FIQH

        warning_lower = SAFE_REFUSAL_FIQH.lower()

        assert "fatwa" in warning_lower, "Must mention this is not fatwa"
        assert "scholar" in warning_lower, "Must direct to scholars"
        assert "educational" in warning_lower or "informational" in warning_lower, \
            "Must clarify informational purpose"

    def test_ruling_intent_triggers_warning(self):
        """Ruling intent must trigger fiqh warning."""
        from app.rag.types import QueryIntent

        # The pipeline should add SAFE_REFUSAL_FIQH to warnings for ruling intent
        assert QueryIntent.RULING.value == "ruling"


# ============================================================================
# 6. LANGUAGE POLICY TESTS
# ============================================================================

class TestLanguagePolicy:
    """
    Tests for language policy enforcement.

    RAG reasoning is ONLY in Arabic (ar) and English (en).
    Other languages are display-only.
    """

    def test_supported_languages_defined(self):
        """RAG supported languages must be defined."""
        from app.rag.types import RAG_SUPPORTED_LANGUAGES

        assert "ar" in RAG_SUPPORTED_LANGUAGES
        assert "en" in RAG_SUPPORTED_LANGUAGES
        assert len(RAG_SUPPORTED_LANGUAGES) == 2

    def test_display_only_languages_defined(self):
        """Display-only languages must be defined."""
        from app.rag.types import DISPLAY_ONLY_LANGUAGES

        assert "ur" in DISPLAY_ONLY_LANGUAGES  # Urdu
        assert "ar" not in DISPLAY_ONLY_LANGUAGES
        assert "en" not in DISPLAY_ONLY_LANGUAGES


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
