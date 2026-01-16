"""
Acceptance Criteria Constants - Single Source of Truth

This module defines the minimum requirements for system correctness.
All verification scripts MUST reference these constants.

MODIFICATION WARNING:
=====================
Changing these values affects the acceptance gate for the entire system.
Any modification requires:
1. Review by project maintainer
2. Update to all verify_* scripts
3. Re-run of full test suite
4. Documentation update

These values are based on:
- Quran: 114 surahs, 6236 verses (standard Uthmani mushaf)
- Tafseer: Ibn Kathir + additional sources from quran-tafsir CDN
- Stories: Based on curriculum of major Quranic stories
"""

# =============================================================================
# QURAN DATA REQUIREMENTS
# =============================================================================

# Standard Uthmani mushaf verse count (absolute minimum)
MIN_VERSES = 6236

# Number of surahs in the Quran
EXPECTED_SURAHS = 114

# Juz (parts) count
EXPECTED_JUZ = 30


# =============================================================================
# TAFSEER DATA REQUIREMENTS
# =============================================================================

# Minimum tafseer chunks required for RAG to function
# Based on: Ibn Kathir EN (~6200) + Ibn Kathir AR (~6200) = ~12400
MIN_TAFSEER_CHUNKS = 10_000

# Minimum number of tafseer sources required
MIN_TAFSEER_SOURCES = 1

# All sources must have valid provenance
REQUIRE_PROVENANCE = True


# =============================================================================
# STORY DATA REQUIREMENTS
# =============================================================================

# Minimum stories required (major prophetic narratives)
# Adam, Nuh, Ibrahim, Musa, Isa, Yusuf, Dawud, Sulayman, etc.
MIN_STORIES = 25

# Minimum story segments (individual narrative units)
MIN_STORY_SEGMENTS = 100


# =============================================================================
# RAG PIPELINE REQUIREMENTS
# =============================================================================

# Evidence density thresholds (from confidence.py)
MIN_EVIDENCE_CHUNKS = 2
MIN_EVIDENCE_SOURCES = 2

# Supported languages for RAG reasoning
RAG_LANGUAGES = {"ar", "en"}

# Embedding dimension (must match across all collections)
EXPECTED_EMBEDDING_DIMENSION = 1024

# Qdrant collection name
QDRANT_COLLECTION = "tafseer_chunks"


# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

# Below this score, response is refused
REFUSAL_THRESHOLD = 0.35

# Minimum citation coverage
MIN_CITATION_COVERAGE = 0.30

# Minimum average relevance
MIN_AVERAGE_RELEVANCE = 0.30


# =============================================================================
# VERIFICATION HELPER
# =============================================================================

def get_acceptance_summary() -> dict:
    """
    Get summary of all acceptance criteria.

    Returns:
        dict with all acceptance thresholds
    """
    return {
        "quran": {
            "min_verses": MIN_VERSES,
            "expected_surahs": EXPECTED_SURAHS,
            "expected_juz": EXPECTED_JUZ,
        },
        "tafseer": {
            "min_chunks": MIN_TAFSEER_CHUNKS,
            "min_sources": MIN_TAFSEER_SOURCES,
            "require_provenance": REQUIRE_PROVENANCE,
        },
        "stories": {
            "min_stories": MIN_STORIES,
            "min_segments": MIN_STORY_SEGMENTS,
        },
        "rag": {
            "min_evidence_chunks": MIN_EVIDENCE_CHUNKS,
            "min_evidence_sources": MIN_EVIDENCE_SOURCES,
            "supported_languages": list(RAG_LANGUAGES),
            "embedding_dimension": EXPECTED_EMBEDDING_DIMENSION,
        },
        "confidence": {
            "refusal_threshold": REFUSAL_THRESHOLD,
            "min_citation_coverage": MIN_CITATION_COVERAGE,
            "min_average_relevance": MIN_AVERAGE_RELEVANCE,
        },
    }


if __name__ == "__main__":
    import json
    print("ACCEPTANCE CRITERIA")
    print("=" * 60)
    print(json.dumps(get_acceptance_summary(), indent=2))
