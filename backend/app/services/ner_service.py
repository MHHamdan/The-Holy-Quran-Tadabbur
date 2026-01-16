"""
Named Entity Recognition (NER) Service for Quranic Text.

Identifies and extracts:
1. Prophets and messengers (أنبياء ورسل)
2. Angels (ملائكة)
3. Historical figures (شخصيات تاريخية)
4. Places (أماكن)
5. Events (أحداث)
6. Divine names and attributes (أسماء الله وصفاته)
7. Religious concepts (مفاهيم دينية)

Arabic: خدمة التعرف على الكيانات المسماة في النص القرآني
"""

import logging
import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# ENTITY TYPES
# =============================================================================

class EntityType(str, Enum):
    """Types of named entities in Quranic text."""
    PROPHET = "prophet"
    ANGEL = "angel"
    HISTORICAL_FIGURE = "historical_figure"
    PLACE = "place"
    EVENT = "event"
    DIVINE_NAME = "divine_name"
    DIVINE_ATTRIBUTE = "divine_attribute"
    RELIGIOUS_CONCEPT = "religious_concept"
    NATION = "nation"
    BOOK = "book"
    TIME_PERIOD = "time_period"


# =============================================================================
# ENTITY DATABASE
# =============================================================================

# Prophets mentioned in the Quran
PROPHETS = {
    "آدم": {
        "en": "Adam",
        "mentions": 25,
        "key_suras": [2, 3, 5, 7, 17, 18, 19, 20],
        "aliases": ["أبو البشر"],
        "description_ar": "أبو البشر وأول الأنبياء",
        "description_en": "Father of humanity and first prophet",
    },
    "نوح": {
        "en": "Noah (Nuh)",
        "mentions": 43,
        "key_suras": [7, 10, 11, 23, 26, 71],
        "aliases": ["نوحا"],
        "description_ar": "نبي الطوفان",
        "description_en": "Prophet of the flood",
    },
    "إبراهيم": {
        "en": "Abraham (Ibrahim)",
        "mentions": 69,
        "key_suras": [2, 6, 14, 19, 21, 37],
        "aliases": ["ابراهيم", "خليل الله", "الخليل"],
        "description_ar": "خليل الرحمن وأبو الأنبياء",
        "description_en": "Friend of Allah and father of prophets",
    },
    "إسماعيل": {
        "en": "Ishmael (Ismail)",
        "mentions": 12,
        "key_suras": [2, 6, 19, 21, 37],
        "aliases": ["اسماعيل"],
        "description_ar": "الذبيح",
        "description_en": "The sacrificed one",
    },
    "إسحاق": {
        "en": "Isaac (Ishaq)",
        "mentions": 17,
        "key_suras": [2, 6, 11, 19, 21, 37],
        "aliases": ["اسحاق", "اسحق"],
        "description_ar": "ابن إبراهيم من سارة",
        "description_en": "Son of Ibrahim from Sarah",
    },
    "يعقوب": {
        "en": "Jacob (Yaqub)",
        "mentions": 16,
        "key_suras": [2, 3, 4, 6, 11, 12, 19, 21],
        "aliases": ["إسرائيل"],
        "description_ar": "أبو الأسباط الاثني عشر",
        "description_en": "Father of the twelve tribes",
    },
    "يوسف": {
        "en": "Joseph (Yusuf)",
        "mentions": 27,
        "key_suras": [12, 40],
        "aliases": [],
        "description_ar": "الصديق",
        "description_en": "The truthful one",
    },
    "موسى": {
        "en": "Moses (Musa)",
        "mentions": 136,
        "key_suras": [2, 7, 10, 11, 17, 18, 19, 20, 26, 27, 28],
        "aliases": ["كليم الله"],
        "description_ar": "كليم الله",
        "description_en": "The one who spoke to Allah",
    },
    "هارون": {
        "en": "Aaron (Harun)",
        "mentions": 20,
        "key_suras": [2, 4, 6, 7, 19, 20, 21, 23, 25, 26, 28, 37],
        "aliases": [],
        "description_ar": "أخو موسى ووزيره",
        "description_en": "Brother and helper of Musa",
    },
    "داود": {
        "en": "David (Dawud)",
        "mentions": 16,
        "key_suras": [2, 4, 5, 6, 17, 21, 27, 34, 38],
        "aliases": [],
        "description_ar": "صاحب الزبور",
        "description_en": "Recipient of the Psalms",
    },
    "سليمان": {
        "en": "Solomon (Sulayman)",
        "mentions": 17,
        "key_suras": [2, 4, 6, 21, 27, 34, 38],
        "aliases": [],
        "description_ar": "النبي الملك",
        "description_en": "The prophet-king",
    },
    "أيوب": {
        "en": "Job (Ayyub)",
        "mentions": 4,
        "key_suras": [4, 6, 21, 38],
        "aliases": [],
        "description_ar": "مثال الصبر",
        "description_en": "Example of patience",
    },
    "يونس": {
        "en": "Jonah (Yunus)",
        "mentions": 4,
        "key_suras": [4, 6, 10, 21, 37, 68],
        "aliases": ["ذو النون", "صاحب الحوت"],
        "description_ar": "صاحب الحوت",
        "description_en": "Companion of the whale",
    },
    "عيسى": {
        "en": "Jesus (Isa)",
        "mentions": 25,
        "key_suras": [2, 3, 4, 5, 19, 21, 23, 33, 42, 43, 57, 61],
        "aliases": ["المسيح", "ابن مريم", "روح الله", "كلمة الله"],
        "description_ar": "المسيح ابن مريم",
        "description_en": "The Messiah, son of Maryam",
    },
    "محمد": {
        "en": "Muhammad",
        "mentions": 4,
        "key_suras": [3, 33, 47, 48],
        "aliases": ["أحمد", "النبي", "الرسول", "خاتم النبيين"],
        "description_ar": "خاتم الأنبياء والمرسلين",
        "description_en": "Seal of the prophets",
    },
    "زكريا": {
        "en": "Zechariah (Zakariya)",
        "mentions": 7,
        "key_suras": [3, 6, 19, 21],
        "aliases": [],
        "description_ar": "كفيل مريم",
        "description_en": "Guardian of Maryam",
    },
    "يحيى": {
        "en": "John (Yahya)",
        "mentions": 5,
        "key_suras": [3, 6, 19, 21],
        "aliases": [],
        "description_ar": "ابن زكريا",
        "description_en": "Son of Zakariya",
    },
    "إلياس": {
        "en": "Elijah (Ilyas)",
        "mentions": 2,
        "key_suras": [6, 37],
        "aliases": [],
        "description_ar": "من أنبياء بني إسرائيل",
        "description_en": "Prophet of the Children of Israel",
    },
    "اليسع": {
        "en": "Elisha (Al-Yasa)",
        "mentions": 2,
        "key_suras": [6, 38],
        "aliases": [],
        "description_ar": "من أنبياء بني إسرائيل",
        "description_en": "Prophet of the Children of Israel",
    },
    "لوط": {
        "en": "Lot (Lut)",
        "mentions": 27,
        "key_suras": [6, 7, 11, 15, 21, 22, 26, 27, 29, 37, 38, 50, 54, 66],
        "aliases": [],
        "description_ar": "ابن أخ إبراهيم",
        "description_en": "Nephew of Ibrahim",
    },
    "شعيب": {
        "en": "Shuayb",
        "mentions": 11,
        "key_suras": [7, 11, 26, 29],
        "aliases": [],
        "description_ar": "خطيب الأنبياء",
        "description_en": "Orator of the prophets",
    },
    "هود": {
        "en": "Hud",
        "mentions": 7,
        "key_suras": [7, 11, 26, 46],
        "aliases": [],
        "description_ar": "نبي عاد",
        "description_en": "Prophet to the people of 'Ad",
    },
    "صالح": {
        "en": "Salih",
        "mentions": 9,
        "key_suras": [7, 11, 26, 27],
        "aliases": [],
        "description_ar": "نبي ثمود",
        "description_en": "Prophet to the people of Thamud",
    },
    "ذو الكفل": {
        "en": "Dhul-Kifl",
        "mentions": 2,
        "key_suras": [21, 38],
        "aliases": [],
        "description_ar": "النبي الصابر",
        "description_en": "The patient prophet",
    },
    "إدريس": {
        "en": "Idris (Enoch)",
        "mentions": 2,
        "key_suras": [19, 21],
        "aliases": [],
        "description_ar": "أول من خط بالقلم",
        "description_en": "First to write with a pen",
    },
}

# Angels mentioned in the Quran
ANGELS = {
    "جبريل": {
        "en": "Gabriel (Jibril)",
        "aliases": ["الروح الأمين", "روح القدس", "جبرائيل"],
        "role_ar": "ملك الوحي",
        "role_en": "Angel of Revelation",
        "key_suras": [2, 66],
    },
    "ميكائيل": {
        "en": "Michael (Mikail)",
        "aliases": ["ميكال"],
        "role_ar": "ملك الأرزاق",
        "role_en": "Angel of Provisions",
        "key_suras": [2],
    },
    "إسرافيل": {
        "en": "Israfil",
        "aliases": [],
        "role_ar": "ملك النفخ في الصور",
        "role_en": "Angel of the Trumpet",
        "key_suras": [],
    },
    "ملك الموت": {
        "en": "Angel of Death",
        "aliases": ["عزرائيل"],
        "role_ar": "قابض الأرواح",
        "role_en": "Taker of souls",
        "key_suras": [32],
    },
    "هاروت": {
        "en": "Harut",
        "aliases": [],
        "role_ar": "من الملائكة المختبرين",
        "role_en": "One of the testing angels",
        "key_suras": [2],
    },
    "ماروت": {
        "en": "Marut",
        "aliases": [],
        "role_ar": "من الملائكة المختبرين",
        "role_en": "One of the testing angels",
        "key_suras": [2],
    },
    "مالك": {
        "en": "Malik",
        "aliases": [],
        "role_ar": "خازن النار",
        "role_en": "Keeper of Hell",
        "key_suras": [43],
    },
}

# Places mentioned in the Quran
PLACES = {
    "مكة": {
        "en": "Mecca",
        "aliases": ["بكة", "أم القرى", "البلد الأمين"],
        "type": "city",
        "significance_ar": "موقع الكعبة وأقدس بقعة",
        "significance_en": "Location of the Kaaba, holiest site",
        "key_suras": [3, 48],
    },
    "المدينة": {
        "en": "Medina",
        "aliases": ["يثرب"],
        "type": "city",
        "significance_ar": "مدينة الهجرة النبوية",
        "significance_en": "City of the Prophet's migration",
        "key_suras": [9, 33],
    },
    "الكعبة": {
        "en": "Kaaba",
        "aliases": ["البيت الحرام", "البيت العتيق"],
        "type": "structure",
        "significance_ar": "قبلة المسلمين",
        "significance_en": "Direction of Muslim prayer",
        "key_suras": [2, 3, 5],
    },
    "مصر": {
        "en": "Egypt",
        "aliases": [],
        "type": "country",
        "significance_ar": "أرض يوسف وموسى",
        "significance_en": "Land of Yusuf and Musa",
        "key_suras": [10, 12, 43],
    },
    "الأقصى": {
        "en": "Al-Aqsa",
        "aliases": ["المسجد الأقصى"],
        "type": "mosque",
        "significance_ar": "أولى القبلتين",
        "significance_en": "First direction of prayer",
        "key_suras": [17],
    },
    "بابل": {
        "en": "Babylon",
        "aliases": [],
        "type": "city",
        "significance_ar": "مدينة السحر",
        "significance_en": "City of magic",
        "key_suras": [2],
    },
    "سيناء": {
        "en": "Sinai",
        "aliases": ["طور سيناء", "الطور"],
        "type": "mountain",
        "significance_ar": "جبل التجلي",
        "significance_en": "Mountain of divine manifestation",
        "key_suras": [23, 95],
    },
    "الجودي": {
        "en": "Mount Judi",
        "aliases": [],
        "type": "mountain",
        "significance_ar": "مرسى سفينة نوح",
        "significance_en": "Landing place of Noah's Ark",
        "key_suras": [11],
    },
    "سبأ": {
        "en": "Sheba (Saba)",
        "aliases": [],
        "type": "kingdom",
        "significance_ar": "مملكة بلقيس",
        "significance_en": "Kingdom of the Queen of Sheba",
        "key_suras": [27, 34],
    },
    "أحقاف": {
        "en": "Ahqaf",
        "aliases": [],
        "type": "region",
        "significance_ar": "أرض عاد",
        "significance_en": "Land of 'Ad",
        "key_suras": [46],
    },
    "مدين": {
        "en": "Madyan",
        "aliases": [],
        "type": "region",
        "significance_ar": "أرض شعيب",
        "significance_en": "Land of Shu'ayb",
        "key_suras": [7, 11, 20, 28, 29],
    },
}

# Historical events
EVENTS = {
    "الطوفان": {
        "en": "The Flood",
        "prophet": "نوح",
        "type": "divine_punishment",
        "description_ar": "غرق قوم نوح",
        "description_en": "Drowning of Noah's people",
        "key_suras": [7, 11, 23, 26, 71],
    },
    "الإسراء": {
        "en": "The Night Journey",
        "prophet": "محمد",
        "type": "miracle",
        "description_ar": "رحلة النبي الليلية إلى المسجد الأقصى",
        "description_en": "Prophet's night journey to Al-Aqsa",
        "key_suras": [17],
    },
    "المعراج": {
        "en": "The Ascension",
        "prophet": "محمد",
        "type": "miracle",
        "description_ar": "صعود النبي إلى السماوات",
        "description_en": "Prophet's ascension to the heavens",
        "key_suras": [17, 53],
    },
    "فتح مكة": {
        "en": "Conquest of Mecca",
        "prophet": "محمد",
        "type": "historical",
        "description_ar": "دخول المسلمين مكة فاتحين",
        "description_en": "Muslims' victorious entry into Mecca",
        "key_suras": [48, 110],
    },
    "بدر": {
        "en": "Battle of Badr",
        "prophet": "محمد",
        "type": "battle",
        "description_ar": "أول غزوة كبرى للمسلمين",
        "description_en": "First major battle for Muslims",
        "key_suras": [3, 8],
    },
    "أحد": {
        "en": "Battle of Uhud",
        "prophet": "محمد",
        "type": "battle",
        "description_ar": "معركة أحد",
        "description_en": "Battle of Uhud",
        "key_suras": [3],
    },
    "الأحزاب": {
        "en": "Battle of the Trench",
        "prophet": "محمد",
        "type": "battle",
        "description_ar": "غزوة الخندق",
        "description_en": "Battle of the Trench",
        "key_suras": [33],
    },
    "خروج موسى": {
        "en": "Exodus of Moses",
        "prophet": "موسى",
        "type": "historical",
        "description_ar": "خروج بني إسرائيل من مصر",
        "description_en": "Exodus of Israelites from Egypt",
        "key_suras": [7, 20, 26],
    },
    "انشقاق البحر": {
        "en": "Parting of the Sea",
        "prophet": "موسى",
        "type": "miracle",
        "description_ar": "انفلاق البحر لموسى",
        "description_en": "Sea splitting for Moses",
        "key_suras": [26],
    },
}

# Divine names (99 names of Allah)
DIVINE_NAMES = {
    "الله": {"en": "Allah", "meaning_ar": "الإله المعبود", "meaning_en": "The God"},
    "الرحمن": {"en": "Ar-Rahman", "meaning_ar": "ذو الرحمة الواسعة", "meaning_en": "The Most Merciful"},
    "الرحيم": {"en": "Ar-Raheem", "meaning_ar": "ذو الرحمة الخاصة", "meaning_en": "The Especially Merciful"},
    "الملك": {"en": "Al-Malik", "meaning_ar": "المالك لكل شيء", "meaning_en": "The King"},
    "القدوس": {"en": "Al-Quddus", "meaning_ar": "المنزه عن النقائص", "meaning_en": "The Holy"},
    "السلام": {"en": "As-Salam", "meaning_ar": "ذو السلامة من كل عيب", "meaning_en": "The Peace"},
    "الغفور": {"en": "Al-Ghafur", "meaning_ar": "كثير المغفرة", "meaning_en": "The Forgiving"},
    "الحكيم": {"en": "Al-Hakeem", "meaning_ar": "ذو الحكمة", "meaning_en": "The Wise"},
    "العزيز": {"en": "Al-Aziz", "meaning_ar": "الغالب الذي لا يُغلب", "meaning_en": "The Mighty"},
    "السميع": {"en": "As-Samee", "meaning_ar": "السامع لكل شيء", "meaning_en": "The All-Hearing"},
    "البصير": {"en": "Al-Baseer", "meaning_ar": "المبصر لكل شيء", "meaning_en": "The All-Seeing"},
    "العليم": {"en": "Al-Aleem", "meaning_ar": "العالم بكل شيء", "meaning_en": "The All-Knowing"},
    "الخالق": {"en": "Al-Khaliq", "meaning_ar": "المبدع للخلق", "meaning_en": "The Creator"},
    "الرزاق": {"en": "Ar-Razzaq", "meaning_ar": "المتكفل بالرزق", "meaning_en": "The Provider"},
}

# Nations mentioned in the Quran
NATIONS = {
    "عاد": {
        "en": "Aad",
        "prophet": "هود",
        "location": "أحقاف",
        "fate_ar": "أهلكوا بريح صرصر",
        "fate_en": "Destroyed by a furious wind",
        "key_suras": [7, 11, 26, 41, 46, 51, 54, 69, 89],
    },
    "ثمود": {
        "en": "Thamud",
        "prophet": "صالح",
        "location": "الحجر",
        "fate_ar": "أهلكوا بالصيحة",
        "fate_en": "Destroyed by the blast",
        "key_suras": [7, 11, 26, 27, 54, 91],
    },
    "قوم لوط": {
        "en": "People of Lot",
        "prophet": "لوط",
        "location": "سدوم",
        "fate_ar": "قلبت مدائنهم",
        "fate_en": "Their cities were overturned",
        "key_suras": [7, 11, 15, 26, 27, 29, 54],
    },
    "فرعون": {
        "en": "Pharaoh's people",
        "prophet": "موسى",
        "location": "مصر",
        "fate_ar": "غرقوا في البحر",
        "fate_en": "Drowned in the sea",
        "key_suras": [7, 10, 20, 26, 28, 40, 43, 44],
    },
    "أصحاب الأيكة": {
        "en": "People of the Thicket",
        "prophet": "شعيب",
        "location": "مدين",
        "fate_ar": "أخذتهم الصيحة",
        "fate_en": "Seized by the blast",
        "key_suras": [15, 26, 38, 50],
    },
    "بنو إسرائيل": {
        "en": "Children of Israel",
        "prophet": "موسى",
        "location": "فلسطين",
        "fate_ar": "أمة مختارة ثم ضلت",
        "fate_en": "Chosen nation that strayed",
        "key_suras": [2, 5, 7, 17, 20, 26],
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Entity:
    """A recognized entity in text."""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    english_name: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityAnalysis:
    """Complete entity analysis of a text."""
    original_text: str
    entities: List[Entity]
    entity_counts: Dict[str, int]
    primary_entities: List[Entity]
    context_summary: Dict[str, str]


# =============================================================================
# NER SERVICE
# =============================================================================

class NERService:
    """
    Named Entity Recognition service for Quranic text.

    Features:
    - Identify prophets, angels, places, events
    - Multi-alias support
    - Confidence scoring
    - Context extraction
    """

    def __init__(self):
        self._prophets = PROPHETS
        self._angels = ANGELS
        self._places = PLACES
        self._events = EVENTS
        self._divine_names = DIVINE_NAMES
        self._nations = NATIONS

        # Build lookup dictionaries
        self._entity_patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[str, Tuple[EntityType, str, Dict]]:
        """Build pattern lookup dictionary."""
        patterns = {}

        # Add prophets
        for name, data in self._prophets.items():
            patterns[name] = (EntityType.PROPHET, data["en"], data)
            for alias in data.get("aliases", []):
                patterns[alias] = (EntityType.PROPHET, data["en"], data)

        # Add angels
        for name, data in self._angels.items():
            patterns[name] = (EntityType.ANGEL, data["en"], data)
            for alias in data.get("aliases", []):
                patterns[alias] = (EntityType.ANGEL, data["en"], data)

        # Add places
        for name, data in self._places.items():
            patterns[name] = (EntityType.PLACE, data["en"], data)
            for alias in data.get("aliases", []):
                patterns[alias] = (EntityType.PLACE, data["en"], data)

        # Add divine names
        for name, data in self._divine_names.items():
            patterns[name] = (EntityType.DIVINE_NAME, data["en"], data)

        # Add nations
        for name, data in self._nations.items():
            patterns[name] = (EntityType.NATION, data["en"], data)

        return patterns

    def extract_entities(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> EntityAnalysis:
        """
        Extract all named entities from text.

        Arabic: استخراج جميع الكيانات المسماة من النص
        """
        entities = []
        entity_counts = defaultdict(int)

        # Search for each pattern
        for pattern, (entity_type, en_name, metadata) in self._entity_patterns.items():
            # Find all occurrences
            start = 0
            while True:
                pos = text.find(pattern, start)
                if pos == -1:
                    break

                # Calculate confidence based on context
                confidence = self._calculate_confidence(text, pattern, pos)

                if confidence >= min_confidence:
                    entity = Entity(
                        text=pattern,
                        entity_type=entity_type,
                        start_pos=pos,
                        end_pos=pos + len(pattern),
                        english_name=en_name,
                        confidence=confidence,
                        metadata=metadata,
                    )
                    entities.append(entity)
                    entity_counts[entity_type.value] += 1

                start = pos + 1

        # Sort by position
        entities.sort(key=lambda e: e.start_pos)

        # Remove duplicates (overlapping entities)
        entities = self._remove_overlaps(entities)

        # Find primary entities (highest confidence per type)
        primary = self._get_primary_entities(entities)

        # Generate context summary
        context = self._generate_context_summary(entities)

        return EntityAnalysis(
            original_text=text,
            entities=entities,
            entity_counts=dict(entity_counts),
            primary_entities=primary,
            context_summary=context,
        )

    def _calculate_confidence(
        self,
        text: str,
        pattern: str,
        position: int,
    ) -> float:
        """Calculate confidence score for entity match."""
        confidence = 0.8  # Base confidence

        # Check for word boundaries
        if position > 0 and text[position - 1].isalpha():
            confidence -= 0.2
        if position + len(pattern) < len(text) and text[position + len(pattern)].isalpha():
            confidence -= 0.2

        # Boost for exact matches
        if len(pattern) > 3:
            confidence += 0.1

        return min(1.0, max(0.0, confidence))

    def _remove_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping higher confidence ones."""
        if not entities:
            return entities

        result = []
        prev = entities[0]

        for entity in entities[1:]:
            if entity.start_pos >= prev.end_pos:
                result.append(prev)
                prev = entity
            elif entity.confidence > prev.confidence:
                prev = entity

        result.append(prev)
        return result

    def _get_primary_entities(self, entities: List[Entity]) -> List[Entity]:
        """Get primary (highest confidence) entity for each type."""
        type_best = {}

        for entity in entities:
            key = entity.entity_type.value
            if key not in type_best or entity.confidence > type_best[key].confidence:
                type_best[key] = entity

        return list(type_best.values())

    def _generate_context_summary(self, entities: List[Entity]) -> Dict[str, str]:
        """Generate context summary from entities."""
        prophets = [e.english_name for e in entities if e.entity_type == EntityType.PROPHET]
        places = [e.english_name for e in entities if e.entity_type == EntityType.PLACE]
        angels = [e.english_name for e in entities if e.entity_type == EntityType.ANGEL]

        summary_parts_ar = []
        summary_parts_en = []

        if prophets:
            summary_parts_ar.append(f"أنبياء: {', '.join(prophets[:3])}")
            summary_parts_en.append(f"Prophets: {', '.join(prophets[:3])}")

        if places:
            summary_parts_ar.append(f"أماكن: {', '.join(places[:3])}")
            summary_parts_en.append(f"Places: {', '.join(places[:3])}")

        if angels:
            summary_parts_ar.append(f"ملائكة: {', '.join(angels[:3])}")
            summary_parts_en.append(f"Angels: {', '.join(angels[:3])}")

        return {
            "ar": " | ".join(summary_parts_ar) if summary_parts_ar else "لا توجد كيانات محددة",
            "en": " | ".join(summary_parts_en) if summary_parts_en else "No specific entities",
        }

    def get_entity_details(
        self,
        entity_name: str,
        entity_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about an entity."""
        name_lower = entity_name.lower()

        # Search prophets
        if not entity_type or entity_type == "prophet":
            for prophet_ar, data in self._prophets.items():
                if (entity_name == prophet_ar or
                    entity_name.lower() == data["en"].lower() or
                    entity_name in data.get("aliases", [])):
                    return {
                        "type": "prophet",
                        "name_ar": prophet_ar,
                        "name_en": data["en"],
                        "mentions": data["mentions"],
                        "key_suras": data["key_suras"],
                        "aliases": data.get("aliases", []),
                        "description_ar": data["description_ar"],
                        "description_en": data["description_en"],
                    }

        # Search places
        if not entity_type or entity_type == "place":
            for place_ar, data in self._places.items():
                if (entity_name == place_ar or
                    entity_name.lower() == data["en"].lower() or
                    entity_name in data.get("aliases", [])):
                    return {
                        "type": "place",
                        "name_ar": place_ar,
                        "name_en": data["en"],
                        "place_type": data["type"],
                        "key_suras": data["key_suras"],
                        "significance_ar": data["significance_ar"],
                        "significance_en": data["significance_en"],
                    }

        # Search nations
        if not entity_type or entity_type == "nation":
            for nation_ar, data in self._nations.items():
                if entity_name == nation_ar or entity_name.lower() == data["en"].lower():
                    return {
                        "type": "nation",
                        "name_ar": nation_ar,
                        "name_en": data["en"],
                        "prophet": data["prophet"],
                        "key_suras": data["key_suras"],
                        "fate_ar": data["fate_ar"],
                        "fate_en": data["fate_en"],
                    }

        return None

    def get_all_prophets(self) -> List[Dict[str, Any]]:
        """Get list of all prophets."""
        return [
            {
                "name_ar": name,
                "name_en": data["en"],
                "mentions": data["mentions"],
                "key_suras": data["key_suras"][:3],
                "description_ar": data["description_ar"],
                "description_en": data["description_en"],
            }
            for name, data in self._prophets.items()
        ]

    def get_all_places(self) -> List[Dict[str, Any]]:
        """Get list of all places."""
        return [
            {
                "name_ar": name,
                "name_en": data["en"],
                "type": data["type"],
                "key_suras": data["key_suras"],
                "significance_en": data["significance_en"],
            }
            for name, data in self._places.items()
        ]

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get list of all events."""
        return [
            {
                "name_ar": name,
                "name_en": data["en"],
                "prophet": data["prophet"],
                "type": data["type"],
                "key_suras": data["key_suras"],
                "description_en": data["description_en"],
            }
            for name, data in self._events.items()
        ]

    def get_entity_stats(self) -> Dict[str, Any]:
        """Get statistics about all entities."""
        return {
            "prophets": len(self._prophets),
            "angels": len(self._angels),
            "places": len(self._places),
            "events": len(self._events),
            "divine_names": len(self._divine_names),
            "nations": len(self._nations),
            "total_patterns": len(self._entity_patterns),
        }


# =============================================================================
# ENTITY RELATIONSHIPS DATA (PHASE 8)
# =============================================================================

ENTITY_RELATIONSHIPS = {
    # Prophet-to-Prophet relationships
    "إبراهيم_إسماعيل": {
        "type": "father_son",
        "entities": ["إبراهيم", "إسماعيل"],
        "description_ar": "إبراهيم أبو إسماعيل",
        "description_en": "Ibrahim is the father of Ismail",
        "shared_events": ["الذبح", "بناء الكعبة"],
        "shared_themes": ["sacrifice", "submission", "faith"],
        "key_verses": ["37:102-107", "2:127"],
    },
    "إبراهيم_إسحاق": {
        "type": "father_son",
        "entities": ["إبراهيم", "إسحاق"],
        "description_ar": "إبراهيم أبو إسحاق من سارة",
        "description_en": "Ibrahim is the father of Ishaq from Sarah",
        "shared_events": ["البشارة بإسحاق"],
        "shared_themes": ["divine_promise", "blessing"],
        "key_verses": ["11:69-73", "51:24-30"],
    },
    "إسحاق_يعقوب": {
        "type": "father_son",
        "entities": ["إسحاق", "يعقوب"],
        "description_ar": "إسحاق أبو يعقوب",
        "description_en": "Ishaq is the father of Yaqub",
        "shared_events": [],
        "shared_themes": ["prophetic_lineage", "blessing"],
        "key_verses": ["12:6", "19:49"],
    },
    "يعقوب_يوسف": {
        "type": "father_son",
        "entities": ["يعقوب", "يوسف"],
        "description_ar": "يعقوب أبو يوسف",
        "description_en": "Yaqub is the father of Yusuf",
        "shared_events": ["رؤيا يوسف", "فراق يوسف", "لقاء يوسف"],
        "shared_themes": ["patience", "family", "divine_plan"],
        "key_verses": ["12:4-6", "12:93-100"],
    },
    "موسى_هارون": {
        "type": "brothers",
        "entities": ["موسى", "هارون"],
        "description_ar": "موسى وهارون أخوان",
        "description_en": "Musa and Harun are brothers",
        "shared_events": ["مواجهة فرعون", "خروج بني إسرائيل"],
        "shared_themes": ["prophethood", "liberation", "teamwork"],
        "key_verses": ["20:29-36", "26:13"],
    },
    "زكريا_يحيى": {
        "type": "father_son",
        "entities": ["زكريا", "يحيى"],
        "description_ar": "زكريا أبو يحيى",
        "description_en": "Zakariya is the father of Yahya",
        "shared_events": ["استجابة الدعاء"],
        "shared_themes": ["divine_gift", "miracle", "piety"],
        "key_verses": ["19:2-15", "3:38-41"],
    },
    "موسى_شعيب": {
        "type": "father_in_law",
        "entities": ["موسى", "شعيب"],
        "description_ar": "شعيب صهر موسى",
        "description_en": "Shuayb is the father-in-law of Musa",
        "shared_events": ["إقامة موسى في مدين"],
        "shared_themes": ["trust", "honesty", "marriage"],
        "key_verses": ["28:22-28"],
    },
    "عيسى_مريم": {
        "type": "mother_son",
        "entities": ["عيسى", "مريم"],
        "description_ar": "مريم أم عيسى",
        "description_en": "Maryam is the mother of Isa",
        "shared_events": ["الولادة المعجزة", "الدفاع عن مريم"],
        "shared_themes": ["miracle", "chastity", "divine_honor"],
        "key_verses": ["19:16-34", "3:45-47"],
    },
    # Prophet parallel experiences
    "يوسف_موسى_parallel": {
        "type": "parallel_experience",
        "entities": ["يوسف", "موسى"],
        "description_ar": "كلاهما في مصر وكلاهما في مناصب عليا",
        "description_en": "Both were in Egypt and both held high positions",
        "shared_events": ["السجن/الاضطهاد", "الوصول للسلطة"],
        "shared_themes": ["patience", "divine_plan", "leadership", "egypt"],
        "key_verses": ["12:54-57", "28:14"],
    },
    "نوح_لوط_parallel": {
        "type": "parallel_experience",
        "entities": ["نوح", "لوط"],
        "description_ar": "كلاهما دعا قومه فكذبوه فأهلك الله قومهما",
        "description_en": "Both called their people who rejected them, then Allah destroyed their people",
        "shared_events": ["الدعوة", "التكذيب", "العذاب"],
        "shared_themes": ["warning", "divine_punishment", "salvation_of_believers"],
        "key_verses": ["11:25-48", "11:77-83"],
    },
    "إبراهيم_محمد_parallel": {
        "type": "parallel_experience",
        "entities": ["إبراهيم", "محمد"],
        "description_ar": "كلاهما حطم الأصنام ودعا للتوحيد",
        "description_en": "Both destroyed idols and called to monotheism",
        "shared_events": ["تحطيم الأصنام", "الدعوة للتوحيد", "الهجرة"],
        "shared_themes": ["monotheism", "courage", "migration"],
        "key_verses": ["21:57-58", "8:30"],
    },
    # Prophet-Place relationships
    "موسى_مصر": {
        "type": "prophet_place",
        "entities": ["موسى", "مصر"],
        "description_ar": "موسى نشأ في مصر وواجه فرعون فيها",
        "description_en": "Musa grew up in Egypt and confronted Pharaoh there",
        "shared_events": ["النشأة", "مواجهة فرعون", "الخروج"],
        "shared_themes": ["liberation", "divine_confrontation"],
        "key_verses": ["28:3-43", "20:9-79"],
    },
    "إبراهيم_مكة": {
        "type": "prophet_place",
        "entities": ["إبراهيم", "مكة"],
        "description_ar": "إبراهيم بنى الكعبة في مكة",
        "description_en": "Ibrahim built the Kaaba in Mecca",
        "shared_events": ["بناء الكعبة", "إسكان إسماعيل"],
        "shared_themes": ["worship", "pilgrimage", "legacy"],
        "key_verses": ["2:125-127", "14:35-37"],
    },
    "محمد_المدينة": {
        "type": "prophet_place",
        "entities": ["محمد", "المدينة"],
        "description_ar": "المدينة دار هجرة النبي محمد",
        "description_en": "Medina is the city of Prophet Muhammad's migration",
        "shared_events": ["الهجرة", "بناء المسجد", "تأسيس الدولة"],
        "shared_themes": ["migration", "community", "state_building"],
        "key_verses": ["9:40", "9:100-101"],
    },
    # Prophet-Event relationships
    "نوح_الطوفان": {
        "type": "prophet_event",
        "entities": ["نوح", "الطوفان"],
        "description_ar": "الطوفان حدث في عهد نوح",
        "description_en": "The Flood occurred during the time of Nuh",
        "shared_themes": ["divine_punishment", "salvation", "new_beginning"],
        "key_verses": ["11:25-49", "71:1-28"],
    },
    "محمد_الإسراء": {
        "type": "prophet_event",
        "entities": ["محمد", "الإسراء"],
        "description_ar": "الإسراء معجزة النبي محمد",
        "description_en": "The Night Journey was a miracle of Prophet Muhammad",
        "shared_themes": ["miracle", "divine_honor", "prayer"],
        "key_verses": ["17:1"],
    },
}

# Thematic parallels between prophets
PROPHET_THEMATIC_PARALLELS = {
    "patience_under_trial": {
        "theme_ar": "الصبر على الابتلاء",
        "theme_en": "Patience Under Trial",
        "prophets": ["أيوب", "يوسف", "يعقوب", "موسى"],
        "description_en": "Prophets who demonstrated exceptional patience during severe trials",
        "key_lessons": [
            {"ar": "الصبر مفتاح الفرج", "en": "Patience is the key to relief"},
            {"ar": "البلاء بقدر الإيمان", "en": "Trials are proportional to faith"},
        ],
    },
    "confronting_tyrants": {
        "theme_ar": "مواجهة الطغاة",
        "theme_en": "Confronting Tyrants",
        "prophets": ["موسى", "إبراهيم", "شعيب", "صالح", "هود"],
        "description_en": "Prophets who stood against oppressive rulers or people",
        "key_lessons": [
            {"ar": "الحق يعلو ولا يعلى عليه", "en": "Truth prevails"},
            {"ar": "الشجاعة في مواجهة الباطل", "en": "Courage in facing falsehood"},
        ],
    },
    "family_sacrifice": {
        "theme_ar": "التضحية من أجل الأسرة",
        "theme_en": "Family Sacrifice",
        "prophets": ["إبراهيم", "يعقوب", "نوح"],
        "description_en": "Prophets who made great sacrifices related to family",
        "key_lessons": [
            {"ar": "الإيمان فوق العاطفة", "en": "Faith above emotion"},
            {"ar": "التوكل في أصعب اللحظات", "en": "Trust in the hardest moments"},
        ],
    },
    "divine_miracles": {
        "theme_ar": "المعجزات الإلهية",
        "theme_en": "Divine Miracles",
        "prophets": ["موسى", "عيسى", "إبراهيم", "سليمان"],
        "description_en": "Prophets who were granted extraordinary miracles",
        "key_lessons": [
            {"ar": "الله على كل شيء قدير", "en": "Allah has power over all things"},
            {"ar": "المعجزات دليل صدق الأنبياء", "en": "Miracles prove prophets' truthfulness"},
        ],
    },
    "leadership_wisdom": {
        "theme_ar": "القيادة والحكمة",
        "theme_en": "Leadership and Wisdom",
        "prophets": ["داود", "سليمان", "يوسف", "موسى"],
        "description_en": "Prophets who demonstrated exceptional leadership and wisdom",
        "key_lessons": [
            {"ar": "العدل أساس الملك", "en": "Justice is the foundation of rule"},
            {"ar": "الحكمة في التعامل مع الناس", "en": "Wisdom in dealing with people"},
        ],
    },
}


class EntityRelationshipService:
    """
    Enhanced NER service with entity relationships.

    Features:
    - Track relationships between entities
    - Identify parallel experiences
    - Map thematic connections
    - Build entity knowledge graph
    """

    def __init__(self, ner_service_instance):
        self._ner = ner_service_instance
        self._relationships = ENTITY_RELATIONSHIPS
        self._parallels = PROPHET_THEMATIC_PARALLELS

    def get_entity_relationships(
        self,
        entity_name: str,
    ) -> Dict[str, Any]:
        """Get all relationships for an entity."""
        relationships = []

        for rel_id, rel_data in self._relationships.items():
            if entity_name in rel_data["entities"]:
                other_entity = [e for e in rel_data["entities"] if e != entity_name]
                relationships.append({
                    "relationship_id": rel_id,
                    "type": rel_data["type"],
                    "related_entity": other_entity[0] if other_entity else entity_name,
                    "description_ar": rel_data["description_ar"],
                    "description_en": rel_data["description_en"],
                    "shared_events": rel_data.get("shared_events", []),
                    "shared_themes": rel_data.get("shared_themes", []),
                    "key_verses": rel_data.get("key_verses", []),
                })

        return {
            "entity": entity_name,
            "relationships": relationships,
            "count": len(relationships),
        }

    def get_parallel_experiences(
        self,
        prophet_name: str,
    ) -> List[Dict[str, Any]]:
        """Get prophets with parallel experiences."""
        parallels = []

        for rel_id, rel_data in self._relationships.items():
            if rel_data["type"] == "parallel_experience" and prophet_name in rel_data["entities"]:
                other_prophet = [e for e in rel_data["entities"] if e != prophet_name][0]
                parallels.append({
                    "prophet": other_prophet,
                    "description_ar": rel_data["description_ar"],
                    "description_en": rel_data["description_en"],
                    "shared_themes": rel_data["shared_themes"],
                    "key_verses": rel_data["key_verses"],
                })

        return parallels

    def get_thematic_parallels(
        self,
        theme: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get thematic parallels between prophets."""
        if theme:
            theme_lower = theme.lower()
            matching = [
                {
                    "theme_id": tid,
                    "theme_ar": data["theme_ar"],
                    "theme_en": data["theme_en"],
                    "prophets": data["prophets"],
                    "description_en": data["description_en"],
                    "key_lessons": data["key_lessons"],
                }
                for tid, data in self._parallels.items()
                if theme_lower in tid or theme_lower in data["theme_en"].lower()
            ]
            return matching

        return [
            {
                "theme_id": tid,
                "theme_ar": data["theme_ar"],
                "theme_en": data["theme_en"],
                "prophets": data["prophets"],
                "description_en": data["description_en"],
                "key_lessons": data["key_lessons"],
            }
            for tid, data in self._parallels.items()
        ]

    def get_prophets_by_theme(
        self,
        theme_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get prophets associated with a specific theme."""
        if theme_id not in self._parallels:
            return None

        data = self._parallels[theme_id]

        # Get prophet details
        prophet_details = []
        for prophet_ar in data["prophets"]:
            details = self._ner.get_entity_details(prophet_ar, "prophet")
            if details:
                prophet_details.append(details)

        return {
            "theme_id": theme_id,
            "theme_ar": data["theme_ar"],
            "theme_en": data["theme_en"],
            "description_en": data["description_en"],
            "prophets": prophet_details,
            "key_lessons": data["key_lessons"],
        }

    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get data for visualizing entity relationships as a graph."""
        nodes = []
        edges = []

        # Collect unique entities
        entity_set = set()
        for rel_data in self._relationships.values():
            entity_set.update(rel_data["entities"])

        # Create nodes
        for entity in entity_set:
            entity_details = self._ner.get_entity_details(entity)
            node_type = entity_details.get("type", "unknown") if entity_details else "unknown"
            nodes.append({
                "id": entity,
                "label": entity,
                "type": node_type,
            })

        # Create edges
        for rel_id, rel_data in self._relationships.items():
            if len(rel_data["entities"]) >= 2:
                edges.append({
                    "id": rel_id,
                    "source": rel_data["entities"][0],
                    "target": rel_data["entities"][1],
                    "type": rel_data["type"],
                    "label": rel_data["description_en"][:50],
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def find_connection_path(
        self,
        entity1: str,
        entity2: str,
        max_depth: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Find connection path between two entities using BFS."""
        from collections import deque

        # Build adjacency list
        adjacency = defaultdict(list)
        for rel_id, rel_data in self._relationships.items():
            entities = rel_data["entities"]
            if len(entities) >= 2:
                adjacency[entities[0]].append((entities[1], rel_id, rel_data))
                adjacency[entities[1]].append((entities[0], rel_id, rel_data))

        # BFS
        queue = deque([(entity1, [entity1], [])])
        visited = {entity1}

        while queue:
            current, path, rels = queue.popleft()

            if current == entity2:
                return {
                    "found": True,
                    "path": path,
                    "relationships": rels,
                    "path_length": len(path) - 1,
                }

            if len(path) > max_depth:
                continue

            for neighbor, rel_id, rel_data in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_rels = rels + [{
                        "id": rel_id,
                        "type": rel_data["type"],
                        "description_en": rel_data["description_en"],
                    }]
                    queue.append((neighbor, path + [neighbor], new_rels))

        return {
            "found": False,
            "message": f"No connection found between {entity1} and {entity2} within depth {max_depth}",
        }

    def get_relationship_statistics(self) -> Dict[str, Any]:
        """Get statistics about entity relationships."""
        type_counts = defaultdict(int)
        theme_counts = defaultdict(int)

        for rel_data in self._relationships.values():
            type_counts[rel_data["type"]] += 1
            for theme in rel_data.get("shared_themes", []):
                theme_counts[theme] += 1

        return {
            "total_relationships": len(self._relationships),
            "relationship_types": dict(type_counts),
            "thematic_parallels": len(self._parallels),
            "theme_distribution": dict(sorted(
                theme_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

ner_service = NERService()
entity_relationship_service = EntityRelationshipService(ner_service)
