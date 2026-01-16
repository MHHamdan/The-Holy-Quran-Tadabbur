"""
Theme Quality Service - 3-Tier Classification & Pruning

CLASSIFICATION RULES (Sunni-safe, 3-Tier):
==========================================
Segments are classified into three tiers based on evidence quality:

CORE (Strongest - High Confidence):
  - Manual segments (curated by scholars) are always CORE
  - (confidence >= 0.82 AND match_type in {direct, exact, root, lexical}) OR
  - (confidence >= 0.74 AND distinct_sources >= 2)

RECOMMENDED (Good - Solid Evidence):
  - (confidence >= 0.70 AND match_type not in {weak, semantic_low}) OR
  - (confidence >= 0.65 AND distinct_sources >= 2)

SUPPORTING (Broader - Supplementary):
  - Everything else that passes minimum quality thresholds

THEME-SPECIFIC GUARDS:
======================
Certain themes require additional validation to prevent false positives:
- tawheed: Must not contain shirk-related keywords unless contextually negating it
- rahma: Must not be in punishment/wrath context without mercy mention
- iman: Must not be in kufr context unless discussing believers vs disbelievers

PRUNING RULES:
==============
Segments are marked for pruning if:
- confidence < 0.35 (very low quality)
- evidence_sources = 0 (no tafsir support)
- reasons_ar contains placeholder text only
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme import ThemeSegment


class SegmentTier(str, Enum):
    """Three-tier quality classification for theme segments."""
    CORE = "core"
    RECOMMENDED = "recommended"
    SUPPORTING = "supporting"


@dataclass
class ClassificationResult:
    """Result of segment classification."""
    segment_id: str
    theme_id: str
    tier: SegmentTier
    is_core: bool  # Backwards compatibility: True for CORE tier
    confidence: float
    evidence_count: int
    reasons_quality_score: float
    classification_reason: str


@dataclass
class PruningCandidate:
    """A segment identified for pruning."""
    segment_id: str
    theme_id: str
    sura_no: int
    ayah_start: int
    ayah_end: int
    confidence: float
    evidence_count: int
    prune_reason: str


# 3-Tier classification thresholds
CORE_CONFIDENCE_DIRECT = 0.82      # CORE with direct match type
CORE_CONFIDENCE_MULTI_SOURCE = 0.74  # CORE with 2+ tafsir sources
RECOMMENDED_CONFIDENCE_SINGLE = 0.70  # RECOMMENDED with good match
RECOMMENDED_CONFIDENCE_MULTI = 0.65   # RECOMMENDED with 2+ sources
PRUNE_MAX_CONFIDENCE = 0.35           # Below this = pruning candidate

# Match type classifications
DIRECT_MATCH_TYPES = {'direct', 'exact', 'root', 'lexical', 'manual', '', None}
WEAK_MATCH_TYPES = {'weak', 'semantic_low'}

# Legacy compatibility
CORE_MIN_EVIDENCE_SOURCES = 2
CORE_MIN_CONFIDENCE = CORE_CONFIDENCE_MULTI_SOURCE

# Theme-specific guards
THEME_GUARDS = {
    "theme_tawheed": {
        "negative_keywords": ["شرك", "عبادة غير الله", "إله مع الله"],
        "require_negation_context": True,
        "min_confidence": 0.65,  # Higher bar for tawheed
    },
    "theme_rahma": {
        "negative_keywords": ["عذاب", "غضب", "نقمة"],
        "require_mercy_context": True,
        "min_confidence": 0.60,
    },
    "theme_iman": {
        "negative_keywords": ["كفر", "شرك", "نفاق"],
        "require_believer_context": True,
        "min_confidence": 0.60,
    },
}

# Placeholder patterns that indicate low-quality reasons_ar
PLACEHOLDER_PATTERNS = [
    r"^تتعلق الآية بموضوع\s+[\u0600-\u06FF\s]+$",  # Generic "relates to theme"
    r"^آية\s+\d+:\d+$",  # Just verse reference
    r"^آيات في موضوع$",  # Just "verses on topic"
]


class ThemeQualityService:
    """Service for theme quality classification and pruning."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def classify_segment(
        self,
        segment: ThemeSegment
    ) -> ClassificationResult:
        """
        Classify a segment into one of three tiers: CORE, RECOMMENDED, SUPPORTING.

        Classification Rules (Sunni-safe):
        - Manual segments are always CORE (curated by scholars)
        - CORE: (conf >= 0.82 AND direct match) OR (conf >= 0.74 AND 2+ sources)
        - RECOMMENDED: (conf >= 0.70 AND non-weak match) OR (conf >= 0.65 AND 2+ sources)
        - SUPPORTING: everything else

        Returns ClassificationResult with tier and reasoning.
        """
        evidence_count = len(segment.evidence_sources or [])
        confidence = segment.confidence or 0.0
        reasons_ar = segment.reasons_ar or ""
        match_type = (segment.match_type or '').lower()

        # Calculate reasons quality score
        reasons_quality = self._calculate_reasons_quality(reasons_ar)

        # Default tier and reason
        tier = SegmentTier.SUPPORTING
        classification_reason = "Default: SUPPORTING tier"

        # Rule 1: Manual segments are always CORE (scholar-curated)
        if match_type == 'manual' or match_type == '':
            tier = SegmentTier.CORE
            classification_reason = "Manual segment (scholar-curated)"

        # Rule 2: CORE tier criteria
        elif confidence >= CORE_CONFIDENCE_DIRECT and match_type in DIRECT_MATCH_TYPES:
            tier = SegmentTier.CORE
            classification_reason = f"CORE: High confidence ({confidence:.2f}) with direct match ({match_type})"
        elif confidence >= CORE_CONFIDENCE_MULTI_SOURCE and evidence_count >= 2:
            tier = SegmentTier.CORE
            classification_reason = f"CORE: Multi-source ({evidence_count} sources) with confidence {confidence:.2f}"

        # Rule 3: RECOMMENDED tier criteria
        elif confidence >= RECOMMENDED_CONFIDENCE_SINGLE and match_type not in WEAK_MATCH_TYPES:
            tier = SegmentTier.RECOMMENDED
            classification_reason = f"RECOMMENDED: Good confidence ({confidence:.2f}) with non-weak match ({match_type})"
        elif confidence >= RECOMMENDED_CONFIDENCE_MULTI and evidence_count >= 2:
            tier = SegmentTier.RECOMMENDED
            classification_reason = f"RECOMMENDED: Multi-source ({evidence_count} sources) with confidence {confidence:.2f}"

        # Rule 4: SUPPORTING tier (default)
        else:
            tier = SegmentTier.SUPPORTING
            classification_reason = f"SUPPORTING: conf={confidence:.2f}, sources={evidence_count}, match={match_type}"

        # Apply theme-specific guards (can downgrade tier)
        if segment.theme_id in THEME_GUARDS:
            guard_result = self._apply_theme_guard(
                segment.theme_id,
                reasons_ar,
                confidence
            )
            if guard_result:
                # Theme guard failed - downgrade to SUPPORTING
                if tier != SegmentTier.SUPPORTING:
                    tier = SegmentTier.SUPPORTING
                    classification_reason = f"Downgraded: {guard_result}"

        return ClassificationResult(
            segment_id=segment.id,
            theme_id=segment.theme_id,
            tier=tier,
            is_core=(tier == SegmentTier.CORE),  # Backwards compatibility
            confidence=confidence,
            evidence_count=evidence_count,
            reasons_quality_score=reasons_quality,
            classification_reason=classification_reason,
        )

    def _calculate_reasons_quality(self, reasons_ar: str) -> float:
        """
        Calculate quality score for reasons_ar text (0.0 to 1.0).

        Higher score = better quality explanation.
        """
        if not reasons_ar or len(reasons_ar.strip()) == 0:
            return 0.0

        # Check for placeholder patterns
        for pattern in PLACEHOLDER_PATTERNS:
            if re.match(pattern, reasons_ar.strip()):
                return 0.2  # Low score for placeholder text

        # Score based on length and content
        score = 0.0

        # Length factor (up to 0.4)
        length = len(reasons_ar)
        if length > 100:
            score += 0.4
        elif length > 50:
            score += 0.3
        elif length > 20:
            score += 0.2
        else:
            score += 0.1

        # Arabic content factor (up to 0.3)
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', reasons_ar))
        if arabic_chars > 50:
            score += 0.3
        elif arabic_chars > 20:
            score += 0.2
        else:
            score += 0.1

        # Tafsir keyword factor (up to 0.3)
        tafsir_keywords = ["تفسير", "ابن كثير", "الطبري", "القرطبي", "قال", "روى"]
        keyword_count = sum(1 for kw in tafsir_keywords if kw in reasons_ar)
        score += min(keyword_count * 0.1, 0.3)

        return min(score, 1.0)

    def _apply_theme_guard(
        self,
        theme_id: str,
        reasons_ar: str,
        confidence: float
    ) -> Optional[str]:
        """
        Apply theme-specific guard rules.

        Returns reason string if guard fails, None if passes.
        """
        guard = THEME_GUARDS.get(theme_id)
        if not guard:
            return None

        # Check minimum confidence for this theme
        min_conf = guard.get("min_confidence", 0.60)
        if confidence < min_conf:
            return f"Theme guard: confidence {confidence:.2f} below {theme_id} minimum {min_conf}"

        # Check negative keywords
        negative_keywords = guard.get("negative_keywords", [])
        for keyword in negative_keywords:
            if keyword in reasons_ar:
                # Check if negation context is required and present
                if guard.get("require_negation_context"):
                    negation_words = ["لا", "نفي", "رد", "إبطال", "تحذير"]
                    has_negation = any(nw in reasons_ar for nw in negation_words)
                    if not has_negation:
                        return f"Theme guard: {theme_id} found '{keyword}' without negation context"

        return None

    async def classify_all_segments(
        self,
        theme_id: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Classify all segments (or segments for a specific theme) into 3 tiers.

        Args:
            theme_id: Optional theme ID to limit classification
            dry_run: If True, don't update database

        Returns:
            Summary statistics of classification with tier breakdown
        """
        # Build query
        query = select(ThemeSegment)
        if theme_id:
            query = query.where(ThemeSegment.theme_id == theme_id)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        stats = {
            "total_segments": len(segments),
            "core_segments": 0,
            "recommended_segments": 0,
            "supporting_segments": 0,
            "tier_breakdown": {
                "core": 0,
                "recommended": 0,
                "supporting": 0,
            },
            "classifications": [],
        }

        for segment in segments:
            classification = await self.classify_segment(segment)
            stats["classifications"].append({
                "segment_id": classification.segment_id,
                "tier": classification.tier.value,
                "is_core": classification.is_core,
                "reason": classification.classification_reason,
            })

            # Track tier counts
            if classification.tier == SegmentTier.CORE:
                stats["core_segments"] += 1
                stats["tier_breakdown"]["core"] += 1
            elif classification.tier == SegmentTier.RECOMMENDED:
                stats["recommended_segments"] += 1
                stats["tier_breakdown"]["recommended"] += 1
            else:
                stats["supporting_segments"] += 1
                stats["tier_breakdown"]["supporting"] += 1

            # Update database if not dry run
            if not dry_run:
                await self.session.execute(
                    update(ThemeSegment)
                    .where(ThemeSegment.id == segment.id)
                    .values(is_core=classification.is_core)
                )

        if not dry_run:
            await self.session.commit()

        # Calculate percentages
        total = stats["total_segments"]
        if total > 0:
            stats["core_percentage"] = round(stats["core_segments"] / total * 100, 1)
            stats["recommended_percentage"] = round(stats["recommended_segments"] / total * 100, 1)
            stats["supporting_percentage"] = round(stats["supporting_segments"] / total * 100, 1)
            stats["quality_percentage"] = round(
                (stats["core_segments"] + stats["recommended_segments"]) / total * 100, 1
            )

        return stats

    async def find_pruning_candidates(
        self,
        theme_id: Optional[str] = None
    ) -> List[PruningCandidate]:
        """
        Find segments that should be pruned (removed or reviewed).

        Pruning criteria:
        - confidence < 0.35
        - evidence_sources = 0
        - reasons_ar is placeholder only
        """
        query = select(ThemeSegment).where(
            ThemeSegment.match_type != 'manual'  # Never prune manual segments
        )

        if theme_id:
            query = query.where(ThemeSegment.theme_id == theme_id)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        candidates = []

        for segment in segments:
            prune_reasons = []

            # Check confidence
            confidence = segment.confidence or 0.0
            if confidence < PRUNE_MAX_CONFIDENCE:
                prune_reasons.append(f"Low confidence: {confidence:.2f}")

            # Check evidence
            evidence_count = len(segment.evidence_sources or [])
            if evidence_count == 0:
                prune_reasons.append("No tafsir evidence")

            # Check reasons_ar quality
            reasons_ar = segment.reasons_ar or ""
            reasons_quality = self._calculate_reasons_quality(reasons_ar)
            if reasons_quality < 0.25:
                prune_reasons.append(f"Placeholder reasons_ar (quality: {reasons_quality:.2f})")

            if prune_reasons:
                candidates.append(PruningCandidate(
                    segment_id=segment.id,
                    theme_id=segment.theme_id,
                    sura_no=segment.sura_no,
                    ayah_start=segment.ayah_start,
                    ayah_end=segment.ayah_end,
                    confidence=confidence,
                    evidence_count=evidence_count,
                    prune_reason="; ".join(prune_reasons),
                ))

        return candidates

    async def prune_segments(
        self,
        candidates: List[PruningCandidate],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Delete pruning candidate segments.

        Args:
            candidates: List of segments to prune
            dry_run: If True, don't actually delete

        Returns:
            Summary of pruning operation
        """
        from sqlalchemy import delete

        segment_ids = [c.segment_id for c in candidates]

        if not dry_run and segment_ids:
            await self.session.execute(
                delete(ThemeSegment)
                .where(ThemeSegment.id.in_(segment_ids))
            )
            await self.session.commit()

        return {
            "dry_run": dry_run,
            "pruned_count": len(candidates),
            "pruned_segments": [
                {
                    "id": c.segment_id,
                    "theme_id": c.theme_id,
                    "verse": f"{c.sura_no}:{c.ayah_start}-{c.ayah_end}",
                    "reason": c.prune_reason,
                }
                for c in candidates
            ],
        }

    async def get_quality_report(
        self,
        theme_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a quality report with 3-tier classification breakdown.
        """
        # Get all segments
        query = select(ThemeSegment)
        if theme_id:
            query = query.where(ThemeSegment.theme_id == theme_id)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        # Calculate basic statistics
        total = len(segments)
        manual = sum(1 for s in segments if (s.match_type or '').lower() in ('manual', ''))
        discovered = total - manual

        # Calculate 3-tier distribution
        tier_counts = {"core": 0, "recommended": 0, "supporting": 0}
        for segment in segments:
            classification = await self.classify_segment(segment)
            tier_counts[classification.tier.value] += 1

        core = tier_counts["core"]
        recommended = tier_counts["recommended"]
        supporting = tier_counts["supporting"]

        # Confidence distribution
        confidence_bands = {
            "high_0.8+": sum(1 for s in segments if (s.confidence or 1.0) >= 0.8),
            "medium_0.5-0.8": sum(1 for s in segments if 0.5 <= (s.confidence or 1.0) < 0.8),
            "low_0.35-0.5": sum(1 for s in segments if PRUNE_MAX_CONFIDENCE <= (s.confidence or 1.0) < 0.5),
            "prune_<0.35": sum(1 for s in segments if (s.confidence or 1.0) < PRUNE_MAX_CONFIDENCE),
        }

        # Evidence distribution
        evidence_bands = {
            "3+_sources": sum(1 for s in segments if len(s.evidence_sources or []) >= 3),
            "2_sources": sum(1 for s in segments if len(s.evidence_sources or []) == 2),
            "1_source": sum(1 for s in segments if len(s.evidence_sources or []) == 1),
            "0_sources": sum(1 for s in segments if len(s.evidence_sources or []) == 0),
        }

        # Find pruning candidates
        prune_candidates = await self.find_pruning_candidates(theme_id)

        return {
            "theme_id": theme_id or "all",
            "total_segments": total,
            "manual_segments": manual,
            "discovered_segments": discovered,
            # 3-tier breakdown
            "tier_breakdown": {
                "core": core,
                "recommended": recommended,
                "supporting": supporting,
            },
            # Legacy fields (backwards compatibility)
            "core_segments": core,
            "supporting_segments": supporting,
            # Percentages
            "core_percentage": round(core / total * 100, 1) if total > 0 else 0,
            "recommended_percentage": round(recommended / total * 100, 1) if total > 0 else 0,
            "supporting_percentage": round(supporting / total * 100, 1) if total > 0 else 0,
            "quality_percentage": round((core + recommended) / total * 100, 1) if total > 0 else 0,
            # Distributions
            "confidence_distribution": confidence_bands,
            "evidence_distribution": evidence_bands,
            "pruning_candidates": len(prune_candidates),
            "sample_prune_candidates": [
                {
                    "id": c.segment_id,
                    "verse": f"{c.sura_no}:{c.ayah_start}",
                    "reason": c.prune_reason,
                }
                for c in prune_candidates[:5]
            ],
        }
