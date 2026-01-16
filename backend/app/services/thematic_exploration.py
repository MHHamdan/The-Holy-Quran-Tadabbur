"""
Interactive Thematic Exploration Service.

Provides interactive exploration of Quranic themes with:
1. Theme-based navigation with connections
2. Life lessons mapped to real-world situations
3. User exploration journey tracking
4. Personalized theme recommendations
5. Interactive visualization data

Arabic: خدمة الاستكشاف الموضوعي التفاعلي
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# THEMATIC CATEGORIES
# =============================================================================

class ThemeCategory(str, Enum):
    """Main theme categories."""
    FAITH = "faith"
    ETHICS = "ethics"
    WORSHIP = "worship"
    STORIES = "stories"
    AFTERLIFE = "afterlife"
    SOCIAL = "social"
    NATURE = "nature"
    HISTORY = "history"


class ExplorationMode(str, Enum):
    """User exploration modes."""
    GUIDED = "guided"           # System-recommended path
    FREE = "free"               # User chooses freely
    GOAL_ORIENTED = "goal"      # Based on study goals
    SITUATIONAL = "situational" # Based on life situations


# =============================================================================
# COMPREHENSIVE THEME DATABASE
# =============================================================================

THEMES = {
    # ============= FAITH THEMES =============
    "tawhid": {
        "ar": "التوحيد",
        "en": "Monotheism (Tawhid)",
        "category": ThemeCategory.FAITH,
        "description_ar": "إفراد الله بالعبادة والربوبية والأسماء والصفات",
        "description_en": "Affirming Allah's Oneness in worship, lordship, and attributes",
        "key_suras": [112, 1, 2, 3, 6, 7],
        "key_verses": ["112:1-4", "2:255", "59:22-24", "3:18"],
        "connected_themes": ["ibadah", "divine_names", "shirk_avoidance"],
        "life_lessons": [
            {
                "situation_ar": "عند الشعور بالضياع",
                "situation_en": "When feeling lost",
                "lesson_ar": "التوحيد يمنح الإنسان وجهة واضحة في الحياة",
                "lesson_en": "Tawhid gives a clear direction in life",
                "verses": ["6:161-162"],
            },
            {
                "situation_ar": "عند مواجهة الخوف",
                "situation_en": "When facing fear",
                "lesson_ar": "من يعرف الله لا يخاف من غيره",
                "lesson_en": "One who knows Allah fears none other",
                "verses": ["3:173-175"],
            },
        ],
        "prophets": ["إبراهيم", "محمد"],
        "exploration_questions": [
            {
                "ar": "كيف يؤثر التوحيد على حياتي اليومية؟",
                "en": "How does Tawhid affect my daily life?",
            },
            {
                "ar": "ما الفرق بين توحيد الربوبية وتوحيد الألوهية؟",
                "en": "What's the difference between Tawhid al-Rububiyyah and Tawhid al-Uluhiyyah?",
            },
        ],
    },
    "tawakkul": {
        "ar": "التوكل على الله",
        "en": "Reliance on Allah (Tawakkul)",
        "category": ThemeCategory.FAITH,
        "description_ar": "الاعتماد على الله مع الأخذ بالأسباب",
        "description_en": "Depending on Allah while taking practical means",
        "key_suras": [3, 8, 12, 65],
        "key_verses": ["3:159", "65:3", "8:2", "12:67"],
        "connected_themes": ["patience", "dua", "qadar"],
        "life_lessons": [
            {
                "situation_ar": "عند اتخاذ قرارات صعبة",
                "situation_en": "When making difficult decisions",
                "lesson_ar": "استشر ثم توكل على الله",
                "lesson_en": "Consult, then rely on Allah",
                "verses": ["3:159"],
            },
            {
                "situation_ar": "عند القلق على المستقبل",
                "situation_en": "When anxious about the future",
                "lesson_ar": "الرزق مضمون لمن يتوكل",
                "lesson_en": "Provision is guaranteed for one who trusts",
                "verses": ["65:2-3"],
            },
        ],
        "prophets": ["يعقوب", "موسى", "شعيب"],
        "exploration_questions": [
            {
                "ar": "كيف أوازن بين التوكل والتخطيط؟",
                "en": "How do I balance trust and planning?",
            },
        ],
    },
    "patience": {
        "ar": "الصبر",
        "en": "Patience (Sabr)",
        "category": ThemeCategory.ETHICS,
        "description_ar": "الثبات على الحق والتحمل عند الابتلاء",
        "description_en": "Steadfastness in truth and endurance in trials",
        "key_suras": [2, 3, 11, 16, 103],
        "key_verses": ["2:153", "2:155-157", "3:200", "16:126", "11:115"],
        "connected_themes": ["gratitude", "trials", "tawakkul", "hope"],
        "life_lessons": [
            {
                "situation_ar": "عند فقدان عزيز",
                "situation_en": "When losing a loved one",
                "lesson_ar": "إنا لله وإنا إليه راجعون - هذا يجلب البركات",
                "lesson_en": "Inna lillahi wa inna ilayhi raji'un - this brings blessings",
                "verses": ["2:155-157"],
            },
            {
                "situation_ar": "عند طول الانتظار",
                "situation_en": "During long waiting",
                "lesson_ar": "الصبر مفتاح الفرج",
                "lesson_en": "Patience is the key to relief",
                "verses": ["12:83", "94:5-6"],
            },
            {
                "situation_ar": "عند الظلم",
                "situation_en": "When facing injustice",
                "lesson_ar": "الصبر على الأذى من علامات المؤمنين",
                "lesson_en": "Patience with harm is a sign of believers",
                "verses": ["3:186", "41:34-35"],
            },
        ],
        "prophets": ["أيوب", "يعقوب", "موسى", "محمد"],
        "exploration_questions": [
            {
                "ar": "ما أنواع الصبر الثلاثة؟",
                "en": "What are the three types of patience?",
            },
            {
                "ar": "كيف أتعلم الصبر من قصص الأنبياء؟",
                "en": "How can I learn patience from prophets' stories?",
            },
        ],
    },
    "gratitude": {
        "ar": "الشكر",
        "en": "Gratitude (Shukr)",
        "category": ThemeCategory.ETHICS,
        "description_ar": "الاعتراف بنعم الله واستخدامها في طاعته",
        "description_en": "Acknowledging Allah's blessings and using them in obedience",
        "key_suras": [14, 31, 34, 55],
        "key_verses": ["14:7", "31:12", "2:152", "55:1-13"],
        "connected_themes": ["patience", "contentment", "worship"],
        "life_lessons": [
            {
                "situation_ar": "في الحياة اليومية",
                "situation_en": "In daily life",
                "lesson_ar": "الشكر يزيد النعم",
                "lesson_en": "Gratitude increases blessings",
                "verses": ["14:7"],
            },
            {
                "situation_ar": "عند النجاح",
                "situation_en": "After success",
                "lesson_ar": "النجاح من فضل الله وليس من كمال الذات",
                "lesson_en": "Success is from Allah's grace, not self-perfection",
                "verses": ["28:78"],
            },
        ],
        "prophets": ["سليمان", "داود", "إبراهيم"],
        "exploration_questions": [
            {
                "ar": "كيف أكون شاكراً حتى في الشدائد؟",
                "en": "How can I be grateful even in hardships?",
            },
        ],
    },
    "forgiveness": {
        "ar": "المغفرة والعفو",
        "en": "Forgiveness",
        "category": ThemeCategory.ETHICS,
        "description_ar": "طلب مغفرة الله والعفو عن الآخرين",
        "description_en": "Seeking Allah's forgiveness and pardoning others",
        "key_suras": [3, 4, 7, 12, 42],
        "key_verses": ["3:134-135", "7:199", "42:40", "12:92"],
        "connected_themes": ["repentance", "mercy", "self_purification"],
        "life_lessons": [
            {
                "situation_ar": "عند الخلافات العائلية",
                "situation_en": "During family conflicts",
                "lesson_ar": "العفو عند المقدرة من صفات الكرام",
                "lesson_en": "Forgiving when able is a noble trait",
                "verses": ["12:92"],
            },
            {
                "situation_ar": "بعد الذنب",
                "situation_en": "After committing a sin",
                "lesson_ar": "باب التوبة مفتوح دائماً",
                "lesson_en": "The door of repentance is always open",
                "verses": ["39:53", "4:110"],
            },
        ],
        "prophets": ["يوسف", "محمد"],
        "exploration_questions": [
            {
                "ar": "كيف أتعلم المغفرة من قصة يوسف؟",
                "en": "How can I learn forgiveness from Yusuf's story?",
            },
        ],
    },
    "justice": {
        "ar": "العدل",
        "en": "Justice (Adl)",
        "category": ThemeCategory.SOCIAL,
        "description_ar": "إعطاء كل ذي حق حقه والإنصاف",
        "description_en": "Giving everyone their due rights and being fair",
        "key_suras": [4, 5, 16, 49],
        "key_verses": ["4:135", "5:8", "16:90", "49:9"],
        "connected_themes": ["equity", "truth", "witness"],
        "life_lessons": [
            {
                "situation_ar": "عند الشهادة",
                "situation_en": "When giving testimony",
                "lesson_ar": "قل الحق ولو على نفسك",
                "lesson_en": "Speak the truth even against yourself",
                "verses": ["4:135"],
            },
            {
                "situation_ar": "عند التعامل مع الخصوم",
                "situation_en": "When dealing with adversaries",
                "lesson_ar": "العدل واجب حتى مع من تكره",
                "lesson_en": "Justice is obligatory even with those you dislike",
                "verses": ["5:8"],
            },
        ],
        "prophets": ["داود", "سليمان", "موسى"],
        "exploration_questions": [
            {
                "ar": "كيف أكون عادلاً في حياتي اليومية؟",
                "en": "How can I be just in my daily life?",
            },
        ],
    },
    "family_relations": {
        "ar": "صلة الرحم وبر الوالدين",
        "en": "Family Relations",
        "category": ThemeCategory.SOCIAL,
        "description_ar": "الحفاظ على العلاقات الأسرية وإكرام الوالدين",
        "description_en": "Maintaining family ties and honoring parents",
        "key_suras": [17, 31, 46, 4],
        "key_verses": ["17:23-24", "31:14-15", "46:15", "4:36"],
        "connected_themes": ["gratitude", "kindness", "patience"],
        "life_lessons": [
            {
                "situation_ar": "مع الوالدين المسنين",
                "situation_en": "With elderly parents",
                "lesson_ar": "لا تقل لهما أف - كلمة صغيرة بأثر كبير",
                "lesson_en": "Don't say 'uff' - a small word with big impact",
                "verses": ["17:23"],
            },
            {
                "situation_ar": "عند خلاف مع الوالدين",
                "situation_en": "When disagreeing with parents",
                "lesson_ar": "أطعهم إلا في المعصية، وعاملهم بالمعروف دائماً",
                "lesson_en": "Obey them except in sin, and treat them kindly always",
                "verses": ["31:15"],
            },
        ],
        "prophets": ["إبراهيم", "يعقوب", "يوسف"],
        "exploration_questions": [
            {
                "ar": "كيف أبر والديّ في الحياة المعاصرة؟",
                "en": "How do I honor my parents in modern life?",
            },
        ],
    },
    # ============= AFTERLIFE THEMES =============
    "paradise": {
        "ar": "الجنة",
        "en": "Paradise",
        "category": ThemeCategory.AFTERLIFE,
        "description_ar": "دار النعيم المعدة للمتقين",
        "description_en": "The abode of bliss prepared for the righteous",
        "key_suras": [55, 56, 76, 88],
        "key_verses": ["55:46-78", "56:10-40", "76:5-22"],
        "connected_themes": ["good_deeds", "faith", "hope"],
        "life_lessons": [
            {
                "situation_ar": "عند صعوبات الحياة",
                "situation_en": "During life's difficulties",
                "lesson_ar": "تذكر الجنة يهون المصائب",
                "lesson_en": "Remembering Paradise eases hardships",
                "verses": ["9:111"],
            },
        ],
        "exploration_questions": [
            {
                "ar": "ما هي أوصاف الجنة في القرآن؟",
                "en": "What are the descriptions of Paradise in Quran?",
            },
        ],
    },
    "day_of_judgment": {
        "ar": "يوم القيامة",
        "en": "Day of Judgment",
        "category": ThemeCategory.AFTERLIFE,
        "description_ar": "يوم الحساب والجزاء",
        "description_en": "The Day of Reckoning and Recompense",
        "key_suras": [99, 101, 82, 81, 75],
        "key_verses": ["99:1-8", "82:1-19", "75:1-15"],
        "connected_themes": ["accountability", "good_deeds", "repentance"],
        "life_lessons": [
            {
                "situation_ar": "عند اتخاذ القرارات",
                "situation_en": "When making decisions",
                "lesson_ar": "تذكر أنك ستُسأل عن كل شيء",
                "lesson_en": "Remember you will be asked about everything",
                "verses": ["99:7-8"],
            },
        ],
        "exploration_questions": [
            {
                "ar": "ما أسماء يوم القيامة في القرآن؟",
                "en": "What are the names of Judgment Day in Quran?",
            },
        ],
    },
    # ============= PROPHET STORIES =============
    "story_ibrahim": {
        "ar": "قصة إبراهيم عليه السلام",
        "en": "Story of Ibrahim (AS)",
        "category": ThemeCategory.STORIES,
        "description_ar": "أبو الأنبياء وخليل الرحمن",
        "description_en": "Father of Prophets and Friend of the Most Merciful",
        "key_suras": [2, 6, 14, 21, 37],
        "key_verses": ["2:124-141", "6:74-83", "21:51-73", "37:83-113"],
        "connected_themes": ["tawhid", "sacrifice", "family", "tawakkul"],
        "life_lessons": [
            {
                "situation_ar": "عند مواجهة الضغط الاجتماعي",
                "situation_en": "When facing social pressure",
                "lesson_ar": "إبراهيم واجه قومه وحده بالحق",
                "lesson_en": "Ibrahim faced his people alone with truth",
                "verses": ["6:74-79"],
            },
            {
                "situation_ar": "عند صراع الأجيال",
                "situation_en": "During generational conflict",
                "lesson_ar": "احترم والديك حتى لو اختلفت معهم",
                "lesson_en": "Respect your parents even if you disagree",
                "verses": ["19:41-48"],
            },
        ],
        "prophets": ["إبراهيم"],
        "exploration_questions": [
            {
                "ar": "ماذا نتعلم من حوار إبراهيم مع أبيه؟",
                "en": "What do we learn from Ibrahim's dialogue with his father?",
            },
        ],
    },
    "story_yusuf": {
        "ar": "قصة يوسف عليه السلام",
        "en": "Story of Yusuf (AS)",
        "category": ThemeCategory.STORIES,
        "description_ar": "أحسن القصص - قصة الصبر والعفة والعفو",
        "description_en": "The best of stories - patience, chastity, and forgiveness",
        "key_suras": [12],
        "key_verses": ["12:1-111"],
        "connected_themes": ["patience", "forgiveness", "chastity", "dreams", "family"],
        "life_lessons": [
            {
                "situation_ar": "عند الإغراء",
                "situation_en": "When tempted",
                "lesson_ar": "معاذ الله - كلمة يوسف التي أنقذته",
                "lesson_en": "Ma'adh Allah - Yusuf's word that saved him",
                "verses": ["12:23-24"],
            },
            {
                "situation_ar": "عند ظلم الأقارب",
                "situation_en": "When wronged by relatives",
                "lesson_ar": "سامح كما سامح يوسف إخوته",
                "lesson_en": "Forgive as Yusuf forgave his brothers",
                "verses": ["12:92"],
            },
            {
                "situation_ar": "في السجن أو الضيق",
                "situation_en": "In prison or confinement",
                "lesson_ar": "يوسف دعا إلى الله حتى في السجن",
                "lesson_en": "Yusuf called to Allah even in prison",
                "verses": ["12:39-40"],
            },
        ],
        "prophets": ["يوسف"],
        "exploration_questions": [
            {
                "ar": "ما المراحل التي مر بها يوسف؟",
                "en": "What stages did Yusuf go through?",
            },
        ],
    },
    "story_musa": {
        "ar": "قصة موسى عليه السلام",
        "en": "Story of Musa (AS)",
        "category": ThemeCategory.STORIES,
        "description_ar": "أكثر الأنبياء ذكراً في القرآن",
        "description_en": "The most mentioned prophet in the Quran",
        "key_suras": [20, 26, 28, 7],
        "key_verses": ["20:9-99", "28:3-43", "7:103-162"],
        "connected_themes": ["courage", "leadership", "patience", "trust"],
        "life_lessons": [
            {
                "situation_ar": "عند مواجهة الظالم",
                "situation_en": "When facing an oppressor",
                "lesson_ar": "اذهب إلى فرعون - لا تخف من قول الحق",
                "lesson_en": "Go to Pharaoh - don't fear speaking truth",
                "verses": ["20:43-44"],
            },
            {
                "situation_ar": "عند الشعور بعدم الكفاءة",
                "situation_en": "When feeling inadequate",
                "lesson_ar": "موسى طلب من الله أن يشرح صدره ويحل عقدة لسانه",
                "lesson_en": "Musa asked Allah to expand his chest and untie his tongue",
                "verses": ["20:25-28"],
            },
        ],
        "prophets": ["موسى"],
        "exploration_questions": [
            {
                "ar": "ما الدروس من لقاء موسى والخضر؟",
                "en": "What lessons from Musa's meeting with Khidr?",
            },
        ],
    },
    # ============= WORSHIP THEMES =============
    "salah": {
        "ar": "الصلاة",
        "en": "Prayer (Salah)",
        "category": ThemeCategory.WORSHIP,
        "description_ar": "عمود الدين والصلة بين العبد وربه",
        "description_en": "Pillar of religion and connection between servant and Lord",
        "key_suras": [2, 4, 11, 17, 29],
        "key_verses": ["2:238", "4:103", "11:114", "17:78", "29:45"],
        "connected_themes": ["khushu", "dhikr", "tawakkul"],
        "life_lessons": [
            {
                "situation_ar": "عند الضيق",
                "situation_en": "When distressed",
                "lesson_ar": "استعينوا بالصبر والصلاة",
                "lesson_en": "Seek help through patience and prayer",
                "verses": ["2:45", "2:153"],
            },
            {
                "situation_ar": "في الأوقات الصعبة",
                "situation_en": "In difficult times",
                "lesson_ar": "الصلاة تنهى عن الفحشاء والمنكر",
                "lesson_en": "Prayer restrains from evil and wrong",
                "verses": ["29:45"],
            },
        ],
        "exploration_questions": [
            {
                "ar": "كيف أحقق الخشوع في الصلاة؟",
                "en": "How do I achieve khushu' in prayer?",
            },
        ],
    },
    "dua": {
        "ar": "الدعاء",
        "en": "Supplication (Dua)",
        "category": ThemeCategory.WORSHIP,
        "description_ar": "مناجاة الله وطلب حوائج الدنيا والآخرة",
        "description_en": "Intimate conversation with Allah and asking for needs",
        "key_suras": [2, 40, 21, 25],
        "key_verses": ["2:186", "40:60", "21:83-90", "25:77"],
        "connected_themes": ["tawakkul", "hope", "patience"],
        "life_lessons": [
            {
                "situation_ar": "عند الحاجة الملحة",
                "situation_en": "When in urgent need",
                "lesson_ar": "ادعوني أستجب لكم - وعد إلهي",
                "lesson_en": "Call upon Me, I will respond - divine promise",
                "verses": ["40:60"],
            },
            {
                "situation_ar": "عند تأخر الإجابة",
                "situation_en": "When response is delayed",
                "lesson_ar": "الله قريب يجيب دعوة الداع",
                "lesson_en": "Allah is near and responds to the caller",
                "verses": ["2:186"],
            },
        ],
        "prophets": ["زكريا", "أيوب", "إبراهيم", "موسى"],
        "exploration_questions": [
            {
                "ar": "ما آداب الدعاء وأوقات الاستجابة؟",
                "en": "What are the etiquettes of dua and times of acceptance?",
            },
        ],
    },
}


# =============================================================================
# USER EXPLORATION STATE
# =============================================================================

@dataclass
class ExplorationJourney:
    """User's thematic exploration journey."""
    user_id: str
    visited_themes: List[str] = field(default_factory=list)
    saved_lessons: List[Dict[str, Any]] = field(default_factory=list)
    current_theme: Optional[str] = None
    exploration_mode: ExplorationMode = ExplorationMode.GUIDED
    goals: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    total_time_minutes: int = 0


# =============================================================================
# THEMATIC EXPLORATION SERVICE
# =============================================================================

class ThematicExplorationService:
    """
    Interactive thematic exploration service.

    Provides:
    - Theme browsing and navigation
    - Life lessons for real-world situations
    - User journey tracking
    - Personalized recommendations
    """

    def __init__(self):
        self._themes = THEMES
        self._user_journeys: Dict[str, ExplorationJourney] = {}

    def get_all_themes(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all themes, optionally filtered by category."""
        result = []

        for theme_id, theme_data in self._themes.items():
            if category:
                try:
                    cat_enum = ThemeCategory(category)
                    if theme_data["category"] != cat_enum:
                        continue
                except ValueError:
                    pass

            result.append({
                "id": theme_id,
                "name_ar": theme_data["ar"],
                "name_en": theme_data["en"],
                "category": theme_data["category"].value,
                "description_ar": theme_data["description_ar"],
                "description_en": theme_data["description_en"],
                "connected_themes_count": len(theme_data.get("connected_themes", [])),
                "life_lessons_count": len(theme_data.get("life_lessons", [])),
            })

        return result

    def get_categories(self) -> List[Dict[str, str]]:
        """Get all theme categories."""
        categories = {
            ThemeCategory.FAITH: {"ar": "الإيمان", "en": "Faith"},
            ThemeCategory.ETHICS: {"ar": "الأخلاق", "en": "Ethics"},
            ThemeCategory.WORSHIP: {"ar": "العبادات", "en": "Worship"},
            ThemeCategory.STORIES: {"ar": "القصص", "en": "Stories"},
            ThemeCategory.AFTERLIFE: {"ar": "الآخرة", "en": "Afterlife"},
            ThemeCategory.SOCIAL: {"ar": "المجتمع", "en": "Social"},
            ThemeCategory.NATURE: {"ar": "الطبيعة", "en": "Nature"},
            ThemeCategory.HISTORY: {"ar": "التاريخ", "en": "History"},
        }

        return [
            {
                "id": cat.value,
                "name_ar": names["ar"],
                "name_en": names["en"],
                "themes_count": sum(1 for t in self._themes.values() if t["category"] == cat),
            }
            for cat, names in categories.items()
        ]

    def get_theme_details(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a theme."""
        theme = self._themes.get(theme_id)
        if not theme:
            return None

        return {
            "id": theme_id,
            "name_ar": theme["ar"],
            "name_en": theme["en"],
            "category": theme["category"].value,
            "description_ar": theme["description_ar"],
            "description_en": theme["description_en"],
            "key_suras": theme.get("key_suras", []),
            "key_verses": theme.get("key_verses", []),
            "connected_themes": [
                {
                    "id": t_id,
                    "name_ar": self._themes[t_id]["ar"] if t_id in self._themes else t_id,
                    "name_en": self._themes[t_id]["en"] if t_id in self._themes else t_id,
                }
                for t_id in theme.get("connected_themes", [])
                if t_id in self._themes
            ],
            "life_lessons": theme.get("life_lessons", []),
            "prophets": theme.get("prophets", []),
            "exploration_questions": theme.get("exploration_questions", []),
        }

    def get_life_lessons_by_situation(self, situation: str) -> List[Dict[str, Any]]:
        """Find life lessons relevant to a specific situation."""
        results = []
        situation_lower = situation.lower()

        for theme_id, theme_data in self._themes.items():
            for lesson in theme_data.get("life_lessons", []):
                if (situation_lower in lesson["situation_en"].lower() or
                    situation_lower in lesson.get("situation_ar", "")):
                    results.append({
                        "theme_id": theme_id,
                        "theme_name_ar": theme_data["ar"],
                        "theme_name_en": theme_data["en"],
                        **lesson,
                    })

        return results

    def get_exploration_path(
        self,
        start_theme: str,
        depth: int = 3,
    ) -> Dict[str, Any]:
        """Generate an exploration path starting from a theme."""
        if start_theme not in self._themes:
            return {"error": "Theme not found"}

        path = []
        visited = set()
        current_theme = start_theme

        for _ in range(depth):
            if current_theme in visited or current_theme not in self._themes:
                break

            visited.add(current_theme)
            theme = self._themes[current_theme]

            path.append({
                "theme_id": current_theme,
                "name_ar": theme["ar"],
                "name_en": theme["en"],
                "key_verse": theme.get("key_verses", [""])[0] if theme.get("key_verses") else None,
            })

            # Move to connected theme
            connected = theme.get("connected_themes", [])
            unvisited = [t for t in connected if t not in visited and t in self._themes]

            if unvisited:
                current_theme = random.choice(unvisited)
            else:
                break

        return {
            "start_theme": start_theme,
            "path": path,
            "depth": len(path),
            "guidance_ar": "اتبع هذا المسار لاستكشاف المواضيع المترابطة",
            "guidance_en": "Follow this path to explore connected themes",
        }

    def start_journey(
        self,
        user_id: str,
        mode: str = "guided",
        goals: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Start a new exploration journey for a user."""
        try:
            exp_mode = ExplorationMode(mode)
        except ValueError:
            exp_mode = ExplorationMode.GUIDED

        journey = ExplorationJourney(
            user_id=user_id,
            exploration_mode=exp_mode,
            goals=goals or [],
        )

        self._user_journeys[user_id] = journey

        # Recommend starting theme based on mode
        if exp_mode == ExplorationMode.GUIDED:
            start_theme = "tawhid"  # Start with fundamentals
        elif goals:
            start_theme = self._find_theme_for_goal(goals[0])
        else:
            start_theme = random.choice(list(self._themes.keys()))

        journey.current_theme = start_theme

        return {
            "user_id": user_id,
            "journey_started": True,
            "mode": exp_mode.value,
            "starting_theme": self.get_theme_details(start_theme),
            "message_ar": "بدأت رحلتك الاستكشافية، استمتع بالتعلم!",
            "message_en": "Your exploration journey has begun, enjoy learning!",
        }

    def _find_theme_for_goal(self, goal: str) -> str:
        """Find a relevant theme for a study goal."""
        goal_lower = goal.lower()

        goal_mappings = {
            "patience": "patience",
            "faith": "tawhid",
            "prayer": "salah",
            "forgiveness": "forgiveness",
            "family": "family_relations",
            "gratitude": "gratitude",
            "justice": "justice",
            "stories": "story_yusuf",
            "paradise": "paradise",
        }

        for keyword, theme in goal_mappings.items():
            if keyword in goal_lower:
                return theme

        return "tawhid"

    def visit_theme(
        self,
        user_id: str,
        theme_id: str,
    ) -> Dict[str, Any]:
        """Record a theme visit and get theme details."""
        if user_id not in self._user_journeys:
            self.start_journey(user_id)

        journey = self._user_journeys[user_id]

        if theme_id not in self._themes:
            return {"error": "Theme not found"}

        # Record visit
        journey.visited_themes.append(theme_id)
        journey.current_theme = theme_id

        theme_details = self.get_theme_details(theme_id)

        # Suggest next themes
        theme = self._themes[theme_id]
        connected = theme.get("connected_themes", [])
        unvisited_connected = [
            t for t in connected
            if t not in journey.visited_themes and t in self._themes
        ]

        next_suggestions = []
        for t_id in unvisited_connected[:3]:
            t = self._themes[t_id]
            next_suggestions.append({
                "id": t_id,
                "name_ar": t["ar"],
                "name_en": t["en"],
            })

        return {
            "theme": theme_details,
            "journey_progress": {
                "themes_visited": len(set(journey.visited_themes)),
                "current_position": theme_id,
            },
            "next_suggestions": next_suggestions,
        }

    def save_lesson(
        self,
        user_id: str,
        theme_id: str,
        lesson_index: int,
    ) -> Dict[str, Any]:
        """Save a life lesson to user's collection."""
        if user_id not in self._user_journeys:
            self.start_journey(user_id)

        journey = self._user_journeys[user_id]

        if theme_id not in self._themes:
            return {"error": "Theme not found"}

        lessons = self._themes[theme_id].get("life_lessons", [])
        if lesson_index >= len(lessons):
            return {"error": "Lesson not found"}

        lesson = lessons[lesson_index]
        saved = {
            "theme_id": theme_id,
            "theme_name_ar": self._themes[theme_id]["ar"],
            "theme_name_en": self._themes[theme_id]["en"],
            "lesson": lesson,
            "saved_at": datetime.utcnow().isoformat(),
        }

        journey.saved_lessons.append(saved)

        return {
            "status": "saved",
            "lesson": saved,
            "total_saved": len(journey.saved_lessons),
            "message_ar": "تم حفظ الدرس في مجموعتك",
            "message_en": "Lesson saved to your collection",
        }

    def get_journey_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's exploration journey."""
        if user_id not in self._user_journeys:
            return {
                "user_id": user_id,
                "has_journey": False,
                "message_ar": "لم تبدأ رحلة استكشافية بعد",
                "message_en": "You haven't started an exploration journey yet",
            }

        journey = self._user_journeys[user_id]

        return {
            "user_id": user_id,
            "has_journey": True,
            "mode": journey.exploration_mode.value,
            "themes_visited": list(set(journey.visited_themes)),
            "total_visits": len(journey.visited_themes),
            "saved_lessons_count": len(journey.saved_lessons),
            "current_theme": journey.current_theme,
            "goals": journey.goals,
            "started_at": journey.started_at.isoformat(),
        }

    def get_graph_data(self) -> Dict[str, Any]:
        """Get data for visualizing themes as an interactive graph."""
        nodes = []
        edges = []

        for theme_id, theme_data in self._themes.items():
            nodes.append({
                "id": theme_id,
                "label_ar": theme_data["ar"],
                "label_en": theme_data["en"],
                "category": theme_data["category"].value,
                "size": len(theme_data.get("life_lessons", [])) + 5,
            })

            for connected in theme_data.get("connected_themes", []):
                if connected in self._themes:
                    edges.append({
                        "source": theme_id,
                        "target": connected,
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "categories": [c.value for c in ThemeCategory],
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

thematic_exploration_service = ThematicExplorationService()
