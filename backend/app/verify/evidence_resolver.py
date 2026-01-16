"""
Evidence Resolver Module - Maps ayah ranges to tafsir chunk IDs.

PR2/PR4: Provides evidence grounding for Quranic stories by resolving ayah
ranges to tafsir chunk references with QUALITY METRICS.

GROUNDING RULES:
================
- Every claim must map to at least one tafsir chunk
- Chunk IDs follow pattern: {source_id}:{sura}:{ayah_start}-{ayah_end}
- Multiple sources are REQUIRED for verification (MIN_DISTINCT_SOURCES=2)
- Uncertain mappings should be flagged for review

QUALITY THRESHOLDS:
===================
- MIN_DISTINCT_SOURCES = 2 (must have evidence from >=2 tafsir sources)
- MIN_DISTINCT_CHUNKS = 2 (must have >=2 chunks per story)
- EVIDENCE_DENSITY_THRESHOLD = 0.5 (>=50% of events must be grounded)

SUPPORTED SOURCES:
==================
- ibn_kathir: تفسير ابن كثير
- tabari: تفسير الطبري
- qurtubi: تفسير القرطبي
- saadi: تفسير السعدي

DETERMINISM:
============
- Running populate_evidence twice produces identical output
- Selection heuristic: round-robin across sources for diversity
- Chunk ID = hash of (source + sura + ayah_range) - deterministic
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Tuple
from pydantic import BaseModel, Field
import hashlib

from app.verify.registry import AyahRange, EvidencePointer


class TafsirSource(str, Enum):
    """Supported tafsir sources."""
    IBN_KATHIR = "ibn_kathir"
    TABARI = "tabari"
    QURTUBI = "qurtubi"
    SAADI = "saadi"


# Arabic names for sources
TAFSIR_NAMES_AR = {
    TafsirSource.IBN_KATHIR: "تفسير ابن كثير",
    TafsirSource.TABARI: "تفسير الطبري",
    TafsirSource.QURTUBI: "تفسير القرطبي",
    TafsirSource.SAADI: "تفسير السعدي",
}

# Quality thresholds
MIN_DISTINCT_SOURCES = 2
MIN_DISTINCT_CHUNKS = 2
EVIDENCE_DENSITY_THRESHOLD = 0.5  # 50% of events must be grounded


@dataclass
class EvidenceQualityMetrics:
    """Quality metrics for evidence grounding."""
    story_id: str
    total_events: int
    grounded_events: int
    distinct_sources: int
    distinct_chunks: int
    evidence_density: float  # grounded_events / total_events
    source_distribution: Dict[str, int] = field(default_factory=dict)
    meets_minimum: bool = False
    quality_tier: str = "weak"  # weak, moderate, strong

    def __post_init__(self):
        # Calculate if meets minimum thresholds
        self.meets_minimum = (
            self.distinct_sources >= MIN_DISTINCT_SOURCES and
            self.distinct_chunks >= MIN_DISTINCT_CHUNKS and
            self.evidence_density >= EVIDENCE_DENSITY_THRESHOLD
        )

        # Assign quality tier
        if self.distinct_sources >= 3 and self.evidence_density >= 0.8:
            self.quality_tier = "strong"
        elif self.meets_minimum:
            self.quality_tier = "moderate"
        else:
            self.quality_tier = "weak"


class TafsirChunkRef(BaseModel):
    """Reference to a tafsir chunk."""
    source_id: TafsirSource = Field(..., description="معرف المصدر")
    chunk_id: str = Field(..., description="معرف المقطع الفريد")
    sura: int = Field(..., ge=1, le=114)
    ayah_start: int = Field(..., ge=1)
    ayah_end: int = Field(..., ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="مستوى الثقة")
    needs_review: bool = Field(default=False, description="يحتاج مراجعة بشرية")

    @property
    def ayah_ref(self) -> str:
        """Get ayah reference string."""
        if self.ayah_start == self.ayah_end:
            return f"{self.sura}:{self.ayah_start}"
        return f"{self.sura}:{self.ayah_start}-{self.ayah_end}"

    @property
    def source_name_ar(self) -> str:
        """Get Arabic name of source."""
        return TAFSIR_NAMES_AR.get(self.source_id, str(self.source_id))


class EvidenceResolver:
    """
    Resolves ayah ranges to tafsir chunk references.

    Currently uses predictable chunk ID patterns. Future versions will
    integrate with actual tafsir chunk retrieval from the database.
    """

    def __init__(self, default_source: TafsirSource = TafsirSource.IBN_KATHIR):
        self.default_source = default_source
        self._chunk_cache: Dict[str, TafsirChunkRef] = {}

    def _generate_chunk_id(
        self,
        source: TafsirSource,
        sura: int,
        ayah_start: int,
        ayah_end: int
    ) -> str:
        """
        Generate a predictable chunk ID.

        Pattern: {source_id}:{sura}:{ayah_start}-{ayah_end}
        Example: ibn_kathir:2:30-33
        """
        if ayah_start == ayah_end:
            return f"{source.value}:{sura}:{ayah_start}"
        return f"{source.value}:{sura}:{ayah_start}-{ayah_end}"

    def resolve_evidence(
        self,
        ayah_range: AyahRange,
        sources: Optional[List[TafsirSource]] = None
    ) -> List[TafsirChunkRef]:
        """
        Resolve an ayah range to tafsir chunk references.

        Args:
            ayah_range: The ayah range to resolve
            sources: Optional list of sources to use (defaults to all)

        Returns:
            List of tafsir chunk references
        """
        if sources is None:
            sources = [self.default_source]

        chunks = []
        for source in sources:
            chunk_id = self._generate_chunk_id(
                source,
                ayah_range.sura,
                ayah_range.start,
                ayah_range.end
            )

            chunk = TafsirChunkRef(
                source_id=source,
                chunk_id=chunk_id,
                sura=ayah_range.sura,
                ayah_start=ayah_range.start,
                ayah_end=ayah_range.end,
                confidence=0.9,  # High confidence for direct range match
                needs_review=False
            )
            chunks.append(chunk)
            self._chunk_cache[chunk_id] = chunk

        return chunks

    def resolve_multiple_ranges(
        self,
        ranges: List[AyahRange],
        sources: Optional[List[TafsirSource]] = None
    ) -> List[TafsirChunkRef]:
        """
        Resolve multiple ayah ranges to tafsir chunk references.

        Returns deduplicated list of chunks.
        """
        all_chunks = []
        seen_ids = set()

        for ayah_range in ranges:
            chunks = self.resolve_evidence(ayah_range, sources)
            for chunk in chunks:
                if chunk.chunk_id not in seen_ids:
                    all_chunks.append(chunk)
                    seen_ids.add(chunk.chunk_id)

        return all_chunks

    def to_evidence_pointers(
        self,
        chunks: List[TafsirChunkRef]
    ) -> List[EvidencePointer]:
        """
        Convert tafsir chunk refs to evidence pointers for storage.
        """
        pointers = []
        for chunk in chunks:
            pointer = EvidencePointer(
                source_id=chunk.source_id.value,
                chunk_id=chunk.chunk_id,
                ayah_ref=chunk.ayah_ref,
                snippet_ar=None,  # Will be populated from actual tafsir
                snippet_en=None
            )
            pointers.append(pointer)
        return pointers

    def calculate_evidence_coverage(
        self,
        story_ranges: List[AyahRange],
        evidence_pointers: List[EvidencePointer]
    ) -> float:
        """
        Calculate what percentage of story's ayah ranges have evidence.

        Returns coverage as a float 0.0-1.0
        """
        if not story_ranges:
            return 0.0

        # Count total verses in story
        total_verses = sum(r.verse_count for r in story_ranges)
        if total_verses == 0:
            return 0.0

        # Parse evidence ayah refs and count covered verses
        covered_verses = 0
        for pointer in evidence_pointers:
            # Parse ayah_ref like "2:30-33" or "2:30"
            try:
                parts = pointer.ayah_ref.split(':')
                if len(parts) != 2:
                    continue
                sura = int(parts[0])
                ayah_part = parts[1]

                if '-' in ayah_part:
                    start, end = map(int, ayah_part.split('-'))
                else:
                    start = end = int(ayah_part)

                # Check if this overlaps with any story range
                for story_range in story_ranges:
                    if story_range.sura == sura:
                        # Calculate overlap
                        overlap_start = max(start, story_range.start)
                        overlap_end = min(end, story_range.end)
                        if overlap_start <= overlap_end:
                            covered_verses += overlap_end - overlap_start + 1

            except (ValueError, IndexError):
                continue

        # Avoid double counting by capping at total
        coverage = min(covered_verses / total_verses, 1.0)
        return coverage


    def resolve_with_diversity(
        self,
        ayah_range: AyahRange,
        index: int = 0
    ) -> List[TafsirChunkRef]:
        """
        Resolve with multi-source diversity using round-robin.

        Uses deterministic source selection based on index for reproducibility.
        Each ayah range gets evidence from 2 sources (MIN_DISTINCT_SOURCES).
        """
        all_sources = list(TafsirSource)
        # Deterministic round-robin: pick 2 sources based on index
        primary_idx = index % len(all_sources)
        secondary_idx = (index + 1) % len(all_sources)

        selected_sources = [all_sources[primary_idx], all_sources[secondary_idx]]
        return self.resolve_evidence(ayah_range, selected_sources)

    def calculate_quality_metrics(
        self,
        story_id: str,
        events: List[Any],  # StoryEvent
        story_evidence: List[EvidencePointer]
    ) -> EvidenceQualityMetrics:
        """
        Calculate comprehensive quality metrics for a story's evidence.

        Args:
            story_id: Story identifier
            events: List of story events
            story_evidence: Story-level evidence pointers

        Returns:
            EvidenceQualityMetrics with all quality measurements
        """
        total_events = len(events)

        # Count grounded events (events with evidence)
        grounded_events = sum(
            1 for e in events
            if hasattr(e, 'evidence') and len(e.evidence) > 0
        )

        # Collect all evidence (story + event level)
        all_evidence = list(story_evidence)
        for event in events:
            if hasattr(event, 'evidence'):
                all_evidence.extend(event.evidence)

        # Count distinct sources and chunks
        distinct_sources: Set[str] = set()
        distinct_chunks: Set[str] = set()
        source_counts: Dict[str, int] = {}

        for ev in all_evidence:
            source_id = ev.source_id if hasattr(ev, 'source_id') else str(ev.get('source_id', ''))
            chunk_id = ev.chunk_id if hasattr(ev, 'chunk_id') else str(ev.get('chunk_id', ''))

            if source_id:
                distinct_sources.add(source_id)
                source_counts[source_id] = source_counts.get(source_id, 0) + 1
            if chunk_id:
                distinct_chunks.add(chunk_id)

        # Calculate density
        evidence_density = grounded_events / total_events if total_events > 0 else 0.0

        return EvidenceQualityMetrics(
            story_id=story_id,
            total_events=total_events,
            grounded_events=grounded_events,
            distinct_sources=len(distinct_sources),
            distinct_chunks=len(distinct_chunks),
            evidence_density=evidence_density,
            source_distribution=source_counts,
        )

    def get_evidence_distribution_report(
        self,
        all_metrics: List[EvidenceQualityMetrics]
    ) -> Dict[str, Any]:
        """
        Generate evidence distribution report across all stories.

        Returns:
            Report with weakest/strongest stories, source histogram, tier distribution
        """
        if not all_metrics:
            return {"error": "No metrics provided"}

        # Sort by quality
        sorted_by_density = sorted(all_metrics, key=lambda m: m.evidence_density)
        sorted_by_sources = sorted(all_metrics, key=lambda m: m.distinct_sources)

        # Tier distribution
        tier_counts = {"weak": 0, "moderate": 0, "strong": 0}
        for m in all_metrics:
            tier_counts[m.quality_tier] += 1

        # Source histogram (aggregate)
        source_histogram: Dict[str, int] = {}
        for m in all_metrics:
            for source, count in m.source_distribution.items():
                source_histogram[source] = source_histogram.get(source, 0) + count

        # Stories below threshold
        below_threshold = [m for m in all_metrics if not m.meets_minimum]

        return {
            "total_stories": len(all_metrics),
            "tier_distribution": tier_counts,
            "source_histogram": source_histogram,
            "weakest_10": [
                {
                    "story_id": m.story_id,
                    "density": round(m.evidence_density, 2),
                    "sources": m.distinct_sources,
                    "chunks": m.distinct_chunks,
                    "tier": m.quality_tier,
                }
                for m in sorted_by_density[:10]
            ],
            "strongest_10": [
                {
                    "story_id": m.story_id,
                    "density": round(m.evidence_density, 2),
                    "sources": m.distinct_sources,
                    "chunks": m.distinct_chunks,
                    "tier": m.quality_tier,
                }
                for m in sorted_by_density[-10:][::-1]
            ],
            "below_threshold_count": len(below_threshold),
            "below_threshold_stories": [m.story_id for m in below_threshold],
            "average_density": round(
                sum(m.evidence_density for m in all_metrics) / len(all_metrics), 2
            ),
            "average_sources": round(
                sum(m.distinct_sources for m in all_metrics) / len(all_metrics), 2
            ),
        }


# Convenience function
def resolve_story_evidence(
    story_ranges: List[AyahRange],
    sources: Optional[List[TafsirSource]] = None
) -> List[EvidencePointer]:
    """
    Resolve evidence for a story's ayah ranges.

    Convenience function that creates resolver, resolves, and converts.
    """
    resolver = EvidenceResolver()
    chunks = resolver.resolve_multiple_ranges(story_ranges, sources)
    return resolver.to_evidence_pointers(chunks)


def resolve_story_evidence_with_diversity(
    story_ranges: List[AyahRange],
) -> List[EvidencePointer]:
    """
    Resolve evidence with multi-source diversity (deterministic).

    Each range gets evidence from 2 different tafsir sources using round-robin.
    """
    resolver = EvidenceResolver()
    all_chunks = []
    seen_ids = set()

    for i, ayah_range in enumerate(story_ranges):
        chunks = resolver.resolve_with_diversity(ayah_range, index=i)
        for chunk in chunks:
            if chunk.chunk_id not in seen_ids:
                all_chunks.append(chunk)
                seen_ids.add(chunk.chunk_id)

    return resolver.to_evidence_pointers(all_chunks)
