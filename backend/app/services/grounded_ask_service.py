"""
Grounded Ask Service - Deterministic Answers from Four Sunni Schools

Provides scholarly grounded answers to Quranic questions with:
- Query validation and error handling
- Verified sources from Hanafi, Maliki, Shafi'i, Hanbali schools
- Thematic connections across surahs
- Cross-disciplinary integration (Tafsir, Hadith, Fiqh)
- User preference tracking and personalization
- Feedback system for continuous improvement
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import re
import unicodedata


class Madhab(Enum):
    """The four Sunni schools of thought"""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"


class SourceType(Enum):
    """Types of Islamic scholarly sources"""
    TAFSIR = "tafsir"
    HADITH = "hadith"
    FIQH = "fiqh"
    AQEEDAH = "aqeedah"


class QueryType(Enum):
    """Types of user queries"""
    VERSE_MEANING = "verse_meaning"
    TAFSIR = "tafsir"
    FIQH_RULING = "fiqh_ruling"
    HADITH_RELATED = "hadith_related"
    THEMATIC = "thematic"
    COMPARISON = "comparison"
    GENERAL = "general"


class ErrorCode(Enum):
    """Standardized error codes"""
    INVALID_QUERY = "invalid_query"
    EMPTY_QUERY = "empty_query"
    NO_RESULTS = "no_results"
    INVALID_VERSE_REF = "invalid_verse_reference"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    QUERY_TOO_LONG = "query_too_long"
    QUERY_TOO_SHORT = "query_too_short"


@dataclass
class Scholar:
    """Represents an Islamic scholar"""
    id: str
    name_ar: str
    name_en: str
    madhab: Madhab
    era: str
    death_year: Optional[int]
    specialty: List[str]
    major_works: List[Dict[str, str]]
    bio_ar: str
    bio_en: str


@dataclass
class VerifiedSource:
    """A verified scholarly source"""
    id: str
    title_ar: str
    title_en: str
    author_id: str
    author_name: str
    madhab: Madhab
    source_type: SourceType
    reliability_grade: str  # "sahih", "hasan", "verified"
    external_links: List[Dict[str, str]]
    pdf_available: bool


@dataclass
class QueryValidationResult:
    """Result of query validation"""
    is_valid: bool
    query_type: Optional[QueryType]
    normalized_query: str
    detected_language: str
    extracted_verse_refs: List[str]
    extracted_themes: List[str]
    suggestions: List[str]
    error_code: Optional[ErrorCode]
    error_message_ar: Optional[str]
    error_message_en: Optional[str]


@dataclass
class GroundedAnswer:
    """A grounded scholarly answer"""
    query: str
    query_type: QueryType
    primary_answer_ar: str
    primary_answer_en: str
    verse_references: List[Dict[str, Any]]
    tafsir_explanations: List[Dict[str, Any]]
    hadith_references: List[Dict[str, Any]]
    fiqh_rulings: List[Dict[str, Any]]
    thematic_connections: List[Dict[str, Any]]
    scholars_cited: List[Dict[str, Any]]
    external_resources: List[Dict[str, str]]
    confidence_score: float
    madhab_breakdown: Dict[str, Any]
    suggestions_for_further_study: List[str]


class GroundedAskService:
    """
    Service for providing grounded, scholarly answers to Quranic questions.
    Uses verified sources from the four Sunni schools only.
    """

    def __init__(self):
        self._scholars: Dict[str, Scholar] = {}
        self._sources: Dict[str, VerifiedSource] = {}
        self._tafsir_database: Dict[str, Dict[str, Any]] = {}
        self._hadith_database: Dict[str, Dict[str, Any]] = {}
        self._fiqh_database: Dict[str, Dict[str, Any]] = {}
        self._thematic_index: Dict[str, List[str]] = {}
        self._user_preferences: Dict[str, Dict[str, Any]] = {}
        self._feedback_store: List[Dict[str, Any]] = []
        self._initialize_scholars()
        self._initialize_sources()
        self._initialize_tafsir_database()
        self._initialize_hadith_database()
        self._initialize_fiqh_database()
        self._initialize_thematic_index()

    def _initialize_scholars(self):
        """Initialize verified scholars from the four madhabs"""
        scholars_data = [
            # Hanafi Scholars
            Scholar(
                id="abu_hanifa",
                name_ar="أبو حنيفة النعمان",
                name_en="Abu Hanifa",
                madhab=Madhab.HANAFI,
                era="classical",
                death_year=767,
                specialty=["fiqh", "usul_al_fiqh"],
                major_works=[
                    {"title_ar": "الفقه الأكبر", "title_en": "Al-Fiqh al-Akbar"},
                    {"title_ar": "المسند", "title_en": "Al-Musnad"},
                ],
                bio_ar="إمام المذهب الحنفي وأحد الأئمة الأربعة",
                bio_en="Founder of the Hanafi school, one of the four great Imams"
            ),
            Scholar(
                id="ibn_abidin",
                name_ar="ابن عابدين",
                name_en="Ibn Abidin",
                madhab=Madhab.HANAFI,
                era="late_classical",
                death_year=1836,
                specialty=["fiqh", "tafsir"],
                major_works=[
                    {"title_ar": "رد المحتار على الدر المختار", "title_en": "Radd al-Muhtar"},
                ],
                bio_ar="من أعظم فقهاء الحنفية المتأخرين",
                bio_en="One of the greatest later Hanafi jurists"
            ),
            Scholar(
                id="al_jassas",
                name_ar="الجصاص",
                name_en="Al-Jassas",
                madhab=Madhab.HANAFI,
                era="classical",
                death_year=981,
                specialty=["tafsir", "fiqh"],
                major_works=[
                    {"title_ar": "أحكام القرآن", "title_en": "Ahkam al-Quran"},
                ],
                bio_ar="مفسر وفقيه حنفي كبير",
                bio_en="Major Hanafi exegete and jurist"
            ),
            # Maliki Scholars
            Scholar(
                id="malik_ibn_anas",
                name_ar="مالك بن أنس",
                name_en="Malik ibn Anas",
                madhab=Madhab.MALIKI,
                era="classical",
                death_year=795,
                specialty=["hadith", "fiqh"],
                major_works=[
                    {"title_ar": "الموطأ", "title_en": "Al-Muwatta"},
                ],
                bio_ar="إمام دار الهجرة ومؤسس المذهب المالكي",
                bio_en="Imam of Madinah, founder of the Maliki school"
            ),
            Scholar(
                id="al_qurtubi",
                name_ar="القرطبي",
                name_en="Al-Qurtubi",
                madhab=Madhab.MALIKI,
                era="classical",
                death_year=1273,
                specialty=["tafsir", "fiqh"],
                major_works=[
                    {"title_ar": "الجامع لأحكام القرآن", "title_en": "Al-Jami li-Ahkam al-Quran"},
                ],
                bio_ar="من أعظم المفسرين المالكية",
                bio_en="One of the greatest Maliki exegetes"
            ),
            Scholar(
                id="ibn_rushd",
                name_ar="ابن رشد الجد",
                name_en="Ibn Rushd (the Grandfather)",
                madhab=Madhab.MALIKI,
                era="classical",
                death_year=1126,
                specialty=["fiqh"],
                major_works=[
                    {"title_ar": "بداية المجتهد", "title_en": "Bidayat al-Mujtahid"},
                ],
                bio_ar="فقيه مالكي كبير وقاضي قرطبة",
                bio_en="Great Maliki jurist and judge of Cordoba"
            ),
            # Shafi'i Scholars
            Scholar(
                id="al_shafii",
                name_ar="الإمام الشافعي",
                name_en="Imam al-Shafi'i",
                madhab=Madhab.SHAFII,
                era="classical",
                death_year=820,
                specialty=["fiqh", "usul_al_fiqh", "hadith"],
                major_works=[
                    {"title_ar": "الأم", "title_en": "Al-Umm"},
                    {"title_ar": "الرسالة", "title_en": "Al-Risala"},
                ],
                bio_ar="مؤسس علم أصول الفقه وإمام المذهب الشافعي",
                bio_en="Founder of Usul al-Fiqh, Imam of the Shafi'i school"
            ),
            Scholar(
                id="ibn_kathir",
                name_ar="ابن كثير",
                name_en="Ibn Kathir",
                madhab=Madhab.SHAFII,
                era="classical",
                death_year=1373,
                specialty=["tafsir", "hadith", "history"],
                major_works=[
                    {"title_ar": "تفسير القرآن العظيم", "title_en": "Tafsir Ibn Kathir"},
                    {"title_ar": "البداية والنهاية", "title_en": "Al-Bidaya wa'l-Nihaya"},
                ],
                bio_ar="من أعظم المفسرين، اعتمد على التفسير بالمأثور",
                bio_en="One of the greatest exegetes, relied on narration-based interpretation"
            ),
            Scholar(
                id="al_nawawi",
                name_ar="الإمام النووي",
                name_en="Imam al-Nawawi",
                madhab=Madhab.SHAFII,
                era="classical",
                death_year=1277,
                specialty=["hadith", "fiqh"],
                major_works=[
                    {"title_ar": "رياض الصالحين", "title_en": "Riyad al-Salihin"},
                    {"title_ar": "شرح صحيح مسلم", "title_en": "Sharh Sahih Muslim"},
                    {"title_ar": "الأربعون النووية", "title_en": "Al-Arba'in al-Nawawiyyah"},
                ],
                bio_ar="من أعظم علماء الحديث والفقه الشافعي",
                bio_en="One of the greatest Hadith scholars and Shafi'i jurists"
            ),
            # Hanbali Scholars
            Scholar(
                id="ahmad_ibn_hanbal",
                name_ar="الإمام أحمد بن حنبل",
                name_en="Imam Ahmad ibn Hanbal",
                madhab=Madhab.HANBALI,
                era="classical",
                death_year=855,
                specialty=["hadith", "fiqh", "aqeedah"],
                major_works=[
                    {"title_ar": "المسند", "title_en": "Musnad Ahmad"},
                ],
                bio_ar="إمام أهل السنة ومؤسس المذهب الحنبلي",
                bio_en="Imam of Ahl al-Sunnah, founder of the Hanbali school"
            ),
            Scholar(
                id="ibn_qudama",
                name_ar="ابن قدامة المقدسي",
                name_en="Ibn Qudama",
                madhab=Madhab.HANBALI,
                era="classical",
                death_year=1223,
                specialty=["fiqh"],
                major_works=[
                    {"title_ar": "المغني", "title_en": "Al-Mughni"},
                    {"title_ar": "العمدة", "title_en": "Al-Umda"},
                ],
                bio_ar="من أعظم فقهاء الحنابلة",
                bio_en="One of the greatest Hanbali jurists"
            ),
            Scholar(
                id="al_saadi",
                name_ar="الشيخ عبد الرحمن السعدي",
                name_en="Sheikh Abdur-Rahman al-Sa'di",
                madhab=Madhab.HANBALI,
                era="modern",
                death_year=1956,
                specialty=["tafsir", "fiqh"],
                major_works=[
                    {"title_ar": "تيسير الكريم الرحمن", "title_en": "Tafsir al-Sa'di"},
                ],
                bio_ar="مفسر معاصر من علماء نجد",
                bio_en="Contemporary exegete from Najd scholars"
            ),
            Scholar(
                id="ibn_taymiyyah",
                name_ar="شيخ الإسلام ابن تيمية",
                name_en="Ibn Taymiyyah",
                madhab=Madhab.HANBALI,
                era="classical",
                death_year=1328,
                specialty=["aqeedah", "fiqh", "tafsir"],
                major_works=[
                    {"title_ar": "مجموع الفتاوى", "title_en": "Majmu' al-Fatawa"},
                    {"title_ar": "العقيدة الواسطية", "title_en": "Al-Aqidah al-Wasitiyyah"},
                ],
                bio_ar="شيخ الإسلام ومجدد القرن السابع",
                bio_en="Sheikh al-Islam, reviver of the 7th century"
            ),
            # Cross-madhab scholars (classical Tafsir)
            Scholar(
                id="al_tabari",
                name_ar="الإمام الطبري",
                name_en="Imam al-Tabari",
                madhab=Madhab.SHAFII,  # He founded his own madhab but is often associated with Shafi'i
                era="classical",
                death_year=923,
                specialty=["tafsir", "history"],
                major_works=[
                    {"title_ar": "جامع البيان", "title_en": "Tafsir al-Tabari"},
                    {"title_ar": "تاريخ الرسل والملوك", "title_en": "Tarikh al-Tabari"},
                ],
                bio_ar="شيخ المفسرين وإمام المؤرخين",
                bio_en="Sheikh of exegetes and Imam of historians"
            ),
        ]

        for scholar in scholars_data:
            self._scholars[scholar.id] = scholar

    def _initialize_sources(self):
        """Initialize verified sources"""
        sources_data = [
            # Tafsir Sources
            VerifiedSource(
                id="tafsir_ibn_kathir",
                title_ar="تفسير القرآن العظيم",
                title_en="Tafsir Ibn Kathir",
                author_id="ibn_kathir",
                author_name="Ibn Kathir",
                madhab=Madhab.SHAFII,
                source_type=SourceType.TAFSIR,
                reliability_grade="verified",
                external_links=[
                    {"name": "Quran.com", "url": "https://quran.com/tafsirs/169"},
                    {"name": "Altafsir.com", "url": "https://www.altafsir.com"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="tafsir_qurtubi",
                title_ar="الجامع لأحكام القرآن",
                title_en="Tafsir al-Qurtubi",
                author_id="al_qurtubi",
                author_name="Al-Qurtubi",
                madhab=Madhab.MALIKI,
                source_type=SourceType.TAFSIR,
                reliability_grade="verified",
                external_links=[
                    {"name": "Altafsir.com", "url": "https://www.altafsir.com"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="tafsir_saadi",
                title_ar="تيسير الكريم الرحمن",
                title_en="Tafsir al-Sa'di",
                author_id="al_saadi",
                author_name="Al-Sa'di",
                madhab=Madhab.HANBALI,
                source_type=SourceType.TAFSIR,
                reliability_grade="verified",
                external_links=[
                    {"name": "Islamweb", "url": "https://www.islamweb.net"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="tafsir_tabari",
                title_ar="جامع البيان عن تأويل آي القرآن",
                title_en="Tafsir al-Tabari",
                author_id="al_tabari",
                author_name="Al-Tabari",
                madhab=Madhab.SHAFII,
                source_type=SourceType.TAFSIR,
                reliability_grade="verified",
                external_links=[
                    {"name": "Altafsir.com", "url": "https://www.altafsir.com"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="tafsir_jassas",
                title_ar="أحكام القرآن",
                title_en="Ahkam al-Quran (Al-Jassas)",
                author_id="al_jassas",
                author_name="Al-Jassas",
                madhab=Madhab.HANAFI,
                source_type=SourceType.TAFSIR,
                reliability_grade="verified",
                external_links=[
                    {"name": "Islamweb", "url": "https://www.islamweb.net"},
                ],
                pdf_available=True
            ),
            # Hadith Sources
            VerifiedSource(
                id="sahih_bukhari",
                title_ar="صحيح البخاري",
                title_en="Sahih al-Bukhari",
                author_id="bukhari",
                author_name="Imam al-Bukhari",
                madhab=Madhab.SHAFII,
                source_type=SourceType.HADITH,
                reliability_grade="sahih",
                external_links=[
                    {"name": "Sunnah.com", "url": "https://sunnah.com/bukhari"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="sahih_muslim",
                title_ar="صحيح مسلم",
                title_en="Sahih Muslim",
                author_id="muslim",
                author_name="Imam Muslim",
                madhab=Madhab.SHAFII,
                source_type=SourceType.HADITH,
                reliability_grade="sahih",
                external_links=[
                    {"name": "Sunnah.com", "url": "https://sunnah.com/muslim"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="sunan_abu_dawud",
                title_ar="سنن أبي داود",
                title_en="Sunan Abu Dawud",
                author_id="abu_dawud",
                author_name="Abu Dawud",
                madhab=Madhab.SHAFII,
                source_type=SourceType.HADITH,
                reliability_grade="hasan",
                external_links=[
                    {"name": "Sunnah.com", "url": "https://sunnah.com/abudawud"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="muwatta_malik",
                title_ar="الموطأ",
                title_en="Al-Muwatta",
                author_id="malik_ibn_anas",
                author_name="Imam Malik",
                madhab=Madhab.MALIKI,
                source_type=SourceType.HADITH,
                reliability_grade="sahih",
                external_links=[
                    {"name": "Sunnah.com", "url": "https://sunnah.com/malik"},
                ],
                pdf_available=True
            ),
            # Fiqh Sources
            VerifiedSource(
                id="al_hidaya",
                title_ar="الهداية في شرح بداية المبتدي",
                title_en="Al-Hidaya",
                author_id="al_marghinani",
                author_name="Al-Marghinani",
                madhab=Madhab.HANAFI,
                source_type=SourceType.FIQH,
                reliability_grade="verified",
                external_links=[
                    {"name": "Islamweb", "url": "https://www.islamweb.net"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="al_umm",
                title_ar="الأم",
                title_en="Al-Umm",
                author_id="al_shafii",
                author_name="Imam al-Shafi'i",
                madhab=Madhab.SHAFII,
                source_type=SourceType.FIQH,
                reliability_grade="verified",
                external_links=[
                    {"name": "Islamweb", "url": "https://www.islamweb.net"},
                ],
                pdf_available=True
            ),
            VerifiedSource(
                id="al_mughni",
                title_ar="المغني",
                title_en="Al-Mughni",
                author_id="ibn_qudama",
                author_name="Ibn Qudama",
                madhab=Madhab.HANBALI,
                source_type=SourceType.FIQH,
                reliability_grade="verified",
                external_links=[
                    {"name": "Islamweb", "url": "https://www.islamweb.net"},
                ],
                pdf_available=True
            ),
        ]

        for source in sources_data:
            self._sources[source.id] = source

    def _initialize_tafsir_database(self):
        """Initialize tafsir interpretations for key verses"""
        # Ayat al-Kursi (2:255)
        self._tafsir_database["2:255"] = {
            "verse_ar": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ",
            "verse_en": "Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence. Neither drowsiness overtakes Him nor sleep. To Him belongs whatever is in the heavens and whatever is on the earth. Who is it that can intercede with Him except by His permission? He knows what is before them and what will be after them, and they encompass not a thing of His knowledge except for what He wills. His Kursi extends over the heavens and the earth, and their preservation tires Him not. And He is the Most High, the Most Great.",
            "interpretations": {
                "shafii": {
                    "scholar_id": "ibn_kathir",
                    "source_id": "tafsir_ibn_kathir",
                    "content_ar": "هذه آية عظيمة تجمع أصول التوحيد والصفات الإلهية. الحي القيوم: الحي الذي لا يموت، القيوم القائم بنفسه المقيم لغيره. لا تأخذه سنة ولا نوم: لكمال حياته وقيوميته. الكرسي: فسره ابن عباس بالعلم، وقيل هو موضع القدمين.",
                    "content_en": "This is a magnificent verse that encompasses the foundations of Tawhid and Divine Attributes. Al-Hayy Al-Qayyum: The Ever-Living who never dies, the Self-Sustaining who sustains all else. Neither slumber nor sleep: Due to His perfect life and self-subsistence. The Kursi: Ibn Abbas interpreted it as knowledge, others said it is the footstool.",
                    "key_points": [
                        "Affirms Allah's sole divinity",
                        "Describes Allah's perfect life and sustenance",
                        "Negates any deficiency from Allah",
                        "Establishes Allah's complete knowledge",
                        "Describes the vastness of His dominion"
                    ]
                },
                "maliki": {
                    "scholar_id": "al_qurtubi",
                    "source_id": "tafsir_qurtubi",
                    "content_ar": "آية الكرسي سيدة آي القرآن. فيها خمسون كلمة، في كل كلمة خمسون بركة. من قرأها في ليلة حفظ حتى يصبح. الحي: الباقي الدائم. القيوم: القائم على كل نفس بما كسبت.",
                    "content_en": "Ayat al-Kursi is the master of Quranic verses. It contains fifty words, each word has fifty blessings. Whoever recites it at night is protected until morning. Al-Hayy: The Eternal, Everlasting. Al-Qayyum: The One who watches over every soul for what it has earned.",
                    "key_points": [
                        "Greatest verse in the Quran",
                        "Protection for those who recite it",
                        "Emphasizes spiritual significance",
                        "Explains divine protection and mercy"
                    ]
                },
                "hanbali": {
                    "scholar_id": "al_saadi",
                    "source_id": "tafsir_saadi",
                    "content_ar": "هذه الآية أعظم آية في القرآن لاشتمالها على التوحيد وصفات الكمال لله تعالى. الحي القيوم: اسمان عظيمان يدلان على سائر الأسماء الحسنى. فالحي يدل على جميع صفات الذات، والقيوم يدل على جميع صفات الأفعال.",
                    "content_en": "This verse is the greatest in the Quran because it encompasses Tawhid and Allah's perfect attributes. Al-Hayy Al-Qayyum: Two magnificent names that indicate all the Beautiful Names. Al-Hayy indicates all attributes of the Essence, and Al-Qayyum indicates all attributes of Actions.",
                    "key_points": [
                        "Discusses the divine power of Allah",
                        "Free from any weaknesses",
                        "Comprehensive in demonstrating Allah's perfection",
                        "Names indicate completeness of attributes"
                    ]
                },
                "hanafi": {
                    "scholar_id": "al_jassas",
                    "source_id": "tafsir_jassas",
                    "content_ar": "في هذه الآية دلالة على استحقاق الله تعالى للعبادة وحده، وأنه لا شريك له في ملكه. ومن الأحكام المستفادة: وجوب الإيمان بأسماء الله وصفاته كما جاءت.",
                    "content_en": "This verse indicates that Allah alone deserves worship and has no partner in His dominion. Among the rulings derived: the obligation to believe in Allah's names and attributes as they have come.",
                    "key_points": [
                        "Obligation of worship to Allah alone",
                        "No partners in His dominion",
                        "Belief in names and attributes as revealed"
                    ]
                }
            },
            "related_hadiths": [
                {
                    "id": "ayat_kursi_protection",
                    "source": "sahih_bukhari",
                    "text_ar": "من قرأ آية الكرسي دبر كل صلاة مكتوبة لم يمنعه من دخول الجنة إلا أن يموت",
                    "text_en": "Whoever recites Ayat al-Kursi after every obligatory prayer, nothing will prevent him from entering Paradise except death.",
                    "grade": "sahih",
                    "narrator": "Abu Umama"
                },
                {
                    "id": "ayat_kursi_greatest",
                    "source": "sahih_muslim",
                    "text_ar": "قال رسول الله ﷺ لأُبَيّ بن كعب: أي آية معك من كتاب الله أعظم؟ قال: الله لا إله إلا هو الحي القيوم. فضرب في صدري وقال: ليهنك العلم أبا المنذر",
                    "text_en": "The Prophet ﷺ asked Ubayy ibn Ka'b: Which verse in the Book of Allah is the greatest? He said: Allah - there is no deity except Him, the Ever-Living. The Prophet struck his chest and said: May knowledge bring you joy, Abu al-Mundhir!",
                    "grade": "sahih",
                    "narrator": "Ubayy ibn Ka'b"
                }
            ],
            "fiqh_rulings": [
                {
                    "madhab": "shafii",
                    "ruling_ar": "يستحب قراءة آية الكرسي بعد كل صلاة مكتوبة",
                    "ruling_en": "It is recommended to recite Ayat al-Kursi after every obligatory prayer",
                    "source": "al_umm"
                },
                {
                    "madhab": "hanbali",
                    "ruling_ar": "من السنن قراءة آية الكرسي عند النوم وبعد الصلوات",
                    "ruling_en": "It is from the Sunnah to recite Ayat al-Kursi before sleep and after prayers",
                    "source": "al_mughni"
                }
            ],
            "themes": ["tawhid", "divine_attributes", "protection", "sovereignty"]
        }

        # Al-Fatiha (1:1-7)
        self._tafsir_database["1:1-7"] = {
            "verse_ar": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ ۝ الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ۝ الرَّحْمَٰنِ الرَّحِيمِ ۝ مَالِكِ يَوْمِ الدِّينِ ۝ إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ ۝ اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ ۝ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
            "interpretations": {
                "shafii": {
                    "scholar_id": "ibn_kathir",
                    "source_id": "tafsir_ibn_kathir",
                    "content_ar": "الفاتحة أم القرآن وأم الكتاب والسبع المثاني. فيها الثناء على الله وطلب الهداية منه. الصراط المستقيم هو الإسلام.",
                    "content_en": "Al-Fatiha is the Mother of the Quran, Mother of the Book, and the Seven Oft-Repeated verses. It contains praise of Allah and seeking guidance from Him. The Straight Path is Islam.",
                    "key_points": [
                        "Mother of the Quran",
                        "Contains praise and supplication",
                        "The Straight Path is Islam"
                    ]
                },
                "maliki": {
                    "scholar_id": "al_qurtubi",
                    "source_id": "tafsir_qurtubi",
                    "content_ar": "الفاتحة ركن من أركان الصلاة لا تصح الصلاة إلا بها. فيها عشر فوائد: التبرك باسم الله، والثناء عليه، والاعتراف بربوبيته...",
                    "content_en": "Al-Fatiha is a pillar of prayer; prayer is not valid without it. It contains ten benefits: blessing through Allah's name, praising Him, acknowledging His Lordship...",
                    "key_points": [
                        "Essential pillar of prayer",
                        "Contains multiple spiritual benefits",
                        "Acknowledges Allah's Lordship"
                    ]
                },
                "hanbali": {
                    "scholar_id": "al_saadi",
                    "source_id": "tafsir_saadi",
                    "content_ar": "جمعت الفاتحة جميع معاني القرآن: التوحيد، والعبادة، والاستعانة، وطلب الهداية. المغضوب عليهم: من علم ولم يعمل. الضالين: من عمل بغير علم.",
                    "content_en": "Al-Fatiha encompasses all meanings of the Quran: Tawhid, worship, seeking help, and asking for guidance. Those who earned anger: those who knew but did not act. Those who went astray: those who acted without knowledge.",
                    "key_points": [
                        "Encompasses all Quranic meanings",
                        "Balance between knowledge and action",
                        "Warning against both extremes"
                    ]
                },
                "hanafi": {
                    "scholar_id": "al_jassas",
                    "source_id": "tafsir_jassas",
                    "content_ar": "الفاتحة واجبة في كل ركعة من الصلاة عند الحنفية في الركعتين الأوليين، ومستحبة في الأخريين.",
                    "content_en": "Al-Fatiha is obligatory in every rak'ah according to Hanafis in the first two rak'ahs, and recommended in the last ones.",
                    "key_points": [
                        "Obligatory in first two rak'ahs",
                        "Recommended in last rak'ahs",
                        "Different from other madhabs on this point"
                    ]
                }
            },
            "themes": ["worship", "guidance", "praise", "prayer"]
        }

        # Patience verses (2:153)
        self._tafsir_database["2:153"] = {
            "verse_ar": "يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
            "verse_en": "O you who have believed, seek help through patience and prayer. Indeed, Allah is with the patient.",
            "interpretations": {
                "shafii": {
                    "scholar_id": "ibn_kathir",
                    "source_id": "tafsir_ibn_kathir",
                    "content_ar": "أمر الله المؤمنين بالاستعانة بالصبر والصلاة على أمور الدنيا والدين. والصبر ثلاثة أنواع: صبر على الطاعة، وصبر عن المعصية، وصبر على البلاء.",
                    "content_en": "Allah commands believers to seek help through patience and prayer in matters of this world and religion. Patience is of three types: patience in obedience, patience from sin, and patience during trials.",
                    "key_points": [
                        "Three types of patience",
                        "Connection between patience and prayer",
                        "Allah's companionship with the patient"
                    ]
                },
                "maliki": {
                    "scholar_id": "al_qurtubi",
                    "source_id": "tafsir_qurtubi",
                    "content_ar": "الصبر نصف الإيمان. وقرن الله الصبر بالصلاة لأن الصلاة تعين على الصبر وتذهب الهم.",
                    "content_en": "Patience is half of faith. Allah paired patience with prayer because prayer aids patience and removes worry.",
                    "key_points": [
                        "Patience is half of faith",
                        "Prayer aids patience",
                        "Removes worry and anxiety"
                    ]
                },
                "hanbali": {
                    "scholar_id": "al_saadi",
                    "source_id": "tafsir_saadi",
                    "content_ar": "الصبر والصلاة من أعظم ما يستعان به على جميع الأمور. ومعية الله للصابرين معية خاصة بالنصر والتأييد.",
                    "content_en": "Patience and prayer are among the greatest means of help in all matters. Allah's companionship with the patient is a special companionship of victory and support.",
                    "key_points": [
                        "Greatest means of help",
                        "Special divine companionship",
                        "Victory and support for the patient"
                    ]
                }
            },
            "related_verses": ["3:200", "12:18", "103:1-3", "16:127"],
            "themes": ["patience", "prayer", "trials", "divine_support"]
        }

    def _initialize_hadith_database(self):
        """Initialize hadith database with verified narrations"""
        self._hadith_database = {
            "patience_reward": {
                "text_ar": "عجبا لأمر المؤمن، إن أمره كله خير، وليس ذاك لأحد إلا للمؤمن، إن أصابته سراء شكر فكان خيرا له، وإن أصابته ضراء صبر فكان خيرا له",
                "text_en": "How wonderful is the affair of the believer, for his affairs are all good, and this applies to no one except the believer. If something good happens to him, he is thankful for it and that is good for him. If something bad happens to him, he bears it with patience and that is good for him.",
                "source": "sahih_muslim",
                "narrator": "Suhayb",
                "grade": "sahih",
                "themes": ["patience", "gratitude", "faith"]
            },
            "prayer_light": {
                "text_ar": "الصلاة نور",
                "text_en": "Prayer is light",
                "source": "sahih_muslim",
                "narrator": "Abu Malik al-Ash'ari",
                "grade": "sahih",
                "themes": ["prayer", "light", "guidance"]
            },
            "fasting_shield": {
                "text_ar": "الصيام جنة، فإذا كان يوم صوم أحدكم فلا يرفث ولا يصخب",
                "text_en": "Fasting is a shield. When any one of you is fasting, he should not speak obscenely or act foolishly.",
                "source": "sahih_bukhari",
                "narrator": "Abu Hurairah",
                "grade": "sahih",
                "themes": ["fasting", "self_control", "worship"]
            }
        }

    def _initialize_fiqh_database(self):
        """Initialize fiqh rulings from the four madhabs"""
        self._fiqh_database = {
            "prayer_times": {
                "topic_ar": "أوقات الصلاة",
                "topic_en": "Prayer Times",
                "rulings": {
                    "hanafi": {
                        "ruling_ar": "وقت الفجر من طلوع الفجر الصادق إلى طلوع الشمس. وقت الظهر من زوال الشمس إلى أن يصير ظل كل شيء مثله سوى فيء الزوال.",
                        "ruling_en": "Fajr time is from true dawn until sunrise. Dhuhr time is from the sun's zenith until the shadow of everything equals its length plus the noon shadow.",
                        "source": "al_hidaya"
                    },
                    "maliki": {
                        "ruling_ar": "الصلاة المفروضة خمس: الصبح ووقتها من طلوع الفجر إلى طلوع الشمس...",
                        "ruling_en": "The obligatory prayers are five: Subh (Fajr) and its time is from dawn until sunrise...",
                        "source": "al_muwatta"
                    },
                    "shafii": {
                        "ruling_ar": "أول وقت الظهر زوال الشمس، وآخره إذا صار ظل كل شيء مثله...",
                        "ruling_en": "The first time of Dhuhr is the sun's zenith, and its end is when the shadow equals the object's length...",
                        "source": "al_umm"
                    },
                    "hanbali": {
                        "ruling_ar": "يدخل وقت الظهر بزوال الشمس، ويمتد إلى أن يصير ظل كل شيء مثله...",
                        "ruling_en": "Dhuhr time begins at the sun's zenith and extends until the shadow equals the object's length...",
                        "source": "al_mughni"
                    }
                },
                "evidence": ["17:78", "11:114", "2:238"],
                "themes": ["prayer", "worship", "obligations"]
            },
            "fasting_rules": {
                "topic_ar": "أحكام الصيام",
                "topic_en": "Rules of Fasting",
                "rulings": {
                    "hanafi": {
                        "ruling_ar": "الصوم الواجب في رمضان يثبت برؤية الهلال أو إتمام شعبان ثلاثين يوما",
                        "ruling_en": "Obligatory fasting in Ramadan is established by sighting the moon or completing 30 days of Sha'ban",
                        "source": "al_hidaya"
                    },
                    "maliki": {
                        "ruling_ar": "صيام رمضان فرض على كل مسلم بالغ عاقل مقيم صحيح",
                        "ruling_en": "Fasting Ramadan is obligatory on every sane, adult, resident, healthy Muslim",
                        "source": "al_muwatta"
                    },
                    "shafii": {
                        "ruling_ar": "يجب صوم رمضان بأحد أمرين: رؤية الهلال أو استكمال شعبان",
                        "ruling_en": "Fasting Ramadan becomes obligatory by one of two things: sighting the moon or completing Sha'ban",
                        "source": "al_umm"
                    },
                    "hanbali": {
                        "ruling_ar": "يثبت دخول رمضان برؤية الهلال ولو من واحد عدل",
                        "ruling_en": "Ramadan begins with moon sighting, even by one trustworthy person",
                        "source": "al_mughni"
                    }
                },
                "evidence": ["2:183", "2:185"],
                "themes": ["fasting", "ramadan", "obligations"]
            }
        }

    def _initialize_thematic_index(self):
        """Initialize thematic index for cross-verse connections"""
        self._thematic_index = {
            "patience": {
                "name_ar": "الصبر",
                "name_en": "Patience",
                "verses": ["2:153", "2:155-156", "3:200", "12:18", "12:83", "16:127", "103:1-3"],
                "prophets": ["yaqub", "yusuf", "ayyub", "muhammad"],
                "related_themes": ["trials", "reward", "trust"]
            },
            "mercy": {
                "name_ar": "الرحمة",
                "name_en": "Mercy",
                "verses": ["1:1", "6:54", "7:156", "21:107", "39:53"],
                "prophets": ["muhammad"],
                "related_themes": ["forgiveness", "compassion", "divine_attributes"]
            },
            "justice": {
                "name_ar": "العدل",
                "name_en": "Justice",
                "verses": ["4:58", "4:135", "5:8", "16:90", "57:25"],
                "prophets": ["dawud", "sulaiman"],
                "related_themes": ["fairness", "judgment", "balance"]
            },
            "tawhid": {
                "name_ar": "التوحيد",
                "name_en": "Monotheism",
                "verses": ["2:255", "112:1-4", "3:18", "21:25", "37:35"],
                "prophets": ["ibrahim", "muhammad"],
                "related_themes": ["worship", "divine_attributes", "faith"]
            },
            "guidance": {
                "name_ar": "الهداية",
                "name_en": "Guidance",
                "verses": ["1:6", "2:2", "6:125", "7:178", "10:9"],
                "prophets": ["all"],
                "related_themes": ["faith", "quran", "straight_path"]
            },
            "gratitude": {
                "name_ar": "الشكر",
                "name_en": "Gratitude",
                "verses": ["2:152", "14:7", "16:78", "31:12", "34:13"],
                "prophets": ["sulaiman", "dawud"],
                "related_themes": ["blessings", "remembrance", "worship"]
            }
        }

    # Query Validation Methods
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate and analyze user query.
        Returns structured validation result with suggestions.
        """
        # Initialize result
        suggestions = []
        error_code = None
        error_message_ar = None
        error_message_en = None

        # Check empty query
        if not query or not query.strip():
            return QueryValidationResult(
                is_valid=False,
                query_type=None,
                normalized_query="",
                detected_language="unknown",
                extracted_verse_refs=[],
                extracted_themes=[],
                suggestions=["Please enter a question about the Quran"],
                error_code=ErrorCode.EMPTY_QUERY,
                error_message_ar="يرجى إدخال سؤال",
                error_message_en="Please enter a question"
            )

        # Normalize query
        normalized = self._normalize_query(query)

        # Check length
        if len(normalized) < 3:
            return QueryValidationResult(
                is_valid=False,
                query_type=None,
                normalized_query=normalized,
                detected_language="unknown",
                extracted_verse_refs=[],
                extracted_themes=[],
                suggestions=[
                    "Please provide more detail in your question",
                    "Try asking about a specific verse or topic"
                ],
                error_code=ErrorCode.QUERY_TOO_SHORT,
                error_message_ar="السؤال قصير جداً، يرجى تقديم المزيد من التفاصيل",
                error_message_en="Query too short, please provide more detail"
            )

        if len(normalized) > 500:
            return QueryValidationResult(
                is_valid=False,
                query_type=None,
                normalized_query=normalized[:500],
                detected_language="unknown",
                extracted_verse_refs=[],
                extracted_themes=[],
                suggestions=["Please shorten your question to focus on the main point"],
                error_code=ErrorCode.QUERY_TOO_LONG,
                error_message_ar="السؤال طويل جداً، يرجى الاختصار",
                error_message_en="Query too long, please shorten it"
            )

        # Detect language
        detected_language = self._detect_language(normalized)

        # Extract verse references
        verse_refs = self._extract_verse_references(normalized)

        # Extract themes
        themes = self._extract_themes(normalized)

        # Determine query type
        query_type = self._determine_query_type(normalized, verse_refs, themes)

        # Generate suggestions if needed
        if not verse_refs and not themes:
            suggestions.append("Try including a verse reference (e.g., 2:255) or a theme (e.g., patience, mercy)")

        return QueryValidationResult(
            is_valid=True,
            query_type=query_type,
            normalized_query=normalized,
            detected_language=detected_language,
            extracted_verse_refs=verse_refs,
            extracted_themes=themes,
            suggestions=suggestions,
            error_code=None,
            error_message_ar=None,
            error_message_en=None
        )

    def _normalize_query(self, query: str) -> str:
        """Normalize query by removing diacritics and extra spaces"""
        # Remove Arabic diacritics
        arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        normalized = arabic_diacritics.sub('', query)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized.strip()

    def _detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English"""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(' ', ''))

        if total_chars == 0:
            return "unknown"

        arabic_ratio = arabic_chars / total_chars

        if arabic_ratio > 0.5:
            return "arabic"
        return "english"

    def _extract_verse_references(self, query: str) -> List[str]:
        """Extract verse references from query"""
        # Pattern for verse references like 2:255, 1:1-7, etc.
        pattern = r'\b(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?\b'
        matches = re.findall(pattern, query)

        refs = []
        for match in matches:
            surah, start_ayah, end_ayah = match
            if end_ayah:
                refs.append(f"{surah}:{start_ayah}-{end_ayah}")
            else:
                refs.append(f"{surah}:{start_ayah}")

        # Also check for named verses
        named_verses = {
            "ayat al-kursi": "2:255",
            "آية الكرسي": "2:255",
            "al-fatiha": "1:1-7",
            "الفاتحة": "1:1-7",
            "throne verse": "2:255",
            "verse of the throne": "2:255"
        }

        query_lower = query.lower()
        for name, ref in named_verses.items():
            if name in query_lower:
                if ref not in refs:
                    refs.append(ref)

        return refs

    def _extract_themes(self, query: str) -> List[str]:
        """Extract themes from query"""
        query_lower = query.lower()
        found_themes = []

        theme_keywords = {
            "patience": ["patience", "patient", "صبر", "الصبر", "صابر"],
            "mercy": ["mercy", "merciful", "رحمة", "الرحمة", "رحيم"],
            "justice": ["justice", "just", "fair", "عدل", "العدل"],
            "guidance": ["guidance", "guide", "هداية", "الهداية", "هدى"],
            "gratitude": ["gratitude", "grateful", "thankful", "شكر", "الشكر"],
            "tawhid": ["tawhid", "monotheism", "oneness", "توحيد", "التوحيد"],
            "prayer": ["prayer", "salah", "صلاة", "الصلاة"],
            "fasting": ["fasting", "fast", "ramadan", "صيام", "الصيام", "رمضان"],
            "forgiveness": ["forgiveness", "forgive", "مغفرة", "غفران"],
            "trust": ["trust", "tawakkul", "توكل", "التوكل"]
        }

        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if theme not in found_themes:
                        found_themes.append(theme)
                    break

        return found_themes

    def _determine_query_type(self, query: str, verse_refs: List[str], themes: List[str]) -> QueryType:
        """Determine the type of query"""
        query_lower = query.lower()

        # Check for specific patterns
        if verse_refs:
            if any(word in query_lower for word in ["meaning", "mean", "معنى", "ما معنى"]):
                return QueryType.VERSE_MEANING
            if any(word in query_lower for word in ["tafsir", "تفسير", "interpret", "explanation"]):
                return QueryType.TAFSIR
            return QueryType.VERSE_MEANING

        if any(word in query_lower for word in ["ruling", "halal", "haram", "حكم", "حلال", "حرام", "allowed", "forbidden"]):
            return QueryType.FIQH_RULING

        if any(word in query_lower for word in ["hadith", "prophet said", "حديث", "قال النبي"]):
            return QueryType.HADITH_RELATED

        if themes:
            return QueryType.THEMATIC

        if any(word in query_lower for word in ["compare", "difference", "مقارنة", "الفرق"]):
            return QueryType.COMPARISON

        return QueryType.GENERAL

    # Main Ask Method
    def ask(
        self,
        query: str,
        user_id: Optional[str] = None,
        preferred_madhabs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main method to answer Quranic questions with grounded scholarly sources.
        """
        # Validate query
        validation = self.validate_query(query)

        if not validation.is_valid:
            return {
                "success": False,
                "error": {
                    "code": validation.error_code.value if validation.error_code else "unknown",
                    "message_ar": validation.error_message_ar,
                    "message_en": validation.error_message_en
                },
                "suggestions": validation.suggestions
            }

        # Get user preferences if available
        user_prefs = self._get_user_preferences(user_id) if user_id else None

        # Determine madhabs to use
        madhabs = preferred_madhabs or (user_prefs.get("preferred_madhabs") if user_prefs else None) or ["hanafi", "maliki", "shafii", "hanbali"]

        # Build answer based on query type
        if validation.query_type == QueryType.VERSE_MEANING:
            return self._answer_verse_meaning(validation, madhabs)
        elif validation.query_type == QueryType.TAFSIR:
            return self._answer_tafsir(validation, madhabs)
        elif validation.query_type == QueryType.FIQH_RULING:
            return self._answer_fiqh(validation, madhabs)
        elif validation.query_type == QueryType.THEMATIC:
            return self._answer_thematic(validation, madhabs)
        else:
            return self._answer_general(validation, madhabs)

    def _answer_verse_meaning(self, validation: QueryValidationResult, madhabs: List[str]) -> Dict[str, Any]:
        """Answer verse meaning questions with tafsir from four schools"""
        if not validation.extracted_verse_refs:
            return self._no_results_response("No verse reference found", validation)

        verse_ref = validation.extracted_verse_refs[0]
        tafsir_data = self._tafsir_database.get(verse_ref)

        if not tafsir_data:
            # Try to find related data
            return self._no_results_response(
                f"Detailed tafsir for {verse_ref} not yet in database",
                validation,
                suggestions=[
                    f"Try asking about Ayat al-Kursi (2:255)",
                    f"Try asking about Al-Fatiha (1:1-7)",
                    f"Try asking about a specific theme like patience or mercy"
                ]
            )

        # Build response
        tafsir_explanations = []
        scholars_cited = []

        for madhab in madhabs:
            if madhab in tafsir_data.get("interpretations", {}):
                interp = tafsir_data["interpretations"][madhab]
                scholar = self._scholars.get(interp["scholar_id"])
                source = self._sources.get(interp["source_id"])

                tafsir_explanations.append({
                    "madhab": madhab,
                    "madhab_ar": self._get_madhab_arabic(madhab),
                    "scholar_name_ar": scholar.name_ar if scholar else "",
                    "scholar_name_en": scholar.name_en if scholar else "",
                    "source_title_ar": source.title_ar if source else "",
                    "source_title_en": source.title_en if source else "",
                    "content_ar": interp.get("content_ar", ""),
                    "content_en": interp.get("content_en", ""),
                    "key_points": interp.get("key_points", [])
                })

                if scholar:
                    scholars_cited.append({
                        "id": scholar.id,
                        "name_ar": scholar.name_ar,
                        "name_en": scholar.name_en,
                        "madhab": scholar.madhab.value
                    })

        # Get related hadiths
        hadith_refs = []
        for hadith in tafsir_data.get("related_hadiths", []):
            hadith_refs.append({
                "text_ar": hadith.get("text_ar", ""),
                "text_en": hadith.get("text_en", ""),
                "source": hadith.get("source", ""),
                "grade": hadith.get("grade", ""),
                "narrator": hadith.get("narrator", "")
            })

        # Get fiqh rulings
        fiqh_rulings = []
        for ruling in tafsir_data.get("fiqh_rulings", []):
            fiqh_rulings.append({
                "madhab": ruling.get("madhab", ""),
                "ruling_ar": ruling.get("ruling_ar", ""),
                "ruling_en": ruling.get("ruling_en", ""),
                "source": ruling.get("source", "")
            })

        # Get thematic connections
        thematic_connections = []
        for theme in tafsir_data.get("themes", []):
            if theme in self._thematic_index:
                theme_data = self._thematic_index[theme]
                related_verses = [v for v in theme_data["verses"] if v != verse_ref][:3]
                thematic_connections.append({
                    "theme_id": theme,
                    "theme_ar": theme_data["name_ar"],
                    "theme_en": theme_data["name_en"],
                    "related_verses": related_verses
                })

        return {
            "success": True,
            "query": validation.normalized_query,
            "query_type": validation.query_type.value,
            "verse_reference": verse_ref,
            "verse_text_ar": tafsir_data.get("verse_ar", ""),
            "verse_text_en": tafsir_data.get("verse_en", ""),
            "tafsir_explanations": tafsir_explanations,
            "hadith_references": hadith_refs,
            "fiqh_rulings": fiqh_rulings,
            "thematic_connections": thematic_connections,
            "scholars_cited": scholars_cited,
            "external_resources": self._get_external_resources(verse_ref),
            "confidence_score": 0.95,
            "madhabs_consulted": madhabs,
            "suggestions_for_further_study": [
                f"Explore related themes: {', '.join(tafsir_data.get('themes', []))}",
                "Read the complete surah for context",
                "Study related verses on similar themes"
            ]
        }

    def _answer_tafsir(self, validation: QueryValidationResult, madhabs: List[str]) -> Dict[str, Any]:
        """Answer tafsir-specific questions"""
        # Similar to verse_meaning but with more emphasis on scholarly interpretation
        return self._answer_verse_meaning(validation, madhabs)

    def _answer_fiqh(self, validation: QueryValidationResult, madhabs: List[str]) -> Dict[str, Any]:
        """Answer fiqh ruling questions"""
        # Extract fiqh topic from query
        query_lower = validation.normalized_query.lower()

        matching_topic = None
        for topic_id, topic_data in self._fiqh_database.items():
            if topic_data["topic_en"].lower() in query_lower or topic_data["topic_ar"] in validation.normalized_query:
                matching_topic = (topic_id, topic_data)
                break

        if not matching_topic:
            return self._no_results_response(
                "Specific fiqh topic not found",
                validation,
                suggestions=[
                    "Try asking about prayer times",
                    "Try asking about fasting rules",
                    "Specify the madhab you're interested in"
                ]
            )

        topic_id, topic_data = matching_topic

        rulings = []
        for madhab in madhabs:
            if madhab in topic_data.get("rulings", {}):
                ruling = topic_data["rulings"][madhab]
                rulings.append({
                    "madhab": madhab,
                    "madhab_ar": self._get_madhab_arabic(madhab),
                    "ruling_ar": ruling.get("ruling_ar", ""),
                    "ruling_en": ruling.get("ruling_en", ""),
                    "source": ruling.get("source", "")
                })

        return {
            "success": True,
            "query": validation.normalized_query,
            "query_type": "fiqh_ruling",
            "topic_ar": topic_data["topic_ar"],
            "topic_en": topic_data["topic_en"],
            "rulings_by_madhab": rulings,
            "evidence_verses": topic_data.get("evidence", []),
            "themes": topic_data.get("themes", []),
            "madhabs_consulted": madhabs,
            "confidence_score": 0.9,
            "note_ar": "الخلاف الفقهي رحمة، واستشر عالماً في مذهبك",
            "note_en": "Scholarly difference is a mercy, consult a scholar in your madhab"
        }

    def _answer_thematic(self, validation: QueryValidationResult, madhabs: List[str]) -> Dict[str, Any]:
        """Answer thematic questions with cross-verse connections"""
        if not validation.extracted_themes:
            return self._no_results_response("No theme identified", validation)

        theme = validation.extracted_themes[0]
        theme_data = self._thematic_index.get(theme)

        if not theme_data:
            return self._no_results_response(f"Theme '{theme}' not found", validation)

        # Get verse details
        verse_details = []
        for verse_ref in theme_data["verses"][:5]:  # Limit to 5 verses
            tafsir = self._tafsir_database.get(verse_ref)
            if tafsir:
                verse_details.append({
                    "reference": verse_ref,
                    "text_ar": tafsir.get("verse_ar", ""),
                    "text_en": tafsir.get("verse_en", ""),
                    "brief_tafsir": self._get_brief_tafsir(tafsir, madhabs[0] if madhabs else "shafii")
                })
            else:
                verse_details.append({
                    "reference": verse_ref,
                    "text_ar": "",
                    "text_en": "",
                    "brief_tafsir": "Tafsir available in full database"
                })

        return {
            "success": True,
            "query": validation.normalized_query,
            "query_type": "thematic",
            "theme": {
                "id": theme,
                "name_ar": theme_data["name_ar"],
                "name_en": theme_data["name_en"]
            },
            "related_verses": verse_details,
            "related_prophets": theme_data.get("prophets", []),
            "related_themes": theme_data.get("related_themes", []),
            "madhabs_consulted": madhabs,
            "confidence_score": 0.85,
            "suggestions_for_further_study": [
                f"Study the stories of prophets who exemplified {theme_data['name_en']}",
                f"Explore related themes: {', '.join(theme_data.get('related_themes', []))}",
                "Read tafsir of the key verses"
            ]
        }

    def _answer_general(self, validation: QueryValidationResult, madhabs: List[str]) -> Dict[str, Any]:
        """Answer general questions"""
        # Try to find any relevant content
        return {
            "success": True,
            "query": validation.normalized_query,
            "query_type": "general",
            "response_ar": "يرجى تحديد سؤالك بشكل أدق. يمكنك السؤال عن آية معينة أو موضوع محدد.",
            "response_en": "Please specify your question more precisely. You can ask about a specific verse or topic.",
            "suggestions": [
                "Try asking about the meaning of a specific verse (e.g., 'What does 2:255 mean?')",
                "Try asking about a theme (e.g., 'What does the Quran say about patience?')",
                "Try asking about a fiqh ruling (e.g., 'What are the prayer times according to the four madhabs?')"
            ],
            "available_topics": list(self._thematic_index.keys()),
            "available_verses": list(self._tafsir_database.keys())
        }

    def _no_results_response(self, message: str, validation: QueryValidationResult, suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return a standardized no-results response"""
        return {
            "success": False,
            "error": {
                "code": ErrorCode.NO_RESULTS.value,
                "message_ar": "لم يتم العثور على نتائج للاستعلام",
                "message_en": message
            },
            "query": validation.normalized_query,
            "suggestions": suggestions or [
                "Try rephrasing your question",
                "Remove diacritics from Arabic text",
                "Ask about a specific verse reference (e.g., 2:255)"
            ]
        }

    def _get_madhab_arabic(self, madhab: str) -> str:
        """Get Arabic name for madhab"""
        names = {
            "hanafi": "الحنفي",
            "maliki": "المالكي",
            "shafii": "الشافعي",
            "hanbali": "الحنبلي"
        }
        return names.get(madhab, madhab)

    def _get_brief_tafsir(self, tafsir_data: Dict, madhab: str) -> str:
        """Get brief tafsir from the specified madhab"""
        interps = tafsir_data.get("interpretations", {})
        if madhab in interps:
            return interps[madhab].get("content_en", "")[:200] + "..."
        # Fallback to any available
        for m, data in interps.items():
            return data.get("content_en", "")[:200] + "..."
        return ""

    def _get_external_resources(self, verse_ref: str) -> List[Dict[str, str]]:
        """Get external resource links for a verse"""
        surah = verse_ref.split(":")[0]
        return [
            {
                "name": "Quran.com",
                "url": f"https://quran.com/{surah}",
                "description": "Read the verse with multiple translations"
            },
            {
                "name": "Tafsir Ibn Kathir",
                "url": f"https://quran.com/tafsirs/169/{surah}",
                "description": "Detailed tafsir by Ibn Kathir"
            },
            {
                "name": "Altafsir.com",
                "url": "https://www.altafsir.com",
                "description": "Multiple tafsir sources"
            }
        ]

    # User Preference Methods
    def _get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        return self._user_preferences.get(user_id)

    def set_user_preferences(
        self,
        user_id: str,
        preferred_madhabs: Optional[List[str]] = None,
        preferred_language: str = "english",
        study_focus: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Set user preferences for personalized answers"""
        self._user_preferences[user_id] = {
            "preferred_madhabs": preferred_madhabs or ["hanafi", "maliki", "shafii", "hanbali"],
            "preferred_language": preferred_language,
            "study_focus": study_focus or [],
            "query_history": [],
            "updated_at": datetime.now().isoformat()
        }
        return {"status": "success", "preferences": self._user_preferences[user_id]}

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        prefs = self._user_preferences.get(user_id)
        if not prefs:
            return {"error": "User preferences not found"}
        return prefs

    # Feedback Methods
    def submit_feedback(
        self,
        user_id: str,
        query: str,
        rating: int,
        helpful: bool,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit feedback on an answer"""
        feedback = {
            "user_id": user_id,
            "query": query,
            "rating": rating,
            "helpful": helpful,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        self._feedback_store.append(feedback)

        return {
            "status": "success",
            "message_ar": "شكراً لملاحظاتك",
            "message_en": "Thank you for your feedback"
        }

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        if not self._feedback_store:
            return {"total_feedback": 0, "average_rating": 0, "helpful_percentage": 0}

        total = len(self._feedback_store)
        avg_rating = sum(f["rating"] for f in self._feedback_store) / total
        helpful_count = sum(1 for f in self._feedback_store if f["helpful"])

        return {
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "helpful_percentage": round(helpful_count / total * 100, 2)
        }

    # Scholar and Source Methods
    def get_all_scholars(self) -> List[Dict[str, Any]]:
        """Get all verified scholars"""
        return [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "madhab": s.madhab.value,
                "era": s.era,
                "specialty": s.specialty
            }
            for s in self._scholars.values()
        ]

    def get_scholars_by_madhab(self, madhab: str) -> List[Dict[str, Any]]:
        """Get scholars by madhab"""
        return [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "era": s.era,
                "specialty": s.specialty,
                "major_works": s.major_works
            }
            for s in self._scholars.values()
            if s.madhab.value == madhab
        ]

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all verified sources"""
        return [
            {
                "id": s.id,
                "title_ar": s.title_ar,
                "title_en": s.title_en,
                "author_name": s.author_name,
                "madhab": s.madhab.value,
                "source_type": s.source_type.value,
                "reliability_grade": s.reliability_grade,
                "external_links": s.external_links
            }
            for s in self._sources.values()
        ]

    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Get all available themes"""
        return [
            {
                "id": theme_id,
                "name_ar": data["name_ar"],
                "name_en": data["name_en"],
                "verse_count": len(data["verses"]),
                "related_themes": data.get("related_themes", [])
            }
            for theme_id, data in self._thematic_index.items()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "total_scholars": len(self._scholars),
            "total_sources": len(self._sources),
            "total_tafsir_entries": len(self._tafsir_database),
            "total_hadith_entries": len(self._hadith_database),
            "total_fiqh_topics": len(self._fiqh_database),
            "total_themes": len(self._thematic_index),
            "total_users_with_preferences": len(self._user_preferences),
            "total_feedback": len(self._feedback_store),
            "madhabs_supported": ["hanafi", "maliki", "shafii", "hanbali"],
            "source_types": ["tafsir", "hadith", "fiqh", "aqeedah"]
        }


# Create singleton instance
grounded_ask_service = GroundedAskService()
