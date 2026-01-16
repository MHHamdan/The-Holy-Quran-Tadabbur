"""
Advanced Similarity Search Service for Quranic Verses.

Provides multi-layered similarity analysis using:
1. Jaccard Similarity (word overlap)
2. Cosine Similarity (TF-IDF vectors)
3. Concept Overlap Score (shared thematic concepts)
4. Grammatical/Syntactic Similarity
5. Semantic Embedding Similarity

Arabic: خدمة البحث المتقدم عن التشابه في الآيات القرآنية
"""

import logging
import math
import re
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse
from app.services.quran_search import (
    normalize_arabic,
    extract_words,
    CONCEPT_EXPANSIONS,
    ARABIC_ROOTS,
    extract_root,
    get_words_by_root,
    THEME_KEYWORDS,
)
from app.services.quran_text_utils import (
    preprocess_for_similarity,
    is_bismillah_verse,
    is_first_verse_with_bismillah,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class ConnectionType(str, Enum):
    """Types of verse connections for visualization."""
    LEXICAL = "lexical"           # Direct word matches
    THEMATIC = "thematic"         # Shared themes
    CONCEPTUAL = "conceptual"     # Related concepts
    GRAMMATICAL = "grammatical"   # Similar sentence structure
    SEMANTIC = "semantic"         # Deep semantic similarity
    ROOT_BASED = "root_based"     # Shared Arabic roots
    NARRATIVE = "narrative"       # Story/narrative connection
    PROPHETIC = "prophetic"       # Prophet-related connection


class SentenceStructure(str, Enum):
    """Arabic sentence structure types."""
    VERBAL = "verbal"             # جملة فعلية
    NOMINAL = "nominal"           # جملة اسمية
    CONDITIONAL = "conditional"   # جملة شرطية
    INTERROGATIVE = "interrogative"  # جملة استفهامية
    IMPERATIVE = "imperative"     # جملة أمرية
    EXCLAMATORY = "exclamatory"   # جملة تعجبية
    OATH = "oath"                 # جملة قسم
    UNKNOWN = "unknown"


# Sentence structure indicators
SENTENCE_INDICATORS = {
    SentenceStructure.VERBAL: ["قال", "قالوا", "جاء", "ذهب", "فعل", "يفعل", "أنزل", "خلق", "جعل"],
    SentenceStructure.NOMINAL: ["إن", "أن", "هو", "هي", "هذا", "ذلك", "الذي", "التي"],
    SentenceStructure.CONDITIONAL: ["إن", "لو", "إذا", "لولا", "لئن", "من"],
    SentenceStructure.INTERROGATIVE: ["أ", "هل", "ما", "من", "كيف", "أين", "متى", "لماذا", "أي"],
    SentenceStructure.IMPERATIVE: ["اعبدوا", "اتقوا", "قل", "اذكر", "انظر", "اقرأ"],
    SentenceStructure.EXCLAMATORY: ["ما أفعل", "سبحان"],
    SentenceStructure.OATH: ["والله", "وربي", "والسماء", "والأرض", "والشمس", "والقمر", "والليل", "والنهار", "والفجر"],
}

# Theme labels in Arabic - Expanded categories
THEME_LABELS_AR = {
    # Core Theological Themes
    "tawheed": "التوحيد",
    "prophets": "الأنبياء",
    "afterlife": "الآخرة",
    "worship": "العبادات",
    "ethics": "الأخلاق",
    "law": "الأحكام",
    "history": "التاريخ",
    "nature": "الكون",
    "guidance": "الهداية",
    "community": "المجتمع",
    # Emotional & Spiritual Themes
    "patience": "الصبر",
    "gratitude": "الشكر",
    "trust": "التوكل",
    "trials": "الابتلاء",
    "grief": "الحزن",
    "hope": "الرجاء",
    "fear": "الخوف",
    "love": "المحبة",
    "repentance": "التوبة",
    "contentment": "الرضا",
    # Divine Attributes Themes
    "divine_mercy": "الرحمة الإلهية",
    "divine_justice": "العدل الإلهي",
    "divine_power": "القدرة الإلهية",
    "divine_wisdom": "الحكمة الإلهية",
    "divine_knowledge": "العلم الإلهي",
    "divine_forgiveness": "المغفرة",
    # Consequence Themes
    "punishment": "العقاب",
    "reward": "الثواب",
    "punishment_reward": "الجزاء",
    "hellfire": "النار",
    "paradise": "الجنة",
    # Social & Moral Themes
    "family": "الأسرة",
    "justice": "العدالة",
    "charity": "الصدقة",
    "honesty": "الصدق",
    "humility": "التواضع",
    "brotherhood": "الأخوة",
    # Narrative Themes
    "creation": "الخلق",
    "resurrection": "البعث",
    "covenant": "العهد",
    "salvation": "النجاة",
    "submission": "الإسلام",
}

# Theme colors for visualization - Expanded palette
THEME_COLORS = {
    # Core Theological
    "tawheed": "#4F46E5",      # Indigo
    "prophets": "#059669",     # Emerald
    "afterlife": "#7C3AED",    # Violet
    "worship": "#0891B2",      # Cyan
    "ethics": "#EA580C",       # Orange
    "law": "#DC2626",          # Red
    "history": "#CA8A04",      # Yellow
    "nature": "#16A34A",       # Green
    "guidance": "#2563EB",     # Blue
    "community": "#9333EA",    # Purple
    # Emotional & Spiritual
    "patience": "#14B8A6",     # Teal
    "gratitude": "#F59E0B",    # Amber
    "trust": "#6366F1",        # Indigo
    "trials": "#EF4444",       # Red
    "grief": "#64748B",        # Slate
    "hope": "#22C55E",         # Green
    "fear": "#78716C",         # Stone
    "love": "#EC4899",         # Pink
    "repentance": "#8B5CF6",   # Violet
    "contentment": "#06B6D4",  # Cyan
    # Divine Attributes
    "divine_mercy": "#10B981", # Emerald
    "divine_justice": "#F97316", # Orange
    "divine_power": "#3B82F6", # Blue
    "divine_wisdom": "#A855F7", # Purple
    "divine_knowledge": "#6366F1", # Indigo
    "divine_forgiveness": "#34D399", # Emerald light
    # Consequences
    "punishment": "#B91C1C",   # Red dark
    "reward": "#15803D",       # Green dark
    "punishment_reward": "#D97706", # Amber dark
    "hellfire": "#991B1B",     # Red darker
    "paradise": "#166534",     # Green darker
    # Social & Moral
    "family": "#F472B6",       # Pink
    "justice": "#FB923C",      # Orange
    "charity": "#4ADE80",      # Green
    "honesty": "#60A5FA",      # Blue
    "humility": "#C4B5FD",     # Violet light
    "brotherhood": "#A78BFA",  # Purple
    # Narrative
    "creation": "#0EA5E9",     # Sky
    "resurrection": "#8B5CF6", # Violet
    "covenant": "#F59E0B",     # Amber
    "salvation": "#22D3EE",    # Cyan
    "submission": "#4F46E5",   # Indigo
}

# Extended theme keywords for detection
EXTENDED_THEME_KEYWORDS = {
    "grief": ["حزن", "حزين", "أسى", "كرب", "هم", "غم", "بكى", "دمع", "ألم"],
    "hope": ["رجاء", "أمل", "طمع", "رجو", "يرجو", "أملوا"],
    "fear": ["خوف", "خشية", "رهبة", "فزع", "خائف", "يخاف", "اتقوا"],
    "love": ["حب", "محبة", "ود", "مودة", "يحب", "أحب", "حبيب"],
    "repentance": ["توبة", "تاب", "توبوا", "يتوب", "غفر", "استغفر"],
    "contentment": ["رضا", "رضي", "راض", "يرضى", "قناعة", "قانع"],
    "divine_mercy": ["رحمة", "رحيم", "رحمن", "يرحم", "رحمته", "أرحم"],
    "divine_justice": ["عدل", "قسط", "ميزان", "حساب", "عادل", "قاسط"],
    "divine_power": ["قدرة", "قدير", "قادر", "يقدر", "قوة", "عزة"],
    "divine_wisdom": ["حكمة", "حكيم", "أحكم", "حكم"],
    "divine_knowledge": ["علم", "عليم", "يعلم", "علام", "خبير"],
    "divine_forgiveness": ["غفر", "غفور", "مغفرة", "يغفر", "عفو", "يعفو"],
    "punishment": ["عذاب", "عقاب", "نكال", "عاقب", "أهلك", "دمر"],
    "reward": ["ثواب", "أجر", "جزاء", "نعيم", "فوز", "فلاح"],
    "punishment_reward": ["جزاء", "حساب", "ميزان", "كسب", "عمل"],
    "hellfire": ["نار", "جهنم", "سعير", "حريق", "لهب", "جحيم"],
    "paradise": ["جنة", "فردوس", "نعيم", "خلد", "رضوان", "روضة"],
    "family": ["أهل", "والد", "والدة", "أب", "أم", "ابن", "بنت", "زوج", "زوجة"],
    "justice": ["عدل", "قسط", "إنصاف", "حق", "ظلم"],
    "charity": ["صدقة", "زكاة", "إنفاق", "أنفق", "تصدق", "إحسان"],
    "honesty": ["صدق", "صادق", "أمانة", "أمين", "وفاء"],
    "humility": ["تواضع", "خشوع", "تذلل", "خضوع", "استكان"],
    "brotherhood": ["أخ", "إخوة", "أخوة", "مؤمن", "مسلم", "أمة"],
    "creation": ["خلق", "فطر", "برأ", "صور", "أنشأ", "كون"],
    "resurrection": ["بعث", "نشر", "أحيا", "قيامة", "حشر"],
    "covenant": ["عهد", "ميثاق", "وعد", "عاهد", "حفظ"],
    "salvation": ["نجاة", "نجى", "أنجى", "خلص", "فرج"],
    "submission": ["إسلام", "أسلم", "مسلم", "خضع", "انقاد"],
}

# =============================================================================
# CONTEXTUAL SIGNIFICANCE - Thematic Word Weights
# =============================================================================

# Words with high thematic significance (weighted more in similarity)
CONTEXTUAL_SIGNIFICANCE = {
    # Divine Names and Attributes (الأسماء والصفات) - Highest significance
    "الله": 3.0, "الرحمن": 2.8, "الرحيم": 2.8, "رب": 2.5, "إله": 3.0,
    "الملك": 2.5, "القدوس": 2.5, "السلام": 2.5, "العزيز": 2.5, "الحكيم": 2.5,
    "العليم": 2.5, "السميع": 2.5, "البصير": 2.5, "الغفور": 2.5, "الرزاق": 2.5,

    # Prophets (الأنبياء) - High significance
    "محمد": 2.8, "موسى": 2.8, "عيسى": 2.8, "إبراهيم": 2.8, "نوح": 2.8,
    "آدم": 2.8, "يوسف": 2.8, "داود": 2.5, "سليمان": 2.5, "يعقوب": 2.5,
    "إسماعيل": 2.5, "إسحاق": 2.5, "هارون": 2.5, "زكريا": 2.5, "يحيى": 2.5,
    "لوط": 2.5, "شعيب": 2.5, "صالح": 2.5, "هود": 2.5, "أيوب": 2.5,

    # Core Concepts (المفاهيم الأساسية)
    "إيمان": 2.5, "كفر": 2.5, "شرك": 2.5, "توحيد": 2.8, "عبادة": 2.5,
    "صلاة": 2.5, "زكاة": 2.5, "صوم": 2.5, "حج": 2.5, "جهاد": 2.5,
    "تقوى": 2.5, "صبر": 2.8, "شكر": 2.5, "توكل": 2.5, "رحمة": 2.5,

    # Afterlife (الآخرة)
    "جنة": 2.5, "نار": 2.5, "يوم القيامة": 2.8, "حساب": 2.5, "بعث": 2.5,
    "ميزان": 2.5, "صراط": 2.5, "عذاب": 2.5, "ثواب": 2.5, "خلود": 2.5,

    # Ethical Terms (الأخلاق)
    "عدل": 2.5, "ظلم": 2.5, "صدق": 2.5, "كذب": 2.5, "أمانة": 2.5,
    "خيانة": 2.5, "إحسان": 2.5, "بر": 2.5, "تواضع": 2.5, "كبر": 2.5,

    # Trials and Tests (الابتلاء والفتنة)
    "ابتلاء": 2.8, "فتنة": 2.8, "امتحان": 2.5, "محنة": 2.5, "بلاء": 2.5,
    "صعوبة": 2.0, "شدة": 2.0, "كرب": 2.0,

    # Guidance and Misguidance (الهداية والضلال)
    "هداية": 2.8, "ضلال": 2.8, "نور": 2.5, "ظلمات": 2.5, "حق": 2.5,
    "باطل": 2.5, "رشد": 2.5, "غي": 2.5,
}

# Prophet-related themes and their test types - Expanded
PROPHETIC_THEMES = {
    "موسى": {
        "trials": ["فرعون", "السحرة", "البحر", "التيه", "العجل", "قارون"],
        "themes": ["liberation", "divine_power", "faith_test", "community_leadership"],
        "related_prophets": ["هارون", "إبراهيم"],
        "suras": [2, 7, 10, 20, 26, 28],  # Main suras mentioning this prophet
        "moral_lessons": {
            "ar": ["الثقة بالله في الشدائد", "التوكل على الله", "الصبر على الأذى"],
            "en": ["Trust in Allah during hardship", "Reliance on Allah", "Patience against harm"],
        },
    },
    "إبراهيم": {
        "trials": ["النار", "الأصنام", "الذبيح", "هاجر", "البناء"],
        "themes": ["monotheism", "sacrifice", "faith_test", "submission"],
        "related_prophets": ["إسماعيل", "إسحاق", "لوط"],
        "suras": [2, 6, 14, 21, 37],
        "moral_lessons": {
            "ar": ["التوحيد الخالص", "التضحية في سبيل الله", "التسليم لأمر الله"],
            "en": ["Pure monotheism", "Sacrifice for Allah", "Submission to Allah's command"],
        },
    },
    "يوسف": {
        "trials": ["الإخوة", "البئر", "امرأة العزيز", "السجن", "الملك"],
        "themes": ["patience", "forgiveness", "divine_plan", "family"],
        "related_prophets": ["يعقوب"],
        "suras": [12],
        "moral_lessons": {
            "ar": ["الصبر على الابتلاء", "العفو عند المقدرة", "حسن التوكل"],
            "en": ["Patience in trials", "Forgiveness when able", "Beautiful reliance on Allah"],
        },
    },
    "نوح": {
        "trials": ["قومه", "الطوفان", "ابنه"],
        "themes": ["perseverance", "divine_warning", "salvation"],
        "related_prophets": [],
        "suras": [7, 11, 23, 26, 71],
        "moral_lessons": {
            "ar": ["الثبات على الدعوة", "الصبر على الإيذاء", "الإيمان بوعد الله"],
            "en": ["Steadfastness in calling to Allah", "Patience against harm", "Faith in Allah's promise"],
        },
    },
    "أيوب": {
        "trials": ["المرض", "الفقر", "الصبر"],
        "themes": ["patience", "gratitude", "divine_test"],
        "related_prophets": [],
        "suras": [21, 38],
        "moral_lessons": {
            "ar": ["الصبر الجميل", "الشكر في السراء والضراء", "اللجوء إلى الله"],
            "en": ["Beautiful patience", "Gratitude in ease and hardship", "Turning to Allah"],
        },
    },
    "محمد": {
        "trials": ["قريش", "الهجرة", "بدر", "أحد", "الطائف"],
        "themes": ["final_message", "persecution", "migration", "community_building"],
        "related_prophets": ["إبراهيم", "موسى", "عيسى"],
        "suras": [3, 8, 9, 33, 47, 48],
        "moral_lessons": {
            "ar": ["الصبر على الدعوة", "بناء المجتمع الإسلامي", "الرحمة والعدل"],
            "en": ["Patience in calling to Islam", "Building Islamic community", "Mercy and justice"],
        },
    },
    "عيسى": {
        "trials": ["الميلاد", "التكذيب", "محاولة القتل"],
        "themes": ["miraculous_birth", "divine_word", "patience"],
        "related_prophets": ["مريم", "زكريا", "يحيى"],
        "suras": [3, 5, 19],
        "moral_lessons": {
            "ar": ["التوحيد الخالص", "العبودية لله", "الصبر على الأذى"],
            "en": ["Pure monotheism", "Servitude to Allah", "Patience against harm"],
        },
    },
    "سليمان": {
        "trials": ["الملك", "الجن", "بلقيس", "الفتنة"],
        "themes": ["wisdom", "gratitude", "divine_power", "justice"],
        "related_prophets": ["داود"],
        "suras": [21, 27, 34, 38],
        "moral_lessons": {
            "ar": ["شكر النعم", "العدل في الحكم", "استخدام النعم في طاعة الله"],
            "en": ["Gratitude for blessings", "Justice in ruling", "Using blessings in Allah's obedience"],
        },
    },
    "داود": {
        "trials": ["جالوت", "الحكم بين الناس"],
        "themes": ["courage", "repentance", "worship", "justice"],
        "related_prophets": ["سليمان"],
        "suras": [2, 21, 34, 38],
        "moral_lessons": {
            "ar": ["الشجاعة في الحق", "سرعة التوبة", "كثرة العبادة"],
            "en": ["Courage for truth", "Quick repentance", "Abundant worship"],
        },
    },
    "يونس": {
        "trials": ["قومه", "الحوت", "اليأس"],
        "themes": ["repentance", "divine_mercy", "patience"],
        "related_prophets": [],
        "suras": [10, 21, 37, 68],
        "moral_lessons": {
            "ar": ["عدم اليأس من رحمة الله", "التوبة والإنابة", "الصبر على القضاء"],
            "en": ["Never despair of Allah's mercy", "Repentance and returning", "Patience with decree"],
        },
    },
    "لوط": {
        "trials": ["قومه", "الفاحشة", "العذاب"],
        "themes": ["moral_stand", "divine_punishment", "patience"],
        "related_prophets": ["إبراهيم"],
        "suras": [7, 11, 15, 26, 27, 29],
        "moral_lessons": {
            "ar": ["الأمر بالمعروف", "النهي عن الفحشاء", "الصبر على الأذى"],
            "en": ["Enjoining good", "Forbidding indecency", "Patience against harm"],
        },
    },
    "شعيب": {
        "trials": ["قومه", "الغش في الميزان"],
        "themes": ["economic_justice", "honesty", "divine_warning"],
        "related_prophets": [],
        "suras": [7, 11, 26, 29],
        "moral_lessons": {
            "ar": ["الأمانة في المعاملات", "العدل في الميزان", "الصدق في البيع"],
            "en": ["Honesty in dealings", "Justice in measures", "Truthfulness in trade"],
        },
    },
    "هود": {
        "trials": ["قوم عاد", "الاستكبار"],
        "themes": ["monotheism", "divine_warning", "patience"],
        "related_prophets": [],
        "suras": [7, 11, 26, 46],
        "moral_lessons": {
            "ar": ["التوحيد ونبذ الشرك", "الصبر على تكذيب القوم", "الثقة بنصر الله"],
            "en": ["Monotheism and rejecting polytheism", "Patience with denial", "Trust in Allah's victory"],
        },
    },
    "صالح": {
        "trials": ["ثمود", "الناقة"],
        "themes": ["miracle", "divine_warning", "patience"],
        "related_prophets": [],
        "suras": [7, 11, 26, 27],
        "moral_lessons": {
            "ar": ["الاستجابة لآيات الله", "عدم الطغيان", "الحذر من عاقبة المكذبين"],
            "en": ["Responding to Allah's signs", "Avoiding transgression", "Warning of deniers' fate"],
        },
    },
}

# Cross-story thematic connections - Expanded
CROSS_STORY_THEMES = {
    # Trials and Tests
    "divine_tests": {
        "ar": "الابتلاءات الإلهية",
        "en": "Divine Tests",
        "keywords": ["ابتلاء", "امتحان", "فتنة", "صبر", "بلاء"],
        "stories": ["يوسف", "أيوب", "إبراهيم", "موسى"],
        "description_ar": "قصص الأنبياء الذين ابتلاهم الله وصبروا",
        "description_en": "Stories of prophets tested by Allah who remained patient",
    },
    "community_opposition": {
        "ar": "معارضة القوم",
        "en": "Community Opposition",
        "keywords": ["كذبوا", "قوم", "كفر", "عصى", "استكبر"],
        "stories": ["نوح", "هود", "صالح", "شعيب", "لوط", "موسى"],
        "description_ar": "قصص الأنبياء الذين واجهوا تكذيب أقوامهم",
        "description_en": "Stories of prophets facing denial from their people",
    },
    "divine_rescue": {
        "ar": "النجاة الإلهية",
        "en": "Divine Rescue",
        "keywords": ["أنجى", "نجا", "خلص", "فرج", "كشف"],
        "stories": ["يونس", "موسى", "إبراهيم", "نوح", "لوط"],
        "description_ar": "قصص النجاة بتدخل إلهي",
        "description_en": "Stories of rescue through divine intervention",
    },
    "sacrifice_submission": {
        "ar": "التضحية والتسليم",
        "en": "Sacrifice and Submission",
        "keywords": ["ذبح", "فدى", "أسلم", "استسلم", "قرب"],
        "stories": ["إبراهيم", "إسماعيل"],
        "description_ar": "قصص التضحية والتسليم لأمر الله",
        "description_en": "Stories of sacrifice and submission to Allah's command",
    },
    "family_trials": {
        "ar": "ابتلاءات الأسرة",
        "en": "Family Trials",
        "keywords": ["أب", "ابن", "أخ", "أهل", "والد"],
        "stories": ["يعقوب", "يوسف", "نوح", "لوط", "إبراهيم"],
        "description_ar": "قصص الابتلاء في العلاقات الأسرية",
        "description_en": "Stories of trials in family relationships",
    },
    "patience_reward": {
        "ar": "الصبر والجزاء",
        "en": "Patience and Reward",
        "keywords": ["صبر", "جزاء", "أجر", "ثواب", "فوز"],
        "stories": ["يوسف", "أيوب", "موسى"],
        "description_ar": "قصص الصبر وحسن العاقبة",
        "description_en": "Stories of patience and good outcome",
    },
    # Divine Mercy and Forgiveness
    "divine_mercy_stories": {
        "ar": "رحمة الله بعباده",
        "en": "Divine Mercy to Servants",
        "keywords": ["رحمة", "رحم", "غفر", "تاب", "عفو"],
        "stories": ["آدم", "يونس", "داود", "موسى"],
        "description_ar": "قصص رحمة الله بالأنبياء والمؤمنين",
        "description_en": "Stories of Allah's mercy to prophets and believers",
    },
    "repentance_acceptance": {
        "ar": "التوبة والقبول",
        "en": "Repentance and Acceptance",
        "keywords": ["تاب", "توبة", "غفر", "أناب", "رجع"],
        "stories": ["آدم", "داود", "يونس"],
        "description_ar": "قصص التوبة وقبول الله لها",
        "description_en": "Stories of repentance and Allah's acceptance",
    },
    # Punishment and Consequences
    "divine_punishment": {
        "ar": "العقوبات الإلهية",
        "en": "Divine Punishments",
        "keywords": ["عذاب", "أهلك", "دمر", "عاقب", "نكال"],
        "stories": ["نوح", "لوط", "هود", "صالح", "شعيب", "فرعون"],
        "description_ar": "قصص العذاب الذي حل بالمكذبين",
        "description_en": "Stories of punishment that befell the deniers",
    },
    "destroyed_nations": {
        "ar": "الأمم المهلكة",
        "en": "Destroyed Nations",
        "keywords": ["أهلكنا", "دمرنا", "قرون", "عاد", "ثمود"],
        "stories": ["نوح", "عاد", "ثمود", "لوط", "فرعون"],
        "description_ar": "قصص الأمم التي أهلكها الله",
        "description_en": "Stories of nations destroyed by Allah",
    },
    # Leadership and Guidance
    "prophetic_leadership": {
        "ar": "القيادة النبوية",
        "en": "Prophetic Leadership",
        "keywords": ["قاد", "أمر", "نهى", "دعا", "هدى"],
        "stories": ["موسى", "محمد", "داود", "سليمان"],
        "description_ar": "قصص قيادة الأنبياء لأقوامهم",
        "description_en": "Stories of prophets leading their people",
    },
    "wisdom_judgment": {
        "ar": "الحكمة والحكم",
        "en": "Wisdom and Judgment",
        "keywords": ["حكم", "حكمة", "فصل", "قضى", "عدل"],
        "stories": ["داود", "سليمان", "يوسف", "موسى"],
        "description_ar": "قصص الحكمة في القضاء والحكم",
        "description_en": "Stories of wisdom in judgment and ruling",
    },
    # Miracles and Signs
    "divine_miracles": {
        "ar": "المعجزات الإلهية",
        "en": "Divine Miracles",
        "keywords": ["آية", "معجزة", "برهان", "سلطان", "بينة"],
        "stories": ["موسى", "عيسى", "إبراهيم", "صالح", "سليمان"],
        "description_ar": "قصص المعجزات التي أيد الله بها أنبياءه",
        "description_en": "Stories of miracles Allah gave to His prophets",
    },
    # Trust and Reliance
    "trust_in_allah": {
        "ar": "التوكل على الله",
        "en": "Trust in Allah",
        "keywords": ["توكل", "وكيل", "كفى", "حسب", "اعتمد"],
        "stories": ["إبراهيم", "موسى", "محمد", "يعقوب"],
        "description_ar": "قصص التوكل على الله في الشدائد",
        "description_en": "Stories of relying on Allah in hardships",
    },
    # Gratitude and Blessings
    "gratitude_blessings": {
        "ar": "الشكر والنعم",
        "en": "Gratitude and Blessings",
        "keywords": ["شكر", "نعمة", "فضل", "أنعم", "آتى"],
        "stories": ["سليمان", "داود", "إبراهيم", "موسى"],
        "description_ar": "قصص شكر النعم وفضل الله",
        "description_en": "Stories of gratitude for Allah's blessings",
    },
    # Women in Prophetic Stories
    "women_faith": {
        "ar": "النساء في قصص الأنبياء",
        "en": "Women in Prophetic Stories",
        "keywords": ["مريم", "آسية", "هاجر", "سارة", "امرأة"],
        "stories": ["عيسى", "موسى", "إبراهيم", "يوسف"],
        "description_ar": "قصص النساء الصالحات في تاريخ الأنبياء",
        "description_en": "Stories of righteous women in prophetic history",
    },
    # Spiritual Transformation
    "spiritual_journey": {
        "ar": "الرحلة الروحية",
        "en": "Spiritual Journey",
        "keywords": ["اهتدى", "آمن", "أسلم", "تاب", "أناب"],
        "stories": ["إبراهيم", "موسى", "محمد"],
        "description_ar": "قصص التحول الروحي والإيمان",
        "description_en": "Stories of spiritual transformation and faith",
    },
}

# Theme categories for organization
THEME_CATEGORIES = {
    "theological": {
        "ar": "عقائدية",
        "en": "Theological",
        "themes": ["tawheed", "afterlife", "divine_mercy", "divine_justice", "divine_power"],
    },
    "emotional": {
        "ar": "روحية وعاطفية",
        "en": "Emotional & Spiritual",
        "themes": ["patience", "gratitude", "trust", "grief", "hope", "fear", "love", "repentance"],
    },
    "moral": {
        "ar": "أخلاقية",
        "en": "Moral",
        "themes": ["ethics", "honesty", "justice", "charity", "humility", "brotherhood"],
    },
    "narrative": {
        "ar": "قصصية",
        "en": "Narrative",
        "themes": ["prophets", "history", "creation", "resurrection", "salvation"],
    },
    "consequence": {
        "ar": "الجزاء",
        "en": "Consequences",
        "themes": ["punishment", "reward", "punishment_reward", "hellfire", "paradise"],
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SimilarityScores:
    """Detailed breakdown of similarity scores."""
    jaccard: float = 0.0              # Word overlap (0-1)
    cosine: float = 0.0               # TF-IDF cosine (0-1)
    concept_overlap: float = 0.0      # Shared concepts (0-1)
    grammatical: float = 0.0          # Sentence structure (0-1)
    semantic: float = 0.0             # Embedding similarity (0-1)
    root_based: float = 0.0           # Shared roots (0-1)
    contextual_jaccard: float = 0.0   # Weighted Jaccard with significance
    contextual_cosine: float = 0.0    # Weighted Cosine with significance
    prophetic: float = 0.0            # Prophetic theme similarity
    narrative: float = 0.0            # Narrative arc similarity
    combined: float = 0.0             # Weighted combined score


@dataclass
class AdvancedSimilarityMatch:
    """A verse match with detailed similarity analysis."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    text_imlaei: str
    reference: str

    # Similarity scores
    scores: SimilarityScores

    # Connection analysis
    connection_type: ConnectionType
    connection_strength: str  # "strong", "moderate", "weak"

    # Shared elements
    shared_words: List[str] = field(default_factory=list)
    shared_roots: List[str] = field(default_factory=list)
    shared_concepts: List[str] = field(default_factory=list)
    shared_themes: List[str] = field(default_factory=list)

    # Theme info for visualization
    primary_theme: str = ""
    primary_theme_ar: str = ""
    theme_color: str = "#6B7280"  # Default gray

    # Grammatical analysis
    sentence_structure: str = ""
    sentence_structure_ar: str = ""

    # Prophetic/narrative connections
    shared_prophets: List[str] = field(default_factory=list)
    cross_story_theme: str = ""
    cross_story_theme_ar: str = ""
    narrative_position: str = ""  # "beginning", "middle", "end"

    # Tafsir link (for integration)
    tafsir_available: bool = False

    # User feedback
    relevance_score: Optional[float] = None  # From user feedback

    # Explanation
    similarity_explanation_ar: str = ""
    similarity_explanation_en: str = ""


@dataclass
class SimilaritySearchResult:
    """Complete result of a similarity search."""
    source_verse: Dict[str, Any]
    source_themes: List[str]
    source_structure: str
    total_similar: int
    matches: List[AdvancedSimilarityMatch]
    theme_distribution: Dict[str, int]
    connection_type_distribution: Dict[str, int]
    search_time_ms: float


# =============================================================================
# SIMILARITY ALGORITHMS
# =============================================================================

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets of words.

    Jaccard = |A ∩ B| / |A ∪ B|

    Returns value between 0 (no overlap) and 1 (identical).
    """
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Compute cosine similarity between two TF-IDF vectors.

    Cosine = (A · B) / (||A|| × ||B||)

    Returns value between 0 and 1.
    """
    if not vec1 or not vec2:
        return 0.0

    # Get all terms
    all_terms = set(vec1.keys()) | set(vec2.keys())

    # Compute dot product
    dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)

    # Compute magnitudes
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def concept_overlap_score(concepts1: Set[str], concepts2: Set[str]) -> float:
    """
    Compute concept overlap score between two sets of concepts.

    Uses Dice coefficient for better handling of different sizes:
    Dice = 2 × |A ∩ B| / (|A| + |B|)
    """
    if not concepts1 or not concepts2:
        return 0.0

    intersection = len(concepts1 & concepts2)

    return (2 * intersection) / (len(concepts1) + len(concepts2))


def root_similarity_score(roots1: Set[str], roots2: Set[str]) -> float:
    """
    Compute similarity based on shared Arabic roots.

    Roots indicate deep linguistic connection.
    """
    if not roots1 or not roots2:
        return 0.0

    shared = len(roots1 & roots2)
    total = len(roots1 | roots2)

    # Weight shared roots more heavily (roots are significant)
    return (shared * 1.5) / total if total > 0 else 0.0


def grammatical_similarity(struct1: SentenceStructure, struct2: SentenceStructure) -> float:
    """
    Compute grammatical similarity based on sentence structure.
    """
    if struct1 == struct2:
        return 1.0

    # Group similar structures
    groups = [
        {SentenceStructure.VERBAL, SentenceStructure.IMPERATIVE},  # Action-oriented
        {SentenceStructure.NOMINAL, SentenceStructure.EXCLAMATORY},  # Descriptive
        {SentenceStructure.CONDITIONAL, SentenceStructure.INTERROGATIVE},  # Questioning/conditional
    ]

    for group in groups:
        if struct1 in group and struct2 in group:
            return 0.7  # Similar category

    return 0.3  # Different categories


def contextual_weighted_jaccard(
    words1: Set[str],
    words2: Set[str],
    significance_weights: Dict[str, float] = None
) -> float:
    """
    Enhanced Jaccard similarity with contextual significance weighting.

    Words with higher thematic significance contribute more to similarity.

    Arabic: تشابه جاكارد المعزز مع ترجيح الأهمية السياقية
    """
    if not words1 or not words2:
        return 0.0

    if significance_weights is None:
        significance_weights = CONTEXTUAL_SIGNIFICANCE

    # Compute weighted intersection
    intersection = words1 & words2
    weighted_intersection = sum(
        significance_weights.get(normalize_arabic(w), 1.0)
        for w in intersection
    )

    # Compute weighted union
    union = words1 | words2
    weighted_union = sum(
        significance_weights.get(normalize_arabic(w), 1.0)
        for w in union
    )

    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0


def contextual_cosine_similarity(
    vec1: Dict[str, float],
    vec2: Dict[str, float],
    significance_weights: Dict[str, float] = None
) -> float:
    """
    Enhanced cosine similarity with contextual significance weighting.

    TF-IDF values are boosted for thematically significant words.

    Arabic: تشابه الجيب التمام المعزز مع ترجيح الأهمية السياقية
    """
    if not vec1 or not vec2:
        return 0.0

    if significance_weights is None:
        significance_weights = CONTEXTUAL_SIGNIFICANCE

    all_terms = set(vec1.keys()) | set(vec2.keys())

    # Apply contextual weights to TF-IDF values
    def weighted_value(term: str, tfidf: float) -> float:
        weight = significance_weights.get(normalize_arabic(term), 1.0)
        return tfidf * weight

    # Compute weighted dot product
    dot_product = sum(
        weighted_value(term, vec1.get(term, 0)) *
        weighted_value(term, vec2.get(term, 0))
        for term in all_terms
    )

    # Compute weighted magnitudes
    mag1 = math.sqrt(sum(weighted_value(t, v) ** 2 for t, v in vec1.items()))
    mag2 = math.sqrt(sum(weighted_value(t, v) ** 2 for t, v in vec2.items()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def prophetic_theme_similarity(text1: str, text2: str) -> Tuple[float, List[str], str]:
    """
    Compute similarity based on prophetic themes and trials.

    Returns:
        - Similarity score (0-1)
        - List of shared prophetic themes
        - Primary connection type (e.g., "divine_tests", "community_opposition")

    Arabic: تشابه المواضيع النبوية
    """
    normalized1 = normalize_arabic(text1)
    normalized2 = normalize_arabic(text2)

    # Find prophets mentioned in each text
    prophets1 = set()
    prophets2 = set()

    for prophet in PROPHETIC_THEMES.keys():
        prophet_norm = normalize_arabic(prophet)
        if prophet_norm in normalized1:
            prophets1.add(prophet)
        if prophet_norm in normalized2:
            prophets2.add(prophet)

    # Find cross-story themes
    themes1 = set()
    themes2 = set()

    for theme_id, theme_data in CROSS_STORY_THEMES.items():
        for keyword in theme_data["keywords"]:
            keyword_norm = normalize_arabic(keyword)
            if keyword_norm in normalized1:
                themes1.add(theme_id)
            if keyword_norm in normalized2:
                themes2.add(theme_id)

    # Compute prophetic connection
    shared_prophets = prophets1 & prophets2
    related_prophets = set()

    # Check for related prophets (e.g., Ibrahim-Ismail, Musa-Harun)
    for p1 in prophets1:
        if p1 in PROPHETIC_THEMES:
            related = set(PROPHETIC_THEMES[p1]["related_prophets"])
            related_prophets.update(related & prophets2)

    # Compute theme connection
    shared_themes = themes1 & themes2

    # Calculate score
    score = 0.0
    if shared_prophets:
        score += 0.4 * len(shared_prophets) / max(len(prophets1 | prophets2), 1)
    if related_prophets:
        score += 0.2 * len(related_prophets) / max(len(prophets1 | prophets2), 1)
    if shared_themes:
        score += 0.4 * len(shared_themes) / max(len(themes1 | themes2), 1)

    # Determine primary theme
    primary_theme = ""
    if shared_themes:
        primary_theme = list(shared_themes)[0]

    # Combine shared elements
    shared_elements = list(shared_prophets) + list(shared_themes)

    return min(score, 1.0), shared_elements, primary_theme


def narrative_arc_similarity(
    text1: str,
    text2: str,
    sura1: int,
    sura2: int,
    aya1: int,
    aya2: int
) -> float:
    """
    Compute narrative arc similarity considering verse position and story flow.

    Verses that appear in similar narrative positions (beginning, middle, end of story)
    or in suras known for related content receive higher scores.

    Arabic: تشابه القوس السردي
    """
    # Story-focused suras and their themes
    STORY_SURAS = {
        12: "يوسف",      # Sura Yusuf - complete story
        18: "الكهف",     # Sura Al-Kahf - stories
        19: "مريم",      # Sura Maryam - stories
        21: "الأنبياء",   # Sura Al-Anbiya - prophets
        26: "الشعراء",   # Sura Ash-Shuara - stories
        27: "النمل",     # Sura An-Naml - stories
        28: "القصص",    # Sura Al-Qasas - stories
        37: "الصافات",   # Stories of prophets
    }

    score = 0.0

    # Check if both verses are from story-focused suras
    if sura1 in STORY_SURAS and sura2 in STORY_SURAS:
        score += 0.3

    # Check if same sura (contextually connected)
    if sura1 == sura2:
        # Verses close together are more narratively connected
        distance = abs(aya1 - aya2)
        if distance <= 5:
            score += 0.4
        elif distance <= 15:
            score += 0.2
        elif distance <= 30:
            score += 0.1

    # Add thematic connection from text analysis
    normalized1 = normalize_arabic(text1)
    normalized2 = normalize_arabic(text2)

    # Narrative markers
    NARRATIVE_MARKERS = {
        "beginning": ["إذ", "واذكر", "فلما", "قال", "وقال"],
        "continuation": ["ثم", "فـ", "و"],
        "conclusion": ["فذلك", "كذلك", "فانظر", "إن في ذلك"],
    }

    markers1 = set()
    markers2 = set()

    for marker_type, markers in NARRATIVE_MARKERS.items():
        for marker in markers:
            if normalize_arabic(marker) in normalized1[:50]:
                markers1.add(marker_type)
            if normalize_arabic(marker) in normalized2[:50]:
                markers2.add(marker_type)

    if markers1 & markers2:
        score += 0.2

    return min(score, 1.0)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def detect_sentence_structure(text: str) -> SentenceStructure:
    """
    Detect the sentence structure type of Arabic text.

    Arabic: تحديد نوع الجملة (فعلية، اسمية، شرطية، إلخ)
    """
    normalized = normalize_arabic(text)
    words = normalized.split()[:5]  # Check first 5 words

    if not words:
        return SentenceStructure.UNKNOWN

    first_word = words[0] if words else ""

    # Check for oath (قسم)
    for indicator in SENTENCE_INDICATORS[SentenceStructure.OATH]:
        if normalized.startswith(normalize_arabic(indicator)):
            return SentenceStructure.OATH

    # Check for interrogative
    if first_word in [normalize_arabic(i) for i in SENTENCE_INDICATORS[SentenceStructure.INTERROGATIVE]]:
        return SentenceStructure.INTERROGATIVE

    # Check for conditional
    for indicator in SENTENCE_INDICATORS[SentenceStructure.CONDITIONAL]:
        if first_word == normalize_arabic(indicator):
            return SentenceStructure.CONDITIONAL

    # Check for imperative (command verbs)
    for indicator in SENTENCE_INDICATORS[SentenceStructure.IMPERATIVE]:
        if normalize_arabic(indicator) in normalized[:50]:
            return SentenceStructure.IMPERATIVE

    # Check for verbal (starts with verb patterns)
    verb_patterns = ["ف", "ي", "ت", "ن", "ا"]  # Common verb prefixes
    if any(first_word.startswith(p) for p in verb_patterns) and len(first_word) > 2:
        for verb in SENTENCE_INDICATORS[SentenceStructure.VERBAL]:
            if normalize_arabic(verb) in normalized:
                return SentenceStructure.VERBAL

    # Check for nominal (starts with noun/particle)
    for indicator in SENTENCE_INDICATORS[SentenceStructure.NOMINAL]:
        if first_word == normalize_arabic(indicator) or normalized.startswith(normalize_arabic(indicator)):
            return SentenceStructure.NOMINAL

    return SentenceStructure.UNKNOWN


def get_sentence_structure_ar(struct: SentenceStructure) -> str:
    """Get Arabic label for sentence structure."""
    labels = {
        SentenceStructure.VERBAL: "جملة فعلية",
        SentenceStructure.NOMINAL: "جملة اسمية",
        SentenceStructure.CONDITIONAL: "جملة شرطية",
        SentenceStructure.INTERROGATIVE: "جملة استفهامية",
        SentenceStructure.IMPERATIVE: "جملة أمرية",
        SentenceStructure.EXCLAMATORY: "جملة تعجبية",
        SentenceStructure.OATH: "جملة قسم",
        SentenceStructure.UNKNOWN: "غير محدد",
    }
    return labels.get(struct, "غير محدد")


def detect_themes(text: str, include_extended: bool = True) -> List[str]:
    """
    Detect themes in text using both base and extended keywords.

    Args:
        text: Arabic text to analyze
        include_extended: If True, also check extended theme keywords

    Returns:
        List of detected theme IDs
    """
    normalized = normalize_arabic(text)
    detected = set()

    # Check base theme keywords
    for theme_id, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if normalize_arabic(keyword) in normalized:
                detected.add(theme_id)
                break

    # Check extended theme keywords
    if include_extended:
        for theme_id, keywords in EXTENDED_THEME_KEYWORDS.items():
            for keyword in keywords:
                if normalize_arabic(keyword) in normalized:
                    detected.add(theme_id)
                    break

    return list(detected)


def detect_themes_with_scores(text: str) -> Dict[str, float]:
    """
    Detect themes in text with relevance scores.

    Returns a dictionary of theme_id -> score (0-1) based on
    how many keywords from each theme are found.

    Arabic: كشف المواضيع مع درجات الصلة
    """
    normalized = normalize_arabic(text)
    theme_scores = {}

    # Combine all theme keywords
    all_keywords = {**THEME_KEYWORDS}
    for theme_id, keywords in EXTENDED_THEME_KEYWORDS.items():
        if theme_id not in all_keywords:
            all_keywords[theme_id] = keywords
        else:
            all_keywords[theme_id] = list(set(all_keywords[theme_id] + keywords))

    for theme_id, keywords in all_keywords.items():
        matches = 0
        for keyword in keywords:
            if normalize_arabic(keyword) in normalized:
                matches += 1

        if matches > 0:
            # Score based on proportion of keywords matched
            score = min(1.0, matches / max(len(keywords) * 0.3, 1))
            theme_scores[theme_id] = round(score, 3)

    return theme_scores


def get_theme_moral_lessons(theme_id: str, prophet: str = None) -> Dict[str, List[str]]:
    """
    Get moral lessons associated with a theme or prophet.

    Args:
        theme_id: Theme identifier
        prophet: Optional prophet name to get specific lessons

    Returns:
        Dictionary with 'ar' and 'en' lists of moral lessons
    """
    lessons = {"ar": [], "en": []}

    # Get from prophet data if specified
    if prophet and prophet in PROPHETIC_THEMES:
        prophet_data = PROPHETIC_THEMES[prophet]
        if "moral_lessons" in prophet_data:
            lessons = prophet_data["moral_lessons"]

    # Get from cross-story themes
    if theme_id in CROSS_STORY_THEMES:
        theme_data = CROSS_STORY_THEMES[theme_id]
        if "description_ar" in theme_data:
            lessons["ar"].append(theme_data["description_ar"])
        if "description_en" in theme_data:
            lessons["en"].append(theme_data["description_en"])

    return lessons


def extract_roots_from_text(text: str) -> Set[str]:
    """Extract all Arabic roots from text."""
    words = extract_words(text)
    roots = set()

    for word in words:
        root = extract_root(word)
        if root:
            roots.add(root)

    return roots


def compute_tf_vector(text: str) -> Dict[str, float]:
    """Compute term frequency vector for text."""
    words = extract_words(text)
    if not words:
        return {}

    tf = Counter(words)
    total = len(words)

    return {word: count / total for word, count in tf.items()}


def get_connection_strength(score: float) -> str:
    """Classify connection strength from combined score."""
    if score >= 0.7:
        return "strong"
    elif score >= 0.4:
        return "moderate"
    else:
        return "weak"


def determine_connection_type(scores: SimilarityScores) -> ConnectionType:
    """Determine primary connection type based on scores."""
    score_types = [
        (scores.semantic, ConnectionType.SEMANTIC),
        (scores.concept_overlap, ConnectionType.CONCEPTUAL),
        (scores.root_based, ConnectionType.ROOT_BASED),
        (scores.grammatical, ConnectionType.GRAMMATICAL),
        (scores.contextual_jaccard, ConnectionType.LEXICAL),
        (scores.prophetic, ConnectionType.PROPHETIC),
        (scores.narrative, ConnectionType.NARRATIVE),
    ]

    # Get the highest scoring type
    max_score, max_type = max(score_types, key=lambda x: x[0])

    # If prophetic score is significant, prioritize it
    if scores.prophetic > 0.4:
        return ConnectionType.PROPHETIC

    # If narrative score is significant, use narrative
    if scores.narrative > 0.5:
        return ConnectionType.NARRATIVE

    # If thematic overlap is significant, use thematic
    if scores.concept_overlap > 0.5:
        return ConnectionType.THEMATIC

    return max_type


def generate_explanation(
    shared_words: List[str],
    shared_roots: List[str],
    shared_themes: List[str],
    connection_type: ConnectionType,
    language: str = "ar"
) -> str:
    """Generate human-readable explanation of similarity."""
    if language == "ar":
        parts = []

        if shared_words:
            words_str = "، ".join(shared_words[:3])
            parts.append(f"كلمات مشتركة: {words_str}")

        if shared_roots:
            roots_str = "، ".join(shared_roots[:3])
            parts.append(f"جذور مشتركة: {roots_str}")

        if shared_themes:
            themes_str = "، ".join([THEME_LABELS_AR.get(t, t) for t in shared_themes[:3]])
            parts.append(f"مواضيع مشتركة: {themes_str}")

        if not parts:
            return "تشابه في المعنى العام"

        return " | ".join(parts)
    else:
        parts = []

        if shared_words:
            words_str = ", ".join(shared_words[:3])
            parts.append(f"Shared words: {words_str}")

        if shared_roots:
            roots_str = ", ".join(shared_roots[:3])
            parts.append(f"Shared roots: {roots_str}")

        if shared_themes:
            themes_str = ", ".join(shared_themes[:3])
            parts.append(f"Shared themes: {themes_str}")

        if not parts:
            return "General semantic similarity"

        return " | ".join(parts)


# =============================================================================
# ADVANCED SIMILARITY SERVICE
# =============================================================================

class AdvancedSimilarityService:
    """
    Advanced similarity search service with multi-layered scoring.

    Features:
    - Multiple similarity algorithms (Jaccard, Cosine, Concept Overlap)
    - Contextual significance weighting for thematic words
    - Prophetic theme and cross-story connections
    - Grammatical structure analysis
    - Root-based morphological connections
    - Narrative arc analysis
    - Theme-aware matching
    - Visual connection type classification
    """

    # Weights for combined score (enhanced with contextual metrics)
    WEIGHTS = {
        "jaccard": 0.05,              # Basic word overlap (reduced)
        "contextual_jaccard": 0.15,   # Weighted by significance
        "cosine": 0.05,               # Basic TF-IDF (reduced)
        "contextual_cosine": 0.15,    # Weighted TF-IDF
        "concept_overlap": 0.20,      # Shared concepts
        "grammatical": 0.08,          # Sentence structure
        "semantic": 0.10,             # Embedding similarity
        "root_based": 0.10,           # Shared roots
        "prophetic": 0.07,            # Prophetic themes
        "narrative": 0.05,            # Narrative arc
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self._corpus_idf = None  # Cached IDF values

    async def _get_corpus_idf(self) -> Dict[str, float]:
        """Get or compute IDF values for the corpus."""
        if self._corpus_idf is not None:
            return self._corpus_idf

        # Compute document frequency for each term
        result = await self.session.execute(
            select(QuranVerse.text_imlaei)
        )
        verses = result.scalars().all()

        doc_count = len(verses)
        term_doc_freq = defaultdict(int)

        for verse_text in verses:
            words = set(extract_words(verse_text))
            for word in words:
                term_doc_freq[word] += 1

        # Compute IDF
        self._corpus_idf = {
            term: math.log(doc_count / (df + 1))
            for term, df in term_doc_freq.items()
        }

        return self._corpus_idf

    def _compute_tfidf_vector(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        """Compute TF-IDF vector for text."""
        tf = compute_tf_vector(text)

        return {
            word: freq * idf.get(word, 1.0)
            for word, freq in tf.items()
        }

    async def find_similar_verses(
        self,
        verse_id: Optional[int] = None,
        verse_text: Optional[str] = None,
        sura_no: Optional[int] = None,
        aya_no: Optional[int] = None,
        top_k: int = 20,
        min_score: float = 0.3,
        theme_filter: Optional[str] = None,
        exclude_same_sura: bool = False,
        connection_types: Optional[List[str]] = None,
        exclude_bismillah: bool = True,
    ) -> SimilaritySearchResult:
        """
        Find verses similar to a source verse using multi-layered analysis.

        Args:
            verse_id: ID of source verse
            verse_text: Or provide verse text directly
            sura_no: Sura number (if using reference)
            aya_no: Aya number (if using reference)
            top_k: Maximum results
            min_score: Minimum combined score threshold
            theme_filter: Filter by theme
            exclude_same_sura: Exclude verses from same sura
            connection_types: Filter by connection types
            exclude_bismillah: Exclude Bismillah phrase from similarity computation
                               (default True to avoid skewed results from repeated phrase)

        Returns:
            SimilaritySearchResult with detailed matches
        """
        import time
        start_time = time.time()

        # Get source verse
        source_verse = None
        if verse_id:
            result = await self.session.execute(
                select(QuranVerse).where(QuranVerse.id == verse_id)
            )
            source_verse = result.scalar_one_or_none()
        elif sura_no and aya_no:
            result = await self.session.execute(
                select(QuranVerse).where(
                    QuranVerse.sura_no == sura_no,
                    QuranVerse.aya_no == aya_no
                )
            )
            source_verse = result.scalar_one_or_none()

        if not source_verse and not verse_text:
            return SimilaritySearchResult(
                source_verse={},
                source_themes=[],
                source_structure="",
                total_similar=0,
                matches=[],
                theme_distribution={},
                connection_type_distribution={},
                search_time_ms=0,
            )

        # Use verse text from DB or provided
        if source_verse:
            verse_text = source_verse.text_imlaei
            source_data = {
                "verse_id": source_verse.id,
                "sura_no": source_verse.sura_no,
                "sura_name_ar": source_verse.sura_name_ar,
                "sura_name_en": source_verse.sura_name_en,
                "aya_no": source_verse.aya_no,
                "text_uthmani": source_verse.text_uthmani,
                "text_imlaei": source_verse.text_imlaei,
                "reference": f"{source_verse.sura_no}:{source_verse.aya_no}",
            }
        else:
            source_data = {"text": verse_text}

        # Preprocess source text (exclude Bismillah if enabled)
        source_text_processed = verse_text
        if exclude_bismillah:
            source_sura = source_verse.sura_no if source_verse else sura_no
            source_aya = source_verse.aya_no if source_verse else aya_no
            source_text_processed = preprocess_for_similarity(
                verse_text,
                sura_no=source_sura,
                aya_no=source_aya,
                exclude_bismillah=True
            )
            # Skip if verse is essentially just Bismillah
            if is_bismillah_verse(verse_text):
                logger.info(f"Source verse {source_sura}:{source_aya} is a Bismillah verse, minimal content for similarity")

        # Analyze source verse (using preprocessed text)
        source_words = set(extract_words(source_text_processed))
        source_roots = extract_roots_from_text(source_text_processed)
        source_themes = detect_themes(source_text_processed)
        source_structure = detect_sentence_structure(source_text_processed)

        # Get IDF values (use preprocessed text for TF-IDF)
        idf = await self._get_corpus_idf()
        source_tfidf = self._compute_tfidf_vector(source_text_processed, idf)

        # Get concepts from source
        source_concepts = set()
        for word in source_words:
            if word in CONCEPT_EXPANSIONS:
                source_concepts.update(CONCEPT_EXPANSIONS[word])
            source_concepts.add(word)

        # Fetch candidate verses
        query = select(QuranVerse)

        if exclude_same_sura and source_verse:
            query = query.where(QuranVerse.sura_no != source_verse.sura_no)

        if source_verse:
            query = query.where(QuranVerse.id != source_verse.id)

        result = await self.session.execute(query)
        candidates = result.scalars().all()

        # Score all candidates
        scored_matches = []
        theme_dist = defaultdict(int)
        conn_type_dist = defaultdict(int)

        for candidate in candidates:
            # Preprocess candidate text (exclude Bismillah if enabled)
            cand_text = candidate.text_imlaei
            if exclude_bismillah:
                # Skip verses that are essentially just Bismillah (like 1:1)
                if is_bismillah_verse(candidate.text_imlaei):
                    logger.debug(f"Skipping Bismillah verse: {candidate.sura_no}:{candidate.aya_no}")
                    continue

                # For first verses of suras, check if they're primarily Bismillah
                if is_first_verse_with_bismillah(candidate.sura_no, candidate.aya_no):
                    # Preprocess to remove Bismillah
                    cand_text = preprocess_for_similarity(
                        candidate.text_imlaei,
                        sura_no=candidate.sura_no,
                        aya_no=candidate.aya_no,
                        exclude_bismillah=True
                    )
                    # Skip if very little content remains after removing Bismillah
                    if not cand_text or len(cand_text.strip().split()) < 2:
                        logger.debug(f"Skipping first verse with minimal content after Bismillah removal: {candidate.sura_no}:{candidate.aya_no}")
                        continue
                else:
                    cand_text = preprocess_for_similarity(
                        candidate.text_imlaei,
                        sura_no=candidate.sura_no,
                        aya_no=candidate.aya_no,
                        exclude_bismillah=True
                    )

            # Extract candidate features (using preprocessed text)
            cand_words = set(extract_words(cand_text))
            cand_roots = extract_roots_from_text(cand_text)
            cand_themes = detect_themes(cand_text)
            cand_structure = detect_sentence_structure(cand_text)
            cand_tfidf = self._compute_tfidf_vector(cand_text, idf)

            # Get concepts from candidate
            cand_concepts = set()
            for word in cand_words:
                if word in CONCEPT_EXPANSIONS:
                    cand_concepts.update(CONCEPT_EXPANSIONS[word])
                cand_concepts.add(word)

            # Compute basic similarity scores
            jacc = jaccard_similarity(source_words, cand_words)
            cos = cosine_similarity(source_tfidf, cand_tfidf)
            concept = concept_overlap_score(source_concepts, cand_concepts)
            gram = grammatical_similarity(source_structure, cand_structure)
            root = root_similarity_score(source_roots, cand_roots)

            # Compute ENHANCED contextual similarity scores
            ctx_jacc = contextual_weighted_jaccard(source_words, cand_words)
            ctx_cos = contextual_cosine_similarity(source_tfidf, cand_tfidf)

            # Compute prophetic/cross-story similarity
            prophetic_score, prophetic_elements, prophetic_theme = prophetic_theme_similarity(
                verse_text, candidate.text_imlaei
            )

            # Compute narrative arc similarity
            narrative_score = narrative_arc_similarity(
                verse_text, candidate.text_imlaei,
                source_verse.sura_no if source_verse else 0,
                candidate.sura_no,
                source_verse.aya_no if source_verse else 0,
                candidate.aya_no
            )

            # Semantic score placeholder (would need embeddings for full implementation)
            semantic_score = 0.0

            # Compute combined score with enhanced weighting
            combined = (
                self.WEIGHTS["jaccard"] * jacc +
                self.WEIGHTS["contextual_jaccard"] * ctx_jacc +
                self.WEIGHTS["cosine"] * cos +
                self.WEIGHTS["contextual_cosine"] * ctx_cos +
                self.WEIGHTS["concept_overlap"] * concept +
                self.WEIGHTS["grammatical"] * gram +
                self.WEIGHTS["semantic"] * semantic_score +
                self.WEIGHTS["root_based"] * root +
                self.WEIGHTS["prophetic"] * prophetic_score +
                self.WEIGHTS["narrative"] * narrative_score
            )

            # Normalize combined score
            active_weights = sum(v for k, v in self.WEIGHTS.items() if k != "semantic")
            combined = combined / active_weights if active_weights > 0 else 0

            if combined < min_score:
                continue

            # Apply filters
            if theme_filter and theme_filter not in cand_themes:
                continue

            scores = SimilarityScores(
                jaccard=round(jacc, 4),
                cosine=round(cos, 4),
                concept_overlap=round(concept, 4),
                grammatical=round(gram, 4),
                semantic=round(semantic_score, 4),
                root_based=round(root, 4),
                contextual_jaccard=round(ctx_jacc, 4),
                contextual_cosine=round(ctx_cos, 4),
                prophetic=round(prophetic_score, 4),
                narrative=round(narrative_score, 4),
                combined=round(combined, 4),
            )

            # Determine connection type
            conn_type = determine_connection_type(scores)

            if connection_types and conn_type.value not in connection_types:
                continue

            # Shared elements
            shared_words = list(source_words & cand_words)[:10]
            shared_roots = list(source_roots & cand_roots)[:5]
            shared_themes = list(set(source_themes) & set(cand_themes))
            shared_concepts = list(source_concepts & cand_concepts)[:10]

            # Primary theme
            primary_theme = cand_themes[0] if cand_themes else ""

            # Extract prophets from prophetic elements
            shared_prophets_list = [e for e in prophetic_elements if e in PROPHETIC_THEMES]
            cross_story_theme_data = CROSS_STORY_THEMES.get(prophetic_theme, {})

            # Build match
            match = AdvancedSimilarityMatch(
                verse_id=candidate.id,
                sura_no=candidate.sura_no,
                sura_name_ar=candidate.sura_name_ar,
                sura_name_en=candidate.sura_name_en,
                aya_no=candidate.aya_no,
                text_uthmani=candidate.text_uthmani,
                text_imlaei=candidate.text_imlaei,
                reference=f"{candidate.sura_no}:{candidate.aya_no}",
                scores=scores,
                connection_type=conn_type,
                connection_strength=get_connection_strength(combined),
                shared_words=shared_words,
                shared_roots=shared_roots,
                shared_concepts=shared_concepts,
                shared_themes=shared_themes,
                primary_theme=primary_theme,
                primary_theme_ar=THEME_LABELS_AR.get(primary_theme, ""),
                theme_color=THEME_COLORS.get(primary_theme, "#6B7280"),
                sentence_structure=cand_structure.value,
                sentence_structure_ar=get_sentence_structure_ar(cand_structure),
                shared_prophets=shared_prophets_list,
                cross_story_theme=prophetic_theme,
                cross_story_theme_ar=cross_story_theme_data.get("ar", ""),
                tafsir_available=True,  # Will check in API layer
                similarity_explanation_ar=generate_explanation(
                    shared_words, shared_roots, shared_themes, conn_type, "ar"
                ),
                similarity_explanation_en=generate_explanation(
                    shared_words, shared_roots, shared_themes, conn_type, "en"
                ),
            )

            scored_matches.append((combined, match))

            # Update distributions
            for theme in cand_themes:
                theme_dist[theme] += 1
            conn_type_dist[conn_type.value] += 1

        # Sort by combined score and take top_k
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        top_matches = [m for _, m in scored_matches[:top_k]]

        search_time = (time.time() - start_time) * 1000

        return SimilaritySearchResult(
            source_verse=source_data,
            source_themes=source_themes,
            source_structure=source_structure.value if isinstance(source_structure, SentenceStructure) else source_structure,
            total_similar=len(scored_matches),
            matches=top_matches,
            theme_distribution=dict(theme_dist),
            connection_type_distribution=dict(conn_type_dist),
            search_time_ms=round(search_time, 2),
        )

    async def find_cross_sura_connections(
        self,
        sura_no: int,
        aya_no: int,
        top_k: int = 10,
    ) -> List[AdvancedSimilarityMatch]:
        """
        Find verses from OTHER suras that are similar to the given verse.

        Useful for understanding how themes appear across different suras.
        """
        result = await self.find_similar_verses(
            sura_no=sura_no,
            aya_no=aya_no,
            top_k=top_k,
            exclude_same_sura=True,
            min_score=0.25,
        )

        return result.matches

    async def get_theme_verses(
        self,
        theme: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get all verses related to a specific theme.
        """
        result = await self.session.execute(select(QuranVerse))
        verses = result.scalars().all()

        theme_verses = []
        for verse in verses:
            detected = detect_themes(verse.text_imlaei)
            if theme in detected:
                theme_verses.append({
                    "verse_id": verse.id,
                    "sura_no": verse.sura_no,
                    "sura_name_ar": verse.sura_name_ar,
                    "sura_name_en": verse.sura_name_en,
                    "aya_no": verse.aya_no,
                    "text_uthmani": verse.text_uthmani,
                    "reference": f"{verse.sura_no}:{verse.aya_no}",
                    "themes": detected,
                })

                if len(theme_verses) >= limit:
                    break

        return theme_verses

    async def find_cross_story_connections(
        self,
        prophet_name: str,
        cross_theme: Optional[str] = None,
        limit: int = 30,
    ) -> Dict[str, Any]:
        """
        Find cross-story thematic connections for a prophet's trials.

        Example: Find stories of other prophets dealing with similar trials
        as Prophet Musa (divine tests, community opposition, etc.)

        Arabic: البحث عن الروابط الموضوعية عبر القصص
        """
        result = await self.session.execute(select(QuranVerse))
        verses = result.scalars().all()

        # Normalize prophet name
        prophet_norm = normalize_arabic(prophet_name)

        # Get prophet's themes
        prophet_data = None
        for p_name, p_data in PROPHETIC_THEMES.items():
            if normalize_arabic(p_name) == prophet_norm:
                prophet_data = p_data
                prophet_name = p_name
                break

        if not prophet_data:
            return {
                "prophet": prophet_name,
                "error": "Prophet not found in database",
                "connections": [],
            }

        # Find verses mentioning this prophet
        prophet_verses = []
        for verse in verses:
            if prophet_norm in normalize_arabic(verse.text_imlaei):
                prophet_verses.append(verse)

        # Find related prophets' stories
        related_stories = []
        related_prophets = prophet_data.get("related_prophets", [])
        themes = prophet_data.get("themes", [])

        # Find cross-story connections
        for theme_id, theme_data in CROSS_STORY_THEMES.items():
            if cross_theme and theme_id != cross_theme:
                continue

            # Check if this prophet is associated with this theme
            if prophet_name not in theme_data.get("stories", []):
                continue

            # Find other prophets with same theme
            other_prophets = [
                p for p in theme_data.get("stories", [])
                if p != prophet_name
            ]

            for other_prophet in other_prophets:
                other_norm = normalize_arabic(other_prophet)

                # Find verses mentioning the other prophet
                for verse in verses:
                    if other_norm in normalize_arabic(verse.text_imlaei):
                        # Check for theme keywords
                        verse_norm = normalize_arabic(verse.text_imlaei)
                        has_theme = any(
                            normalize_arabic(kw) in verse_norm
                            for kw in theme_data.get("keywords", [])
                        )

                        if has_theme or True:  # Include all for now
                            related_stories.append({
                                "verse_id": verse.id,
                                "sura_no": verse.sura_no,
                                "sura_name_ar": verse.sura_name_ar,
                                "sura_name_en": verse.sura_name_en,
                                "aya_no": verse.aya_no,
                                "text_uthmani": verse.text_uthmani,
                                "reference": f"{verse.sura_no}:{verse.aya_no}",
                                "prophet": other_prophet,
                                "theme_id": theme_id,
                                "theme_ar": theme_data.get("ar", ""),
                                "theme_en": theme_data.get("en", ""),
                            })

                            if len(related_stories) >= limit:
                                break

                if len(related_stories) >= limit:
                    break
            if len(related_stories) >= limit:
                break

        return {
            "prophet": prophet_name,
            "prophet_themes": themes,
            "related_prophets": related_prophets,
            "source_verses_count": len(prophet_verses),
            "cross_story_connections": related_stories,
            "available_themes": [
                {"id": t_id, "ar": t_data.get("ar", ""), "en": t_data.get("en", "")}
                for t_id, t_data in CROSS_STORY_THEMES.items()
                if prophet_name in t_data.get("stories", [])
            ],
        }

    async def get_story_mode_narrative(
        self,
        theme: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Story Mode: Generate a narrative arc of verses on a theme.

        Links related stories across different surahs to create
        a cohesive thematic journey.

        Themes: patience, gratitude, trust, divine_tests, etc.

        Arabic: وضع القصة - عرض الآيات في قوس سردي موضوعي
        """
        result = await self.session.execute(select(QuranVerse))
        verses = result.scalars().all()

        # Get theme data
        theme_data = CROSS_STORY_THEMES.get(theme)
        theme_keywords = THEME_KEYWORDS.get(theme, [])

        if not theme_data and not theme_keywords:
            # Try common themes
            common_themes = {
                "patience": {
                    "ar": "الصبر", "en": "Patience",
                    "keywords": ["صبر", "صابر", "اصبر", "صبرا"],
                    "stories": ["يوسف", "أيوب", "موسى"],
                },
                "gratitude": {
                    "ar": "الشكر", "en": "Gratitude",
                    "keywords": ["شكر", "شاكر", "اشكر", "حمد"],
                    "stories": ["سليمان", "داود", "إبراهيم"],
                },
                "trust": {
                    "ar": "التوكل", "en": "Trust in Allah",
                    "keywords": ["توكل", "متوكل", "وكيل", "توكلت"],
                    "stories": ["إبراهيم", "موسى", "محمد"],
                },
                "mercy": {
                    "ar": "الرحمة", "en": "Mercy",
                    "keywords": ["رحمة", "رحيم", "رحمن", "ارحم"],
                    "stories": [],
                },
                "guidance": {
                    "ar": "الهداية", "en": "Guidance",
                    "keywords": ["هداية", "هدى", "اهد", "مهتد"],
                    "stories": [],
                },
            }
            theme_data = common_themes.get(theme, {})
            theme_keywords = theme_data.get("keywords", theme_keywords)

        if not theme_keywords and theme_data:
            theme_keywords = theme_data.get("keywords", [])

        # Collect verses matching the theme
        narrative_sections = {
            "introduction": [],      # Opening/setting verses
            "development": [],       # Main body verses
            "climax": [],           # Key moments
            "resolution": [],       # Conclusion/lessons
        }

        # Find all matching verses
        matching_verses = []
        for verse in verses:
            verse_norm = normalize_arabic(verse.text_imlaei)
            for keyword in theme_keywords:
                if normalize_arabic(keyword) in verse_norm:
                    matching_verses.append({
                        "verse_id": verse.id,
                        "sura_no": verse.sura_no,
                        "sura_name_ar": verse.sura_name_ar,
                        "sura_name_en": verse.sura_name_en,
                        "aya_no": verse.aya_no,
                        "text_uthmani": verse.text_uthmani,
                        "reference": f"{verse.sura_no}:{verse.aya_no}",
                        "keyword_matched": keyword,
                    })
                    break

            if len(matching_verses) >= limit * 2:
                break

        # Organize into narrative sections based on sura order and position
        for i, verse in enumerate(matching_verses[:limit]):
            # Simple heuristic for narrative position
            position_ratio = i / max(len(matching_verses), 1)

            if position_ratio < 0.2:
                narrative_sections["introduction"].append(verse)
            elif position_ratio < 0.6:
                narrative_sections["development"].append(verse)
            elif position_ratio < 0.85:
                narrative_sections["climax"].append(verse)
            else:
                narrative_sections["resolution"].append(verse)

        return {
            "theme": theme,
            "theme_ar": theme_data.get("ar", THEME_LABELS_AR.get(theme, theme)),
            "theme_en": theme_data.get("en", theme.replace("_", " ").title()),
            "theme_color": THEME_COLORS.get(theme, "#6B7280"),
            "total_verses": len(matching_verses),
            "related_prophets": theme_data.get("stories", []),
            "narrative_arc": {
                "introduction": {
                    "title_ar": "المقدمة",
                    "title_en": "Introduction",
                    "description_ar": f"آيات تفتتح موضوع {theme_data.get('ar', theme)}",
                    "description_en": f"Verses introducing the theme of {theme_data.get('en', theme)}",
                    "verses": narrative_sections["introduction"],
                },
                "development": {
                    "title_ar": "التطور",
                    "title_en": "Development",
                    "description_ar": "آيات تفصّل وتشرح الموضوع",
                    "description_en": "Verses that elaborate on the theme",
                    "verses": narrative_sections["development"],
                },
                "climax": {
                    "title_ar": "الذروة",
                    "title_en": "Climax",
                    "description_ar": "آيات تمثل قمة الموضوع",
                    "description_en": "Key verses representing the peak of the theme",
                    "verses": narrative_sections["climax"],
                },
                "resolution": {
                    "title_ar": "الخاتمة",
                    "title_en": "Resolution",
                    "description_ar": "آيات تختتم الموضوع بالدروس والعبر",
                    "description_en": "Concluding verses with lessons and wisdom",
                    "verses": narrative_sections["resolution"],
                },
            },
        }

    async def get_available_story_themes(self) -> List[Dict[str, Any]]:
        """Get list of available themes for Story Mode."""
        themes = []

        # Add cross-story themes
        for theme_id, theme_data in CROSS_STORY_THEMES.items():
            themes.append({
                "id": theme_id,
                "name_ar": theme_data.get("ar", ""),
                "name_en": theme_data.get("en", ""),
                "color": THEME_COLORS.get(theme_id, "#6B7280"),
                "related_prophets": theme_data.get("stories", []),
                "category": "cross_story",
            })

        # Add additional common themes
        common_themes = [
            {"id": "patience", "name_ar": "الصبر", "name_en": "Patience", "category": "virtue"},
            {"id": "gratitude", "name_ar": "الشكر", "name_en": "Gratitude", "category": "virtue"},
            {"id": "trust", "name_ar": "التوكل", "name_en": "Trust in Allah", "category": "virtue"},
            {"id": "mercy", "name_ar": "الرحمة", "name_en": "Mercy", "category": "divine_attribute"},
            {"id": "guidance", "name_ar": "الهداية", "name_en": "Guidance", "category": "divine_attribute"},
            {"id": "tawheed", "name_ar": "التوحيد", "name_en": "Monotheism", "category": "belief"},
            {"id": "afterlife", "name_ar": "الآخرة", "name_en": "Afterlife", "category": "belief"},
        ]

        for theme in common_themes:
            theme["color"] = THEME_COLORS.get(theme["id"], "#6B7280")
            if theme["id"] not in [t["id"] for t in themes]:
                themes.append(theme)

        return themes
