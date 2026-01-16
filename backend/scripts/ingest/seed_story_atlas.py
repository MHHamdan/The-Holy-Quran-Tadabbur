#!/usr/bin/env python3
"""
Story Atlas Seed Script - Comprehensive Quranic Story Database.

This script populates the story_clusters and story_events tables with
grounded data for ALL major Quranic narratives.

GROUNDING RULES:
================
- NON-NEGOTIABLE: Do NOT invent details
- Place/time basis must be "explicit", "inferred", or "unknown"
- Every event must have at least 1 tafsir evidence snippet
- Evidence sources: ibn_kathir_en, tabari_ar, qurtubi_ar (enabled in system)

CATEGORIES:
===========
A) Prophet stories
B) Named non-prophet characters
C) Peoples/nations
D) Parables/lessons

Usage:
    python scripts/ingest/seed_story_atlas.py
"""
import json
import os
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"
)

# =============================================================================
# STORY CLUSTERS DATA
# =============================================================================

STORY_CLUSTERS = [
    # =========================================================================
    # AL-KAHF STORIES (Surah 18)
    # =========================================================================
    {
        "id": "cluster_cave_sleepers",
        "title_ar": "أصحاب الكهف",
        "title_en": "People of the Cave (Sleepers)",
        "short_title_ar": "أصحاب الكهف",
        "short_title_en": "Cave Sleepers",
        "category": "historical",
        "main_persons": ["Young Believers"],
        "groups": [],
        "tags": ["faith", "persecution", "miracle", "sleep", "protection"],
        "places": [{"name": "Cave (Kahf)", "name_ar": "الكهف", "basis": "explicit"}],
        "era": "unknown",
        "era_basis": "unknown",
        "time_description_en": "Era unknown - possibly Roman persecution of early Christians",
        "ayah_spans": [{"sura": 18, "start": 9, "end": 26}],
        "primary_sura": 18,
        "summary_ar": "شباب آمنوا بربهم وفروا من الاضطهاد إلى كهف، فأنامهم الله ثلاثمئة سنة وتسع سنين",
        "summary_en": "Young believers who fled persecution to a cave, where Allah made them sleep for 309 years as a sign.",
        "lessons_ar": ["الإيمان يحمي", "معجزة الحفظ الإلهي", "الفتية مثال للشباب المؤمن"],
        "lessons_en": ["Faith protects", "Divine preservation miracle", "Youth as models of belief"],
    },
    {
        "id": "cluster_two_gardens",
        "title_ar": "صاحب الجنتين",
        "title_en": "Owner of Two Gardens",
        "short_title_ar": "صاحب الجنتين",
        "short_title_en": "Two Gardens",
        "category": "parable",
        "main_persons": ["Rich Man", "Poor Believer"],
        "groups": [],
        "tags": ["wealth", "arrogance", "gratitude", "destruction", "lesson"],
        "places": [],
        "era": "unknown",
        "era_basis": "unknown",
        "ayah_spans": [{"sura": 18, "start": 32, "end": 44}],
        "primary_sura": 18,
        "summary_ar": "مثل رجلين: أحدهما غني بجنتين تكبر على صاحبه الفقير، فدمر الله جنتيه",
        "summary_en": "Parable of two men: one rich with two gardens who boasted over his poor believing companion, then lost everything.",
        "lessons_ar": ["الغنى ابتلاء", "التكبر سبب الهلاك", "الشكر واجب"],
        "lessons_en": ["Wealth is a test", "Arrogance leads to ruin", "Gratitude is obligatory"],
    },
    {
        "id": "cluster_musa_khidr",
        "title_ar": "موسى والخضر",
        "title_en": "Musa and Al-Khidr",
        "short_title_ar": "موسى والخضر",
        "short_title_en": "Musa & Khidr",
        "category": "prophet",
        "main_persons": ["Musa", "Al-Khidr"],
        "groups": [],
        "tags": ["knowledge", "patience", "hidden_wisdom", "journey", "learning"],
        "places": [{"name": "Junction of Two Seas", "name_ar": "مجمع البحرين", "basis": "explicit"}],
        "era": "egypt",
        "era_basis": "inferred",
        "time_description_en": "After Musa received revelation, during Bani Israil period",
        "ayah_spans": [{"sura": 18, "start": 60, "end": 82}],
        "primary_sura": 18,
        "summary_ar": "رحلة موسى لطلب العلم من الخضر، وثلاثة اختبارات في الصبر على ما لا يفهم",
        "summary_en": "Musa's journey to learn from Al-Khidr, and three tests of patience with things he didn't understand.",
        "lessons_ar": ["العلم فوق كل ذي علم عليم", "الصبر على ما لا نفهم", "الحكمة الخفية"],
        "lessons_en": ["Above every knowledgeable one is one more knowing", "Patience with the incomprehensible", "Hidden wisdom"],
    },
    {
        "id": "cluster_dhulqarnayn",
        "title_ar": "ذو القرنين",
        "title_en": "Dhul-Qarnayn",
        "short_title_ar": "ذو القرنين",
        "short_title_en": "Dhul-Qarnayn",
        "category": "named_char",
        "main_persons": ["Dhul-Qarnayn"],
        "groups": ["Yajuj wa Majuj"],
        "tags": ["power", "justice", "travel", "barrier", "tamkeen", "humility"],
        "places": [
            {"name": "West (Setting Sun)", "name_ar": "مغرب الشمس", "basis": "explicit"},
            {"name": "East (Rising Sun)", "name_ar": "مطلع الشمس", "basis": "explicit"},
            {"name": "Between Two Mountains", "name_ar": "بين السدين", "basis": "explicit"}
        ],
        "era": "pre_islamic",
        "era_basis": "inferred",
        "time_description_en": "Pre-Islamic era, identity debated (Alexander, Cyrus, or other)",
        "ayah_spans": [{"sura": 18, "start": 83, "end": 98}],
        "primary_sura": 18,
        "summary_ar": "ملك صالح مكنه الله في الأرض، رحل شرقاً وغرباً وبنى سداً ضد يأجوج ومأجوج",
        "summary_en": "A righteous ruler empowered by Allah, who traveled east and west and built a barrier against Yajuj & Majuj.",
        "lessons_ar": ["القوة مع العدل", "التمكين يتطلب الشكر", "رفض الأجر والإخلاص"],
        "lessons_en": ["Power with justice", "Empowerment requires gratitude", "Refusing payment, sincere service"],
    },

    # =========================================================================
    # YUSUF (Surah 12 - Complete story in one surah)
    # =========================================================================
    {
        "id": "cluster_yusuf",
        "title_ar": "قصة يوسف",
        "title_en": "Story of Yusuf (Joseph)",
        "short_title_ar": "يوسف",
        "short_title_en": "Yusuf",
        "category": "prophet",
        "main_persons": ["Yusuf", "Yaqub", "Brothers", "Aziz of Egypt", "Wife of Aziz", "King"],
        "groups": ["Bani Israil"],
        "tags": ["dreams", "jealousy", "patience", "chastity", "forgiveness", "family"],
        "places": [
            {"name": "Canaan (Palestine)", "name_ar": "كنعان", "basis": "inferred"},
            {"name": "Egypt", "name_ar": "مصر", "basis": "explicit"}
        ],
        "era": "egypt",
        "era_basis": "explicit",
        "time_description_en": "Before Musa, during early Israelite period in Egypt",
        "ayah_spans": [{"sura": 12, "start": 1, "end": 111}],
        "primary_sura": 12,
        "summary_ar": "أحسن القصص: يوسف من البئر إلى العرش، قصة الصبر والعفة والمغفرة",
        "summary_en": "The best of stories: Yusuf from the well to the throne - a story of patience, chastity, and forgiveness.",
        "lessons_ar": ["الصبر الجميل", "العفة عند الفتنة", "المغفرة للإخوة", "تأويل الرؤيا"],
        "lessons_en": ["Beautiful patience", "Chastity under temptation", "Forgiving brothers", "Dream interpretation"],
    },

    # =========================================================================
    # MUSA & PHARAOH (Multiple suras)
    # =========================================================================
    {
        "id": "cluster_musa_pharaoh",
        "title_ar": "موسى وفرعون",
        "title_en": "Musa and Pharaoh",
        "short_title_ar": "موسى وفرعون",
        "short_title_en": "Musa vs Pharaoh",
        "category": "prophet",
        "main_persons": ["Musa", "Harun", "Firawn (Pharaoh)", "Asiya"],
        "groups": ["Bani Israil", "Egyptians"],
        "tags": ["liberation", "miracles", "tyrant", "exodus", "sea_parting", "signs"],
        "places": [
            {"name": "Egypt", "name_ar": "مصر", "basis": "explicit"},
            {"name": "Sinai", "name_ar": "سيناء", "basis": "inferred"},
            {"name": "Red Sea", "name_ar": "البحر", "basis": "explicit"}
        ],
        "era": "egypt",
        "era_basis": "explicit",
        "ayah_spans": [
            {"sura": 2, "start": 49, "end": 61},
            {"sura": 7, "start": 103, "end": 162},
            {"sura": 10, "start": 75, "end": 92},
            {"sura": 20, "start": 9, "end": 98},
            {"sura": 26, "start": 10, "end": 68},
            {"sura": 28, "start": 3, "end": 43},
            {"sura": 79, "start": 15, "end": 26}
        ],
        "primary_sura": 20,
        "summary_ar": "قصة موسى من ولادته إلى مواجهة فرعون وتحرير بني إسرائيل",
        "summary_en": "The story of Musa from birth to confronting Pharaoh and liberating Bani Israil.",
        "lessons_ar": ["الطغاة يُهلكون", "المعجزات تُظهر الحق", "الصبر على الأذى"],
        "lessons_en": ["Tyrants are destroyed", "Miracles reveal truth", "Patience under persecution"],
    },

    # =========================================================================
    # NUH (Multiple suras)
    # =========================================================================
    {
        "id": "cluster_nuh",
        "title_ar": "قصة نوح",
        "title_en": "Story of Nuh (Noah)",
        "short_title_ar": "نوح",
        "short_title_en": "Nuh",
        "category": "prophet",
        "main_persons": ["Nuh", "Son of Nuh", "Wife of Nuh"],
        "groups": ["People of Nuh"],
        "tags": ["dawah", "patience", "flood", "ark", "rejection", "family_test"],
        "places": [],
        "era": "primordial",
        "era_basis": "inferred",
        "time_description_en": "Very early human history, before Ibrahim",
        "ayah_spans": [
            {"sura": 7, "start": 59, "end": 64},
            {"sura": 11, "start": 25, "end": 49},
            {"sura": 23, "start": 23, "end": 30},
            {"sura": 26, "start": 105, "end": 122},
            {"sura": 71, "start": 1, "end": 28}
        ],
        "primary_sura": 71,
        "summary_ar": "دعوة نوح ألف سنة إلا خمسين عاماً، ثم الطوفان الذي أهلك الكافرين",
        "summary_en": "Nuh's 950-year dawah, then the flood that destroyed the disbelievers.",
        "lessons_ar": ["الدعوة تستمر مهما طالت", "العصيان يجلب الهلاك", "امتحان الأهل"],
        "lessons_en": ["Dawah continues however long", "Disobedience brings destruction", "Family tests"],
    },

    # =========================================================================
    # IBRAHIM (Multiple suras)
    # =========================================================================
    {
        "id": "cluster_ibrahim",
        "title_ar": "قصة إبراهيم",
        "title_en": "Story of Ibrahim (Abraham)",
        "short_title_ar": "إبراهيم",
        "short_title_en": "Ibrahim",
        "category": "prophet",
        "main_persons": ["Ibrahim", "Sarah", "Hajar", "Ismail", "Ishaq", "Lut", "Namrud"],
        "groups": [],
        "tags": ["monotheism", "sacrifice", "fire", "kaaba", "hajj", "arguing_with_idolaters"],
        "places": [
            {"name": "Babylon/Iraq", "name_ar": "بابل", "basis": "inferred"},
            {"name": "Makkah", "name_ar": "مكة", "basis": "explicit"},
            {"name": "Palestine", "name_ar": "فلسطين", "basis": "inferred"}
        ],
        "era": "ancient",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 2, "start": 124, "end": 141},
            {"sura": 6, "start": 74, "end": 83},
            {"sura": 14, "start": 35, "end": 41},
            {"sura": 19, "start": 41, "end": 50},
            {"sura": 21, "start": 51, "end": 73},
            {"sura": 26, "start": 69, "end": 104},
            {"sura": 37, "start": 83, "end": 113}
        ],
        "primary_sura": 37,
        "summary_ar": "خليل الرحمن، حطم الأصنام، نجا من النار، بنى الكعبة، وامتُحن بذبح ابنه",
        "summary_en": "Friend of Allah, smashed idols, saved from fire, built Ka'bah, tested with sacrificing his son.",
        "lessons_ar": ["التوحيد أساس", "التوكل على الله", "الطاعة في أصعب الاختبارات"],
        "lessons_en": ["Monotheism is foundation", "Trust in Allah", "Obedience in hardest tests"],
    },

    # =========================================================================
    # MARYAM & ISA
    # =========================================================================
    {
        "id": "cluster_maryam_isa",
        "title_ar": "مريم وعيسى",
        "title_en": "Maryam and Isa (Jesus)",
        "short_title_ar": "مريم وعيسى",
        "short_title_en": "Maryam & Isa",
        "category": "prophet",
        "main_persons": ["Maryam", "Isa", "Zakariyya", "Yahya"],
        "groups": ["Bani Israil", "Disciples (Hawariyyun)"],
        "tags": ["miracle_birth", "chastity", "miracles", "revelation", "table"],
        "places": [
            {"name": "Bayt al-Maqdis", "name_ar": "بيت المقدس", "basis": "inferred"},
            {"name": "Bethlehem", "name_ar": "بيت لحم", "basis": "inferred"}
        ],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 3, "start": 35, "end": 63},
            {"sura": 5, "start": 110, "end": 120},
            {"sura": 19, "start": 16, "end": 40},
            {"sura": 61, "start": 6, "end": 6},
            {"sura": 61, "start": 14, "end": 14}
        ],
        "primary_sura": 19,
        "summary_ar": "ولادة عيسى بمعجزة من مريم العذراء، ورسالته لبني إسرائيل",
        "summary_en": "The miraculous birth of Isa from virgin Maryam, and his message to Bani Israil.",
        "lessons_ar": ["قدرة الله فوق الأسباب", "العفة والتقوى", "عيسى عبد الله ورسوله"],
        "lessons_en": ["Allah's power transcends causes", "Chastity and piety", "Isa is Allah's servant and messenger"],
    },

    # =========================================================================
    # NATIONS: ʿĀD & HUD
    # =========================================================================
    {
        "id": "cluster_aad_hud",
        "title_ar": "عاد وهود",
        "title_en": "ʿĀd and Prophet Hud",
        "short_title_ar": "عاد",
        "short_title_en": "ʿĀd",
        "category": "nation",
        "main_persons": ["Hud"],
        "groups": ["ʿĀd"],
        "tags": ["arrogance", "strength", "wind", "destruction", "iram"],
        "places": [{"name": "Ahqaf (Southern Arabia)", "name_ar": "الأحقاف", "basis": "explicit"}],
        "era": "ancient",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 7, "start": 65, "end": 72},
            {"sura": 11, "start": 50, "end": 60},
            {"sura": 26, "start": 123, "end": 140},
            {"sura": 41, "start": 15, "end": 16},
            {"sura": 46, "start": 21, "end": 26},
            {"sura": 89, "start": 6, "end": 8}
        ],
        "primary_sura": 11,
        "summary_ar": "قوم عاد كانوا أقوياء بانين، أرسل الله إليهم هوداً فكذبوه فأهلكهم بريح صرصر",
        "summary_en": "ʿĀd were powerful builders, Allah sent Hud to them but they rejected him, destroyed by furious wind.",
        "lessons_ar": ["القوة لا تغني من الله", "التكبر سبب الهلاك"],
        "lessons_en": ["Strength doesn't protect from Allah", "Arrogance causes destruction"],
    },

    # =========================================================================
    # NATIONS: THAMUD & SALIH
    # =========================================================================
    {
        "id": "cluster_thamud_salih",
        "title_ar": "ثمود وصالح",
        "title_en": "Thamūd and Prophet Salih",
        "short_title_ar": "ثمود",
        "short_title_en": "Thamūd",
        "category": "nation",
        "main_persons": ["Salih"],
        "groups": ["Thamūd"],
        "tags": ["she_camel", "miracle", "rock_dwellings", "earthquake", "disobedience"],
        "places": [{"name": "Al-Hijr (Mada'in Salih)", "name_ar": "الحجر", "basis": "explicit"}],
        "era": "ancient",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 7, "start": 73, "end": 79},
            {"sura": 11, "start": 61, "end": 68},
            {"sura": 26, "start": 141, "end": 159},
            {"sura": 27, "start": 45, "end": 53},
            {"sura": 54, "start": 23, "end": 31},
            {"sura": 91, "start": 11, "end": 15}
        ],
        "primary_sura": 11,
        "summary_ar": "قوم ثمود نحتوا الجبال بيوتاً، أرسل الله الناقة آية فعقروها فأهلكهم",
        "summary_en": "Thamūd carved houses from mountains, Allah sent she-camel as sign, they killed it, were destroyed.",
        "lessons_ar": ["الآيات لا تُكذَّب", "العقوق يجلب العذاب"],
        "lessons_en": ["Signs must not be denied", "Transgression brings punishment"],
    },

    # =========================================================================
    # NATIONS: PEOPLE OF LUT
    # =========================================================================
    {
        "id": "cluster_lut",
        "title_ar": "قوم لوط",
        "title_en": "People of Lut (Lot)",
        "short_title_ar": "قوم لوط",
        "short_title_en": "Lut's People",
        "category": "nation",
        "main_persons": ["Lut", "Wife of Lut"],
        "groups": ["People of Lut"],
        "tags": ["fahisha", "homosexuality", "destruction", "angels", "rain_of_stones"],
        "places": [{"name": "Sodom", "name_ar": "سدوم", "basis": "inferred"}],
        "era": "ancient",
        "era_basis": "inferred",
        "time_description_en": "Contemporary of Ibrahim",
        "ayah_spans": [
            {"sura": 7, "start": 80, "end": 84},
            {"sura": 11, "start": 77, "end": 83},
            {"sura": 15, "start": 61, "end": 77},
            {"sura": 26, "start": 160, "end": 175},
            {"sura": 27, "start": 54, "end": 58},
            {"sura": 29, "start": 28, "end": 35}
        ],
        "primary_sura": 11,
        "summary_ar": "قوم لوط أتوا الفاحشة فأهلكهم الله بحجارة من السماء",
        "summary_en": "The people of Lut committed fahisha (immorality), Allah destroyed them with stones from sky.",
        "lessons_ar": ["الفاحشة توجب العذاب", "نجاة المؤمنين"],
        "lessons_en": ["Immorality brings punishment", "Believers are saved"],
    },

    # =========================================================================
    # SULAYMAN (Solomon)
    # =========================================================================
    {
        "id": "cluster_sulayman",
        "title_ar": "سليمان",
        "title_en": "Prophet Sulayman (Solomon)",
        "short_title_ar": "سليمان",
        "short_title_en": "Sulayman",
        "category": "prophet",
        "main_persons": ["Sulayman", "Queen of Sheba (Bilqis)"],
        "groups": ["Jinn", "Birds", "Ants"],
        "tags": ["kingdom", "jinn", "birds", "ants", "wisdom", "sheba"],
        "places": [
            {"name": "Jerusalem", "name_ar": "بيت المقدس", "basis": "inferred"},
            {"name": "Sheba (Yemen)", "name_ar": "سبأ", "basis": "explicit"}
        ],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 21, "start": 78, "end": 82},
            {"sura": 27, "start": 15, "end": 44},
            {"sura": 34, "start": 12, "end": 14},
            {"sura": 38, "start": 30, "end": 40}
        ],
        "primary_sura": 27,
        "summary_ar": "سليمان سخر الله له الجن والريح وعلمه منطق الطير، وقصته مع ملكة سبأ",
        "summary_en": "Sulayman was given control of jinn and wind, taught language of birds, story with Queen of Sheba.",
        "lessons_ar": ["الملك نعمة تُشكر", "العلم من الله", "الحكمة في الدعوة"],
        "lessons_en": ["Kingdom is blessing to be grateful for", "Knowledge is from Allah", "Wisdom in dawah"],
    },

    # =========================================================================
    # DAWUD (David)
    # =========================================================================
    {
        "id": "cluster_dawud",
        "title_ar": "داود",
        "title_en": "Prophet Dawud (David)",
        "short_title_ar": "داود",
        "short_title_en": "Dawud",
        "category": "prophet",
        "main_persons": ["Dawud", "Jalut (Goliath)", "Talut (Saul)"],
        "groups": ["Bani Israil"],
        "tags": ["zabur", "psalms", "iron", "judgment", "goliath"],
        "places": [{"name": "Palestine", "name_ar": "فلسطين", "basis": "inferred"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 2, "start": 246, "end": 252},
            {"sura": 21, "start": 78, "end": 80},
            {"sura": 34, "start": 10, "end": 11},
            {"sura": 38, "start": 17, "end": 26}
        ],
        "primary_sura": 38,
        "summary_ar": "قتل داود جالوت، أُوتي الزبور، سخر الله له الحديد والجبال",
        "summary_en": "Dawud killed Goliath, given Zabur (Psalms), iron and mountains made subservient to him.",
        "lessons_ar": ["الشجاعة في سبيل الله", "الشكر على النعم", "العدل في الحكم"],
        "lessons_en": ["Courage for Allah's sake", "Gratitude for blessings", "Justice in judgment"],
    },

    # =========================================================================
    # LUQMAN
    # =========================================================================
    {
        "id": "cluster_luqman",
        "title_ar": "لقمان الحكيم",
        "title_en": "Luqman the Wise",
        "short_title_ar": "لقمان",
        "short_title_en": "Luqman",
        "category": "named_char",
        "main_persons": ["Luqman", "Luqman's Son"],
        "groups": [],
        "tags": ["wisdom", "advice", "parenting", "gratitude", "tawhid"],
        "places": [],
        "era": "unknown",
        "era_basis": "unknown",
        "ayah_spans": [{"sura": 31, "start": 12, "end": 19}],
        "primary_sura": 31,
        "summary_ar": "لقمان أُوتي الحكمة، ونصائحه الخالدة لابنه",
        "summary_en": "Luqman was given wisdom, his timeless advice to his son.",
        "lessons_ar": ["الحكمة من الله", "نصيحة الوالد للولد", "التواضع وعدم الكبر"],
        "lessons_en": ["Wisdom is from Allah", "Father's advice to son", "Humility, avoiding arrogance"],
    },

    # =========================================================================
    # QARUN (Korah)
    # =========================================================================
    {
        "id": "cluster_qarun",
        "title_ar": "قارون",
        "title_en": "Qarun (Korah)",
        "short_title_ar": "قارون",
        "short_title_en": "Qarun",
        "category": "named_char",
        "main_persons": ["Qarun"],
        "groups": ["Bani Israil"],
        "tags": ["wealth", "arrogance", "swallowing", "destruction", "lesson"],
        "places": [{"name": "Egypt", "name_ar": "مصر", "basis": "inferred"}],
        "era": "egypt",
        "era_basis": "inferred",
        "time_description_en": "Contemporary of Musa",
        "ayah_spans": [{"sura": 28, "start": 76, "end": 82}, {"sura": 29, "start": 39, "end": 40}],
        "primary_sura": 28,
        "summary_ar": "قارون من قوم موسى، تكبر بكنوزه فخسف الله به الأرض",
        "summary_en": "Qarun from Musa's people, arrogant with his treasures, Allah caused earth to swallow him.",
        "lessons_ar": ["المال فتنة", "التكبر يُهلك", "العاقبة للمتقين"],
        "lessons_en": ["Wealth is a trial", "Arrogance destroys", "Good end for the righteous"],
    },

    # =========================================================================
    # ASHAB AL-FIL (People of the Elephant)
    # =========================================================================
    {
        "id": "cluster_elephant",
        "title_ar": "أصحاب الفيل",
        "title_en": "People of the Elephant",
        "short_title_ar": "الفيل",
        "short_title_en": "Elephant",
        "category": "historical",
        "main_persons": ["Abraha"],
        "groups": ["Abyssinian Army"],
        "tags": ["kaaba", "protection", "birds", "miracle", "destruction"],
        "places": [{"name": "Makkah", "name_ar": "مكة", "basis": "explicit"}],
        "era": "pre_islamic",
        "era_basis": "explicit",
        "time_description_en": "Year of the Prophet's birth (~570 CE)",
        "ayah_spans": [{"sura": 105, "start": 1, "end": 5}],
        "primary_sura": 105,
        "summary_ar": "أبرهة وجيشه جاءوا لهدم الكعبة، فأرسل الله طيراً أبابيل",
        "summary_en": "Abraha and his army came to destroy Ka'bah, Allah sent birds with stones.",
        "lessons_ar": ["الله يحمي بيته", "الحيل لا تنفع ضد قدر الله"],
        "lessons_en": ["Allah protects His House", "Schemes don't work against Allah's decree"],
    },

    # =========================================================================
    # ASHAB AL-UKHDUD (People of the Ditch)
    # =========================================================================
    {
        "id": "cluster_ukhdud",
        "title_ar": "أصحاب الأخدود",
        "title_en": "People of the Ditch",
        "short_title_ar": "الأخدود",
        "short_title_en": "Ditch",
        "category": "historical",
        "main_persons": ["The Boy", "The King", "The Sorcerer", "The Monk"],
        "groups": ["Believers"],
        "tags": ["martyrdom", "persecution", "faith", "fire", "sacrifice"],
        "places": [{"name": "Najran (Yemen)", "name_ar": "نجران", "basis": "inferred"}],
        "era": "pre_islamic",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 85, "start": 4, "end": 9}],
        "primary_sura": 85,
        "summary_ar": "مؤمنون أُلقوا في النار في أخاديد، وصبروا على دينهم",
        "summary_en": "Believers thrown into fire-filled ditches, they remained steadfast in faith.",
        "lessons_ar": ["الشهادة في سبيل الله", "الثبات على الإيمان"],
        "lessons_en": ["Martyrdom for Allah's sake", "Steadfastness in faith"],
    },

    # =========================================================================
    # HABIL & QABIL (Two Sons of Adam)
    # =========================================================================
    {
        "id": "cluster_habil_qabil",
        "title_ar": "هابيل وقابيل",
        "title_en": "Habil and Qabil (Abel and Cain)",
        "short_title_ar": "ابنا آدم",
        "short_title_en": "Sons of Adam",
        "category": "historical",
        "main_persons": ["Habil (Abel)", "Qabil (Cain)", "Adam"],
        "groups": [],
        "tags": ["first_murder", "jealousy", "sacrifice", "regret", "crow"],
        "places": [],
        "era": "primordial",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 5, "start": 27, "end": 31}],
        "primary_sura": 5,
        "summary_ar": "أول قتل في التاريخ: قابيل قتل هابيل حسداً",
        "summary_en": "The first murder in history: Cain killed Abel out of jealousy.",
        "lessons_ar": ["الحسد يُهلك", "قتل نفس كقتل الناس جميعاً"],
        "lessons_en": ["Jealousy destroys", "Killing one soul is like killing all humanity"],
    },

    # =========================================================================
    # YUNUS (Jonah)
    # =========================================================================
    {
        "id": "cluster_yunus",
        "title_ar": "يونس",
        "title_en": "Prophet Yunus (Jonah)",
        "short_title_ar": "يونس",
        "short_title_en": "Yunus",
        "category": "prophet",
        "main_persons": ["Yunus"],
        "groups": ["People of Yunus"],
        "tags": ["whale", "repentance", "patience", "darkness", "forgiveness"],
        "places": [{"name": "Nineveh", "name_ar": "نينوى", "basis": "inferred"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 10, "start": 98, "end": 98},
            {"sura": 21, "start": 87, "end": 88},
            {"sura": 37, "start": 139, "end": 148},
            {"sura": 68, "start": 48, "end": 50}
        ],
        "primary_sura": 37,
        "summary_ar": "يونس غادب فالتقمه الحوت، فسبح في الظلمات فنجاه الله",
        "summary_en": "Yunus left angry, swallowed by whale, glorified Allah in darkness, was saved.",
        "lessons_ar": ["لا تغادب من قدر الله", "الدعاء في الشدة", "التسبيح ينجي"],
        "lessons_en": ["Don't be angry at Allah's decree", "Dua in hardship", "Tasbeeh saves"],
    },

    # =========================================================================
    # AYYUB (Job)
    # =========================================================================
    {
        "id": "cluster_ayyub",
        "title_ar": "أيوب",
        "title_en": "Prophet Ayyub (Job)",
        "short_title_ar": "أيوب",
        "short_title_en": "Ayyub",
        "category": "prophet",
        "main_persons": ["Ayyub"],
        "groups": [],
        "tags": ["patience", "illness", "test", "healing", "gratitude"],
        "places": [],
        "era": "ancient",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 21, "start": 83, "end": 84},
            {"sura": 38, "start": 41, "end": 44}
        ],
        "primary_sura": 38,
        "summary_ar": "أيوب ابتُلي بالمرض فصبر، ثم شفاه الله وأعاد له أهله",
        "summary_en": "Ayyub was tested with illness, remained patient, Allah healed him and restored his family.",
        "lessons_ar": ["الصبر الجميل", "الابتلاء اختبار", "الفرج بعد الشدة"],
        "lessons_en": ["Beautiful patience", "Trial is a test", "Relief after hardship"],
    },

    # =========================================================================
    # SHUAYB & MADYAN
    # =========================================================================
    {
        "id": "cluster_shuayb_madyan",
        "title_ar": "شعيب ومدين",
        "title_en": "Prophet Shu'ayb and Madyan",
        "short_title_ar": "شعيب",
        "short_title_en": "Shu'ayb",
        "category": "nation",
        "main_persons": ["Shu'ayb"],
        "groups": ["People of Madyan", "Ashab al-Aykah"],
        "tags": ["honesty", "fraud", "weights_measures", "earthquake", "business"],
        "places": [{"name": "Madyan", "name_ar": "مدين", "basis": "explicit"}],
        "era": "ancient",
        "era_basis": "inferred",
        "time_description_en": "Before Musa (who later married Shu'ayb's daughter)",
        "ayah_spans": [
            {"sura": 7, "start": 85, "end": 93},
            {"sura": 11, "start": 84, "end": 95},
            {"sura": 26, "start": 176, "end": 191},
            {"sura": 29, "start": 36, "end": 37}
        ],
        "primary_sura": 11,
        "summary_ar": "شعيب دعا قومه لترك الغش في الميزان، فكذبوه فأهلكهم الله",
        "summary_en": "Shu'ayb called his people to stop cheating in measures, they rejected him, Allah destroyed them.",
        "lessons_ar": ["الأمانة في التجارة", "الغش يجلب العذاب"],
        "lessons_en": ["Honesty in business", "Fraud brings punishment"],
    },

    # =========================================================================
    # ZAKARIYYA & YAHYA
    # =========================================================================
    {
        "id": "cluster_zakariyya_yahya",
        "title_ar": "زكريا ويحيى",
        "title_en": "Prophets Zakariyya and Yahya",
        "short_title_ar": "زكريا ويحيى",
        "short_title_en": "Zakariyya & Yahya",
        "category": "prophet",
        "main_persons": ["Zakariyya", "Yahya", "Wife of Zakariyya"],
        "groups": ["Bani Israil"],
        "tags": ["miracle_child", "old_age", "prayer", "piety"],
        "places": [{"name": "Bayt al-Maqdis", "name_ar": "بيت المقدس", "basis": "inferred"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 3, "start": 37, "end": 41},
            {"sura": 19, "start": 2, "end": 15},
            {"sura": 21, "start": 89, "end": 90}
        ],
        "primary_sura": 19,
        "summary_ar": "زكريا دعا الله وهو كبير فرزقه يحيى",
        "summary_en": "Zakariyya prayed to Allah in old age, was granted Yahya.",
        "lessons_ar": ["الدعاء مستجاب", "لا ييأس من رحمة الله"],
        "lessons_en": ["Dua is answered", "Never despair of Allah's mercy"],
    },

    # =========================================================================
    # ASHAB AL-JANNAH (Owners of the Garden - Surah 68)
    # =========================================================================
    {
        "id": "cluster_ashab_jannah",
        "title_ar": "أصحاب الجنة",
        "title_en": "Owners of the Garden",
        "short_title_ar": "أصحاب الجنة",
        "short_title_en": "Garden Owners",
        "category": "parable",
        "main_persons": [],
        "groups": ["Garden Owners"],
        "tags": ["charity", "greed", "destruction", "regret", "lesson"],
        "places": [],
        "era": "unknown",
        "era_basis": "unknown",
        "ayah_spans": [{"sura": 68, "start": 17, "end": 33}],
        "primary_sura": 68,
        "summary_ar": "أصحاب جنة أقسموا أن يحصدوها دون إعطاء المساكين، فأحرقها الله",
        "summary_en": "Garden owners swore to harvest without giving to the poor, Allah burned it.",
        "lessons_ar": ["البخل يُهلك", "حق الفقير في المال"],
        "lessons_en": ["Stinginess destroys", "The poor have rights in wealth"],
    },

    # =========================================================================
    # SABBATH BREAKERS
    # =========================================================================
    {
        "id": "cluster_sabbath_breakers",
        "title_ar": "أصحاب السبت",
        "title_en": "Sabbath Breakers",
        "short_title_ar": "أصحاب السبت",
        "short_title_en": "Sabbath",
        "category": "historical",
        "main_persons": [],
        "groups": ["Bani Israil", "Village by the Sea"],
        "tags": ["disobedience", "fishing", "apes", "transformation", "warning"],
        "places": [{"name": "Coastal village", "name_ar": "القرية الساحلية", "basis": "inferred"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [
            {"sura": 2, "start": 65, "end": 66},
            {"sura": 7, "start": 163, "end": 166}
        ],
        "primary_sura": 7,
        "summary_ar": "قرية من بني إسرائيل خالفوا أمر السبت فصيدوا الحيتان، فمسخهم الله قردة",
        "summary_en": "A village of Bani Israil violated Sabbath by fishing, Allah transformed them into apes.",
        "lessons_ar": ["طاعة الأوامر واجبة", "الحيلة لا تُسقط الحكم"],
        "lessons_en": ["Obedience to commands is obligatory", "Tricks don't invalidate rulings"],
    },

    # =========================================================================
    # BAQARAH (The Cow)
    # =========================================================================
    {
        "id": "cluster_baqarah_cow",
        "title_ar": "بقرة بني إسرائيل",
        "title_en": "The Cow of Bani Israil",
        "short_title_ar": "البقرة",
        "short_title_en": "The Cow",
        "category": "historical",
        "main_persons": ["Musa"],
        "groups": ["Bani Israil"],
        "tags": ["murder", "miracle", "cow", "revelation", "obedience"],
        "places": [],
        "era": "egypt",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 2, "start": 67, "end": 73}],
        "primary_sura": 2,
        "summary_ar": "أمر الله بني إسرائيل بذبح بقرة لكشف قاتل، فتلكأوا وسألوا كثيراً",
        "summary_en": "Allah commanded Bani Israil to slaughter a cow to reveal a murderer, they delayed with many questions.",
        "lessons_ar": ["عدم التنطع في الدين", "السمع والطاعة"],
        "lessons_en": ["Don't over-complicate religion", "Hear and obey"],
    },

    # =========================================================================
    # ADAM
    # =========================================================================
    {
        "id": "cluster_adam",
        "title_ar": "آدم",
        "title_en": "Prophet Adam",
        "short_title_ar": "آدم",
        "short_title_en": "Adam",
        "category": "prophet",
        "main_persons": ["Adam", "Hawwa (Eve)", "Iblis"],
        "groups": ["Angels"],
        "tags": ["creation", "prostration", "forbidden_tree", "repentance", "khalifah"],
        "places": [{"name": "Jannah (Paradise)", "name_ar": "الجنة", "basis": "explicit"}],
        "era": "primordial",
        "era_basis": "explicit",
        "ayah_spans": [
            {"sura": 2, "start": 30, "end": 39},
            {"sura": 7, "start": 11, "end": 25},
            {"sura": 15, "start": 26, "end": 44},
            {"sura": 17, "start": 61, "end": 65},
            {"sura": 20, "start": 115, "end": 124},
            {"sura": 38, "start": 71, "end": 85}
        ],
        "primary_sura": 7,
        "summary_ar": "خلق آدم خليفة، سجود الملائكة، إبليس أبى، الشجرة والهبوط",
        "summary_en": "Adam created as khalifah, angels prostrated, Iblis refused, the tree and descent.",
        "lessons_ar": ["التوبة تُغفر", "عداوة الشيطان", "آدم أبو البشر"],
        "lessons_en": ["Repentance is forgiven", "Satan's enmity", "Adam is father of humanity"],
    },

    # =========================================================================
    # UZAIR
    # =========================================================================
    {
        "id": "cluster_uzair",
        "title_ar": "عزير",
        "title_en": "Uzair (Ezra)",
        "short_title_ar": "عزير",
        "short_title_en": "Uzair",
        "category": "named_char",
        "main_persons": ["Uzair"],
        "groups": [],
        "tags": ["resurrection", "hundred_years", "donkey", "miracle"],
        "places": [{"name": "Village (ruined)", "name_ar": "قرية خاوية", "basis": "explicit"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 2, "start": 259, "end": 259}],
        "primary_sura": 2,
        "summary_ar": "رجل أماته الله مئة عام ثم بعثه ليريه كيف يحيي الموتى",
        "summary_en": "A man whom Allah caused to die for 100 years then resurrected, showing how He revives the dead.",
        "lessons_ar": ["الله قادر على الإحياء", "البعث حق"],
        "lessons_en": ["Allah can resurrect", "Resurrection is true"],
    },

    # =========================================================================
    # TALUT & JALUT
    # =========================================================================
    {
        "id": "cluster_talut_jalut",
        "title_ar": "طالوت وجالوت",
        "title_en": "Talut and Jalut (Saul and Goliath)",
        "short_title_ar": "طالوت وجالوت",
        "short_title_en": "Talut vs Jalut",
        "category": "historical",
        "main_persons": ["Talut (Saul)", "Jalut (Goliath)", "Dawud"],
        "groups": ["Bani Israil"],
        "tags": ["kingship", "river_test", "battle", "patience", "victory"],
        "places": [{"name": "Palestine", "name_ar": "فلسطين", "basis": "inferred"}],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 2, "start": 246, "end": 252}],
        "primary_sura": 2,
        "summary_ar": "طالوت مَلَك بني إسرائيل، امتحان النهر، داود قتل جالوت",
        "summary_en": "Talut became king of Bani Israil, river test, Dawud killed Goliath.",
        "lessons_ar": ["الملك ليس بالمال بل بالعلم", "الصبر في القتال"],
        "lessons_en": ["Kingship is not about wealth but knowledge", "Patience in battle"],
    },

    # =========================================================================
    # COMPANIONS OF THE PROPHET (Ashab)
    # =========================================================================
    {
        "id": "cluster_uhud_hypocrites",
        "title_ar": "غزوة أحد والمنافقون",
        "title_en": "Battle of Uhud & Hypocrites",
        "short_title_ar": "أحد",
        "short_title_en": "Uhud",
        "category": "historical",
        "main_persons": ["Prophet Muhammad", "Companions"],
        "groups": ["Muslims", "Quraysh", "Hypocrites"],
        "tags": ["battle", "test", "patience", "hypocrites", "archers"],
        "places": [{"name": "Uhud Mountain", "name_ar": "جبل أحد", "basis": "explicit"}],
        "era": "pre_islamic",
        "era_basis": "explicit",
        "time_description_en": "3 AH, prophetic era",
        "ayah_spans": [{"sura": 3, "start": 121, "end": 175}],
        "primary_sura": 3,
        "summary_ar": "غزوة أحد وتحول المعركة وانكشاف المنافقين",
        "summary_en": "Battle of Uhud, turning of battle tide, exposure of hypocrites.",
        "lessons_ar": ["الطاعة للقائد", "الثبات عند المحن", "الابتلاء سنة"],
        "lessons_en": ["Obedience to leader", "Steadfastness in trials", "Testing is divine way"],
    },

    # =========================================================================
    # IFRIT & SULAYMAN'S THRONE
    # =========================================================================
    {
        "id": "cluster_sheba_throne",
        "title_ar": "عرش سبأ",
        "title_en": "Throne of Sheba",
        "short_title_ar": "عرش بلقيس",
        "short_title_en": "Sheba Throne",
        "category": "historical",
        "main_persons": ["Sulayman", "Queen of Sheba", "Ifrit", "One with Knowledge"],
        "groups": ["Jinn"],
        "tags": ["throne", "speed", "knowledge", "submission"],
        "places": [
            {"name": "Sheba (Yemen)", "name_ar": "سبأ", "basis": "explicit"},
            {"name": "Jerusalem", "name_ar": "القدس", "basis": "inferred"}
        ],
        "era": "israelite",
        "era_basis": "inferred",
        "ayah_spans": [{"sura": 27, "start": 38, "end": 44}],
        "primary_sura": 27,
        "summary_ar": "سليمان يطلب عرش بلقيس، عرض العفريت ثم من عنده علم الكتاب",
        "summary_en": "Sulayman requests Sheba's throne, Ifrit offers, one with knowledge of the Book brings it instantly.",
        "lessons_ar": ["العلم أقوى من القوة", "الخضوع للحق"],
        "lessons_en": ["Knowledge is stronger than force", "Submission to truth"],
    },

    # =========================================================================
    # AL-ISRA (NIGHT JOURNEY)
    # =========================================================================
    {
        "id": "cluster_isra_miraj",
        "title_ar": "الإسراء والمعراج",
        "title_en": "The Night Journey (Al-Isra)",
        "short_title_ar": "الإسراء",
        "short_title_en": "Night Journey",
        "category": "prophet",
        "main_persons": ["Muhammad"],
        "groups": ["Angels", "Prophets"],
        "tags": ["miracle", "journey", "ascension", "prayer", "blessing"],
        "places": [
            {"name": "Masjid al-Haram (Mecca)", "name_ar": "المسجد الحرام", "basis": "explicit"},
            {"name": "Masjid al-Aqsa (Jerusalem)", "name_ar": "المسجد الأقصى", "basis": "explicit"}
        ],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "Occurred during the Meccan period, before the Hijrah",
        "ayah_spans": [{"sura": 17, "start": 1, "end": 1}],
        "primary_sura": 17,
        "summary_ar": "رحلة النبي ﷺ الليلية من المسجد الحرام إلى المسجد الأقصى، ثم العروج إلى السماوات العلى",
        "summary_en": "The Prophet's miraculous night journey from Mecca to Jerusalem, then ascension through the heavens.",
        "lessons_ar": ["قدرة الله المطلقة", "مكانة المسجد الأقصى", "فرضية الصلاة"],
        "lessons_en": ["Allah's absolute power", "Importance of Al-Aqsa", "Obligation of prayer established"],
    },

    # =========================================================================
    # BATTLE OF BADR
    # =========================================================================
    {
        "id": "cluster_badr",
        "title_ar": "غزوة بدر الكبرى",
        "title_en": "Battle of Badr",
        "short_title_ar": "بدر",
        "short_title_en": "Badr",
        "category": "historical",
        "main_persons": ["Muhammad", "Abu Jahl", "Believers"],
        "groups": ["Muslims", "Quraysh", "Angels"],
        "tags": ["battle", "victory", "angels", "divine_help", "faith"],
        "places": [{"name": "Badr", "name_ar": "بدر", "basis": "explicit"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "2 AH (624 CE), 17th of Ramadan",
        "ayah_spans": [
            {"sura": 8, "start": 5, "end": 19},
            {"sura": 8, "start": 41, "end": 44},
            {"sura": 3, "start": 123, "end": 127}
        ],
        "primary_sura": 8,
        "summary_ar": "أول معركة فاصلة في الإسلام، انتصر فيها المسلمون على قريش بنصر من الله ودعم الملائكة",
        "summary_en": "The first decisive battle in Islam where Muslims, with divine support and angels, defeated Quraysh.",
        "lessons_ar": ["النصر من عند الله", "قلة العدد لا تمنع النصر", "التوكل على الله"],
        "lessons_en": ["Victory is from Allah", "Small numbers don't prevent victory", "Reliance on Allah"],
    },

    # =========================================================================
    # PROPHET IDRIS
    # =========================================================================
    {
        "id": "cluster_idris",
        "title_ar": "قصة إدريس عليه السلام",
        "title_en": "Prophet Idris (Enoch)",
        "short_title_ar": "إدريس",
        "short_title_en": "Idris",
        "category": "prophet",
        "main_persons": ["Idris"],
        "groups": [],
        "tags": ["prophet", "truthfulness", "elevated", "patience"],
        "places": [],
        "era": "unknown",
        "era_basis": "unknown",
        "time_description_en": "Early prophet, possibly before Nuh (Noah)",
        "ayah_spans": [
            {"sura": 19, "start": 56, "end": 57},
            {"sura": 21, "start": 85, "end": 85}
        ],
        "primary_sura": 19,
        "summary_ar": "كان صديقاً نبياً ورفعه الله مكاناً علياً",
        "summary_en": "A prophet of truth whom Allah raised to a high station.",
        "lessons_ar": ["الصدق من صفات الأنبياء", "الله يرفع من يشاء"],
        "lessons_en": ["Truthfulness is a quality of prophets", "Allah elevates whom He wills"],
    },

    # =========================================================================
    # CONQUEST OF MECCA (AL-FATH)
    # =========================================================================
    {
        "id": "cluster_fath_mecca",
        "title_ar": "فتح مكة",
        "title_en": "Conquest of Mecca",
        "short_title_ar": "الفتح",
        "short_title_en": "Conquest",
        "category": "historical",
        "main_persons": ["Muhammad"],
        "groups": ["Muslims", "Quraysh"],
        "tags": ["victory", "forgiveness", "idols", "kaaba", "peace"],
        "places": [{"name": "Mecca", "name_ar": "مكة", "basis": "explicit"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "8 AH (630 CE)",
        "ayah_spans": [{"sura": 48, "start": 1, "end": 29}],
        "primary_sura": 48,
        "summary_ar": "دخل النبي ﷺ مكة فاتحاً منتصراً، وطهر الكعبة من الأصنام وعفا عن أهل مكة",
        "summary_en": "The Prophet entered Mecca victorious, cleansed the Ka'bah of idols, and pardoned the people of Mecca.",
        "lessons_ar": ["العفو عند المقدرة", "نصر الله للمؤمنين", "تطهير بيت الله"],
        "lessons_en": ["Forgiveness when in power", "Allah's victory for believers", "Purifying Allah's House"],
    },

    # =========================================================================
    # STORY OF IFK (ACCUSATION)
    # =========================================================================
    {
        "id": "cluster_ifk",
        "title_ar": "حادثة الإفك",
        "title_en": "The Incident of Ifk (Slander)",
        "short_title_ar": "الإفك",
        "short_title_en": "The Slander",
        "category": "historical",
        "main_persons": ["Aisha"],
        "groups": ["Hypocrites", "Believers"],
        "tags": ["slander", "innocence", "patience", "revelation", "honor"],
        "places": [],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "5 or 6 AH, after a military expedition",
        "ayah_spans": [{"sura": 24, "start": 11, "end": 26}],
        "primary_sura": 24,
        "summary_ar": "الافتراء الكاذب على أم المؤمنين عائشة رضي الله عنها وبراءتها من السماء",
        "summary_en": "The false accusation against Aisha and her vindication through divine revelation.",
        "lessons_ar": ["حفظ الأعراض", "عدم نشر الإشاعات", "براءة الصادقين"],
        "lessons_en": ["Protecting honor", "Not spreading rumors", "Innocence of the truthful"],
    },

    # =========================================================================
    # TREATY OF HUDAYBIYYAH
    # =========================================================================
    {
        "id": "cluster_hudaybiyyah",
        "title_ar": "صلح الحديبية",
        "title_en": "Treaty of Hudaybiyyah",
        "short_title_ar": "الحديبية",
        "short_title_en": "Hudaybiyyah",
        "category": "historical",
        "main_persons": ["Muhammad"],
        "groups": ["Muslims", "Quraysh"],
        "tags": ["peace", "treaty", "wisdom", "patience", "victory"],
        "places": [{"name": "Al-Hudaybiyyah", "name_ar": "الحديبية", "basis": "explicit"}],
        "era": "prophetic",
        "era_basis": "explicit",
        "time_description_en": "6 AH (628 CE)",
        "ayah_spans": [{"sura": 48, "start": 1, "end": 29}],
        "primary_sura": 48,
        "summary_ar": "معاهدة الصلح بين المسلمين وقريش، التي سماها الله فتحاً مبيناً",
        "summary_en": "The peace treaty between Muslims and Quraysh, which Allah called a clear victory.",
        "lessons_ar": ["الصلح خير", "النصر قد يأتي بالحكمة", "الصبر على أمر الله"],
        "lessons_en": ["Peace is better", "Victory may come through wisdom", "Patience with Allah's decree"],
    },
]

# =============================================================================
# STORY EVENTS DATA (Sample for key clusters)
# =============================================================================

STORY_EVENTS = {
    # =========================================================================
    # CLUSTER: CAVE SLEEPERS (18:9-26)
    # =========================================================================
    "cluster_cave_sleepers": [
        {
            "id": "cluster_cave_sleepers:intro",
            "title_ar": "السؤال عن أصحاب الكهف",
            "title_en": "The Question About Cave Sleepers",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 18, "aya_start": 9, "aya_end": 9,
            "is_entry_point": True,
            "summary_ar": "أصحاب الكهف والرقيم من آيات الله العجيبة",
            "summary_en": "The companions of the cave and inscription are among Allah's wondrous signs.",
            "semantic_tags": ["signs", "wonder"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:9", "snippet": "Do you think that the people of the cave and the inscription were among Our wondrous signs?"}],
        },
        {
            "id": "cluster_cave_sleepers:flight",
            "title_ar": "الفرار إلى الكهف",
            "title_en": "Flight to the Cave",
            "narrative_role": "migration",
            "chronological_index": 2,
            "sura_no": 18, "aya_start": 10, "aya_end": 12,
            "is_entry_point": False,
            "summary_ar": "فتية آمنوا بربهم ففروا إلى الكهف طالبين رحمة الله",
            "summary_en": "Young men who believed in their Lord fled to the cave seeking Allah's mercy.",
            "semantic_tags": ["faith", "youth", "escape"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:10", "snippet": "When the youths fled for refuge to the cave and said: Our Lord! Bestow on us mercy from Yourself."}],
        },
        {
            "id": "cluster_cave_sleepers:sleep",
            "title_ar": "النوم الطويل",
            "title_en": "The Long Sleep",
            "narrative_role": "miracle",
            "chronological_index": 3,
            "sura_no": 18, "aya_start": 11, "aya_end": 12,
            "is_entry_point": False,
            "summary_ar": "ضرب الله على آذانهم في الكهف سنين عدداً",
            "summary_en": "Allah sealed their ears (made them sleep) in the cave for years.",
            "semantic_tags": ["miracle", "sleep", "protection"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:11", "snippet": "We sealed up their hearing in the cave for a number of years."}],
        },
        {
            "id": "cluster_cave_sleepers:awakening",
            "title_ar": "الاستيقاظ",
            "title_en": "The Awakening",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 18, "aya_start": 19, "aya_end": 21,
            "is_entry_point": False,
            "summary_ar": "بعثهم الله ليتساءلوا بينهم، وأرسلوا أحدهم بورقهم إلى المدينة",
            "summary_en": "Allah raised them to question among themselves, sent one with coins to the city.",
            "semantic_tags": ["awakening", "discovery"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:19", "snippet": "We raised them up that they might question one another. A speaker among them said: How long have you tarried?"}],
        },
        {
            "id": "cluster_cave_sleepers:duration",
            "title_ar": "مدة اللبث",
            "title_en": "The Duration",
            "narrative_role": "reflection",
            "chronological_index": 5,
            "sura_no": 18, "aya_start": 25, "aya_end": 26,
            "is_entry_point": False,
            "summary_ar": "لبثوا في كهفهم ثلاثمائة سنين وازدادوا تسعاً",
            "summary_en": "They remained in their cave 300 years, and add 9 (309 lunar years).",
            "semantic_tags": ["time", "miracle", "lesson"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:25", "snippet": "They stayed in their cave three hundred years, and add nine."}],
        },
    ],

    # =========================================================================
    # CLUSTER: TWO GARDENS (18:32-44)
    # =========================================================================
    "cluster_two_gardens": [
        {
            "id": "cluster_two_gardens:parable_intro",
            "title_ar": "مثل الرجلين",
            "title_en": "The Parable of Two Men",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 18, "aya_start": 32, "aya_end": 34,
            "is_entry_point": True,
            "summary_ar": "مثل رجلين: أحدهما أوتي جنتين من أعناب",
            "summary_en": "Parable of two men: one given two gardens of grapes.",
            "semantic_tags": ["parable", "wealth"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:32", "snippet": "Set forth to them the parable of two men: for one of them We made two gardens of grapes."}],
        },
        {
            "id": "cluster_two_gardens:arrogance",
            "title_ar": "التكبر والإنكار",
            "title_en": "Arrogance and Denial",
            "narrative_role": "confrontation",
            "chronological_index": 2,
            "sura_no": 18, "aya_start": 35, "aya_end": 36,
            "is_entry_point": False,
            "summary_ar": "دخل جنته وهو ظالم لنفسه، أنكر الساعة",
            "summary_en": "He entered his garden wronging himself, denied the Hour.",
            "semantic_tags": ["arrogance", "denial", "kufr"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:35", "snippet": "He went into his garden wronging himself. He said: I think not that this will ever perish."}],
        },
        {
            "id": "cluster_two_gardens:warning",
            "title_ar": "نصيحة الصاحب",
            "title_en": "The Companion's Advice",
            "narrative_role": "warning",
            "chronological_index": 3,
            "sura_no": 18, "aya_start": 37, "aya_end": 41,
            "is_entry_point": False,
            "summary_ar": "قال له صاحبه: أكفرت بالذي خلقك؟ لولا إذ دخلت جنتك قلت ما شاء الله",
            "summary_en": "His companion said: Do you disbelieve in Him who created you? If only you had said 'What Allah wills!'",
            "semantic_tags": ["advice", "reminder", "mashallah"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:37", "snippet": "His companion said to him while arguing: Do you disbelieve in Him who created you from dust?"}],
        },
        {
            "id": "cluster_two_gardens:destruction",
            "title_ar": "الهلاك",
            "title_en": "The Destruction",
            "narrative_role": "outcome",
            "chronological_index": 4,
            "sura_no": 18, "aya_start": 42, "aya_end": 43,
            "is_entry_point": False,
            "summary_ar": "أحيط بثمره فأصبح يقلب كفيه على ما أنفق فيها",
            "summary_en": "His fruits were encompassed (destroyed), he wrung his hands over what he had spent.",
            "semantic_tags": ["destruction", "regret"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:42", "snippet": "And his fruits were encompassed, so he began wringing his hands over what he had spent on it."}],
        },
        {
            "id": "cluster_two_gardens:lesson",
            "title_ar": "الدرس",
            "title_en": "The Lesson",
            "narrative_role": "reflection",
            "chronological_index": 5,
            "sura_no": 18, "aya_start": 44, "aya_end": 44,
            "is_entry_point": False,
            "summary_ar": "الولاية لله الحق، هو خير ثواباً وخير عقباً",
            "summary_en": "Protection is from Allah the True. He is best in reward and best in outcome.",
            "semantic_tags": ["lesson", "truth", "protection"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:44", "snippet": "There, protection is from Allah, the True. He is best for reward and best for outcome."}],
        },
    ],

    # =========================================================================
    # CLUSTER: MUSA & KHIDR (18:60-82)
    # =========================================================================
    "cluster_musa_khidr": [
        {
            "id": "cluster_musa_khidr:journey_begins",
            "title_ar": "بداية الرحلة",
            "title_en": "Journey Begins",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 18, "aya_start": 60, "aya_end": 64,
            "is_entry_point": True,
            "summary_ar": "موسى يرحل مع فتاه طلباً للعلم حتى مجمع البحرين",
            "summary_en": "Musa travels with his young companion seeking knowledge to the junction of two seas.",
            "semantic_tags": ["journey", "knowledge_seeking"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:60", "snippet": "When Musa said to his young companion: I will not give up until I reach the junction of the two seas."}],
        },
        {
            "id": "cluster_musa_khidr:meeting_khidr",
            "title_ar": "لقاء الخضر",
            "title_en": "Meeting Khidr",
            "narrative_role": "encounter",
            "chronological_index": 2,
            "sura_no": 18, "aya_start": 65, "aya_end": 70,
            "is_entry_point": False,
            "summary_ar": "لقاء موسى بعبد من عباد الله أوتي رحمة وعلماً من لدنه",
            "summary_en": "Musa meets a servant whom Allah granted mercy and knowledge from Himself.",
            "semantic_tags": ["meeting", "special_knowledge"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:65", "snippet": "They found a servant from among Our servants to whom We had given mercy and taught him knowledge from Us."}],
        },
        {
            "id": "cluster_musa_khidr:ship",
            "title_ar": "السفينة",
            "title_en": "The Ship",
            "narrative_role": "trial",
            "chronological_index": 3,
            "sura_no": 18, "aya_start": 71, "aya_end": 73,
            "is_entry_point": False,
            "summary_ar": "خرقا السفينة - الحكمة: حمايتها من ملك غاصب",
            "summary_en": "They damaged the ship - Wisdom: protecting it from a tyrant king.",
            "semantic_tags": ["test", "hidden_wisdom", "ship"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:71", "snippet": "He made a hole in it. Musa said: Have you made a hole to drown its people?"}],
        },
        {
            "id": "cluster_musa_khidr:boy",
            "title_ar": "الغلام",
            "title_en": "The Boy",
            "narrative_role": "trial",
            "chronological_index": 4,
            "sura_no": 18, "aya_start": 74, "aya_end": 76,
            "is_entry_point": False,
            "summary_ar": "قتل الغلام - الحكمة: كان سيُرهق والديه بالكفر والطغيان",
            "summary_en": "The boy killed - Wisdom: he would burden parents with disbelief and transgression.",
            "semantic_tags": ["test", "hidden_wisdom", "fate"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:74", "snippet": "He killed him. Musa said: Have you killed an innocent soul without him having killed anyone?"}],
        },
        {
            "id": "cluster_musa_khidr:wall",
            "title_ar": "الجدار",
            "title_en": "The Wall",
            "narrative_role": "trial",
            "chronological_index": 5,
            "sura_no": 18, "aya_start": 77, "aya_end": 78,
            "is_entry_point": False,
            "summary_ar": "إقامة الجدار - الحكمة: حماية كنز يتيمين صالحين",
            "summary_en": "Wall erected - Wisdom: protecting treasure of two righteous orphans.",
            "semantic_tags": ["test", "hidden_wisdom", "orphans"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:77", "snippet": "They found a wall about to collapse, so he set it straight."}],
        },
        {
            "id": "cluster_musa_khidr:explanation",
            "title_ar": "التأويل",
            "title_en": "The Explanation",
            "narrative_role": "reflection",
            "chronological_index": 6,
            "sura_no": 18, "aya_start": 79, "aya_end": 82,
            "is_entry_point": False,
            "summary_ar": "تفسير الأفعال الثلاثة وبيان الحكمة الخفية",
            "summary_en": "Explanation of the three actions and revelation of hidden wisdom.",
            "semantic_tags": ["explanation", "wisdom_revealed"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:82", "snippet": "I did it not of my own accord. This is the interpretation of that about which you could not be patient."}],
        },
    ],

    # =========================================================================
    # CLUSTER: DHUL-QARNAYN (18:83-98) - Already detailed
    # =========================================================================
    "cluster_dhulqarnayn": [
        {
            "id": "cluster_dhulqarnayn:intro",
            "title_ar": "السؤال عن ذي القرنين",
            "title_en": "The Question About Dhul-Qarnayn",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 18, "aya_start": 83, "aya_end": 83,
            "is_entry_point": True,
            "summary_ar": "يُسأل النبي ﷺ عن ذي القرنين",
            "summary_en": "The Prophet is asked about Dhul-Qarnayn.",
            "semantic_tags": ["question", "revelation"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:83", "snippet": "They ask you about Dhul-Qarnayn."}],
        },
        {
            "id": "cluster_dhulqarnayn:empowerment",
            "title_ar": "التمكين الإلهي",
            "title_en": "Divine Empowerment",
            "narrative_role": "divine_intervention",
            "chronological_index": 2,
            "sura_no": 18, "aya_start": 84, "aya_end": 84,
            "is_entry_point": False,
            "summary_ar": "مكّن الله ذا القرنين في الأرض وآتاه من كل شيء سبباً",
            "summary_en": "Allah established him on earth and gave him means to everything.",
            "semantic_tags": ["tamkeen", "power", "means"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:84", "snippet": "We established him in the earth and gave him the means to everything."}],
        },
        {
            "id": "cluster_dhulqarnayn:west",
            "title_ar": "الرحلة إلى الغرب",
            "title_en": "Journey West",
            "narrative_role": "trial",
            "chronological_index": 3,
            "sura_no": 18, "aya_start": 85, "aya_end": 88,
            "is_entry_point": False,
            "summary_ar": "رحل غرباً ووجد قوماً، خُيّر بين العقاب والإحسان فاختار العدل",
            "summary_en": "Traveled west, found a people, chose justice between punishment and kindness.",
            "semantic_tags": ["journey", "justice", "west"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:86", "snippet": "Until, when he reached the setting of the sun, he found it setting in a murky spring."}],
        },
        {
            "id": "cluster_dhulqarnayn:east",
            "title_ar": "الرحلة إلى الشرق",
            "title_en": "Journey East",
            "narrative_role": "trial",
            "chronological_index": 4,
            "sura_no": 18, "aya_start": 89, "aya_end": 91,
            "is_entry_point": False,
            "summary_ar": "رحل شرقاً فوجد قوماً لا ستر لهم، عاملهم بالعدل",
            "summary_en": "Traveled east, found vulnerable people with no shelter, treated them justly.",
            "semantic_tags": ["journey", "east", "restraint"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:90", "snippet": "Until, when he reached the rising of the sun, he found it rising on a people for whom We had not made any shelter."}],
        },
        {
            "id": "cluster_dhulqarnayn:barrier_encounter",
            "title_ar": "لقاء المستضعفين",
            "title_en": "Encounter with the Oppressed",
            "narrative_role": "encounter",
            "chronological_index": 5,
            "sura_no": 18, "aya_start": 92, "aya_end": 94,
            "is_entry_point": False,
            "summary_ar": "وجد قوماً بين جبلين يشكون من يأجوج ومأجوج",
            "summary_en": "Found people between mountains suffering from Yajuj and Majuj.",
            "semantic_tags": ["encounter", "oppressed", "yajuj"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:94", "snippet": "They said: O Dhul-Qarnayn! Yajuj and Majuj are doing great mischief in the land."}],
        },
        {
            "id": "cluster_dhulqarnayn:refuses_tribute",
            "title_ar": "رفض الخراج",
            "title_en": "Refusing Tribute",
            "narrative_role": "dialogue",
            "chronological_index": 6,
            "sura_no": 18, "aya_start": 95, "aya_end": 95,
            "is_entry_point": False,
            "summary_ar": "رفض أخذ المال: ما مكني فيه ربي خير",
            "summary_en": "Refused payment: What my Lord has established me in is better.",
            "semantic_tags": ["tawakkul", "generosity", "selfless"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:95", "snippet": "He said: That in which my Lord has established me is better."}],
        },
        {
            "id": "cluster_dhulqarnayn:barrier",
            "title_ar": "بناء السد",
            "title_en": "Building the Barrier",
            "narrative_role": "outcome",
            "chronological_index": 7,
            "sura_no": 18, "aya_start": 96, "aya_end": 97,
            "is_entry_point": False,
            "summary_ar": "بناء السد من الحديد والنحاس المذاب",
            "summary_en": "Building the barrier from iron and molten copper.",
            "semantic_tags": ["construction", "engineering", "protection"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:96", "snippet": "Bring me blocks of iron - until he had filled up the gap between the mountain-sides."}],
        },
        {
            "id": "cluster_dhulqarnayn:humility",
            "title_ar": "هذا رحمة من ربي",
            "title_en": "This is Mercy from my Lord",
            "narrative_role": "reflection",
            "chronological_index": 8,
            "sura_no": 18, "aya_start": 98, "aya_end": 98,
            "is_entry_point": False,
            "summary_ar": "قال: هذا رحمة من ربي، وأقر بزوال كل شيء",
            "summary_en": "He said: This is mercy from my Lord, acknowledged impermanence of all things.",
            "semantic_tags": ["humility", "tawakkul", "gratitude"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "18:98", "snippet": "He said: This is a mercy from my Lord."}],
        },
    ],

    # =========================================================================
    # CLUSTER: YUSUF (Surah 12) - Key events
    # =========================================================================
    "cluster_yusuf": [
        {
            "id": "cluster_yusuf:dream",
            "title_ar": "رؤيا يوسف",
            "title_en": "Yusuf's Dream",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 12, "aya_start": 4, "aya_end": 6,
            "is_entry_point": True,
            "summary_ar": "رأى يوسف أحد عشر كوكباً والشمس والقمر له ساجدين",
            "summary_en": "Yusuf saw eleven stars, sun and moon prostrating to him.",
            "semantic_tags": ["dream", "prophecy", "signs"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:4", "snippet": "When Yusuf said to his father: O my father! I saw eleven stars and the sun and moon - I saw them prostrating to me."}],
        },
        {
            "id": "cluster_yusuf:brothers_jealousy",
            "title_ar": "حسد الإخوة",
            "title_en": "Brothers' Jealousy",
            "narrative_role": "confrontation",
            "chronological_index": 2,
            "sura_no": 12, "aya_start": 8, "aya_end": 10,
            "is_entry_point": False,
            "summary_ar": "الإخوة يتآمرون على يوسف بسبب الحسد",
            "summary_en": "Brothers plot against Yusuf out of jealousy.",
            "semantic_tags": ["jealousy", "plot", "brothers"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:8", "snippet": "When they said: Yusuf and his brother are more loved by our father than we are."}],
        },
        {
            "id": "cluster_yusuf:well",
            "title_ar": "إلقاؤه في البئر",
            "title_en": "Thrown into the Well",
            "narrative_role": "trial",
            "chronological_index": 3,
            "sura_no": 12, "aya_start": 15, "aya_end": 18,
            "is_entry_point": False,
            "summary_ar": "ألقى الإخوة يوسف في غيابة الجب",
            "summary_en": "Brothers threw Yusuf into the depths of the well.",
            "semantic_tags": ["abandonment", "well", "betrayal"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:15", "snippet": "They put him in the bottom of a well."}],
        },
        {
            "id": "cluster_yusuf:sold_egypt",
            "title_ar": "بيعه وذهابه لمصر",
            "title_en": "Sold and Taken to Egypt",
            "narrative_role": "migration",
            "chronological_index": 4,
            "sura_no": 12, "aya_start": 19, "aya_end": 22,
            "is_entry_point": False,
            "summary_ar": "جاءت قافلة فالتقطته وباعوه في مصر للعزيز",
            "summary_en": "A caravan found him, sold him in Egypt to the Aziz.",
            "semantic_tags": ["caravan", "egypt", "slavery"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:21", "snippet": "The one from Egypt who bought him said to his wife: Treat him honorably."}],
        },
        {
            "id": "cluster_yusuf:temptation",
            "title_ar": "فتنة امرأة العزيز",
            "title_en": "Wife of Aziz's Temptation",
            "narrative_role": "trial",
            "chronological_index": 5,
            "sura_no": 12, "aya_start": 23, "aya_end": 34,
            "is_entry_point": False,
            "summary_ar": "راودته التي هو في بيتها، واستعصم وفر منها",
            "summary_en": "She sought to seduce him, but he resisted and fled from her.",
            "semantic_tags": ["chastity", "temptation", "resistance"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:23", "snippet": "She closed the doors and said: Come! He said: I seek refuge in Allah."}],
        },
        {
            "id": "cluster_yusuf:prison",
            "title_ar": "السجن",
            "title_en": "Prison",
            "narrative_role": "trial",
            "chronological_index": 6,
            "sura_no": 12, "aya_start": 35, "aya_end": 42,
            "is_entry_point": False,
            "summary_ar": "دخل السجن وفسر رؤيا السجينين",
            "summary_en": "Entered prison, interpreted dreams of two prisoners.",
            "semantic_tags": ["prison", "dreams", "patience"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:36", "snippet": "Two young men entered the prison with him. One said: I saw myself pressing wine."}],
        },
        {
            "id": "cluster_yusuf:king_dream",
            "title_ar": "رؤيا الملك",
            "title_en": "King's Dream",
            "narrative_role": "prophecy",
            "chronological_index": 7,
            "sura_no": 12, "aya_start": 43, "aya_end": 49,
            "is_entry_point": False,
            "summary_ar": "فسر يوسف رؤيا الملك: سبع سنين سمان ثم سبع عجاف",
            "summary_en": "Yusuf interpreted king's dream: seven years of plenty, seven of famine.",
            "semantic_tags": ["dream", "interpretation", "prophecy"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:47", "snippet": "He said: You will plant for seven years, and what you harvest leave in its ears."}],
        },
        {
            "id": "cluster_yusuf:power",
            "title_ar": "التمكين في مصر",
            "title_en": "Authority in Egypt",
            "narrative_role": "outcome",
            "chronological_index": 8,
            "sura_no": 12, "aya_start": 54, "aya_end": 57,
            "is_entry_point": False,
            "summary_ar": "صار يوسف على خزائن الأرض",
            "summary_en": "Yusuf was made treasurer of the land.",
            "semantic_tags": ["power", "vindication", "authority"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:55", "snippet": "He said: Set me over the storehouses of the land. I am a knowing guardian."}],
        },
        {
            "id": "cluster_yusuf:brothers_come",
            "title_ar": "مجيء الإخوة",
            "title_en": "Brothers Come",
            "narrative_role": "encounter",
            "chronological_index": 9,
            "sura_no": 12, "aya_start": 58, "aya_end": 68,
            "is_entry_point": False,
            "summary_ar": "جاء إخوة يوسف لمصر طلباً للطعام",
            "summary_en": "Yusuf's brothers came to Egypt seeking food.",
            "semantic_tags": ["reunion", "recognition", "test"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:58", "snippet": "Yusuf's brothers came and entered upon him. He knew them but they did not recognize him."}],
        },
        {
            "id": "cluster_yusuf:binyamin",
            "title_ar": "حيلة بنيامين",
            "title_en": "Benjamin's Test",
            "narrative_role": "trial",
            "chronological_index": 10,
            "sura_no": 12, "aya_start": 69, "aya_end": 79,
            "is_entry_point": False,
            "summary_ar": "يوسف يختبر إخوته ويستبقي بنيامين",
            "summary_en": "Yusuf tests his brothers and keeps Benjamin.",
            "semantic_tags": ["test", "brother", "cup"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:70", "snippet": "He put the drinking-cup in his brother's saddlebag."}],
        },
        {
            "id": "cluster_yusuf:reveal",
            "title_ar": "الكشف عن الهوية",
            "title_en": "Identity Revealed",
            "narrative_role": "outcome",
            "chronological_index": 11,
            "sura_no": 12, "aya_start": 89, "aya_end": 93,
            "is_entry_point": False,
            "summary_ar": "يوسف يكشف هويته لإخوته ويغفر لهم",
            "summary_en": "Yusuf reveals identity to brothers and forgives them.",
            "semantic_tags": ["revelation", "forgiveness", "reunion"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:90", "snippet": "He said: I am Yusuf, and this is my brother. Allah has been gracious to us."}],
        },
        {
            "id": "cluster_yusuf:family_reunited",
            "title_ar": "لم شمل الأسرة",
            "title_en": "Family Reunited",
            "narrative_role": "outcome",
            "chronological_index": 12,
            "sura_no": 12, "aya_start": 99, "aya_end": 101,
            "is_entry_point": False,
            "summary_ar": "يعقوب وأسرته يدخلون مصر، سجود الجميع ليوسف",
            "summary_en": "Yaqub and family enter Egypt, all prostrate to Yusuf.",
            "semantic_tags": ["reunion", "dream_fulfilled", "family"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "12:100", "snippet": "He raised his parents upon the throne, and they fell down before him prostrate."}],
        },
    ],

    # =========================================================================
    # CLUSTER: NUH (Multiple suras) - Key events
    # =========================================================================
    "cluster_nuh": [
        {
            "id": "cluster_nuh:mission",
            "title_ar": "إرسال نوح",
            "title_en": "Nuh's Mission",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 71, "aya_start": 1, "aya_end": 4,
            "is_entry_point": True,
            "summary_ar": "أرسلنا نوحاً إلى قومه أن أنذر قومك",
            "summary_en": "We sent Nuh to his people: Warn your people.",
            "semantic_tags": ["mission", "warning", "dawah"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "71:1", "snippet": "We sent Nuh to his people: Warn your people before a painful punishment comes to them."}],
        },
        {
            "id": "cluster_nuh:dawah_methods",
            "title_ar": "أساليب الدعوة",
            "title_en": "Methods of Dawah",
            "narrative_role": "dialogue",
            "chronological_index": 2,
            "sura_no": 71, "aya_start": 5, "aya_end": 20,
            "is_entry_point": False,
            "summary_ar": "دعاهم ليلاً ونهاراً، سراً وجهاراً",
            "summary_en": "Called them night and day, secretly and openly.",
            "semantic_tags": ["dawah", "persistence", "methods"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "71:5", "snippet": "He said: My Lord, I have called my people night and day."}],
        },
        {
            "id": "cluster_nuh:rejection",
            "title_ar": "رفض القوم",
            "title_en": "People's Rejection",
            "narrative_role": "confrontation",
            "chronological_index": 3,
            "sura_no": 11, "aya_start": 27, "aya_end": 31,
            "is_entry_point": False,
            "summary_ar": "كذبه قومه وقالوا: ما أنت إلا بشر مثلنا",
            "summary_en": "His people denied him: You are only a human like us.",
            "semantic_tags": ["rejection", "mockery", "disbelief"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "11:27", "snippet": "The chiefs of his people who disbelieved said: We see you are only a human like us."}],
        },
        {
            "id": "cluster_nuh:dua_against",
            "title_ar": "دعاء نوح على قومه",
            "title_en": "Nuh's Dua Against His People",
            "narrative_role": "divine_intervention",
            "chronological_index": 4,
            "sura_no": 71, "aya_start": 26, "aya_end": 28,
            "is_entry_point": False,
            "summary_ar": "رب لا تذر على الأرض من الكافرين دياراً",
            "summary_en": "Lord, do not leave upon the earth any disbeliever.",
            "semantic_tags": ["dua", "judgment", "finality"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "71:26", "snippet": "Nuh said: My Lord! Do not leave upon the earth any disbeliever."}],
        },
        {
            "id": "cluster_nuh:ark_command",
            "title_ar": "الأمر ببناء السفينة",
            "title_en": "Command to Build the Ark",
            "narrative_role": "divine_intervention",
            "chronological_index": 5,
            "sura_no": 11, "aya_start": 36, "aya_end": 38,
            "is_entry_point": False,
            "summary_ar": "أوحي إلى نوح أن اصنع الفلك بأعيننا",
            "summary_en": "It was revealed to Nuh: Build the ark under Our observation.",
            "semantic_tags": ["ark", "command", "preparation"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "11:37", "snippet": "Build the ark under Our eyes and Our revelation."}],
        },
        {
            "id": "cluster_nuh:flood",
            "title_ar": "الطوفان",
            "title_en": "The Flood",
            "narrative_role": "outcome",
            "chronological_index": 6,
            "sura_no": 11, "aya_start": 40, "aya_end": 44,
            "is_entry_point": False,
            "summary_ar": "فار التنور وجاء الطوفان، ونوح ينادي ابنه",
            "summary_en": "The oven gushed, flood came, Nuh called to his son.",
            "semantic_tags": ["flood", "judgment", "son"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "11:42", "snippet": "Nuh called out to his son who was apart: O my son, come aboard with us."}],
        },
        {
            "id": "cluster_nuh:survival",
            "title_ar": "النجاة",
            "title_en": "Survival",
            "narrative_role": "outcome",
            "chronological_index": 7,
            "sura_no": 11, "aya_start": 44, "aya_end": 48,
            "is_entry_point": False,
            "summary_ar": "استوت السفينة على الجودي، ونجا المؤمنون",
            "summary_en": "The ark rested on Judi, believers were saved.",
            "semantic_tags": ["salvation", "judi", "new_beginning"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "11:44", "snippet": "It was said: O earth, swallow your water! And the ark came to rest on Judi."}],
        },
    ],

    # =========================================================================
    # CLUSTER: IBRAHIM - Key events
    # =========================================================================
    "cluster_ibrahim": [
        {
            "id": "cluster_ibrahim:stars_moon_sun",
            "title_ar": "استدلال النجوم والقمر والشمس",
            "title_en": "Stars, Moon, Sun Reasoning",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 6, "aya_start": 76, "aya_end": 79,
            "is_entry_point": True,
            "summary_ar": "إبراهيم يستدل على وحدانية الله من الكواكب",
            "summary_en": "Ibrahim reasons to Allah's oneness from celestial bodies.",
            "semantic_tags": ["reasoning", "tawhid", "stars"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "6:76", "snippet": "When night fell, he saw a star and said: This is my Lord. But when it set, he said: I do not love those that set."}],
        },
        {
            "id": "cluster_ibrahim:arguing_father",
            "title_ar": "محاجة أبيه",
            "title_en": "Arguing with His Father",
            "narrative_role": "confrontation",
            "chronological_index": 2,
            "sura_no": 19, "aya_start": 42, "aya_end": 48,
            "is_entry_point": False,
            "summary_ar": "إبراهيم يحاج أباه آزر عن الأصنام",
            "summary_en": "Ibrahim argues with his father Azar about idols.",
            "semantic_tags": ["father", "idols", "dawah"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "19:42", "snippet": "When he said to his father: O my father, why do you worship that which does not hear and does not see?"}],
        },
        {
            "id": "cluster_ibrahim:smashing_idols",
            "title_ar": "تحطيم الأصنام",
            "title_en": "Smashing the Idols",
            "narrative_role": "confrontation",
            "chronological_index": 3,
            "sura_no": 21, "aya_start": 57, "aya_end": 67,
            "is_entry_point": False,
            "summary_ar": "حطم إبراهيم الأصنام وترك الكبير",
            "summary_en": "Ibrahim smashed idols, left the big one.",
            "semantic_tags": ["idols", "challenge", "proof"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "21:58", "snippet": "He broke them to pieces, all but the biggest of them."}],
        },
        {
            "id": "cluster_ibrahim:fire",
            "title_ar": "إلقاؤه في النار",
            "title_en": "Thrown into Fire",
            "narrative_role": "trial",
            "chronological_index": 4,
            "sura_no": 21, "aya_start": 68, "aya_end": 70,
            "is_entry_point": False,
            "summary_ar": "قالوا حرقوه، قلنا يا نار كوني برداً وسلاماً",
            "summary_en": "They said burn him, We said: O fire, be coolness and peace.",
            "semantic_tags": ["fire", "miracle", "protection"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "21:69", "snippet": "We said: O fire, be coolness and peace upon Ibrahim."}],
        },
        {
            "id": "cluster_ibrahim:migration",
            "title_ar": "الهجرة",
            "title_en": "Migration",
            "narrative_role": "migration",
            "chronological_index": 5,
            "sura_no": 21, "aya_start": 71, "aya_end": 71,
            "is_entry_point": False,
            "summary_ar": "نجيناه ولوطاً إلى الأرض المباركة",
            "summary_en": "We saved him and Lut to the blessed land.",
            "semantic_tags": ["migration", "salvation", "blessed_land"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "21:71", "snippet": "We saved him and Lut to the land which We had blessed for all peoples."}],
        },
        {
            "id": "cluster_ibrahim:hajar_ismail",
            "title_ar": "هاجر وإسماعيل",
            "title_en": "Hajar and Ismail",
            "narrative_role": "trial",
            "chronological_index": 6,
            "sura_no": 14, "aya_start": 37, "aya_end": 37,
            "is_entry_point": False,
            "summary_ar": "أسكن إبراهيم من ذريته بوادٍ غير ذي زرع عند البيت المحرم",
            "summary_en": "Ibrahim settled some of his offspring in a barren valley by the Sacred House.",
            "semantic_tags": ["makkah", "family", "trust"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "14:37", "snippet": "Our Lord, I have settled some of my descendants in an uncultivated valley near Your Sacred House."}],
        },
        {
            "id": "cluster_ibrahim:sacrifice",
            "title_ar": "الذبح العظيم",
            "title_en": "The Great Sacrifice",
            "narrative_role": "trial",
            "chronological_index": 7,
            "sura_no": 37, "aya_start": 102, "aya_end": 107,
            "is_entry_point": False,
            "summary_ar": "إبراهيم يُؤمر بذبح ابنه، فيطيعان، ثم يُفدى بذبح عظيم",
            "summary_en": "Ibrahim commanded to sacrifice his son, both submit, ransomed with great sacrifice.",
            "semantic_tags": ["sacrifice", "obedience", "test"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "37:102", "snippet": "When he was old enough to work with him, he said: O my son, I have seen in a dream that I am slaughtering you."}],
        },
        {
            "id": "cluster_ibrahim:kaaba",
            "title_ar": "بناء الكعبة",
            "title_en": "Building the Ka'bah",
            "narrative_role": "outcome",
            "chronological_index": 8,
            "sura_no": 2, "aya_start": 127, "aya_end": 129,
            "is_entry_point": False,
            "summary_ar": "إبراهيم وإسماعيل يرفعان القواعد من البيت",
            "summary_en": "Ibrahim and Ismail raised the foundations of the House.",
            "semantic_tags": ["kaaba", "building", "dua"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "2:127", "snippet": "When Ibrahim and Ismail were raising the foundations of the House."}],
        },
    ],

    # =========================================================================
    # CLUSTER: UHUD & HYPOCRITES (3:121-175)
    # =========================================================================
    "cluster_uhud_hypocrites": [
        {
            "id": "cluster_uhud_hypocrites:positioning",
            "title_ar": "تنظيم الجيش",
            "title_en": "Positioning the Army",
            "narrative_role": "introduction",
            "chronological_index": 1,
            "sura_no": 3, "aya_start": 121, "aya_end": 122,
            "is_entry_point": True,
            "summary_ar": "خرج النبي ﷺ لتبوئة المؤمنين مقاعد للقتال",
            "summary_en": "The Prophet ﷺ went out to position believers at their battle stations.",
            "semantic_tags": ["battle", "leadership", "strategy"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:121", "snippet": "When you (O Muhammad) left your household in the morning to post the believers at their stations for the battle."}],
        },
        {
            "id": "cluster_uhud_hypocrites:angel_support",
            "title_ar": "وعد بالملائكة",
            "title_en": "Promise of Angel Support",
            "narrative_role": "prophecy",
            "chronological_index": 2,
            "sura_no": 3, "aya_start": 123, "aya_end": 127,
            "is_entry_point": False,
            "summary_ar": "ذكر نصر بدر وعد الله بإمداد الملائكة للمتقين الصابرين",
            "summary_en": "Reference to Badr victory, Allah's promise of angel reinforcement for those patient and conscious of Him.",
            "semantic_tags": ["angels", "victory", "patience", "badr"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:124", "snippet": "Is it not sufficient for you that your Lord should reinforce you with three thousand angels sent down?"}],
        },
        {
            "id": "cluster_uhud_hypocrites:initial_victory",
            "title_ar": "النصر المبدئي",
            "title_en": "Initial Victory",
            "narrative_role": "outcome",
            "chronological_index": 3,
            "sura_no": 3, "aya_start": 152, "aya_end": 152,
            "is_entry_point": False,
            "summary_ar": "صدق الله وعده إذ تحسون المشركين بإذنه",
            "summary_en": "Allah fulfilled His promise when believers were defeating the enemy by His permission.",
            "semantic_tags": ["victory", "promise", "divine_help"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:152", "snippet": "And Allah had certainly fulfilled His promise to you when you were killing them by His permission."}],
        },
        {
            "id": "cluster_uhud_hypocrites:archers_disobey",
            "title_ar": "عصيان الرماة",
            "title_en": "Archers' Disobedience",
            "narrative_role": "trial",
            "chronological_index": 4,
            "sura_no": 3, "aya_start": 152, "aya_end": 153,
            "is_entry_point": False,
            "summary_ar": "فشل الرماة وتنازعوا وعصوا بعد أن أراهم الله ما يحبون",
            "summary_en": "Archers failed, disputed, and disobeyed after Allah showed them what they loved (victory).",
            "semantic_tags": ["disobedience", "greed", "test", "archers"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:152", "snippet": "Until when you lost courage and fell to disputing about the order and disobeyed after He had shown you that which you love."}],
        },
        {
            "id": "cluster_uhud_hypocrites:tide_turns",
            "title_ar": "تحول المعركة",
            "title_en": "Battle Tide Turns",
            "narrative_role": "confrontation",
            "chronological_index": 5,
            "sura_no": 3, "aya_start": 153, "aya_end": 155,
            "is_entry_point": False,
            "summary_ar": "صعد المسلمون الجبل والرسول يدعوهم، عفا الله عنهم",
            "summary_en": "Believers fled uphill while the Messenger called them back; Allah pardoned them.",
            "semantic_tags": ["retreat", "forgiveness", "test"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:153", "snippet": "When you were climbing and not looking aside at anyone while the Messenger was calling you from behind."}],
        },
        {
            "id": "cluster_uhud_hypocrites:hypocrites_exposed",
            "title_ar": "انكشاف المنافقين",
            "title_en": "Hypocrites Exposed",
            "narrative_role": "warning",
            "chronological_index": 6,
            "sura_no": 3, "aya_start": 165, "aya_end": 168,
            "is_entry_point": False,
            "summary_ar": "المنافقون قالوا لإخوانهم: لو أطاعونا ما قتلوا، قيل لهم: ادفعوا عن أنفسكم الموت",
            "summary_en": "Hypocrites said: 'Had they obeyed us, they wouldn't have died.' Told: 'Then avert death from yourselves!'",
            "semantic_tags": ["hypocrisy", "exposure", "cowardice"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:167", "snippet": "And those who are hypocrites, who said to their brothers while sitting: Had they obeyed us, they would not have been killed."}],
        },
        {
            "id": "cluster_uhud_hypocrites:dont_lose_heart",
            "title_ar": "لا تهنوا",
            "title_en": "Do Not Lose Heart",
            "narrative_role": "reflection",
            "chronological_index": 7,
            "sura_no": 3, "aya_start": 139, "aya_end": 142,
            "is_entry_point": False,
            "summary_ar": "لا تهنوا ولا تحزنوا وأنتم الأعلون إن كنتم مؤمنين",
            "summary_en": "Do not weaken or grieve - you are superior if you are believers.",
            "semantic_tags": ["encouragement", "faith", "superiority"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:139", "snippet": "So do not weaken and do not grieve, and you will be superior if you are believers."}],
        },
        {
            "id": "cluster_uhud_hypocrites:muhammad_messenger",
            "title_ar": "محمد رسول",
            "title_en": "Muhammad is a Messenger",
            "narrative_role": "warning",
            "chronological_index": 8,
            "sura_no": 3, "aya_start": 144, "aya_end": 145,
            "is_entry_point": False,
            "summary_ar": "محمد رسول قد خلت من قبله الرسل، أفإن مات انقلبتم على أعقابكم؟",
            "summary_en": "Muhammad is only a messenger; messengers passed before him. If he dies, will you turn back?",
            "semantic_tags": ["messenger", "mortality", "steadfastness"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:144", "snippet": "Muhammad is not but a messenger. Messengers have passed on before him. So if he was to die or be killed, would you turn back on your heels?"}],
        },
        {
            "id": "cluster_uhud_hypocrites:consult_them",
            "title_ar": "المشاورة",
            "title_en": "Consultation & Trust",
            "narrative_role": "reflection",
            "chronological_index": 9,
            "sura_no": 3, "aya_start": 159, "aya_end": 160,
            "is_entry_point": False,
            "summary_ar": "شاورهم في الأمر فإذا عزمت فتوكل على الله",
            "summary_en": "Consult them in affairs, then when decided, trust in Allah.",
            "semantic_tags": ["consultation", "shura", "trust", "leadership"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:159", "snippet": "And consult them in the matter. And when you have decided, then rely upon Allah."}],
        },
        {
            "id": "cluster_uhud_hypocrites:martyrs_alive",
            "title_ar": "الشهداء أحياء",
            "title_en": "Martyrs Are Alive",
            "narrative_role": "outcome",
            "chronological_index": 10,
            "sura_no": 3, "aya_start": 169, "aya_end": 171,
            "is_entry_point": False,
            "summary_ar": "لا تحسبن الذين قتلوا في سبيل الله أمواتاً بل أحياء عند ربهم يرزقون",
            "summary_en": "Do not think those killed in Allah's cause are dead - they are alive with their Lord, provided for.",
            "semantic_tags": ["martyrdom", "afterlife", "reward", "honor"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:169", "snippet": "And never think of those who have been killed in the cause of Allah as dead. Rather, they are alive with their Lord, receiving provision."}],
        },
        {
            "id": "cluster_uhud_hypocrites:believers_rejoice",
            "title_ar": "فرح المؤمنين",
            "title_en": "Believers Rejoice",
            "narrative_role": "reflection",
            "chronological_index": 11,
            "sura_no": 3, "aya_start": 171, "aya_end": 175,
            "is_entry_point": False,
            "summary_ar": "يستبشرون بنعمة من الله وفضل وأن الله لا يضيع أجر المؤمنين",
            "summary_en": "They rejoice in Allah's bounty and favor, and that Allah does not waste the reward of believers.",
            "semantic_tags": ["joy", "reward", "blessing", "conclusion"],
            "evidence": [{"source_id": "ibn_kathir_en", "reference": "3:171", "snippet": "They receive good tidings of favor from Allah and bounty and that Allah does not allow the reward of believers to be lost."}],
        },
    ],
}

# =============================================================================
# SEEDING FUNCTIONS
# =============================================================================

def seed_clusters(session):
    """Seed story clusters."""
    print("\n1. Seeding Story Clusters...")

    for cluster_data in STORY_CLUSTERS:
        cluster_id = cluster_data["id"]

        # Check if exists
        result = session.execute(
            text("SELECT id FROM story_clusters WHERE id = :id"),
            {"id": cluster_id}
        )
        exists = result.fetchone()

        if exists:
            # Update
            update_sql = text("""
                UPDATE story_clusters SET
                    title_ar = :title_ar,
                    title_en = :title_en,
                    short_title_ar = :short_title_ar,
                    short_title_en = :short_title_en,
                    category = :category,
                    main_persons = :main_persons,
                    groups = :groups,
                    tags = :tags,
                    places = :places,
                    era = :era,
                    era_basis = :era_basis,
                    time_description_en = :time_description_en,
                    ayah_spans = :ayah_spans,
                    primary_sura = :primary_sura,
                    summary_ar = :summary_ar,
                    summary_en = :summary_en,
                    lessons_ar = :lessons_ar,
                    lessons_en = :lessons_en,
                    updated_at = :updated_at
                WHERE id = :id
            """)
            session.execute(update_sql, {
                "id": cluster_id,
                "title_ar": cluster_data["title_ar"],
                "title_en": cluster_data["title_en"],
                "short_title_ar": cluster_data.get("short_title_ar"),
                "short_title_en": cluster_data.get("short_title_en"),
                "category": cluster_data["category"],
                "main_persons": cluster_data.get("main_persons"),
                "groups": cluster_data.get("groups"),
                "tags": cluster_data.get("tags"),
                "places": json.dumps(cluster_data.get("places", [])),
                "era": cluster_data.get("era"),
                "era_basis": cluster_data.get("era_basis", "unknown"),
                "time_description_en": cluster_data.get("time_description_en"),
                "ayah_spans": json.dumps(cluster_data["ayah_spans"]),
                "primary_sura": cluster_data.get("primary_sura"),
                "summary_ar": cluster_data.get("summary_ar"),
                "summary_en": cluster_data.get("summary_en"),
                "lessons_ar": cluster_data.get("lessons_ar"),
                "lessons_en": cluster_data.get("lessons_en"),
                "updated_at": datetime.utcnow(),
            })
            print(f"   Updated: {cluster_id}")
        else:
            # Insert
            insert_sql = text("""
                INSERT INTO story_clusters (
                    id, title_ar, title_en, short_title_ar, short_title_en,
                    category, main_persons, groups, tags, places,
                    era, era_basis, time_description_en, ayah_spans, primary_sura,
                    summary_ar, summary_en, lessons_ar, lessons_en,
                    created_at, updated_at
                ) VALUES (
                    :id, :title_ar, :title_en, :short_title_ar, :short_title_en,
                    :category, :main_persons, :groups, :tags, :places,
                    :era, :era_basis, :time_description_en, :ayah_spans, :primary_sura,
                    :summary_ar, :summary_en, :lessons_ar, :lessons_en,
                    :created_at, :updated_at
                )
            """)
            session.execute(insert_sql, {
                "id": cluster_id,
                "title_ar": cluster_data["title_ar"],
                "title_en": cluster_data["title_en"],
                "short_title_ar": cluster_data.get("short_title_ar"),
                "short_title_en": cluster_data.get("short_title_en"),
                "category": cluster_data["category"],
                "main_persons": cluster_data.get("main_persons"),
                "groups": cluster_data.get("groups"),
                "tags": cluster_data.get("tags"),
                "places": json.dumps(cluster_data.get("places", [])),
                "era": cluster_data.get("era"),
                "era_basis": cluster_data.get("era_basis", "unknown"),
                "time_description_en": cluster_data.get("time_description_en"),
                "ayah_spans": json.dumps(cluster_data["ayah_spans"]),
                "primary_sura": cluster_data.get("primary_sura"),
                "summary_ar": cluster_data.get("summary_ar"),
                "summary_en": cluster_data.get("summary_en"),
                "lessons_ar": cluster_data.get("lessons_ar"),
                "lessons_en": cluster_data.get("lessons_en"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            print(f"   Created: {cluster_id}")

    print(f"\n   Total clusters: {len(STORY_CLUSTERS)}")


def seed_events(session):
    """Seed story events."""
    print("\n2. Seeding Story Events...")

    total_events = 0
    for cluster_id, events in STORY_EVENTS.items():
        print(f"\n   Cluster: {cluster_id}")

        for event_data in events:
            event_id = event_data["id"]

            # Check if exists
            result = session.execute(
                text("SELECT id FROM story_events WHERE id = :id"),
                {"id": event_id}
            )
            exists = result.fetchone()

            if exists:
                # Update
                update_sql = text("""
                    UPDATE story_events SET
                        title_ar = :title_ar,
                        title_en = :title_en,
                        narrative_role = :narrative_role,
                        chronological_index = :chronological_index,
                        sura_no = :sura_no,
                        aya_start = :aya_start,
                        aya_end = :aya_end,
                        is_entry_point = :is_entry_point,
                        summary_ar = :summary_ar,
                        summary_en = :summary_en,
                        semantic_tags = :semantic_tags,
                        evidence = :evidence,
                        updated_at = :updated_at
                    WHERE id = :id
                """)
                session.execute(update_sql, {
                    "id": event_id,
                    "title_ar": event_data["title_ar"],
                    "title_en": event_data["title_en"],
                    "narrative_role": event_data["narrative_role"],
                    "chronological_index": event_data["chronological_index"],
                    "sura_no": event_data["sura_no"],
                    "aya_start": event_data["aya_start"],
                    "aya_end": event_data["aya_end"],
                    "is_entry_point": event_data.get("is_entry_point", False),
                    "summary_ar": event_data["summary_ar"],
                    "summary_en": event_data["summary_en"],
                    "semantic_tags": event_data.get("semantic_tags"),
                    "evidence": json.dumps(event_data["evidence"]),
                    "updated_at": datetime.utcnow(),
                })
                print(f"      Updated: {event_id}")
            else:
                # Insert
                insert_sql = text("""
                    INSERT INTO story_events (
                        id, cluster_id, title_ar, title_en,
                        narrative_role, chronological_index,
                        sura_no, aya_start, aya_end,
                        is_entry_point, summary_ar, summary_en,
                        semantic_tags, evidence,
                        created_at, updated_at
                    ) VALUES (
                        :id, :cluster_id, :title_ar, :title_en,
                        :narrative_role, :chronological_index,
                        :sura_no, :aya_start, :aya_end,
                        :is_entry_point, :summary_ar, :summary_en,
                        :semantic_tags, :evidence,
                        :created_at, :updated_at
                    )
                """)
                session.execute(insert_sql, {
                    "id": event_id,
                    "cluster_id": cluster_id,
                    "title_ar": event_data["title_ar"],
                    "title_en": event_data["title_en"],
                    "narrative_role": event_data["narrative_role"],
                    "chronological_index": event_data["chronological_index"],
                    "sura_no": event_data["sura_no"],
                    "aya_start": event_data["aya_start"],
                    "aya_end": event_data["aya_end"],
                    "is_entry_point": event_data.get("is_entry_point", False),
                    "summary_ar": event_data["summary_ar"],
                    "summary_en": event_data["summary_en"],
                    "semantic_tags": event_data.get("semantic_tags"),
                    "evidence": json.dumps(event_data["evidence"]),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })
                print(f"      Created: {event_id}")

            total_events += 1

    print(f"\n   Total events: {total_events}")


def seed_event_connections(session):
    """Seed chronological connections between events."""
    print("\n3. Seeding Event Connections...")

    # Clear existing connections
    session.execute(text("DELETE FROM event_connections"))

    conn_count = 0
    for cluster_id, events in STORY_EVENTS.items():
        # Sort by chronological index
        sorted_events = sorted(events, key=lambda e: e["chronological_index"])

        # Create chronological_next edges
        for i in range(len(sorted_events) - 1):
            source = sorted_events[i]["id"]
            target = sorted_events[i + 1]["id"]

            insert_sql = text("""
                INSERT INTO event_connections (
                    source_event_id, target_event_id, edge_type,
                    is_chronological, strength, created_at
                ) VALUES (
                    :source, :target, 'chronological_next',
                    true, 1.0, :created_at
                )
            """)
            session.execute(insert_sql, {
                "source": source,
                "target": target,
                "created_at": datetime.utcnow(),
            })
            conn_count += 1

    print(f"   Connections created: {conn_count}")


def update_cluster_counts(session):
    """Update event counts on clusters."""
    print("\n4. Updating Cluster Event Counts...")

    session.execute(text("""
        UPDATE story_clusters SET event_count = (
            SELECT COUNT(*) FROM story_events WHERE cluster_id = story_clusters.id
        )
    """))

    # Also calculate total verses
    session.execute(text("""
        UPDATE story_clusters SET total_verses = (
            SELECT COALESCE(SUM(aya_end - aya_start + 1), 0)
            FROM story_events WHERE cluster_id = story_clusters.id
        )
    """))


def main():
    """Run the seed script."""
    print("=" * 60)
    print("SEEDING STORY ATLAS")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        seed_clusters(session)
        seed_events(session)
        seed_event_connections(session)
        update_cluster_counts(session)

        session.commit()

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)

        # Verify
        print("\nVerification:")
        result = session.execute(text("SELECT COUNT(*) FROM story_clusters"))
        cluster_count = result.scalar()
        print(f"   Clusters: {cluster_count}")

        result = session.execute(text("SELECT COUNT(*) FROM story_events"))
        event_count = result.scalar()
        print(f"   Events: {event_count}")

        result = session.execute(text("SELECT COUNT(*) FROM event_connections"))
        conn_count = result.scalar()
        print(f"   Connections: {conn_count}")

        # Show clusters by category
        print("\nClusters by Category:")
        result = session.execute(text("""
            SELECT category, COUNT(*) as count
            FROM story_clusters
            GROUP BY category
            ORDER BY count DESC
        """))
        for row in result.fetchall():
            print(f"   {row[0]}: {row[1]}")

    except Exception as e:
        session.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
