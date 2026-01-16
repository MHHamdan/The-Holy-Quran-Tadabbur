"""
Rhetorical Analyzer Service - Arabic Rhetoric (علم البلاغة) Detection

This service provides:
1. Detection of rhetorical devices in Quranic verses
2. Extraction of rhetoric mentions from balagha-focused tafsirs
3. Pattern-based device identification with Arabic markers
4. Evidence grounding from tafsir chunks

EPISTEMIC GROUNDING:
====================
All rhetorical device detections MUST be grounded in tafsir evidence.
Priority sources (balagha-focused):
- Al-Zamakhshari (الكشاف) - Primary for balagha
- Al-Razi (التفسير الكبير) - Philosophical + rhetorical
- Abu Su'ud (إرشاد العقل السليم) - Ottoman rhetorical tradition
- Ibn Ashur (التحرير والتنوير) - Modern linguistic analysis
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rhetoric import (
    RhetoricalDeviceType,
    RhetoricalOccurrence,
    BalaghaCategory,
    RhetoricalDeviceKey,
    BALAGHA_CATEGORY_TRANSLATIONS,
    RHETORICAL_DEVICE_TRANSLATIONS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ARABIC PATTERN MARKERS FOR DEVICE DETECTION
# =============================================================================

# Simile markers (أدوات التشبيه)
TASHBIH_MARKERS = [
    "كَ",           # ka - like
    "مِثْل",        # mithl - similar to
    "مَثَل",        # mathal - likeness
    "كَأَنَّ",      # ka'anna - as if
    "كَأَنَّمَا",    # ka'annama - as though
    "شِبْه",        # shibh - resembling
    "نَحْو",        # nahw - like/towards
]

# Rhetorical question particles (أدوات الاستفهام)
ISTIFHAM_PARTICLES = [
    "أَ",           # 'a - question
    "هَلْ",         # hal - is/does
    "مَا",          # ma - what
    "مَاذَا",       # madha - what
    "مَنْ",         # man - who
    "أَيّ",         # ayy - which
    "كَيْفَ",       # kayf - how
    "أَيْنَ",       # ayn - where
    "مَتَى",        # mata - when
    "أَنَّى",       # anna - how/from where
    "كَمْ",         # kam - how many
    "لِمَ",         # lima - why
    "لِمَاذَا",     # limadha - why
]

# Vocative particles (أدوات النداء)
NIDA_PARTICLES = [
    "يَا",          # ya - O
    "أَيَّ",        # ayya - O (for middle distance)
    "أَيُّهَا",     # ayyuha - O (formal, masculine)
    "أَيَّتُهَا",    # ayyatuha - O (formal, feminine)
]

# Restriction markers (أدوات القصر)
QASR_MARKERS = [
    "إِنَّمَا",     # innama - only/indeed
    "لَا...إِلَّا",  # la...illa - none except
    "مَا...إِلَّا",  # ma...illa - nothing except
]

# Supplication/prayer markers
SUPPLICATION_MARKERS = [
    "رَبَّنَا",     # rabbana - Our Lord
    "رَبِّ",        # rabbi - My Lord
    "اللَّهُمَّ",   # allahumma - O Allah
]

# Legal ruling markers
LEGAL_MARKERS = [
    "حُرِّمَتْ",    # hurrimat - forbidden
    "أُحِلَّ",      # uhilla - permitted
    "كُتِبَ",       # kutiba - prescribed
    "فُرِضَ",       # furida - obligated
    "حَلَال",       # halal - permissible
    "حَرَام",       # haram - forbidden
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RhetoricalDeviceSummary:
    """Summary of a rhetorical device type."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    occurrence_count: int = 0


@dataclass
class RhetoricalDeviceDetail:
    """Full detail of a rhetorical device type."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    definition_ar: Optional[str]
    definition_en: Optional[str]
    examples: Optional[List[Dict[str, Any]]]
    sub_types: Optional[List[Dict[str, Any]]]
    parent_device_id: Optional[str]
    is_active: bool


@dataclass
class RhetoricalOccurrenceInfo:
    """Information about a rhetorical device occurrence."""
    id: int
    device_type_id: str
    device_name_ar: str
    device_name_en: str
    device_category: str
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    text_snippet_ar: Optional[str]
    explanation_ar: Optional[str]
    explanation_en: Optional[str]
    evidence_count: int
    confidence: float
    source: Optional[str]
    is_verified: bool


@dataclass
class RhetoricalDetection:
    """Result of rhetorical device detection."""
    device_key: str
    device_name_ar: str
    device_name_en: str
    category: str
    matched_text: str
    pattern_type: str  # "marker", "structural", "tafsir_extraction"
    confidence: float
    evidence_needed: bool = True


@dataclass
class CategoryFacet:
    """Balagha category with count."""
    category: str
    label_ar: str
    label_en: str
    count: int


# =============================================================================
# RHETORICAL ANALYZER SERVICE
# =============================================================================

class RhetoricalAnalyzer:
    """
    Service for Arabic rhetoric (علم البلاغة) analysis.

    Provides detection of rhetorical devices, tafsir extraction,
    and evidence-grounded occurrence management.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------------------------------
    # DEVICE TYPE OPERATIONS
    # -------------------------------------------------------------------------

    async def list_device_types(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[RhetoricalDeviceSummary], int]:
        """
        List rhetorical device types with optional filtering.

        Args:
            category: Filter by balagha category (bayaan, maani, badeea)
            search: Search in names and definitions
            include_inactive: Include inactive devices
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (devices, total_count)
        """
        logger.debug(
            "list_device_types called",
            extra={"category": category, "search": search, "limit": limit}
        )

        query = select(RhetoricalDeviceType)

        if category:
            query = query.where(RhetoricalDeviceType.category == category)

        if not include_inactive:
            query = query.where(RhetoricalDeviceType.is_active == True)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    RhetoricalDeviceType.name_ar.ilike(search_pattern),
                    RhetoricalDeviceType.name_en.ilike(search_pattern),
                    RhetoricalDeviceType.slug.ilike(search_pattern),
                    RhetoricalDeviceType.definition_ar.ilike(search_pattern),
                    RhetoricalDeviceType.definition_en.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(
            RhetoricalDeviceType.category,
            RhetoricalDeviceType.display_order,
            RhetoricalDeviceType.name_en
        )
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        devices = result.scalars().all()

        summaries = []
        for device in devices:
            occ_count = await self._get_occurrence_count(device.id)
            cat_trans = BALAGHA_CATEGORY_TRANSLATIONS.get(device.category, {})
            summaries.append(RhetoricalDeviceSummary(
                id=device.id,
                slug=device.slug,
                name_ar=device.name_ar,
                name_en=device.name_en,
                category=device.category,
                category_label_ar=cat_trans.get("ar", device.category),
                category_label_en=cat_trans.get("en", device.category),
                occurrence_count=occ_count,
            ))

        return summaries, total_count

    async def get_device_type(self, device_id: str) -> Optional[RhetoricalDeviceDetail]:
        """Get full details of a rhetorical device type."""
        result = await self.session.execute(
            select(RhetoricalDeviceType).where(RhetoricalDeviceType.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            return None

        cat_trans = BALAGHA_CATEGORY_TRANSLATIONS.get(device.category, {})

        return RhetoricalDeviceDetail(
            id=device.id,
            slug=device.slug,
            name_ar=device.name_ar,
            name_en=device.name_en,
            category=device.category,
            category_label_ar=cat_trans.get("ar", device.category),
            category_label_en=cat_trans.get("en", device.category),
            definition_ar=device.definition_ar,
            definition_en=device.definition_en,
            examples=device.examples_json,
            sub_types=device.sub_types_json,
            parent_device_id=device.parent_device_id,
            is_active=device.is_active,
        )

    async def get_categories(self) -> List[CategoryFacet]:
        """Get balagha categories with occurrence counts."""
        query = (
            select(
                RhetoricalDeviceType.category,
                func.count(RhetoricalDeviceType.id).label("count")
            )
            .where(RhetoricalDeviceType.is_active == True)
            .group_by(RhetoricalDeviceType.category)
            .order_by(RhetoricalDeviceType.category)
        )

        result = await self.session.execute(query)
        rows = result.all()

        facets = []
        for row in rows:
            category = row[0]
            count = row[1]
            trans = BALAGHA_CATEGORY_TRANSLATIONS.get(category, {})
            facets.append(CategoryFacet(
                category=category,
                label_ar=trans.get("ar", category),
                label_en=trans.get("en", category),
                count=count,
            ))

        return facets

    # -------------------------------------------------------------------------
    # OCCURRENCE OPERATIONS
    # -------------------------------------------------------------------------

    async def list_occurrences(
        self,
        device_type_id: Optional[str] = None,
        sura_no: Optional[int] = None,
        category: Optional[str] = None,
        verified_only: bool = False,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[RhetoricalOccurrenceInfo], int]:
        """
        List rhetorical device occurrences with filtering.

        Args:
            device_type_id: Filter by specific device type
            sura_no: Filter by surah number
            category: Filter by balagha category
            verified_only: Only return verified occurrences
            source: Filter by source (balagha_tafsir, curated, llm_extraction)
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (occurrences, total_count)
        """
        query = (
            select(RhetoricalOccurrence)
            .join(RhetoricalDeviceType)
        )

        if device_type_id:
            query = query.where(RhetoricalOccurrence.device_type_id == device_type_id)

        if sura_no:
            query = query.where(RhetoricalOccurrence.sura_no == sura_no)

        if category:
            query = query.where(RhetoricalDeviceType.category == category)

        if verified_only:
            query = query.where(RhetoricalOccurrence.is_verified == True)

        if source:
            query = query.where(RhetoricalOccurrence.source == source)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(
            RhetoricalOccurrence.sura_no,
            RhetoricalOccurrence.ayah_start
        )
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        occurrences = result.scalars().all()

        infos = []
        for occ in occurrences:
            # Get device type info
            device = await self._get_device_type_cached(occ.device_type_id)
            device_name_ar = device.name_ar if device else occ.device_type_id
            device_name_en = device.name_en if device else occ.device_type_id
            device_category = device.category if device else "unknown"

            infos.append(RhetoricalOccurrenceInfo(
                id=occ.id,
                device_type_id=occ.device_type_id,
                device_name_ar=device_name_ar,
                device_name_en=device_name_en,
                device_category=device_category,
                sura_no=occ.sura_no,
                ayah_start=occ.ayah_start,
                ayah_end=occ.ayah_end,
                verse_reference=occ.verse_reference,
                text_snippet_ar=occ.text_snippet_ar,
                explanation_ar=occ.explanation_ar,
                explanation_en=occ.explanation_en,
                evidence_count=len(occ.evidence_chunk_ids) if occ.evidence_chunk_ids else 0,
                confidence=occ.confidence or 1.0,
                source=occ.source,
                is_verified=occ.is_verified,
            ))

        return infos, total_count

    async def get_occurrences_by_verse(
        self,
        sura_no: int,
        ayah_no: int,
    ) -> List[RhetoricalOccurrenceInfo]:
        """Get all rhetorical device occurrences for a specific verse."""
        query = (
            select(RhetoricalOccurrence)
            .where(
                and_(
                    RhetoricalOccurrence.sura_no == sura_no,
                    RhetoricalOccurrence.ayah_start <= ayah_no,
                    RhetoricalOccurrence.ayah_end >= ayah_no,
                )
            )
            .order_by(RhetoricalOccurrence.device_type_id)
        )

        result = await self.session.execute(query)
        occurrences = result.scalars().all()

        infos = []
        for occ in occurrences:
            device = await self._get_device_type_cached(occ.device_type_id)
            device_name_ar = device.name_ar if device else occ.device_type_id
            device_name_en = device.name_en if device else occ.device_type_id
            device_category = device.category if device else "unknown"

            infos.append(RhetoricalOccurrenceInfo(
                id=occ.id,
                device_type_id=occ.device_type_id,
                device_name_ar=device_name_ar,
                device_name_en=device_name_en,
                device_category=device_category,
                sura_no=occ.sura_no,
                ayah_start=occ.ayah_start,
                ayah_end=occ.ayah_end,
                verse_reference=occ.verse_reference,
                text_snippet_ar=occ.text_snippet_ar,
                explanation_ar=occ.explanation_ar,
                explanation_en=occ.explanation_en,
                evidence_count=len(occ.evidence_chunk_ids) if occ.evidence_chunk_ids else 0,
                confidence=occ.confidence or 1.0,
                source=occ.source,
                is_verified=occ.is_verified,
            ))

        return infos

    async def get_occurrences_by_sura(
        self,
        sura_no: int,
        limit: int = 100,
    ) -> Tuple[List[RhetoricalOccurrenceInfo], Dict[str, int]]:
        """
        Get all rhetorical device occurrences for a surah with summary.

        Returns:
            Tuple of (occurrences, device_counts)
        """
        occurrences, _ = await self.list_occurrences(
            sura_no=sura_no,
            limit=limit,
        )

        # Build device count summary
        device_counts: Dict[str, int] = {}
        for occ in occurrences:
            key = occ.device_type_id
            device_counts[key] = device_counts.get(key, 0) + 1

        return occurrences, device_counts

    # -------------------------------------------------------------------------
    # PATTERN-BASED DETECTION (FOR ANALYSIS)
    # -------------------------------------------------------------------------

    def detect_potential_devices(
        self,
        text_ar: str,
    ) -> List[RhetoricalDetection]:
        """
        Detect potential rhetorical devices in Arabic text using pattern matching.

        NOTE: This is for analysis assistance only. Results must be validated
        against tafsir sources before creating actual occurrences.

        Args:
            text_ar: Arabic text to analyze

        Returns:
            List of potential device detections
        """
        detections: List[RhetoricalDetection] = []

        # Check for simile markers (تشبيه)
        for marker in TASHBIH_MARKERS:
            if marker in text_ar:
                trans = RHETORICAL_DEVICE_TRANSLATIONS.get("tashbih", {})
                detections.append(RhetoricalDetection(
                    device_key="tashbih",
                    device_name_ar=trans.get("ar", "تشبيه"),
                    device_name_en=trans.get("en", "Simile"),
                    category="bayaan",
                    matched_text=marker,
                    pattern_type="marker",
                    confidence=0.6,
                    evidence_needed=True,
                ))
                break  # Only detect once per category

        # Check for rhetorical question particles (استفهام بلاغي)
        for particle in ISTIFHAM_PARTICLES:
            if text_ar.startswith(particle) or f" {particle}" in text_ar:
                trans = RHETORICAL_DEVICE_TRANSLATIONS.get("istifham", {})
                detections.append(RhetoricalDetection(
                    device_key="istifham",
                    device_name_ar=trans.get("ar", "استفهام بلاغي"),
                    device_name_en=trans.get("en", "Rhetorical Question"),
                    category="maani",
                    matched_text=particle,
                    pattern_type="marker",
                    confidence=0.5,  # Lower confidence - needs context
                    evidence_needed=True,
                ))
                break

        # Check for vocative (نداء)
        for particle in NIDA_PARTICLES:
            if particle in text_ar:
                trans = RHETORICAL_DEVICE_TRANSLATIONS.get("nida", {})
                detections.append(RhetoricalDetection(
                    device_key="nida",
                    device_name_ar="نداء",
                    device_name_en="Vocative",
                    category="maani",
                    matched_text=particle,
                    pattern_type="marker",
                    confidence=0.7,
                    evidence_needed=True,
                ))
                break

        # Check for restriction markers (قصر)
        for marker in QASR_MARKERS:
            if marker in text_ar:
                trans = RHETORICAL_DEVICE_TRANSLATIONS.get("qasr", {})
                detections.append(RhetoricalDetection(
                    device_key="qasr",
                    device_name_ar="قصر",
                    device_name_en="Restriction",
                    category="maani",
                    matched_text=marker,
                    pattern_type="marker",
                    confidence=0.7,
                    evidence_needed=True,
                ))
                break

        return detections

    def detect_antithesis(self, text_ar: str) -> Optional[RhetoricalDetection]:
        """
        Detect potential antithesis (طباق) by finding opposing word pairs.

        Common Quranic antitheses:
        - الليل/النهار (night/day)
        - الأعمى/البصير (blind/seeing)
        - الظلمات/النور (darkness/light)
        - الموت/الحياة (death/life)
        """
        antithesis_pairs = [
            ("اللَّيْل", "النَّهَار"),
            ("الأَعْمَى", "البَصِير"),
            ("الظُّلُمَات", "النُّور"),
            ("المَوْت", "الحَيَاة"),
            ("السَّمَاء", "الأَرْض"),
            ("الخَيْر", "الشَّرّ"),
            ("الجَنَّة", "النَّار"),
            ("الحَقّ", "البَاطِل"),
        ]

        for word1, word2 in antithesis_pairs:
            # Simplified matching (real implementation would use morphological analysis)
            if word1.replace("ال", "") in text_ar and word2.replace("ال", "") in text_ar:
                trans = RHETORICAL_DEVICE_TRANSLATIONS.get("tibaq", {})
                return RhetoricalDetection(
                    device_key="tibaq",
                    device_name_ar=trans.get("ar", "طباق"),
                    device_name_en=trans.get("en", "Antithesis"),
                    category="badeea",
                    matched_text=f"{word1} / {word2}",
                    pattern_type="structural",
                    confidence=0.6,
                    evidence_needed=True,
                )

        return None

    # -------------------------------------------------------------------------
    # TAFSIR EXTRACTION HELPERS
    # -------------------------------------------------------------------------

    def get_balagha_search_terms(self) -> Dict[str, List[str]]:
        """
        Get Arabic search terms for finding rhetoric in tafsir text.

        Returns:
            Dictionary mapping device keys to Arabic search terms
        """
        return {
            "istiaara": ["استعارة", "استعير", "المستعار"],
            "tashbih": ["تشبيه", "شُبّه", "المشبه", "التمثيل"],
            "tibaq": ["طباق", "المطابقة", "الضد", "الأضداد"],
            "jinas": ["جناس", "التجانس", "الجناس"],
            "kinaya": ["كناية", "كنى", "الكناية"],
            "majaz": ["مجاز", "المجاز", "مجازي"],
            "iltifat": ["التفات", "الالتفات", "التحول"],
            "istifham": ["استفهام", "السؤال البلاغي"],
            "itnaab": ["إطناب", "الإطناب", "التفصيل"],
            "ijaz": ["إيجاز", "الإيجاز", "الحذف"],
            "taqdim": ["تقديم", "التقديم والتأخير", "قدّم"],
            "saj": ["سجع", "الفاصلة", "الفواصل"],
            "tawriya": ["تورية", "التورية"],
            "muqabala": ["مقابلة", "المقابلة"],
        }

    async def search_tafsir_for_rhetoric(
        self,
        tafsir_chunks: List[Dict[str, Any]],
        device_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search tafsir chunks for rhetorical device mentions.

        Args:
            tafsir_chunks: List of tafsir text chunks with metadata
            device_key: Optional specific device to search for

        Returns:
            List of matches with chunk info and matched terms
        """
        search_terms = self.get_balagha_search_terms()

        if device_key:
            search_terms = {device_key: search_terms.get(device_key, [])}

        matches = []
        for chunk in tafsir_chunks:
            text = chunk.get("text_ar", "") or chunk.get("text", "")

            for key, terms in search_terms.items():
                for term in terms:
                    if term in text:
                        matches.append({
                            "chunk_id": chunk.get("id"),
                            "device_key": key,
                            "matched_term": term,
                            "tafsir_source": chunk.get("source"),
                            "sura_no": chunk.get("sura_no"),
                            "ayah_no": chunk.get("ayah_no"),
                            "text_snippet": text[:200] + "..." if len(text) > 200 else text,
                        })
                        break  # One match per device per chunk

        return matches

    # -------------------------------------------------------------------------
    # STATISTICS AND AGGREGATIONS
    # -------------------------------------------------------------------------

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall rhetorical analysis statistics."""
        # Total device types
        device_count_result = await self.session.execute(
            select(func.count(RhetoricalDeviceType.id))
            .where(RhetoricalDeviceType.is_active == True)
        )
        total_devices = device_count_result.scalar() or 0

        # Total occurrences
        occ_count_result = await self.session.execute(
            select(func.count(RhetoricalOccurrence.id))
        )
        total_occurrences = occ_count_result.scalar() or 0

        # Verified occurrences
        verified_count_result = await self.session.execute(
            select(func.count(RhetoricalOccurrence.id))
            .where(RhetoricalOccurrence.is_verified == True)
        )
        verified_occurrences = verified_count_result.scalar() or 0

        # By category
        category_query = (
            select(
                RhetoricalDeviceType.category,
                func.count(RhetoricalOccurrence.id).label("count")
            )
            .join(RhetoricalOccurrence)
            .group_by(RhetoricalDeviceType.category)
        )
        category_result = await self.session.execute(category_query)
        by_category = {row[0]: row[1] for row in category_result.all()}

        # By source
        source_query = (
            select(
                RhetoricalOccurrence.source,
                func.count(RhetoricalOccurrence.id).label("count")
            )
            .group_by(RhetoricalOccurrence.source)
        )
        source_result = await self.session.execute(source_query)
        by_source = {row[0] or "unknown": row[1] for row in source_result.all()}

        return {
            "total_device_types": total_devices,
            "total_occurrences": total_occurrences,
            "verified_occurrences": verified_occurrences,
            "verification_rate": round(verified_occurrences / total_occurrences, 2) if total_occurrences > 0 else 0,
            "by_category": by_category,
            "by_source": by_source,
        }

    # -------------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------------

    async def _get_occurrence_count(self, device_type_id: str) -> int:
        """Get count of occurrences for a device type."""
        query = select(func.count(RhetoricalOccurrence.id)).where(
            RhetoricalOccurrence.device_type_id == device_type_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_device_type_cached(self, device_type_id: str) -> Optional[RhetoricalDeviceType]:
        """Get device type (would benefit from caching in production)."""
        result = await self.session.execute(
            select(RhetoricalDeviceType).where(RhetoricalDeviceType.id == device_type_id)
        )
        return result.scalar_one_or_none()
