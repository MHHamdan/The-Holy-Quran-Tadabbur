"""
Tone Analyzer Service - Quranic Emotional Tone Detection

This service provides:
1. Emotional tone tagging for verse ranges
2. Intensity scoring for tones
3. Surah tone profiles and distribution
4. Evidence-grounded tone classification

TONE TYPES:
==========
Quranic emotional tones differ from general sentiment analysis - they reflect
the spiritual and moral dimensions of the Quran's message:

- HOPE (رجاء): Emphasis on Allah's mercy, forgiveness, reward
- FEAR (خوف): Emphasis on accountability, punishment, Day of Judgment
- AWE (خشوع): Divine majesty, creation, power
- ADMONISHMENT (تذكير): Reminder and warning
- GLAD_TIDINGS (بشارة): Good news for believers
- WARNING (تحذير): Stern warning to disbelievers
- CONSOLATION (تسلية): Comfort to Prophet and believers
- GRATITUDE (شكر): Call to thankfulness
- CERTAINTY (يقين): Emphasis on truth and conviction
- URGENCY (استعجال): Time-sensitive call to action
- COMPASSION (رحمة): Divine compassion and mercy
- REBUKE (تأنيب): Criticism of wrong behavior
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rhetoric import (
    VerseTone,
    ToneType,
    TONE_TYPE_TRANSLATIONS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ARABIC VOCABULARY FOR TONE DETECTION
# =============================================================================

# Hope vocabulary (رجاء)
HOPE_VOCABULARY = [
    "رَحْمَة",           # rahma - mercy
    "مَغْفِرَة",         # maghfira - forgiveness
    "جَنَّة",           # janna - paradise
    "تَوْبَة",          # tawba - repentance
    "فَضْل",           # fadl - grace
    "رَحِيم",          # rahim - merciful
    "غَفُور",          # ghafur - forgiving
    "تَائِب",          # ta'ib - accepting repentance
    "رَجَاء",          # raja' - hope
    "أَمَل",           # amal - hope
]

# Fear vocabulary (خوف)
FEAR_VOCABULARY = [
    "عَذَاب",          # adhab - punishment
    "نَار",            # nar - fire
    "حِسَاب",          # hisab - reckoning
    "جَهَنَّم",         # jahannam - hell
    "يَوْم الْقِيَامَة",  # yawm al-qiyama - Day of Resurrection
    "خَوْف",           # khawf - fear
    "شَدِيد",          # shadid - severe
    "عَقَاب",          # iqab - punishment
    "خَشْيَة",          # khashya - awe/fear
]

# Awe vocabulary (خشوع)
AWE_VOCABULARY = [
    "سُبْحَان",         # subhan - glory
    "الْعَظِيم",        # al-adhim - the Magnificent
    "الْكَبِير",        # al-kabir - the Great
    "الْمَلِك",         # al-malik - the King
    "الْقُدُّوس",       # al-quddus - the Holy
    "خَلَقَ",          # khalaqa - created
    "السَّمَاوَات",     # al-samawat - the heavens
    "خَشَعَ",          # khasha'a - humbled
    "تَوَاضَعَ",        # tawada'a - humbled
]

# Glad tidings vocabulary (بشارة)
GLAD_TIDINGS_VOCABULARY = [
    "بُشْرَى",          # bushra - glad tidings
    "بَشِّرْ",          # bashshir - give good news
    "فَوْز",           # fawz - success
    "نَجَاة",          # najat - salvation
    "فَلَاح",          # falah - prosperity
    "أَجْر",           # ajr - reward
    "ثَوَاب",          # thawab - reward
]

# Warning vocabulary (تحذير)
WARNING_VOCABULARY = [
    "وَيْل",           # wayl - woe
    "هَلَاك",          # halak - destruction
    "خُسْرَان",         # khusran - loss
    "ضَلَال",          # dalal - misguidance
    "فَسَاد",          # fasad - corruption
    "احْذَرُوا",        # ihdharu - beware
    "لَا تَ",          # la ta- (prohibition prefix)
]

# Consolation vocabulary (تسلية)
CONSOLATION_VOCABULARY = [
    "لَا تَحْزَنْ",      # la tahzan - do not grieve
    "لَا تَخَفْ",       # la takhaf - do not fear
    "صَبْر",           # sabr - patience
    "مَعَ الْعُسْرِ",    # ma'a al-usr - with hardship
    "إِنَّ مَعَ الْعُسْرِ يُسْرًا",  # with hardship comes ease
    "فَاصْبِرْ",        # fasbir - so be patient
]

# Gratitude vocabulary (شكر)
GRATITUDE_VOCABULARY = [
    "الْحَمْدُ",        # al-hamd - praise
    "شُكْر",           # shukr - gratitude
    "نِعْمَة",          # ni'ma - blessing
    "اشْكُرُوا",        # ushkuru - be grateful
    "شَاكِر",          # shakir - grateful
    "حَامِد",          # hamid - praising
]

# Urgency vocabulary (استعجال)
URGENCY_VOCABULARY = [
    "سَارِعُوا",        # sari'u - hasten
    "فَفِرُّوا",        # fafirru - so flee
    "وَبَادِرُوا",       # wa badiru - and rush
    "أَسْرِعُوا",       # asri'u - hurry
    "قَبْلَ أَنْ",       # qabla an - before
    "الْيَوْم",         # al-yawm - today
]

# Compassion vocabulary (رحمة)
COMPASSION_VOCABULARY = [
    "رَحْمَة",          # rahma - mercy
    "رَأْفَة",          # ra'fa - compassion
    "حَنَان",          # hanan - tenderness
    "رَفِيق",          # rafiq - gentle
    "لَطِيف",          # latif - subtle/kind
    "وَدُود",          # wadud - loving
    "بَرّ",            # barr - righteous/kind
]

# Rebuke vocabulary (تأنيب)
REBUKE_VOCABULARY = [
    "أَفَلَا",          # afala - do they not
    "بِئْسَ",          # bi'sa - wretched is
    "قَبِيح",          # qabih - ugly/evil
    "لَوْمَة",          # lawma - blame
    "ظَالِم",          # dhalim - wrongdoer
    "كَافِر",          # kafir - disbeliever
    "مُنَافِق",         # munafiq - hypocrite
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ToneAnnotationSummary:
    """Summary of a tone annotation."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    tone_type: str
    tone_label_ar: str
    tone_label_en: str
    intensity: float
    is_verified: bool


@dataclass
class ToneAnnotationDetail:
    """Full detail of a tone annotation."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    tone_type: str
    tone_label_ar: str
    tone_label_en: str
    intensity: float
    explanation_ar: Optional[str]
    explanation_en: Optional[str]
    evidence_count: int
    confidence: float
    source: Optional[str]
    is_verified: bool


@dataclass
class ToneTypeFacet:
    """Tone type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


@dataclass
class ToneDetection:
    """Result of tone detection."""
    tone_type: str
    tone_label_ar: str
    tone_label_en: str
    matched_vocabulary: List[str]
    intensity: float  # 0.0 to 1.0
    confidence: float
    evidence_needed: bool = True


@dataclass
class SurahToneProfile:
    """Tone profile for a surah."""
    sura_no: int
    total_annotations: int
    tone_distribution: Dict[str, int]
    dominant_tone: str
    average_intensity: float
    intensity_by_tone: Dict[str, float]
    has_warning: bool
    has_glad_tidings: bool
    emotional_range: List[str]  # List of unique tones present


@dataclass
class ToneTransition:
    """Transition between tones in a surah."""
    from_tone: str
    to_tone: str
    at_ayah: int
    transition_type: str  # "gradual", "sharp"


# =============================================================================
# TONE ANALYZER SERVICE
# =============================================================================

class ToneAnalyzer:
    """
    Service for Quranic emotional tone analysis.

    Detects and classifies emotional tones in verses with
    intensity scoring and evidence grounding.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------------------------------
    # ANNOTATION OPERATIONS
    # -------------------------------------------------------------------------

    async def list_annotations(
        self,
        tone_type: Optional[str] = None,
        sura_no: Optional[int] = None,
        min_intensity: Optional[float] = None,
        verified_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ToneAnnotationSummary], int]:
        """
        List tone annotations with optional filtering.

        Args:
            tone_type: Filter by tone type
            sura_no: Filter by surah number
            min_intensity: Filter by minimum intensity
            verified_only: Only return verified annotations
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (annotations, total_count)
        """
        logger.debug(
            "list_annotations called",
            extra={"type": tone_type, "sura": sura_no}
        )

        query = select(VerseTone)

        if tone_type:
            query = query.where(VerseTone.tone_type == tone_type)

        if sura_no:
            query = query.where(VerseTone.sura_no == sura_no)

        if min_intensity is not None:
            query = query.where(VerseTone.intensity >= min_intensity)

        if verified_only:
            query = query.where(VerseTone.is_verified == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(
            VerseTone.sura_no,
            VerseTone.ayah_start
        )
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        annotations = result.scalars().all()

        summaries = []
        for ann in annotations:
            trans = TONE_TYPE_TRANSLATIONS.get(ann.tone_type, {})
            summaries.append(ToneAnnotationSummary(
                id=ann.id,
                sura_no=ann.sura_no,
                ayah_start=ann.ayah_start,
                ayah_end=ann.ayah_end,
                verse_reference=ann.verse_reference,
                tone_type=ann.tone_type,
                tone_label_ar=trans.get("ar", ann.tone_type),
                tone_label_en=trans.get("en", ann.tone_type),
                intensity=ann.intensity or 0.5,
                is_verified=ann.is_verified,
            ))

        return summaries, total_count

    async def get_annotation(self, annotation_id: int) -> Optional[ToneAnnotationDetail]:
        """Get full details of a tone annotation."""
        result = await self.session.execute(
            select(VerseTone).where(VerseTone.id == annotation_id)
        )
        ann = result.scalar_one_or_none()

        if not ann:
            return None

        trans = TONE_TYPE_TRANSLATIONS.get(ann.tone_type, {})

        return ToneAnnotationDetail(
            id=ann.id,
            sura_no=ann.sura_no,
            ayah_start=ann.ayah_start,
            ayah_end=ann.ayah_end,
            verse_reference=ann.verse_reference,
            tone_type=ann.tone_type,
            tone_label_ar=trans.get("ar", ann.tone_type),
            tone_label_en=trans.get("en", ann.tone_type),
            intensity=ann.intensity or 0.5,
            explanation_ar=ann.explanation_ar,
            explanation_en=ann.explanation_en,
            evidence_count=len(ann.evidence_chunk_ids) if ann.evidence_chunk_ids else 0,
            confidence=ann.confidence or 1.0,
            source=ann.source,
            is_verified=ann.is_verified,
        )

    async def get_annotations_by_verse(
        self,
        sura_no: int,
        ayah_no: int,
    ) -> List[ToneAnnotationSummary]:
        """Get tone annotations for a specific verse."""
        query = (
            select(VerseTone)
            .where(
                and_(
                    VerseTone.sura_no == sura_no,
                    VerseTone.ayah_start <= ayah_no,
                    VerseTone.ayah_end >= ayah_no,
                )
            )
            .order_by(VerseTone.intensity.desc())
        )

        result = await self.session.execute(query)
        annotations = result.scalars().all()

        summaries = []
        for ann in annotations:
            trans = TONE_TYPE_TRANSLATIONS.get(ann.tone_type, {})
            summaries.append(ToneAnnotationSummary(
                id=ann.id,
                sura_no=ann.sura_no,
                ayah_start=ann.ayah_start,
                ayah_end=ann.ayah_end,
                verse_reference=ann.verse_reference,
                tone_type=ann.tone_type,
                tone_label_ar=trans.get("ar", ann.tone_type),
                tone_label_en=trans.get("en", ann.tone_type),
                intensity=ann.intensity or 0.5,
                is_verified=ann.is_verified,
            ))

        return summaries

    async def get_tone_types(self) -> List[ToneTypeFacet]:
        """Get available tone types with counts."""
        query = (
            select(
                VerseTone.tone_type,
                func.count(VerseTone.id).label("count")
            )
            .group_by(VerseTone.tone_type)
            .order_by(func.count(VerseTone.id).desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        facets = []
        for row in rows:
            ttype = row[0]
            count = row[1]
            trans = TONE_TYPE_TRANSLATIONS.get(ttype, {})
            facets.append(ToneTypeFacet(
                type=ttype,
                label_ar=trans.get("ar", ttype),
                label_en=trans.get("en", ttype),
                count=count,
            ))

        return facets

    # -------------------------------------------------------------------------
    # SURAH ANALYSIS
    # -------------------------------------------------------------------------

    async def get_surah_tone_profile(
        self,
        sura_no: int,
    ) -> SurahToneProfile:
        """
        Get the emotional tone profile for a surah.

        Returns:
            Profile with tone distribution, dominant tone, and intensity metrics
        """
        annotations, _ = await self.list_annotations(sura_no=sura_no, limit=500)

        tone_distribution: Dict[str, int] = {}
        intensity_totals: Dict[str, float] = {}
        intensity_counts: Dict[str, int] = {}

        for ann in annotations:
            ttype = ann.tone_type
            tone_distribution[ttype] = tone_distribution.get(ttype, 0) + 1
            intensity_totals[ttype] = intensity_totals.get(ttype, 0) + ann.intensity
            intensity_counts[ttype] = intensity_counts.get(ttype, 0) + 1

        # Calculate average intensity per tone
        intensity_by_tone = {
            ttype: round(intensity_totals[ttype] / intensity_counts[ttype], 2)
            for ttype in intensity_totals
        }

        # Overall average intensity
        all_intensities = [ann.intensity for ann in annotations]
        avg_intensity = round(sum(all_intensities) / len(all_intensities), 2) if all_intensities else 0.5

        # Determine dominant tone
        dominant_tone = max(tone_distribution, key=tone_distribution.get) if tone_distribution else "unknown"

        # Check for specific tones
        has_warning = ToneType.WARNING.value in tone_distribution
        has_glad_tidings = ToneType.GLAD_TIDINGS.value in tone_distribution

        return SurahToneProfile(
            sura_no=sura_no,
            total_annotations=len(annotations),
            tone_distribution=tone_distribution,
            dominant_tone=dominant_tone,
            average_intensity=avg_intensity,
            intensity_by_tone=intensity_by_tone,
            has_warning=has_warning,
            has_glad_tidings=has_glad_tidings,
            emotional_range=list(tone_distribution.keys()),
        )

    async def get_high_intensity_verses(
        self,
        sura_no: Optional[int] = None,
        tone_type: Optional[str] = None,
        min_intensity: float = 0.8,
        limit: int = 20,
    ) -> List[ToneAnnotationSummary]:
        """Get verses with high emotional intensity."""
        annotations, _ = await self.list_annotations(
            tone_type=tone_type,
            sura_no=sura_no,
            min_intensity=min_intensity,
            limit=limit,
        )
        return annotations

    # -------------------------------------------------------------------------
    # PATTERN-BASED DETECTION (FOR ANALYSIS)
    # -------------------------------------------------------------------------

    def detect_tones(
        self,
        text_ar: str,
    ) -> List[ToneDetection]:
        """
        Detect potential emotional tones in Arabic text using vocabulary matching.

        NOTE: This is for analysis assistance only. Results must be validated
        against tafsir sources before creating actual annotations.

        Args:
            text_ar: Arabic text to analyze

        Returns:
            List of potential tone detections ordered by confidence
        """
        detections: List[ToneDetection] = []

        # Check for hope vocabulary
        hope_matches = [v for v in HOPE_VOCABULARY if v in text_ar]
        if hope_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("hope", {})
            intensity = min(0.5 + (len(hope_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="hope",
                tone_label_ar=trans.get("ar", "رجاء"),
                tone_label_en=trans.get("en", "Hope"),
                matched_vocabulary=hope_matches,
                intensity=intensity,
                confidence=0.6 + (len(hope_matches) * 0.05),
            ))

        # Check for fear vocabulary
        fear_matches = [v for v in FEAR_VOCABULARY if v in text_ar]
        if fear_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("fear", {})
            intensity = min(0.5 + (len(fear_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="fear",
                tone_label_ar=trans.get("ar", "خوف"),
                tone_label_en=trans.get("en", "Fear"),
                matched_vocabulary=fear_matches,
                intensity=intensity,
                confidence=0.6 + (len(fear_matches) * 0.05),
            ))

        # Check for awe vocabulary
        awe_matches = [v for v in AWE_VOCABULARY if v in text_ar]
        if awe_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("awe", {})
            intensity = min(0.5 + (len(awe_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="awe",
                tone_label_ar=trans.get("ar", "خشوع"),
                tone_label_en=trans.get("en", "Awe"),
                matched_vocabulary=awe_matches,
                intensity=intensity,
                confidence=0.6 + (len(awe_matches) * 0.05),
            ))

        # Check for glad tidings vocabulary
        glad_matches = [v for v in GLAD_TIDINGS_VOCABULARY if v in text_ar]
        if glad_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("glad_tidings", {})
            intensity = min(0.5 + (len(glad_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="glad_tidings",
                tone_label_ar=trans.get("ar", "بشارة"),
                tone_label_en=trans.get("en", "Glad Tidings"),
                matched_vocabulary=glad_matches,
                intensity=intensity,
                confidence=0.7 + (len(glad_matches) * 0.05),
            ))

        # Check for warning vocabulary
        warning_matches = [v for v in WARNING_VOCABULARY if v in text_ar]
        if warning_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("warning", {})
            intensity = min(0.6 + (len(warning_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="warning",
                tone_label_ar=trans.get("ar", "تحذير"),
                tone_label_en=trans.get("en", "Warning"),
                matched_vocabulary=warning_matches,
                intensity=intensity,
                confidence=0.7 + (len(warning_matches) * 0.05),
            ))

        # Check for consolation vocabulary
        consolation_matches = [v for v in CONSOLATION_VOCABULARY if v in text_ar]
        if consolation_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("consolation", {})
            intensity = min(0.5 + (len(consolation_matches) * 0.15), 1.0)
            detections.append(ToneDetection(
                tone_type="consolation",
                tone_label_ar=trans.get("ar", "تسلية"),
                tone_label_en=trans.get("en", "Consolation"),
                matched_vocabulary=consolation_matches,
                intensity=intensity,
                confidence=0.7 + (len(consolation_matches) * 0.05),
            ))

        # Check for gratitude vocabulary
        gratitude_matches = [v for v in GRATITUDE_VOCABULARY if v in text_ar]
        if gratitude_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("gratitude", {})
            intensity = min(0.5 + (len(gratitude_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="gratitude",
                tone_label_ar=trans.get("ar", "شكر"),
                tone_label_en=trans.get("en", "Gratitude"),
                matched_vocabulary=gratitude_matches,
                intensity=intensity,
                confidence=0.6 + (len(gratitude_matches) * 0.05),
            ))

        # Check for urgency vocabulary
        urgency_matches = [v for v in URGENCY_VOCABULARY if v in text_ar]
        if urgency_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("urgency", {})
            intensity = min(0.6 + (len(urgency_matches) * 0.15), 1.0)
            detections.append(ToneDetection(
                tone_type="urgency",
                tone_label_ar=trans.get("ar", "استعجال"),
                tone_label_en=trans.get("en", "Urgency"),
                matched_vocabulary=urgency_matches,
                intensity=intensity,
                confidence=0.7 + (len(urgency_matches) * 0.05),
            ))

        # Check for compassion vocabulary
        compassion_matches = [v for v in COMPASSION_VOCABULARY if v in text_ar]
        if compassion_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("compassion", {})
            intensity = min(0.5 + (len(compassion_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="compassion",
                tone_label_ar=trans.get("ar", "رحمة"),
                tone_label_en=trans.get("en", "Compassion"),
                matched_vocabulary=compassion_matches,
                intensity=intensity,
                confidence=0.6 + (len(compassion_matches) * 0.05),
            ))

        # Check for rebuke vocabulary
        rebuke_matches = [v for v in REBUKE_VOCABULARY if v in text_ar]
        if rebuke_matches:
            trans = TONE_TYPE_TRANSLATIONS.get("rebuke", {})
            intensity = min(0.6 + (len(rebuke_matches) * 0.1), 1.0)
            detections.append(ToneDetection(
                tone_type="rebuke",
                tone_label_ar=trans.get("ar", "تأنيب"),
                tone_label_en=trans.get("en", "Rebuke"),
                matched_vocabulary=rebuke_matches,
                intensity=intensity,
                confidence=0.6 + (len(rebuke_matches) * 0.05),
            ))

        # Sort by confidence
        detections.sort(key=lambda d: d.confidence, reverse=True)

        return detections

    def calculate_overall_tone(
        self,
        detections: List[ToneDetection],
    ) -> Optional[ToneDetection]:
        """
        Calculate the overall dominant tone from multiple detections.

        Args:
            detections: List of tone detections

        Returns:
            The dominant tone detection or None if no detections
        """
        if not detections:
            return None

        # Weight by confidence and intensity
        scored_detections = [
            (d, d.confidence * d.intensity) for d in detections
        ]
        scored_detections.sort(key=lambda x: x[1], reverse=True)

        return scored_detections[0][0]

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall tone analysis statistics."""
        # Total annotations
        total_result = await self.session.execute(
            select(func.count(VerseTone.id))
        )
        total_annotations = total_result.scalar() or 0

        # Verified annotations
        verified_result = await self.session.execute(
            select(func.count(VerseTone.id))
            .where(VerseTone.is_verified == True)
        )
        verified_annotations = verified_result.scalar() or 0

        # Average intensity
        avg_intensity_result = await self.session.execute(
            select(func.avg(VerseTone.intensity))
        )
        avg_intensity = round(avg_intensity_result.scalar() or 0.5, 2)

        # By type
        types = await self.get_tone_types()
        by_type = {t.type: t.count for t in types}

        # High intensity count (>= 0.8)
        high_intensity_result = await self.session.execute(
            select(func.count(VerseTone.id))
            .where(VerseTone.intensity >= 0.8)
        )
        high_intensity_count = high_intensity_result.scalar() or 0

        # Unique surahs covered
        surahs_result = await self.session.execute(
            select(func.count(func.distinct(VerseTone.sura_no)))
        )
        surahs_covered = surahs_result.scalar() or 0

        return {
            "total_annotations": total_annotations,
            "verified_annotations": verified_annotations,
            "verification_rate": round(verified_annotations / total_annotations, 2) if total_annotations > 0 else 0,
            "average_intensity": avg_intensity,
            "high_intensity_count": high_intensity_count,
            "surahs_covered": surahs_covered,
            "by_type": by_type,
        }
