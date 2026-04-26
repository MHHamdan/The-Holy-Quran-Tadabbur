"""
Phase 2.5 – Strict sourceId validation unit tests.

Rules under test:
1. Missing source_id → hard block (no_verified_source)
2. Unknown source_id → hard block
3. Known source_id (base form) → allowed
4. Known source_id (_ar suffix) → allowed
5. Known source_id (_en suffix) → allowed
6. Experimental-only + intent=ruling → hard block
7. Experimental-only + intent=verse_meaning → allowed (warning only if no high-reliability)
8. Supporting-only citations → non-fatal warning
9. At least one verified/canonical citation → no reliability warning
10. Empty citation list → hard block
11. is_trusted_source_id() helper works correctly
12. TRUSTED_SOURCE_IDS contains expected canonical IDs
13. Hard block: no answer can have status=answered with empty citations after validation
14. Bilingual hard-block messages are correct format
15. validate_citations returns filtered_citations on success

Run with: pytest tests/unit/test_source_validation.py -v
"""
import pytest
from app.rag.source_validator import (
    SourceValidator,
    SourceValidationResult,
    TRUSTED_SOURCE_IDS,
    source_validator,
)
from app.rag.types import Citation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_citation(
    source_id: str = "ibn_kathir",
    reliability_level: str = "verified",
    verse_reference: str = "2:255",
) -> Citation:
    return Citation(
        chunk_id=f"{source_id}_2_255",
        source_id=source_id,
        source_name="Ibn Kathir",
        source_name_ar="ابن كثير",
        verse_reference=verse_reference,
        excerpt="Test excerpt.",
        relevance_score=0.9,
        reliability_level=reliability_level,
        surah_number=2,
        ayah_number=255,
    )


# ---------------------------------------------------------------------------
# 1–2. source_id presence and trust
# ---------------------------------------------------------------------------

class TestSourceIdPresence:
    def test_missing_source_id_is_hard_block(self):
        cit = make_citation(source_id="")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid
        assert "missing source_id" in result.hard_block_reason.lower()

    def test_none_source_id_is_hard_block(self):
        cit = make_citation()
        cit.source_id = None  # type: ignore
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid

    def test_unknown_source_id_is_hard_block(self):
        cit = make_citation(source_id="made_up_source")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid
        assert "made_up_source" in result.hard_block_reason
        assert "trusted registry" in result.hard_block_reason.lower()

    def test_invented_source_name_is_hard_block(self):
        cit = make_citation(source_id="al_hallucinator_123")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid

    def test_partially_matching_source_id_is_blocked(self):
        """'ibn' alone is not a valid source_id."""
        cit = make_citation(source_id="ibn")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid


# ---------------------------------------------------------------------------
# 3–5. Known source IDs (base + suffixed DB variants)
# ---------------------------------------------------------------------------

class TestTrustedSourceIds:
    @pytest.mark.parametrize("source_id", [
        "ibn_kathir",
        "tabari",
        "qurtubi",
        "jalalayn",
        "fi_zilal",
        "sha_rawi",
        "muyassar",
        "ibn_ashur",
        "saadi",
        "tantawi",
        "bayyinah",
        "maariful_quran",
        "tafsir_hamiduddin",
        "tafsir_french",
        "tafsir_indonesian",
    ])
    def test_catalog_base_id_is_trusted(self, source_id):
        cit = make_citation(source_id=source_id)
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid, f"Expected {source_id} to be trusted, got: {result.hard_block_reason}"

    def test_ar_suffix_variant_is_trusted(self):
        cit = make_citation(source_id="ibn_kathir_ar")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid

    def test_en_suffix_variant_is_trusted(self):
        cit = make_citation(source_id="tabari_en")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid

    def test_trusted_source_ids_contains_canonical_sources(self):
        for expected in ("ibn_kathir", "tabari", "qurtubi", "ibn_kathir_ar", "tabari_en"):
            assert expected in TRUSTED_SOURCE_IDS

    def test_trusted_source_ids_excludes_unknown(self):
        for unknown in ("random_scholar", "hallucinated_tafsir", "", "ibn"):
            assert unknown not in TRUSTED_SOURCE_IDS


# ---------------------------------------------------------------------------
# 6–7. Experimental-only + ruling intent
# ---------------------------------------------------------------------------

class TestExperimentalRulingBlock:
    def test_experimental_only_ruling_is_hard_block(self):
        cit = make_citation(reliability_level="experimental")
        result = source_validator.validate_citations([cit], intent="ruling")
        assert not result.is_valid
        assert "experimental" in result.hard_block_reason.lower()
        assert "ruling" in result.hard_block_reason.lower()

    def test_experimental_only_verse_meaning_is_allowed(self):
        """Experimental sources are allowed for non-ruling intents."""
        cit = make_citation(reliability_level="experimental")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid

    def test_mixed_reliability_ruling_is_allowed(self):
        """At least one verified source unblocks a ruling query."""
        exp = make_citation(source_id="ibn_kathir", reliability_level="experimental")
        ver = make_citation(source_id="tabari", reliability_level="verified")
        result = source_validator.validate_citations([exp, ver], intent="ruling")
        assert result.is_valid

    def test_canonical_source_ruling_is_allowed(self):
        cit = make_citation(reliability_level="canonical")
        result = source_validator.validate_citations([cit], intent="ruling")
        assert result.is_valid

    def test_verified_source_ruling_is_allowed(self):
        cit = make_citation(reliability_level="verified")
        result = source_validator.validate_citations([cit], intent="ruling")
        assert result.is_valid


# ---------------------------------------------------------------------------
# 8–9. Supporting-only → warning; high-reliability → no warning
# ---------------------------------------------------------------------------

class TestReliabilityWarnings:
    def test_supporting_only_adds_warning(self):
        cit = make_citation(reliability_level="supporting")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("supporting" in w.lower() for w in result.warnings)

    def test_experimental_non_ruling_adds_warning(self):
        cit = make_citation(reliability_level="experimental")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_verified_citation_no_reliability_warning(self):
        cit = make_citation(reliability_level="verified")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid
        assert not any("supporting" in w.lower() for w in result.warnings)

    def test_canonical_citation_no_reliability_warning(self):
        cit = make_citation(reliability_level="canonical")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid
        assert not any("supporting" in w.lower() for w in result.warnings)

    def test_mixed_reliability_no_reliability_warning(self):
        sup = make_citation(source_id="ibn_kathir", reliability_level="supporting")
        ver = make_citation(source_id="tabari", reliability_level="verified")
        result = source_validator.validate_citations([sup, ver], intent="verse_meaning")
        assert result.is_valid
        assert not any("supporting or experimental" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# 10. Empty citation list → hard block
# ---------------------------------------------------------------------------

class TestEmptyCitations:
    def test_empty_list_is_hard_block(self):
        result = source_validator.validate_citations([], intent="verse_meaning")
        assert not result.is_valid
        assert result.hard_block_reason is not None

    def test_empty_list_returns_empty_filtered_citations(self):
        result = source_validator.validate_citations([], intent="verse_meaning")
        assert result.filtered_citations == []


# ---------------------------------------------------------------------------
# 11. is_trusted_source_id helper
# ---------------------------------------------------------------------------

class TestIsTrustedSourceId:
    def test_known_id_is_trusted(self):
        assert source_validator.is_trusted_source_id("ibn_kathir")
        assert source_validator.is_trusted_source_id("tabari_ar")
        assert source_validator.is_trusted_source_id("saadi_en")

    def test_empty_string_is_not_trusted(self):
        assert not source_validator.is_trusted_source_id("")

    def test_none_is_not_trusted(self):
        assert not source_validator.is_trusted_source_id(None)  # type: ignore

    def test_unknown_string_is_not_trusted(self):
        assert not source_validator.is_trusted_source_id("random_scholar_xyz")


# ---------------------------------------------------------------------------
# 12. Hard block: no answered + empty citations
# ---------------------------------------------------------------------------

class TestNoAnsweredWithEmptyCitations:
    def test_valid_citation_list_has_filtered_citations(self):
        cit = make_citation()
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert result.is_valid
        assert len(result.filtered_citations) == 1
        assert result.filtered_citations[0].source_id == "ibn_kathir"

    def test_hard_block_returns_no_filtered_citations(self):
        cit = make_citation(source_id="unknown_source")
        result = source_validator.validate_citations([cit], intent="verse_meaning")
        assert not result.is_valid
        assert result.filtered_citations == []

    def test_second_unknown_in_list_also_blocked(self):
        """Validation fails even if the first citation is valid."""
        good = make_citation(source_id="ibn_kathir")
        bad = make_citation(source_id="made_up")
        result = source_validator.validate_citations([good, bad], intent="verse_meaning")
        assert not result.is_valid
        assert "made_up" in result.hard_block_reason


# ---------------------------------------------------------------------------
# 13. Singleton is importable and functional
# ---------------------------------------------------------------------------

class TestModuleSingleton:
    def test_source_validator_singleton_exists(self):
        from app.rag.source_validator import source_validator as sv
        assert sv is not None
        assert isinstance(sv, SourceValidator)

    def test_singleton_and_class_agree(self):
        sv = SourceValidator()
        cit = make_citation()
        r1 = sv.validate_citations([cit], intent="verse_meaning")
        r2 = source_validator.validate_citations([cit], intent="verse_meaning")
        assert r1.is_valid == r2.is_valid
