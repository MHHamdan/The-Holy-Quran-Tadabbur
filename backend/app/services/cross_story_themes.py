"""
Cross-Story Thematic Connections Service for Quranic Studies.

Provides:
1. Thematic connections across prophet stories
2. Interactive visualization data for exploring connections
3. Shared theme discovery between different narratives
4. Cross-sura similarity scoring

Arabic: خدمة الروابط الموضوعية عبر القصص القرآنية
"""

import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class ThemeCategory(str, Enum):
    """Categories of cross-story themes."""
    TRIALS = "trials"                    # الابتلاءات
    DIVINE_INTERVENTION = "divine_intervention"  # التدخل الإلهي
    COMMUNITY_RESPONSE = "community_response"    # استجابة القوم
    MORAL_LESSON = "moral_lesson"        # الدرس الأخلاقي
    DIVINE_ATTRIBUTE = "divine_attribute"  # الصفات الإلهية
    HUMAN_QUALITY = "human_quality"      # الصفات البشرية
    OUTCOME = "outcome"                  # النتيجة


class ConnectionStrength(str, Enum):
    """Strength of thematic connection."""
    VERY_STRONG = "very_strong"  # Direct parallel
    STRONG = "strong"            # Clear connection
    MODERATE = "moderate"        # Related themes
    WEAK = "weak"                # Distant connection


# =============================================================================
# CROSS-STORY THEMATIC DATA
# =============================================================================

# Comprehensive thematic connections across prophet stories
CROSS_STORY_THEMES = {
    # Trials and Tests
    "patience_in_adversity": {
        "ar": "الصبر على البلاء",
        "en": "Patience in Adversity",
        "category": ThemeCategory.TRIALS,
        "description_ar": "كيف واجه الأنبياء المحن والصعوبات بالصبر",
        "description_en": "How prophets faced hardships with patience",
        "prophets": {
            "أيوب": {
                "relevance": 1.0,
                "aspect": "Physical suffering and loss",
                "suras": [21, 38],
                "key_verses": ["21:83-84", "38:41-44"],
            },
            "يعقوب": {
                "relevance": 0.95,
                "aspect": "Loss of beloved son",
                "suras": [12],
                "key_verses": ["12:18", "12:83-86"],
            },
            "موسى": {
                "relevance": 0.85,
                "aspect": "Persecution and exile",
                "suras": [20, 26, 28],
                "key_verses": ["20:40", "28:21"],
            },
            "محمد": {
                "relevance": 0.9,
                "aspect": "Rejection and persecution",
                "suras": [3, 6, 15],
                "key_verses": ["3:186", "6:34"],
            },
            "نوح": {
                "relevance": 0.88,
                "aspect": "950 years of da'wah",
                "suras": [71, 11],
                "key_verses": ["71:5-6", "11:36-38"],
            },
        },
        "moral_lessons": {
            "ar": ["الصبر مفتاح الفرج", "الابتلاء رفعة للدرجات", "الله مع الصابرين"],
            "en": ["Patience is the key to relief", "Trials elevate ranks", "Allah is with the patient"],
        },
        "related_themes": ["trust_in_allah", "divine_wisdom", "reward_hereafter"],
    },

    "trust_in_allah": {
        "ar": "التوكل على الله",
        "en": "Trust in Allah",
        "category": ThemeCategory.DIVINE_ATTRIBUTE,
        "description_ar": "الاعتماد الكامل على الله في كل الأمور",
        "description_en": "Complete reliance on Allah in all matters",
        "prophets": {
            "إبراهيم": {
                "relevance": 1.0,
                "aspect": "Trust when thrown into fire",
                "suras": [21, 37],
                "key_verses": ["21:68-69", "37:97-99"],
            },
            "موسى": {
                "relevance": 0.95,
                "aspect": "Trust at the Red Sea",
                "suras": [26, 20],
                "key_verses": ["26:61-63", "20:77-78"],
            },
            "يونس": {
                "relevance": 0.9,
                "aspect": "Trust in the whale's belly",
                "suras": [21, 37],
                "key_verses": ["21:87-88", "37:143-144"],
            },
            "هود": {
                "relevance": 0.85,
                "aspect": "Trust against powerful nation",
                "suras": [11, 26],
                "key_verses": ["11:56", "26:123-127"],
            },
            "محمد": {
                "relevance": 0.92,
                "aspect": "Trust during Hijra (cave)",
                "suras": [9],
                "key_verses": ["9:40"],
            },
        },
        "moral_lessons": {
            "ar": ["من توكل على الله فهو حسبه", "التوكل لا ينافي الأخذ بالأسباب", "الله خير الحافظين"],
            "en": ["Whoever trusts Allah, He is sufficient", "Trust doesn't negate taking means", "Allah is the best protector"],
        },
        "related_themes": ["patience_in_adversity", "divine_protection", "faith_strength"],
    },

    "divine_mercy": {
        "ar": "الرحمة الإلهية",
        "en": "Divine Mercy",
        "category": ThemeCategory.DIVINE_ATTRIBUTE,
        "description_ar": "تجليات رحمة الله في قصص الأنبياء",
        "description_en": "Manifestations of Allah's mercy in prophetic stories",
        "prophets": {
            "يوسف": {
                "relevance": 1.0,
                "aspect": "Mercy after years of suffering",
                "suras": [12],
                "key_verses": ["12:90", "12:100"],
            },
            "موسى": {
                "relevance": 0.95,
                "aspect": "Mercy to mother and child",
                "suras": [28, 20],
                "key_verses": ["28:7-13", "20:37-40"],
            },
            "أيوب": {
                "relevance": 0.92,
                "aspect": "Restoration after trial",
                "suras": [21, 38],
                "key_verses": ["21:84", "38:43"],
            },
            "زكريا": {
                "relevance": 0.9,
                "aspect": "Child in old age",
                "suras": [19, 21],
                "key_verses": ["19:7-9", "21:89-90"],
            },
            "يونس": {
                "relevance": 0.88,
                "aspect": "Rescue from whale",
                "suras": [37, 68],
                "key_verses": ["37:145-146", "68:48-50"],
            },
        },
        "moral_lessons": {
            "ar": ["رحمة الله وسعت كل شيء", "لا تيأسوا من رحمة الله", "الله يغفر الذنوب جميعاً"],
            "en": ["Allah's mercy encompasses all things", "Never despair of Allah's mercy", "Allah forgives all sins"],
        },
        "related_themes": ["forgiveness", "hope", "divine_love"],
    },

    "community_opposition": {
        "ar": "معارضة القوم",
        "en": "Community Opposition",
        "category": ThemeCategory.COMMUNITY_RESPONSE,
        "description_ar": "كيف واجه الأنبياء معارضة أقوامهم",
        "description_en": "How prophets faced opposition from their people",
        "prophets": {
            "نوح": {
                "relevance": 1.0,
                "aspect": "950 years of mockery",
                "suras": [11, 71, 23],
                "key_verses": ["11:27", "71:5-7", "23:24-25"],
            },
            "هود": {
                "relevance": 0.95,
                "aspect": "Opposition from 'Ad",
                "suras": [7, 11, 26],
                "key_verses": ["7:65-67", "11:53-54"],
            },
            "صالح": {
                "relevance": 0.93,
                "aspect": "Thamud's rejection",
                "suras": [7, 11, 26],
                "key_verses": ["7:73-76", "11:61-62"],
            },
            "شعيب": {
                "relevance": 0.9,
                "aspect": "Madyan's economic crimes",
                "suras": [7, 11, 26],
                "key_verses": ["7:85-88", "11:84-87"],
            },
            "لوط": {
                "relevance": 0.92,
                "aspect": "Opposition from Sodom",
                "suras": [7, 11, 26],
                "key_verses": ["7:80-84", "11:77-79"],
            },
            "محمد": {
                "relevance": 0.88,
                "aspect": "Quraysh opposition",
                "suras": [25, 38],
                "key_verses": ["25:4-6", "38:4-8"],
            },
        },
        "moral_lessons": {
            "ar": ["الحق لا يتبع الكثرة", "المعارضة لا تعني الباطل", "الأنبياء أسوة في مواجهة المعارضة"],
            "en": ["Truth doesn't follow majority", "Opposition doesn't mean falsehood", "Prophets are role models in facing opposition"],
        },
        "related_themes": ["patience_in_adversity", "steadfastness", "divine_support"],
    },

    "divine_punishment": {
        "ar": "العقوبة الإلهية",
        "en": "Divine Punishment",
        "category": ThemeCategory.OUTCOME,
        "description_ar": "عقاب الله للأقوام الظالمة المكذبة",
        "description_en": "Allah's punishment for oppressive disbelieving nations",
        "prophets": {
            "نوح": {
                "relevance": 1.0,
                "aspect": "The Great Flood",
                "suras": [11, 71, 23],
                "key_verses": ["11:40-44", "71:25-26"],
            },
            "هود": {
                "relevance": 0.98,
                "aspect": "Destructive wind",
                "suras": [41, 46, 69],
                "key_verses": ["41:16", "46:24-25", "69:6-8"],
            },
            "صالح": {
                "relevance": 0.97,
                "aspect": "The Shriek/Earthquake",
                "suras": [7, 11, 91],
                "key_verses": ["7:78", "11:67", "91:14-15"],
            },
            "لوط": {
                "relevance": 0.96,
                "aspect": "Rained stones",
                "suras": [11, 15, 54],
                "key_verses": ["11:82-83", "15:73-74"],
            },
            "شعيب": {
                "relevance": 0.95,
                "aspect": "Day of the Shadow",
                "suras": [26, 7],
                "key_verses": ["26:189", "7:91"],
            },
            "موسى": {
                "relevance": 0.9,
                "aspect": "Pharaoh drowned",
                "suras": [10, 20, 26],
                "key_verses": ["10:90-92", "20:78", "26:66"],
            },
        },
        "moral_lessons": {
            "ar": ["الظلم مؤذن بخراب العمران", "إمهال الله لا يعني إهماله", "التاريخ درس وعبرة"],
            "en": ["Oppression leads to destruction", "Allah's delay is not neglect", "History is a lesson"],
        },
        "related_themes": ["divine_justice", "consequences_of_sin", "warnings"],
    },

    "family_sacrifice": {
        "ar": "التضحية العائلية",
        "en": "Family Sacrifice",
        "category": ThemeCategory.TRIALS,
        "description_ar": "التضحيات العائلية في سبيل الله",
        "description_en": "Family sacrifices for Allah's sake",
        "prophets": {
            "إبراهيم": {
                "relevance": 1.0,
                "aspect": "Sacrifice of Ismail",
                "suras": [37],
                "key_verses": ["37:102-107"],
            },
            "يعقوب": {
                "relevance": 0.95,
                "aspect": "Loss of Yusuf",
                "suras": [12],
                "key_verses": ["12:84-86"],
            },
            "نوح": {
                "relevance": 0.85,
                "aspect": "Son's disbelief and drowning",
                "suras": [11],
                "key_verses": ["11:42-47"],
            },
            "لوط": {
                "relevance": 0.8,
                "aspect": "Wife's betrayal",
                "suras": [66, 11],
                "key_verses": ["66:10", "11:81"],
            },
        },
        "moral_lessons": {
            "ar": ["الولاء لله فوق كل ولاء", "الابتلاء في أقرب الناس", "الإيمان يفوق روابط الدم"],
            "en": ["Loyalty to Allah above all", "Tests come through closest people", "Faith transcends blood ties"],
        },
        "related_themes": ["obedience_to_allah", "patience_in_adversity", "submission"],
    },

    "prophetic_miracles": {
        "ar": "معجزات الأنبياء",
        "en": "Prophetic Miracles",
        "category": ThemeCategory.DIVINE_INTERVENTION,
        "description_ar": "المعجزات التي أيد الله بها أنبياءه",
        "description_en": "Miracles Allah supported His prophets with",
        "prophets": {
            "موسى": {
                "relevance": 1.0,
                "aspect": "Staff, hand, sea parting",
                "suras": [7, 20, 26],
                "key_verses": ["7:107-108", "20:17-23", "26:32-33"],
            },
            "عيسى": {
                "relevance": 0.98,
                "aspect": "Healing, raising dead",
                "suras": [3, 5],
                "key_verses": ["3:49", "5:110"],
            },
            "إبراهيم": {
                "relevance": 0.85,
                "aspect": "Fire became cool",
                "suras": [21],
                "key_verses": ["21:69"],
            },
            "سليمان": {
                "relevance": 0.9,
                "aspect": "Command over jinn, wind, animals",
                "suras": [27, 34, 38],
                "key_verses": ["27:16-17", "34:12", "38:36-38"],
            },
            "صالح": {
                "relevance": 0.82,
                "aspect": "She-camel from rock",
                "suras": [7, 11, 26],
                "key_verses": ["7:73", "11:64", "26:155-156"],
            },
            "محمد": {
                "relevance": 0.95,
                "aspect": "The Quran itself",
                "suras": [17, 2],
                "key_verses": ["17:88", "2:23-24"],
            },
        },
        "moral_lessons": {
            "ar": ["المعجزة تثبت صدق الرسول", "الله قادر على كل شيء", "المعجزة ليست السبب الوحيد للإيمان"],
            "en": ["Miracles prove prophet's truth", "Allah is capable of all things", "Miracles aren't the only reason for faith"],
        },
        "related_themes": ["divine_power", "proof_of_prophethood", "signs_of_allah"],
    },

    "forgiveness_reconciliation": {
        "ar": "العفو والمصالحة",
        "en": "Forgiveness and Reconciliation",
        "category": ThemeCategory.MORAL_LESSON,
        "description_ar": "العفو عند المقدرة والمصالحة مع المسيئين",
        "description_en": "Forgiveness when able and reconciliation with wrongdoers",
        "prophets": {
            "يوسف": {
                "relevance": 1.0,
                "aspect": "Forgiving his brothers",
                "suras": [12],
                "key_verses": ["12:92", "12:90"],
            },
            "محمد": {
                "relevance": 0.95,
                "aspect": "Forgiving Quraysh at conquest",
                "suras": [3],
                "key_verses": ["3:159"],
            },
            "إبراهيم": {
                "relevance": 0.8,
                "aspect": "Praying for his father",
                "suras": [19, 14],
                "key_verses": ["19:47", "14:41"],
            },
        },
        "moral_lessons": {
            "ar": ["العفو من شيم الكرام", "المصالحة خير من القطيعة", "لا تثريب عليكم اليوم"],
            "en": ["Forgiveness is noble character", "Reconciliation is better than enmity", "No blame on you today"],
        },
        "related_themes": ["mercy", "noble_character", "family_bonds"],
    },

    "guidance_calling": {
        "ar": "الدعوة والهداية",
        "en": "Calling to Guidance",
        "category": ThemeCategory.MORAL_LESSON,
        "description_ar": "منهج الأنبياء في الدعوة إلى الله",
        "description_en": "Prophetic methodology in calling to Allah",
        "prophets": {
            "نوح": {
                "relevance": 1.0,
                "aspect": "Day and night, secretly and openly",
                "suras": [71],
                "key_verses": ["71:5-9"],
            },
            "إبراهيم": {
                "relevance": 0.95,
                "aspect": "Logical argumentation",
                "suras": [6, 21],
                "key_verses": ["6:74-79", "21:51-67"],
            },
            "موسى": {
                "relevance": 0.9,
                "aspect": "Gentle speech to Pharaoh",
                "suras": [20],
                "key_verses": ["20:43-44"],
            },
            "عيسى": {
                "relevance": 0.88,
                "aspect": "Miracles and wisdom",
                "suras": [3, 5, 43],
                "key_verses": ["3:49-51", "43:63"],
            },
            "محمد": {
                "relevance": 0.92,
                "aspect": "Wisdom and good preaching",
                "suras": [16],
                "key_verses": ["16:125"],
            },
        },
        "moral_lessons": {
            "ar": ["الحكمة في الدعوة", "اللين أبلغ من الشدة", "الصبر على المدعوين"],
            "en": ["Wisdom in calling", "Gentleness is more effective", "Patience with those called"],
        },
        "related_themes": ["patience_in_adversity", "wisdom", "mercy"],
    },

    "women_of_faith": {
        "ar": "نساء الإيمان",
        "en": "Women of Faith",
        "category": ThemeCategory.HUMAN_QUALITY,
        "description_ar": "قصص النساء المؤمنات في القرآن",
        "description_en": "Stories of believing women in the Quran",
        "prophets": {
            "موسى": {
                "relevance": 1.0,
                "aspect": "Mother of Musa, Asiya",
                "suras": [28, 66],
                "key_verses": ["28:7-13", "66:11"],
            },
            "عيسى": {
                "relevance": 0.98,
                "aspect": "Maryam's story",
                "suras": [19, 3, 66],
                "key_verses": ["19:16-36", "3:42-47", "66:12"],
            },
            "إبراهيم": {
                "relevance": 0.85,
                "aspect": "Sarah and Hajar",
                "suras": [11, 14],
                "key_verses": ["11:69-73", "14:37"],
            },
            "لوط": {
                "relevance": 0.7,
                "aspect": "Wife as contrast (disbeliever)",
                "suras": [66],
                "key_verses": ["66:10"],
            },
            "نوح": {
                "relevance": 0.7,
                "aspect": "Wife as contrast (disbeliever)",
                "suras": [66],
                "key_verses": ["66:10"],
            },
        },
        "moral_lessons": {
            "ar": ["الإيمان لا يتوقف على الجنس", "المرأة الصالحة قدوة", "العلاقة بالله تفوق كل علاقة"],
            "en": ["Faith is not gender-dependent", "Righteous women are role models", "Relationship with Allah transcends all"],
        },
        "related_themes": ["faith_strength", "sacrifice", "divine_selection"],
    },

    "divine_selection": {
        "ar": "الاصطفاء الإلهي",
        "en": "Divine Selection",
        "category": ThemeCategory.DIVINE_ATTRIBUTE,
        "description_ar": "اختيار الله للأنبياء والصالحين",
        "description_en": "Allah's selection of prophets and righteous",
        "prophets": {
            "إبراهيم": {
                "relevance": 1.0,
                "aspect": "Khalil Allah, Imam of mankind",
                "suras": [2, 4],
                "key_verses": ["2:124", "4:125"],
            },
            "موسى": {
                "relevance": 0.95,
                "aspect": "Chosen and brought near",
                "suras": [19, 7],
                "key_verses": ["19:51-52", "7:144"],
            },
            "عيسى": {
                "relevance": 0.92,
                "aspect": "Word from Allah",
                "suras": [3],
                "key_verses": ["3:45"],
            },
            "محمد": {
                "relevance": 0.98,
                "aspect": "Seal of prophets",
                "suras": [33],
                "key_verses": ["33:40"],
            },
            "داود": {
                "relevance": 0.85,
                "aspect": "Given kingdom and wisdom",
                "suras": [38, 27],
                "key_verses": ["38:20", "27:15"],
            },
            "سليمان": {
                "relevance": 0.85,
                "aspect": "Unprecedented kingdom",
                "suras": [38],
                "key_verses": ["38:35"],
            },
        },
        "moral_lessons": {
            "ar": ["الله يختار من يشاء", "الاصطفاء يتبعه مسؤولية", "الله أعلم حيث يجعل رسالته"],
            "en": ["Allah chooses whom He wills", "Selection comes with responsibility", "Allah knows best where to place His message"],
        },
        "related_themes": ["divine_wisdom", "prophethood", "responsibility"],
    },
}


# Prophet relationship graph for visualization
PROPHET_CONNECTIONS = {
    "إبراهيم": {
        "family": ["إسماعيل", "إسحاق", "يعقوب", "لوط"],
        "thematic": ["موسى", "محمد", "نوح"],
        "era": "Ancient",
    },
    "موسى": {
        "family": ["هارون"],
        "thematic": ["إبراهيم", "محمد", "فرعون"],
        "era": "Ancient Egypt",
    },
    "عيسى": {
        "family": ["مريم", "زكريا", "يحيى"],
        "thematic": ["محمد", "موسى"],
        "era": "1st Century CE",
    },
    "محمد": {
        "family": [],
        "thematic": ["إبراهيم", "موسى", "عيسى", "نوح"],
        "era": "7th Century CE",
    },
    "يوسف": {
        "family": ["يعقوب", "إبراهيم"],
        "thematic": ["موسى"],
        "era": "Ancient Egypt",
    },
    "نوح": {
        "family": [],
        "thematic": ["هود", "صالح", "محمد"],
        "era": "Pre-history",
    },
    "أيوب": {
        "family": [],
        "thematic": ["يعقوب"],
        "era": "Unknown",
    },
    "يونس": {
        "family": [],
        "thematic": ["موسى"],
        "era": "Assyrian Period",
    },
    "سليمان": {
        "family": ["داود"],
        "thematic": ["موسى"],
        "era": "Kingdom of Israel",
    },
    "داود": {
        "family": ["سليمان"],
        "thematic": ["موسى"],
        "era": "Kingdom of Israel",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ThematicConnection:
    """A thematic connection between prophet stories."""
    theme_id: str
    theme_ar: str
    theme_en: str
    category: ThemeCategory
    prophets_involved: List[str]
    connection_strength: ConnectionStrength
    shared_verses: List[str]
    moral_lessons_ar: List[str]
    moral_lessons_en: List[str]


@dataclass
class ProphetThemeProfile:
    """Theme profile for a specific prophet."""
    prophet_name: str
    themes: List[Dict[str, Any]]
    key_suras: List[int]
    total_theme_coverage: float
    primary_narrative_aspects: List[str]


@dataclass
class CrossStoryVisualization:
    """Visualization data for cross-story exploration."""
    nodes: List[Dict[str, Any]]  # Prophets and themes as nodes
    edges: List[Dict[str, Any]]  # Connections between nodes
    clusters: List[Dict[str, Any]]  # Theme clusters
    statistics: Dict[str, Any]


# =============================================================================
# CROSS-STORY THEMES SERVICE
# =============================================================================

class CrossStoryThemesService:
    """
    Service for exploring thematic connections across Quranic stories.

    Provides:
    - Theme discovery across prophet narratives
    - Visualization data for interactive exploration
    - Cross-sura similarity scoring
    - Personalized theme recommendations based on study history
    """

    def __init__(self):
        self._themes = CROSS_STORY_THEMES
        self._prophet_connections = PROPHET_CONNECTIONS
        self._theme_index = self._build_theme_index()
        self._prophet_index = self._build_prophet_index()

    def _build_theme_index(self) -> Dict[str, Set[str]]:
        """Build index of prophets by theme."""
        index = defaultdict(set)
        for theme_id, theme_data in self._themes.items():
            for prophet in theme_data.get("prophets", {}):
                index[theme_id].add(prophet)
        return dict(index)

    def _build_prophet_index(self) -> Dict[str, Set[str]]:
        """Build index of themes by prophet."""
        index = defaultdict(set)
        for theme_id, theme_data in self._themes.items():
            for prophet in theme_data.get("prophets", {}):
                index[prophet].add(theme_id)
        return dict(index)

    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Get all cross-story themes."""
        themes = []
        for theme_id, theme_data in self._themes.items():
            themes.append({
                "id": theme_id,
                "name_ar": theme_data["ar"],
                "name_en": theme_data["en"],
                "category": theme_data["category"].value,
                "description_ar": theme_data["description_ar"],
                "description_en": theme_data["description_en"],
                "prophet_count": len(theme_data.get("prophets", {})),
                "related_themes": theme_data.get("related_themes", []),
            })
        return themes

    def get_theme_details(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific theme."""
        theme_data = self._themes.get(theme_id)
        if not theme_data:
            return None

        prophets_detail = []
        for prophet, data in theme_data.get("prophets", {}).items():
            prophets_detail.append({
                "name": prophet,
                "relevance": data["relevance"],
                "aspect": data["aspect"],
                "suras": data["suras"],
                "key_verses": data["key_verses"],
            })

        # Sort by relevance
        prophets_detail.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "id": theme_id,
            "name_ar": theme_data["ar"],
            "name_en": theme_data["en"],
            "category": theme_data["category"].value,
            "description_ar": theme_data["description_ar"],
            "description_en": theme_data["description_en"],
            "prophets": prophets_detail,
            "moral_lessons": theme_data.get("moral_lessons", {}),
            "related_themes": theme_data.get("related_themes", []),
        }

    def get_prophet_themes(self, prophet_name: str) -> ProphetThemeProfile:
        """Get all themes associated with a prophet."""
        themes = []
        all_suras = set()

        for theme_id in self._prophet_index.get(prophet_name, set()):
            theme_data = self._themes[theme_id]
            prophet_data = theme_data["prophets"].get(prophet_name, {})

            themes.append({
                "theme_id": theme_id,
                "theme_ar": theme_data["ar"],
                "theme_en": theme_data["en"],
                "category": theme_data["category"].value,
                "relevance": prophet_data.get("relevance", 0),
                "aspect": prophet_data.get("aspect", ""),
                "key_verses": prophet_data.get("key_verses", []),
            })

            all_suras.update(prophet_data.get("suras", []))

        # Sort by relevance
        themes.sort(key=lambda x: x["relevance"], reverse=True)

        # Calculate total theme coverage
        total_coverage = sum(t["relevance"] for t in themes) / len(themes) if themes else 0

        # Get primary aspects
        primary_aspects = [t["aspect"] for t in themes[:5] if t["aspect"]]

        return ProphetThemeProfile(
            prophet_name=prophet_name,
            themes=themes,
            key_suras=sorted(list(all_suras)),
            total_theme_coverage=round(total_coverage, 3),
            primary_narrative_aspects=primary_aspects,
        )

    def find_shared_themes(
        self,
        prophets: List[str],
        min_relevance: float = 0.5,
    ) -> List[ThematicConnection]:
        """Find themes shared between multiple prophets."""
        shared = []

        for theme_id, theme_data in self._themes.items():
            prophets_in_theme = theme_data.get("prophets", {})
            involved = []
            all_verses = []
            total_relevance = 0

            for prophet in prophets:
                if prophet in prophets_in_theme:
                    prophet_data = prophets_in_theme[prophet]
                    if prophet_data.get("relevance", 0) >= min_relevance:
                        involved.append(prophet)
                        all_verses.extend(prophet_data.get("key_verses", []))
                        total_relevance += prophet_data.get("relevance", 0)

            if len(involved) >= 2:  # At least 2 prophets share this theme
                avg_relevance = total_relevance / len(involved)

                # Determine connection strength
                if avg_relevance >= 0.9 and len(involved) >= 3:
                    strength = ConnectionStrength.VERY_STRONG
                elif avg_relevance >= 0.8:
                    strength = ConnectionStrength.STRONG
                elif avg_relevance >= 0.6:
                    strength = ConnectionStrength.MODERATE
                else:
                    strength = ConnectionStrength.WEAK

                shared.append(ThematicConnection(
                    theme_id=theme_id,
                    theme_ar=theme_data["ar"],
                    theme_en=theme_data["en"],
                    category=theme_data["category"],
                    prophets_involved=involved,
                    connection_strength=strength,
                    shared_verses=all_verses,
                    moral_lessons_ar=theme_data.get("moral_lessons", {}).get("ar", []),
                    moral_lessons_en=theme_data.get("moral_lessons", {}).get("en", []),
                ))

        # Sort by number of prophets involved, then by strength
        shared.sort(key=lambda x: (len(x.prophets_involved), x.connection_strength.value), reverse=True)
        return shared

    def get_visualization_data(
        self,
        focus_prophets: Optional[List[str]] = None,
        focus_themes: Optional[List[str]] = None,
    ) -> CrossStoryVisualization:
        """
        Generate visualization data for interactive exploration.

        Returns nodes (prophets and themes) and edges (connections).
        """
        nodes = []
        edges = []
        node_ids = set()

        # Filter prophets if specified
        prophets_to_include = focus_prophets or list(self._prophet_index.keys())
        themes_to_include = focus_themes or list(self._themes.keys())

        # Add prophet nodes
        for prophet in prophets_to_include:
            if prophet in self._prophet_index:
                node_id = f"prophet_{prophet}"
                node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "type": "prophet",
                    "label": prophet,
                    "label_en": self._get_prophet_name_en(prophet),
                    "theme_count": len(self._prophet_index.get(prophet, set())),
                    "era": self._prophet_connections.get(prophet, {}).get("era", "Unknown"),
                })

        # Add theme nodes and edges
        for theme_id in themes_to_include:
            if theme_id in self._themes:
                theme_data = self._themes[theme_id]
                theme_node_id = f"theme_{theme_id}"

                # Only add theme if it connects to included prophets
                prophets_in_theme = [
                    p for p in theme_data.get("prophets", {})
                    if p in prophets_to_include
                ]

                if prophets_in_theme:
                    node_ids.add(theme_node_id)
                    nodes.append({
                        "id": theme_node_id,
                        "type": "theme",
                        "label": theme_data["ar"],
                        "label_en": theme_data["en"],
                        "category": theme_data["category"].value,
                        "prophet_count": len(prophets_in_theme),
                    })

                    # Add edges from theme to prophets
                    for prophet in prophets_in_theme:
                        prophet_data = theme_data["prophets"][prophet]
                        edges.append({
                            "source": theme_node_id,
                            "target": f"prophet_{prophet}",
                            "weight": prophet_data.get("relevance", 0.5),
                            "aspect": prophet_data.get("aspect", ""),
                        })

        # Add prophet-to-prophet family/thematic connections
        for prophet, connections in self._prophet_connections.items():
            if prophet in prophets_to_include:
                for related in connections.get("family", []) + connections.get("thematic", []):
                    if related in prophets_to_include:
                        # Avoid duplicates
                        edge_id = tuple(sorted([prophet, related]))
                        edges.append({
                            "source": f"prophet_{prophet}",
                            "target": f"prophet_{related}",
                            "type": "family" if related in connections.get("family", []) else "thematic",
                            "weight": 0.8 if related in connections.get("family", []) else 0.5,
                        })

        # Create clusters by theme category
        clusters = []
        for category in ThemeCategory:
            category_themes = [
                t for t in themes_to_include
                if self._themes.get(t, {}).get("category") == category
            ]
            if category_themes:
                clusters.append({
                    "category": category.value,
                    "themes": category_themes,
                    "count": len(category_themes),
                })

        return CrossStoryVisualization(
            nodes=nodes,
            edges=edges,
            clusters=clusters,
            statistics={
                "total_prophets": len([n for n in nodes if n["type"] == "prophet"]),
                "total_themes": len([n for n in nodes if n["type"] == "theme"]),
                "total_connections": len(edges),
                "theme_categories": len(clusters),
            },
        )

    def _get_prophet_name_en(self, arabic_name: str) -> str:
        """Get English name for prophet."""
        name_map = {
            "إبراهيم": "Ibrahim (Abraham)",
            "موسى": "Musa (Moses)",
            "عيسى": "Isa (Jesus)",
            "محمد": "Muhammad",
            "نوح": "Nuh (Noah)",
            "يوسف": "Yusuf (Joseph)",
            "يعقوب": "Ya'qub (Jacob)",
            "إسماعيل": "Ismail (Ishmael)",
            "إسحاق": "Ishaq (Isaac)",
            "داود": "Dawud (David)",
            "سليمان": "Sulayman (Solomon)",
            "أيوب": "Ayyub (Job)",
            "يونس": "Yunus (Jonah)",
            "زكريا": "Zakariya (Zechariah)",
            "يحيى": "Yahya (John)",
            "هود": "Hud",
            "صالح": "Salih",
            "شعيب": "Shu'ayb",
            "لوط": "Lut (Lot)",
            "هارون": "Harun (Aaron)",
        }
        return name_map.get(arabic_name, arabic_name)

    async def get_cross_sura_connections(
        self,
        sura_no: int,
        theme_filter: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find thematic connections from a sura to other suras.

        Arabic: إيجاد الروابط الموضوعية بين السور
        """
        connections = []

        # Find themes that appear in this sura
        themes_in_sura = []
        for theme_id, theme_data in self._themes.items():
            if theme_filter and theme_id != theme_filter:
                continue

            for prophet, prophet_data in theme_data.get("prophets", {}).items():
                if sura_no in prophet_data.get("suras", []):
                    themes_in_sura.append({
                        "theme_id": theme_id,
                        "theme_ar": theme_data["ar"],
                        "theme_en": theme_data["en"],
                        "prophet": prophet,
                        "aspect": prophet_data.get("aspect", ""),
                    })

        # Find other suras with same themes
        for theme_info in themes_in_sura:
            theme_id = theme_info["theme_id"]
            theme_data = self._themes[theme_id]

            for prophet, prophet_data in theme_data.get("prophets", {}).items():
                for other_sura in prophet_data.get("suras", []):
                    if other_sura != sura_no:
                        connections.append({
                            "source_sura": sura_no,
                            "target_sura": other_sura,
                            "theme_id": theme_id,
                            "theme_ar": theme_data["ar"],
                            "theme_en": theme_data["en"],
                            "prophet": prophet,
                            "connection_type": "thematic",
                            "key_verses": prophet_data.get("key_verses", []),
                        })

        # Remove duplicates and sort
        seen = set()
        unique_connections = []
        for conn in connections:
            key = (conn["target_sura"], conn["theme_id"])
            if key not in seen:
                seen.add(key)
                unique_connections.append(conn)

        unique_connections.sort(key=lambda x: x["target_sura"])
        return unique_connections

    def get_theme_journey(
        self,
        start_theme: str,
        max_steps: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate a learning journey starting from a theme.

        Creates a sequence of related themes for structured learning.
        """
        journey = []
        visited = {start_theme}

        current_theme = start_theme
        for step in range(max_steps):
            theme_data = self._themes.get(current_theme)
            if not theme_data:
                break

            # Get prophets for current theme
            prophets = [
                {"name": p, "relevance": d.get("relevance", 0)}
                for p, d in theme_data.get("prophets", {}).items()
            ]
            prophets.sort(key=lambda x: x["relevance"], reverse=True)

            journey.append({
                "step": step + 1,
                "theme_id": current_theme,
                "theme_ar": theme_data["ar"],
                "theme_en": theme_data["en"],
                "category": theme_data["category"].value,
                "top_prophets": prophets[:3],
                "moral_lesson_ar": theme_data.get("moral_lessons", {}).get("ar", [""])[0],
                "moral_lesson_en": theme_data.get("moral_lessons", {}).get("en", [""])[0],
            })

            # Find next unvisited related theme
            related = theme_data.get("related_themes", [])
            next_theme = None
            for rt in related:
                if rt not in visited and rt in self._themes:
                    next_theme = rt
                    visited.add(rt)
                    break

            if not next_theme:
                break
            current_theme = next_theme

        return journey

    def search_themes_by_keyword(
        self,
        keyword: str,
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        """Search themes by keyword."""
        results = []
        keyword_lower = keyword.lower()

        for theme_id, theme_data in self._themes.items():
            # Search in name and description
            name = theme_data["en"].lower() if language == "en" else theme_data["ar"]
            desc = theme_data["description_en"].lower() if language == "en" else theme_data["description_ar"]

            if keyword_lower in name or keyword_lower in desc:
                results.append({
                    "theme_id": theme_id,
                    "theme_ar": theme_data["ar"],
                    "theme_en": theme_data["en"],
                    "category": theme_data["category"].value,
                    "match_type": "name" if keyword_lower in name else "description",
                })

            # Also search in moral lessons
            lessons = theme_data.get("moral_lessons", {}).get(language, [])
            for lesson in lessons:
                if keyword_lower in lesson.lower():
                    results.append({
                        "theme_id": theme_id,
                        "theme_ar": theme_data["ar"],
                        "theme_en": theme_data["en"],
                        "category": theme_data["category"].value,
                        "match_type": "moral_lesson",
                        "matched_lesson": lesson,
                    })
                    break

        return results

    def get_category_themes(self, category: ThemeCategory) -> List[Dict[str, Any]]:
        """Get all themes in a category."""
        themes = []
        for theme_id, theme_data in self._themes.items():
            if theme_data["category"] == category:
                themes.append({
                    "theme_id": theme_id,
                    "theme_ar": theme_data["ar"],
                    "theme_en": theme_data["en"],
                    "prophet_count": len(theme_data.get("prophets", {})),
                })
        return themes


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

cross_story_service = CrossStoryThemesService()
