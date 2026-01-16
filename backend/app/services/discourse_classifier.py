"""
Discourse Classifier Service - Quranic Discourse Segmentation

This service provides:
1. Classification of verse ranges by discourse type (narrative, legal, exhortation, etc.)
2. Linking discourse segments to stories for narrative passages
3. Sub-type classification for granular analysis
4. Evidence-grounded discourse tagging

DISCOURSE TYPES:
===============
- NARRATIVE (قصصي): Story narration (prophets, nations, events)
- EXHORTATION (وعظي): Moral guidance and admonition
- LEGAL_RULING (تشريعي): Jurisprudential verses (ahkam)
- SUPPLICATION (دعائي): Prayers and invocations
- PROMISE (وعد): Divine promises to believers
- WARNING (وعيد): Warnings to disbelievers
- PARABLE (مثلي): Parables and similitudes
- ARGUMENTATION (حجاجي): Logical arguments and debates
- DESCRIPTION (وصفي): Descriptions (paradise, hell, creation)
- DIALOGUE (حواري): Conversations and dialogues
- PRAISE (تحميدي): Praise of Allah
- OATH (قسمي): Divine oaths
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rhetoric import (
    DiscourseSegment,
    DiscourseType,
    DISCOURSE_TYPE_TRANSLATIONS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ARABIC PATTERN MARKERS FOR DISCOURSE DETECTION
# =============================================================================

# Narrative markers
NARRATIVE_MARKERS = [
    "إِذْ",              # idh - when (narrative opening)
    "وَإِذْ",            # wa-idh - and when
    "وَاذْكُرْ",          # wadhkur - and mention
    "نَبَأَ",            # naba' - story/news
    "قِصَّة",           # qissa - story
    "وَلَقَدْ",          # wa-laqad - and indeed (narrative emphasis)
    "أَلَمْ تَرَ",        # alam tara - have you not seen
    "أَوَلَمْ",          # awa-lam - have they not
]

# Legal/ruling markers
LEGAL_MARKERS = [
    "حُرِّمَتْ",         # hurrimat - forbidden
    "أُحِلَّ",           # uhilla - permitted
    "كُتِبَ عَلَيْكُمْ",   # kutiba alaykum - prescribed upon you
    "فُرِضَ",           # furida - obligated
    "يَا أَيُّهَا الَّذِينَ آمَنُوا",  # ya ayyuha alladhina amanu (often precedes rulings)
    "حَلَالٌ",           # halal - permissible
    "حَرَامٌ",           # haram - forbidden
]

# Supplication markers
SUPPLICATION_MARKERS = [
    "رَبَّنَا",          # rabbana - Our Lord
    "رَبِّ",            # rabbi - My Lord
    "اللَّهُمَّ",        # allahumma - O Allah
    "دَعَا",            # da'a - called/invoked
    "سُبْحَانَ",         # subhan - Glory to
    "الْحَمْدُ لِلَّهِ",   # alhamdulillah - praise to Allah
]

# Warning markers
WARNING_MARKERS = [
    "وَيْلٌ",           # wayl - woe
    "إِنَّ جَهَنَّمَ",     # inna jahannam - indeed Hell
    "عَذَابٌ",          # adhab - punishment
    "يَوْمَ الْقِيَامَةِ",  # yawm al-qiyamah - Day of Resurrection
    "النَّارِ",          # al-nar - the Fire
    "سَوْفَ",           # sawfa - will (future warning)
]

# Promise markers
PROMISE_MARKERS = [
    "جَنَّات",          # jannat - gardens
    "الْجَنَّةَ",        # al-jannah - Paradise
    "وَعَدَ اللَّهُ",     # wa'ada Allah - Allah promised
    "بُشْرَى",          # bushra - glad tidings
    "فَلَهُمْ أَجْرُهُمْ",  # falahum ajruhum - for them is their reward
]

# Oath markers
OATH_MARKERS = [
    "وَالْ",            # wal- (oath by)
    "وَالشَّمْسِ",       # wa-al-shams - by the sun
    "وَاللَّيْلِ",       # wa-al-layl - by the night
    "وَالْفَجْرِ",       # wa-al-fajr - by the dawn
    "وَالضُّحَى",        # wa-al-duha - by the morning
    "لَا أُقْسِمُ",      # la uqsimu - I swear
]

# Praise/glorification markers
PRAISE_MARKERS = [
    "الْحَمْدُ لِلَّهِ",   # alhamdulillah
    "تَبَارَكَ",         # tabaraka - blessed is
    "سَبَّحَ",          # sabbaha - glorified
    "يُسَبِّحُ",         # yusabbihu - glorifies
    "سُبْحَانَ الَّذِي",  # subhan alladhi - glory to He who
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DiscourseSegmentSummary:
    """Summary of a discourse segment."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    discourse_type: str
    type_label_ar: str
    type_label_en: str
    sub_type: Optional[str]
    title_ar: Optional[str]
    title_en: Optional[str]
    linked_story_id: Optional[str]
    is_verified: bool


@dataclass
class DiscourseSegmentDetail:
    """Full detail of a discourse segment."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    discourse_type: str
    type_label_ar: str
    type_label_en: str
    sub_type: Optional[str]
    title_ar: Optional[str]
    title_en: Optional[str]
    summary_ar: Optional[str]
    summary_en: Optional[str]
    linked_story_id: Optional[str]
    linked_segment_ids: Optional[List[str]]
    evidence_count: int
    confidence: float
    source: Optional[str]
    is_verified: bool


@dataclass
class DiscourseTypeFacet:
    """Discourse type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


@dataclass
class DiscourseDetection:
    """Result of discourse type detection."""
    discourse_type: str
    type_label_ar: str
    type_label_en: str
    matched_markers: List[str]
    confidence: float
    evidence_needed: bool = True


@dataclass
class SurahDiscourseProfile:
    """Discourse profile for a surah."""
    sura_no: int
    total_segments: int
    type_distribution: Dict[str, int]
    dominant_type: str
    narrative_segments: int
    has_legal_rulings: bool
    has_stories: bool


# =============================================================================
# DISCOURSE CLASSIFIER SERVICE
# =============================================================================

class DiscourseClassifier:
    """
    Service for Quranic discourse segmentation and classification.

    Classifies verse ranges by their communicative function and
    links narrative passages to story entities.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------------------------------
    # SEGMENT OPERATIONS
    # -------------------------------------------------------------------------

    async def list_segments(
        self,
        discourse_type: Optional[str] = None,
        sura_no: Optional[int] = None,
        linked_story_id: Optional[str] = None,
        verified_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[DiscourseSegmentSummary], int]:
        """
        List discourse segments with optional filtering.

        Args:
            discourse_type: Filter by discourse type
            sura_no: Filter by surah number
            linked_story_id: Filter by linked story
            verified_only: Only return verified segments
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (segments, total_count)
        """
        logger.debug(
            "list_segments called",
            extra={"type": discourse_type, "sura": sura_no}
        )

        query = select(DiscourseSegment)

        if discourse_type:
            query = query.where(DiscourseSegment.discourse_type == discourse_type)

        if sura_no:
            query = query.where(DiscourseSegment.sura_no == sura_no)

        if linked_story_id:
            query = query.where(DiscourseSegment.linked_story_id == linked_story_id)

        if verified_only:
            query = query.where(DiscourseSegment.is_verified == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(
            DiscourseSegment.sura_no,
            DiscourseSegment.ayah_start
        )
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        summaries = []
        for seg in segments:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get(seg.discourse_type, {})
            summaries.append(DiscourseSegmentSummary(
                id=seg.id,
                sura_no=seg.sura_no,
                ayah_start=seg.ayah_start,
                ayah_end=seg.ayah_end,
                verse_reference=seg.verse_reference,
                discourse_type=seg.discourse_type,
                type_label_ar=trans.get("ar", seg.discourse_type),
                type_label_en=trans.get("en", seg.discourse_type),
                sub_type=seg.sub_type,
                title_ar=seg.title_ar,
                title_en=seg.title_en,
                linked_story_id=seg.linked_story_id,
                is_verified=seg.is_verified,
            ))

        return summaries, total_count

    async def get_segment(self, segment_id: int) -> Optional[DiscourseSegmentDetail]:
        """Get full details of a discourse segment."""
        result = await self.session.execute(
            select(DiscourseSegment).where(DiscourseSegment.id == segment_id)
        )
        seg = result.scalar_one_or_none()

        if not seg:
            return None

        trans = DISCOURSE_TYPE_TRANSLATIONS.get(seg.discourse_type, {})

        return DiscourseSegmentDetail(
            id=seg.id,
            sura_no=seg.sura_no,
            ayah_start=seg.ayah_start,
            ayah_end=seg.ayah_end,
            verse_reference=seg.verse_reference,
            discourse_type=seg.discourse_type,
            type_label_ar=trans.get("ar", seg.discourse_type),
            type_label_en=trans.get("en", seg.discourse_type),
            sub_type=seg.sub_type,
            title_ar=seg.title_ar,
            title_en=seg.title_en,
            summary_ar=seg.summary_ar,
            summary_en=seg.summary_en,
            linked_story_id=seg.linked_story_id,
            linked_segment_ids=seg.linked_segment_ids,
            evidence_count=len(seg.evidence_chunk_ids) if seg.evidence_chunk_ids else 0,
            confidence=seg.confidence or 1.0,
            source=seg.source,
            is_verified=seg.is_verified,
        )

    async def get_segments_by_verse(
        self,
        sura_no: int,
        ayah_no: int,
    ) -> List[DiscourseSegmentSummary]:
        """Get discourse segments containing a specific verse."""
        query = (
            select(DiscourseSegment)
            .where(
                and_(
                    DiscourseSegment.sura_no == sura_no,
                    DiscourseSegment.ayah_start <= ayah_no,
                    DiscourseSegment.ayah_end >= ayah_no,
                )
            )
            .order_by(DiscourseSegment.ayah_start)
        )

        result = await self.session.execute(query)
        segments = result.scalars().all()

        summaries = []
        for seg in segments:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get(seg.discourse_type, {})
            summaries.append(DiscourseSegmentSummary(
                id=seg.id,
                sura_no=seg.sura_no,
                ayah_start=seg.ayah_start,
                ayah_end=seg.ayah_end,
                verse_reference=seg.verse_reference,
                discourse_type=seg.discourse_type,
                type_label_ar=trans.get("ar", seg.discourse_type),
                type_label_en=trans.get("en", seg.discourse_type),
                sub_type=seg.sub_type,
                title_ar=seg.title_ar,
                title_en=seg.title_en,
                linked_story_id=seg.linked_story_id,
                is_verified=seg.is_verified,
            ))

        return summaries

    async def get_discourse_types(self) -> List[DiscourseTypeFacet]:
        """Get available discourse types with counts."""
        query = (
            select(
                DiscourseSegment.discourse_type,
                func.count(DiscourseSegment.id).label("count")
            )
            .group_by(DiscourseSegment.discourse_type)
            .order_by(func.count(DiscourseSegment.id).desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        facets = []
        for row in rows:
            dtype = row[0]
            count = row[1]
            trans = DISCOURSE_TYPE_TRANSLATIONS.get(dtype, {})
            facets.append(DiscourseTypeFacet(
                type=dtype,
                label_ar=trans.get("ar", dtype),
                label_en=trans.get("en", dtype),
                count=count,
            ))

        return facets

    # -------------------------------------------------------------------------
    # SURAH ANALYSIS
    # -------------------------------------------------------------------------

    async def get_surah_discourse_profile(
        self,
        sura_no: int,
    ) -> SurahDiscourseProfile:
        """
        Get the discourse profile for a surah.

        Returns:
            Profile with type distribution and dominant discourse type
        """
        segments, _ = await self.list_segments(sura_no=sura_no, limit=500)

        type_distribution: Dict[str, int] = {}
        for seg in segments:
            dtype = seg.discourse_type
            type_distribution[dtype] = type_distribution.get(dtype, 0) + 1

        # Determine dominant type
        dominant_type = max(type_distribution, key=type_distribution.get) if type_distribution else "unknown"

        # Count narrative segments
        narrative_count = type_distribution.get(DiscourseType.NARRATIVE.value, 0)

        # Check for legal rulings
        has_legal = type_distribution.get(DiscourseType.LEGAL_RULING.value, 0) > 0

        # Check for stories (narrative with linked story)
        has_stories = any(seg.linked_story_id for seg in segments)

        return SurahDiscourseProfile(
            sura_no=sura_no,
            total_segments=len(segments),
            type_distribution=type_distribution,
            dominant_type=dominant_type,
            narrative_segments=narrative_count,
            has_legal_rulings=has_legal,
            has_stories=has_stories,
        )

    async def get_segments_by_story(
        self,
        story_id: str,
    ) -> List[DiscourseSegmentSummary]:
        """Get all discourse segments linked to a specific story."""
        segments, _ = await self.list_segments(linked_story_id=story_id, limit=100)
        return segments

    # -------------------------------------------------------------------------
    # PATTERN-BASED DETECTION (FOR ANALYSIS)
    # -------------------------------------------------------------------------

    def detect_discourse_type(
        self,
        text_ar: str,
        context_markers: Optional[List[str]] = None,
    ) -> List[DiscourseDetection]:
        """
        Detect potential discourse types in Arabic text using pattern matching.

        NOTE: This is for analysis assistance only. Results must be validated
        against tafsir sources before creating actual segments.

        Args:
            text_ar: Arabic text to analyze
            context_markers: Additional context from surrounding verses

        Returns:
            List of potential discourse type detections
        """
        detections: List[DiscourseDetection] = []

        # Check for narrative markers
        narrative_matches = [m for m in NARRATIVE_MARKERS if m in text_ar]
        if narrative_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("narrative", {})
            detections.append(DiscourseDetection(
                discourse_type="narrative",
                type_label_ar=trans.get("ar", "قصصي"),
                type_label_en=trans.get("en", "Narrative"),
                matched_markers=narrative_matches,
                confidence=0.7,
            ))

        # Check for legal markers
        legal_matches = [m for m in LEGAL_MARKERS if m in text_ar]
        if legal_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("legal_ruling", {})
            detections.append(DiscourseDetection(
                discourse_type="legal_ruling",
                type_label_ar=trans.get("ar", "تشريعي"),
                type_label_en=trans.get("en", "Legal Ruling"),
                matched_markers=legal_matches,
                confidence=0.8,
            ))

        # Check for supplication markers
        supplication_matches = [m for m in SUPPLICATION_MARKERS if m in text_ar]
        if supplication_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("supplication", {})
            detections.append(DiscourseDetection(
                discourse_type="supplication",
                type_label_ar=trans.get("ar", "دعائي"),
                type_label_en=trans.get("en", "Supplication"),
                matched_markers=supplication_matches,
                confidence=0.8,
            ))

        # Check for warning markers
        warning_matches = [m for m in WARNING_MARKERS if m in text_ar]
        if warning_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("warning", {})
            detections.append(DiscourseDetection(
                discourse_type="warning",
                type_label_ar=trans.get("ar", "وعيد"),
                type_label_en=trans.get("en", "Warning"),
                matched_markers=warning_matches,
                confidence=0.7,
            ))

        # Check for promise markers
        promise_matches = [m for m in PROMISE_MARKERS if m in text_ar]
        if promise_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("promise", {})
            detections.append(DiscourseDetection(
                discourse_type="promise",
                type_label_ar=trans.get("ar", "وعد"),
                type_label_en=trans.get("en", "Promise"),
                matched_markers=promise_matches,
                confidence=0.7,
            ))

        # Check for oath markers (typically at surah openings)
        oath_matches = [m for m in OATH_MARKERS if text_ar.startswith(m) or f"\n{m}" in text_ar]
        if oath_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("oath", {})
            detections.append(DiscourseDetection(
                discourse_type="oath",
                type_label_ar=trans.get("ar", "قسمي"),
                type_label_en=trans.get("en", "Oath"),
                matched_markers=oath_matches,
                confidence=0.9,
            ))

        # Check for praise markers
        praise_matches = [m for m in PRAISE_MARKERS if m in text_ar]
        if praise_matches:
            trans = DISCOURSE_TYPE_TRANSLATIONS.get("praise", {})
            detections.append(DiscourseDetection(
                discourse_type="praise",
                type_label_ar=trans.get("ar", "تحميدي"),
                type_label_en=trans.get("en", "Praise"),
                matched_markers=praise_matches,
                confidence=0.8,
            ))

        # Sort by confidence
        detections.sort(key=lambda d: d.confidence, reverse=True)

        return detections

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall discourse classification statistics."""
        # Total segments
        total_result = await self.session.execute(
            select(func.count(DiscourseSegment.id))
        )
        total_segments = total_result.scalar() or 0

        # Verified segments
        verified_result = await self.session.execute(
            select(func.count(DiscourseSegment.id))
            .where(DiscourseSegment.is_verified == True)
        )
        verified_segments = verified_result.scalar() or 0

        # With story links
        story_linked_result = await self.session.execute(
            select(func.count(DiscourseSegment.id))
            .where(DiscourseSegment.linked_story_id.isnot(None))
        )
        story_linked = story_linked_result.scalar() or 0

        # Unique surahs covered
        surahs_result = await self.session.execute(
            select(func.count(func.distinct(DiscourseSegment.sura_no)))
        )
        surahs_covered = surahs_result.scalar() or 0

        # By type
        types = await self.get_discourse_types()
        by_type = {t.type: t.count for t in types}

        return {
            "total_segments": total_segments,
            "verified_segments": verified_segments,
            "verification_rate": round(verified_segments / total_segments, 2) if total_segments > 0 else 0,
            "story_linked_segments": story_linked,
            "surahs_covered": surahs_covered,
            "by_type": by_type,
        }

    # -------------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------------

    def _calculate_verse_count(self, ayah_start: int, ayah_end: int) -> int:
        """Calculate number of verses in a segment."""
        return ayah_end - ayah_start + 1
