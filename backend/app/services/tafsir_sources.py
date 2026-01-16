"""
Modern Tafsir Sources Service for Quranic Studies.

Provides support for:
1. Modern Tafsir sources (20th-21st century scholars)
2. Multilingual Tafsir (Arabic, English, French, Urdu, Indonesian)
3. Thematic categorization of Tafsir content
4. Comparative Tafsir analysis

Arabic: خدمة مصادر التفسير الحديث للقرآن الكريم
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class TafsirEra(str, Enum):
    """Era classification for Tafsir sources."""
    CLASSICAL = "classical"      # Pre-1900 CE
    MODERN = "modern"            # 1900-2000 CE
    CONTEMPORARY = "contemporary" # 2000+ CE


class TafsirMethodology(str, Enum):
    """Tafsir methodology types."""
    BIL_MATHUR = "bil_mathur"    # تفسير بالمأثور - Based on narrations
    BIL_RAY = "bil_ray"          # تفسير بالرأي - Based on reasoning
    LINGUISTIC = "linguistic"    # تفسير لغوي - Linguistic analysis
    THEMATIC = "thematic"        # تفسير موضوعي - Thematic approach
    SCIENTIFIC = "scientific"    # تفسير علمي - Scientific interpretation
    SOCIAL = "social"            # تفسير اجتماعي - Social/reform focus
    COMPREHENSIVE = "comprehensive"  # شامل - Multiple approaches


class TafsirLanguage(str, Enum):
    """Supported languages for Tafsir."""
    ARABIC = "ar"
    ENGLISH = "en"
    FRENCH = "fr"
    URDU = "ur"
    INDONESIAN = "id"
    TURKISH = "tr"
    MALAY = "ms"
    PERSIAN = "fa"


# =============================================================================
# MODERN TAFSIR SOURCES CATALOG
# =============================================================================

# Comprehensive catalog of modern and classical Tafsir sources
TAFSIR_CATALOG = {
    # Classical Sources (already in DB, but enhanced metadata)
    "ibn_kathir": {
        "id": "ibn_kathir",
        "name_ar": "تفسير ابن كثير",
        "name_en": "Tafsir Ibn Kathir",
        "author_ar": "إسماعيل بن عمر بن كثير",
        "author_en": "Ismail ibn Umar ibn Kathir",
        "era": TafsirEra.CLASSICAL,
        "death_year_hijri": 774,
        "death_year_ce": 1373,
        "methodology": TafsirMethodology.BIL_MATHUR,
        "languages_available": [TafsirLanguage.ARABIC, TafsirLanguage.ENGLISH, TafsirLanguage.URDU],
        "description_ar": "من أشهر كتب التفسير بالمأثور، يعتمد على الأحاديث والآثار",
        "description_en": "One of the most renowned tafsirs, relies on hadith and reports from companions",
        "strengths": ["hadith_based", "chain_verification", "linguistic_analysis"],
        "focus_areas": ["prophets", "history", "hadith"],
        "school": "sunni",
    },
    "tabari": {
        "id": "tabari",
        "name_ar": "جامع البيان في تأويل القرآن",
        "name_en": "Jami' al-Bayan (Tafsir al-Tabari)",
        "author_ar": "محمد بن جرير الطبري",
        "author_en": "Muhammad ibn Jarir al-Tabari",
        "era": TafsirEra.CLASSICAL,
        "death_year_hijri": 310,
        "death_year_ce": 923,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "أم التفاسير، يجمع أقوال السلف مع الترجيح",
        "description_en": "The 'mother of all tafsirs', comprehensive collection of scholarly opinions",
        "strengths": ["comprehensive", "historical", "linguistic"],
        "focus_areas": ["all_topics", "scholarly_opinions"],
        "school": "sunni",
    },
    "qurtubi": {
        "id": "qurtubi",
        "name_ar": "الجامع لأحكام القرآن",
        "name_en": "Al-Jami' li Ahkam al-Quran (Tafsir al-Qurtubi)",
        "author_ar": "محمد بن أحمد القرطبي",
        "author_en": "Muhammad ibn Ahmad al-Qurtubi",
        "era": TafsirEra.CLASSICAL,
        "death_year_hijri": 671,
        "death_year_ce": 1273,
        "methodology": TafsirMethodology.BIL_RAY,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "تفسير فقهي شامل يركز على أحكام القرآن",
        "description_en": "Comprehensive jurisprudential tafsir focusing on Quranic rulings",
        "strengths": ["fiqh", "rulings", "linguistic"],
        "focus_areas": ["law", "ethics", "rulings"],
        "school": "sunni_maliki",
    },
    "jalalayn": {
        "id": "jalalayn",
        "name_ar": "تفسير الجلالين",
        "name_en": "Tafsir al-Jalalayn",
        "author_ar": "جلال الدين المحلي وجلال الدين السيوطي",
        "author_en": "Jalal ad-Din al-Mahalli and Jalal ad-Din as-Suyuti",
        "era": TafsirEra.CLASSICAL,
        "death_year_hijri": 911,
        "death_year_ce": 1505,
        "methodology": TafsirMethodology.LINGUISTIC,
        "languages_available": [TafsirLanguage.ARABIC, TafsirLanguage.ENGLISH],
        "description_ar": "تفسير مختصر يركز على معاني الألفاظ",
        "description_en": "Concise tafsir focusing on word meanings and basic explanations",
        "strengths": ["concise", "accessible", "beginner_friendly"],
        "focus_areas": ["word_meanings", "basic_understanding"],
        "school": "sunni_shafii",
    },

    # Modern Sources (20th century)
    "fi_zilal": {
        "id": "fi_zilal",
        "name_ar": "في ظلال القرآن",
        "name_en": "Fi Zilal al-Quran (In the Shade of the Quran)",
        "author_ar": "سيد قطب",
        "author_en": "Sayyid Qutb",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1386,
        "death_year_ce": 1966,
        "methodology": TafsirMethodology.SOCIAL,
        "languages_available": [TafsirLanguage.ARABIC, TafsirLanguage.ENGLISH],
        "description_ar": "تفسير أدبي اجتماعي يركز على التطبيق المعاصر",
        "description_en": "Literary and social tafsir focusing on contemporary application",
        "strengths": ["literary", "social_reform", "spiritual"],
        "focus_areas": ["social_justice", "spiritual_growth", "islamic_movement"],
        "school": "sunni",
    },
    "sha_rawi": {
        "id": "sha_rawi",
        "name_ar": "تفسير الشعراوي",
        "name_en": "Tafsir al-Sha'rawi",
        "author_ar": "محمد متولي الشعراوي",
        "author_en": "Muhammad Metwalli al-Sha'rawi",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1419,
        "death_year_ce": 1998,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "تفسير شعبي يجمع بين البساطة والعمق",
        "description_en": "Popular tafsir combining simplicity with depth, from TV lectures",
        "strengths": ["accessible", "spiritual", "practical"],
        "focus_areas": ["daily_life", "spiritual_reflection", "arabic_beauty"],
        "school": "sunni",
    },
    "muyassar": {
        "id": "muyassar",
        "name_ar": "التفسير الميسر",
        "name_en": "Al-Tafsir Al-Muyassar",
        "author_ar": "مجمع الملك فهد لطباعة المصحف الشريف",
        "author_en": "King Fahd Complex for Printing the Holy Quran",
        "era": TafsirEra.MODERN,
        "death_year_hijri": None,
        "death_year_ce": 2003,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "تفسير مختصر سهل للقارئ العام",
        "description_en": "Simplified tafsir for general readers",
        "strengths": ["simple", "accessible", "official"],
        "focus_areas": ["general_understanding", "beginners"],
        "school": "sunni",
    },
    "ibn_ashur": {
        "id": "ibn_ashur",
        "name_ar": "التحرير والتنوير",
        "name_en": "At-Tahrir wat-Tanwir",
        "author_ar": "محمد الطاهر بن عاشور",
        "author_en": "Muhammad al-Tahir ibn Ashur",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1393,
        "death_year_ce": 1973,
        "methodology": TafsirMethodology.LINGUISTIC,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "تفسير لغوي بلاغي معاصر من أعمق التفاسير",
        "description_en": "Linguistic and rhetorical modern tafsir, deeply scholarly",
        "strengths": ["linguistic", "rhetorical", "maqasid"],
        "focus_areas": ["arabic_rhetoric", "purposes_of_sharia", "linguistic_analysis"],
        "school": "sunni_maliki",
    },
    "saadi": {
        "id": "saadi",
        "name_ar": "تيسير الكريم الرحمن",
        "name_en": "Taysir al-Karim al-Rahman (Tafsir al-Sa'di)",
        "author_ar": "عبد الرحمن بن ناصر السعدي",
        "author_en": "Abd al-Rahman ibn Nasir al-Sa'di",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1376,
        "death_year_ce": 1956,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.ARABIC, TafsirLanguage.ENGLISH],
        "description_ar": "تفسير سهل يركز على الهداية والتربية",
        "description_en": "Accessible tafsir focusing on guidance and spiritual education",
        "strengths": ["accessible", "spiritual", "educational"],
        "focus_areas": ["spiritual_guidance", "moral_lessons", "practical_application"],
        "school": "sunni_hanbali",
    },
    "tantawi": {
        "id": "tantawi",
        "name_ar": "التفسير الوسيط",
        "name_en": "Al-Tafsir Al-Wasit",
        "author_ar": "محمد سيد طنطاوي",
        "author_en": "Muhammad Sayyid Tantawi",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1431,
        "death_year_ce": 2010,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.ARABIC],
        "description_ar": "تفسير وسط يجمع بين القديم والحديث",
        "description_en": "Moderate tafsir combining classical and modern approaches",
        "strengths": ["balanced", "scholarly", "contemporary"],
        "focus_areas": ["moderate_interpretation", "contemporary_issues"],
        "school": "sunni",
    },

    # Contemporary Sources (21st century)
    "bayyinah": {
        "id": "bayyinah",
        "name_ar": "بيّنة",
        "name_en": "Bayyinah Quran Studies",
        "author_ar": "نعمان علي خان",
        "author_en": "Nouman Ali Khan",
        "era": TafsirEra.CONTEMPORARY,
        "death_year_hijri": None,
        "death_year_ce": None,
        "methodology": TafsirMethodology.LINGUISTIC,
        "languages_available": [TafsirLanguage.ENGLISH, TafsirLanguage.ARABIC],
        "description_ar": "دراسات لغوية معاصرة للقرآن",
        "description_en": "Contemporary linguistic Quran studies with Arabic word analysis",
        "strengths": ["linguistic", "contemporary", "english_audience"],
        "focus_areas": ["word_analysis", "coherence", "modern_application"],
        "school": "sunni",
    },
    "maariful_quran": {
        "id": "maariful_quran",
        "name_ar": "معارف القرآن",
        "name_en": "Ma'ariful Quran",
        "author_ar": "مفتي محمد شفيع",
        "author_en": "Mufti Muhammad Shafi",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1396,
        "death_year_ce": 1976,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.URDU, TafsirLanguage.ENGLISH],
        "description_ar": "تفسير أردي شامل",
        "description_en": "Comprehensive Urdu tafsir, widely used in South Asia",
        "strengths": ["comprehensive", "hanafi_fiqh", "accessible"],
        "focus_areas": ["fiqh", "practical_guidance", "south_asian_context"],
        "school": "sunni_hanafi",
    },
    "tafsir_hamiduddin": {
        "id": "tafsir_hamiduddin",
        "name_ar": "تدبر القرآن",
        "name_en": "Tadabbur-i-Quran",
        "author_ar": "أمين أحسن إصلاحي",
        "author_en": "Amin Ahsan Islahi",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1418,
        "death_year_ce": 1997,
        "methodology": TafsirMethodology.THEMATIC,
        "languages_available": [TafsirLanguage.URDU, TafsirLanguage.ENGLISH],
        "description_ar": "تفسير يركز على نظم القرآن والتدبر",
        "description_en": "Tafsir focusing on Quranic coherence (nazm) and deep reflection",
        "strengths": ["coherence", "thematic", "analytical"],
        "focus_areas": ["sura_coherence", "thematic_unity", "deep_reflection"],
        "school": "sunni",
    },

    # Multilingual Modern Sources
    "tafsir_french": {
        "id": "tafsir_french",
        "name_ar": "تفسير القرآن بالفرنسية",
        "name_en": "French Quran Commentary",
        "author_ar": "محمد حميد الله",
        "author_en": "Muhammad Hamidullah",
        "era": TafsirEra.MODERN,
        "death_year_hijri": 1423,
        "death_year_ce": 2002,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.FRENCH],
        "description_ar": "ترجمة وتفسير فرنسي",
        "description_en": "French translation and commentary of the Quran",
        "strengths": ["french_audience", "scholarly"],
        "focus_areas": ["translation", "basic_commentary"],
        "school": "sunni",
    },
    "tafsir_indonesian": {
        "id": "tafsir_indonesian",
        "name_ar": "تفسير وزارة الدين الإندونيسية",
        "name_en": "Tafsir Kemenag (Indonesian Ministry of Religion)",
        "author_ar": "وزارة الشؤون الدينية الإندونيسية",
        "author_en": "Indonesian Ministry of Religious Affairs",
        "era": TafsirEra.CONTEMPORARY,
        "death_year_hijri": None,
        "death_year_ce": None,
        "methodology": TafsirMethodology.COMPREHENSIVE,
        "languages_available": [TafsirLanguage.INDONESIAN],
        "description_ar": "تفسير رسمي إندونيسي",
        "description_en": "Official Indonesian government tafsir",
        "strengths": ["accessible", "official", "indonesian_context"],
        "focus_areas": ["general_understanding", "local_application"],
        "school": "sunni_shafii",
    },
}


# =============================================================================
# THEMATIC TAFSIR CATEGORIES
# =============================================================================

TAFSIR_THEMATIC_CATEGORIES = {
    "aqeedah": {
        "ar": "العقيدة والتوحيد",
        "en": "Creed and Monotheism",
        "description_ar": "مباحث التوحيد والإيمان",
        "description_en": "Topics related to belief and faith",
        "recommended_sources": ["ibn_kathir", "tabari", "saadi", "fi_zilal"],
    },
    "fiqh": {
        "ar": "الفقه والأحكام",
        "en": "Jurisprudence and Rulings",
        "description_ar": "آيات الأحكام والتشريع",
        "description_en": "Verses related to Islamic law",
        "recommended_sources": ["qurtubi", "maariful_quran", "ibn_kathir"],
    },
    "linguistic": {
        "ar": "اللغة والبلاغة",
        "en": "Language and Rhetoric",
        "description_ar": "الإعجاز اللغوي والبلاغي",
        "description_en": "Linguistic and rhetorical analysis",
        "recommended_sources": ["ibn_ashur", "tabari", "bayyinah"],
    },
    "spiritual": {
        "ar": "الروحانية والتزكية",
        "en": "Spirituality and Purification",
        "description_ar": "التربية الروحية وتزكية النفس",
        "description_en": "Spiritual growth and self-purification",
        "recommended_sources": ["sha_rawi", "fi_zilal", "saadi"],
    },
    "stories": {
        "ar": "القصص والعبر",
        "en": "Stories and Lessons",
        "description_ar": "قصص الأنبياء والأمم",
        "description_en": "Prophetic stories and lessons",
        "recommended_sources": ["ibn_kathir", "tabari", "sha_rawi"],
    },
    "scientific": {
        "ar": "الإعجاز العلمي",
        "en": "Scientific Reflections",
        "description_ar": "التأملات العلمية في القرآن",
        "description_en": "Scientific reflections in the Quran",
        "recommended_sources": ["tantawi", "sha_rawi"],
    },
    "coherence": {
        "ar": "نظم القرآن وترابطه",
        "en": "Quranic Coherence",
        "description_ar": "الترابط الموضوعي بين الآيات والسور",
        "description_en": "Thematic connections between verses and suras",
        "recommended_sources": ["tafsir_hamiduddin", "ibn_ashur", "bayyinah"],
    },
    "contemporary": {
        "ar": "القضايا المعاصرة",
        "en": "Contemporary Issues",
        "description_ar": "تطبيق القرآن على الواقع المعاصر",
        "description_en": "Applying Quran to modern life",
        "recommended_sources": ["fi_zilal", "tantawi", "bayyinah", "sha_rawi"],
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TafsirSourceInfo:
    """Information about a Tafsir source."""
    id: str
    name_ar: str
    name_en: str
    author_ar: str
    author_en: str
    era: TafsirEra
    methodology: TafsirMethodology
    languages: List[str]
    description_ar: str
    description_en: str
    strengths: List[str]
    focus_areas: List[str]
    is_available: bool = False  # In database


@dataclass
class TafsirComparison:
    """Comparison of multiple Tafsir interpretations."""
    verse_reference: str
    verse_text_ar: str
    interpretations: List[Dict[str, Any]]
    common_themes: List[str]
    unique_insights: Dict[str, List[str]]


@dataclass
class ThematicTafsir:
    """Tafsir content grouped by theme."""
    theme_id: str
    theme_ar: str
    theme_en: str
    sources_used: List[str]
    content_entries: List[Dict[str, Any]]
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None


# =============================================================================
# MODERN TAFSIR SERVICE
# =============================================================================

class ModernTafsirService:
    """
    Service for managing and querying modern Tafsir sources.

    Provides:
    - Catalog browsing and filtering
    - Source recommendations based on study goals
    - Multilingual Tafsir access
    - Thematic Tafsir grouping
    """

    def __init__(self):
        self._catalog = TAFSIR_CATALOG
        self._thematic_categories = TAFSIR_THEMATIC_CATEGORIES

    async def get_all_sources(
        self,
        era: Optional[TafsirEra] = None,
        language: Optional[TafsirLanguage] = None,
        methodology: Optional[TafsirMethodology] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[TafsirSourceInfo]:
        """
        Get all Tafsir sources with optional filtering.

        Arabic: الحصول على جميع مصادر التفسير
        """
        # Get available sources from DB if session provided
        available_ids = set()
        if session:
            from app.models.tafseer import TafseerSource
            result = await session.execute(select(TafseerSource.id))
            available_ids = {r[0] for r in result.all()}

        sources = []
        for source_id, data in self._catalog.items():
            # Apply filters
            if era and data.get("era") != era:
                continue
            if language and language not in data.get("languages_available", []):
                continue
            if methodology and data.get("methodology") != methodology:
                continue

            sources.append(TafsirSourceInfo(
                id=source_id,
                name_ar=data["name_ar"],
                name_en=data["name_en"],
                author_ar=data["author_ar"],
                author_en=data["author_en"],
                era=data["era"],
                methodology=data["methodology"],
                languages=[l.value for l in data["languages_available"]],
                description_ar=data["description_ar"],
                description_en=data["description_en"],
                strengths=data["strengths"],
                focus_areas=data["focus_areas"],
                is_available=source_id in available_ids or f"{source_id}_ar" in available_ids or f"{source_id}_en" in available_ids,
            ))

        return sources

    async def get_source_by_id(self, source_id: str) -> Optional[TafsirSourceInfo]:
        """Get a specific Tafsir source by ID."""
        data = self._catalog.get(source_id)
        if not data:
            return None

        return TafsirSourceInfo(
            id=source_id,
            name_ar=data["name_ar"],
            name_en=data["name_en"],
            author_ar=data["author_ar"],
            author_en=data["author_en"],
            era=data["era"],
            methodology=data["methodology"],
            languages=[l.value for l in data["languages_available"]],
            description_ar=data["description_ar"],
            description_en=data["description_en"],
            strengths=data["strengths"],
            focus_areas=data["focus_areas"],
            is_available=False,
        )

    async def get_recommended_sources(
        self,
        study_goal: str,
        language_preference: Optional[TafsirLanguage] = None,
        themes_of_interest: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recommended Tafsir sources based on study goals.

        Arabic: الحصول على مصادر التفسير الموصى بها
        """
        recommendations = []

        # Map study goals to source characteristics
        goal_mapping = {
            "memorization": ["accessible", "simple", "beginner_friendly"],
            "comprehension": ["comprehensive", "accessible", "educational"],
            "research": ["scholarly", "linguistic", "comprehensive"],
            "reflection": ["spiritual", "social_reform", "practical"],
        }

        preferred_strengths = goal_mapping.get(study_goal, ["comprehensive"])

        for source_id, data in self._catalog.items():
            # Check language availability
            if language_preference:
                if language_preference not in data.get("languages_available", []):
                    continue

            # Calculate relevance score
            score = 0.0
            source_strengths = data.get("strengths", [])

            # Match strengths
            for strength in preferred_strengths:
                if strength in source_strengths:
                    score += 0.3

            # Match themes
            if themes_of_interest:
                source_focus = data.get("focus_areas", [])
                for theme in themes_of_interest:
                    if theme in source_focus:
                        score += 0.2
                    # Check thematic categories
                    for cat_id, cat_data in self._thematic_categories.items():
                        if theme in cat_id and source_id in cat_data.get("recommended_sources", []):
                            score += 0.15

            # Era preference for different goals
            if study_goal == "reflection" and data.get("era") in [TafsirEra.MODERN, TafsirEra.CONTEMPORARY]:
                score += 0.2
            elif study_goal == "research" and data.get("era") == TafsirEra.CLASSICAL:
                score += 0.2

            if score > 0:
                recommendations.append({
                    "source_id": source_id,
                    "name_ar": data["name_ar"],
                    "name_en": data["name_en"],
                    "author_en": data["author_en"],
                    "era": data["era"].value,
                    "methodology": data["methodology"].value,
                    "relevance_score": round(score, 3),
                    "reason_ar": self._get_recommendation_reason_ar(data, study_goal),
                    "reason_en": self._get_recommendation_reason_en(data, study_goal),
                })

        # Sort by relevance
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:limit]

    def _get_recommendation_reason_ar(self, data: Dict, goal: str) -> str:
        """Generate Arabic recommendation reason."""
        reasons = {
            "memorization": "مناسب للحفظ والفهم الأساسي",
            "comprehension": "يوفر شرحاً شاملاً للآيات",
            "research": "مصدر علمي موثق للبحث",
            "reflection": "يساعد على التدبر والتأمل",
        }
        return reasons.get(goal, "مصدر موصى به")

    def _get_recommendation_reason_en(self, data: Dict, goal: str) -> str:
        """Generate English recommendation reason."""
        reasons = {
            "memorization": "Suitable for memorization and basic understanding",
            "comprehension": "Provides comprehensive verse explanations",
            "research": "Scholarly authenticated source for research",
            "reflection": "Helps with deep reflection and contemplation",
        }
        return reasons.get(goal, "Recommended source")

    def get_thematic_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all thematic Tafsir categories."""
        return self._thematic_categories

    async def get_sources_by_theme(
        self,
        theme_category: str,
        session: Optional[AsyncSession] = None,
    ) -> List[TafsirSourceInfo]:
        """Get recommended sources for a specific theme."""
        category = self._thematic_categories.get(theme_category)
        if not category:
            return []

        recommended_ids = category.get("recommended_sources", [])
        sources = []

        for source_id in recommended_ids:
            source = await self.get_source_by_id(source_id)
            if source:
                sources.append(source)

        return sources

    async def compare_interpretations(
        self,
        sura_no: int,
        aya_no: int,
        source_ids: List[str],
        session: AsyncSession,
    ) -> TafsirComparison:
        """
        Compare interpretations from multiple sources for a verse.

        Arabic: مقارنة تفسيرات مختلفة للآية الواحدة
        """
        from app.models.quran import QuranVerse
        from app.models.tafseer import TafseerChunk, TafseerSource

        # Get verse
        verse_result = await session.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no == aya_no
            )
        )
        verse = verse_result.scalar_one_or_none()
        if not verse:
            return TafsirComparison(
                verse_reference=f"{sura_no}:{aya_no}",
                verse_text_ar="",
                interpretations=[],
                common_themes=[],
                unique_insights={},
            )

        # Get Tafsir chunks
        interpretations = []
        for source_id in source_ids:
            # Try both with and without language suffix
            for sid in [source_id, f"{source_id}_ar", f"{source_id}_en"]:
                chunk_result = await session.execute(
                    select(TafseerChunk).where(
                        TafseerChunk.source_id == sid,
                        TafseerChunk.verse_start_id <= verse.id,
                        TafseerChunk.verse_end_id >= verse.id,
                    )
                )
                chunk = chunk_result.scalar_one_or_none()
                if chunk:
                    source_info = self._catalog.get(source_id, {})
                    interpretations.append({
                        "source_id": source_id,
                        "source_name_ar": source_info.get("name_ar", sid),
                        "source_name_en": source_info.get("name_en", sid),
                        "author_en": source_info.get("author_en", ""),
                        "era": source_info.get("era", TafsirEra.CLASSICAL).value if source_info.get("era") else "unknown",
                        "content_ar": chunk.content_ar,
                        "content_en": chunk.content_en,
                        "methodology": source_info.get("methodology", TafsirMethodology.COMPREHENSIVE).value if source_info.get("methodology") else "unknown",
                    })
                    break

        return TafsirComparison(
            verse_reference=f"{sura_no}:{aya_no}",
            verse_text_ar=verse.text_uthmani,
            interpretations=interpretations,
            common_themes=[],  # Could be analyzed with NLP
            unique_insights={},
        )

    def get_methodology_info(self, methodology: TafsirMethodology) -> Dict[str, str]:
        """Get information about a Tafsir methodology."""
        methodology_info = {
            TafsirMethodology.BIL_MATHUR: {
                "ar": "تفسير بالمأثور",
                "en": "Tafsir based on narrations",
                "description_ar": "يعتمد على الأحاديث وأقوال الصحابة والتابعين",
                "description_en": "Relies on hadith and statements of companions",
            },
            TafsirMethodology.BIL_RAY: {
                "ar": "تفسير بالرأي",
                "en": "Tafsir based on reasoning",
                "description_ar": "يعتمد على الاجتهاد والتحليل العقلي",
                "description_en": "Relies on scholarly reasoning and analysis",
            },
            TafsirMethodology.LINGUISTIC: {
                "ar": "تفسير لغوي",
                "en": "Linguistic Tafsir",
                "description_ar": "يركز على تحليل اللغة والبلاغة",
                "description_en": "Focuses on language and rhetorical analysis",
            },
            TafsirMethodology.THEMATIC: {
                "ar": "تفسير موضوعي",
                "en": "Thematic Tafsir",
                "description_ar": "يجمع الآيات حسب الموضوع",
                "description_en": "Groups verses by theme",
            },
            TafsirMethodology.SCIENTIFIC: {
                "ar": "تفسير علمي",
                "en": "Scientific Tafsir",
                "description_ar": "يربط بين القرآن والعلم الحديث",
                "description_en": "Connects Quran with modern science",
            },
            TafsirMethodology.SOCIAL: {
                "ar": "تفسير اجتماعي",
                "en": "Social Tafsir",
                "description_ar": "يركز على التطبيق الاجتماعي والإصلاح",
                "description_en": "Focuses on social application and reform",
            },
            TafsirMethodology.COMPREHENSIVE: {
                "ar": "تفسير شامل",
                "en": "Comprehensive Tafsir",
                "description_ar": "يجمع بين عدة مناهج",
                "description_en": "Combines multiple methodologies",
            },
        }
        return methodology_info.get(methodology, {})

    async def get_multilingual_tafsir(
        self,
        sura_no: int,
        aya_no: int,
        languages: List[TafsirLanguage],
        session: AsyncSession,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get Tafsir in multiple languages for a verse.

        Arabic: الحصول على التفسير بلغات متعددة
        """
        from app.models.quran import QuranVerse
        from app.models.tafseer import TafseerChunk, TafseerSource

        # Get verse
        verse_result = await session.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no == aya_no
            )
        )
        verse = verse_result.scalar_one_or_none()
        if not verse:
            return {lang.value: [] for lang in languages}

        # Get all chunks for this verse
        chunks_result = await session.execute(
            select(TafseerChunk, TafseerSource).join(
                TafseerSource, TafseerChunk.source_id == TafseerSource.id
            ).where(
                TafseerChunk.verse_start_id <= verse.id,
                TafseerChunk.verse_end_id >= verse.id,
            )
        )

        results = {lang.value: [] for lang in languages}

        for chunk, source in chunks_result.all():
            source_info = self._catalog.get(source.id.replace("_ar", "").replace("_en", ""), {})

            for lang in languages:
                content = None
                if lang == TafsirLanguage.ARABIC and chunk.content_ar:
                    content = chunk.content_ar
                elif lang == TafsirLanguage.ENGLISH and chunk.content_en:
                    content = chunk.content_en

                if content:
                    results[lang.value].append({
                        "source_id": source.id,
                        "source_name": source.name_en if lang == TafsirLanguage.ENGLISH else source.name_ar,
                        "author": source.author_en if lang == TafsirLanguage.ENGLISH else source.author_ar,
                        "content": content,
                        "era": source.era or source_info.get("era", TafsirEra.CLASSICAL).value,
                    })

        return results

    def get_era_info(self, era: TafsirEra) -> Dict[str, str]:
        """Get information about a Tafsir era."""
        era_info = {
            TafsirEra.CLASSICAL: {
                "ar": "التفاسير الكلاسيكية",
                "en": "Classical Tafsirs",
                "period_ar": "قبل 1900م",
                "period_en": "Before 1900 CE",
                "description_ar": "تفاسير العلماء المتقدمين التي تشكل الأساس لفهم القرآن",
                "description_en": "Foundational scholarly works forming the basis of Quranic understanding",
            },
            TafsirEra.MODERN: {
                "ar": "التفاسير الحديثة",
                "en": "Modern Tafsirs",
                "period_ar": "1900-2000م",
                "period_en": "1900-2000 CE",
                "description_ar": "تفاسير القرن العشرين التي تجمع بين التراث والمعاصرة",
                "description_en": "20th century works combining tradition with contemporary approaches",
            },
            TafsirEra.CONTEMPORARY: {
                "ar": "التفاسير المعاصرة",
                "en": "Contemporary Tafsirs",
                "period_ar": "2000م وما بعدها",
                "period_en": "2000 CE onwards",
                "description_ar": "تفاسير حديثة تستخدم وسائل التعليم المعاصرة",
                "description_en": "Recent works using modern educational methods",
            },
        }
        return era_info.get(era, {})

    async def search_tafsir_by_scholar(
        self,
        scholar_id: str,
        keyword: Optional[str] = None,
        sura_no: Optional[int] = None,
        limit: int = 20,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Search Tafsir content by a specific scholar.

        Arabic: البحث في تفسير عالم معين
        """
        source_info = self._catalog.get(scholar_id)
        if not source_info:
            return {"error": f"Scholar '{scholar_id}' not found", "results": []}

        results = []

        if session:
            from app.models.tafseer import TafseerChunk, TafseerSource

            # Build query
            query = select(TafseerChunk).where(
                TafseerChunk.source_id.in_([scholar_id, f"{scholar_id}_ar", f"{scholar_id}_en"])
            )

            if sura_no:
                query = query.where(TafseerChunk.sura_no == sura_no)

            query = query.limit(limit)
            chunks_result = await session.execute(query)
            chunks = chunks_result.scalars().all()

            for chunk in chunks:
                content = chunk.content_ar or chunk.content_en or ""

                # Filter by keyword if provided
                if keyword and keyword.lower() not in content.lower():
                    continue

                # Create preview
                preview = content[:500] + "..." if len(content) > 500 else content

                results.append({
                    "chunk_id": chunk.chunk_id,
                    "sura_no": chunk.sura_no,
                    "aya_range": f"{chunk.aya_start}-{chunk.aya_end}" if chunk.aya_end != chunk.aya_start else str(chunk.aya_start),
                    "preview_ar": chunk.content_ar[:300] if chunk.content_ar else None,
                    "preview_en": chunk.content_en[:300] if chunk.content_en else None,
                })

        return {
            "scholar_id": scholar_id,
            "scholar_name_ar": source_info["name_ar"],
            "scholar_name_en": source_info["name_en"],
            "author_ar": source_info["author_ar"],
            "author_en": source_info["author_en"],
            "methodology": source_info["methodology"].value,
            "results": results,
            "count": len(results),
        }

    def get_scholars_by_focus(self, focus_area: str) -> List[Dict[str, Any]]:
        """
        Get scholars specializing in a specific focus area.

        Arabic: الحصول على العلماء المتخصصين في مجال معين
        """
        scholars = []
        for source_id, data in self._catalog.items():
            if focus_area in data.get("focus_areas", []):
                scholars.append({
                    "id": source_id,
                    "name_ar": data["name_ar"],
                    "name_en": data["name_en"],
                    "author_en": data["author_en"],
                    "methodology": data["methodology"].value,
                    "era": data["era"].value,
                    "focus_areas": data["focus_areas"],
                })
        return scholars

    def get_scholar_profile(self, scholar_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive profile of a Tafsir scholar.

        Arabic: الحصول على ملف شامل لمفسر
        """
        data = self._catalog.get(scholar_id)
        if not data:
            return None

        return {
            "id": scholar_id,
            "name_ar": data["name_ar"],
            "name_en": data["name_en"],
            "author_ar": data["author_ar"],
            "author_en": data["author_en"],
            "era": data["era"].value,
            "death_year_hijri": data.get("death_year_hijri"),
            "death_year_ce": data.get("death_year_ce"),
            "methodology": data["methodology"].value,
            "methodology_info": self.get_methodology_info(data["methodology"]),
            "languages": [l.value for l in data["languages_available"]],
            "description_ar": data["description_ar"],
            "description_en": data["description_en"],
            "strengths": data["strengths"],
            "focus_areas": data["focus_areas"],
            "school": data.get("school", "sunni"),
            # Get related scholars
            "related_scholars": self._get_related_scholars(scholar_id),
        }

    def _get_related_scholars(self, scholar_id: str) -> List[Dict[str, str]]:
        """Get scholars with similar methodology or focus."""
        data = self._catalog.get(scholar_id)
        if not data:
            return []

        related = []
        for other_id, other_data in self._catalog.items():
            if other_id == scholar_id:
                continue

            # Check methodology match
            if other_data["methodology"] == data["methodology"]:
                related.append({
                    "id": other_id,
                    "name_en": other_data["name_en"],
                    "relation": "same_methodology",
                })
            # Check focus overlap
            elif set(other_data.get("focus_areas", [])) & set(data.get("focus_areas", [])):
                related.append({
                    "id": other_id,
                    "name_en": other_data["name_en"],
                    "relation": "similar_focus",
                })

        return related[:5]

    async def get_tafsir_for_study_goal(
        self,
        sura_no: int,
        aya_no: int,
        study_goal: str,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get Tafsir content tailored to a specific study goal.

        Arabic: الحصول على التفسير المناسب لهدف الدراسة
        """
        from app.models.quran import QuranVerse
        from app.models.tafseer import TafseerChunk, TafseerSource

        # Map goals to preferred sources
        goal_sources = {
            "memorization": ["muyassar", "jalalayn", "saadi"],
            "comprehension": ["ibn_kathir", "saadi", "sha_rawi"],
            "research": ["tabari", "ibn_ashur", "qurtubi"],
            "reflection": ["fi_zilal", "sha_rawi", "saadi"],
        }

        preferred_sources = goal_sources.get(study_goal, ["ibn_kathir", "saadi"])

        # Get verse
        verse_result = await session.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no == aya_no
            )
        )
        verse = verse_result.scalar_one_or_none()
        if not verse:
            return {"error": "Verse not found", "tafsir": []}

        tafsir_results = []

        for source_id in preferred_sources:
            for sid in [source_id, f"{source_id}_ar", f"{source_id}_en"]:
                chunk_result = await session.execute(
                    select(TafseerChunk).where(
                        TafseerChunk.source_id == sid,
                        TafseerChunk.verse_start_id <= verse.id,
                        TafseerChunk.verse_end_id >= verse.id,
                    )
                )
                chunk = chunk_result.scalar_one_or_none()
                if chunk:
                    source_info = self._catalog.get(source_id, {})
                    tafsir_results.append({
                        "source_id": source_id,
                        "source_name_ar": source_info.get("name_ar", sid),
                        "source_name_en": source_info.get("name_en", sid),
                        "author_en": source_info.get("author_en", ""),
                        "why_recommended": self._get_goal_recommendation_reason(source_id, study_goal),
                        "content_ar": chunk.content_ar,
                        "content_en": chunk.content_en,
                    })
                    break

        return {
            "verse_reference": f"{sura_no}:{aya_no}",
            "verse_text": verse.text_uthmani,
            "study_goal": study_goal,
            "tafsir": tafsir_results,
            "count": len(tafsir_results),
        }

    def _get_goal_recommendation_reason(self, source_id: str, goal: str) -> Dict[str, str]:
        """Get reason why this source is recommended for the goal."""
        reasons = {
            "memorization": {
                "muyassar": {"ar": "تفسير مختصر سهل الفهم", "en": "Concise and easy to understand"},
                "jalalayn": {"ar": "يركز على معاني الألفاظ", "en": "Focuses on word meanings"},
                "saadi": {"ar": "شرح واضح ومباشر", "en": "Clear and direct explanation"},
            },
            "comprehension": {
                "ibn_kathir": {"ar": "شرح شامل بالأحاديث والآثار", "en": "Comprehensive with hadith support"},
                "saadi": {"ar": "يربط الآيات بالحياة العملية", "en": "Connects verses to practical life"},
                "sha_rawi": {"ar": "أسلوب سهل وروحاني", "en": "Easy and spiritual style"},
            },
            "research": {
                "tabari": {"ar": "أم التفاسير بجميع الأقوال", "en": "Mother of tafsirs with all opinions"},
                "ibn_ashur": {"ar": "تحليل لغوي وبلاغي عميق", "en": "Deep linguistic and rhetorical analysis"},
                "qurtubi": {"ar": "تفصيل الأحكام الفقهية", "en": "Detailed jurisprudential rulings"},
            },
            "reflection": {
                "fi_zilal": {"ar": "تدبر روحي وتطبيق معاصر", "en": "Spiritual reflection and contemporary application"},
                "sha_rawi": {"ar": "تأملات قلبية ولغوية", "en": "Heartfelt and linguistic contemplations"},
                "saadi": {"ar": "دروس تربوية وإيمانية", "en": "Educational and faith-building lessons"},
            },
        }
        default = {"ar": "مصدر موثوق", "en": "Reliable source"}
        return reasons.get(goal, {}).get(source_id, default)

    async def get_interpretation_highlights(
        self,
        sura_no: int,
        aya_no: int,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get key highlights and differences from multiple Tafsir interpretations.

        Arabic: الحصول على أبرز النقاط والاختلافات بين التفاسير
        """
        from app.models.quran import QuranVerse
        from app.models.tafseer import TafseerChunk, TafseerSource

        # Get verse
        verse_result = await session.execute(
            select(QuranVerse).where(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no == aya_no
            )
        )
        verse = verse_result.scalar_one_or_none()
        if not verse:
            return {"error": "Verse not found"}

        # Get all chunks for this verse
        chunks_result = await session.execute(
            select(TafseerChunk, TafseerSource).join(
                TafseerSource, TafseerChunk.source_id == TafseerSource.id
            ).where(
                TafseerChunk.verse_start_id <= verse.id,
                TafseerChunk.verse_end_id >= verse.id,
            )
        )

        interpretations = []
        for chunk, source in chunks_result.all():
            base_id = source.id.replace("_ar", "").replace("_en", "")
            source_info = self._catalog.get(base_id, {})

            interpretations.append({
                "source_id": base_id,
                "source_name_en": source_info.get("name_en", source.name_en),
                "methodology": source_info.get("methodology", TafsirMethodology.COMPREHENSIVE).value if source_info else source.methodology,
                "era": source_info.get("era", TafsirEra.CLASSICAL).value if source_info else source.era,
                "content_preview_ar": (chunk.content_ar or "")[:200],
                "content_preview_en": (chunk.content_en or "")[:200],
                "focus_areas": source_info.get("focus_areas", []),
            })

        # Group by methodology
        methodology_groups = {}
        for interp in interpretations:
            method = interp["methodology"]
            if method not in methodology_groups:
                methodology_groups[method] = []
            methodology_groups[method].append(interp["source_name_en"])

        # Group by era
        era_groups = {}
        for interp in interpretations:
            era = interp["era"]
            if era not in era_groups:
                era_groups[era] = []
            era_groups[era].append(interp["source_name_en"])

        return {
            "verse_reference": f"{sura_no}:{aya_no}",
            "verse_text": verse.text_uthmani,
            "total_sources": len(interpretations),
            "interpretations": interpretations,
            "by_methodology": methodology_groups,
            "by_era": era_groups,
            "comparison_insights": {
                "classical_count": len(era_groups.get("classical", [])),
                "modern_count": len(era_groups.get("modern", [])),
                "contemporary_count": len(era_groups.get("contemporary", [])),
            },
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

modern_tafsir_service = ModernTafsirService()
