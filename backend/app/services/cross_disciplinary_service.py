"""
Cross-Disciplinary Knowledge Integration Service.

Integrates Quranic verses with related knowledge from:
1. Fiqh (Islamic Jurisprudence)
2. Hadith (Prophetic Traditions)
3. Sira (Prophetic Biography)
4. Aqidah (Islamic Theology)
5. Tazkiyah (Spiritual Purification)

Arabic: خدمة تكامل المعرفة عبر التخصصات
"""

import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class Discipline(str, Enum):
    """Islamic disciplines."""
    FIQH = "fiqh"
    HADITH = "hadith"
    SIRA = "sira"
    AQIDAH = "aqidah"
    TAZKIYAH = "tazkiyah"
    TAFSIR = "tafsir"
    ARABIC = "arabic"


class FiqhSchool(str, Enum):
    """Schools of Islamic jurisprudence."""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"
    JAFARI = "jafari"


class HadithGrade(str, Enum):
    """Hadith authenticity grades."""
    SAHIH = "sahih"
    HASAN = "hasan"
    DAIF = "daif"
    MUTAWATIR = "mutawatir"


class SiraEra(str, Enum):
    """Eras in Prophetic biography."""
    PRE_PROPHETHOOD = "pre_prophethood"
    MECCAN = "meccan"
    MEDINAN = "medinan"
    FINAL_YEARS = "final_years"


@dataclass
class FiqhRuling:
    """A Fiqh ruling related to a verse."""
    ruling_id: str
    topic_ar: str
    topic_en: str
    ruling_ar: str
    ruling_en: str
    evidence_verses: List[str]
    evidence_hadith: List[str]
    schools_agreement: Dict[str, str]  # School -> Position
    conditions: List[str]
    exceptions: List[str]


@dataclass
class HadithReference:
    """A Hadith related to a verse."""
    hadith_id: str
    text_ar: str
    text_en: str
    narrator: str
    source: str  # Bukhari, Muslim, etc.
    grade: HadithGrade
    chapter: str
    number: int
    related_verses: List[str]
    themes: List[str]


@dataclass
class SiraEvent:
    """An event from the Sira related to a verse."""
    event_id: str
    title_ar: str
    title_en: str
    era: SiraEra
    year_hijri: Optional[int]
    description_ar: str
    description_en: str
    related_verses: List[str]
    lessons: List[str]
    participants: List[str]


# =============================================================================
# FIQH RULINGS DATA
# =============================================================================

FIQH_RULINGS = {
    "salah_obligation": {
        "topic_ar": "فرضية الصلاة",
        "topic_en": "Obligation of Prayer",
        "ruling_ar": "الصلاة فرض عين على كل مسلم بالغ عاقل",
        "ruling_en": "Prayer is an individual obligation on every sane adult Muslim",
        "evidence_verses": ["2:43", "2:110", "4:103", "20:14"],
        "evidence_hadith": ["بني الإسلام على خمس"],
        "schools_agreement": {
            "hanafi": "فرض عين",
            "maliki": "فرض عين",
            "shafii": "فرض عين",
            "hanbali": "فرض عين",
        },
        "conditions": ["الإسلام", "البلوغ", "العقل"],
        "exceptions": ["الحائض", "النفساء"],
        "category": "worship",
    },
    "zakat_obligation": {
        "topic_ar": "فرضية الزكاة",
        "topic_en": "Obligation of Zakat",
        "ruling_ar": "الزكاة فرض على كل مسلم ملك النصاب وحال عليه الحول",
        "ruling_en": "Zakat is obligatory on every Muslim who owns the nisab for a full year",
        "evidence_verses": ["2:43", "2:110", "9:103", "2:267"],
        "evidence_hadith": ["بني الإسلام على خمس"],
        "schools_agreement": {
            "hanafi": "2.5% من النقد والتجارة",
            "maliki": "2.5% مع اختلاف في بعض الأموال",
            "shafii": "2.5% من النقد والتجارة",
            "hanbali": "2.5% من النقد والتجارة",
        },
        "conditions": ["الملك التام", "بلوغ النصاب", "حولان الحول"],
        "exceptions": ["الديون المستغرقة"],
        "category": "worship",
    },
    "fasting_obligation": {
        "topic_ar": "فرضية صيام رمضان",
        "topic_en": "Obligation of Ramadan Fasting",
        "ruling_ar": "صيام رمضان فرض على كل مسلم بالغ عاقل قادر",
        "ruling_en": "Fasting Ramadan is obligatory on every sane, adult, able Muslim",
        "evidence_verses": ["2:183", "2:185", "2:187"],
        "evidence_hadith": ["بني الإسلام على خمس", "من صام رمضان إيمانا واحتسابا"],
        "schools_agreement": {
            "hanafi": "فرض عين",
            "maliki": "فرض عين",
            "shafii": "فرض عين",
            "hanbali": "فرض عين",
        },
        "conditions": ["الإسلام", "البلوغ", "العقل", "القدرة"],
        "exceptions": ["المريض", "المسافر", "الحامل", "المرضع"],
        "category": "worship",
    },
    "hajj_obligation": {
        "topic_ar": "فرضية الحج",
        "topic_en": "Obligation of Hajj",
        "ruling_ar": "الحج فرض مرة في العمر على المستطيع",
        "ruling_en": "Hajj is obligatory once in a lifetime for those who are able",
        "evidence_verses": ["3:97", "2:196", "2:197", "22:27"],
        "evidence_hadith": ["بني الإسلام على خمس"],
        "schools_agreement": {
            "hanafi": "فرض على الفور عند الاستطاعة",
            "maliki": "فرض على التراخي",
            "shafii": "فرض على التراخي",
            "hanbali": "فرض على الفور",
        },
        "conditions": ["الإسلام", "البلوغ", "العقل", "الاستطاعة", "الأمن"],
        "exceptions": ["العاجز بدنيا", "من لا يجد النفقة"],
        "category": "worship",
    },
    "hijab_ruling": {
        "topic_ar": "حكم الحجاب",
        "topic_en": "Ruling on Hijab",
        "ruling_ar": "يجب على المرأة المسلمة ستر بدنها عدا الوجه والكفين",
        "ruling_en": "Muslim women must cover their body except face and hands",
        "evidence_verses": ["24:31", "33:59", "24:60"],
        "evidence_hadith": ["يا أسماء إن المرأة إذا بلغت المحيض"],
        "schools_agreement": {
            "hanafi": "وجه وكفان ليسا بعورة",
            "maliki": "وجه وكفان ليسا بعورة",
            "shafii": "كل البدن عورة عدا الوجه والكفين",
            "hanbali": "اختلاف في الوجه",
        },
        "conditions": ["البلوغ", "حضور الأجانب"],
        "exceptions": ["أمام المحارم", "في الصلاة"],
        "category": "dress",
    },
    "riba_prohibition": {
        "topic_ar": "تحريم الربا",
        "topic_en": "Prohibition of Interest (Riba)",
        "ruling_ar": "الربا محرم بجميع أشكاله في الإسلام",
        "ruling_en": "Interest/usury is prohibited in all its forms in Islam",
        "evidence_verses": ["2:275", "2:276", "2:278", "3:130"],
        "evidence_hadith": ["لعن الله آكل الربا"],
        "schools_agreement": {
            "hanafi": "حرام قطعا",
            "maliki": "حرام قطعا",
            "shafii": "حرام قطعا",
            "hanbali": "حرام قطعا",
        },
        "conditions": [],
        "exceptions": ["حالة الضرورة عند بعض العلماء"],
        "category": "transactions",
    },
    "inheritance_rules": {
        "topic_ar": "أحكام الميراث",
        "topic_en": "Inheritance Rules",
        "ruling_ar": "قسمة التركة حسب الفرائض المحددة شرعا",
        "ruling_en": "Estate division according to Shariah-specified shares",
        "evidence_verses": ["4:7", "4:11", "4:12", "4:176"],
        "evidence_hadith": ["ألحقوا الفرائض بأهلها"],
        "schools_agreement": {
            "hanafi": "اتفاق على الأصول",
            "maliki": "اتفاق على الأصول",
            "shafii": "اتفاق على الأصول",
            "hanbali": "اتفاق على الأصول",
        },
        "conditions": ["موت المورث", "حياة الوارث", "عدم موانع الإرث"],
        "exceptions": ["القاتل", "المرتد", "اختلاف الدين"],
        "category": "family",
    },
    "marriage_contract": {
        "topic_ar": "عقد النكاح",
        "topic_en": "Marriage Contract",
        "ruling_ar": "النكاح سنة مؤكدة وقد يجب على القادر الخائف على نفسه",
        "ruling_en": "Marriage is a confirmed Sunnah and may be obligatory for one who fears falling into sin",
        "evidence_verses": ["4:3", "30:21", "24:32", "2:221"],
        "evidence_hadith": ["يا معشر الشباب من استطاع منكم الباءة"],
        "schools_agreement": {
            "hanafi": "سنة مؤكدة",
            "maliki": "سنة مؤكدة",
            "shafii": "سنة مؤكدة",
            "hanbali": "سنة مؤكدة",
        },
        "conditions": ["الولي", "الشاهدين", "المهر", "الإيجاب والقبول"],
        "exceptions": [],
        "category": "family",
    },
}

# =============================================================================
# HADITH REFERENCES DATA
# =============================================================================

HADITH_REFERENCES = {
    "five_pillars": {
        "text_ar": "بُنِيَ الإِسْلامُ عَلَى خَمْسٍ: شَهَادَةِ أَنْ لا إِلَهَ إِلا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ، وَإِقَامِ الصَّلاةِ، وَإِيتَاءِ الزَّكَاةِ، وَحَجِّ الْبَيْتِ، وَصَوْمِ رَمَضَانَ",
        "text_en": "Islam is built upon five pillars: testifying that there is no god but Allah and Muhammad is His messenger, establishing prayer, paying zakat, pilgrimage to the House, and fasting Ramadan",
        "narrator": "عبد الله بن عمر",
        "narrator_en": "Abdullah ibn Umar",
        "source": "البخاري ومسلم",
        "source_en": "Bukhari and Muslim",
        "grade": HadithGrade.MUTAWATIR,
        "chapter_ar": "الإيمان",
        "chapter_en": "Faith",
        "number": 8,
        "related_verses": ["2:43", "2:183", "3:97", "9:103"],
        "themes": ["pillars_of_islam", "faith", "worship"],
    },
    "actions_by_intentions": {
        "text_ar": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "text_en": "Actions are but by intentions, and every person will have only what they intended",
        "narrator": "عمر بن الخطاب",
        "narrator_en": "Umar ibn al-Khattab",
        "source": "البخاري ومسلم",
        "source_en": "Bukhari and Muslim",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "بدء الوحي",
        "chapter_en": "Beginning of Revelation",
        "number": 1,
        "related_verses": ["98:5", "39:2", "39:11"],
        "themes": ["intentions", "sincerity", "deeds"],
    },
    "halal_haram_clear": {
        "text_ar": "الحَلالُ بَيِّنٌ وَالحَرامُ بَيِّنٌ، وَبَيْنَهُمَا أُمُورٌ مُشْتَبِهَاتٌ",
        "text_en": "The halal is clear and the haram is clear, and between them are doubtful matters",
        "narrator": "النعمان بن بشير",
        "narrator_en": "Nu'man ibn Bashir",
        "source": "البخاري ومسلم",
        "source_en": "Bukhari and Muslim",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "البيوع",
        "chapter_en": "Sales",
        "number": 52,
        "related_verses": ["2:168", "5:88", "16:114"],
        "themes": ["halal_haram", "piety", "caution"],
    },
    "love_for_brother": {
        "text_ar": "لا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        "text_en": "None of you truly believes until he loves for his brother what he loves for himself",
        "narrator": "أنس بن مالك",
        "narrator_en": "Anas ibn Malik",
        "source": "البخاري ومسلم",
        "source_en": "Bukhari and Muslim",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "الإيمان",
        "chapter_en": "Faith",
        "number": 13,
        "related_verses": ["49:10", "59:9", "3:103"],
        "themes": ["brotherhood", "faith", "love"],
    },
    "protect_tongue": {
        "text_ar": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
        "text_en": "Whoever believes in Allah and the Last Day should speak good or remain silent",
        "narrator": "أبو هريرة",
        "narrator_en": "Abu Hurairah",
        "source": "البخاري ومسلم",
        "source_en": "Bukhari and Muslim",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "الأدب",
        "chapter_en": "Manners",
        "number": 6018,
        "related_verses": ["17:53", "2:83", "4:148"],
        "themes": ["speech", "faith", "manners"],
    },
    "mercy_to_creation": {
        "text_ar": "الرَّاحِمُونَ يَرْحَمُهُمُ الرَّحْمَنُ، ارْحَمُوا مَنْ فِي الأَرْضِ يَرْحَمْكُمْ مَنْ فِي السَّمَاءِ",
        "text_en": "The merciful are shown mercy by the Most Merciful. Show mercy to those on earth, and you will be shown mercy from above",
        "narrator": "عبد الله بن عمرو",
        "narrator_en": "Abdullah ibn Amr",
        "source": "الترمذي",
        "source_en": "Tirmidhi",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "البر والصلة",
        "chapter_en": "Righteousness and Maintaining Ties",
        "number": 1924,
        "related_verses": ["21:107", "7:156", "6:12"],
        "themes": ["mercy", "compassion", "divine_attributes"],
    },
    "no_harm": {
        "text_ar": "لا ضَرَرَ وَلا ضِرَارَ",
        "text_en": "There should be no harm nor reciprocating harm",
        "narrator": "أبو سعيد الخدري",
        "narrator_en": "Abu Sa'id al-Khudri",
        "source": "ابن ماجه والدارقطني",
        "source_en": "Ibn Majah and Daraqutni",
        "grade": HadithGrade.HASAN,
        "chapter_ar": "الأحكام",
        "chapter_en": "Rulings",
        "number": 2341,
        "related_verses": ["2:231", "2:233", "4:12"],
        "themes": ["harm", "rights", "principles"],
    },
    "strong_believer": {
        "text_ar": "المُؤْمِنُ القَوِيُّ خَيْرٌ وَأَحَبُّ إِلَى اللَّهِ مِنَ المُؤْمِنِ الضَّعِيفِ",
        "text_en": "The strong believer is better and more beloved to Allah than the weak believer",
        "narrator": "أبو هريرة",
        "narrator_en": "Abu Hurairah",
        "source": "مسلم",
        "source_en": "Muslim",
        "grade": HadithGrade.SAHIH,
        "chapter_ar": "القدر",
        "chapter_en": "Divine Decree",
        "number": 2664,
        "related_verses": ["8:60", "3:139", "47:35"],
        "themes": ["strength", "faith", "excellence"],
    },
}

# =============================================================================
# SIRA EVENTS DATA
# =============================================================================

SIRA_EVENTS = {
    "birth_prophet": {
        "title_ar": "مولد النبي صلى الله عليه وسلم",
        "title_en": "Birth of the Prophet (PBUH)",
        "era": SiraEra.PRE_PROPHETHOOD,
        "year_hijri": None,
        "year_ce": 570,
        "description_ar": "ولد النبي محمد في مكة في عام الفيل",
        "description_en": "Prophet Muhammad was born in Mecca in the Year of the Elephant",
        "related_verses": ["105:1-5"],
        "lessons": ["Divine protection", "Special providence"],
        "participants": ["آمنة بنت وهب", "عبد المطلب"],
    },
    "first_revelation": {
        "title_ar": "نزول الوحي الأول",
        "title_en": "First Revelation",
        "era": SiraEra.MECCAN,
        "year_hijri": None,
        "year_ce": 610,
        "description_ar": "نزل جبريل على النبي في غار حراء بأول آيات القرآن",
        "description_en": "Gabriel descended upon the Prophet in Cave Hira with the first verses",
        "related_verses": ["96:1-5", "74:1-7"],
        "lessons": ["Beginning of prophethood", "Importance of knowledge"],
        "participants": ["جبريل", "خديجة بنت خويلد"],
    },
    "public_dawah": {
        "title_ar": "الجهر بالدعوة",
        "title_en": "Public Preaching",
        "era": SiraEra.MECCAN,
        "year_hijri": None,
        "year_ce": 613,
        "description_ar": "بدأ النبي بالدعوة الجهرية بعد ثلاث سنوات من الدعوة السرية",
        "description_en": "The Prophet began public preaching after three years of private invitation",
        "related_verses": ["26:214", "15:94"],
        "lessons": ["Gradual methodology", "Patience in dawah"],
        "participants": ["قريش"],
    },
    "hijra_abyssinia": {
        "title_ar": "الهجرة إلى الحبشة",
        "title_en": "Migration to Abyssinia",
        "era": SiraEra.MECCAN,
        "year_hijri": None,
        "year_ce": 615,
        "description_ar": "هاجر المسلمون الأوائل إلى الحبشة فرارا من اضطهاد قريش",
        "description_en": "Early Muslims migrated to Abyssinia fleeing Quraysh persecution",
        "related_verses": ["39:10", "4:97"],
        "lessons": ["Seeking safety for religion", "Justice of righteous rulers"],
        "participants": ["جعفر بن أبي طالب", "النجاشي"],
    },
    "isra_miraj": {
        "title_ar": "الإسراء والمعراج",
        "title_en": "Night Journey and Ascension",
        "era": SiraEra.MECCAN,
        "year_hijri": None,
        "year_ce": 621,
        "description_ar": "رحلة النبي الليلية إلى بيت المقدس ثم الصعود إلى السماوات",
        "description_en": "The Prophet's night journey to Jerusalem then ascension through heavens",
        "related_verses": ["17:1", "53:1-18"],
        "lessons": ["Divine honor", "Prescription of prayer", "Faith in unseen"],
        "participants": ["جبريل", "الأنبياء السابقون"],
    },
    "hijra_medina": {
        "title_ar": "الهجرة إلى المدينة",
        "title_en": "Migration to Medina",
        "era": SiraEra.MEDINAN,
        "year_hijri": 1,
        "year_ce": 622,
        "description_ar": "هاجر النبي من مكة إلى المدينة تأسيسا للدولة الإسلامية",
        "description_en": "The Prophet migrated from Mecca to Medina establishing the Islamic state",
        "related_verses": ["8:30", "9:40"],
        "lessons": ["Sacrifice for religion", "Planning and tawakkul", "Brotherhood"],
        "participants": ["أبو بكر الصديق", "الأنصار"],
    },
    "badr": {
        "title_ar": "غزوة بدر",
        "title_en": "Battle of Badr",
        "era": SiraEra.MEDINAN,
        "year_hijri": 2,
        "year_ce": 624,
        "description_ar": "أول معركة كبرى بين المسلمين وقريش، انتصر فيها المسلمون",
        "description_en": "First major battle between Muslims and Quraysh, Muslims were victorious",
        "related_verses": ["3:13", "8:5-19", "8:41-48"],
        "lessons": ["Divine support", "Patience brings victory", "Quality over quantity"],
        "participants": ["313 صحابي", "قريش"],
    },
    "uhud": {
        "title_ar": "غزوة أحد",
        "title_en": "Battle of Uhud",
        "era": SiraEra.MEDINAN,
        "year_hijri": 3,
        "year_ce": 625,
        "description_ar": "المعركة الثانية مع قريش، تعلم فيها المسلمون درس الطاعة",
        "description_en": "Second battle with Quraysh, Muslims learned the lesson of obedience",
        "related_verses": ["3:121-175"],
        "lessons": ["Obedience to leadership", "Testing through setbacks", "Steadfastness"],
        "participants": ["حمزة بن عبد المطلب", "خالد بن الوليد"],
    },
    "khandaq": {
        "title_ar": "غزوة الخندق",
        "title_en": "Battle of the Trench",
        "era": SiraEra.MEDINAN,
        "year_hijri": 5,
        "year_ce": 627,
        "description_ar": "حاصر الأحزاب المدينة لكن الله صرفهم بالريح",
        "description_en": "Confederate forces besieged Medina but Allah repelled them with wind",
        "related_verses": ["33:9-27"],
        "lessons": ["Unity against adversity", "Innovative thinking", "Trust in Allah"],
        "participants": ["سلمان الفارسي", "الأحزاب"],
    },
    "hudaybiyyah": {
        "title_ar": "صلح الحديبية",
        "title_en": "Treaty of Hudaybiyyah",
        "era": SiraEra.MEDINAN,
        "year_hijri": 6,
        "year_ce": 628,
        "description_ar": "معاهدة سلام مع قريش كانت فتحا مبينا",
        "description_en": "Peace treaty with Quraysh that was a clear victory",
        "related_verses": ["48:1-29"],
        "lessons": ["Strategic patience", "Long-term vision", "Peace when beneficial"],
        "participants": ["قريش", "سهيل بن عمرو"],
    },
    "fath_makkah": {
        "title_ar": "فتح مكة",
        "title_en": "Conquest of Mecca",
        "era": SiraEra.MEDINAN,
        "year_hijri": 8,
        "year_ce": 630,
        "description_ar": "دخل المسلمون مكة فاتحين وعفا النبي عن أهلها",
        "description_en": "Muslims entered Mecca victoriously and the Prophet pardoned its people",
        "related_verses": ["110:1-3", "48:27"],
        "lessons": ["Forgiveness after victory", "Humility in success", "Purifying the Kaaba"],
        "participants": ["10000 صحابي", "أبو سفيان"],
    },
    "farewell_pilgrimage": {
        "title_ar": "حجة الوداع",
        "title_en": "Farewell Pilgrimage",
        "era": SiraEra.FINAL_YEARS,
        "year_hijri": 10,
        "year_ce": 632,
        "description_ar": "آخر حج للنبي، ألقى فيه خطبته الشهيرة",
        "description_en": "The Prophet's final Hajj where he delivered his famous sermon",
        "related_verses": ["5:3", "3:97"],
        "lessons": ["Completion of religion", "Human rights", "Unity of Muslims"],
        "participants": ["100000+ حاج"],
    },
}


# =============================================================================
# VERSE-DISCIPLINE MAPPINGS
# =============================================================================

VERSE_DISCIPLINE_MAP = {
    "2:43": {
        "fiqh": ["salah_obligation", "zakat_obligation"],
        "hadith": ["five_pillars"],
        "sira": [],
        "topics": ["worship", "pillars"],
    },
    "2:183": {
        "fiqh": ["fasting_obligation"],
        "hadith": ["five_pillars"],
        "sira": [],
        "topics": ["fasting", "worship"],
    },
    "2:185": {
        "fiqh": ["fasting_obligation"],
        "hadith": [],
        "sira": [],
        "topics": ["ramadan", "quran_revelation"],
    },
    "2:275": {
        "fiqh": ["riba_prohibition"],
        "hadith": [],
        "sira": [],
        "topics": ["finance", "prohibition"],
    },
    "3:97": {
        "fiqh": ["hajj_obligation"],
        "hadith": ["five_pillars"],
        "sira": ["farewell_pilgrimage"],
        "topics": ["hajj", "worship"],
    },
    "4:11": {
        "fiqh": ["inheritance_rules"],
        "hadith": [],
        "sira": [],
        "topics": ["inheritance", "family_law"],
    },
    "17:1": {
        "fiqh": [],
        "hadith": [],
        "sira": ["isra_miraj"],
        "topics": ["miracle", "prophecy"],
    },
    "24:31": {
        "fiqh": ["hijab_ruling"],
        "hadith": [],
        "sira": [],
        "topics": ["dress_code", "modesty"],
    },
    "33:59": {
        "fiqh": ["hijab_ruling"],
        "hadith": [],
        "sira": [],
        "topics": ["dress_code", "women"],
    },
    "48:1": {
        "fiqh": [],
        "hadith": [],
        "sira": ["hudaybiyyah"],
        "topics": ["victory", "treaty"],
    },
    "8:41": {
        "fiqh": [],
        "hadith": [],
        "sira": ["badr"],
        "topics": ["battle", "spoils"],
    },
    "3:121": {
        "fiqh": [],
        "hadith": [],
        "sira": ["uhud"],
        "topics": ["battle", "obedience"],
    },
    "33:9": {
        "fiqh": [],
        "hadith": [],
        "sira": ["khandaq"],
        "topics": ["battle", "siege"],
    },
    "110:1": {
        "fiqh": [],
        "hadith": [],
        "sira": ["fath_makkah"],
        "topics": ["victory", "conversion"],
    },
    "96:1": {
        "fiqh": [],
        "hadith": [],
        "sira": ["first_revelation"],
        "topics": ["revelation", "knowledge"],
    },
}


# =============================================================================
# CROSS-DISCIPLINARY SERVICE
# =============================================================================

class CrossDisciplinaryService:
    """
    Service for integrating cross-disciplinary Islamic knowledge.

    Features:
    - Link verses to Fiqh rulings
    - Connect verses to Hadith references
    - Map verses to Sira events
    - Provide comprehensive understanding
    """

    def __init__(self):
        self._fiqh = FIQH_RULINGS
        self._hadith = HADITH_REFERENCES
        self._sira = SIRA_EVENTS
        self._verse_map = VERSE_DISCIPLINE_MAP

    def get_verse_cross_references(
        self,
        verse_reference: str,
    ) -> Dict[str, Any]:
        """Get all cross-disciplinary references for a verse."""
        if verse_reference not in self._verse_map:
            # Try partial match
            sura_aya = verse_reference.split(":")
            if len(sura_aya) == 2:
                # Check for verse ranges or partial matches
                partial_matches = [
                    v for v in self._verse_map
                    if v.startswith(f"{sura_aya[0]}:")
                ]
                if partial_matches:
                    return self._aggregate_references(partial_matches)

            return {
                "verse_reference": verse_reference,
                "has_references": False,
                "fiqh": [],
                "hadith": [],
                "sira": [],
                "topics": [],
            }

        mapping = self._verse_map[verse_reference]

        return {
            "verse_reference": verse_reference,
            "has_references": True,
            "fiqh": [self._get_fiqh_summary(fid) for fid in mapping.get("fiqh", [])],
            "hadith": [self._get_hadith_summary(hid) for hid in mapping.get("hadith", [])],
            "sira": [self._get_sira_summary(sid) for sid in mapping.get("sira", [])],
            "topics": mapping.get("topics", []),
        }

    def _aggregate_references(self, verses: List[str]) -> Dict[str, Any]:
        """Aggregate references from multiple verses."""
        fiqh_ids = set()
        hadith_ids = set()
        sira_ids = set()
        topics = set()

        for v in verses:
            mapping = self._verse_map.get(v, {})
            fiqh_ids.update(mapping.get("fiqh", []))
            hadith_ids.update(mapping.get("hadith", []))
            sira_ids.update(mapping.get("sira", []))
            topics.update(mapping.get("topics", []))

        return {
            "verses": verses,
            "has_references": bool(fiqh_ids or hadith_ids or sira_ids),
            "fiqh": [self._get_fiqh_summary(fid) for fid in fiqh_ids],
            "hadith": [self._get_hadith_summary(hid) for hid in hadith_ids],
            "sira": [self._get_sira_summary(sid) for sid in sira_ids],
            "topics": list(topics),
        }

    def _get_fiqh_summary(self, ruling_id: str) -> Dict[str, Any]:
        """Get summary of a Fiqh ruling."""
        if ruling_id not in self._fiqh:
            return {"error": f"Ruling {ruling_id} not found"}

        r = self._fiqh[ruling_id]
        return {
            "ruling_id": ruling_id,
            "topic_ar": r["topic_ar"],
            "topic_en": r["topic_en"],
            "ruling_ar": r["ruling_ar"],
            "ruling_en": r["ruling_en"],
            "category": r.get("category", "general"),
        }

    def _get_hadith_summary(self, hadith_id: str) -> Dict[str, Any]:
        """Get summary of a Hadith."""
        if hadith_id not in self._hadith:
            return {"error": f"Hadith {hadith_id} not found"}

        h = self._hadith[hadith_id]
        return {
            "hadith_id": hadith_id,
            "text_ar": h["text_ar"][:100] + "..." if len(h["text_ar"]) > 100 else h["text_ar"],
            "source": h["source"],
            "source_en": h["source_en"],
            "grade": h["grade"].value,
            "narrator_en": h["narrator_en"],
        }

    def _get_sira_summary(self, event_id: str) -> Dict[str, Any]:
        """Get summary of a Sira event."""
        if event_id not in self._sira:
            return {"error": f"Event {event_id} not found"}

        e = self._sira[event_id]
        return {
            "event_id": event_id,
            "title_ar": e["title_ar"],
            "title_en": e["title_en"],
            "era": e["era"].value,
            "year_hijri": e.get("year_hijri"),
        }

    def get_fiqh_ruling(self, ruling_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed Fiqh ruling."""
        if ruling_id not in self._fiqh:
            return None

        r = self._fiqh[ruling_id]
        return {
            "ruling_id": ruling_id,
            "topic_ar": r["topic_ar"],
            "topic_en": r["topic_en"],
            "ruling_ar": r["ruling_ar"],
            "ruling_en": r["ruling_en"],
            "evidence_verses": r["evidence_verses"],
            "evidence_hadith": r["evidence_hadith"],
            "schools_agreement": r["schools_agreement"],
            "conditions": r["conditions"],
            "exceptions": r["exceptions"],
            "category": r.get("category", "general"),
        }

    def get_hadith_details(self, hadith_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed Hadith information."""
        if hadith_id not in self._hadith:
            return None

        h = self._hadith[hadith_id]
        return {
            "hadith_id": hadith_id,
            "text_ar": h["text_ar"],
            "text_en": h["text_en"],
            "narrator": h["narrator"],
            "narrator_en": h["narrator_en"],
            "source": h["source"],
            "source_en": h["source_en"],
            "grade": h["grade"].value,
            "chapter_ar": h["chapter_ar"],
            "chapter_en": h["chapter_en"],
            "number": h["number"],
            "related_verses": h["related_verses"],
            "themes": h["themes"],
        }

    def get_sira_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed Sira event."""
        if event_id not in self._sira:
            return None

        e = self._sira[event_id]
        return {
            "event_id": event_id,
            "title_ar": e["title_ar"],
            "title_en": e["title_en"],
            "era": e["era"].value,
            "year_hijri": e.get("year_hijri"),
            "year_ce": e.get("year_ce"),
            "description_ar": e["description_ar"],
            "description_en": e["description_en"],
            "related_verses": e["related_verses"],
            "lessons": e["lessons"],
            "participants": e["participants"],
        }

    def get_all_fiqh_rulings(
        self,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Fiqh rulings, optionally filtered by category."""
        results = []
        for rid, r in self._fiqh.items():
            if category and r.get("category") != category:
                continue
            results.append({
                "ruling_id": rid,
                "topic_ar": r["topic_ar"],
                "topic_en": r["topic_en"],
                "category": r.get("category", "general"),
                "evidence_verses_count": len(r["evidence_verses"]),
            })
        return results

    def get_all_hadith(
        self,
        grade: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Hadith, optionally filtered."""
        results = []
        for hid, h in self._hadith.items():
            if grade and h["grade"].value != grade:
                continue
            if theme and theme not in h["themes"]:
                continue
            results.append({
                "hadith_id": hid,
                "text_ar": h["text_ar"][:80] + "...",
                "source_en": h["source_en"],
                "grade": h["grade"].value,
                "themes": h["themes"],
            })
        return results

    def get_all_sira_events(
        self,
        era: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Sira events, optionally filtered by era."""
        results = []
        for eid, e in self._sira.items():
            if era and e["era"].value != era:
                continue
            results.append({
                "event_id": eid,
                "title_ar": e["title_ar"],
                "title_en": e["title_en"],
                "era": e["era"].value,
                "year_hijri": e.get("year_hijri"),
            })

        # Sort by year
        results.sort(key=lambda x: x.get("year_hijri") or 0)
        return results

    def get_sira_timeline(self) -> List[Dict[str, Any]]:
        """Get Sira events as a timeline."""
        events = []
        for eid, e in self._sira.items():
            events.append({
                "event_id": eid,
                "title_en": e["title_en"],
                "title_ar": e["title_ar"],
                "era": e["era"].value,
                "year_hijri": e.get("year_hijri"),
                "year_ce": e.get("year_ce"),
            })

        # Sort chronologically
        events.sort(key=lambda x: (x.get("year_ce") or 0, x.get("year_hijri") or 0))
        return events

    def search_by_topic(self, topic: str) -> Dict[str, Any]:
        """Search across all disciplines by topic."""
        topic_lower = topic.lower()

        fiqh_matches = []
        for rid, r in self._fiqh.items():
            if (topic_lower in r["topic_en"].lower() or
                topic_lower in r.get("category", "").lower() or
                any(topic_lower in t.lower() for t in r.get("evidence_verses", []))):
                fiqh_matches.append({
                    "ruling_id": rid,
                    "topic_en": r["topic_en"],
                    "category": r.get("category"),
                })

        hadith_matches = []
        for hid, h in self._hadith.items():
            if (topic_lower in h["text_en"].lower() or
                any(topic_lower in t.lower() for t in h["themes"])):
                hadith_matches.append({
                    "hadith_id": hid,
                    "source_en": h["source_en"],
                    "themes": h["themes"],
                })

        sira_matches = []
        for eid, e in self._sira.items():
            if (topic_lower in e["title_en"].lower() or
                topic_lower in e["description_en"].lower() or
                any(topic_lower in l.lower() for l in e["lessons"])):
                sira_matches.append({
                    "event_id": eid,
                    "title_en": e["title_en"],
                    "era": e["era"].value,
                })

        return {
            "search_topic": topic,
            "fiqh": fiqh_matches,
            "hadith": hadith_matches,
            "sira": sira_matches,
            "total_results": len(fiqh_matches) + len(hadith_matches) + len(sira_matches),
        }

    def get_fiqh_categories(self) -> List[str]:
        """Get all Fiqh categories."""
        categories = set()
        for r in self._fiqh.values():
            if "category" in r:
                categories.add(r["category"])
        return sorted(categories)

    def get_hadith_themes(self) -> List[str]:
        """Get all Hadith themes."""
        themes = set()
        for h in self._hadith.values():
            themes.update(h["themes"])
        return sorted(themes)

    def get_sira_eras(self) -> List[Dict[str, str]]:
        """Get all Sira eras with descriptions."""
        return [
            {"id": "pre_prophethood", "name_ar": "قبل البعثة", "name_en": "Before Prophethood"},
            {"id": "meccan", "name_ar": "العهد المكي", "name_en": "Meccan Period"},
            {"id": "medinan", "name_ar": "العهد المدني", "name_en": "Medinan Period"},
            {"id": "final_years", "name_ar": "السنوات الأخيرة", "name_en": "Final Years"},
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about cross-disciplinary data."""
        return {
            "fiqh_rulings": len(self._fiqh),
            "hadith_references": len(self._hadith),
            "sira_events": len(self._sira),
            "mapped_verses": len(self._verse_map),
            "fiqh_categories": len(self.get_fiqh_categories()),
            "hadith_themes": len(self.get_hadith_themes()),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

cross_disciplinary_service = CrossDisciplinaryService()
