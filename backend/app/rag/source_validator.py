"""
Phase 2.5 – Strict source-ID validation for RAG citations.

Rules enforced:
1. Every citation must have a non-empty source_id.
2. source_id must exist in TRUSTED_SOURCE_IDS (catalog keys + _ar/_en DB variants).
3. Missing or unknown source_id → hard block → status=no_verified_source.
4. Experimental-only citations with intent=ruling → hard block.
5. Supporting-only citations (no verified/canonical) → warning appended.
"""
from typing import List, Optional
from dataclasses import dataclass, field

from app.services.tafsir_sources import TAFSIR_CATALOG
from app.rag.types import Citation

# ---------------------------------------------------------------------------
# Trusted source registry — built once at import time
# ---------------------------------------------------------------------------

_BASE_IDS: frozenset = frozenset(TAFSIR_CATALOG.keys())

# DB stores language-suffixed variants (e.g. "ibn_kathir_ar", "ibn_kathir_en").
# Accept both the base ID and the two suffix forms.
TRUSTED_SOURCE_IDS: frozenset = frozenset(
    _BASE_IDS
    | {f"{sid}_ar" for sid in _BASE_IDS}
    | {f"{sid}_en" for sid in _BASE_IDS}
)

_HIGH_RELIABILITY = frozenset({"canonical", "verified"})
_EXPERIMENTAL_ONLY = frozenset({"experimental"})


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class SourceValidationResult:
    """Outcome of citation source validation."""
    is_valid: bool
    hard_block_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    filtered_citations: List[Citation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class SourceValidator:
    """
    Validates that every citation in a RAG response comes from a known,
    trusted tafsir source.

    The trusted list is TAFSIR_CATALOG from tafsir_sources.py (15 sources)
    plus their _ar/_en DB variants — 45 total accepted IDs.

    A hard block (is_valid=False) forces the pipeline to return
    status="no_verified_source" with the bilingual safe refusal text.
    """

    def is_trusted_source_id(self, source_id: str) -> bool:
        """Return True only if source_id appears in the trusted registry."""
        return bool(source_id) and source_id in TRUSTED_SOURCE_IDS

    def validate_citations(
        self,
        citations: List[Citation],
        intent: str,
        language: str = "en",
    ) -> SourceValidationResult:
        """
        Apply all source-validation rules to a list of citations.

        Returns SourceValidationResult.  If is_valid=False, the caller
        must replace the response with a no_verified_source refusal.
        """
        # Rule 0: no citations at all
        if not citations:
            return SourceValidationResult(
                is_valid=False,
                hard_block_reason="No citations — no verified source available.",
            )

        # Rules 1 & 2: every source_id must be non-empty and in the registry
        for cit in citations:
            if not cit.source_id:
                return SourceValidationResult(
                    is_valid=False,
                    hard_block_reason=(
                        "Citation has missing source_id — cannot verify provenance."
                    ),
                )
            if cit.source_id not in TRUSTED_SOURCE_IDS:
                return SourceValidationResult(
                    is_valid=False,
                    hard_block_reason=(
                        f"Unknown source_id '{cit.source_id}' — not in trusted registry."
                    ),
                )

        # All source IDs are trusted; proceed to reliability checks
        warnings: List[str] = []

        reliability_levels = frozenset(
            (c.reliability_level or "experimental") for c in citations
        )

        # Rule 3: experimental-only + ruling intent → hard block
        if intent == "ruling" and reliability_levels <= _EXPERIMENTAL_ONLY:
            return SourceValidationResult(
                is_valid=False,
                hard_block_reason=(
                    "A religious ruling requires at least one verified or canonical source; "
                    "only experimental sources found."
                ),
            )

        # Rule 4: no high-reliability source → non-fatal warning
        if not (reliability_levels & _HIGH_RELIABILITY):
            warnings.append(
                "All citations come from supporting or experimental sources. "
                "Consider verifying with canonical or verified scholarly sources."
            )

        return SourceValidationResult(
            is_valid=True,
            warnings=warnings,
            filtered_citations=list(citations),
        )


# Module-level singleton used by the pipeline
source_validator = SourceValidator()
