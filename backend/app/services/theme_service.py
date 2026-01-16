"""
Theme Service - CRUD and querying for Quranic themes.

This service provides:
1. Theme listing with filtering (category, search, parent_only)
2. Theme detail retrieval with segments
3. Theme consequences (divine rewards/punishments)
4. Location-based lookups (by sura, by ayah)
5. Related theme discovery

GROUNDING RULES:
================
- All queries respect evidence grounding
- Evidence is required for all theme segments
- Bilingual support (Arabic-first)
"""
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.theme import (
    QuranicTheme, ThemeSegment, ThemeConnection, ThemeConsequence,
    THEME_CATEGORY_TRANSLATIONS, THEME_CATEGORY_ORDER,
    CONSEQUENCE_TYPE_TRANSLATIONS, ThemeCategory,
)


# =============================================================================
# DATA CLASSES FOR RESPONSES
# =============================================================================

@dataclass
class ThemeSummary:
    """Summary view of a theme for listings."""
    id: str
    slug: str
    title_ar: str
    title_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    order_of_importance: int
    key_concepts: List[str]
    segment_count: int
    total_verses: int
    has_consequences: bool
    parent_id: Optional[str] = None
    short_title_ar: Optional[str] = None
    short_title_en: Optional[str] = None


@dataclass
class ThemeDetail:
    """Full detail view of a theme."""
    id: str
    slug: str
    title_ar: str
    title_en: str
    short_title_ar: Optional[str]
    short_title_en: Optional[str]
    category: str
    category_label_ar: str
    category_label_en: str
    order_of_importance: int
    key_concepts: List[str]
    description_ar: Optional[str]
    description_en: Optional[str]
    parent_id: Optional[str]
    related_theme_ids: List[str]
    tafsir_sources: List[str]
    segment_count: int
    total_verses: int
    suras_mentioned: List[int]
    makki_percentage: float
    madani_percentage: float
    is_complete: bool
    children: List[ThemeSummary]


@dataclass
class ThemeSegmentInfo:
    """Segment information for API responses."""
    id: str
    segment_order: int
    chronological_index: Optional[int]
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    title_ar: Optional[str]
    title_en: Optional[str]
    summary_ar: str
    summary_en: str
    semantic_tags: List[str]
    revelation_context: Optional[str]
    is_entry_point: bool
    is_verified: bool
    importance_weight: float
    evidence_count: int
    # Discovery fields
    match_type: Optional[str] = None
    confidence: Optional[float] = None
    reasons_ar: Optional[str] = None
    reasons_en: Optional[str] = None
    is_core: Optional[bool] = None
    discovered_at: Optional[str] = None


@dataclass
class ThemeConsequenceInfo:
    """Consequence information for API responses."""
    id: int
    consequence_type: str
    type_label_ar: str
    type_label_en: str
    description_ar: str
    description_en: str
    supporting_verses: List[Dict[str, Any]]
    evidence_count: int


@dataclass
class ThemeCategoryFacet:
    """Category facet with count."""
    category: str
    label_ar: str
    label_en: str
    theme_count: int
    order: int


@dataclass
class ThemeOccurrence:
    """A theme's occurrence at a specific verse."""
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    segment_id: str
    segment_title_ar: Optional[str]
    segment_title_en: Optional[str]
    summary_ar: str
    summary_en: str


# =============================================================================
# THEME SERVICE
# =============================================================================

class ThemeService:
    """Service for Quranic theme operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # LISTING OPERATIONS
    # =========================================================================

    async def list_themes(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        parent_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ThemeSummary], int]:
        """
        List themes with optional filtering.

        Args:
            category: Filter by theme category
            search: Search in title and key_concepts (Arabic supported)
            parent_only: Only return root themes (no parent)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Tuple of (theme_summaries, total_count)
        """
        # Base query
        query = select(QuranicTheme)

        # Filters
        conditions = []

        if category:
            conditions.append(QuranicTheme.category == category)

        if parent_only:
            conditions.append(QuranicTheme.parent_theme_id.is_(None))

        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    QuranicTheme.title_ar.ilike(search_pattern),
                    QuranicTheme.title_en.ilike(search_pattern),
                    QuranicTheme.key_concepts.contains([search]),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Order by category order, then importance
        query = query.order_by(
            # Custom order by category
            func.array_position(
                list(THEME_CATEGORY_ORDER.keys()),
                QuranicTheme.category
            ),
            QuranicTheme.order_of_importance,
            QuranicTheme.title_ar
        )

        # Pagination
        query = query.offset(offset).limit(limit)

        # Execute
        result = await self.session.execute(query)
        themes = result.scalars().all()

        # Check for consequences
        consequence_counts = await self._get_consequence_counts(
            [t.id for t in themes]
        )

        summaries = [
            ThemeSummary(
                id=t.id,
                slug=t.slug,
                title_ar=t.title_ar,
                title_en=t.title_en,
                short_title_ar=t.short_title_ar,
                short_title_en=t.short_title_en,
                category=t.category,
                category_label_ar=t.category_label_ar,
                category_label_en=t.category_label_en,
                order_of_importance=t.order_of_importance or 0,
                key_concepts=t.key_concepts or [],
                segment_count=t.segment_count or 0,
                total_verses=t.total_verses or 0,
                has_consequences=consequence_counts.get(t.id, 0) > 0,
                parent_id=t.parent_theme_id,
            )
            for t in themes
        ]

        return summaries, total

    async def _get_consequence_counts(
        self,
        theme_ids: List[str]
    ) -> Dict[str, int]:
        """Get consequence counts for themes."""
        if not theme_ids:
            return {}

        query = (
            select(
                ThemeConsequence.theme_id,
                func.count(ThemeConsequence.id)
            )
            .where(ThemeConsequence.theme_id.in_(theme_ids))
            .group_by(ThemeConsequence.theme_id)
        )

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result}

    async def get_theme_categories(self) -> List[ThemeCategoryFacet]:
        """Get all theme categories with counts, ordered methodologically."""
        query = (
            select(
                QuranicTheme.category,
                func.count(QuranicTheme.id)
            )
            .group_by(QuranicTheme.category)
        )

        result = await self.session.execute(query)
        counts = {row[0]: row[1] for row in result}

        facets = []
        for category, order in sorted(THEME_CATEGORY_ORDER.items(), key=lambda x: x[1]):
            translations = THEME_CATEGORY_TRANSLATIONS.get(category, {})
            facets.append(ThemeCategoryFacet(
                category=category,
                label_ar=translations.get("ar", category),
                label_en=translations.get("en", category),
                theme_count=counts.get(category, 0),
                order=order,
            ))

        return facets

    # =========================================================================
    # DETAIL OPERATIONS
    # =========================================================================

    async def get_theme(self, theme_id: str) -> Optional[ThemeDetail]:
        """Get full theme detail with children."""
        query = (
            select(QuranicTheme)
            .where(QuranicTheme.id == theme_id)
            .options(selectinload(QuranicTheme.children))
        )

        result = await self.session.execute(query)
        theme = result.scalar_one_or_none()

        if not theme:
            return None

        # Get children summaries
        children_summaries = []
        if theme.children:
            consequence_counts = await self._get_consequence_counts(
                [c.id for c in theme.children]
            )
            children_summaries = [
                ThemeSummary(
                    id=c.id,
                    slug=c.slug,
                    title_ar=c.title_ar,
                    title_en=c.title_en,
                    category=c.category,
                    category_label_ar=c.category_label_ar,
                    category_label_en=c.category_label_en,
                    order_of_importance=c.order_of_importance or 0,
                    key_concepts=c.key_concepts or [],
                    segment_count=c.segment_count or 0,
                    total_verses=c.total_verses or 0,
                    has_consequences=consequence_counts.get(c.id, 0) > 0,
                    parent_id=c.parent_theme_id,
                )
                for c in sorted(theme.children, key=lambda x: x.order_of_importance or 0)
            ]

        return ThemeDetail(
            id=theme.id,
            slug=theme.slug,
            title_ar=theme.title_ar,
            title_en=theme.title_en,
            short_title_ar=theme.short_title_ar,
            short_title_en=theme.short_title_en,
            category=theme.category,
            category_label_ar=theme.category_label_ar,
            category_label_en=theme.category_label_en,
            order_of_importance=theme.order_of_importance or 0,
            key_concepts=theme.key_concepts or [],
            description_ar=theme.description_ar,
            description_en=theme.description_en,
            parent_id=theme.parent_theme_id,
            related_theme_ids=theme.related_theme_ids or [],
            tafsir_sources=theme.tafsir_sources or [],
            segment_count=theme.segment_count or 0,
            total_verses=theme.total_verses or 0,
            suras_mentioned=theme.suras_mentioned or [],
            makki_percentage=theme.makki_percentage or 0,
            madani_percentage=theme.madani_percentage or 0,
            is_complete=theme.is_complete or False,
            children=children_summaries,
        )

    async def get_theme_segments(
        self,
        theme_id: str,
        verified_only: bool = False,
        match_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        is_core: Optional[bool] = None,
        sura_no: Optional[int] = None,
        source: Optional[str] = None,
        sort: str = "segment_order",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ThemeSegmentInfo], int]:
        """
        Get segments for a theme with optional filters and sorting.

        Args:
            theme_id: Theme ID
            verified_only: Only verified segments
            match_type: Filter by match type (lexical, root, semantic, mixed, manual)
            min_confidence: Minimum confidence threshold
            is_core: Filter by core (True) vs supporting (False)
            sura_no: Filter by surah number
            source: Filter by tafsir source (e.g., 'ibn_kathir_ar')
            sort: Sort order - one of:
                - segment_order (default)
                - confidence_desc
                - confidence_asc
                - sura_asc
                - sura_desc
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Tuple of (segments, total_count)
        """
        # Base query
        query = (
            select(ThemeSegment)
            .where(ThemeSegment.theme_id == theme_id)
        )

        if verified_only:
            query = query.where(ThemeSegment.is_verified == True)

        if match_type:
            query = query.where(ThemeSegment.match_type == match_type)

        if min_confidence is not None:
            query = query.where(ThemeSegment.confidence >= min_confidence)

        if is_core is not None:
            query = query.where(ThemeSegment.is_core == is_core)

        if sura_no is not None:
            query = query.where(ThemeSegment.sura_no == sura_no)

        if source:
            # Filter by tafsir source in evidence_sources JSONB array
            query = query.where(
                ThemeSegment.evidence_sources.contains([{"source_id": source}])
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Apply sorting with stable secondary sort
        sort_options = {
            "segment_order": [ThemeSegment.segment_order, ThemeSegment.id],
            "confidence_desc": [ThemeSegment.confidence.desc().nullslast(), ThemeSegment.segment_order, ThemeSegment.id],
            "confidence_asc": [ThemeSegment.confidence.asc().nullsfirst(), ThemeSegment.segment_order, ThemeSegment.id],
            "sura_asc": [ThemeSegment.sura_no, ThemeSegment.ayah_start, ThemeSegment.id],
            "sura_desc": [ThemeSegment.sura_no.desc(), ThemeSegment.ayah_start.desc(), ThemeSegment.id],
        }
        sort_columns = sort_options.get(sort, sort_options["segment_order"])
        query = query.order_by(*sort_columns)

        # Paginate
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        return [
            ThemeSegmentInfo(
                id=s.id,
                segment_order=s.segment_order,
                chronological_index=getattr(s, 'chronological_index', None),
                sura_no=s.sura_no,
                ayah_start=s.ayah_start,
                ayah_end=s.ayah_end,
                verse_reference=getattr(s, 'verse_reference', f"{s.sura_no}:{s.ayah_start}-{s.ayah_end}"),
                title_ar=s.title_ar,
                title_en=s.title_en,
                summary_ar=s.summary_ar,
                summary_en=s.summary_en,
                semantic_tags=getattr(s, 'semantic_tags', []) or [],
                revelation_context=getattr(s, 'revelation_context', None),
                is_entry_point=getattr(s, 'is_entry_point', False) or False,
                is_verified=getattr(s, 'is_verified', False) or False,
                importance_weight=getattr(s, 'importance_weight', 0.5) or 0.5,
                evidence_count=getattr(s, 'evidence_count', 0) or 0,
                # Discovery fields
                match_type=getattr(s, 'match_type', None),
                confidence=getattr(s, 'confidence', None),
                reasons_ar=getattr(s, 'reasons_ar', None),
                reasons_en=getattr(s, 'reasons_en', None),
                is_core=getattr(s, 'is_core', None),
                discovered_at=str(s.discovered_at) if getattr(s, 'discovered_at', None) else None,
            )
            for s in segments
        ], total

    async def get_theme_consequences(
        self,
        theme_id: str,
        consequence_type: Optional[str] = None,
    ) -> List[ThemeConsequenceInfo]:
        """Get divine consequences for a theme."""
        query = (
            select(ThemeConsequence)
            .where(ThemeConsequence.theme_id == theme_id)
        )

        if consequence_type:
            query = query.where(ThemeConsequence.consequence_type == consequence_type)

        query = query.order_by(ThemeConsequence.display_order)

        result = await self.session.execute(query)
        consequences = result.scalars().all()

        return [
            ThemeConsequenceInfo(
                id=c.id,
                consequence_type=c.consequence_type,
                type_label_ar=c.type_label_ar,
                type_label_en=c.type_label_en,
                description_ar=c.description_ar,
                description_en=c.description_en,
                supporting_verses=c.supporting_verses or [],
                evidence_count=c.evidence_count,
            )
            for c in consequences
        ]

    # =========================================================================
    # RELATED THEMES
    # =========================================================================

    async def get_related_themes(self, theme_id: str) -> List[ThemeSummary]:
        """Get themes related to this one."""
        # First get the theme to find related IDs
        theme_query = select(QuranicTheme).where(QuranicTheme.id == theme_id)
        result = await self.session.execute(theme_query)
        theme = result.scalar_one_or_none()

        if not theme or not theme.related_theme_ids:
            return []

        # Get the related themes
        query = (
            select(QuranicTheme)
            .where(QuranicTheme.id.in_(theme.related_theme_ids))
        )

        result = await self.session.execute(query)
        related_themes = result.scalars().all()

        consequence_counts = await self._get_consequence_counts(
            [t.id for t in related_themes]
        )

        return [
            ThemeSummary(
                id=t.id,
                slug=t.slug,
                title_ar=t.title_ar,
                title_en=t.title_en,
                category=t.category,
                category_label_ar=t.category_label_ar,
                category_label_en=t.category_label_en,
                order_of_importance=t.order_of_importance or 0,
                key_concepts=t.key_concepts or [],
                segment_count=t.segment_count or 0,
                total_verses=t.total_verses or 0,
                has_consequences=consequence_counts.get(t.id, 0) > 0,
                parent_id=t.parent_theme_id,
            )
            for t in related_themes
        ]

    async def get_child_themes(self, theme_id: str) -> List[ThemeSummary]:
        """Get child themes (subthemes)."""
        query = (
            select(QuranicTheme)
            .where(QuranicTheme.parent_theme_id == theme_id)
            .order_by(QuranicTheme.order_of_importance)
        )

        result = await self.session.execute(query)
        children = result.scalars().all()

        consequence_counts = await self._get_consequence_counts(
            [c.id for c in children]
        )

        return [
            ThemeSummary(
                id=c.id,
                slug=c.slug,
                title_ar=c.title_ar,
                title_en=c.title_en,
                category=c.category,
                category_label_ar=c.category_label_ar,
                category_label_en=c.category_label_en,
                order_of_importance=c.order_of_importance or 0,
                key_concepts=c.key_concepts or [],
                segment_count=c.segment_count or 0,
                total_verses=c.total_verses or 0,
                has_consequences=consequence_counts.get(c.id, 0) > 0,
                parent_id=c.parent_theme_id,
            )
            for c in children
        ]

    # =========================================================================
    # LOCATION-BASED LOOKUPS
    # =========================================================================

    async def get_themes_by_sura(self, sura_no: int) -> List[ThemeSummary]:
        """Get all themes that appear in a specific surah."""
        # Find themes that have segments in this sura
        subquery = (
            select(ThemeSegment.theme_id)
            .where(ThemeSegment.sura_no == sura_no)
            .distinct()
        )

        query = (
            select(QuranicTheme)
            .where(QuranicTheme.id.in_(subquery))
            .order_by(QuranicTheme.order_of_importance)
        )

        result = await self.session.execute(query)
        themes = result.scalars().all()

        consequence_counts = await self._get_consequence_counts(
            [t.id for t in themes]
        )

        return [
            ThemeSummary(
                id=t.id,
                slug=t.slug,
                title_ar=t.title_ar,
                title_en=t.title_en,
                category=t.category,
                category_label_ar=t.category_label_ar,
                category_label_en=t.category_label_en,
                order_of_importance=t.order_of_importance or 0,
                key_concepts=t.key_concepts or [],
                segment_count=t.segment_count or 0,
                total_verses=t.total_verses or 0,
                has_consequences=consequence_counts.get(t.id, 0) > 0,
                parent_id=t.parent_theme_id,
            )
            for t in themes
        ]

    async def get_themes_by_ayah(
        self,
        sura_no: int,
        ayah_no: int
    ) -> List[ThemeOccurrence]:
        """Get themes that cover a specific ayah."""
        query = (
            select(ThemeSegment, QuranicTheme)
            .join(QuranicTheme, ThemeSegment.theme_id == QuranicTheme.id)
            .where(
                and_(
                    ThemeSegment.sura_no == sura_no,
                    ThemeSegment.ayah_start <= ayah_no,
                    ThemeSegment.ayah_end >= ayah_no,
                )
            )
            .order_by(QuranicTheme.order_of_importance)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            ThemeOccurrence(
                theme_id=theme.id,
                theme_title_ar=theme.title_ar,
                theme_title_en=theme.title_en,
                segment_id=segment.id,
                segment_title_ar=segment.title_ar,
                segment_title_en=segment.title_en,
                summary_ar=segment.summary_ar,
                summary_en=segment.summary_en,
            )
            for segment, theme in rows
        ]

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_theme_stats(self) -> Dict[str, Any]:
        """Get overall statistics for themes."""
        # Total themes
        total_themes = (
            await self.session.execute(
                select(func.count(QuranicTheme.id))
            )
        ).scalar() or 0

        # Total segments
        total_segments = (
            await self.session.execute(
                select(func.count(ThemeSegment.id))
            )
        ).scalar() or 0

        # Verified segments
        verified_segments = (
            await self.session.execute(
                select(func.count(ThemeSegment.id))
                .where(ThemeSegment.is_verified == True)
            )
        ).scalar() or 0

        # By category
        category_counts = await self.get_theme_categories()

        return {
            "total_themes": total_themes,
            "total_segments": total_segments,
            "verified_segments": verified_segments,
            "verification_rate": (
                verified_segments / total_segments * 100
                if total_segments > 0 else 0
            ),
            "by_category": [
                {
                    "category": c.category,
                    "label_ar": c.label_ar,
                    "label_en": c.label_en,
                    "count": c.theme_count,
                }
                for c in category_counts
            ],
        }

    # =========================================================================
    # COVERAGE AND EVIDENCE
    # =========================================================================

    async def get_theme_coverage(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get coverage statistics for a theme."""
        # Get theme info
        theme_result = await self.session.execute(
            select(QuranicTheme).where(QuranicTheme.id == theme_id)
        )
        theme = theme_result.scalar_one_or_none()
        if not theme:
            return None

        # Get all segments for this theme
        segments_result = await self.session.execute(
            select(ThemeSegment).where(ThemeSegment.theme_id == theme_id)
        )
        segments = segments_result.scalars().all()

        # Calculate statistics
        total_segments = len(segments)
        manual_segments = sum(1 for s in segments if getattr(s, 'match_type', None) in (None, 'manual'))
        discovered_segments = total_segments - manual_segments
        core_segments = sum(1 for s in segments if getattr(s, 'is_core', True))
        supporting_segments = total_segments - core_segments

        # Calculate average confidence
        confidences = [getattr(s, 'confidence', 1.0) or 1.0 for s in segments]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Count by match type
        by_match_type = {}
        for s in segments:
            mt = getattr(s, 'match_type', None) or 'manual'
            by_match_type[mt] = by_match_type.get(mt, 0) + 1

        # Count by confidence band
        by_confidence_band = {'high': 0, 'medium': 0, 'low': 0}
        for s in segments:
            conf = getattr(s, 'confidence', 1.0) or 1.0
            if conf >= 0.8:
                by_confidence_band['high'] += 1
            elif conf >= 0.5:
                by_confidence_band['medium'] += 1
            else:
                by_confidence_band['low'] += 1

        # Get unique verses and tafsir sources
        unique_verses = set()
        tafsir_sources = set()
        for s in segments:
            for aya in range(s.ayah_start, s.ayah_end + 1):
                unique_verses.add((s.sura_no, aya))
            for ev in (s.evidence_sources or []):
                if isinstance(ev, dict) and 'source_id' in ev:
                    tafsir_sources.add(ev['source_id'])

        # Quran coverage percentage (6236 total verses)
        quran_coverage = (len(unique_verses) / 6236) * 100

        return {
            'theme_id': theme_id,
            'title_ar': theme.title_ar,
            'title_en': theme.title_en,
            'total_segments': total_segments,
            'total_verses': len(unique_verses),
            'manual_segments': manual_segments,
            'discovered_segments': discovered_segments,
            'core_segments': core_segments,
            'supporting_segments': supporting_segments,
            'avg_confidence': round(avg_confidence, 3),
            'by_match_type': by_match_type,
            'by_confidence_band': by_confidence_band,
            'tafsir_sources_used': list(tafsir_sources),
            'quran_coverage_percentage': round(quran_coverage, 2),
        }

    async def get_segment_evidence(self, theme_id: str, segment_id: str) -> Optional[Dict[str, Any]]:
        """Get evidence for why a segment belongs to a theme ('Why this verse?')."""
        # Get segment
        segment_result = await self.session.execute(
            select(ThemeSegment).where(
                ThemeSegment.id == segment_id,
                ThemeSegment.theme_id == theme_id,
            )
        )
        segment = segment_result.scalar_one_or_none()
        if not segment:
            return None

        # Get theme info
        theme_result = await self.session.execute(
            select(QuranicTheme).where(QuranicTheme.id == theme_id)
        )
        theme = theme_result.scalar_one_or_none()
        if not theme:
            return None

        # Get verse text
        from sqlalchemy import text as sql_text
        verse_result = await self.session.execute(sql_text("""
            SELECT text_uthmani FROM quran_verses
            WHERE sura_no = :sura_no AND aya_no = :aya_no
        """), {'sura_no': segment.sura_no, 'aya_no': segment.ayah_start})
        verse_row = verse_result.fetchone()
        text_uthmani = verse_row[0] if verse_row else ''

        return {
            'segment_id': segment.id,
            'theme_id': theme_id,
            'theme_title_ar': theme.title_ar,
            'theme_title_en': theme.title_en,
            'sura_no': segment.sura_no,
            'ayah_no': segment.ayah_start,
            'text_uthmani': text_uthmani,
            'match_type': getattr(segment, 'match_type', 'manual') or 'manual',
            'confidence': getattr(segment, 'confidence', 1.0) or 1.0,
            'reasons_ar': getattr(segment, 'reasons_ar', '') or segment.summary_ar,
            'reasons_en': getattr(segment, 'reasons_en', None),
            'is_core': getattr(segment, 'is_core', True) if getattr(segment, 'is_core', None) is not None else True,
            'evidence_sources': segment.evidence_sources or [],
            'matching_keywords': [],  # Would need to parse from reasons_ar
        }
