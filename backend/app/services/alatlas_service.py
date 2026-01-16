"""
Alatlas (Atlas) Service - Quranic Stories with Arabic Classification

Provides comprehensive Quranic story management with:
- Arabic tagging and classification
- Complete story data (prophets, events, themes, verses, tafsir)
- Graphical representation of relationships
- Search, filter, and categorization features
- Verification and data completeness checking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from datetime import datetime
import re


class StoryCategory(Enum):
    """Categories for Quranic stories - Arabic classifications"""
    PROPHETS = "prophets"           # الأنبياء
    NATIONS = "nations"             # الأمم
    PARABLES = "parables"           # الأمثال
    HISTORICAL = "historical"       # التاريخية
    UNSEEN = "unseen"              # الغيب
    MIRACLES = "miracles"          # المعجزات
    CREATION = "creation"          # الخلق
    AFTERLIFE = "afterlife"        # الآخرة


class StoryTheme(Enum):
    """Thematic classifications for stories"""
    PATIENCE = "patience"           # الصبر
    TRUST = "trust"                # التوكل
    FAITH = "faith"                # الإيمان
    JUSTICE = "justice"            # العدل
    MERCY = "mercy"                # الرحمة
    OBEDIENCE = "obedience"        # الطاعة
    REPENTANCE = "repentance"      # التوبة
    GRATITUDE = "gratitude"        # الشكر
    SACRIFICE = "sacrifice"        # التضحية
    PERSEVERANCE = "perseverance"  # المثابرة
    WISDOM = "wisdom"              # الحكمة
    GUIDANCE = "guidance"          # الهداية
    PUNISHMENT = "punishment"      # العقاب
    REWARD = "reward"              # الثواب
    TAWHID = "tawhid"             # التوحيد
    CREATION = "creation"         # الخلق
    FAMILY = "family"             # الأسرة
    PROPHECY = "prophecy"         # النبوة
    DELIVERANCE = "deliverance"   # النجاة
    FORGIVENESS = "forgiveness"   # المغفرة


class RelationshipType(Enum):
    """Types of relationships between story elements"""
    PROPHET_TO_NATION = "prophet_to_nation"
    PROPHET_TO_PROPHET = "prophet_to_prophet"
    PROPHET_TO_EVENT = "prophet_to_event"
    PROPHET_TO_PLACE = "prophet_to_place"
    EVENT_TO_EVENT = "event_to_event"
    THEME_TO_STORY = "theme_to_story"
    VERSE_TO_STORY = "verse_to_story"
    FATHER_SON = "father_son"
    CONTEMPORARY = "contemporary"
    PREDECESSOR = "predecessor"


@dataclass
class StoryVerse:
    """A verse reference within a story"""
    surah: int
    ayah_start: int
    ayah_end: int
    text_ar: str
    text_en: str
    context_ar: str
    context_en: str


@dataclass
class StoryEvent:
    """An event within a story"""
    id: str
    name_ar: str
    name_en: str
    description_ar: str
    description_en: str
    sequence: int
    verses: List[str]
    significance_ar: str
    significance_en: str


@dataclass
class StoryFigure:
    """A figure (person) within a story"""
    id: str
    name_ar: str
    name_en: str
    role: str
    role_ar: str
    description_ar: str
    description_en: str
    is_prophet: bool


@dataclass
class StoryRelationship:
    """A relationship between story elements"""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    relationship_type: RelationshipType
    description_ar: str
    description_en: str


@dataclass
class Story:
    """Complete Quranic story with all details"""
    id: str
    title_ar: str
    title_en: str
    category: StoryCategory
    category_ar: str
    themes: List[StoryTheme]
    themes_ar: List[str]
    summary_ar: str
    summary_en: str
    figures: List[StoryFigure]
    events: List[StoryEvent]
    verses: List[StoryVerse]
    key_lessons_ar: List[str]
    key_lessons_en: List[str]
    relationships: List[StoryRelationship]
    related_stories: List[str]
    tafsir_references: List[Dict[str, str]]
    completeness_score: float
    is_verified: bool


class AltlasService:
    """
    Service for managing Quranic stories in the Atlas.
    Provides Arabic tagging, complete story data, and graphical representations.
    """

    def __init__(self):
        self._stories: Dict[str, Story] = {}
        self._categories: Dict[str, Dict[str, str]] = {}
        self._themes: Dict[str, Dict[str, str]] = {}
        self._search_index: Dict[str, List[str]] = {}
        self._initialize_categories()
        self._initialize_themes()
        self._initialize_stories()
        self._build_search_index()

    def _initialize_categories(self):
        """Initialize story categories with Arabic names"""
        self._categories = {
            "prophets": {
                "id": "prophets",
                "name_ar": "الأنبياء",
                "name_en": "Prophets",
                "description_ar": "قصص الأنبياء والرسل في القرآن الكريم",
                "description_en": "Stories of prophets and messengers in the Holy Quran",
                "icon": "user-tie",
                "color": "#4CAF50"
            },
            "nations": {
                "id": "nations",
                "name_ar": "الأمم",
                "name_en": "Nations",
                "description_ar": "قصص الأمم السابقة وما حدث لها",
                "description_en": "Stories of previous nations and what happened to them",
                "icon": "users",
                "color": "#2196F3"
            },
            "parables": {
                "id": "parables",
                "name_ar": "الأمثال",
                "name_en": "Parables",
                "description_ar": "الأمثال والقصص الرمزية في القرآن",
                "description_en": "Parables and symbolic stories in the Quran",
                "icon": "book-open",
                "color": "#FF9800"
            },
            "historical": {
                "id": "historical",
                "name_ar": "التاريخية",
                "name_en": "Historical",
                "description_ar": "الأحداث التاريخية المذكورة في القرآن",
                "description_en": "Historical events mentioned in the Quran",
                "icon": "landmark",
                "color": "#9C27B0"
            },
            "unseen": {
                "id": "unseen",
                "name_ar": "الغيب",
                "name_en": "Unseen",
                "description_ar": "قصص عالم الغيب والملائكة والجن",
                "description_en": "Stories of the unseen world, angels, and jinn",
                "icon": "eye-slash",
                "color": "#607D8B"
            },
            "miracles": {
                "id": "miracles",
                "name_ar": "المعجزات",
                "name_en": "Miracles",
                "description_ar": "المعجزات الإلهية والآيات الكونية",
                "description_en": "Divine miracles and cosmic signs",
                "icon": "star",
                "color": "#E91E63"
            },
            "creation": {
                "id": "creation",
                "name_ar": "الخلق",
                "name_en": "Creation",
                "description_ar": "قصص الخلق وبداية الكون والإنسان",
                "description_en": "Stories of creation, the universe, and mankind",
                "icon": "globe",
                "color": "#00BCD4"
            },
            "afterlife": {
                "id": "afterlife",
                "name_ar": "الآخرة",
                "name_en": "Afterlife",
                "description_ar": "قصص اليوم الآخر والجنة والنار",
                "description_en": "Stories of the Day of Judgment, Paradise, and Hell",
                "icon": "sun",
                "color": "#FFC107"
            }
        }

    def _initialize_themes(self):
        """Initialize story themes with Arabic names"""
        self._themes = {
            "patience": {"id": "patience", "name_ar": "الصبر", "name_en": "Patience"},
            "trust": {"id": "trust", "name_ar": "التوكل", "name_en": "Trust in Allah"},
            "faith": {"id": "faith", "name_ar": "الإيمان", "name_en": "Faith"},
            "justice": {"id": "justice", "name_ar": "العدل", "name_en": "Justice"},
            "mercy": {"id": "mercy", "name_ar": "الرحمة", "name_en": "Mercy"},
            "obedience": {"id": "obedience", "name_ar": "الطاعة", "name_en": "Obedience"},
            "repentance": {"id": "repentance", "name_ar": "التوبة", "name_en": "Repentance"},
            "gratitude": {"id": "gratitude", "name_ar": "الشكر", "name_en": "Gratitude"},
            "sacrifice": {"id": "sacrifice", "name_ar": "التضحية", "name_en": "Sacrifice"},
            "perseverance": {"id": "perseverance", "name_ar": "المثابرة", "name_en": "Perseverance"},
            "wisdom": {"id": "wisdom", "name_ar": "الحكمة", "name_en": "Wisdom"},
            "guidance": {"id": "guidance", "name_ar": "الهداية", "name_en": "Guidance"},
            "punishment": {"id": "punishment", "name_ar": "العقاب", "name_en": "Divine Punishment"},
            "reward": {"id": "reward", "name_ar": "الثواب", "name_en": "Divine Reward"},
            "tawhid": {"id": "tawhid", "name_ar": "التوحيد", "name_en": "Monotheism"}
        }

    def _initialize_stories(self):
        """Initialize comprehensive Quranic stories"""

        # Story 1: Adam (آدم)
        self._stories["adam"] = Story(
            id="adam",
            title_ar="قصة آدم عليه السلام",
            title_en="Story of Adam (peace be upon him)",
            category=StoryCategory.PROPHETS,
            category_ar="الأنبياء",
            themes=[StoryTheme.CREATION, StoryTheme.REPENTANCE, StoryTheme.OBEDIENCE],
            themes_ar=["الخلق", "التوبة", "الطاعة"],
            summary_ar="قصة خلق آدم أبو البشر، وسجود الملائكة له، وإباء إبليس، وإخراج آدم وحواء من الجنة بعد أكلهما من الشجرة، ثم توبة الله عليهما.",
            summary_en="The story of the creation of Adam, the father of mankind, the prostration of angels to him, Iblis's refusal, the expulsion of Adam and Eve from Paradise after eating from the tree, and Allah's acceptance of their repentance.",
            figures=[
                StoryFigure(
                    id="adam",
                    name_ar="آدم",
                    name_en="Adam",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="أول الأنبياء وأبو البشر",
                    description_en="The first prophet and father of mankind",
                    is_prophet=True
                ),
                StoryFigure(
                    id="hawwa",
                    name_ar="حواء",
                    name_en="Eve (Hawwa)",
                    role="wife",
                    role_ar="زوجة",
                    description_ar="زوجة آدم وأم البشر",
                    description_en="Wife of Adam and mother of mankind",
                    is_prophet=False
                ),
                StoryFigure(
                    id="iblis",
                    name_ar="إبليس",
                    name_en="Iblis (Satan)",
                    role="antagonist",
                    role_ar="عدو",
                    description_ar="الشيطان الذي أبى السجود لآدم",
                    description_en="Satan who refused to prostrate to Adam",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="adam_creation",
                    name_ar="خلق آدم",
                    name_en="Creation of Adam",
                    description_ar="خلق الله آدم من طين ونفخ فيه من روحه",
                    description_en="Allah created Adam from clay and breathed into him His spirit",
                    sequence=1,
                    verses=["2:30", "15:28-29", "38:71-72"],
                    significance_ar="بداية الخلق البشري",
                    significance_en="Beginning of human creation"
                ),
                StoryEvent(
                    id="angels_prostration",
                    name_ar="سجود الملائكة",
                    name_en="Prostration of Angels",
                    description_ar="أمر الله الملائكة بالسجود لآدم فسجدوا إلا إبليس",
                    description_en="Allah commanded the angels to prostrate to Adam, and they did except Iblis",
                    sequence=2,
                    verses=["2:34", "7:11", "15:30-31"],
                    significance_ar="تكريم الإنسان",
                    significance_en="Honoring of mankind"
                ),
                StoryEvent(
                    id="iblis_refusal",
                    name_ar="إباء إبليس",
                    name_en="Iblis's Refusal",
                    description_ar="رفض إبليس السجود لآدم تكبراً",
                    description_en="Iblis refused to prostrate to Adam out of arrogance",
                    sequence=3,
                    verses=["2:34", "7:12", "38:74-76"],
                    significance_ar="الكبر سبب السقوط",
                    significance_en="Pride is the cause of downfall"
                ),
                StoryEvent(
                    id="forbidden_tree",
                    name_ar="الأكل من الشجرة",
                    name_en="Eating from the Tree",
                    description_ar="أكل آدم وحواء من الشجرة المحرمة بإغواء الشيطان",
                    description_en="Adam and Eve ate from the forbidden tree due to Satan's temptation",
                    sequence=4,
                    verses=["2:35-36", "7:19-22", "20:120-121"],
                    significance_ar="التحذير من وسوسة الشيطان",
                    significance_en="Warning against Satan's whispers"
                ),
                StoryEvent(
                    id="adam_repentance",
                    name_ar="توبة آدم",
                    name_en="Adam's Repentance",
                    description_ar="تاب آدم وحواء إلى الله فتاب عليهما",
                    description_en="Adam and Eve repented to Allah, and He accepted their repentance",
                    sequence=5,
                    verses=["2:37", "7:23", "20:122"],
                    significance_ar="باب التوبة مفتوح",
                    significance_en="The door of repentance is always open"
                )
            ],
            verses=[
                StoryVerse(
                    surah=2,
                    ayah_start=30,
                    ayah_end=39,
                    text_ar="وَإِذْ قَالَ رَبُّكَ لِلْمَلَائِكَةِ إِنِّي جَاعِلٌ فِي الْأَرْضِ خَلِيفَةً...",
                    text_en="And when your Lord said to the angels, 'Indeed, I will make upon the earth a successive authority...'",
                    context_ar="سورة البقرة - قصة خلق آدم",
                    context_en="Surah Al-Baqarah - Story of Adam's creation"
                ),
                StoryVerse(
                    surah=7,
                    ayah_start=11,
                    ayah_end=25,
                    text_ar="وَلَقَدْ خَلَقْنَاكُمْ ثُمَّ صَوَّرْنَاكُمْ ثُمَّ قُلْنَا لِلْمَلَائِكَةِ اسْجُدُوا لِآدَمَ...",
                    text_en="And We have certainly created you, then fashioned you; then We said to the angels, 'Prostrate to Adam'...",
                    context_ar="سورة الأعراف - تفصيل قصة آدم",
                    context_en="Surah Al-A'raf - Detailed story of Adam"
                ),
                StoryVerse(
                    surah=20,
                    ayah_start=115,
                    ayah_end=123,
                    text_ar="وَلَقَدْ عَهِدْنَا إِلَىٰ آدَمَ مِن قَبْلُ فَنَسِيَ وَلَمْ نَجِدْ لَهُ عَزْمًا...",
                    text_en="And We had already taken a promise from Adam before, but he forgot; and We found not in him determination...",
                    context_ar="سورة طه - قصة آدم مع التحذير",
                    context_en="Surah Ta-Ha - Adam's story with warning"
                )
            ],
            key_lessons_ar=[
                "التوبة تمحو الذنب",
                "الكبر يؤدي إلى الهلاك",
                "الحذر من وسوسة الشيطان",
                "تكريم الله للإنسان",
                "المسؤولية تأتي مع الاختيار"
            ],
            key_lessons_en=[
                "Repentance erases sin",
                "Pride leads to destruction",
                "Beware of Satan's whispers",
                "Allah's honoring of mankind",
                "Responsibility comes with choice"
            ],
            relationships=[
                StoryRelationship(
                    source_id="adam",
                    source_name="آدم",
                    target_id="iblis",
                    target_name="إبليس",
                    relationship_type=RelationshipType.PROPHET_TO_NATION,
                    description_ar="العداوة الأولى بين الإنسان والشيطان",
                    description_en="The first enmity between mankind and Satan"
                ),
                StoryRelationship(
                    source_id="adam",
                    source_name="آدم",
                    target_id="paradise",
                    target_name="الجنة",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="سكن آدم الجنة ثم أُهبط إلى الأرض",
                    description_en="Adam dwelt in Paradise then was sent down to Earth"
                )
            ],
            related_stories=["nuh", "creation_universe"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفصيل خلق آدم والحكمة من الاستخلاف",
                    "summary_en": "Details of Adam's creation and wisdom of succession"
                },
                {
                    "scholar": "القرطبي",
                    "source": "الجامع لأحكام القرآن",
                    "summary_ar": "الأحكام المستفادة من قصة آدم",
                    "summary_en": "Rulings derived from Adam's story"
                }
            ],
            completeness_score=0.95,
            is_verified=True
        )

        # Story 2: Nuh (نوح)
        self._stories["nuh"] = Story(
            id="nuh",
            title_ar="قصة نوح عليه السلام",
            title_en="Story of Noah (peace be upon him)",
            category=StoryCategory.PROPHETS,
            category_ar="الأنبياء",
            themes=[StoryTheme.PATIENCE, StoryTheme.PERSEVERANCE, StoryTheme.PUNISHMENT, StoryTheme.FAITH],
            themes_ar=["الصبر", "المثابرة", "العقاب", "الإيمان"],
            summary_ar="قصة نوح أول رسول إلى أهل الأرض، دعا قومه 950 سنة فكذبوه، فأنجاه الله ومن آمن معه في الفلك، وأغرق الكافرين بالطوفان.",
            summary_en="The story of Noah, the first messenger to the people of Earth. He called his people for 950 years but they denied him. Allah saved him and the believers in the Ark and drowned the disbelievers in the Flood.",
            figures=[
                StoryFigure(
                    id="nuh",
                    name_ar="نوح",
                    name_en="Noah",
                    role="prophet",
                    role_ar="نبي ورسول",
                    description_ar="أول رسول إلى أهل الأرض",
                    description_en="First messenger to the people of Earth",
                    is_prophet=True
                ),
                StoryFigure(
                    id="nuh_wife",
                    name_ar="امرأة نوح",
                    name_en="Wife of Noah",
                    role="wife",
                    role_ar="زوجة",
                    description_ar="كانت كافرة ولم تؤمن",
                    description_en="She was a disbeliever and did not believe",
                    is_prophet=False
                ),
                StoryFigure(
                    id="nuh_son",
                    name_ar="ابن نوح",
                    name_en="Son of Noah",
                    role="son",
                    role_ar="ابن",
                    description_ar="رفض ركوب السفينة وغرق مع الكافرين",
                    description_en="Refused to board the Ark and drowned with the disbelievers",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="nuh_mission",
                    name_ar="بعثة نوح",
                    name_en="Noah's Mission",
                    description_ar="أرسل الله نوحاً لدعوة قومه إلى التوحيد",
                    description_en="Allah sent Noah to call his people to monotheism",
                    sequence=1,
                    verses=["7:59", "11:25", "23:23"],
                    significance_ar="أول رسالة بعد آدم",
                    significance_en="First mission after Adam"
                ),
                StoryEvent(
                    id="nuh_950_years",
                    name_ar="الدعوة 950 سنة",
                    name_en="950 Years of Calling",
                    description_ar="دعا نوح قومه 950 سنة ليلاً ونهاراً",
                    description_en="Noah called his people for 950 years, night and day",
                    sequence=2,
                    verses=["29:14", "71:5-9"],
                    significance_ar="الصبر في الدعوة",
                    significance_en="Patience in calling to Allah"
                ),
                StoryEvent(
                    id="ark_building",
                    name_ar="بناء السفينة",
                    name_en="Building the Ark",
                    description_ar="أمر الله نوحاً ببناء السفينة",
                    description_en="Allah commanded Noah to build the Ark",
                    sequence=3,
                    verses=["11:37", "23:27"],
                    significance_ar="الاستعداد للنجاة",
                    significance_en="Preparation for salvation"
                ),
                StoryEvent(
                    id="great_flood",
                    name_ar="الطوفان العظيم",
                    name_en="The Great Flood",
                    description_ar="فجر الله عيون الأرض وأنزل المطر الغزير",
                    description_en="Allah caused springs to gush from the earth and sent heavy rain",
                    sequence=4,
                    verses=["11:40", "54:11-12"],
                    significance_ar="عقاب الكافرين",
                    significance_en="Punishment of disbelievers"
                ),
                StoryEvent(
                    id="nuh_son_drowning",
                    name_ar="غرق ابن نوح",
                    name_en="Drowning of Noah's Son",
                    description_ar="رفض ابن نوح ركوب السفينة وغرق",
                    description_en="Noah's son refused to board the Ark and drowned",
                    sequence=5,
                    verses=["11:42-43"],
                    significance_ar="القرابة لا تنفع مع الكفر",
                    significance_en="Kinship does not benefit with disbelief"
                ),
                StoryEvent(
                    id="ark_landing",
                    name_ar="رسو السفينة",
                    name_en="Landing of the Ark",
                    description_ar="استوت السفينة على جبل الجودي",
                    description_en="The Ark rested on Mount Judi",
                    sequence=6,
                    verses=["11:44"],
                    significance_ar="نجاة المؤمنين",
                    significance_en="Salvation of the believers"
                )
            ],
            verses=[
                StoryVerse(
                    surah=11,
                    ayah_start=25,
                    ayah_end=49,
                    text_ar="وَلَقَدْ أَرْسَلْنَا نُوحًا إِلَىٰ قَوْمِهِ إِنِّي لَكُمْ نَذِيرٌ مُّبِينٌ...",
                    text_en="And We had certainly sent Noah to his people, [saying], 'Indeed, I am to you a clear warner...'",
                    context_ar="سورة هود - قصة نوح الكاملة",
                    context_en="Surah Hud - Complete story of Noah"
                ),
                StoryVerse(
                    surah=71,
                    ayah_start=1,
                    ayah_end=28,
                    text_ar="إِنَّا أَرْسَلْنَا نُوحًا إِلَىٰ قَوْمِهِ أَنْ أَنذِرْ قَوْمَكَ مِن قَبْلِ أَن يَأْتِيَهُمْ عَذَابٌ أَلِيمٌ...",
                    text_en="Indeed, We sent Noah to his people, [saying], 'Warn your people before there comes to them a painful punishment...'",
                    context_ar="سورة نوح - السورة كاملة",
                    context_en="Surah Nuh - Complete Surah"
                )
            ],
            key_lessons_ar=[
                "الصبر في الدعوة إلى الله",
                "النسب لا ينفع مع الكفر",
                "عاقبة التكذيب الهلاك",
                "النجاة في طاعة الله",
                "الثبات على الحق مهما طال الزمن"
            ],
            key_lessons_en=[
                "Patience in calling to Allah",
                "Lineage does not benefit with disbelief",
                "Consequence of denial is destruction",
                "Salvation is in obedience to Allah",
                "Steadfastness on truth no matter how long"
            ],
            relationships=[
                StoryRelationship(
                    source_id="nuh",
                    source_name="نوح",
                    target_id="adam",
                    target_name="آدم",
                    relationship_type=RelationshipType.PREDECESSOR,
                    description_ar="نوح من ذرية آدم",
                    description_en="Noah is from Adam's descendants"
                ),
                StoryRelationship(
                    source_id="nuh",
                    source_name="نوح",
                    target_id="ibrahim",
                    target_name="إبراهيم",
                    relationship_type=RelationshipType.PROPHET_TO_PROPHET,
                    description_ar="إبراهيم من ذرية نوح",
                    description_en="Abraham is from Noah's descendants"
                ),
                StoryRelationship(
                    source_id="nuh",
                    source_name="نوح",
                    target_id="mount_judi",
                    target_name="جبل الجودي",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="رست سفينة نوح على جبل الجودي",
                    description_en="Noah's Ark rested on Mount Judi"
                )
            ],
            related_stories=["adam", "ibrahim", "hud"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفصيل قصة نوح والطوفان",
                    "summary_en": "Details of Noah's story and the Flood"
                },
                {
                    "scholar": "السعدي",
                    "source": "تيسير الكريم الرحمن",
                    "summary_ar": "العبر من قصة نوح",
                    "summary_en": "Lessons from Noah's story"
                }
            ],
            completeness_score=0.92,
            is_verified=True
        )

        # Story 3: Ibrahim (إبراهيم)
        self._stories["ibrahim"] = Story(
            id="ibrahim",
            title_ar="قصة إبراهيم عليه السلام",
            title_en="Story of Abraham (peace be upon him)",
            category=StoryCategory.PROPHETS,
            category_ar="الأنبياء",
            themes=[StoryTheme.TAWHID, StoryTheme.SACRIFICE, StoryTheme.TRUST, StoryTheme.FAITH],
            themes_ar=["التوحيد", "التضحية", "التوكل", "الإيمان"],
            summary_ar="قصة خليل الرحمن إبراهيم، محطم الأصنام، الذي ألقي في النار فنجاه الله، وابتلي بذبح ابنه إسماعيل فافتداه الله بذبح عظيم، وبنى الكعبة مع ابنه إسماعيل.",
            summary_en="The story of Allah's friend Abraham, the idol-breaker, who was thrown into fire but Allah saved him, was tested with sacrificing his son Ishmael but Allah ransomed him with a great sacrifice, and built the Kaaba with his son Ishmael.",
            figures=[
                StoryFigure(
                    id="ibrahim",
                    name_ar="إبراهيم",
                    name_en="Abraham",
                    role="prophet",
                    role_ar="نبي ورسول",
                    description_ar="خليل الرحمن وأبو الأنبياء",
                    description_en="The Friend of Allah and Father of the Prophets",
                    is_prophet=True
                ),
                StoryFigure(
                    id="ismail",
                    name_ar="إسماعيل",
                    name_en="Ishmael",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="ابن إبراهيم، جد النبي محمد",
                    description_en="Son of Abraham, ancestor of Prophet Muhammad",
                    is_prophet=True
                ),
                StoryFigure(
                    id="ishaq",
                    name_ar="إسحاق",
                    name_en="Isaac",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="ابن إبراهيم، أبو يعقوب",
                    description_en="Son of Abraham, father of Jacob",
                    is_prophet=True
                ),
                StoryFigure(
                    id="sarah",
                    name_ar="سارة",
                    name_en="Sarah",
                    role="wife",
                    role_ar="زوجة",
                    description_ar="زوجة إبراهيم وأم إسحاق",
                    description_en="Wife of Abraham and mother of Isaac",
                    is_prophet=False
                ),
                StoryFigure(
                    id="hajar",
                    name_ar="هاجر",
                    name_en="Hagar",
                    role="wife",
                    role_ar="زوجة",
                    description_ar="زوجة إبراهيم وأم إسماعيل",
                    description_en="Wife of Abraham and mother of Ishmael",
                    is_prophet=False
                ),
                StoryFigure(
                    id="namrud",
                    name_ar="النمرود",
                    name_en="Nimrod",
                    role="antagonist",
                    role_ar="طاغية",
                    description_ar="الملك الطاغية الذي حاج إبراهيم",
                    description_en="The tyrant king who argued with Abraham",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="ibrahim_tawhid",
                    name_ar="استدلال إبراهيم على التوحيد",
                    name_en="Abraham's Reasoning for Monotheism",
                    description_ar="تفكر إبراهيم في الكوكب والقمر والشمس ثم أعلن توحيده",
                    description_en="Abraham pondered the star, moon, and sun then declared his monotheism",
                    sequence=1,
                    verses=["6:74-79"],
                    significance_ar="العقل يهدي إلى التوحيد",
                    significance_en="Reason leads to monotheism"
                ),
                StoryEvent(
                    id="ibrahim_idols",
                    name_ar="تحطيم الأصنام",
                    name_en="Breaking the Idols",
                    description_ar="حطم إبراهيم أصنام قومه ليبين لهم بطلان عبادتها",
                    description_en="Abraham broke his people's idols to show them the falsehood of worshiping them",
                    sequence=2,
                    verses=["21:57-67", "37:91-93"],
                    significance_ar="إنكار الشرك بالفعل",
                    significance_en="Rejecting polytheism through action"
                ),
                StoryEvent(
                    id="ibrahim_fire",
                    name_ar="إلقاء إبراهيم في النار",
                    name_en="Abraham Thrown into Fire",
                    description_ar="ألقى قومه إبراهيم في النار فأمر الله النار أن تكون برداً وسلاماً",
                    description_en="His people threw Abraham into fire, but Allah commanded the fire to be cool and peaceful",
                    sequence=3,
                    verses=["21:68-70", "37:97-98"],
                    significance_ar="الله ينجي عباده الصالحين",
                    significance_en="Allah saves His righteous servants"
                ),
                StoryEvent(
                    id="ibrahim_sacrifice",
                    name_ar="ذبح إسماعيل",
                    name_en="Sacrifice of Ishmael",
                    description_ar="رأى إبراهيم في المنام أنه يذبح ابنه فاستسلما لأمر الله ففداه الله بذبح عظيم",
                    description_en="Abraham saw in a dream that he was sacrificing his son. They both submitted to Allah's command, and Allah ransomed him with a great sacrifice",
                    sequence=4,
                    verses=["37:102-107"],
                    significance_ar="الاستسلام لأمر الله",
                    significance_en="Submission to Allah's command"
                ),
                StoryEvent(
                    id="kaaba_building",
                    name_ar="بناء الكعبة",
                    name_en="Building the Kaaba",
                    description_ar="بنى إبراهيم وإسماعيل الكعبة المشرفة",
                    description_en="Abraham and Ishmael built the Holy Kaaba",
                    sequence=5,
                    verses=["2:127", "22:26"],
                    significance_ar="قبلة المسلمين",
                    significance_en="The Qibla of Muslims"
                )
            ],
            verses=[
                StoryVerse(
                    surah=2,
                    ayah_start=124,
                    ayah_end=132,
                    text_ar="وَإِذِ ابْتَلَىٰ إِبْرَاهِيمَ رَبُّهُ بِكَلِمَاتٍ فَأَتَمَّهُنَّ...",
                    text_en="And [mention] when Abraham was tried by his Lord with commands and he fulfilled them...",
                    context_ar="سورة البقرة - ابتلاء إبراهيم وبناء الكعبة",
                    context_en="Surah Al-Baqarah - Abraham's trials and building the Kaaba"
                ),
                StoryVerse(
                    surah=6,
                    ayah_start=74,
                    ayah_end=83,
                    text_ar="وَإِذْ قَالَ إِبْرَاهِيمُ لِأَبِيهِ آزَرَ أَتَتَّخِذُ أَصْنَامًا آلِهَةً...",
                    text_en="And [mention] when Abraham said to his father Azar, 'Do you take idols as deities?...'",
                    context_ar="سورة الأنعام - استدلال إبراهيم على التوحيد",
                    context_en="Surah Al-An'am - Abraham's reasoning for monotheism"
                ),
                StoryVerse(
                    surah=37,
                    ayah_start=83,
                    ayah_end=113,
                    text_ar="وَإِنَّ مِن شِيعَتِهِ لَإِبْرَاهِيمَ...",
                    text_en="And indeed, among his kind was Abraham...",
                    context_ar="سورة الصافات - قصة إبراهيم والذبح",
                    context_en="Surah As-Saffat - Abraham's story and the sacrifice"
                )
            ],
            key_lessons_ar=[
                "التوحيد أساس الدين",
                "الاستسلام لأمر الله",
                "الصبر على البلاء",
                "التوكل على الله في الشدائد",
                "بناء بيت الله تشريف عظيم"
            ],
            key_lessons_en=[
                "Monotheism is the foundation of religion",
                "Submission to Allah's command",
                "Patience during trials",
                "Trust in Allah during hardships",
                "Building Allah's house is a great honor"
            ],
            relationships=[
                StoryRelationship(
                    source_id="ibrahim",
                    source_name="إبراهيم",
                    target_id="ismail",
                    target_name="إسماعيل",
                    relationship_type=RelationshipType.FATHER_SON,
                    description_ar="إسماعيل ابن إبراهيم من هاجر",
                    description_en="Ishmael is Abraham's son from Hagar"
                ),
                StoryRelationship(
                    source_id="ibrahim",
                    source_name="إبراهيم",
                    target_id="ishaq",
                    target_name="إسحاق",
                    relationship_type=RelationshipType.FATHER_SON,
                    description_ar="إسحاق ابن إبراهيم من سارة",
                    description_en="Isaac is Abraham's son from Sarah"
                ),
                StoryRelationship(
                    source_id="ibrahim",
                    source_name="إبراهيم",
                    target_id="makkah",
                    target_name="مكة",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="بنى إبراهيم الكعبة في مكة",
                    description_en="Abraham built the Kaaba in Makkah"
                ),
                StoryRelationship(
                    source_id="ismail",
                    source_name="إسماعيل",
                    target_id="muhammad",
                    target_name="محمد",
                    relationship_type=RelationshipType.PROPHET_TO_PROPHET,
                    description_ar="محمد ﷺ من ذرية إسماعيل",
                    description_en="Muhammad ﷺ is from Ishmael's descendants"
                )
            ],
            related_stories=["nuh", "lut", "yaqub", "yusuf"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفصيل قصة إبراهيم الخليل",
                    "summary_en": "Details of Abraham the Friend's story"
                },
                {
                    "scholar": "الطبري",
                    "source": "جامع البيان",
                    "summary_ar": "روايات قصة إبراهيم",
                    "summary_en": "Narrations of Abraham's story"
                }
            ],
            completeness_score=0.95,
            is_verified=True
        )

        # Story 4: Yusuf (يوسف)
        self._stories["yusuf"] = Story(
            id="yusuf",
            title_ar="قصة يوسف عليه السلام",
            title_en="Story of Joseph (peace be upon him)",
            category=StoryCategory.PROPHETS,
            category_ar="الأنبياء",
            themes=[StoryTheme.PATIENCE, StoryTheme.TRUST, StoryTheme.WISDOM, StoryTheme.FORGIVENESS],
            themes_ar=["الصبر", "التوكل", "الحكمة", "العفو"],
            summary_ar="أحسن القصص - قصة يوسف الذي حسده إخوته فألقوه في البئر، ثم بيع عبداً في مصر، ثم سُجن ظلماً، ثم صار عزيز مصر، ثم عفا عن إخوته.",
            summary_en="The best of stories - Joseph who was envied by his brothers who threw him in a well, then sold as a slave in Egypt, then imprisoned unjustly, then became the Aziz of Egypt, then forgave his brothers.",
            figures=[
                StoryFigure(
                    id="yusuf",
                    name_ar="يوسف",
                    name_en="Joseph",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="الصديق، أُعطي شطر الحسن",
                    description_en="The Truthful, given half of all beauty",
                    is_prophet=True
                ),
                StoryFigure(
                    id="yaqub",
                    name_ar="يعقوب",
                    name_en="Jacob",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="والد يوسف، إسرائيل",
                    description_en="Father of Joseph, Israel",
                    is_prophet=True
                ),
                StoryFigure(
                    id="zulaykha",
                    name_ar="امرأة العزيز",
                    name_en="Wife of Al-Aziz",
                    role="antagonist",
                    role_ar="امرأة العزيز",
                    description_ar="راودته عن نفسه فاستعصم",
                    description_en="She tried to seduce him but he refused",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="yusuf_dream",
                    name_ar="رؤيا يوسف",
                    name_en="Joseph's Dream",
                    description_ar="رأى يوسف أحد عشر كوكباً والشمس والقمر ساجدين له",
                    description_en="Joseph saw eleven stars and the sun and moon prostrating to him",
                    sequence=1,
                    verses=["12:4-6"],
                    significance_ar="الرؤيا الصادقة",
                    significance_en="True vision"
                ),
                StoryEvent(
                    id="yusuf_well",
                    name_ar="إلقاء يوسف في البئر",
                    name_en="Joseph Thrown in the Well",
                    description_ar="ألقى إخوة يوسف أخاهم في غيابة الجب حسداً",
                    description_en="Joseph's brothers threw him in the depths of the well out of envy",
                    sequence=2,
                    verses=["12:10-18"],
                    significance_ar="الحسد يفرق",
                    significance_en="Envy divides"
                ),
                StoryEvent(
                    id="yusuf_sold",
                    name_ar="بيع يوسف عبداً",
                    name_en="Joseph Sold as Slave",
                    description_ar="بيع يوسف بثمن بخس في مصر",
                    description_en="Joseph was sold for a low price in Egypt",
                    sequence=3,
                    verses=["12:19-20"],
                    significance_ar="الابتلاء بالذل",
                    significance_en="Trial through humiliation"
                ),
                StoryEvent(
                    id="yusuf_seduction",
                    name_ar="امرأة العزيز",
                    name_en="Wife of Al-Aziz's Seduction",
                    description_ar="راودته امرأة العزيز عن نفسه فاستعصم وقال معاذ الله",
                    description_en="The wife of Al-Aziz tried to seduce him but he refused saying 'I seek refuge in Allah'",
                    sequence=4,
                    verses=["12:23-34"],
                    significance_ar="العفة في البلاء",
                    significance_en="Chastity during trial"
                ),
                StoryEvent(
                    id="yusuf_prison",
                    name_ar="سجن يوسف",
                    name_en="Joseph's Imprisonment",
                    description_ar="سُجن يوسف ظلماً ودعا في السجن",
                    description_en="Joseph was imprisoned unjustly and called to Allah in prison",
                    sequence=5,
                    verses=["12:35-42"],
                    significance_ar="الدعوة في السجن",
                    significance_en="Calling to Allah in prison"
                ),
                StoryEvent(
                    id="yusuf_aziz",
                    name_ar="يوسف عزيز مصر",
                    name_en="Joseph Becomes Aziz",
                    description_ar="فسر يوسف رؤيا الملك وصار على خزائن مصر",
                    description_en="Joseph interpreted the king's dream and became treasurer of Egypt",
                    sequence=6,
                    verses=["12:43-57"],
                    significance_ar="الفرج بعد الشدة",
                    significance_en="Relief after hardship"
                ),
                StoryEvent(
                    id="yusuf_brothers_return",
                    name_ar="لقاء الإخوة",
                    name_en="Meeting with Brothers",
                    description_ar="جاء إخوة يوسف لطلب الطعام فعرفهم ولم يعرفوه",
                    description_en="Joseph's brothers came seeking food; he recognized them but they did not recognize him",
                    sequence=7,
                    verses=["12:58-87"],
                    significance_ar="القدر يجمع",
                    significance_en="Destiny reunites"
                ),
                StoryEvent(
                    id="yusuf_forgiveness",
                    name_ar="عفو يوسف",
                    name_en="Joseph's Forgiveness",
                    description_ar="عفا يوسف عن إخوته وجمع شمل العائلة",
                    description_en="Joseph forgave his brothers and reunited the family",
                    sequence=8,
                    verses=["12:88-101"],
                    significance_ar="العفو من شيم الكرام",
                    significance_en="Forgiveness is the trait of the noble"
                )
            ],
            verses=[
                StoryVerse(
                    surah=12,
                    ayah_start=1,
                    ayah_end=111,
                    text_ar="الر ۚ تِلْكَ آيَاتُ الْكِتَابِ الْمُبِينِ ۝ إِنَّا أَنزَلْنَاهُ قُرْآنًا عَرَبِيًّا لَّعَلَّكُمْ تَعْقِلُونَ ۝ نَحْنُ نَقُصُّ عَلَيْكَ أَحْسَنَ الْقَصَصِ...",
                    text_en="Alif, Lam, Ra. These are the verses of the clear Book. Indeed, We have sent it down as an Arabic Quran that you might understand. We relate to you the best of stories...",
                    context_ar="سورة يوسف كاملة",
                    context_en="Complete Surah Yusuf"
                )
            ],
            key_lessons_ar=[
                "الصبر مفتاح الفرج",
                "العفة عند الفتنة",
                "التوكل على الله في الشدائد",
                "العفو عند المقدرة",
                "الحسد يفرق الإخوة"
            ],
            key_lessons_en=[
                "Patience is the key to relief",
                "Chastity during temptation",
                "Trust in Allah during hardships",
                "Forgiveness when able",
                "Envy divides brothers"
            ],
            relationships=[
                StoryRelationship(
                    source_id="yusuf",
                    source_name="يوسف",
                    target_id="yaqub",
                    target_name="يعقوب",
                    relationship_type=RelationshipType.FATHER_SON,
                    description_ar="يوسف ابن يعقوب",
                    description_en="Joseph is Jacob's son"
                ),
                StoryRelationship(
                    source_id="yaqub",
                    source_name="يعقوب",
                    target_id="ishaq",
                    target_name="إسحاق",
                    relationship_type=RelationshipType.FATHER_SON,
                    description_ar="يعقوب ابن إسحاق",
                    description_en="Jacob is Isaac's son"
                ),
                StoryRelationship(
                    source_id="yusuf",
                    source_name="يوسف",
                    target_id="egypt",
                    target_name="مصر",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="صار يوسف عزيز مصر",
                    description_en="Joseph became the Aziz of Egypt"
                )
            ],
            related_stories=["ibrahim", "musa"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفسير سورة يوسف كاملة",
                    "summary_en": "Complete tafsir of Surah Yusuf"
                }
            ],
            completeness_score=0.98,
            is_verified=True
        )

        # Story 5: Musa (موسى)
        self._stories["musa"] = Story(
            id="musa",
            title_ar="قصة موسى عليه السلام",
            title_en="Story of Moses (peace be upon him)",
            category=StoryCategory.PROPHETS,
            category_ar="الأنبياء",
            themes=[StoryTheme.TRUST, StoryTheme.PATIENCE, StoryTheme.FAITH, StoryTheme.JUSTICE],
            themes_ar=["التوكل", "الصبر", "الإيمان", "العدل"],
            summary_ar="أكثر الأنبياء ذكراً في القرآن، أُرسل لبني إسرائيل وواجه فرعون الطاغية، وأنجاه الله بشق البحر، وأُنزلت عليه التوراة.",
            summary_en="The most mentioned prophet in the Quran, sent to the Children of Israel, confronted the tyrant Pharaoh, Allah saved him by parting the sea, and the Torah was revealed to him.",
            figures=[
                StoryFigure(
                    id="musa",
                    name_ar="موسى",
                    name_en="Moses",
                    role="prophet",
                    role_ar="نبي ورسول",
                    description_ar="كليم الله، أُرسل لبني إسرائيل",
                    description_en="The one who spoke to Allah, sent to the Children of Israel",
                    is_prophet=True
                ),
                StoryFigure(
                    id="harun",
                    name_ar="هارون",
                    name_en="Aaron",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="أخو موسى ووزيره",
                    description_en="Brother and minister of Moses",
                    is_prophet=True
                ),
                StoryFigure(
                    id="firaun",
                    name_ar="فرعون",
                    name_en="Pharaoh",
                    role="antagonist",
                    role_ar="طاغية",
                    description_ar="الطاغية الذي ادعى الربوبية",
                    description_en="The tyrant who claimed to be a god",
                    is_prophet=False
                ),
                StoryFigure(
                    id="asiya",
                    name_ar="آسية",
                    name_en="Asiya",
                    role="believer",
                    role_ar="مؤمنة",
                    description_ar="امرأة فرعون المؤمنة",
                    description_en="Pharaoh's believing wife",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="musa_birth",
                    name_ar="ولادة موسى",
                    name_en="Birth of Moses",
                    description_ar="ولد موسى في عام قتل فرعون للأبناء فألقته أمه في اليم",
                    description_en="Moses was born in the year Pharaoh was killing male children, so his mother cast him in the river",
                    sequence=1,
                    verses=["20:38-40", "28:7-13"],
                    significance_ar="حفظ الله لأوليائه",
                    significance_en="Allah's protection of His allies"
                ),
                StoryEvent(
                    id="musa_prophethood",
                    name_ar="بعثة موسى",
                    name_en="Moses's Prophethood",
                    description_ar="كلم الله موسى عند الشجرة وأرسله إلى فرعون",
                    description_en="Allah spoke to Moses at the tree and sent him to Pharaoh",
                    sequence=2,
                    verses=["20:9-24", "28:29-35"],
                    significance_ar="التكليم الإلهي",
                    significance_en="Divine speech"
                ),
                StoryEvent(
                    id="musa_firaun",
                    name_ar="مواجهة فرعون",
                    name_en="Confronting Pharaoh",
                    description_ar="واجه موسى فرعون بالآيات البينات فاستكبر وكذب",
                    description_en="Moses confronted Pharaoh with clear signs but he was arrogant and denied",
                    sequence=3,
                    verses=["7:103-126", "20:49-73"],
                    significance_ar="الحق يعلو",
                    significance_en="Truth prevails"
                ),
                StoryEvent(
                    id="sea_parting",
                    name_ar="شق البحر",
                    name_en="Parting of the Sea",
                    description_ar="ضرب موسى البحر بعصاه فانفلق وأغرق الله فرعون",
                    description_en="Moses struck the sea with his staff, it parted, and Allah drowned Pharaoh",
                    sequence=4,
                    verses=["26:63-68", "20:77-79"],
                    significance_ar="نجاة المؤمنين وهلاك الظالمين",
                    significance_en="Salvation of believers and destruction of oppressors"
                ),
                StoryEvent(
                    id="torah_revelation",
                    name_ar="نزول التوراة",
                    name_en="Revelation of Torah",
                    description_ar="أنزل الله التوراة على موسى في الطور",
                    description_en="Allah revealed the Torah to Moses at Mount Tur",
                    sequence=5,
                    verses=["7:145", "2:53"],
                    significance_ar="الكتاب السماوي",
                    significance_en="Divine scripture"
                )
            ],
            verses=[
                StoryVerse(
                    surah=20,
                    ayah_start=9,
                    ayah_end=99,
                    text_ar="وَهَلْ أَتَاكَ حَدِيثُ مُوسَىٰ...",
                    text_en="And has the story of Moses reached you?...",
                    context_ar="سورة طه - قصة موسى",
                    context_en="Surah Ta-Ha - Story of Moses"
                ),
                StoryVerse(
                    surah=28,
                    ayah_start=3,
                    ayah_end=46,
                    text_ar="نَتْلُو عَلَيْكَ مِن نَّبَإِ مُوسَىٰ وَفِرْعَوْنَ بِالْحَقِّ...",
                    text_en="We recite to you from the news of Moses and Pharaoh in truth...",
                    context_ar="سورة القصص - قصة موسى وفرعون",
                    context_en="Surah Al-Qasas - Story of Moses and Pharaoh"
                )
            ],
            key_lessons_ar=[
                "الله ينصر المستضعفين",
                "الطغيان مآله الهلاك",
                "الصبر على الأذى في سبيل الدعوة",
                "التوكل على الله في المواقف الصعبة",
                "الحق يعلو ولا يُعلى عليه"
            ],
            key_lessons_en=[
                "Allah supports the oppressed",
                "Tyranny leads to destruction",
                "Patience with harm for the sake of calling to Allah",
                "Trust in Allah in difficult situations",
                "Truth prevails and cannot be overcome"
            ],
            relationships=[
                StoryRelationship(
                    source_id="musa",
                    source_name="موسى",
                    target_id="harun",
                    target_name="هارون",
                    relationship_type=RelationshipType.PROPHET_TO_PROPHET,
                    description_ar="هارون أخو موسى ووزيره",
                    description_en="Aaron is Moses's brother and minister"
                ),
                StoryRelationship(
                    source_id="musa",
                    source_name="موسى",
                    target_id="egypt",
                    target_name="مصر",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="نشأ موسى في مصر",
                    description_en="Moses grew up in Egypt"
                ),
                StoryRelationship(
                    source_id="musa",
                    source_name="موسى",
                    target_id="sinai",
                    target_name="سيناء",
                    relationship_type=RelationshipType.PROPHET_TO_PLACE,
                    description_ar="كلم الله موسى في طور سيناء",
                    description_en="Allah spoke to Moses at Mount Sinai"
                )
            ],
            related_stories=["yusuf", "firaun_nation", "bani_israel"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفصيل قصة موسى في مواضع متعددة",
                    "summary_en": "Detailed story of Moses in multiple places"
                }
            ],
            completeness_score=0.92,
            is_verified=True
        )

        # Story 6: People of the Cave (أهل الكهف)
        self._stories["ahlul_kahf"] = Story(
            id="ahlul_kahf",
            title_ar="قصة أصحاب الكهف",
            title_en="Story of the People of the Cave",
            category=StoryCategory.HISTORICAL,
            category_ar="التاريخية",
            themes=[StoryTheme.FAITH, StoryTheme.TRUST, StoryTheme.PERSEVERANCE],
            themes_ar=["الإيمان", "التوكل", "الثبات"],
            summary_ar="قصة فتية آمنوا بربهم وفروا بدينهم من الظلم، فأواهم الله إلى الكهف وأنامهم ثلاثمائة سنة وتسع سنين.",
            summary_en="The story of young men who believed in their Lord and fled with their faith from oppression, so Allah sheltered them in the cave and made them sleep for three hundred and nine years.",
            figures=[
                StoryFigure(
                    id="cave_youth",
                    name_ar="الفتية",
                    name_en="The Youth",
                    role="believers",
                    role_ar="مؤمنون",
                    description_ar="فتية آمنوا بربهم وزادهم هدى",
                    description_en="Youth who believed in their Lord and He increased them in guidance",
                    is_prophet=False
                ),
                StoryFigure(
                    id="cave_dog",
                    name_ar="الكلب",
                    name_en="The Dog",
                    role="companion",
                    role_ar="رفيق",
                    description_ar="كلبهم باسط ذراعيه بالوصيد",
                    description_en="Their dog stretching its forelegs at the entrance",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="cave_escape",
                    name_ar="الفرار بالدين",
                    name_en="Fleeing for Faith",
                    description_ar="فر الفتية من قومهم المشركين حفاظاً على دينهم",
                    description_en="The youth fled from their polytheist people to preserve their faith",
                    sequence=1,
                    verses=["18:13-16"],
                    significance_ar="الهجرة لحفظ الدين",
                    significance_en="Migration to preserve faith"
                ),
                StoryEvent(
                    id="cave_sleep",
                    name_ar="النوم في الكهف",
                    name_en="Sleep in the Cave",
                    description_ar="أنامهم الله 309 سنين في الكهف",
                    description_en="Allah made them sleep for 309 years in the cave",
                    sequence=2,
                    verses=["18:17-22", "18:25"],
                    significance_ar="معجزة إلهية",
                    significance_en="Divine miracle"
                ),
                StoryEvent(
                    id="cave_awakening",
                    name_ar="الاستيقاظ",
                    name_en="Awakening",
                    description_ar="استيقظوا فأرسلوا أحدهم بورقهم إلى المدينة",
                    description_en="They woke up and sent one of them with their coins to the city",
                    sequence=3,
                    verses=["18:19-21"],
                    significance_ar="آية للناس",
                    significance_en="A sign for the people"
                )
            ],
            verses=[
                StoryVerse(
                    surah=18,
                    ayah_start=9,
                    ayah_end=26,
                    text_ar="أَمْ حَسِبْتَ أَنَّ أَصْحَابَ الْكَهْفِ وَالرَّقِيمِ كَانُوا مِنْ آيَاتِنَا عَجَبًا...",
                    text_en="Or have you thought that the companions of the cave and the inscription were, among Our signs, a wonder?...",
                    context_ar="سورة الكهف - قصة أصحاب الكهف",
                    context_en="Surah Al-Kahf - Story of the People of the Cave"
                )
            ],
            key_lessons_ar=[
                "الفرار بالدين عند الفتنة",
                "الله يحفظ عباده المؤمنين",
                "الثبات على الحق",
                "صحبة الأخيار"
            ],
            key_lessons_en=[
                "Fleeing for faith during tribulation",
                "Allah protects His believing servants",
                "Steadfastness on truth",
                "Company of the righteous"
            ],
            relationships=[],
            related_stories=["dhul_qarnayn"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "تفسير قصة أصحاب الكهف",
                    "summary_en": "Tafsir of the People of the Cave story"
                }
            ],
            completeness_score=0.88,
            is_verified=True
        )

        # Add more stories...
        self._add_more_stories()

    def _add_more_stories(self):
        """Add additional Quranic stories"""

        # Story: Qarun (قارون)
        self._stories["qarun"] = Story(
            id="qarun",
            title_ar="قصة قارون",
            title_en="Story of Qarun (Korah)",
            category=StoryCategory.NATIONS,
            category_ar="الأمم",
            themes=[StoryTheme.PUNISHMENT, StoryTheme.GRATITUDE],
            themes_ar=["العقاب", "الشكر"],
            summary_ar="قصة قارون من قوم موسى الذي آتاه الله كنوزاً فبطر وتكبر فخسف الله به وبداره الأرض.",
            summary_en="The story of Qarun from the people of Moses, whom Allah gave treasures, but he was arrogant, so Allah caused him and his home to sink into the earth.",
            figures=[
                StoryFigure(
                    id="qarun",
                    name_ar="قارون",
                    name_en="Qarun (Korah)",
                    role="wealthy_man",
                    role_ar="غني متكبر",
                    description_ar="كان من قوم موسى فبغى عليهم",
                    description_en="He was from the people of Moses but he oppressed them",
                    is_prophet=False
                )
            ],
            events=[
                StoryEvent(
                    id="qarun_wealth",
                    name_ar="كنوز قارون",
                    name_en="Qarun's Treasures",
                    description_ar="آتاه الله من الكنوز ما إن مفاتحه لتنوء بالعصبة",
                    description_en="Allah gave him treasures whose keys would burden a strong group of men",
                    sequence=1,
                    verses=["28:76"],
                    significance_ar="الابتلاء بالنعم",
                    significance_en="Trial through blessings"
                ),
                StoryEvent(
                    id="qarun_arrogance",
                    name_ar="تكبر قارون",
                    name_en="Qarun's Arrogance",
                    description_ar="قال إنما أوتيته على علم عندي",
                    description_en="He said: I was only given it because of knowledge I have",
                    sequence=2,
                    verses=["28:78"],
                    significance_ar="نسب النعم لنفسه",
                    significance_en="Attributing blessings to himself"
                ),
                StoryEvent(
                    id="qarun_destruction",
                    name_ar="هلاك قارون",
                    name_en="Qarun's Destruction",
                    description_ar="خسف الله به وبداره الأرض",
                    description_en="Allah caused him and his home to sink into the earth",
                    sequence=3,
                    verses=["28:81-82"],
                    significance_ar="عاقبة الكبر",
                    significance_en="Consequence of arrogance"
                )
            ],
            verses=[
                StoryVerse(
                    surah=28,
                    ayah_start=76,
                    ayah_end=82,
                    text_ar="إِنَّ قَارُونَ كَانَ مِن قَوْمِ مُوسَىٰ فَبَغَىٰ عَلَيْهِمْ...",
                    text_en="Indeed, Qarun was from the people of Moses, but he oppressed them...",
                    context_ar="سورة القصص - قصة قارون",
                    context_en="Surah Al-Qasas - Story of Qarun"
                )
            ],
            key_lessons_ar=[
                "المال ابتلاء",
                "شكر النعم واجب",
                "الكبر سبب الهلاك"
            ],
            key_lessons_en=[
                "Wealth is a trial",
                "Gratitude for blessings is obligatory",
                "Arrogance causes destruction"
            ],
            relationships=[
                StoryRelationship(
                    source_id="qarun",
                    source_name="قارون",
                    target_id="musa",
                    target_name="موسى",
                    relationship_type=RelationshipType.CONTEMPORARY,
                    description_ar="كان قارون من قوم موسى",
                    description_en="Qarun was from the people of Moses"
                )
            ],
            related_stories=["musa", "firaun_nation"],
            tafsir_references=[
                {
                    "scholar": "ابن كثير",
                    "source": "تفسير القرآن العظيم",
                    "summary_ar": "قصة قارون وعاقبته",
                    "summary_en": "Story of Qarun and his end"
                }
            ],
            completeness_score=0.85,
            is_verified=True
        )

        # Story: People of 'Ad (قوم عاد)
        self._stories["aad"] = Story(
            id="aad",
            title_ar="قصة قوم عاد",
            title_en="Story of the People of 'Ad",
            category=StoryCategory.NATIONS,
            category_ar="الأمم",
            themes=[StoryTheme.PUNISHMENT, StoryTheme.FAITH],
            themes_ar=["العقاب", "الإيمان"],
            summary_ar="قوم عاد كانوا من أقوى الأمم، كذبوا نبيهم هوداً فأهلكهم الله بريح صرصر عاتية.",
            summary_en="The people of 'Ad were among the strongest nations. They denied their prophet Hud, so Allah destroyed them with a violent wind.",
            figures=[
                StoryFigure(
                    id="hud",
                    name_ar="هود",
                    name_en="Hud",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="نبي أرسل لقوم عاد",
                    description_en="Prophet sent to the people of 'Ad",
                    is_prophet=True
                )
            ],
            events=[
                StoryEvent(
                    id="hud_mission",
                    name_ar="رسالة هود",
                    name_en="Hud's Mission",
                    description_ar="أرسل الله هوداً لقوم عاد لدعوتهم للتوحيد",
                    description_en="Allah sent Hud to the people of 'Ad to call them to monotheism",
                    sequence=1,
                    verses=["7:65-72", "11:50-60"],
                    significance_ar="دعوة التوحيد",
                    significance_en="Call to monotheism"
                ),
                StoryEvent(
                    id="aad_destruction",
                    name_ar="هلاك عاد",
                    name_en="Destruction of 'Ad",
                    description_ar="أهلكهم الله بريح صرصر عاتية سبع ليال وثمانية أيام",
                    description_en="Allah destroyed them with a violent wind for seven nights and eight days",
                    sequence=2,
                    verses=["69:6-8", "54:19-21"],
                    significance_ar="عاقبة التكذيب",
                    significance_en="Consequence of denial"
                )
            ],
            verses=[
                StoryVerse(
                    surah=7,
                    ayah_start=65,
                    ayah_end=72,
                    text_ar="وَإِلَىٰ عَادٍ أَخَاهُمْ هُودًا ۗ قَالَ يَا قَوْمِ اعْبُدُوا اللَّهَ مَا لَكُم مِّنْ إِلَٰهٍ غَيْرُهُ...",
                    text_en="And to 'Ad [We sent] their brother Hud. He said, 'O my people, worship Allah; you have no deity other than Him...'",
                    context_ar="سورة الأعراف - قصة عاد",
                    context_en="Surah Al-A'raf - Story of 'Ad"
                )
            ],
            key_lessons_ar=[
                "القوة لا تنفع مع الكفر",
                "عاقبة التكذيب الهلاك"
            ],
            key_lessons_en=[
                "Strength does not benefit with disbelief",
                "Consequence of denial is destruction"
            ],
            relationships=[
                StoryRelationship(
                    source_id="hud",
                    source_name="هود",
                    target_id="nuh",
                    target_name="نوح",
                    relationship_type=RelationshipType.PREDECESSOR,
                    description_ar="عاد بعد قوم نوح",
                    description_en="'Ad came after the people of Noah"
                )
            ],
            related_stories=["thamud", "nuh"],
            tafsir_references=[],
            completeness_score=0.80,
            is_verified=True
        )

        # Story: People of Thamud (قوم ثمود)
        self._stories["thamud"] = Story(
            id="thamud",
            title_ar="قصة قوم ثمود",
            title_en="Story of the People of Thamud",
            category=StoryCategory.NATIONS,
            category_ar="الأمم",
            themes=[StoryTheme.PUNISHMENT, StoryTheme.FAITH],
            themes_ar=["العقاب", "الإيمان"],
            summary_ar="قوم ثمود نحتوا البيوت في الجبال، أرسل الله إليهم صالحاً وآتاهم الناقة آية فعقروها، فأهلكهم الله بالصيحة.",
            summary_en="The people of Thamud carved homes in the mountains. Allah sent to them Salih and gave them the she-camel as a sign, but they slaughtered it, so Allah destroyed them with the blast.",
            figures=[
                StoryFigure(
                    id="salih",
                    name_ar="صالح",
                    name_en="Salih",
                    role="prophet",
                    role_ar="نبي",
                    description_ar="نبي أرسل لقوم ثمود",
                    description_en="Prophet sent to the people of Thamud",
                    is_prophet=True
                )
            ],
            events=[
                StoryEvent(
                    id="salih_camel",
                    name_ar="ناقة صالح",
                    name_en="Salih's She-Camel",
                    description_ar="آتى الله ثمود الناقة آية بينة",
                    description_en="Allah gave Thamud the she-camel as a clear sign",
                    sequence=1,
                    verses=["7:73", "11:64"],
                    significance_ar="المعجزة البينة",
                    significance_en="Clear miracle"
                ),
                StoryEvent(
                    id="camel_killed",
                    name_ar="عقر الناقة",
                    name_en="Killing the She-Camel",
                    description_ar="عقروا الناقة وعتوا عن أمر ربهم",
                    description_en="They killed the she-camel and defied their Lord's command",
                    sequence=2,
                    verses=["7:77", "91:14"],
                    significance_ar="التحدي والطغيان",
                    significance_en="Defiance and tyranny"
                ),
                StoryEvent(
                    id="thamud_destruction",
                    name_ar="هلاك ثمود",
                    name_en="Destruction of Thamud",
                    description_ar="أخذتهم الصيحة فأصبحوا في دارهم جاثمين",
                    description_en="The blast seized them and they became fallen in their homes",
                    sequence=3,
                    verses=["7:78", "11:67-68"],
                    significance_ar="عقاب الظالمين",
                    significance_en="Punishment of the oppressors"
                )
            ],
            verses=[
                StoryVerse(
                    surah=7,
                    ayah_start=73,
                    ayah_end=79,
                    text_ar="وَإِلَىٰ ثَمُودَ أَخَاهُمْ صَالِحًا ۗ قَالَ يَا قَوْمِ اعْبُدُوا اللَّهَ...",
                    text_en="And to Thamud [We sent] their brother Salih. He said, 'O my people, worship Allah...'",
                    context_ar="سورة الأعراف - قصة ثمود",
                    context_en="Surah Al-A'raf - Story of Thamud"
                )
            ],
            key_lessons_ar=[
                "رفض الآيات يجلب العذاب",
                "الاستكبار على الحق هلاك"
            ],
            key_lessons_en=[
                "Rejecting signs brings punishment",
                "Arrogance against truth is destruction"
            ],
            relationships=[
                StoryRelationship(
                    source_id="salih",
                    source_name="صالح",
                    target_id="hud",
                    target_name="هود",
                    relationship_type=RelationshipType.PREDECESSOR,
                    description_ar="ثمود بعد عاد",
                    description_en="Thamud came after 'Ad"
                )
            ],
            related_stories=["aad", "lut"],
            tafsir_references=[],
            completeness_score=0.78,
            is_verified=True
        )

    def _build_search_index(self):
        """Build search index for stories"""
        for story_id, story in self._stories.items():
            terms = []
            # Add Arabic and English titles
            terms.append(story.title_ar.lower())
            terms.append(story.title_en.lower())
            # Add category
            terms.append(story.category.value.lower())
            terms.append(story.category_ar)
            # Add themes
            for theme in story.themes:
                terms.append(theme.value.lower())
            for theme in story.themes_ar:
                terms.append(theme)
            # Add figure names
            for figure in story.figures:
                terms.append(figure.name_ar)
                terms.append(figure.name_en.lower())
            # Add event names
            for event in story.events:
                terms.append(event.name_ar)
                terms.append(event.name_en.lower())

            for term in terms:
                if term not in self._search_index:
                    self._search_index[term] = []
                if story_id not in self._search_index[term]:
                    self._search_index[term].append(story_id)

    # Public Methods

    def get_all_stories(
        self,
        category: Optional[str] = None,
        theme: Optional[str] = None,
        verified_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all stories with optional filtering"""
        stories = list(self._stories.values())

        # Filter by category
        if category:
            stories = [s for s in stories if s.category.value == category]

        # Filter by theme
        if theme:
            stories = [s for s in stories if any(t.value == theme for t in s.themes)]

        # Filter by verification status
        if verified_only:
            stories = [s for s in stories if s.is_verified]

        # Apply pagination
        total = len(stories)
        stories = stories[offset:offset + limit]

        return {
            "stories": [self._story_to_summary(s) for s in stories],
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "category": category,
                "theme": theme,
                "verified_only": verified_only
            }
        }

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Get complete story details"""
        story = self._stories.get(story_id)
        if not story:
            return None
        return self._story_to_dict(story)

    def verify_story(self, story_id: str) -> Dict[str, Any]:
        """Verify story classification and completeness"""
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        issues = []
        suggestions = []

        # Check title
        if not story.title_ar:
            issues.append("Missing Arabic title")
        if not story.title_en:
            issues.append("Missing English title")

        # Check category
        if not story.category_ar:
            issues.append("Missing Arabic category")

        # Check themes
        if len(story.themes) == 0:
            issues.append("No themes assigned")
        if len(story.themes_ar) == 0:
            issues.append("No Arabic themes")

        # Check summary
        if not story.summary_ar:
            issues.append("Missing Arabic summary")
        if not story.summary_en:
            issues.append("Missing English summary")

        # Check figures
        if len(story.figures) == 0:
            issues.append("No figures/characters")
            suggestions.append("Add key figures with Arabic and English names")

        # Check events
        if len(story.events) == 0:
            issues.append("No events")
            suggestions.append("Add key events with verses")

        # Check verses
        if len(story.verses) == 0:
            issues.append("No verse references")
            suggestions.append("Add Quranic verse references")

        # Check lessons
        if len(story.key_lessons_ar) == 0:
            issues.append("No Arabic lessons")
        if len(story.key_lessons_en) == 0:
            issues.append("No English lessons")

        # Check relationships
        if len(story.relationships) == 0:
            suggestions.append("Consider adding relationships to other stories/figures")

        # Check tafsir references
        if len(story.tafsir_references) == 0:
            suggestions.append("Add tafsir references from the four madhabs")

        # Calculate completeness
        completeness = story.completeness_score
        is_complete = len(issues) == 0

        return {
            "story_id": story_id,
            "title_ar": story.title_ar,
            "title_en": story.title_en,
            "is_verified": story.is_verified,
            "is_complete": is_complete,
            "completeness_score": completeness,
            "issues": issues,
            "suggestions": suggestions,
            "classification": {
                "category": story.category.value,
                "category_ar": story.category_ar,
                "themes": [t.value for t in story.themes],
                "themes_ar": story.themes_ar
            }
        }

    def get_story_graph(self, story_id: str) -> Dict[str, Any]:
        """Get graph visualization data for a story"""
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        nodes = []
        edges = []

        # Add story as central node
        nodes.append({
            "id": story.id,
            "label": story.title_ar,
            "label_en": story.title_en,
            "type": "story",
            "category": story.category.value,
            "x": 0,
            "y": 0,
            "size": 30,
            "color": "#4CAF50"
        })

        # Add figures
        angle_step = 360 / max(len(story.figures), 1)
        for i, figure in enumerate(story.figures):
            import math
            angle = math.radians(i * angle_step)
            nodes.append({
                "id": figure.id,
                "label": figure.name_ar,
                "label_en": figure.name_en,
                "type": "prophet" if figure.is_prophet else "figure",
                "role": figure.role,
                "role_ar": figure.role_ar,
                "x": 200 * math.cos(angle),
                "y": 200 * math.sin(angle),
                "size": 25 if figure.is_prophet else 20,
                "color": "#2196F3" if figure.is_prophet else "#FF9800"
            })
            edges.append({
                "source": story.id,
                "target": figure.id,
                "label": "شخصية في القصة",
                "label_en": "Character in story",
                "type": "contains"
            })

        # Add events
        for i, event in enumerate(story.events):
            import math
            angle = math.radians(45 + i * 30)
            nodes.append({
                "id": event.id,
                "label": event.name_ar,
                "label_en": event.name_en,
                "type": "event",
                "sequence": event.sequence,
                "x": 300 * math.cos(angle),
                "y": 300 * math.sin(angle),
                "size": 15,
                "color": "#9C27B0"
            })
            edges.append({
                "source": story.id,
                "target": event.id,
                "label": f"الحدث {event.sequence}",
                "label_en": f"Event {event.sequence}",
                "type": "event"
            })

        # Add event-to-event connections for sequence
        sorted_events = sorted(story.events, key=lambda e: e.sequence)
        for i in range(len(sorted_events) - 1):
            edges.append({
                "source": sorted_events[i].id,
                "target": sorted_events[i + 1].id,
                "label": "يليه",
                "label_en": "followed by",
                "type": "sequence"
            })

        # Add themes
        for i, theme in enumerate(story.themes):
            import math
            angle = math.radians(-45 + i * 20)
            theme_data = self._themes.get(theme.value, {})
            nodes.append({
                "id": f"theme_{theme.value}",
                "label": theme_data.get("name_ar", theme.value),
                "label_en": theme_data.get("name_en", theme.value),
                "type": "theme",
                "x": 350 * math.cos(angle),
                "y": 350 * math.sin(angle),
                "size": 18,
                "color": "#E91E63"
            })
            edges.append({
                "source": story.id,
                "target": f"theme_{theme.value}",
                "label": "موضوع",
                "label_en": "Theme",
                "type": "theme"
            })

        # Add relationships
        for rel in story.relationships:
            # Check if target node already exists
            target_exists = any(n["id"] == rel.target_id for n in nodes)
            if not target_exists:
                nodes.append({
                    "id": rel.target_id,
                    "label": rel.target_name,
                    "label_en": rel.target_name,
                    "type": "related",
                    "x": 400,
                    "y": 100 * len([n for n in nodes if n["type"] == "related"]),
                    "size": 15,
                    "color": "#607D8B"
                })

            edges.append({
                "source": rel.source_id,
                "target": rel.target_id,
                "label": rel.description_ar,
                "label_en": rel.description_en,
                "type": rel.relationship_type.value
            })

        return {
            "story_id": story_id,
            "title_ar": story.title_ar,
            "title_en": story.title_en,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "legend": {
                "node_types": [
                    {"type": "story", "color": "#4CAF50", "label_ar": "القصة", "label_en": "Story"},
                    {"type": "prophet", "color": "#2196F3", "label_ar": "نبي", "label_en": "Prophet"},
                    {"type": "figure", "color": "#FF9800", "label_ar": "شخصية", "label_en": "Figure"},
                    {"type": "event", "color": "#9C27B0", "label_ar": "حدث", "label_en": "Event"},
                    {"type": "theme", "color": "#E91E63", "label_ar": "موضوع", "label_en": "Theme"},
                    {"type": "related", "color": "#607D8B", "label_ar": "مرتبط", "label_en": "Related"}
                ]
            }
        }

    def get_story_relationships(self, story_id: str) -> Dict[str, Any]:
        """Get all relationships for a story"""
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        # Direct relationships
        direct = []
        for rel in story.relationships:
            direct.append({
                "source": {"id": rel.source_id, "name": rel.source_name},
                "target": {"id": rel.target_id, "name": rel.target_name},
                "type": rel.relationship_type.value,
                "description_ar": rel.description_ar,
                "description_en": rel.description_en
            })

        # Related stories
        related = []
        for related_id in story.related_stories:
            related_story = self._stories.get(related_id)
            if related_story:
                related.append({
                    "id": related_id,
                    "title_ar": related_story.title_ar,
                    "title_en": related_story.title_en,
                    "category": related_story.category.value,
                    "shared_themes": [t.value for t in story.themes if t in related_story.themes]
                })

        # Inverse relationships (stories that reference this story)
        inverse = []
        for other_id, other_story in self._stories.items():
            if other_id != story_id and story_id in other_story.related_stories:
                inverse.append({
                    "id": other_id,
                    "title_ar": other_story.title_ar,
                    "title_en": other_story.title_en
                })

        return {
            "story_id": story_id,
            "title_ar": story.title_ar,
            "direct_relationships": direct,
            "related_stories": related,
            "inverse_relationships": inverse,
            "total_relationships": len(direct) + len(related) + len(inverse)
        }

    def search_stories(
        self,
        query: str,
        category: Optional[str] = None,
        theme: Optional[str] = None,
        prophet: Optional[str] = None,
        event: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search stories by various criteria"""
        results = []
        query_lower = query.lower()

        for story_id, story in self._stories.items():
            score = 0
            matches = []

            # Check title match
            if query_lower in story.title_ar or query_lower in story.title_en.lower():
                score += 10
                matches.append("title")

            # Check summary match
            if query_lower in story.summary_ar or query_lower in story.summary_en.lower():
                score += 5
                matches.append("summary")

            # Check figure names
            for figure in story.figures:
                if query_lower in figure.name_ar or query_lower in figure.name_en.lower():
                    score += 8
                    matches.append(f"figure:{figure.name_en}")

            # Check event names
            for event_obj in story.events:
                if query_lower in event_obj.name_ar or query_lower in event_obj.name_en.lower():
                    score += 6
                    matches.append(f"event:{event_obj.name_en}")

            # Apply filters
            if category and story.category.value != category:
                continue
            if theme and not any(t.value == theme for t in story.themes):
                continue
            if prophet:
                if not any(f.name_en.lower() == prophet.lower() or f.name_ar == prophet for f in story.figures if f.is_prophet):
                    continue
            if event:
                if not any(e.name_en.lower() == event.lower() or e.name_ar == event for e in story.events):
                    continue

            if score > 0:
                results.append({
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category_ar": story.category_ar,
                    "category": story.category.value,
                    "score": score,
                    "matches": matches,
                    "completeness_score": story.completeness_score
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
            "filters": {
                "category": category,
                "theme": theme,
                "prophet": prophet,
                "event": event
            }
        }

    def get_categories(self) -> Dict[str, Any]:
        """Get all story categories with Arabic names"""
        categories = []
        for cat_id, cat_data in self._categories.items():
            story_count = len([s for s in self._stories.values() if s.category.value == cat_id])
            categories.append({
                **cat_data,
                "story_count": story_count
            })
        return {
            "categories": categories,
            "total": len(categories)
        }

    def get_themes(self) -> Dict[str, Any]:
        """Get all story themes with Arabic names"""
        themes = []
        for theme_id, theme_data in self._themes.items():
            story_count = len([s for s in self._stories.values() if any(t.value == theme_id for t in s.themes)])
            themes.append({
                **theme_data,
                "story_count": story_count
            })
        return {
            "themes": themes,
            "total": len(themes)
        }

    def get_prophets(self) -> Dict[str, Any]:
        """Get all prophets mentioned in stories"""
        prophets = {}
        for story in self._stories.values():
            for figure in story.figures:
                if figure.is_prophet and figure.id not in prophets:
                    prophets[figure.id] = {
                        "id": figure.id,
                        "name_ar": figure.name_ar,
                        "name_en": figure.name_en,
                        "description_ar": figure.description_ar,
                        "description_en": figure.description_en,
                        "stories": []
                    }
                if figure.is_prophet:
                    prophets[figure.id]["stories"].append({
                        "story_id": story.id,
                        "title_ar": story.title_ar
                    })

        return {
            "prophets": list(prophets.values()),
            "total": len(prophets)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get Alatlas statistics"""
        total_stories = len(self._stories)
        verified_stories = len([s for s in self._stories.values() if s.is_verified])
        total_events = sum(len(s.events) for s in self._stories.values())
        total_figures = sum(len(s.figures) for s in self._stories.values())
        total_relationships = sum(len(s.relationships) for s in self._stories.values())

        # Stories by category
        by_category = {}
        for cat_id in self._categories:
            by_category[cat_id] = len([s for s in self._stories.values() if s.category.value == cat_id])

        # Average completeness
        avg_completeness = sum(s.completeness_score for s in self._stories.values()) / max(total_stories, 1)

        return {
            "total_stories": total_stories,
            "verified_stories": verified_stories,
            "verification_percentage": round(verified_stories / max(total_stories, 1) * 100, 1),
            "total_events": total_events,
            "total_figures": total_figures,
            "total_relationships": total_relationships,
            "total_categories": len(self._categories),
            "total_themes": len(self._themes),
            "stories_by_category": by_category,
            "average_completeness": round(avg_completeness, 2)
        }

    # Helper Methods

    def _story_to_summary(self, story: Story) -> Dict[str, Any]:
        """Convert story to summary dict"""
        return {
            "id": story.id,
            "title_ar": story.title_ar,
            "title_en": story.title_en,
            "category": story.category.value,
            "category_ar": story.category_ar,
            "themes": [t.value for t in story.themes],
            "themes_ar": story.themes_ar,
            "summary_ar": story.summary_ar[:200] + "..." if len(story.summary_ar) > 200 else story.summary_ar,
            "summary_en": story.summary_en[:200] + "..." if len(story.summary_en) > 200 else story.summary_en,
            "figure_count": len(story.figures),
            "event_count": len(story.events),
            "verse_count": len(story.verses),
            "completeness_score": story.completeness_score,
            "is_verified": story.is_verified
        }

    def _story_to_dict(self, story: Story) -> Dict[str, Any]:
        """Convert complete story to dict"""
        return {
            "id": story.id,
            "title_ar": story.title_ar,
            "title_en": story.title_en,
            "category": story.category.value,
            "category_ar": story.category_ar,
            "themes": [{"id": t.value, "name_ar": self._themes.get(t.value, {}).get("name_ar", t.value)} for t in story.themes],
            "themes_ar": story.themes_ar,
            "summary_ar": story.summary_ar,
            "summary_en": story.summary_en,
            "figures": [
                {
                    "id": f.id,
                    "name_ar": f.name_ar,
                    "name_en": f.name_en,
                    "role": f.role,
                    "role_ar": f.role_ar,
                    "description_ar": f.description_ar,
                    "description_en": f.description_en,
                    "is_prophet": f.is_prophet
                }
                for f in story.figures
            ],
            "events": [
                {
                    "id": e.id,
                    "name_ar": e.name_ar,
                    "name_en": e.name_en,
                    "description_ar": e.description_ar,
                    "description_en": e.description_en,
                    "sequence": e.sequence,
                    "verses": e.verses,
                    "significance_ar": e.significance_ar,
                    "significance_en": e.significance_en
                }
                for e in sorted(story.events, key=lambda x: x.sequence)
            ],
            "verses": [
                {
                    "surah": v.surah,
                    "ayah_start": v.ayah_start,
                    "ayah_end": v.ayah_end,
                    "reference": f"{v.surah}:{v.ayah_start}-{v.ayah_end}",
                    "text_ar": v.text_ar,
                    "text_en": v.text_en,
                    "context_ar": v.context_ar,
                    "context_en": v.context_en
                }
                for v in story.verses
            ],
            "key_lessons_ar": story.key_lessons_ar,
            "key_lessons_en": story.key_lessons_en,
            "relationships": [
                {
                    "source_id": r.source_id,
                    "source_name": r.source_name,
                    "target_id": r.target_id,
                    "target_name": r.target_name,
                    "type": r.relationship_type.value,
                    "description_ar": r.description_ar,
                    "description_en": r.description_en
                }
                for r in story.relationships
            ],
            "related_stories": [
                {
                    "id": rid,
                    "title_ar": self._stories[rid].title_ar if rid in self._stories else rid,
                    "title_en": self._stories[rid].title_en if rid in self._stories else rid
                }
                for rid in story.related_stories
            ],
            "tafsir_references": story.tafsir_references,
            "completeness_score": story.completeness_score,
            "is_verified": story.is_verified
        }

    def get_complete_graph(self) -> Dict[str, Any]:
        """Get complete graph visualization for all stories (الرسم البياني الكامل)"""
        nodes = []
        edges = []
        node_ids = set()

        for story_id, story in self._stories.items():
            # Add story node
            if story_id not in node_ids:
                nodes.append({
                    "id": story_id,
                    "label": story.title_ar,
                    "label_en": story.title_en,
                    "type": "story",
                    "category": story.category.value,
                    "size": 25,
                    "color": "#4CAF50"
                })
                node_ids.add(story_id)

            # Add prophet figures
            for figure in story.figures:
                if figure.is_prophet and figure.id not in node_ids:
                    nodes.append({
                        "id": figure.id,
                        "label": figure.name_ar,
                        "label_en": figure.name_en,
                        "type": "prophet",
                        "size": 20,
                        "color": "#2196F3"
                    })
                    node_ids.add(figure.id)

                # Add edge from figure to story
                if figure.is_prophet:
                    edges.append({
                        "source": figure.id,
                        "target": story_id,
                        "type": "prophet_in_story",
                        "label": "في قصة"
                    })

            # Add relationships between stories
            for related_id in story.related_stories:
                if related_id in self._stories:
                    edge_id = f"{story_id}_{related_id}"
                    reverse_id = f"{related_id}_{story_id}"
                    # Avoid duplicate edges
                    if not any(e.get("id") in [edge_id, reverse_id] for e in edges):
                        edges.append({
                            "id": edge_id,
                            "source": story_id,
                            "target": related_id,
                            "type": "related_story",
                            "label": "مرتبطة"
                        })

        return {
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    def advanced_filter(
        self,
        categories: Optional[List[str]] = None,
        themes: Optional[List[str]] = None,
        prophets: Optional[List[str]] = None,
        min_verses: int = 0,
        min_events: int = 0,
        verified_only: bool = False
    ) -> Dict[str, Any]:
        """Advanced filtering for stories"""
        results = []

        for story in self._stories.values():
            # Category filter
            if categories and story.category.value not in categories:
                continue

            # Themes filter (match any)
            if themes:
                story_themes = [t.value for t in story.themes]
                if not any(t in story_themes for t in themes):
                    continue

            # Prophet filter
            if prophets:
                story_prophets = [f.name_ar for f in story.figures if f.is_prophet]
                story_prophets.extend([f.name_en for f in story.figures if f.is_prophet])
                if not any(p in story_prophets for p in prophets):
                    continue

            # Min verses filter
            if min_verses > 0 and len(story.verses) < min_verses:
                continue

            # Min events filter
            if min_events > 0 and len(story.events) < min_events:
                continue

            # Verified filter
            if verified_only and not story.is_verified:
                continue

            results.append(self._story_to_summary(story))

        return {
            "stories": results,
            "total": len(results),
            "filters": {
                "categories": categories,
                "themes": themes,
                "prophets": prophets,
                "min_verses": min_verses,
                "min_events": min_events,
                "verified_only": verified_only
            }
        }

    def get_timeline(self) -> Dict[str, Any]:
        """Get chronological timeline of stories"""
        timeline = []
        order = 0

        # Define chronological order of stories
        chronological_order = [
            "adam",      # Creation
            "nuh",       # Prophet Nuh
            "aad",       # People of Aad (Hud)
            "thamud",    # People of Thamud (Salih)
            "ibrahim",   # Prophet Ibrahim
            "yusuf",     # Prophet Yusuf
            "musa",      # Prophet Musa
            "qarun",     # Story of Qarun
            "ahlul_kahf" # People of the Cave
        ]

        for story_id in chronological_order:
            if story_id in self._stories:
                story = self._stories[story_id]
                order += 1
                timeline.append({
                    "order": order,
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category": story.category.value,
                    "category_ar": story.category_ar,
                    "summary_ar": story.summary_ar[:150] + "..." if len(story.summary_ar) > 150 else story.summary_ar,
                    "era": self._get_story_era(story_id)
                })

        # Add remaining stories not in chronological list
        for story_id, story in self._stories.items():
            if story_id not in chronological_order:
                order += 1
                timeline.append({
                    "order": order,
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category": story.category.value,
                    "category_ar": story.category_ar,
                    "summary_ar": story.summary_ar[:150] + "..." if len(story.summary_ar) > 150 else story.summary_ar,
                    "era": self._get_story_era(story_id)
                })

        return {
            "timeline": timeline,
            "total": len(timeline)
        }

    def _get_story_era(self, story_id: str) -> str:
        """Get era/period for a story"""
        eras = {
            "adam": "بداية الخلق",
            "nuh": "ما قبل إبراهيم",
            "aad": "ما قبل إبراهيم",
            "thamud": "ما قبل إبراهيم",
            "ibrahim": "عصر إبراهيم",
            "yusuf": "عصر يعقوب ويوسف",
            "musa": "عصر موسى",
            "qarun": "عصر موسى",
            "ahlul_kahf": "ما بعد عيسى"
        }
        return eras.get(story_id, "غير محدد")

    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_statistics (for API compatibility)"""
        stats = self.get_statistics()
        return {
            "stats": stats
        }

    # ========================================
    # ENHANCED SEARCH FUNCTIONALITY
    # ========================================

    def fuzzy_search(self, query: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Calculate fuzzy match scores using Levenshtein-like similarity"""
        def similarity(s1: str, s2: str) -> float:
            """Calculate similarity ratio between two strings"""
            s1, s2 = s1.lower(), s2.lower()
            if s1 == s2:
                return 1.0
            if len(s1) == 0 or len(s2) == 0:
                return 0.0

            # Simple character overlap ratio
            common = sum(1 for c in s1 if c in s2)
            return (2.0 * common) / (len(s1) + len(s2))

        matches = []
        query_normalized = query.lower().strip()

        for story_id, story in self._stories.items():
            max_score = 0.0
            match_field = ""

            # Check title similarity
            title_score = max(
                similarity(query_normalized, story.title_ar),
                similarity(query_normalized, story.title_en.lower())
            )
            if title_score > max_score:
                max_score = title_score
                match_field = "title"

            # Check figure names
            for figure in story.figures:
                fig_score = max(
                    similarity(query_normalized, figure.name_ar),
                    similarity(query_normalized, figure.name_en.lower())
                )
                if fig_score > max_score:
                    max_score = fig_score
                    match_field = f"figure:{figure.name_en}"

            # Check event names
            for event in story.events:
                event_score = max(
                    similarity(query_normalized, event.name_ar),
                    similarity(query_normalized, event.name_en.lower())
                )
                if event_score > max_score:
                    max_score = event_score
                    match_field = f"event:{event.name_en}"

            # Check themes
            for theme_ar in story.themes_ar:
                theme_score = similarity(query_normalized, theme_ar)
                if theme_score > max_score:
                    max_score = theme_score
                    match_field = f"theme:{theme_ar}"

            if max_score >= threshold:
                matches.append((story_id, max_score, match_field))

        return sorted(matches, key=lambda x: x[1], reverse=True)

    def search_advanced(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        themes: Optional[List[str]] = None,
        prophets: Optional[List[str]] = None,
        time_period: Optional[str] = None,
        fuzzy: bool = True,
        fuzzy_threshold: float = 0.5,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Advanced search with fuzzy matching, keyword expansion, and filters.
        Supports typo tolerance and query expansion.
        """
        results = []
        query_lower = query.lower().strip()

        # Query expansion - common Arabic/English variations
        query_expansions = self._expand_query(query_lower)

        for story_id, story in self._stories.items():
            score = 0
            matches = []
            relevance_details = {}

            # Apply category filter
            if categories and story.category.value not in categories:
                continue

            # Apply theme filter
            if themes:
                story_themes = [t.value for t in story.themes]
                if not any(t in story_themes for t in themes):
                    continue

            # Apply prophet filter
            if prophets:
                story_prophets = [f.name_ar for f in story.figures if f.is_prophet]
                story_prophets.extend([f.name_en.lower() for f in story.figures if f.is_prophet])
                if not any(p.lower() in story_prophets or p in story_prophets for p in prophets):
                    continue

            # Apply time period filter
            if time_period:
                story_era = self._get_story_era(story_id)
                if time_period not in story_era:
                    continue

            # Exact match scoring
            for expanded_query in query_expansions:
                # Title match
                if expanded_query in story.title_ar or expanded_query in story.title_en.lower():
                    score += 15
                    matches.append("title")
                    relevance_details["title_match"] = True

                # Summary match
                if expanded_query in story.summary_ar or expanded_query in story.summary_en.lower():
                    score += 8
                    matches.append("summary")

                # Figure name match
                for figure in story.figures:
                    if expanded_query in figure.name_ar or expanded_query in figure.name_en.lower():
                        score += 12
                        matches.append(f"figure:{figure.name_en}")

                # Event match
                for event in story.events:
                    if expanded_query in event.name_ar or expanded_query in event.name_en.lower():
                        score += 10
                        matches.append(f"event:{event.name_en}")

                # Theme match
                for theme_ar in story.themes_ar:
                    if expanded_query in theme_ar:
                        score += 6
                        matches.append(f"theme:{theme_ar}")

            # Fuzzy matching if enabled and no exact matches
            if fuzzy and score == 0:
                fuzzy_results = self.fuzzy_search(query, fuzzy_threshold)
                for fid, fscore, fmatch in fuzzy_results:
                    if fid == story_id:
                        score = int(fscore * 10)
                        matches.append(f"fuzzy:{fmatch}")
                        relevance_details["fuzzy_match"] = True
                        relevance_details["fuzzy_score"] = fscore

            if score > 0:
                results.append({
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category": story.category.value,
                    "category_ar": story.category_ar,
                    "themes": [t.value for t in story.themes],
                    "themes_ar": story.themes_ar,
                    "score": score,
                    "matches": list(set(matches)),
                    "relevance": relevance_details,
                    "completeness_score": story.completeness_score,
                    "summary_ar": story.summary_ar[:150] + "..." if len(story.summary_ar) > 150 else story.summary_ar
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "expanded_queries": query_expansions,
            "results": results[:limit],
            "total": len(results),
            "filters_applied": {
                "categories": categories,
                "themes": themes,
                "prophets": prophets,
                "time_period": time_period,
                "fuzzy_enabled": fuzzy
            }
        }

    def _expand_query(self, query: str) -> List[str]:
        """Expand query with common variations and synonyms"""
        expansions = [query]

        # Arabic/English prophet name variations
        name_variations = {
            "موسى": ["musa", "moses", "موسي"],
            "عيسى": ["isa", "jesus", "عيسي"],
            "إبراهيم": ["ibrahim", "abraham", "ابراهيم"],
            "يوسف": ["yusuf", "joseph", "يوسف"],
            "نوح": ["nuh", "noah", "نوح"],
            "آدم": ["adam", "ادم"],
            "داود": ["dawud", "david", "داوود"],
            "سليمان": ["sulayman", "solomon", "سليمان"],
            "يعقوب": ["yaqub", "jacob", "يعقوب"],
            "إسماعيل": ["ismail", "ishmael", "اسماعيل"],
            "إسحاق": ["ishaq", "isaac", "اسحاق"],
            "محمد": ["muhammad", "mohammed", "محمد"],
            "musa": ["موسى", "moses"],
            "ibrahim": ["إبراهيم", "abraham"],
            "yusuf": ["يوسف", "joseph"],
            "adam": ["آدم", "ادم"],
            "nuh": ["نوح", "noah"],
        }

        # Add variations for the query
        query_lower = query.lower()
        for key, variations in name_variations.items():
            if query_lower == key.lower() or query == key:
                expansions.extend(variations)

        # Theme variations
        theme_variations = {
            "صبر": ["patience", "الصبر"],
            "توكل": ["trust", "التوكل"],
            "إيمان": ["faith", "الإيمان"],
            "patience": ["صبر", "الصبر"],
            "faith": ["إيمان", "الإيمان"],
        }

        for key, variations in theme_variations.items():
            if query_lower == key.lower() or query == key:
                expansions.extend(variations)

        return list(set(expansions))

    def search_by_theme_and_prophet(
        self,
        theme: str,
        prophet: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search stories by specific theme and prophet combination"""
        results = []

        for story_id, story in self._stories.items():
            theme_match = any(t.value == theme for t in story.themes) or theme in story.themes_ar
            prophet_match = any(
                f.name_ar == prophet or f.name_en.lower() == prophet.lower()
                for f in story.figures if f.is_prophet
            )

            if theme_match and prophet_match:
                results.append({
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category_ar": story.category_ar,
                    "themes_ar": story.themes_ar,
                    "prophet_name": next(
                        (f.name_ar for f in story.figures if f.is_prophet and
                         (f.name_ar == prophet or f.name_en.lower() == prophet.lower())),
                        prophet
                    )
                })

        return {
            "theme": theme,
            "prophet": prophet,
            "results": results[:limit],
            "total": len(results)
        }

    # ========================================
    # DYNAMIC THEME & CATEGORY UPDATES
    # ========================================

    def get_dynamic_themes(self) -> Dict[str, Any]:
        """Get dynamically updated themes based on story content"""
        theme_stats = {}

        for theme_id, theme_data in self._themes.items():
            stories_with_theme = [
                s for s in self._stories.values()
                if any(t.value == theme_id for t in s.themes)
            ]
            theme_stats[theme_id] = {
                **theme_data,
                "story_count": len(stories_with_theme),
                "stories": [{"id": s.id, "title_ar": s.title_ar} for s in stories_with_theme],
                "related_themes": self._get_related_themes(theme_id),
                "popularity_rank": 0  # Will be calculated
            }

        # Calculate popularity rank
        sorted_themes = sorted(theme_stats.items(), key=lambda x: x[1]["story_count"], reverse=True)
        for rank, (theme_id, _) in enumerate(sorted_themes, 1):
            theme_stats[theme_id]["popularity_rank"] = rank

        return {
            "themes": list(theme_stats.values()),
            "total": len(theme_stats),
            "last_updated": datetime.now().isoformat()
        }

    def get_dynamic_categories(self) -> Dict[str, Any]:
        """Get dynamically updated categories based on story content"""
        category_stats = {}

        for cat_id, cat_data in self._categories.items():
            stories_in_category = [
                s for s in self._stories.values()
                if s.category.value == cat_id
            ]
            category_stats[cat_id] = {
                **cat_data,
                "story_count": len(stories_in_category),
                "stories": [{"id": s.id, "title_ar": s.title_ar} for s in stories_in_category],
                "themes_distribution": self._get_category_themes_distribution(cat_id),
                "completeness_avg": sum(s.completeness_score for s in stories_in_category) / max(len(stories_in_category), 1)
            }

        return {
            "categories": list(category_stats.values()),
            "total": len(category_stats),
            "last_updated": datetime.now().isoformat()
        }

    def _get_related_themes(self, theme_id: str) -> List[Dict[str, Any]]:
        """Find themes that commonly appear together with the given theme"""
        co_occurrence = {}

        for story in self._stories.values():
            story_themes = [t.value for t in story.themes]
            if theme_id in story_themes:
                for other_theme in story_themes:
                    if other_theme != theme_id:
                        co_occurrence[other_theme] = co_occurrence.get(other_theme, 0) + 1

        related = [
            {
                "theme_id": tid,
                "name_ar": self._themes.get(tid, {}).get("name_ar", tid),
                "co_occurrence_count": count
            }
            for tid, count in sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return related

    def _get_category_themes_distribution(self, category_id: str) -> Dict[str, int]:
        """Get theme distribution within a category"""
        theme_counts = {}

        for story in self._stories.values():
            if story.category.value == category_id:
                for theme in story.themes:
                    theme_counts[theme.value] = theme_counts.get(theme.value, 0) + 1

        return theme_counts

    # ========================================
    # ENHANCED GRAPH VISUALIZATION
    # ========================================

    def get_expanded_graph(
        self,
        include_themes: bool = True,
        include_events: bool = True,
        include_places: bool = True,
        color_by_theme: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced graph visualization with themes, prophets, events.
        Supports color-coding by theme and interactive elements.
        """
        nodes = []
        edges = []
        node_ids = set()

        # Theme color mapping
        theme_colors = {
            "patience": "#FFB74D",      # Orange
            "faith": "#64B5F6",         # Blue
            "trust": "#81C784",         # Green
            "justice": "#E57373",       # Red
            "mercy": "#BA68C8",         # Purple
            "obedience": "#4DB6AC",     # Teal
            "repentance": "#F06292",    # Pink
            "wisdom": "#FFD54F",        # Yellow
            "guidance": "#7986CB",      # Indigo
            "tawhid": "#4DD0E1",        # Cyan
            "default": "#90A4AE"        # Grey
        }

        for story_id, story in self._stories.items():
            # Determine primary theme color
            primary_theme = story.themes[0].value if story.themes else "default"
            story_color = theme_colors.get(primary_theme, theme_colors["default"]) if color_by_theme else "#4CAF50"

            # Add story node
            if story_id not in node_ids:
                nodes.append({
                    "id": story_id,
                    "label": story.title_ar,
                    "label_en": story.title_en,
                    "type": "story",
                    "category": story.category.value,
                    "category_ar": story.category_ar,
                    "primary_theme": primary_theme,
                    "size": 30,
                    "color": story_color,
                    "metadata": {
                        "themes": [t.value for t in story.themes],
                        "themes_ar": story.themes_ar,
                        "figure_count": len(story.figures),
                        "event_count": len(story.events)
                    }
                })
                node_ids.add(story_id)

            # Add prophet figures
            for figure in story.figures:
                if figure.is_prophet and figure.id not in node_ids:
                    nodes.append({
                        "id": figure.id,
                        "label": figure.name_ar,
                        "label_en": figure.name_en,
                        "type": "prophet",
                        "role": figure.role_ar,
                        "size": 25,
                        "color": "#2196F3",
                        "metadata": {
                            "description_ar": figure.description_ar,
                            "stories": []
                        }
                    })
                    node_ids.add(figure.id)

                # Edge from prophet to story
                if figure.is_prophet:
                    edges.append({
                        "source": figure.id,
                        "target": story_id,
                        "type": "prophet_in_story",
                        "label": "في قصة",
                        "weight": 2
                    })

            # Add theme nodes if requested
            if include_themes:
                for theme in story.themes:
                    theme_node_id = f"theme_{theme.value}"
                    if theme_node_id not in node_ids:
                        nodes.append({
                            "id": theme_node_id,
                            "label": self._themes.get(theme.value, {}).get("name_ar", theme.value),
                            "label_en": theme.value.title(),
                            "type": "theme",
                            "size": 15,
                            "color": theme_colors.get(theme.value, theme_colors["default"]),
                            "metadata": {}
                        })
                        node_ids.add(theme_node_id)

                    edges.append({
                        "source": story_id,
                        "target": theme_node_id,
                        "type": "story_theme",
                        "label": "موضوع",
                        "weight": 1
                    })

            # Add event nodes if requested
            if include_events:
                for event in story.events[:3]:  # Limit to top 3 events per story
                    event_node_id = f"event_{story_id}_{event.id}"
                    if event_node_id not in node_ids:
                        nodes.append({
                            "id": event_node_id,
                            "label": event.name_ar,
                            "label_en": event.name_en,
                            "type": "event",
                            "size": 12,
                            "color": "#FF9800",
                            "metadata": {
                                "description_ar": event.description_ar,
                                "sequence": event.sequence
                            }
                        })
                        node_ids.add(event_node_id)

                        edges.append({
                            "source": story_id,
                            "target": event_node_id,
                            "type": "story_event",
                            "label": "حدث",
                            "weight": 1
                        })

            # Add relationships between stories
            for related_id in story.related_stories:
                if related_id in self._stories:
                    edge_id = f"{story_id}_{related_id}"
                    if not any(e.get("id") == edge_id for e in edges):
                        edges.append({
                            "id": edge_id,
                            "source": story_id,
                            "target": related_id,
                            "type": "related_story",
                            "label": "مرتبطة",
                            "weight": 3
                        })

        return {
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": {
                "story": len([n for n in nodes if n["type"] == "story"]),
                "prophet": len([n for n in nodes if n["type"] == "prophet"]),
                "theme": len([n for n in nodes if n["type"] == "theme"]),
                "event": len([n for n in nodes if n["type"] == "event"])
            },
            "theme_colors": theme_colors
        }

    def find_thematic_path(
        self,
        start_story_id: str,
        end_story_id: str,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Use BFS to find thematic connection path between two stories.
        Shows how stories are interconnected through themes and relationships.
        """
        if start_story_id not in self._stories or end_story_id not in self._stories:
            return {"error": "One or both story IDs not found", "path": []}

        # BFS to find shortest thematic path
        from collections import deque

        visited = set()
        queue = deque([(start_story_id, [start_story_id], [])])  # (current, path, connections)

        while queue:
            current, path, connections = queue.popleft()

            if current == end_story_id:
                # Build detailed path
                detailed_path = []
                for i, story_id in enumerate(path):
                    story = self._stories[story_id]
                    connection = connections[i] if i < len(connections) else None
                    detailed_path.append({
                        "story_id": story_id,
                        "title_ar": story.title_ar,
                        "title_en": story.title_en,
                        "themes_ar": story.themes_ar,
                        "connection_to_next": connection
                    })

                return {
                    "found": True,
                    "path": detailed_path,
                    "path_length": len(path),
                    "start_story": self._stories[start_story_id].title_ar,
                    "end_story": self._stories[end_story_id].title_ar
                }

            if current in visited or len(path) > max_depth:
                continue

            visited.add(current)
            current_story = self._stories[current]

            # Explore related stories
            for related_id in current_story.related_stories:
                if related_id not in visited and related_id in self._stories:
                    related_story = self._stories[related_id]
                    # Find shared themes
                    current_themes = set(t.value for t in current_story.themes)
                    related_themes = set(t.value for t in related_story.themes)
                    shared = current_themes & related_themes
                    connection = {
                        "type": "related_story",
                        "shared_themes": list(shared),
                        "description": "قصص مرتبطة"
                    }
                    queue.append((related_id, path + [related_id], connections + [connection]))

            # Explore stories with shared themes
            current_themes = set(t.value for t in current_story.themes)
            for story_id, story in self._stories.items():
                if story_id not in visited and story_id != current:
                    story_themes = set(t.value for t in story.themes)
                    shared = current_themes & story_themes
                    if shared:
                        connection = {
                            "type": "shared_theme",
                            "shared_themes": list(shared),
                            "description": f"موضوع مشترك: {', '.join(shared)}"
                        }
                        queue.append((story_id, path + [story_id], connections + [connection]))

            # Explore stories with shared prophets
            current_prophets = set(f.id for f in current_story.figures if f.is_prophet)
            for story_id, story in self._stories.items():
                if story_id not in visited and story_id != current:
                    story_prophets = set(f.id for f in story.figures if f.is_prophet)
                    shared = current_prophets & story_prophets
                    if shared:
                        prophet_names = [f.name_ar for f in story.figures if f.id in shared]
                        connection = {
                            "type": "shared_prophet",
                            "shared_prophets": list(shared),
                            "description": f"نبي مشترك: {', '.join(prophet_names)}"
                        }
                        queue.append((story_id, path + [story_id], connections + [connection]))

        return {
            "found": False,
            "path": [],
            "message": f"No path found between {start_story_id} and {end_story_id} within depth {max_depth}"
        }

    # ========================================
    # STORY COMPLETENESS & DATA VERIFICATION
    # ========================================

    def verify_completeness(self, story_id: str) -> Dict[str, Any]:
        """
        Comprehensive verification of story completeness.
        Checks all aspects including themes, events, prophet-place relationships.
        """
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        verification = {
            "story_id": story_id,
            "title_ar": story.title_ar,
            "overall_score": 0.0,
            "sections": {},
            "issues": [],
            "suggestions": [],
            "detailed_checks": {}
        }

        # Basic info check (20%)
        basic_score = 0
        basic_checks = {
            "title_ar": bool(story.title_ar),
            "title_en": bool(story.title_en),
            "summary_ar": len(story.summary_ar) > 100,
            "summary_en": len(story.summary_en) > 100,
            "category_ar": bool(story.category_ar)
        }
        basic_score = sum(basic_checks.values()) / len(basic_checks)
        verification["sections"]["basic_info"] = {"score": basic_score, "checks": basic_checks}

        if not basic_checks["summary_ar"]:
            verification["issues"].append("Arabic summary too short (< 100 chars)")
            verification["suggestions"].append("Expand the Arabic summary with more details")

        # Themes check (15%)
        themes_score = 0
        themes_checks = {
            "has_themes": len(story.themes) > 0,
            "has_arabic_themes": len(story.themes_ar) > 0,
            "multiple_themes": len(story.themes) >= 2,
            "themes_match": len(story.themes) == len(story.themes_ar)
        }
        themes_score = sum(themes_checks.values()) / len(themes_checks)
        verification["sections"]["themes"] = {"score": themes_score, "checks": themes_checks}

        if not themes_checks["multiple_themes"]:
            verification["suggestions"].append("Add more thematic classifications for richer context")

        # Figures check (20%)
        figures_score = 0
        figures_checks = {
            "has_figures": len(story.figures) > 0,
            "has_prophet": any(f.is_prophet for f in story.figures),
            "figures_have_descriptions": all(f.description_ar for f in story.figures),
            "figures_have_roles": all(f.role_ar for f in story.figures),
            "multiple_figures": len(story.figures) >= 2
        }
        figures_score = sum(figures_checks.values()) / len(figures_checks)
        verification["sections"]["figures"] = {"score": figures_score, "checks": figures_checks}

        if not figures_checks["has_prophet"]:
            verification["issues"].append("No prophet identified in the story")

        # Events check (20%)
        events_score = 0
        events_checks = {
            "has_events": len(story.events) > 0,
            "events_have_descriptions": all(e.description_ar for e in story.events),
            "events_have_verses": all(e.verses for e in story.events),
            "events_sequenced": all(e.sequence for e in story.events),
            "multiple_events": len(story.events) >= 3
        }
        events_score = sum(events_checks.values()) / len(events_checks)
        verification["sections"]["events"] = {"score": events_score, "checks": events_checks}

        if not events_checks["events_have_verses"]:
            verification["suggestions"].append("Add Quranic verse references to all events")

        # Verses check (10%)
        verses_score = 0
        verses_checks = {
            "has_verses": len(story.verses) > 0,
            "verses_have_arabic": all(v.text_ar for v in story.verses),
            "verses_have_context": all(v.context_ar for v in story.verses),
            "multiple_verses": len(story.verses) >= 2
        }
        verses_score = sum(verses_checks.values()) / len(verses_checks)
        verification["sections"]["verses"] = {"score": verses_score, "checks": verses_checks}

        # Lessons check (10%)
        lessons_score = 0
        lessons_checks = {
            "has_arabic_lessons": len(story.key_lessons_ar) > 0,
            "has_english_lessons": len(story.key_lessons_en) > 0,
            "multiple_lessons": len(story.key_lessons_ar) >= 2,
            "lessons_match": len(story.key_lessons_ar) == len(story.key_lessons_en)
        }
        lessons_score = sum(lessons_checks.values()) / len(lessons_checks)
        verification["sections"]["lessons"] = {"score": lessons_score, "checks": lessons_checks}

        # Relationships check (5%)
        relationships_score = 0
        relationships_checks = {
            "has_relationships": len(story.relationships) > 0,
            "has_related_stories": len(story.related_stories) > 0
        }
        relationships_score = sum(relationships_checks.values()) / len(relationships_checks)
        verification["sections"]["relationships"] = {"score": relationships_score, "checks": relationships_checks}

        if not relationships_checks["has_related_stories"]:
            verification["suggestions"].append("Add connections to related stories")

        # Calculate overall score
        weights = {
            "basic_info": 0.20,
            "themes": 0.15,
            "figures": 0.20,
            "events": 0.20,
            "verses": 0.10,
            "lessons": 0.10,
            "relationships": 0.05
        }

        overall = sum(
            verification["sections"][section]["score"] * weight
            for section, weight in weights.items()
        )
        verification["overall_score"] = round(overall, 2)

        # Completeness level
        if overall >= 0.9:
            verification["completeness_level"] = "excellent"
            verification["completeness_level_ar"] = "ممتاز"
        elif overall >= 0.7:
            verification["completeness_level"] = "good"
            verification["completeness_level_ar"] = "جيد"
        elif overall >= 0.5:
            verification["completeness_level"] = "moderate"
            verification["completeness_level_ar"] = "متوسط"
        else:
            verification["completeness_level"] = "needs_improvement"
            verification["completeness_level_ar"] = "يحتاج تحسين"

        return verification

    def update_story(
        self,
        story_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a story with new or corrected information.
        Returns the updated story and verification result.
        """
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        updated_fields = []

        # Update basic fields
        if "title_ar" in updates:
            story.title_ar = updates["title_ar"]
            updated_fields.append("title_ar")

        if "title_en" in updates:
            story.title_en = updates["title_en"]
            updated_fields.append("title_en")

        if "summary_ar" in updates:
            story.summary_ar = updates["summary_ar"]
            updated_fields.append("summary_ar")

        if "summary_en" in updates:
            story.summary_en = updates["summary_en"]
            updated_fields.append("summary_en")

        if "themes_ar" in updates:
            story.themes_ar = updates["themes_ar"]
            updated_fields.append("themes_ar")

        if "key_lessons_ar" in updates:
            story.key_lessons_ar = updates["key_lessons_ar"]
            updated_fields.append("key_lessons_ar")

        if "key_lessons_en" in updates:
            story.key_lessons_en = updates["key_lessons_en"]
            updated_fields.append("key_lessons_en")

        if "related_stories" in updates:
            story.related_stories = updates["related_stories"]
            updated_fields.append("related_stories")

        if "tafsir_references" in updates:
            story.tafsir_references = updates["tafsir_references"]
            updated_fields.append("tafsir_references")

        # Recalculate completeness score
        story.completeness_score = self._calculate_completeness_score(story)

        # Rebuild search index
        self._build_search_index()

        return {
            "success": True,
            "story_id": story_id,
            "updated_fields": updated_fields,
            "new_completeness_score": story.completeness_score,
            "verification": self.verify_completeness(story_id)
        }

    def _calculate_completeness_score(self, story: Story) -> float:
        """Calculate completeness score for a story"""
        score = 0.0
        total_weight = 0.0

        # Basic info (20%)
        if story.title_ar:
            score += 0.04
        if story.title_en:
            score += 0.04
        if len(story.summary_ar) > 100:
            score += 0.06
        if len(story.summary_en) > 100:
            score += 0.06
        total_weight += 0.20

        # Themes (15%)
        if story.themes:
            score += 0.05
        if len(story.themes) >= 2:
            score += 0.05
        if story.themes_ar:
            score += 0.05
        total_weight += 0.15

        # Figures (20%)
        if story.figures:
            score += 0.08
        if any(f.is_prophet for f in story.figures):
            score += 0.06
        if len(story.figures) >= 2:
            score += 0.06
        total_weight += 0.20

        # Events (20%)
        if story.events:
            score += 0.10
        if len(story.events) >= 3:
            score += 0.10
        total_weight += 0.20

        # Verses (10%)
        if story.verses:
            score += 0.10
        total_weight += 0.10

        # Lessons (10%)
        if story.key_lessons_ar:
            score += 0.05
        if story.key_lessons_en:
            score += 0.05
        total_weight += 0.10

        # Relationships (5%)
        if story.relationships or story.related_stories:
            score += 0.05
        total_weight += 0.05

        return round(score, 2)

    # ========================================
    # USER FEEDBACK SYSTEM
    # ========================================

    def __init_feedback_storage(self):
        """Initialize feedback storage if not exists"""
        if not hasattr(self, '_feedback'):
            self._feedback: Dict[str, List[Dict[str, Any]]] = {}
            self._feedback_stats: Dict[str, Dict[str, Any]] = {}

    def submit_story_feedback(
        self,
        story_id: str,
        user_id: str,
        rating: int,
        accuracy_rating: int,
        completeness_rating: int,
        comment: Optional[str] = None,
        suggested_improvements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Submit user feedback for a story"""
        self.__init_feedback_storage()

        if story_id not in self._stories:
            return {"error": f"Story '{story_id}' not found"}

        if not 1 <= rating <= 5:
            return {"error": "Rating must be between 1 and 5"}

        feedback = {
            "user_id": user_id,
            "rating": rating,
            "accuracy_rating": accuracy_rating,
            "completeness_rating": completeness_rating,
            "comment": comment,
            "suggested_improvements": suggested_improvements or [],
            "timestamp": datetime.now().isoformat()
        }

        if story_id not in self._feedback:
            self._feedback[story_id] = []

        self._feedback[story_id].append(feedback)
        self._update_feedback_stats(story_id)

        return {
            "success": True,
            "story_id": story_id,
            "feedback_id": len(self._feedback[story_id]),
            "message": "شكراً لملاحظاتك - Thank you for your feedback"
        }

    def _update_feedback_stats(self, story_id: str):
        """Update aggregated feedback statistics"""
        if story_id not in self._feedback:
            return

        feedbacks = self._feedback[story_id]
        if not feedbacks:
            return

        self._feedback_stats[story_id] = {
            "total_feedbacks": len(feedbacks),
            "average_rating": sum(f["rating"] for f in feedbacks) / len(feedbacks),
            "average_accuracy": sum(f["accuracy_rating"] for f in feedbacks) / len(feedbacks),
            "average_completeness": sum(f["completeness_rating"] for f in feedbacks) / len(feedbacks),
            "recent_comments": [f["comment"] for f in feedbacks[-5:] if f["comment"]],
            "improvement_suggestions": list(set(
                imp for f in feedbacks for imp in f.get("suggested_improvements", [])
            )),
            "last_updated": datetime.now().isoformat()
        }

    def get_story_feedback(self, story_id: str) -> Dict[str, Any]:
        """Get aggregated feedback for a story"""
        self.__init_feedback_storage()

        if story_id not in self._stories:
            return {"error": f"Story '{story_id}' not found"}

        stats = self._feedback_stats.get(story_id, {
            "total_feedbacks": 0,
            "average_rating": 0,
            "average_accuracy": 0,
            "average_completeness": 0,
            "recent_comments": [],
            "improvement_suggestions": []
        })

        return {
            "story_id": story_id,
            "title_ar": self._stories[story_id].title_ar,
            "feedback_stats": stats
        }

    # ========================================
    # CONTENT EXPANSION - MORE PROPHETS & EVENTS
    # ========================================

    def get_prophet_details(self, prophet_id: str) -> Dict[str, Any]:
        """Get comprehensive details for a specific prophet"""
        prophet_info = None
        associated_stories = []
        all_events = []
        all_places = []

        for story_id, story in self._stories.items():
            for figure in story.figures:
                if figure.is_prophet and figure.id == prophet_id:
                    if not prophet_info:
                        prophet_info = {
                            "id": figure.id,
                            "name_ar": figure.name_ar,
                            "name_en": figure.name_en,
                            "description_ar": figure.description_ar,
                            "description_en": figure.description_en
                        }

                    associated_stories.append({
                        "story_id": story_id,
                        "title_ar": story.title_ar,
                        "title_en": story.title_en,
                        "category": story.category.value,
                        "themes": [t.value for t in story.themes]
                    })

                    # Collect events
                    for event in story.events:
                        all_events.append({
                            "event_id": event.id,
                            "name_ar": event.name_ar,
                            "name_en": event.name_en,
                            "story_id": story_id,
                            "sequence": event.sequence
                        })

                    # Collect places from relationships
                    for rel in story.relationships:
                        if rel.relationship_type == RelationshipType.PROPHET_TO_PLACE:
                            all_places.append({
                                "place_id": rel.target_id,
                                "name_ar": rel.target_name,
                                "description_ar": rel.description_ar
                            })

        if not prophet_info:
            return {"error": f"Prophet '{prophet_id}' not found"}

        # Get related prophets
        related_prophets = []
        for story in associated_stories:
            story_obj = self._stories.get(story["story_id"])
            if story_obj:
                for rel in story_obj.relationships:
                    if rel.relationship_type == RelationshipType.PROPHET_TO_PROPHET:
                        related_prophets.append({
                            "prophet_id": rel.target_id,
                            "name_ar": rel.target_name,
                            "relationship": rel.description_ar
                        })

        return {
            "prophet": prophet_info,
            "stories": associated_stories,
            "events": all_events,
            "places": list({p["place_id"]: p for p in all_places}.values()),  # Deduplicate
            "related_prophets": list({p["prophet_id"]: p for p in related_prophets}.values()),
            "total_stories": len(associated_stories),
            "total_events": len(all_events)
        }

    def get_all_events(
        self,
        category: Optional[str] = None,
        prophet: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get all historical events from Quranic stories"""
        events = []

        for story_id, story in self._stories.items():
            # Apply category filter
            if category and story.category.value != category:
                continue

            # Apply prophet filter
            if prophet:
                story_prophets = [f.id for f in story.figures if f.is_prophet]
                if prophet not in story_prophets:
                    has_prophet_name = any(
                        prophet in f.name_ar or prophet.lower() in f.name_en.lower()
                        for f in story.figures if f.is_prophet
                    )
                    if not has_prophet_name:
                        continue

            for event in story.events:
                events.append({
                    "event_id": event.id,
                    "name_ar": event.name_ar,
                    "name_en": event.name_en,
                    "description_ar": event.description_ar,
                    "description_en": event.description_en,
                    "story_id": story_id,
                    "story_title_ar": story.title_ar,
                    "category": story.category.value,
                    "sequence": event.sequence,
                    "verses": event.verses,
                    "significance_ar": event.significance_ar,
                    "significance_en": event.significance_en
                })

        # Sort by story then sequence
        events.sort(key=lambda x: (x["story_id"], x["sequence"]))

        return {
            "events": events[:limit],
            "total": len(events),
            "filters": {
                "category": category,
                "prophet": prophet
            }
        }

    # ========================================
    # PERSONALIZED USER JOURNEY & STUDY PROGRESS
    # ========================================

    def __init_user_storage(self):
        """Initialize user storage if not exists"""
        if not hasattr(self, '_user_journeys'):
            self._user_journeys: Dict[str, Dict[str, Any]] = {}
            self._user_progress: Dict[str, Dict[str, Any]] = {}

    def save_user_journey(
        self,
        user_id: str,
        current_story_id: str,
        themes_explored: List[str],
        time_spent_seconds: int = 0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save user's thematic journey through stories"""
        self.__init_user_storage()

        if user_id not in self._user_journeys:
            self._user_journeys[user_id] = {
                "user_id": user_id,
                "journey_history": [],
                "themes_explored": set(),
                "stories_visited": set(),
                "total_time_spent": 0,
                "created_at": datetime.now().isoformat()
            }

        journey = self._user_journeys[user_id]

        # Add journey entry
        entry = {
            "story_id": current_story_id,
            "story_title": self._stories.get(current_story_id, {}).title_ar if current_story_id in self._stories else current_story_id,
            "themes": themes_explored,
            "time_spent": time_spent_seconds,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        journey["journey_history"].append(entry)
        journey["themes_explored"].update(themes_explored)
        journey["stories_visited"].add(current_story_id)
        journey["total_time_spent"] += time_spent_seconds

        # Update progress
        self._update_user_progress(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "entry_added": entry,
            "total_stories_visited": len(journey["stories_visited"]),
            "total_themes_explored": len(journey["themes_explored"])
        }

    def _update_user_progress(self, user_id: str):
        """Update user progress statistics"""
        if user_id not in self._user_journeys:
            return

        journey = self._user_journeys[user_id]
        total_stories = len(self._stories)
        total_themes = len(self._themes)

        self._user_progress[user_id] = {
            "stories_completed": len(journey["stories_visited"]),
            "stories_total": total_stories,
            "stories_progress_percent": round(len(journey["stories_visited"]) / total_stories * 100, 1),
            "themes_explored": len(journey["themes_explored"]),
            "themes_total": total_themes,
            "themes_progress_percent": round(len(journey["themes_explored"]) / total_themes * 100, 1),
            "total_time_spent_minutes": journey["total_time_spent"] // 60,
            "milestones": self._calculate_milestones(user_id),
            "last_activity": journey["journey_history"][-1]["timestamp"] if journey["journey_history"] else None
        }

    def _calculate_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """Calculate achievement milestones for a user"""
        milestones = []
        journey = self._user_journeys.get(user_id, {})

        stories_visited = len(journey.get("stories_visited", set()))
        themes_explored = len(journey.get("themes_explored", set()))

        # Story milestones
        if stories_visited >= 1:
            milestones.append({"id": "first_story", "name_ar": "القصة الأولى", "name_en": "First Story", "achieved": True})
        if stories_visited >= 5:
            milestones.append({"id": "five_stories", "name_ar": "خمس قصص", "name_en": "Five Stories", "achieved": True})
        if stories_visited >= len(self._stories):
            milestones.append({"id": "all_stories", "name_ar": "جميع القصص", "name_en": "All Stories", "achieved": True})

        # Theme milestones
        if themes_explored >= 5:
            milestones.append({"id": "five_themes", "name_ar": "خمسة مواضيع", "name_en": "Five Themes", "achieved": True})
        if themes_explored >= len(self._themes):
            milestones.append({"id": "all_themes", "name_ar": "جميع المواضيع", "name_en": "All Themes", "achieved": True})

        # Prophet stories milestone
        prophet_stories_visited = sum(
            1 for sid in journey.get("stories_visited", set())
            if sid in self._stories and self._stories[sid].category == StoryCategory.PROPHETS
        )
        if prophet_stories_visited >= 5:
            milestones.append({"id": "prophet_explorer", "name_ar": "مستكشف الأنبياء", "name_en": "Prophet Explorer", "achieved": True})

        return milestones

    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's study progress and achievements"""
        self.__init_user_storage()

        if user_id not in self._user_progress:
            return {
                "user_id": user_id,
                "message": "No progress recorded yet",
                "progress": {
                    "stories_completed": 0,
                    "themes_explored": 0,
                    "milestones": []
                }
            }

        progress = self._user_progress[user_id]
        journey = self._user_journeys.get(user_id, {})

        # Get suggested next stories
        visited = journey.get("stories_visited", set())
        suggested = []
        for story_id, story in self._stories.items():
            if story_id not in visited:
                suggested.append({
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "category_ar": story.category_ar,
                    "relevance": "based on your interests"
                })
                if len(suggested) >= 3:
                    break

        return {
            "user_id": user_id,
            "progress": progress,
            "recent_activity": journey.get("journey_history", [])[-5:],
            "suggested_next": suggested
        }

    # ========================================
    # MULTILINGUAL SUPPORT & TAFSIR INTEGRATION
    # ========================================

    def get_available_languages(self) -> Dict[str, Any]:
        """Get available language support"""
        return {
            "languages": [
                {"code": "ar", "name": "العربية", "name_en": "Arabic", "is_primary": True},
                {"code": "en", "name": "English", "name_en": "English", "is_primary": True},
                {"code": "fr", "name": "Français", "name_en": "French", "is_primary": False, "status": "planned"},
                {"code": "ur", "name": "اردو", "name_en": "Urdu", "is_primary": False, "status": "planned"},
                {"code": "id", "name": "Indonesia", "name_en": "Indonesian", "is_primary": False, "status": "planned"}
            ],
            "default_language": "ar",
            "tafsir_languages": ["ar", "en"]
        }

    def get_story_with_tafsir(
        self,
        story_id: str,
        language: str = "ar",
        tafsir_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get story with integrated Tafsir explanations"""
        story = self._stories.get(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        # Get base story data
        story_data = self._story_to_dict(story)

        # Add Tafsir for each verse
        tafsir_explanations = []
        for verse in story.verses:
            tafsir_entry = {
                "verse_reference": f"{verse.surah}:{verse.ayah_start}-{verse.ayah_end}",
                "verse_text_ar": verse.text_ar,
                "verse_text_en": verse.text_en,
                "tafsir": []
            }

            # Add available Tafsir sources
            tafsir_sources = [
                {
                    "source": "Ibn Kathir",
                    "source_ar": "ابن كثير",
                    "madhab": "shafii",
                    "explanation_ar": f"تفسير ابن كثير لهذه الآية في سياق قصة {story.title_ar}",
                    "explanation_en": f"Ibn Kathir's interpretation of this verse in the context of {story.title_en}"
                },
                {
                    "source": "Al-Qurtubi",
                    "source_ar": "القرطبي",
                    "madhab": "maliki",
                    "explanation_ar": f"تفسير القرطبي مع الأحكام الفقهية المستنبطة",
                    "explanation_en": "Al-Qurtubi's interpretation with derived jurisprudential rulings"
                },
                {
                    "source": "Al-Saadi",
                    "source_ar": "السعدي",
                    "madhab": "hanbali",
                    "explanation_ar": "تيسير الكريم الرحمن في تفسير كلام المنان",
                    "explanation_en": "Al-Saadi's accessible interpretation"
                }
            ]

            if tafsir_source:
                tafsir_sources = [t for t in tafsir_sources if t["source"].lower() == tafsir_source.lower()]

            tafsir_entry["tafsir"] = tafsir_sources
            tafsir_explanations.append(tafsir_entry)

        story_data["tafsir_integration"] = {
            "available_sources": ["Ibn Kathir", "Al-Qurtubi", "Al-Saadi"],
            "verse_tafsir": tafsir_explanations
        }

        # Add language-specific content
        if language == "en":
            story_data["display_title"] = story.title_en
            story_data["display_summary"] = story.summary_en
        else:
            story_data["display_title"] = story.title_ar
            story_data["display_summary"] = story.summary_ar

        story_data["language"] = language

        return story_data

    # ========================================
    # AUTOMATED STORY RECOMMENDATIONS
    # ========================================

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
        current_story_id: Optional[str] = None,
        based_on: str = "themes",  # "themes", "category", "prophets", "mixed"
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get automated story recommendations"""
        self.__init_user_storage()

        recommendations = []
        visited_stories = set()

        # Get user's visited stories if user_id provided
        if user_id and user_id in self._user_journeys:
            visited_stories = self._user_journeys[user_id].get("stories_visited", set())

        # If current story provided, recommend based on it
        if current_story_id and current_story_id in self._stories:
            current_story = self._stories[current_story_id]

            if based_on in ["themes", "mixed"]:
                # Find stories with similar themes
                current_themes = set(t.value for t in current_story.themes)
                for story_id, story in self._stories.items():
                    if story_id == current_story_id or story_id in visited_stories:
                        continue
                    story_themes = set(t.value for t in story.themes)
                    shared = current_themes & story_themes
                    if shared:
                        recommendations.append({
                            "story_id": story_id,
                            "title_ar": story.title_ar,
                            "title_en": story.title_en,
                            "category_ar": story.category_ar,
                            "reason": "shared_themes",
                            "reason_ar": f"مواضيع مشتركة: {', '.join(shared)}",
                            "shared_themes": list(shared),
                            "score": len(shared)
                        })

            if based_on in ["category", "mixed"]:
                # Find stories in same category
                for story_id, story in self._stories.items():
                    if story_id == current_story_id or story_id in visited_stories:
                        continue
                    if story.category == current_story.category:
                        existing = next((r for r in recommendations if r["story_id"] == story_id), None)
                        if existing:
                            existing["score"] += 2
                            existing["reason"] = "mixed"
                        else:
                            recommendations.append({
                                "story_id": story_id,
                                "title_ar": story.title_ar,
                                "title_en": story.title_en,
                                "category_ar": story.category_ar,
                                "reason": "same_category",
                                "reason_ar": f"نفس التصنيف: {story.category_ar}",
                                "score": 2
                            })

            if based_on in ["prophets", "mixed"]:
                # Find stories with related prophets
                current_prophets = set(f.id for f in current_story.figures if f.is_prophet)
                for story_id, story in self._stories.items():
                    if story_id == current_story_id or story_id in visited_stories:
                        continue
                    story_prophets = set(f.id for f in story.figures if f.is_prophet)
                    shared = current_prophets & story_prophets
                    if shared:
                        prophet_names = [f.name_ar for f in story.figures if f.id in shared]
                        existing = next((r for r in recommendations if r["story_id"] == story_id), None)
                        if existing:
                            existing["score"] += 3
                            existing["reason"] = "mixed"
                        else:
                            recommendations.append({
                                "story_id": story_id,
                                "title_ar": story.title_ar,
                                "title_en": story.title_en,
                                "category_ar": story.category_ar,
                                "reason": "shared_prophet",
                                "reason_ar": f"نبي مشترك: {', '.join(prophet_names)}",
                                "score": 3
                            })

        # If no current story, recommend based on user history or popular stories
        else:
            # Get popular/unvisited stories
            for story_id, story in self._stories.items():
                if story_id in visited_stories:
                    continue
                recommendations.append({
                    "story_id": story_id,
                    "title_ar": story.title_ar,
                    "title_en": story.title_en,
                    "category_ar": story.category_ar,
                    "reason": "popular",
                    "reason_ar": "قصة موصى بها",
                    "score": story.completeness_score * 10
                })

        # Sort by score and limit
        recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "recommendations": recommendations[:limit],
            "total": len(recommendations),
            "based_on": based_on,
            "user_id": user_id,
            "current_story_id": current_story_id
        }

    # ========================================
    # DATA CACHING & PERFORMANCE OPTIMIZATION
    # ========================================

    def __init_cache(self):
        """Initialize cache storage if not exists"""
        if not hasattr(self, '_cache'):
            self._cache: Dict[str, Dict[str, Any]] = {}
            self._cache_timestamps: Dict[str, datetime] = {}
            self._cache_ttl_seconds = 300  # 5 minutes default TTL

    def get_cached_stories(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get cached story data for quicker access"""
        self.__init_cache()

        cache_key = "all_stories"

        # Check if cache is valid
        if not force_refresh and cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and (datetime.now() - cache_time).seconds < self._cache_ttl_seconds:
                return {
                    "data": self._cache[cache_key],
                    "from_cache": True,
                    "cached_at": cache_time.isoformat()
                }

        # Rebuild cache
        stories_data = []
        for story_id, story in self._stories.items():
            stories_data.append({
                "id": story_id,
                "title_ar": story.title_ar,
                "title_en": story.title_en,
                "category": story.category.value,
                "category_ar": story.category_ar,
                "themes": [t.value for t in story.themes],
                "themes_ar": story.themes_ar,
                "summary_ar": story.summary_ar[:200] + "..." if len(story.summary_ar) > 200 else story.summary_ar,
                "figure_count": len(story.figures),
                "event_count": len(story.events),
                "completeness_score": story.completeness_score
            })

        self._cache[cache_key] = stories_data
        self._cache_timestamps[cache_key] = datetime.now()

        return {
            "data": stories_data,
            "from_cache": False,
            "cached_at": self._cache_timestamps[cache_key].isoformat()
        }

    def clear_cache(self, cache_key: Optional[str] = None) -> Dict[str, Any]:
        """Clear cache data"""
        self.__init_cache()

        if cache_key:
            if cache_key in self._cache:
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
                return {"success": True, "cleared": cache_key}
            return {"success": False, "error": f"Cache key '{cache_key}' not found"}

        self._cache.clear()
        self._cache_timestamps.clear()
        return {"success": True, "cleared": "all"}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.__init_cache()

        stats = {
            "total_cached_items": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "ttl_seconds": self._cache_ttl_seconds,
            "cache_entries": []
        }

        for key, timestamp in self._cache_timestamps.items():
            age_seconds = (datetime.now() - timestamp).seconds
            stats["cache_entries"].append({
                "key": key,
                "cached_at": timestamp.isoformat(),
                "age_seconds": age_seconds,
                "is_valid": age_seconds < self._cache_ttl_seconds
            })

        return stats


# Create singleton instance
alatlas_service = AltlasService()
