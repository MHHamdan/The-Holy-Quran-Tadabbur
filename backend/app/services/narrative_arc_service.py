"""
Cross-Sura Narrative Arc Exploration Service.

Enables exploration of narrative arcs across multiple suras,
tracking thematic evolution and story continuity.

Features:
1. Prophet story arcs spanning multiple suras
2. Thematic evolution tracking
3. Chronological story sequencing
4. Cross-reference mapping
5. Story completion tracking

Arabic: خدمة استكشاف الأقواس السردية عبر السور
"""

import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class NarrativeType(str, Enum):
    """Types of narratives in the Quran."""
    PROPHET_STORY = "prophet_story"
    HISTORICAL_EVENT = "historical_event"
    DIVINE_DIALOGUE = "divine_dialogue"
    PARABLE = "parable"
    COMMUNITY_STORY = "community_story"
    COSMIC_EVENT = "cosmic_event"
    ESCHATOLOGICAL = "eschatological"


class ThemeEvolution(str, Enum):
    """How a theme evolves across suras."""
    INTRODUCED = "introduced"
    DEVELOPED = "developed"
    EMPHASIZED = "emphasized"
    CONCLUDED = "concluded"
    REFERENCED = "referenced"


class StoryPhase(str, Enum):
    """Phases of a narrative arc."""
    INTRODUCTION = "introduction"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"
    AFTERMATH = "aftermath"


@dataclass
class NarrativeSegment:
    """A segment of a narrative arc in a specific sura."""
    sura_no: int
    verse_range: str  # e.g., "1-20"
    phase: StoryPhase
    key_events: List[str]
    themes: List[str]
    lessons: List[str]
    intensity: float  # 0-1 scale


@dataclass
class NarrativeArc:
    """Complete narrative arc across suras."""
    arc_id: str
    name_ar: str
    name_en: str
    narrative_type: NarrativeType
    main_character: str
    segments: List[NarrativeSegment]
    total_verses: int
    key_themes: List[str]
    moral_lessons: List[str]
    chronological_order: List[int]  # Sura numbers in story order


@dataclass
class ThematicProgression:
    """How a theme progresses across suras."""
    theme_id: str
    theme_name_ar: str
    theme_name_en: str
    first_appearance: Dict[str, Any]
    evolution_points: List[Dict[str, Any]]
    peak_intensity: Dict[str, Any]
    related_themes: List[str]


# =============================================================================
# NARRATIVE ARC DATA
# =============================================================================

NARRATIVE_ARCS = {
    "musa_story": {
        "name_ar": "قصة موسى عليه السلام",
        "name_en": "Story of Moses (Musa)",
        "type": NarrativeType.PROPHET_STORY,
        "main_character": "موسى",
        "segments": [
            {
                "sura_no": 28,
                "verse_range": "3-43",
                "phase": StoryPhase.INTRODUCTION,
                "key_events": ["Birth", "Rescue from river", "Upbringing in palace", "Killing the man", "Flight to Madyan"],
                "themes": ["divine_protection", "divine_plan", "trust_in_allah"],
                "lessons_ar": ["الله يحفظ عباده", "خطة الله فوق كل خطة"],
                "lessons_en": ["Allah protects His servants", "Allah's plan supersedes all plans"],
                "intensity": 0.7,
            },
            {
                "sura_no": 20,
                "verse_range": "9-98",
                "phase": StoryPhase.RISING_ACTION,
                "key_events": ["Divine call at the valley", "Staff miracle", "Confrontation with Pharaoh", "Magic contest"],
                "themes": ["prophethood", "miracles", "faith_vs_tyranny"],
                "lessons_ar": ["الله يختار من يشاء", "المعجزات تثبت الحق"],
                "lessons_en": ["Allah chooses whom He wills", "Miracles confirm the truth"],
                "intensity": 0.85,
            },
            {
                "sura_no": 26,
                "verse_range": "10-68",
                "phase": StoryPhase.CLIMAX,
                "key_events": ["Exodus", "Pursuit by Pharaoh", "Parting of the sea", "Drowning of Pharaoh"],
                "themes": ["divine_victory", "liberation", "punishment_of_tyrants"],
                "lessons_ar": ["نصر الله قريب", "عاقبة الظلم وخيمة"],
                "lessons_en": ["Allah's victory is near", "Tyranny leads to destruction"],
                "intensity": 1.0,
            },
            {
                "sura_no": 7,
                "verse_range": "138-171",
                "phase": StoryPhase.FALLING_ACTION,
                "key_events": ["Journey in desert", "Golden calf incident", "Tablets from Allah", "Repentance"],
                "themes": ["testing", "human_weakness", "divine_forgiveness"],
                "lessons_ar": ["الفتنة قد تأتي بعد النصر", "التوبة تفتح أبواب الرحمة"],
                "lessons_en": ["Trials may come after victory", "Repentance opens doors of mercy"],
                "intensity": 0.75,
            },
            {
                "sura_no": 2,
                "verse_range": "40-74",
                "phase": StoryPhase.RESOLUTION,
                "key_events": ["Commandments", "Cow sacrifice", "Lessons for Bani Israel"],
                "themes": ["obedience", "following_prophets", "consequences"],
                "lessons_ar": ["طاعة الله واجبة", "اتباع الأنبياء سبيل النجاة"],
                "lessons_en": ["Obedience to Allah is obligatory", "Following prophets is the path to salvation"],
                "intensity": 0.6,
            },
        ],
        "total_verses": 250,
        "key_themes": ["liberation", "faith", "patience", "divine_plan", "leadership"],
        "moral_lessons": [
            {"ar": "الصبر على الابتلاء", "en": "Patience during trials"},
            {"ar": "الثقة في خطة الله", "en": "Trust in Allah's plan"},
            {"ar": "مقاومة الظلم واجب", "en": "Resisting oppression is a duty"},
            {"ar": "القيادة بالعدل", "en": "Leadership with justice"},
        ],
    },
    "ibrahim_story": {
        "name_ar": "قصة إبراهيم عليه السلام",
        "name_en": "Story of Abraham (Ibrahim)",
        "type": NarrativeType.PROPHET_STORY,
        "main_character": "إبراهيم",
        "segments": [
            {
                "sura_no": 6,
                "verse_range": "74-83",
                "phase": StoryPhase.INTRODUCTION,
                "key_events": ["Search for truth", "Observation of stars, moon, sun", "Rejection of idols"],
                "themes": ["seeking_truth", "monotheism", "rational_faith"],
                "lessons_ar": ["البحث عن الحقيقة", "استخدام العقل في الإيمان"],
                "lessons_en": ["Seeking the truth", "Using reason in faith"],
                "intensity": 0.8,
            },
            {
                "sura_no": 21,
                "verse_range": "51-70",
                "phase": StoryPhase.RISING_ACTION,
                "key_events": ["Breaking idols", "Confrontation with people", "Thrown into fire", "Saved by Allah"],
                "themes": ["courage", "challenging_falsehood", "divine_protection"],
                "lessons_ar": ["الشجاعة في الحق", "الله ينصر المؤمنين"],
                "lessons_en": ["Courage in truth", "Allah supports believers"],
                "intensity": 0.95,
            },
            {
                "sura_no": 37,
                "verse_range": "99-113",
                "phase": StoryPhase.CLIMAX,
                "key_events": ["Migration", "Prayer for son", "Dream of sacrifice", "Test of sacrificing Ismail", "Ransom with ram"],
                "themes": ["submission", "sacrifice", "ultimate_test"],
                "lessons_ar": ["التسليم لأمر الله", "البلاء بقدر الإيمان"],
                "lessons_en": ["Submission to Allah's command", "Tests proportional to faith"],
                "intensity": 1.0,
            },
            {
                "sura_no": 2,
                "verse_range": "124-141",
                "phase": StoryPhase.RESOLUTION,
                "key_events": ["Building Kaaba", "Prayer for Mecca", "Establishing pilgrimage", "Legacy for descendants"],
                "themes": ["legacy", "worship", "nation_building"],
                "lessons_ar": ["بناء الإرث الصالح", "العبادة تبقى"],
                "lessons_en": ["Building righteous legacy", "Worship endures"],
                "intensity": 0.8,
            },
        ],
        "total_verses": 100,
        "key_themes": ["monotheism", "sacrifice", "submission", "legacy", "courage"],
        "moral_lessons": [
            {"ar": "التوحيد أساس الإيمان", "en": "Monotheism is the foundation of faith"},
            {"ar": "التضحية في سبيل الله", "en": "Sacrifice for Allah's sake"},
            {"ar": "بناء الإرث للأجيال", "en": "Building legacy for generations"},
        ],
    },
    "yusuf_story": {
        "name_ar": "قصة يوسف عليه السلام",
        "name_en": "Story of Joseph (Yusuf)",
        "type": NarrativeType.PROPHET_STORY,
        "main_character": "يوسف",
        "segments": [
            {
                "sura_no": 12,
                "verse_range": "4-18",
                "phase": StoryPhase.INTRODUCTION,
                "key_events": ["Dream of eleven stars", "Brothers' jealousy", "Thrown into well"],
                "themes": ["jealousy", "divine_dreams", "family_conflict"],
                "lessons_ar": ["الحسد يفسد العلاقات", "الرؤيا من الله"],
                "lessons_en": ["Jealousy corrupts relationships", "Dreams can be from Allah"],
                "intensity": 0.7,
            },
            {
                "sura_no": 12,
                "verse_range": "19-35",
                "phase": StoryPhase.RISING_ACTION,
                "key_events": ["Sold as slave", "House of Aziz", "Temptation by Zulaykha", "Imprisonment"],
                "themes": ["chastity", "patience", "trust_in_allah"],
                "lessons_ar": ["العفة في زمن الفتن", "الصبر على المحن"],
                "lessons_en": ["Chastity in times of temptation", "Patience during hardships"],
                "intensity": 0.85,
            },
            {
                "sura_no": 12,
                "verse_range": "36-57",
                "phase": StoryPhase.CLIMAX,
                "key_events": ["Prison dreams", "King's dream", "Release from prison", "Appointed over treasures"],
                "themes": ["wisdom", "divine_plan", "vindication"],
                "lessons_ar": ["الله يرفع من يشاء", "الصدق منجاة"],
                "lessons_en": ["Allah elevates whom He wills", "Truthfulness saves"],
                "intensity": 1.0,
            },
            {
                "sura_no": 12,
                "verse_range": "58-101",
                "phase": StoryPhase.RESOLUTION,
                "key_events": ["Brothers come for grain", "Recognition", "Family reunion", "Dream fulfilled"],
                "themes": ["forgiveness", "family_reconciliation", "dream_fulfillment"],
                "lessons_ar": ["العفو عند المقدرة", "وعد الله حق"],
                "lessons_en": ["Forgiveness when able", "Allah's promise is true"],
                "intensity": 0.9,
            },
        ],
        "total_verses": 111,
        "key_themes": ["patience", "chastity", "forgiveness", "divine_plan", "dreams"],
        "moral_lessons": [
            {"ar": "الصبر مفتاح الفرج", "en": "Patience is the key to relief"},
            {"ar": "العفاف في زمن الشهوات", "en": "Modesty in times of desires"},
            {"ar": "المغفرة أعلى من الانتقام", "en": "Forgiveness is higher than revenge"},
        ],
    },
    "nuh_story": {
        "name_ar": "قصة نوح عليه السلام",
        "name_en": "Story of Noah (Nuh)",
        "type": NarrativeType.PROPHET_STORY,
        "main_character": "نوح",
        "segments": [
            {
                "sura_no": 71,
                "verse_range": "1-28",
                "phase": StoryPhase.INTRODUCTION,
                "key_events": ["Call to worship Allah", "Long period of calling", "People's rejection"],
                "themes": ["patience_in_dawah", "perseverance", "rejection"],
                "lessons_ar": ["الدعوة تحتاج صبرا", "المثابرة رغم الرفض"],
                "lessons_en": ["Calling to truth requires patience", "Perseverance despite rejection"],
                "intensity": 0.7,
            },
            {
                "sura_no": 11,
                "verse_range": "25-49",
                "phase": StoryPhase.RISING_ACTION,
                "key_events": ["Command to build ark", "Mockery from people", "Preparing the ark"],
                "themes": ["faith_in_unseen", "preparation", "mockery"],
                "lessons_ar": ["الإيمان بالغيب", "الاستعداد للمستقبل"],
                "lessons_en": ["Faith in the unseen", "Preparing for the future"],
                "intensity": 0.8,
            },
            {
                "sura_no": 54,
                "verse_range": "9-17",
                "phase": StoryPhase.CLIMAX,
                "key_events": ["Flood begins", "Boarding the ark", "Son refuses to board", "Drowning of disbelievers"],
                "themes": ["divine_punishment", "salvation", "loss"],
                "lessons_ar": ["عذاب الله شديد", "النجاة بالإيمان فقط"],
                "lessons_en": ["Allah's punishment is severe", "Salvation only through faith"],
                "intensity": 1.0,
            },
            {
                "sura_no": 23,
                "verse_range": "27-30",
                "phase": StoryPhase.RESOLUTION,
                "key_events": ["Waters recede", "Landing on Judi", "New beginning"],
                "themes": ["new_start", "gratitude", "covenant"],
                "lessons_ar": ["بداية جديدة بعد البلاء", "الشكر على النجاة"],
                "lessons_en": ["New beginning after trial", "Gratitude for salvation"],
                "intensity": 0.7,
            },
        ],
        "total_verses": 100,
        "key_themes": ["patience", "perseverance", "divine_punishment", "salvation", "faith"],
        "moral_lessons": [
            {"ar": "الصبر على الدعوة", "en": "Patience in calling to truth"},
            {"ar": "عاقبة التكذيب", "en": "Consequence of denial"},
            {"ar": "النجاة بالإيمان", "en": "Salvation through faith"},
        ],
    },
    "isa_story": {
        "name_ar": "قصة عيسى عليه السلام",
        "name_en": "Story of Jesus (Isa)",
        "type": NarrativeType.PROPHET_STORY,
        "main_character": "عيسى",
        "segments": [
            {
                "sura_no": 19,
                "verse_range": "16-40",
                "phase": StoryPhase.INTRODUCTION,
                "key_events": ["Angel appears to Maryam", "Miraculous conception", "Birth under palm tree", "Speaks in cradle"],
                "themes": ["miracle_of_birth", "divine_power", "honor_of_maryam"],
                "lessons_ar": ["قدرة الله على كل شيء", "كرامة مريم"],
                "lessons_en": ["Allah's power over all things", "Honor of Maryam"],
                "intensity": 0.9,
            },
            {
                "sura_no": 5,
                "verse_range": "110-115",
                "phase": StoryPhase.RISING_ACTION,
                "key_events": ["Teaching Injil", "Miracles: healing blind, lepers, raising dead", "Table from heaven"],
                "themes": ["miracles", "prophethood", "divine_support"],
                "lessons_ar": ["المعجزات دليل النبوة", "دعم الله لرسله"],
                "lessons_en": ["Miracles prove prophethood", "Allah supports His messengers"],
                "intensity": 0.85,
            },
            {
                "sura_no": 3,
                "verse_range": "45-60",
                "phase": StoryPhase.CLIMAX,
                "key_events": ["Opposition from people", "Plot to kill him", "Raised to Allah"],
                "themes": ["persecution", "divine_protection", "ascension"],
                "lessons_ar": ["الله يحمي أنبياءه", "رفع عيسى حيا"],
                "lessons_en": ["Allah protects His prophets", "Isa was raised alive"],
                "intensity": 1.0,
            },
            {
                "sura_no": 4,
                "verse_range": "157-159",
                "phase": StoryPhase.AFTERMATH,
                "key_events": ["Clarification he wasn't killed", "Will return before Day of Judgment"],
                "themes": ["truth_about_crucifixion", "second_coming"],
                "lessons_ar": ["الحقيقة عن الصلب", "سيعود قبل القيامة"],
                "lessons_en": ["Truth about crucifixion", "Will return before Judgment"],
                "intensity": 0.8,
            },
        ],
        "total_verses": 80,
        "key_themes": ["miracles", "divine_protection", "truth", "prophethood"],
        "moral_lessons": [
            {"ar": "عيسى عبد الله ورسوله", "en": "Isa is Allah's servant and messenger"},
            {"ar": "الله ينصر رسله", "en": "Allah supports His messengers"},
            {"ar": "تصحيح المفاهيم الخاطئة", "en": "Correcting misconceptions"},
        ],
    },
}

# Thematic progressions across suras
THEMATIC_PROGRESSIONS = {
    "patience": {
        "theme_name_ar": "الصبر",
        "theme_name_en": "Patience",
        "first_appearance": {"sura": 2, "verse": 45, "context": "Seeking help through patience"},
        "evolution_points": [
            {"sura": 3, "verse": 200, "evolution": ThemeEvolution.DEVELOPED, "context": "Patience and perseverance"},
            {"sura": 16, "verse": 127, "evolution": ThemeEvolution.EMPHASIZED, "context": "Patience is from Allah"},
            {"sura": 39, "verse": 10, "evolution": ThemeEvolution.DEVELOPED, "context": "Reward for patient"},
            {"sura": 103, "verse": 3, "evolution": ThemeEvolution.CONCLUDED, "context": "Patience as salvation"},
        ],
        "peak_intensity": {"sura": 12, "verse": 90, "context": "Yusuf's patience rewarded"},
        "related_themes": ["perseverance", "trust_in_allah", "gratitude"],
    },
    "tawbah": {
        "theme_name_ar": "التوبة",
        "theme_name_en": "Repentance",
        "first_appearance": {"sura": 2, "verse": 37, "context": "Adam's repentance"},
        "evolution_points": [
            {"sura": 4, "verse": 17, "evolution": ThemeEvolution.DEVELOPED, "context": "Conditions for acceptance"},
            {"sura": 9, "verse": 104, "evolution": ThemeEvolution.EMPHASIZED, "context": "Allah accepts repentance"},
            {"sura": 25, "verse": 70, "evolution": ThemeEvolution.DEVELOPED, "context": "Sins converted to good"},
            {"sura": 66, "verse": 8, "evolution": ThemeEvolution.CONCLUDED, "context": "Sincere repentance"},
        ],
        "peak_intensity": {"sura": 9, "verse": 118, "context": "Three who were left behind"},
        "related_themes": ["forgiveness", "mercy", "new_beginning"],
    },
    "tawakkul": {
        "theme_name_ar": "التوكل",
        "theme_name_en": "Trust in Allah",
        "first_appearance": {"sura": 3, "verse": 159, "context": "Trust after consultation"},
        "evolution_points": [
            {"sura": 8, "verse": 2, "evolution": ThemeEvolution.DEVELOPED, "context": "Believers trust Allah"},
            {"sura": 12, "verse": 67, "evolution": ThemeEvolution.EMPHASIZED, "context": "Yaqub's trust"},
            {"sura": 14, "verse": 12, "evolution": ThemeEvolution.DEVELOPED, "context": "Trust despite harm"},
            {"sura": 65, "verse": 3, "evolution": ThemeEvolution.CONCLUDED, "context": "Allah is sufficient"},
        ],
        "peak_intensity": {"sura": 9, "verse": 51, "context": "Nothing befalls except Allah's decree"},
        "related_themes": ["faith", "patience", "divine_decree"],
    },
}

# Cross-references between narratives
NARRATIVE_CROSS_REFERENCES = {
    "musa_ibrahim": {
        "connection": "Family lineage and prophetic tradition",
        "shared_themes": ["monotheism", "leadership", "sacrifice"],
        "connecting_suras": [2, 6, 19, 37],
    },
    "yusuf_musa": {
        "connection": "Both in Egypt, both in positions of power",
        "shared_themes": ["patience", "divine_plan", "leadership"],
        "connecting_suras": [12, 40],
    },
    "nuh_lut": {
        "connection": "Both faced destruction of disbelieving people",
        "shared_themes": ["warning", "divine_punishment", "salvation_of_believers"],
        "connecting_suras": [7, 11, 26],
    },
}


# =============================================================================
# NARRATIVE ARC SERVICE
# =============================================================================

class NarrativeArcService:
    """
    Service for exploring narrative arcs across suras.

    Features:
    - Track stories across multiple suras
    - Identify thematic evolution
    - Map story phases and progression
    - Find cross-references between narratives
    """

    def __init__(self):
        self._arcs = NARRATIVE_ARCS
        self._progressions = THEMATIC_PROGRESSIONS
        self._cross_refs = NARRATIVE_CROSS_REFERENCES
        self._user_progress = {}  # Track user progress through arcs

    def get_all_narrative_arcs(self) -> List[Dict[str, Any]]:
        """Get list of all available narrative arcs."""
        return [
            {
                "arc_id": arc_id,
                "name_ar": data["name_ar"],
                "name_en": data["name_en"],
                "type": data["type"].value,
                "main_character": data["main_character"],
                "segment_count": len(data["segments"]),
                "total_verses": data["total_verses"],
                "key_themes": data["key_themes"],
            }
            for arc_id, data in self._arcs.items()
        ]

    def get_narrative_arc(self, arc_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed narrative arc."""
        if arc_id not in self._arcs:
            return None

        data = self._arcs[arc_id]

        return {
            "arc_id": arc_id,
            "name_ar": data["name_ar"],
            "name_en": data["name_en"],
            "type": data["type"].value,
            "main_character": data["main_character"],
            "segments": [
                {
                    "sura_no": seg["sura_no"],
                    "verse_range": seg["verse_range"],
                    "phase": seg["phase"].value,
                    "key_events": seg["key_events"],
                    "themes": seg["themes"],
                    "lessons_ar": seg["lessons_ar"],
                    "lessons_en": seg["lessons_en"],
                    "intensity": seg["intensity"],
                }
                for seg in data["segments"]
            ],
            "total_verses": data["total_verses"],
            "key_themes": data["key_themes"],
            "moral_lessons": data["moral_lessons"],
            "reading_order": [seg["sura_no"] for seg in data["segments"]],
        }

    def get_arc_segment(
        self,
        arc_id: str,
        segment_index: int,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific segment of a narrative arc."""
        if arc_id not in self._arcs:
            return None

        segments = self._arcs[arc_id]["segments"]
        if segment_index < 0 or segment_index >= len(segments):
            return None

        seg = segments[segment_index]
        arc_data = self._arcs[arc_id]

        return {
            "arc_id": arc_id,
            "arc_name_en": arc_data["name_en"],
            "segment_index": segment_index,
            "total_segments": len(segments),
            "segment": {
                "sura_no": seg["sura_no"],
                "verse_range": seg["verse_range"],
                "phase": seg["phase"].value,
                "key_events": seg["key_events"],
                "themes": seg["themes"],
                "lessons_ar": seg["lessons_ar"],
                "lessons_en": seg["lessons_en"],
                "intensity": seg["intensity"],
            },
            "has_previous": segment_index > 0,
            "has_next": segment_index < len(segments) - 1,
        }

    def get_thematic_progression(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get how a theme evolves across suras."""
        if theme_id not in self._progressions:
            return None

        data = self._progressions[theme_id]

        return {
            "theme_id": theme_id,
            "theme_name_ar": data["theme_name_ar"],
            "theme_name_en": data["theme_name_en"],
            "first_appearance": data["first_appearance"],
            "evolution_points": data["evolution_points"],
            "peak_intensity": data["peak_intensity"],
            "related_themes": data["related_themes"],
            "total_evolution_points": len(data["evolution_points"]) + 1,  # +1 for first appearance
        }

    def get_all_thematic_progressions(self) -> List[Dict[str, Any]]:
        """Get all tracked thematic progressions."""
        return [
            {
                "theme_id": theme_id,
                "theme_name_ar": data["theme_name_ar"],
                "theme_name_en": data["theme_name_en"],
                "first_sura": data["first_appearance"]["sura"],
                "evolution_points_count": len(data["evolution_points"]),
                "related_themes": data["related_themes"],
            }
            for theme_id, data in self._progressions.items()
        ]

    def get_narrative_cross_references(
        self,
        arc_id: str,
    ) -> List[Dict[str, Any]]:
        """Get cross-references to other narratives."""
        cross_refs = []

        for ref_id, ref_data in self._cross_refs.items():
            if arc_id in ref_id:
                # Get the other arc in this reference
                parts = ref_id.split("_")
                other_arc = parts[1] if parts[0] == arc_id.split("_")[0] else parts[0]

                cross_refs.append({
                    "reference_id": ref_id,
                    "related_arc": f"{other_arc}_story",
                    "connection": ref_data["connection"],
                    "shared_themes": ref_data["shared_themes"],
                    "connecting_suras": ref_data["connecting_suras"],
                })

        return cross_refs

    def get_story_by_sura(self, sura_no: int) -> List[Dict[str, Any]]:
        """Get all narrative arcs that include a specific sura."""
        results = []

        for arc_id, arc_data in self._arcs.items():
            for seg in arc_data["segments"]:
                if seg["sura_no"] == sura_no:
                    results.append({
                        "arc_id": arc_id,
                        "arc_name_ar": arc_data["name_ar"],
                        "arc_name_en": arc_data["name_en"],
                        "main_character": arc_data["main_character"],
                        "segment_phase": seg["phase"].value,
                        "verse_range": seg["verse_range"],
                        "key_events": seg["key_events"],
                    })

        return results

    def start_arc_journey(
        self,
        user_id: str,
        arc_id: str,
    ) -> Dict[str, Any]:
        """Start a user's journey through a narrative arc."""
        if arc_id not in self._arcs:
            return {"error": "Arc not found"}

        self._user_progress[user_id] = self._user_progress.get(user_id, {})
        self._user_progress[user_id][arc_id] = {
            "current_segment": 0,
            "started_at": datetime.now().isoformat(),
            "segments_completed": [],
            "lessons_saved": [],
        }

        arc_data = self._arcs[arc_id]
        first_segment = arc_data["segments"][0]

        return {
            "journey_started": True,
            "arc_id": arc_id,
            "arc_name_en": arc_data["name_en"],
            "total_segments": len(arc_data["segments"]),
            "first_segment": {
                "sura_no": first_segment["sura_no"],
                "verse_range": first_segment["verse_range"],
                "phase": first_segment["phase"].value,
                "key_events": first_segment["key_events"],
            },
            "guidance_ar": "ابدأ رحلتك في استكشاف هذه القصة القرآنية",
            "guidance_en": "Begin your journey exploring this Quranic story",
        }

    def advance_arc_journey(
        self,
        user_id: str,
        arc_id: str,
    ) -> Dict[str, Any]:
        """Advance to the next segment in a narrative arc."""
        if user_id not in self._user_progress:
            return {"error": "No journey started"}

        if arc_id not in self._user_progress[user_id]:
            return {"error": "Arc journey not started"}

        progress = self._user_progress[user_id][arc_id]
        arc_data = self._arcs[arc_id]

        current = progress["current_segment"]

        # Mark current as completed
        if current not in progress["segments_completed"]:
            progress["segments_completed"].append(current)

        # Move to next
        if current < len(arc_data["segments"]) - 1:
            progress["current_segment"] = current + 1
            next_segment = arc_data["segments"][current + 1]

            return {
                "advanced": True,
                "current_segment": current + 1,
                "total_segments": len(arc_data["segments"]),
                "segment": {
                    "sura_no": next_segment["sura_no"],
                    "verse_range": next_segment["verse_range"],
                    "phase": next_segment["phase"].value,
                    "key_events": next_segment["key_events"],
                    "themes": next_segment["themes"],
                },
                "progress_percent": round((current + 1) / len(arc_data["segments"]) * 100, 1),
            }
        else:
            # Arc completed
            return {
                "advanced": False,
                "arc_completed": True,
                "arc_id": arc_id,
                "arc_name_en": arc_data["name_en"],
                "moral_lessons": arc_data["moral_lessons"],
                "congratulations_ar": "مبارك! أتممت استكشاف هذه القصة",
                "congratulations_en": "Congratulations! You completed exploring this story",
            }

    def get_user_arc_progress(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get user's progress across all narrative arcs."""
        if user_id not in self._user_progress:
            return {
                "user_id": user_id,
                "arcs_started": 0,
                "arcs_completed": 0,
                "progress": {},
            }

        user_data = self._user_progress[user_id]
        completed = 0
        progress_details = {}

        for arc_id, prog in user_data.items():
            arc_data = self._arcs.get(arc_id, {})
            total_segments = len(arc_data.get("segments", []))
            completed_count = len(prog["segments_completed"])

            is_complete = completed_count >= total_segments
            if is_complete:
                completed += 1

            progress_details[arc_id] = {
                "arc_name_en": arc_data.get("name_en", "Unknown"),
                "segments_completed": completed_count,
                "total_segments": total_segments,
                "percent_complete": round(completed_count / total_segments * 100, 1) if total_segments > 0 else 0,
                "is_complete": is_complete,
                "started_at": prog["started_at"],
            }

        return {
            "user_id": user_id,
            "arcs_started": len(user_data),
            "arcs_completed": completed,
            "progress": progress_details,
        }

    def get_story_timeline(self, arc_id: str) -> Dict[str, Any]:
        """Get timeline visualization data for a story arc."""
        if arc_id not in self._arcs:
            return {"error": "Arc not found"}

        arc_data = self._arcs[arc_id]

        timeline = []
        for i, seg in enumerate(arc_data["segments"]):
            timeline.append({
                "index": i,
                "sura_no": seg["sura_no"],
                "verse_range": seg["verse_range"],
                "phase": seg["phase"].value,
                "phase_label_ar": self._get_phase_label_ar(seg["phase"]),
                "phase_label_en": self._get_phase_label_en(seg["phase"]),
                "intensity": seg["intensity"],
                "key_events": seg["key_events"][:3],  # Top 3 events
            })

        return {
            "arc_id": arc_id,
            "arc_name_ar": arc_data["name_ar"],
            "arc_name_en": arc_data["name_en"],
            "timeline": timeline,
            "total_segments": len(timeline),
        }

    def _get_phase_label_ar(self, phase: StoryPhase) -> str:
        """Get Arabic label for story phase."""
        labels = {
            StoryPhase.INTRODUCTION: "المقدمة",
            StoryPhase.RISING_ACTION: "تصاعد الأحداث",
            StoryPhase.CLIMAX: "الذروة",
            StoryPhase.FALLING_ACTION: "انحدار الأحداث",
            StoryPhase.RESOLUTION: "الحل",
            StoryPhase.AFTERMATH: "ما بعد القصة",
        }
        return labels.get(phase, "غير محدد")

    def _get_phase_label_en(self, phase: StoryPhase) -> str:
        """Get English label for story phase."""
        labels = {
            StoryPhase.INTRODUCTION: "Introduction",
            StoryPhase.RISING_ACTION: "Rising Action",
            StoryPhase.CLIMAX: "Climax",
            StoryPhase.FALLING_ACTION: "Falling Action",
            StoryPhase.RESOLUTION: "Resolution",
            StoryPhase.AFTERMATH: "Aftermath",
        }
        return labels.get(phase, "Unknown")

    def search_narratives_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Search narratives that contain a specific theme."""
        results = []
        theme_lower = theme.lower()

        for arc_id, arc_data in self._arcs.items():
            # Check key themes
            if any(theme_lower in t.lower() for t in arc_data["key_themes"]):
                results.append({
                    "arc_id": arc_id,
                    "arc_name_ar": arc_data["name_ar"],
                    "arc_name_en": arc_data["name_en"],
                    "main_character": arc_data["main_character"],
                    "matching_themes": [t for t in arc_data["key_themes"] if theme_lower in t.lower()],
                })
                continue

            # Check segment themes
            matching_segments = []
            for seg in arc_data["segments"]:
                if any(theme_lower in t.lower() for t in seg["themes"]):
                    matching_segments.append({
                        "sura_no": seg["sura_no"],
                        "phase": seg["phase"].value,
                    })

            if matching_segments:
                results.append({
                    "arc_id": arc_id,
                    "arc_name_ar": arc_data["name_ar"],
                    "arc_name_en": arc_data["name_en"],
                    "main_character": arc_data["main_character"],
                    "matching_segments": matching_segments,
                })

        return results

    def get_narrative_statistics(self) -> Dict[str, Any]:
        """Get statistics about all narrative arcs."""
        total_verses = sum(arc["total_verses"] for arc in self._arcs.values())
        all_themes = set()
        for arc in self._arcs.values():
            all_themes.update(arc["key_themes"])

        return {
            "total_arcs": len(self._arcs),
            "total_verses_covered": total_verses,
            "unique_themes": len(all_themes),
            "themes_list": sorted(all_themes),
            "thematic_progressions": len(self._progressions),
            "cross_references": len(self._cross_refs),
            "narrative_types": list(set(arc["type"].value for arc in self._arcs.values())),
        }


# =============================================================================
# CROSS-STORY SEARCH SERVICE (PHASE 8 ENHANCEMENT)
# =============================================================================

class CrossStorySearchService:
    """
    Enhanced cross-story search and comparison service.

    Integrates narrative arcs with thematic search, enabling users to:
    - Search for themes across multiple prophet stories
    - Compare parallel experiences between prophets
    - Track journeys through interconnected narratives
    - Discover thematic patterns across stories

    Arabic: خدمة البحث المتقاطع عبر القصص
    """

    def __init__(self, narrative_service: NarrativeArcService):
        self._narrative_service = narrative_service
        self._user_journeys: Dict[str, Dict[str, Any]] = {}

        # Pre-compute theme-to-story mappings
        self._theme_story_index = self._build_theme_index()
        self._event_index = self._build_event_index()
        self._prophet_comparison_data = self._build_comparison_data()

    def _build_theme_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build index mapping themes to stories and segments."""
        index = defaultdict(list)

        for arc_id, arc_data in self._narrative_service._arcs.items():
            # Index key themes
            for theme in arc_data["key_themes"]:
                index[theme.lower()].append({
                    "arc_id": arc_id,
                    "prophet": arc_data["main_character"],
                    "level": "key_theme",
                    "moral_lessons": arc_data["moral_lessons"],
                })

            # Index segment themes
            for seg in arc_data["segments"]:
                for theme in seg["themes"]:
                    index[theme.lower()].append({
                        "arc_id": arc_id,
                        "prophet": arc_data["main_character"],
                        "level": "segment",
                        "sura_no": seg["sura_no"],
                        "verse_range": seg["verse_range"],
                        "phase": seg["phase"].value,
                        "lessons_ar": seg.get("lessons_ar", []),
                        "lessons_en": seg.get("lessons_en", []),
                    })

        return dict(index)

    def _build_event_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build index mapping events to stories."""
        index = defaultdict(list)

        for arc_id, arc_data in self._narrative_service._arcs.items():
            for seg in arc_data["segments"]:
                for event in seg["key_events"]:
                    event_lower = event.lower()
                    index[event_lower].append({
                        "arc_id": arc_id,
                        "prophet": arc_data["main_character"],
                        "sura_no": seg["sura_no"],
                        "verse_range": seg["verse_range"],
                        "phase": seg["phase"].value,
                        "event": event,
                    })

        return dict(index)

    def _build_comparison_data(self) -> Dict[str, Dict[str, Any]]:
        """Build prophet comparison data for parallel experiences."""
        comparisons = {
            "patience_under_trial": {
                "theme_ar": "الصبر على البلاء",
                "theme_en": "Patience Under Trial",
                "prophets": {
                    "يوسف": {
                        "experience": "Betrayal by brothers, slavery, imprisonment",
                        "duration": "Many years",
                        "outcome": "Became minister of Egypt",
                        "key_verses": ["12:18", "12:33-35", "12:90"],
                        "lessons_ar": ["الصبر يفتح أبواب الفرج"],
                        "lessons_en": ["Patience opens doors to relief"],
                    },
                    "أيوب": {
                        "experience": "Loss of health, wealth, and family",
                        "duration": "18 years of illness",
                        "outcome": "Restored with double blessings",
                        "key_verses": ["21:83-84", "38:41-44"],
                        "lessons_ar": ["الشكر في البلاء"],
                        "lessons_en": ["Gratitude during affliction"],
                    },
                    "يعقوب": {
                        "experience": "Loss of beloved son Yusuf, then Binyamin",
                        "duration": "Decades of separation",
                        "outcome": "Reunited with both sons",
                        "key_verses": ["12:18", "12:83-86"],
                        "lessons_ar": ["الصبر الجميل"],
                        "lessons_en": ["Beautiful patience (sabr jameel)"],
                    },
                },
            },
            "confronting_tyrants": {
                "theme_ar": "مواجهة الطغاة",
                "theme_en": "Confronting Tyrants",
                "prophets": {
                    "موسى": {
                        "experience": "Confronted Pharaoh demanding release of Bani Israel",
                        "tyrant": "Pharaoh (Fir'aun)",
                        "outcome": "Pharaoh drowned, people liberated",
                        "key_verses": ["7:103-137", "26:10-68"],
                        "lessons_ar": ["الحق يعلو ولا يُعلى عليه"],
                        "lessons_en": ["Truth prevails over tyranny"],
                    },
                    "إبراهيم": {
                        "experience": "Challenged Nimrod and idol worship",
                        "tyrant": "Nimrod (Namrud)",
                        "outcome": "Saved from fire, migrated victorious",
                        "key_verses": ["21:51-70", "2:258"],
                        "lessons_ar": ["الشجاعة في قول الحق"],
                        "lessons_en": ["Courage in speaking truth"],
                    },
                    "نوح": {
                        "experience": "Called people for 950 years despite mockery",
                        "tyrant": "Disbelieving elite",
                        "outcome": "Flood destroyed oppressors",
                        "key_verses": ["71:1-28", "11:25-49"],
                        "lessons_ar": ["المثابرة في الدعوة"],
                        "lessons_en": ["Perseverance in calling to truth"],
                    },
                },
            },
            "family_sacrifice": {
                "theme_ar": "التضحية العائلية",
                "theme_en": "Family Sacrifice",
                "prophets": {
                    "إبراهيم": {
                        "experience": "Commanded to sacrifice his son Ismail",
                        "sacrifice_type": "Near-sacrifice of son",
                        "outcome": "Ransom provided, legacy of Eid al-Adha",
                        "key_verses": ["37:99-111"],
                        "lessons_ar": ["التسليم لأمر الله"],
                        "lessons_en": ["Submission to Allah's command"],
                    },
                    "نوح": {
                        "experience": "Could not save his disbelieving son from flood",
                        "sacrifice_type": "Accepting loss of son to divine decree",
                        "outcome": "Lesson in faith over family bonds",
                        "key_verses": ["11:42-47"],
                        "lessons_ar": ["الإيمان فوق روابط الدم"],
                        "lessons_en": ["Faith above blood ties"],
                    },
                    "لوط": {
                        "experience": "Wife disbelieved and was destroyed",
                        "sacrifice_type": "Losing spouse to divine punishment",
                        "outcome": "Saved with believing family",
                        "key_verses": ["7:83", "11:81"],
                        "lessons_ar": ["لا يغني القرب من النبي"],
                        "lessons_en": ["Proximity to prophet doesn't guarantee salvation"],
                    },
                },
            },
            "exile_and_migration": {
                "theme_ar": "النفي والهجرة",
                "theme_en": "Exile and Migration",
                "prophets": {
                    "إبراهيم": {
                        "experience": "Migrated from Mesopotamia to Canaan to Egypt",
                        "reason": "Fleeing persecution, seeking land",
                        "outcome": "Established monotheism in new lands",
                        "key_verses": ["29:26", "21:71"],
                        "lessons_ar": ["الهجرة لله"],
                        "lessons_en": ["Migration for Allah's sake"],
                    },
                    "موسى": {
                        "experience": "Fled Egypt to Madyan, later led exodus",
                        "reason": "Fear of punishment, then divine command",
                        "outcome": "Led people to freedom",
                        "key_verses": ["28:21-28", "20:77-79"],
                        "lessons_ar": ["الفرار من الظلم مشروع"],
                        "lessons_en": ["Fleeing oppression is legitimate"],
                    },
                    "لوط": {
                        "experience": "Commanded to leave with family at night",
                        "reason": "Divine punishment coming on city",
                        "outcome": "Saved while city destroyed",
                        "key_verses": ["11:81", "15:65"],
                        "lessons_ar": ["طاعة الأمر الإلهي"],
                        "lessons_en": ["Obedience to divine command"],
                    },
                },
            },
            "miraculous_rescue": {
                "theme_ar": "الإنقاذ المعجز",
                "theme_en": "Miraculous Rescue",
                "prophets": {
                    "إبراهيم": {
                        "experience": "Thrown into massive fire",
                        "miracle": "Fire became cool and peaceful",
                        "key_verses": ["21:68-69"],
                        "lessons_ar": ["الله ينجي المتوكلين"],
                        "lessons_en": ["Allah saves those who trust Him"],
                    },
                    "موسى": {
                        "experience": "Trapped between sea and Pharaoh's army",
                        "miracle": "Sea parted creating path",
                        "key_verses": ["26:63-68"],
                        "lessons_ar": ["النصر من عند الله"],
                        "lessons_en": ["Victory comes from Allah"],
                    },
                    "يونس": {
                        "experience": "Swallowed by whale in the sea",
                        "miracle": "Whale released him alive",
                        "key_verses": ["21:87-88", "37:139-148"],
                        "lessons_ar": ["الدعاء في الشدة"],
                        "lessons_en": ["Supplication in distress"],
                    },
                    "عيسى": {
                        "experience": "Plotted to be crucified",
                        "miracle": "Raised to heaven alive",
                        "key_verses": ["4:157-158", "3:55"],
                        "lessons_ar": ["الله يحمي رسله"],
                        "lessons_en": ["Allah protects His messengers"],
                    },
                },
            },
        }

        return comparisons

    def cross_story_search(
        self,
        query: str,
        search_type: str = "all",  # all, theme, event, lesson
    ) -> Dict[str, Any]:
        """
        Search across all stories for a theme, event, or lesson.

        Arabic: البحث عبر جميع القصص عن موضوع أو حدث أو درس
        """
        query_lower = query.lower()
        results = {
            "query": query,
            "search_type": search_type,
            "theme_matches": [],
            "event_matches": [],
            "lesson_matches": [],
        }

        # Search themes
        if search_type in ["all", "theme"]:
            for theme, entries in self._theme_story_index.items():
                if query_lower in theme:
                    for entry in entries:
                        results["theme_matches"].append({
                            **entry,
                            "matched_theme": theme,
                        })

        # Search events
        if search_type in ["all", "event"]:
            for event_key, entries in self._event_index.items():
                if query_lower in event_key:
                    for entry in entries:
                        results["event_matches"].append(entry)

        # Search lessons in moral_lessons
        if search_type in ["all", "lesson"]:
            for arc_id, arc_data in self._narrative_service._arcs.items():
                for lesson in arc_data["moral_lessons"]:
                    if query_lower in lesson.get("en", "").lower() or query_lower in lesson.get("ar", ""):
                        results["lesson_matches"].append({
                            "arc_id": arc_id,
                            "prophet": arc_data["main_character"],
                            "lesson_ar": lesson.get("ar"),
                            "lesson_en": lesson.get("en"),
                        })

        results["total_matches"] = (
            len(results["theme_matches"]) +
            len(results["event_matches"]) +
            len(results["lesson_matches"])
        )

        return results

    def get_parallel_experiences(
        self,
        theme_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get prophets' parallel experiences for a specific theme.

        Arabic: الحصول على التجارب المتوازية للأنبياء في موضوع معين
        """
        if theme_id not in self._prophet_comparison_data:
            return None

        data = self._prophet_comparison_data[theme_id]

        return {
            "theme_id": theme_id,
            "theme_ar": data["theme_ar"],
            "theme_en": data["theme_en"],
            "prophets": [
                {
                    "name": prophet_name,
                    **prophet_data,
                }
                for prophet_name, prophet_data in data["prophets"].items()
            ],
            "prophet_count": len(data["prophets"]),
        }

    def get_all_parallel_themes(self) -> List[Dict[str, str]]:
        """Get all available parallel experience themes."""
        return [
            {
                "theme_id": theme_id,
                "theme_ar": data["theme_ar"],
                "theme_en": data["theme_en"],
                "prophet_count": len(data["prophets"]),
            }
            for theme_id, data in self._prophet_comparison_data.items()
        ]

    def compare_prophets(
        self,
        prophet1: str,
        prophet2: str,
    ) -> Dict[str, Any]:
        """
        Compare two prophets across all parallel themes.

        Arabic: مقارنة نبيين عبر جميع المواضيع المتوازية
        """
        shared_themes = []

        for theme_id, data in self._prophet_comparison_data.items():
            prophets_in_theme = data["prophets"]

            if prophet1 in prophets_in_theme and prophet2 in prophets_in_theme:
                shared_themes.append({
                    "theme_id": theme_id,
                    "theme_ar": data["theme_ar"],
                    "theme_en": data["theme_en"],
                    f"{prophet1}": prophets_in_theme[prophet1],
                    f"{prophet2}": prophets_in_theme[prophet2],
                })

        # Also check narrative cross-references
        arc_id1 = f"{prophet1.replace('موسى', 'musa').replace('إبراهيم', 'ibrahim').replace('يوسف', 'yusuf').replace('نوح', 'nuh').replace('عيسى', 'isa')}_story"
        arc_id2 = f"{prophet2.replace('موسى', 'musa').replace('إبراهيم', 'ibrahim').replace('يوسف', 'yusuf').replace('نوح', 'nuh').replace('عيسى', 'isa')}_story"

        narrative_connection = None
        for ref_id, ref_data in self._narrative_service._cross_refs.items():
            if arc_id1.split("_")[0] in ref_id and arc_id2.split("_")[0] in ref_id:
                narrative_connection = ref_data
                break

        return {
            "prophet1": prophet1,
            "prophet2": prophet2,
            "shared_parallel_themes": shared_themes,
            "shared_theme_count": len(shared_themes),
            "narrative_connection": narrative_connection,
        }

    def start_multi_story_journey(
        self,
        user_id: str,
        theme_id: str,
    ) -> Dict[str, Any]:
        """
        Start a journey through multiple stories connected by a theme.

        Arabic: بدء رحلة عبر قصص متعددة مرتبطة بموضوع
        """
        if theme_id not in self._prophet_comparison_data:
            return {"error": f"Theme '{theme_id}' not found"}

        theme_data = self._prophet_comparison_data[theme_id]
        prophets = list(theme_data["prophets"].keys())

        self._user_journeys[user_id] = {
            "type": "multi_story",
            "theme_id": theme_id,
            "theme_ar": theme_data["theme_ar"],
            "theme_en": theme_data["theme_en"],
            "prophets": prophets,
            "current_prophet_index": 0,
            "started_at": datetime.now().isoformat(),
            "completed_prophets": [],
            "insights_saved": [],
        }

        first_prophet = prophets[0]
        first_data = theme_data["prophets"][first_prophet]

        return {
            "journey_started": True,
            "theme_id": theme_id,
            "theme_en": theme_data["theme_en"],
            "total_prophets": len(prophets),
            "first_prophet": {
                "name": first_prophet,
                **first_data,
            },
            "remaining_prophets": prophets[1:],
            "guidance_ar": f"ابدأ رحلة استكشاف موضوع {theme_data['theme_ar']} عبر قصص الأنبياء",
            "guidance_en": f"Begin exploring the theme of {theme_data['theme_en']} across prophet stories",
        }

    def advance_multi_story_journey(
        self,
        user_id: str,
        insight: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Advance to the next prophet in a multi-story journey.

        Arabic: التقدم إلى النبي التالي في الرحلة
        """
        if user_id not in self._user_journeys:
            return {"error": "No journey started"}

        journey = self._user_journeys[user_id]
        theme_data = self._prophet_comparison_data[journey["theme_id"]]

        current_idx = journey["current_prophet_index"]
        current_prophet = journey["prophets"][current_idx]

        # Save insight if provided
        if insight:
            journey["insights_saved"].append({
                "prophet": current_prophet,
                "insight": insight,
                "timestamp": datetime.now().isoformat(),
            })

        # Mark current as completed
        if current_prophet not in journey["completed_prophets"]:
            journey["completed_prophets"].append(current_prophet)

        # Move to next
        if current_idx < len(journey["prophets"]) - 1:
            journey["current_prophet_index"] = current_idx + 1
            next_prophet = journey["prophets"][current_idx + 1]
            next_data = theme_data["prophets"][next_prophet]

            return {
                "advanced": True,
                "current_prophet_index": current_idx + 1,
                "total_prophets": len(journey["prophets"]),
                "next_prophet": {
                    "name": next_prophet,
                    **next_data,
                },
                "progress_percent": round((current_idx + 1) / len(journey["prophets"]) * 100, 1),
            }
        else:
            # Journey completed
            return {
                "advanced": False,
                "journey_completed": True,
                "theme_id": journey["theme_id"],
                "theme_en": journey["theme_en"],
                "prophets_explored": journey["completed_prophets"],
                "insights_saved": journey["insights_saved"],
                "summary": {
                    "prophets_count": len(journey["prophets"]),
                    "insights_count": len(journey["insights_saved"]),
                },
                "congratulations_ar": f"مبارك! أتممت استكشاف موضوع {journey['theme_ar']} عبر جميع القصص",
                "congratulations_en": f"Congratulations! You completed exploring {journey['theme_en']} across all stories",
            }

    def get_user_journey_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's current journey status."""
        if user_id not in self._user_journeys:
            return {
                "user_id": user_id,
                "has_active_journey": False,
            }

        journey = self._user_journeys[user_id]

        return {
            "user_id": user_id,
            "has_active_journey": True,
            "journey_type": journey["type"],
            "theme_id": journey["theme_id"],
            "theme_en": journey["theme_en"],
            "total_prophets": len(journey["prophets"]),
            "completed_prophets": len(journey["completed_prophets"]),
            "progress_percent": round(len(journey["completed_prophets"]) / len(journey["prophets"]) * 100, 1),
            "started_at": journey["started_at"],
        }

    def get_story_connections(
        self,
        arc_id: str,
    ) -> Dict[str, Any]:
        """
        Get all connections from a story to other stories.

        Arabic: جميع الروابط من قصة إلى قصص أخرى
        """
        if arc_id not in self._narrative_service._arcs:
            return {"error": "Arc not found"}

        arc_data = self._narrative_service._arcs[arc_id]
        main_prophet = arc_data["main_character"]

        # Find cross-references
        cross_refs = self._narrative_service.get_narrative_cross_references(arc_id)

        # Find shared themes with other stories
        shared_themes = []
        for theme in arc_data["key_themes"]:
            theme_entries = self._theme_story_index.get(theme.lower(), [])
            other_arcs = set()
            for entry in theme_entries:
                if entry["arc_id"] != arc_id:
                    other_arcs.add((entry["arc_id"], entry["prophet"]))

            if other_arcs:
                shared_themes.append({
                    "theme": theme,
                    "shared_with": [
                        {"arc_id": a, "prophet": p} for a, p in other_arcs
                    ],
                })

        # Find parallel experiences
        parallel_themes = []
        for theme_id, data in self._prophet_comparison_data.items():
            if main_prophet in data["prophets"]:
                other_prophets = [p for p in data["prophets"].keys() if p != main_prophet]
                if other_prophets:
                    parallel_themes.append({
                        "theme_id": theme_id,
                        "theme_en": data["theme_en"],
                        "shared_with": other_prophets,
                    })

        return {
            "arc_id": arc_id,
            "main_prophet": main_prophet,
            "cross_references": cross_refs,
            "shared_themes": shared_themes,
            "parallel_experiences": parallel_themes,
            "total_connections": len(cross_refs) + len(shared_themes) + len(parallel_themes),
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

narrative_arc_service = NarrativeArcService()
cross_story_search_service = CrossStorySearchService(narrative_arc_service)
