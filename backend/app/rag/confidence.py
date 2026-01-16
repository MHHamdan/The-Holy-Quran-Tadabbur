"""
Confidence scoring and degradation for RAG responses.

EXPLICIT THRESHOLDS (with clear boundaries):
- HIGH_CONFIDENCE >= 0.85: Well-supported response, multiple sources agree
- MEDIUM_CONFIDENCE >= 0.65: Adequate support, may benefit from verification
- LOW_CONFIDENCE >= 0.45: Limited support, response includes strong caveats
- REFUSAL < 0.35: Insufficient evidence - REFUSE to answer

BOUNDARY BEHAVIOR:
- 0.85+: High confidence, no caveats needed
- 0.65-0.84: Medium confidence, suggest verification
- 0.45-0.64: Low confidence, include strong disclaimer
- 0.35-0.44: Borderline - respond with heavy caveats OR refuse based on context
- <0.35: Hard refuse - insufficient evidence

HARD REFUSAL CONDITIONS (any triggers immediate refusal):
- No valid citations found
- All citations invalid
- Citation coverage < 30%
- Average relevance < 0.3
- All sources have reliability < 0.5
"""
from typing import List, Tuple
from dataclasses import dataclass, field


# EXPLICIT THRESHOLD CONSTANTS (with clear separation)
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.65
LOW_CONFIDENCE_THRESHOLD = 0.45
REFUSAL_THRESHOLD = 0.35  # Below this = hard refuse (separated from LOW)

# BORDERLINE ZONE: 0.35 <= score < 0.45 triggers low confidence with heavy caveats

# REFUSAL TRIGGER CONDITIONS
MIN_CITATION_COVERAGE = 0.30  # At least 30% of paragraphs need citations
MIN_AVERAGE_RELEVANCE = 0.20  # Average relevance must be at least 0.2 (lowered for cross-encoder scores)
MIN_TOP_RELEVANCE = 0.50  # At least one chunk must have high relevance
MIN_SOURCE_RELIABILITY = 0.50  # At least one source must have 0.5+ reliability

# EVIDENCE DENSITY REQUIREMENTS
# Response must have EITHER:
#   - >= MIN_DISTINCT_CHUNKS distinct evidence chunks, OR
#   - >= MIN_DISTINCT_SOURCES distinct tafseer sources
MIN_DISTINCT_CHUNKS = 2
MIN_DISTINCT_SOURCES = 2


@dataclass
class EvidenceDensity:
    """Evidence density metrics for grounded responses."""
    distinct_chunks: int = 0
    distinct_sources: int = 0
    source_ids: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    meets_chunk_threshold: bool = False
    meets_source_threshold: bool = False
    is_sufficient: bool = False

    def evaluate(self):
        """Evaluate if evidence density is sufficient."""
        self.meets_chunk_threshold = self.distinct_chunks >= MIN_DISTINCT_CHUNKS
        self.meets_source_threshold = self.distinct_sources >= MIN_DISTINCT_SOURCES
        self.is_sufficient = self.meets_chunk_threshold or self.meets_source_threshold


@dataclass
class ConfidenceBreakdown:
    """Detailed confidence scoring breakdown."""
    base_score: float = 1.0
    citation_coverage_score: float = 1.0
    source_reliability_score: float = 1.0
    relevance_score: float = 1.0
    validation_score: float = 1.0
    evidence_density_score: float = 1.0  # NEW: Evidence density score
    final_score: float = 1.0
    degradation_reasons: List[str] = field(default_factory=list)
    confidence_level: str = "high"  # high, medium, low, insufficient
    should_refuse: bool = False
    refusal_reason: str = ""
    evidence_density: EvidenceDensity = field(default_factory=EvidenceDensity)


class ConfidenceScorer:
    """
    Calculates and degrades confidence based on validation results.

    EXPLICIT REFUSAL POLICY:
    - Refuse if final_score < REFUSAL_THRESHOLD
    - Refuse if any hard refusal condition is triggered
    """

    # Confidence thresholds
    HIGH_CONFIDENCE = HIGH_CONFIDENCE_THRESHOLD
    MEDIUM_CONFIDENCE = MEDIUM_CONFIDENCE_THRESHOLD
    LOW_CONFIDENCE = LOW_CONFIDENCE_THRESHOLD
    REFUSAL = REFUSAL_THRESHOLD

    # Degradation penalties
    PENALTY_NO_CITATION = 0.20  # Per paragraph without citation
    PENALTY_INVALID_CITATION = 0.15  # Per invalid citation
    PENALTY_LOW_RELEVANCE = 0.10  # Per low-relevance source
    PENALTY_NO_PRIMARY_SOURCE = 0.25  # If no primary source used
    PENALTY_SINGLE_SOURCE = 0.15  # If only one source used
    PENALTY_CLAIM_UNSUPPORTED = 0.20  # Per unsupported claim
    PENALTY_LOW_EVIDENCE_DENSITY = 0.25  # If evidence density insufficient

    def calculate(
        self,
        total_paragraphs: int,
        paragraphs_with_citations: int,
        valid_citations: int,
        invalid_citations: int,
        source_reliability_scores: List[float],
        relevance_scores: List[float],
        has_primary_source: bool = True,
        unsupported_claims: int = 0,
        chunk_ids: List[str] = None,
        source_ids: List[str] = None,
    ) -> ConfidenceBreakdown:
        """
        Calculate confidence score with detailed breakdown.

        Args:
            total_paragraphs: Number of substantive paragraphs
            paragraphs_with_citations: Paragraphs with at least one citation
            valid_citations: Number of valid citations
            invalid_citations: Number of invalid citations
            source_reliability_scores: Reliability scores of sources used
            relevance_scores: Relevance scores of retrieved chunks
            has_primary_source: Whether a primary source is included
            unsupported_claims: Number of claims not supported by sources
            chunk_ids: List of chunk IDs used in the response (for evidence density)
            source_ids: List of source IDs used in the response (for evidence density)

        Returns:
            ConfidenceBreakdown with detailed scoring and refusal decision
        """
        # Initialize with defaults if not provided
        chunk_ids = chunk_ids or []
        source_ids = source_ids or []
        breakdown = ConfidenceBreakdown()
        degradation_reasons = []

        # Calculate evidence density
        evidence_density = EvidenceDensity(
            distinct_chunks=len(set(chunk_ids)),
            distinct_sources=len(set(source_ids)),
            source_ids=list(set(source_ids)),
            chunk_ids=list(set(chunk_ids)),
        )
        evidence_density.evaluate()
        breakdown.evidence_density = evidence_density

        # Check hard refusal conditions first
        should_refuse, refusal_reason = self._check_refusal_conditions(
            total_paragraphs=total_paragraphs,
            paragraphs_with_citations=paragraphs_with_citations,
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
            source_reliability_scores=source_reliability_scores,
            relevance_scores=relevance_scores,
            evidence_density=evidence_density,
        )

        if should_refuse:
            breakdown.should_refuse = True
            breakdown.refusal_reason = refusal_reason
            breakdown.confidence_level = "insufficient"
            breakdown.final_score = 0.0
            breakdown.degradation_reasons = [refusal_reason]
            return breakdown

        # 1. Citation coverage score
        if total_paragraphs > 0:
            citation_coverage = paragraphs_with_citations / total_paragraphs
            breakdown.citation_coverage_score = citation_coverage

            missing_citations = total_paragraphs - paragraphs_with_citations
            if missing_citations > 0:
                penalty = min(missing_citations * self.PENALTY_NO_CITATION, 0.5)
                breakdown.base_score -= penalty
                degradation_reasons.append(
                    f"-{penalty:.2f}: {missing_citations} paragraphs lack citations"
                )

        # 2. Invalid citations penalty
        if invalid_citations > 0:
            penalty = min(invalid_citations * self.PENALTY_INVALID_CITATION, 0.4)
            breakdown.base_score -= penalty
            breakdown.validation_score -= penalty
            degradation_reasons.append(
                f"-{penalty:.2f}: {invalid_citations} citations could not be validated"
            )

        # 3. Source reliability score
        if source_reliability_scores:
            avg_reliability = sum(source_reliability_scores) / len(source_reliability_scores)
            breakdown.source_reliability_score = avg_reliability

            if avg_reliability < 0.7:
                penalty = (0.7 - avg_reliability) * 0.3
                breakdown.base_score -= penalty
                degradation_reasons.append(
                    f"-{penalty:.2f}: Low average source reliability ({avg_reliability:.2f})"
                )
        else:
            breakdown.source_reliability_score = 0.5
            breakdown.base_score -= 0.3
            degradation_reasons.append("-0.30: No source reliability data")

        # 4. Relevance score
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            breakdown.relevance_score = avg_relevance

            low_relevance_count = sum(1 for r in relevance_scores if r < 0.5)
            if low_relevance_count > 0:
                penalty = min(low_relevance_count * self.PENALTY_LOW_RELEVANCE, 0.3)
                breakdown.base_score -= penalty
                degradation_reasons.append(
                    f"-{penalty:.2f}: {low_relevance_count} sources with low relevance"
                )
        else:
            breakdown.relevance_score = 0.5
            breakdown.base_score -= 0.2
            degradation_reasons.append("-0.20: No relevance data")

        # 5. Primary source penalty
        if not has_primary_source:
            breakdown.base_score -= self.PENALTY_NO_PRIMARY_SOURCE
            degradation_reasons.append(
                f"-{self.PENALTY_NO_PRIMARY_SOURCE:.2f}: No primary source used"
            )

        # 6. Single source penalty
        if source_reliability_scores and len(set(source_reliability_scores)) == 1:
            breakdown.base_score -= self.PENALTY_SINGLE_SOURCE
            degradation_reasons.append(
                f"-{self.PENALTY_SINGLE_SOURCE:.2f}: Only one source used"
            )

        # 7. Unsupported claims penalty
        if unsupported_claims > 0:
            penalty = min(unsupported_claims * self.PENALTY_CLAIM_UNSUPPORTED, 0.5)
            breakdown.base_score -= penalty
            degradation_reasons.append(
                f"-{penalty:.2f}: {unsupported_claims} claims not clearly supported by sources"
            )

        # 8. Evidence density penalty
        # Require ≥2 distinct chunks OR ≥2 distinct sources
        if not evidence_density.is_sufficient:
            breakdown.base_score -= self.PENALTY_LOW_EVIDENCE_DENSITY
            breakdown.evidence_density_score = 0.5  # Partial score
            degradation_reasons.append(
                f"-{self.PENALTY_LOW_EVIDENCE_DENSITY:.2f}: Insufficient evidence density "
                f"({evidence_density.distinct_chunks} chunks, {evidence_density.distinct_sources} sources) - "
                f"need ≥{MIN_DISTINCT_CHUNKS} chunks OR ≥{MIN_DISTINCT_SOURCES} sources"
            )
        else:
            breakdown.evidence_density_score = 1.0

        # Clamp score
        breakdown.base_score = max(0.0, min(1.0, breakdown.base_score))

        # Calculate final score (weighted average)
        # Weights: base=35%, citation_coverage=20%, source_reliability=15%,
        #          relevance=10%, validation=10%, evidence_density=10%
        breakdown.final_score = (
            breakdown.base_score * 0.35 +
            breakdown.citation_coverage_score * 0.20 +
            breakdown.source_reliability_score * 0.15 +
            breakdown.relevance_score * 0.10 +
            breakdown.validation_score * 0.10 +
            breakdown.evidence_density_score * 0.10
        )

        # Determine confidence level with explicit thresholds
        # Clear separation: LOW >= 0.45, REFUSAL < 0.35, with borderline zone between
        if breakdown.final_score >= self.HIGH_CONFIDENCE:
            breakdown.confidence_level = "high"
        elif breakdown.final_score >= self.MEDIUM_CONFIDENCE:
            breakdown.confidence_level = "medium"
        elif breakdown.final_score >= self.LOW_CONFIDENCE:
            breakdown.confidence_level = "low"
        elif breakdown.final_score >= self.REFUSAL:
            # BORDERLINE ZONE (0.35 <= score < 0.45)
            # Still respond but with heavy caveats - user should verify with scholars
            breakdown.confidence_level = "borderline"
            degradation_reasons.append(
                f"BORDERLINE: Score {breakdown.final_score:.2f} requires scholarly verification"
            )
        else:
            # HARD REFUSAL (score < 0.35)
            breakdown.confidence_level = "insufficient"
            breakdown.should_refuse = True
            breakdown.refusal_reason = f"Confidence score ({breakdown.final_score:.2f}) below refusal threshold ({self.REFUSAL:.2f})"

        breakdown.degradation_reasons = degradation_reasons

        return breakdown

    def _check_refusal_conditions(
        self,
        total_paragraphs: int,
        paragraphs_with_citations: int,
        valid_citations: int,
        invalid_citations: int,
        source_reliability_scores: List[float],
        relevance_scores: List[float],
        evidence_density: EvidenceDensity = None,
    ) -> Tuple[bool, str]:
        """
        Check hard refusal conditions.

        Returns (should_refuse, reason)
        """
        # Condition 1: No citations at all
        if valid_citations == 0:
            return True, "No valid citations found - cannot verify claims"

        # Condition 2: All citations invalid
        if invalid_citations > 0 and valid_citations == 0:
            return True, "All citations invalid - cannot verify claims"

        # Condition 3: Citation coverage too low
        if total_paragraphs > 0:
            coverage = paragraphs_with_citations / total_paragraphs
            if coverage < MIN_CITATION_COVERAGE:
                return True, f"Citation coverage ({coverage:.0%}) below minimum ({MIN_CITATION_COVERAGE:.0%})"

        # Condition 4: Relevance too low
        # Check both average and top relevance - allow response if top chunk is highly relevant
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            max_relevance = max(relevance_scores)
            # Only refuse if BOTH average is too low AND top chunk is also weak
            if avg_relevance < MIN_AVERAGE_RELEVANCE and max_relevance < MIN_TOP_RELEVANCE:
                return True, f"Relevance too low (avg={avg_relevance:.2f}, max={max_relevance:.2f})"

        # Condition 5: All sources have low reliability
        if source_reliability_scores:
            max_reliability = max(source_reliability_scores)
            if max_reliability < MIN_SOURCE_RELIABILITY:
                return True, f"No reliable sources (max reliability: {max_reliability:.2f})"

        # Condition 6: Insufficient evidence density
        # NOTE: This is a degradation condition, not a hard refusal
        # We still allow responses with single source/chunk but with penalty
        # Only refuse if BOTH chunks AND sources are zero
        if evidence_density is not None:
            if evidence_density.distinct_chunks == 0 and evidence_density.distinct_sources == 0:
                return True, "No evidence chunks or sources found - cannot ground response"

        return False, ""


def get_confidence_message(level: str) -> str:
    """Get human-readable confidence message."""
    messages = {
        "high": "This response is well-supported by multiple scholarly sources.",
        "medium": "This response is supported by sources but may benefit from additional verification.",
        "low": "This response has limited source support. Consider consulting additional scholarly works.",
        "borderline": "CAUTION: This response has minimal source support. Please verify with qualified scholars before relying on this information.",
        "insufficient": "Insufficient evidence to provide a reliable answer. Please consult qualified scholars.",
    }
    return messages.get(level, messages["insufficient"])


def should_refuse_response(breakdown: ConfidenceBreakdown) -> Tuple[bool, str]:
    """
    Determine if a response should be refused based on confidence breakdown.

    Returns (should_refuse, message)
    """
    if breakdown.should_refuse:
        return True, breakdown.refusal_reason or "Insufficient evidence to answer"

    if breakdown.confidence_level == "insufficient":
        return True, get_confidence_message("insufficient")

    if breakdown.final_score < REFUSAL_THRESHOLD:
        return True, f"Confidence score ({breakdown.final_score:.2f}) below refusal threshold"

    return False, ""


# Global instance
confidence_scorer = ConfidenceScorer()


# Test cases for verification
REFUSAL_TEST_CASES = [
    {
        "name": "no_citations",
        "params": {
            "total_paragraphs": 5,
            "paragraphs_with_citations": 0,
            "valid_citations": 0,
            "invalid_citations": 0,
            "source_reliability_scores": [],
            "relevance_scores": [],
        },
        "expected_refuse": True,
    },
    {
        "name": "all_invalid_citations",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 0,
            "invalid_citations": 5,
            "source_reliability_scores": [0.8],
            "relevance_scores": [0.7],
        },
        "expected_refuse": True,
    },
    {
        "name": "low_coverage",
        "params": {
            "total_paragraphs": 10,
            "paragraphs_with_citations": 2,
            "valid_citations": 2,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9],
            "relevance_scores": [0.8],
        },
        "expected_refuse": True,  # 20% coverage < 30% minimum
    },
    {
        "name": "low_relevance",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 3,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9],
            "relevance_scores": [0.1, 0.2, 0.15],
        },
        "expected_refuse": True,  # avg relevance 0.15 < 0.30
    },
    {
        "name": "good_response",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 5,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9, 0.85],
            "relevance_scores": [0.8, 0.9, 0.85],
            "chunk_ids": ["chunk_1", "chunk_2", "chunk_3"],
            "source_ids": ["ibn_kathir", "tabari"],
        },
        "expected_refuse": False,
    },
    # Evidence density test cases
    {
        "name": "no_evidence_density",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 3,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9],
            "relevance_scores": [0.8],
            "chunk_ids": [],
            "source_ids": [],
        },
        "expected_refuse": True,  # No chunks or sources = refuse
    },
    {
        "name": "single_chunk_single_source",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 3,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9],
            "relevance_scores": [0.8],
            "chunk_ids": ["chunk_1"],
            "source_ids": ["ibn_kathir"],
        },
        "expected_refuse": False,  # Not refused but gets penalty
    },
    {
        "name": "sufficient_chunks",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 3,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9],
            "relevance_scores": [0.8],
            "chunk_ids": ["chunk_1", "chunk_2"],
            "source_ids": ["ibn_kathir"],  # Only 1 source but 2 chunks = sufficient
        },
        "expected_refuse": False,
    },
    {
        "name": "sufficient_sources",
        "params": {
            "total_paragraphs": 3,
            "paragraphs_with_citations": 3,
            "valid_citations": 3,
            "invalid_citations": 0,
            "source_reliability_scores": [0.9, 0.85],
            "relevance_scores": [0.8],
            "chunk_ids": ["chunk_1"],  # Only 1 chunk but 2 sources = sufficient
            "source_ids": ["ibn_kathir", "tabari"],
        },
        "expected_refuse": False,
    },
]


def run_refusal_tests() -> list[dict]:
    """Run refusal test cases."""
    results = []

    for test in REFUSAL_TEST_CASES:
        breakdown = confidence_scorer.calculate(**test["params"])
        should_refuse, reason = should_refuse_response(breakdown)

        passed = should_refuse == test["expected_refuse"]

        results.append({
            "name": test["name"],
            "passed": passed,
            "expected_refuse": test["expected_refuse"],
            "actual_refuse": should_refuse,
            "reason": reason,
            "confidence_level": breakdown.confidence_level,
            "final_score": breakdown.final_score,
        })

    return results
