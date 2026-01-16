"""
Multi-School Tafsir Comparison Service

Provides comprehensive tafsir (Quranic exegesis) from the four major Sunni schools of thought
(Hanafi, Maliki, Shafi'i, Hanbali), enabling users to compare interpretations from various
classical and contemporary scholars of these madhabs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import hashlib


class SchoolOfThought(Enum):
    """The four major Sunni schools of Islamic jurisprudence (madhabs)"""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"


class TafsirMethodology(Enum):
    """Methodological approaches to tafsir"""
    BIL_MATHUR = "bil_mathur"  # Based on transmitted narrations
    BIL_RAY = "bil_ray"  # Based on scholarly opinion/reasoning
    ISHARI = "ishari"  # Spiritual/mystical interpretation
    FIQHI = "fiqhi"  # Jurisprudential focus
    ILMI = "ilmi"  # Scientific interpretation
    ADABI = "adabi"  # Literary/linguistic analysis
    IJTIMAAYI = "ijtimaayi"  # Social interpretation


class TafsirEra(Enum):
    """Historical eras of tafsir scholars"""
    COMPANION = "companion"  # Sahaba
    TABIIN = "tabiin"  # Successors
    CLASSICAL = "classical"  # 3rd-7th century Hijri
    MEDIEVAL = "medieval"  # 7th-12th century Hijri
    MODERN = "modern"  # 13th-14th century Hijri
    CONTEMPORARY = "contemporary"  # 15th century Hijri onwards


@dataclass
class TafsirScholar:
    """Represents a tafsir scholar"""
    id: str
    name_arabic: str
    name_english: str
    birth_year_hijri: Optional[int]
    death_year_hijri: Optional[int]
    era: TafsirEra
    school: SchoolOfThought
    methodology: List[TafsirMethodology]
    tafsir_name: str
    tafsir_name_arabic: str
    specialization: List[str]
    biography_brief: str
    notable_contributions: List[str]


@dataclass
class TafsirEntry:
    """A single tafsir interpretation for a verse"""
    id: str
    scholar_id: str
    surah: int
    ayah: int
    arabic_text: str
    english_translation: str
    key_points: List[str]
    linguistic_analysis: Optional[str]
    historical_context: Optional[str]
    fiqhi_rulings: List[str]
    related_hadiths: List[str]
    cross_references: List[Dict[str, Any]]  # Related verses
    themes: List[str]
    methodology_notes: Optional[str]


@dataclass
class TafsirComparison:
    """Comparison result between multiple tafsir interpretations"""
    surah: int
    ayah: int
    verse_arabic: str
    verse_translation: str
    interpretations: List[Dict[str, Any]]
    common_themes: List[str]
    points_of_agreement: List[str]
    points_of_difference: List[str]
    methodology_comparison: Dict[str, List[str]]
    scholarly_consensus: Optional[str]
    recommended_reading: List[str]


@dataclass
class UserTafsirPreference:
    """User preferences for tafsir study"""
    user_id: str
    preferred_schools: List[SchoolOfThought]
    preferred_methodologies: List[TafsirMethodology]
    preferred_scholars: List[str]
    language_preference: str
    study_level: str  # beginner, intermediate, advanced, scholarly
    saved_comparisons: List[str]
    notes: Dict[str, str]  # verse_key -> user notes
    created_at: datetime = field(default_factory=datetime.now)


class TafsirService:
    """Service for multi-school tafsir comparison and study"""

    def __init__(self):
        self.scholars: Dict[str, TafsirScholar] = {}
        self.tafsir_entries: Dict[str, List[TafsirEntry]] = {}  # verse_key -> entries
        self.user_preferences: Dict[str, UserTafsirPreference] = {}
        self._initialize_scholars()
        self._initialize_sample_tafsir()

    def _initialize_scholars(self):
        """Initialize database of tafsir scholars from the four Sunni madhabs"""
        scholars_data = [
            # Shafi'i Scholars
            TafsirScholar(
                id="ibn_kathir",
                name_arabic="ابن كثير",
                name_english="Ibn Kathir",
                birth_year_hijri=701,
                death_year_hijri=774,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.SHAFII,
                methodology=[TafsirMethodology.BIL_MATHUR],
                tafsir_name="Tafsir al-Quran al-Azim",
                tafsir_name_arabic="تفسير القرآن العظيم",
                specialization=["Hadith", "History", "Narration-based exegesis"],
                biography_brief="Ismail ibn Umar ibn Kathir was a highly influential Islamic scholar and historian. His tafsir is considered one of the most comprehensive based on transmitted reports.",
                notable_contributions=["Pioneered hadith-based tafsir methodology", "Extensive cross-referencing of narrations", "Historical contextualization"]
            ),
            TafsirScholar(
                id="tabari",
                name_arabic="الطبري",
                name_english="Al-Tabari",
                birth_year_hijri=224,
                death_year_hijri=310,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.SHAFII,
                methodology=[TafsirMethodology.BIL_MATHUR, TafsirMethodology.ADABI],
                tafsir_name="Jami al-Bayan an Ta'wil Ay al-Quran",
                tafsir_name_arabic="جامع البيان عن تأويل آي القرآن",
                specialization=["Comprehensive narrations", "Linguistic analysis", "Multiple interpretations"],
                biography_brief="Muhammad ibn Jarir al-Tabari was a Persian scholar who wrote the earliest and most comprehensive tafsir, collecting all available interpretations from early authorities.",
                notable_contributions=["Most comprehensive early tafsir", "Preserved sayings of Companions and Successors", "Linguistic excellence"]
            ),
            TafsirScholar(
                id="baghawi",
                name_arabic="البغوي",
                name_english="Al-Baghawi",
                birth_year_hijri=436,
                death_year_hijri=516,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.SHAFII,
                methodology=[TafsirMethodology.BIL_MATHUR],
                tafsir_name="Ma'alim al-Tanzil",
                tafsir_name_arabic="معالم التنزيل",
                specialization=["Hadith", "Simplified narrations", "Accessible explanation"],
                biography_brief="Al-Husayn ibn Mas'ud al-Baghawi was a Persian Islamic scholar known for his concise and reliable tafsir based on authentic narrations.",
                notable_contributions=["Concise narration-based tafsir", "Removed weak narrations", "Accessible to students"]
            ),
            # Maliki Scholars
            TafsirScholar(
                id="qurtubi",
                name_arabic="القرطبي",
                name_english="Al-Qurtubi",
                birth_year_hijri=600,
                death_year_hijri=671,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.MALIKI,
                methodology=[TafsirMethodology.FIQHI, TafsirMethodology.BIL_RAY],
                tafsir_name="Al-Jami li-Ahkam al-Quran",
                tafsir_name_arabic="الجامع لأحكام القرآن",
                specialization=["Jurisprudence", "Legal rulings", "Comparative fiqh"],
                biography_brief="Abu Abdullah Muhammad al-Qurtubi was an Andalusian Maliki scholar known for his comprehensive treatment of legal rulings derived from the Quran.",
                notable_contributions=["Comprehensive legal analysis", "Comparative jurisprudence", "Practical application of verses"]
            ),
            TafsirScholar(
                id="ibn_atiyyah",
                name_arabic="ابن عطية",
                name_english="Ibn Atiyyah",
                birth_year_hijri=481,
                death_year_hijri=541,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.MALIKI,
                methodology=[TafsirMethodology.ADABI, TafsirMethodology.BIL_RAY],
                tafsir_name="Al-Muharrar al-Wajiz",
                tafsir_name_arabic="المحرر الوجيز",
                specialization=["Arabic linguistics", "Grammar", "Balanced approach"],
                biography_brief="Abu Muhammad Abd al-Haqq ibn Atiyyah was an Andalusian scholar whose tafsir is praised for its linguistic precision and balanced methodology.",
                notable_contributions=["Excellent linguistic analysis", "Balanced between narration and reason", "Influence on later scholars"]
            ),
            TafsirScholar(
                id="ibn_juzayy",
                name_arabic="ابن جزي",
                name_english="Ibn Juzayy",
                birth_year_hijri=693,
                death_year_hijri=741,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.MALIKI,
                methodology=[TafsirMethodology.FIQHI, TafsirMethodology.ADABI],
                tafsir_name="Al-Tashil li-Ulum al-Tanzil",
                tafsir_name_arabic="التسهيل لعلوم التنزيل",
                specialization=["Simplified explanation", "Legal rulings", "Comprehensive yet concise"],
                biography_brief="Abu al-Qasim ibn Juzayy al-Kalbi was an Andalusian Maliki scholar known for his accessible yet comprehensive tafsir.",
                notable_contributions=["Simplified complex topics", "Comprehensive coverage", "Practical guidance"]
            ),
            # Hanafi Scholars
            TafsirScholar(
                id="jassas",
                name_arabic="الجصاص",
                name_english="Al-Jassas",
                birth_year_hijri=305,
                death_year_hijri=370,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.HANAFI,
                methodology=[TafsirMethodology.FIQHI],
                tafsir_name="Ahkam al-Quran",
                tafsir_name_arabic="أحكام القرآن",
                specialization=["Hanafi jurisprudence", "Legal verses", "Fiqhi analysis"],
                biography_brief="Abu Bakr Ahmad al-Jassas was a prominent Hanafi jurist whose tafsir focuses on extracting legal rulings from the Quran according to Hanafi principles.",
                notable_contributions=["Definitive Hanafi legal tafsir", "Detailed fiqhi analysis", "Defense of Hanafi positions"]
            ),
            TafsirScholar(
                id="nasafi",
                name_arabic="النسفي",
                name_english="Al-Nasafi",
                birth_year_hijri=461,
                death_year_hijri=537,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.HANAFI,
                methodology=[TafsirMethodology.ADABI, TafsirMethodology.BIL_RAY],
                tafsir_name="Madarik al-Tanzil",
                tafsir_name_arabic="مدارك التنزيل وحقائق التأويل",
                specialization=["Concise explanation", "Linguistic analysis", "Theological clarity"],
                biography_brief="Abu al-Barakat al-Nasafi was a Hanafi scholar known for his concise yet comprehensive tafsir that balances linguistic and theological analysis.",
                notable_contributions=["Concise and clear", "Widely studied in Hanafi circles", "Balanced approach"]
            ),
            TafsirScholar(
                id="abu_saud",
                name_arabic="أبو السعود",
                name_english="Abu al-Su'ud",
                birth_year_hijri=898,
                death_year_hijri=982,
                era=TafsirEra.MEDIEVAL,
                school=SchoolOfThought.HANAFI,
                methodology=[TafsirMethodology.ADABI, TafsirMethodology.BIL_RAY],
                tafsir_name="Irshad al-Aql al-Salim",
                tafsir_name_arabic="إرشاد العقل السليم إلى مزايا الكتاب الكريم",
                specialization=["Rhetoric", "Eloquence", "Literary analysis"],
                biography_brief="Abu al-Su'ud al-Imadi was the Grand Mufti of the Ottoman Empire, known for his eloquent tafsir focusing on the rhetorical beauty of the Quran.",
                notable_contributions=["Supreme rhetorical analysis", "Literary excellence", "Ottoman-era authority"]
            ),
            # Hanbali Scholars
            TafsirScholar(
                id="saadi",
                name_arabic="السعدي",
                name_english="Al-Saadi",
                birth_year_hijri=1307,
                death_year_hijri=1376,
                era=TafsirEra.MODERN,
                school=SchoolOfThought.HANBALI,
                methodology=[TafsirMethodology.BIL_MATHUR, TafsirMethodology.ADABI],
                tafsir_name="Taysir al-Karim al-Rahman",
                tafsir_name_arabic="تيسير الكريم الرحمن",
                specialization=["Accessibility", "Practical guidance", "Clear explanation"],
                biography_brief="Abd al-Rahman al-Saadi was a Saudi scholar known for his accessible and concise tafsir that focuses on practical application and spiritual benefit.",
                notable_contributions=["Accessible to common reader", "Clear and concise", "Practical spiritual guidance"]
            ),
            TafsirScholar(
                id="ibn_rajab",
                name_arabic="ابن رجب",
                name_english="Ibn Rajab al-Hanbali",
                birth_year_hijri=736,
                death_year_hijri=795,
                era=TafsirEra.CLASSICAL,
                school=SchoolOfThought.HANBALI,
                methodology=[TafsirMethodology.BIL_MATHUR],
                tafsir_name="Tafsir Ibn Rajab",
                tafsir_name_arabic="تفسير ابن رجب الحنبلي",
                specialization=["Hadith", "Spiritual insights", "Narration-based"],
                biography_brief="Zayn al-Din ibn Rajab al-Hanbali was a renowned Hanbali scholar known for his deep spiritual insights and narration-based approach to Quranic interpretation.",
                notable_contributions=["Deep spiritual analysis", "Strong hadith methodology", "Hanbali authority"]
            ),
            TafsirScholar(
                id="shinqiti",
                name_arabic="الشنقيطي",
                name_english="Al-Shinqiti",
                birth_year_hijri=1325,
                death_year_hijri=1393,
                era=TafsirEra.MODERN,
                school=SchoolOfThought.HANBALI,
                methodology=[TafsirMethodology.BIL_MATHUR, TafsirMethodology.ADABI],
                tafsir_name="Adwa al-Bayan",
                tafsir_name_arabic="أضواء البيان في إيضاح القرآن بالقرآن",
                specialization=["Quran explains Quran", "Arabic linguistics", "Legal analysis"],
                biography_brief="Muhammad al-Amin al-Shinqiti was a Mauritanian scholar famous for his methodology of explaining the Quran by the Quran itself.",
                notable_contributions=["Quran-centric methodology", "Linguistic excellence", "Modern classical approach"]
            ),
        ]

        for scholar in scholars_data:
            self.scholars[scholar.id] = scholar

    def _initialize_sample_tafsir(self):
        """Initialize sample tafsir entries for demonstration"""
        # Al-Fatiha verse 1 tafsir entries
        verse_key = "1:1"
        self.tafsir_entries[verse_key] = [
            TafsirEntry(
                id="1_1_ibn_kathir",
                scholar_id="ibn_kathir",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Beginning with Allah's name brings blessing (barakah)",
                    "Al-Rahman indicates encompassing mercy for all creation",
                    "Al-Raheem indicates specific mercy for believers",
                    "The Basmalah is recited to seek Allah's help and blessing"
                ],
                linguistic_analysis="The 'ba' in 'Bismillah' indicates seeking assistance. Rahman is on the pattern of fa'lan indicating intensity and fullness, while Raheem is on the pattern of fa'il indicating constancy.",
                historical_context="The Prophet (PBUH) began his letters and treaties with Bismillah. The Companions continued this practice in all their affairs.",
                fiqhi_rulings=[
                    "Recommended to begin all good deeds with Bismillah",
                    "Scholars differ on whether it is a verse of Al-Fatiha"
                ],
                related_hadiths=[
                    "Every important matter not begun with Bismillah is deficient",
                    "When you eat, mention Allah's name"
                ],
                cross_references=[
                    {"surah": 11, "ayah": 41, "relevance": "Begin in Allah's name"},
                    {"surah": 27, "ayah": 30, "relevance": "Solomon's letter with Bismillah"}
                ],
                themes=["Divine Names", "Mercy", "Beginning with Allah", "Seeking blessing"],
                methodology_notes="Ibn Kathir relies heavily on narrations from the Prophet, Companions, and Successors in explaining this verse."
            ),
            TafsirEntry(
                id="1_1_tabari",
                scholar_id="tabari",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Multiple linguistic interpretations of the structure",
                    "Allah is the proper name of the Creator, unique to Him",
                    "Collection of all scholarly opinions on Rahman and Raheem distinction",
                    "Documentation of debates among early scholars"
                ],
                linguistic_analysis="Tabari presents multiple grammatical analyses: the implied verb could be 'I recite', 'I begin', or 'I seek help'. He documents each scholarly position with evidence.",
                historical_context="Tabari traces the usage of Bismillah from pre-Islamic Arabia through the Prophet's mission, documenting its evolution.",
                fiqhi_rulings=[
                    "Extensive documentation of scholarly differences on Bismillah as verse",
                    "Multiple opinions on recitation in prayer"
                ],
                related_hadiths=[
                    "Comprehensive collection of all narrations about Bismillah",
                    "Chains of transmission carefully documented"
                ],
                cross_references=[
                    {"surah": 96, "ayah": 1, "relevance": "First revelation begins with 'Read in the name'"},
                    {"surah": 55, "ayah": 1, "relevance": "Al-Rahman as Divine Name"}
                ],
                themes=["Divine Names", "Linguistic analysis", "Scholarly consensus", "Early interpretations"],
                methodology_notes="Al-Tabari's methodology is to collect all available interpretations from early authorities and then select the strongest based on evidence."
            ),
            TafsirEntry(
                id="1_1_qurtubi",
                scholar_id="qurtubi",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Legal rulings derived from Bismillah",
                    "Obligation of Bismillah before slaughter",
                    "Scholarly positions on loud vs silent recitation",
                    "Bismillah in contracts and legal documents"
                ],
                linguistic_analysis="Al-Qurtubi analyzes the legal implications of each linguistic element, connecting grammar to jurisprudence.",
                historical_context="Documents how early Muslim communities applied Bismillah in legal and commercial contexts.",
                fiqhi_rulings=[
                    "Obligatory before slaughtering animals",
                    "Recommended before eating and drinking",
                    "Part of contracts according to Maliki school",
                    "Scholarly difference on audible recitation in prayer"
                ],
                related_hadiths=[
                    "That which is slaughtered without Allah's name mentioned is carrion",
                    "Every matter of importance not begun with Allah's name is severed"
                ],
                cross_references=[
                    {"surah": 6, "ayah": 121, "relevance": "Eating meat slaughtered with Allah's name"},
                    {"surah": 5, "ayah": 4, "relevance": "Mention Allah's name when hunting"}
                ],
                themes=["Legal rulings", "Ritual slaughter", "Prayer", "Commerce"],
                methodology_notes="Al-Qurtubi focuses on extracting legal rulings (ahkam) from each verse, comparing positions of the four madhabs."
            ),
            TafsirEntry(
                id="1_1_jassas",
                scholar_id="jassas",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Hanafi position on Bismillah in prayer",
                    "Legal status of Bismillah before actions",
                    "Ruling on Bismillah before slaughter according to Hanafi fiqh",
                    "Whether Bismillah is a verse of Al-Fatiha"
                ],
                linguistic_analysis="Al-Jassas analyzes the grammatical structure to derive legal implications according to Hanafi usul al-fiqh.",
                historical_context="Documents the Hanafi scholarly tradition on applying Bismillah in various legal contexts.",
                fiqhi_rulings=[
                    "Bismillah is not recited aloud in prayer according to Hanafi madhab",
                    "Obligatory to say Bismillah before slaughter",
                    "Recommended before all permissible actions",
                    "Not counted as verse of Al-Fatiha in Hanafi view"
                ],
                related_hadiths=[
                    "Narrations supporting Hanafi positions",
                    "Evidence from Companions' practice"
                ],
                cross_references=[
                    {"surah": 6, "ayah": 121, "relevance": "Legal ruling on mentioning Allah's name"},
                    {"surah": 5, "ayah": 4, "relevance": "Bismillah when hunting"}
                ],
                themes=["Hanafi jurisprudence", "Legal rulings", "Prayer", "Slaughter"],
                methodology_notes="Al-Jassas focuses on deriving Hanafi legal rulings from the verse with detailed fiqhi analysis."
            ),
            TafsirEntry(
                id="1_1_baghawi",
                scholar_id="baghawi",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Concise explanation based on authentic narrations",
                    "Meaning of each Divine Name",
                    "Virtue of beginning with Allah's name",
                    "Narrations from Companions on Bismillah"
                ],
                linguistic_analysis="Al-Baghawi provides clear linguistic explanation accessible to students without overly technical terminology.",
                historical_context="Summarizes authentic narrations from early generations about the practice of saying Bismillah.",
                fiqhi_rulings=[
                    "Sunnah to begin all good actions with Bismillah",
                    "Scholarly agreement on its recommendation"
                ],
                related_hadiths=[
                    "Authentic narrations selected with care",
                    "Narrations from the Prophet and Companions"
                ],
                cross_references=[
                    {"surah": 11, "ayah": 41, "relevance": "Embark in the name of Allah"},
                    {"surah": 27, "ayah": 30, "relevance": "Solomon's letter begins with Bismillah"}
                ],
                themes=["Divine Names", "Narrations", "Virtue", "Simplicity"],
                methodology_notes="Al-Baghawi's approach is to provide concise, reliable narration-based explanation accessible to all levels of readers."
            ),
            TafsirEntry(
                id="1_1_saadi",
                scholar_id="saadi",
                surah=1,
                ayah=1,
                arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                english_translation="In the Name of Allah, the Most Gracious, the Most Merciful",
                key_points=[
                    "Simple and accessible explanation for all readers",
                    "Practical benefit of saying Bismillah",
                    "Allah's mercy encompasses all our affairs",
                    "Beginning with Allah's name is seeking His help"
                ],
                linguistic_analysis="Clear and straightforward linguistic explanation without overly technical terminology, making it accessible to the average Muslim.",
                historical_context="Brief contextual notes focused on practical application in daily life.",
                fiqhi_rulings=[
                    "Sunnah to say Bismillah before all permissible acts",
                    "Brings blessing to one's actions"
                ],
                related_hadiths=[
                    "Selected hadiths most relevant to daily practice"
                ],
                cross_references=[
                    {"surah": 1, "ayah": 2, "relevance": "Connection to praising Allah"}
                ],
                themes=["Practical guidance", "Daily worship", "Seeking blessing", "Simplicity"],
                methodology_notes="Al-Saadi's tafsir is known for its clarity, brevity, and focus on spiritual and practical benefit for the reader."
            ),
        ]

        # Al-Fatiha verse 2
        verse_key = "1:2"
        self.tafsir_entries[verse_key] = [
            TafsirEntry(
                id="1_2_ibn_kathir",
                scholar_id="ibn_kathir",
                surah=1,
                ayah=2,
                arabic_text="الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                english_translation="All praise is due to Allah, Lord of the worlds",
                key_points=[
                    "Hamd encompasses praise and gratitude",
                    "The 'Al' indicates encompassing all praise",
                    "Rabb means Lord, Sustainer, Nurturer",
                    "'Alameen includes all of creation - humans, jinn, angels, animals"
                ],
                linguistic_analysis="'Al-Hamd' with the definite article indicates complete and comprehensive praise. 'Rabb' comes from tarbiyah (nurturing) indicating Allah's continuous care for creation.",
                historical_context="The Prophet taught that Al-Hamdulillah fills the scales of good deeds.",
                fiqhi_rulings=[
                    "Essential part of Al-Fatiha in prayer",
                    "Sunnah to say after sneezing"
                ],
                related_hadiths=[
                    "Al-Hamdulillah fills the scales",
                    "Say Al-Hamdulillah after sneezing"
                ],
                cross_references=[
                    {"surah": 6, "ayah": 1, "relevance": "All praise to Allah who created heavens and earth"},
                    {"surah": 34, "ayah": 1, "relevance": "All praise to Allah, to Whom belongs all in heavens and earth"}
                ],
                themes=["Praise", "Gratitude", "Lordship", "Creation"],
                methodology_notes="Ibn Kathir explains using narrations from Prophet and Companions."
            ),
        ]

        # Al-Baqarah 2:255 (Ayat al-Kursi)
        verse_key = "2:255"
        self.tafsir_entries[verse_key] = [
            TafsirEntry(
                id="2_255_ibn_kathir",
                scholar_id="ibn_kathir",
                surah=2,
                ayah=255,
                arabic_text="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
                english_translation="Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence",
                key_points=[
                    "Greatest verse in the Quran",
                    "Contains Allah's greatest name (Ism al-A'zam)",
                    "Al-Hayy - Ever-Living, eternal existence",
                    "Al-Qayyum - Self-Sustaining and sustaining all creation",
                    "Neither drowsiness nor sleep overtakes Him"
                ],
                linguistic_analysis="Al-Qayyum is an intensive form indicating complete self-sufficiency and the sustenance of all else. The negation of slumber and sleep emphasizes eternal vigilance.",
                historical_context="The Prophet said this is the greatest verse. Ubayy ibn Ka'b confirmed this when asked.",
                fiqhi_rulings=[
                    "Recitation after every prayer protects until next prayer",
                    "Recitation before sleep brings protection"
                ],
                related_hadiths=[
                    "Whoever recites Ayat al-Kursi after prayer, only death prevents Paradise",
                    "When you go to bed, recite Ayat al-Kursi"
                ],
                cross_references=[
                    {"surah": 3, "ayah": 2, "relevance": "Allah - no deity except Him, the Ever-Living, the Sustainer"},
                    {"surah": 20, "ayah": 111, "relevance": "Faces will be humbled before the Ever-Living, the Sustainer"}
                ],
                themes=["Tawhid", "Divine Attributes", "Protection", "Greatest verse"],
                methodology_notes="Ibn Kathir emphasizes the hadith evidence for the verse's virtue."
            ),
            TafsirEntry(
                id="2_255_qurtubi",
                scholar_id="qurtubi",
                surah=2,
                ayah=255,
                arabic_text="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
                english_translation="Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence",
                key_points=[
                    "Legal and theological implications of Tawhid",
                    "Meaning of Al-Hayy and Al-Qayyum according to the four madhabs",
                    "Rulings related to seeking protection through this verse",
                    "Comparative fiqhi analysis of its recitation",
                    "Evidence for Allah's attributes from this verse"
                ],
                linguistic_analysis="Al-Qurtubi analyzes the Divine Names linguistically while deriving practical legal implications from the verse's affirmation of Allah's attributes.",
                historical_context="Documents scholarly consensus on the virtue of Ayat al-Kursi and its use for protection.",
                fiqhi_rulings=[
                    "Recommended to recite after every obligatory prayer",
                    "Recitation before sleep is from the Sunnah",
                    "Can be recited for protection (ruqyah)"
                ],
                related_hadiths=[
                    "Greatest verse in the Quran",
                    "Protection from harm until morning"
                ],
                cross_references=[
                    {"surah": 112, "ayah": 1, "relevance": "Say: He is Allah, the One"},
                    {"surah": 3, "ayah": 2, "relevance": "Allah, there is no deity except Him"}
                ],
                themes=["Tawhid", "Divine Attributes", "Legal rulings", "Protection"],
                methodology_notes="Al-Qurtubi combines theological explanation with practical legal rulings according to the Maliki madhab and comparative jurisprudence."
            ),
            TafsirEntry(
                id="2_255_saadi",
                scholar_id="saadi",
                surah=2,
                ayah=255,
                arabic_text="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
                english_translation="Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence",
                key_points=[
                    "Clear and accessible explanation of Divine Unity",
                    "Practical benefits of understanding Allah's names",
                    "Spiritual impact of reflecting on this verse",
                    "How this verse strengthens faith",
                    "Daily application in a Muslim's life"
                ],
                linguistic_analysis="Al-Saadi provides straightforward linguistic explanation focused on spiritual benefit rather than technical analysis.",
                historical_context="Emphasizes the Prophet's teaching on this verse's greatness and its practical application by the Companions.",
                fiqhi_rulings=[
                    "Sunnah to recite regularly for protection",
                    "Recite after prayers and before sleep"
                ],
                related_hadiths=[
                    "The greatest verse in Allah's Book",
                    "Whoever recites it, Allah sends a guardian"
                ],
                cross_references=[
                    {"surah": 59, "ayah": 22, "relevance": "He is Allah, there is no deity except Him"},
                    {"surah": 20, "ayah": 111, "relevance": "Faces humbled before the Ever-Living"}
                ],
                themes=["Tawhid", "Practical guidance", "Spiritual benefit", "Daily worship"],
                methodology_notes="Al-Saadi's approach emphasizes clarity, spiritual benefit, and practical application for everyday Muslims."
            ),
        ]

    def get_all_scholars(self) -> List[Dict[str, Any]]:
        """Get list of all tafsir scholars"""
        return [
            {
                "id": s.id,
                "name_arabic": s.name_arabic,
                "name_english": s.name_english,
                "era": s.era.value,
                "school": s.school.value,
                "methodology": [m.value for m in s.methodology],
                "tafsir_name": s.tafsir_name,
                "tafsir_name_arabic": s.tafsir_name_arabic,
                "specialization": s.specialization,
                "birth_year_hijri": s.birth_year_hijri,
                "death_year_hijri": s.death_year_hijri
            }
            for s in self.scholars.values()
        ]

    def get_scholar(self, scholar_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific scholar"""
        scholar = self.scholars.get(scholar_id)
        if not scholar:
            return None
        return {
            "id": scholar.id,
            "name_arabic": scholar.name_arabic,
            "name_english": scholar.name_english,
            "era": scholar.era.value,
            "school": scholar.school.value,
            "methodology": [m.value for m in scholar.methodology],
            "tafsir_name": scholar.tafsir_name,
            "tafsir_name_arabic": scholar.tafsir_name_arabic,
            "specialization": scholar.specialization,
            "biography_brief": scholar.biography_brief,
            "notable_contributions": scholar.notable_contributions,
            "birth_year_hijri": scholar.birth_year_hijri,
            "death_year_hijri": scholar.death_year_hijri
        }

    def get_scholars_by_school(self, school: str) -> List[Dict[str, Any]]:
        """Get scholars belonging to a specific school of thought"""
        try:
            school_enum = SchoolOfThought(school.lower())
        except ValueError:
            return []

        return [
            self.get_scholar(s.id)
            for s in self.scholars.values()
            if s.school == school_enum
        ]

    def get_scholars_by_methodology(self, methodology: str) -> List[Dict[str, Any]]:
        """Get scholars using a specific methodology"""
        try:
            method_enum = TafsirMethodology(methodology.lower())
        except ValueError:
            return []

        return [
            self.get_scholar(s.id)
            for s in self.scholars.values()
            if method_enum in s.methodology
        ]

    def get_scholars_by_era(self, era: str) -> List[Dict[str, Any]]:
        """Get scholars from a specific historical era"""
        try:
            era_enum = TafsirEra(era.lower())
        except ValueError:
            return []

        return [
            self.get_scholar(s.id)
            for s in self.scholars.values()
            if s.era == era_enum
        ]

    def get_tafsir_for_verse(self, surah: int, ayah: int, scholar_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get tafsir entries for a specific verse"""
        verse_key = f"{surah}:{ayah}"
        entries = self.tafsir_entries.get(verse_key, [])

        if scholar_ids:
            entries = [e for e in entries if e.scholar_id in scholar_ids]

        result = []
        for entry in entries:
            scholar = self.scholars.get(entry.scholar_id)
            result.append({
                "id": entry.id,
                "verse": f"{entry.surah}:{entry.ayah}",
                "arabic_text": entry.arabic_text,
                "english_translation": entry.english_translation,
                "scholar": {
                    "id": scholar.id if scholar else entry.scholar_id,
                    "name_english": scholar.name_english if scholar else "Unknown",
                    "name_arabic": scholar.name_arabic if scholar else "",
                    "school": scholar.school.value if scholar else "",
                    "tafsir_name": scholar.tafsir_name if scholar else ""
                },
                "key_points": entry.key_points,
                "linguistic_analysis": entry.linguistic_analysis,
                "historical_context": entry.historical_context,
                "fiqhi_rulings": entry.fiqhi_rulings,
                "related_hadiths": entry.related_hadiths,
                "cross_references": entry.cross_references,
                "themes": entry.themes,
                "methodology_notes": entry.methodology_notes
            })

        return result

    def compare_tafsir(self, surah: int, ayah: int, scholar_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare tafsir interpretations for a verse across multiple scholars"""
        entries = self.get_tafsir_for_verse(surah, ayah, scholar_ids)

        if not entries:
            return {
                "surah": surah,
                "ayah": ayah,
                "message": "No tafsir entries found for this verse",
                "interpretations": []
            }

        # Extract common themes
        all_themes = []
        for entry in entries:
            all_themes.extend(entry.get("themes", []))
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        common_themes = [theme for theme, count in theme_counts.items() if count > 1]

        # Identify points of agreement and difference
        all_points = []
        for entry in entries:
            all_points.extend(entry.get("key_points", []))

        # Group by methodology
        methodology_groups = {}
        for entry in entries:
            scholar = entry.get("scholar", {})
            scholar_obj = self.scholars.get(scholar.get("id", ""))
            if scholar_obj:
                for method in scholar_obj.methodology:
                    method_name = method.value
                    if method_name not in methodology_groups:
                        methodology_groups[method_name] = []
                    methodology_groups[method_name].append(entry.get("scholar", {}).get("name_english", "Unknown"))

        return {
            "surah": surah,
            "ayah": ayah,
            "verse_arabic": entries[0]["arabic_text"] if entries else "",
            "verse_translation": entries[0]["english_translation"] if entries else "",
            "total_interpretations": len(entries),
            "interpretations": entries,
            "common_themes": common_themes,
            "unique_themes": list(set(all_themes) - set(common_themes)),
            "methodology_comparison": methodology_groups,
            "analysis": {
                "linguistic_approaches": len([e for e in entries if e.get("linguistic_analysis")]),
                "with_fiqhi_rulings": len([e for e in entries if e.get("fiqhi_rulings")]),
                "with_hadith_references": len([e for e in entries if e.get("related_hadiths")])
            }
        }

    def search_tafsir_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Search tafsir entries by theme"""
        results = []
        theme_lower = theme.lower()

        for verse_key, entries in self.tafsir_entries.items():
            for entry in entries:
                if any(theme_lower in t.lower() for t in entry.themes):
                    scholar = self.scholars.get(entry.scholar_id)
                    results.append({
                        "verse": verse_key,
                        "scholar": scholar.name_english if scholar else entry.scholar_id,
                        "tafsir": scholar.tafsir_name if scholar else "",
                        "themes": entry.themes,
                        "key_points": entry.key_points[:2]  # First 2 points
                    })

        return results

    def get_fiqhi_rulings_from_tafsir(self, surah: int, ayah: int) -> Dict[str, Any]:
        """Extract fiqhi rulings from tafsir entries for a verse"""
        verse_key = f"{surah}:{ayah}"
        entries = self.tafsir_entries.get(verse_key, [])

        rulings_by_school = {}
        for entry in entries:
            scholar = self.scholars.get(entry.scholar_id)
            if scholar and entry.fiqhi_rulings:
                school = scholar.school.value
                if school not in rulings_by_school:
                    rulings_by_school[school] = []
                rulings_by_school[school].append({
                    "scholar": scholar.name_english,
                    "rulings": entry.fiqhi_rulings
                })

        return {
            "verse": f"{surah}:{ayah}",
            "rulings_by_school": rulings_by_school,
            "total_rulings": sum(len(v) for v in rulings_by_school.values())
        }

    def get_schools_of_thought(self) -> List[Dict[str, str]]:
        """Get list of all schools of thought"""
        return [
            {
                "id": school.value,
                "name": school.name.replace("_", " ").title(),
                "scholars_count": len([s for s in self.scholars.values() if s.school == school])
            }
            for school in SchoolOfThought
        ]

    def get_methodologies(self) -> List[Dict[str, str]]:
        """Get list of all tafsir methodologies"""
        methodology_descriptions = {
            TafsirMethodology.BIL_MATHUR: "Based on transmitted narrations from Prophet, Companions, and Successors",
            TafsirMethodology.BIL_RAY: "Based on scholarly opinion, reasoning, and ijtihad",
            TafsirMethodology.ISHARI: "Spiritual and mystical interpretation revealing inner meanings",
            TafsirMethodology.FIQHI: "Focus on deriving legal rulings and jurisprudential analysis",
            TafsirMethodology.ILMI: "Scientific interpretation connecting Quran to natural sciences",
            TafsirMethodology.ADABI: "Literary and linguistic analysis emphasizing Arabic rhetoric",
            TafsirMethodology.IJTIMAAYI: "Social interpretation addressing contemporary issues"
        }

        return [
            {
                "id": method.value,
                "name": method.name.replace("_", " ").title(),
                "description": methodology_descriptions.get(method, ""),
                "scholars_count": len([s for s in self.scholars.values() if method in s.methodology])
            }
            for method in TafsirMethodology
        ]

    def get_eras(self) -> List[Dict[str, Any]]:
        """Get list of all tafsir eras"""
        era_descriptions = {
            TafsirEra.COMPANION: {"hijri_range": "1-100", "description": "Interpretations from Companions of the Prophet"},
            TafsirEra.TABIIN: {"hijri_range": "50-150", "description": "Interpretations from the generation following the Companions"},
            TafsirEra.CLASSICAL: {"hijri_range": "150-700", "description": "Golden age of comprehensive tafsir works"},
            TafsirEra.MEDIEVAL: {"hijri_range": "700-1200", "description": "Period of refinement and specialization"},
            TafsirEra.MODERN: {"hijri_range": "1200-1400", "description": "Revival and reformation period"},
            TafsirEra.CONTEMPORARY: {"hijri_range": "1400+", "description": "Current scholarly interpretations"}
        }

        return [
            {
                "id": era.value,
                "name": era.name.replace("_", " ").title(),
                "hijri_range": era_descriptions.get(era, {}).get("hijri_range", ""),
                "description": era_descriptions.get(era, {}).get("description", ""),
                "scholars_count": len([s for s in self.scholars.values() if s.era == era])
            }
            for era in TafsirEra
        ]

    # User Preference Methods
    def create_user_preference(
        self,
        user_id: str,
        preferred_schools: Optional[List[str]] = None,
        preferred_methodologies: Optional[List[str]] = None,
        preferred_scholars: Optional[List[str]] = None,
        language_preference: str = "english",
        study_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Create or update user tafsir preferences"""
        schools = []
        if preferred_schools:
            for school in preferred_schools:
                try:
                    schools.append(SchoolOfThought(school.lower()))
                except ValueError:
                    pass

        methodologies = []
        if preferred_methodologies:
            for method in preferred_methodologies:
                try:
                    methodologies.append(TafsirMethodology(method.lower()))
                except ValueError:
                    pass

        preference = UserTafsirPreference(
            user_id=user_id,
            preferred_schools=schools,
            preferred_methodologies=methodologies,
            preferred_scholars=preferred_scholars or [],
            language_preference=language_preference,
            study_level=study_level,
            saved_comparisons=[],
            notes={}
        )

        self.user_preferences[user_id] = preference

        return {
            "user_id": user_id,
            "preferred_schools": [s.value for s in schools],
            "preferred_methodologies": [m.value for m in methodologies],
            "preferred_scholars": preferred_scholars or [],
            "language_preference": language_preference,
            "study_level": study_level,
            "message": "Preferences saved successfully"
        }

    def get_user_preference(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's tafsir preferences"""
        pref = self.user_preferences.get(user_id)
        if not pref:
            return None

        return {
            "user_id": pref.user_id,
            "preferred_schools": [s.value for s in pref.preferred_schools],
            "preferred_methodologies": [m.value for m in pref.preferred_methodologies],
            "preferred_scholars": pref.preferred_scholars,
            "language_preference": pref.language_preference,
            "study_level": pref.study_level,
            "saved_comparisons": pref.saved_comparisons,
            "notes_count": len(pref.notes)
        }

    def get_personalized_tafsir(self, user_id: str, surah: int, ayah: int) -> Dict[str, Any]:
        """Get tafsir personalized to user's preferences"""
        pref = self.user_preferences.get(user_id)

        if not pref:
            # Return default selection
            return self.compare_tafsir(surah, ayah)

        # Filter scholars based on preferences
        preferred_scholar_ids = []

        # Add explicitly preferred scholars
        preferred_scholar_ids.extend(pref.preferred_scholars)

        # Add scholars from preferred schools
        for scholar in self.scholars.values():
            if scholar.school in pref.preferred_schools:
                if scholar.id not in preferred_scholar_ids:
                    preferred_scholar_ids.append(scholar.id)

        # Add scholars using preferred methodologies
        for scholar in self.scholars.values():
            if any(m in pref.preferred_methodologies for m in scholar.methodology):
                if scholar.id not in preferred_scholar_ids:
                    preferred_scholar_ids.append(scholar.id)

        comparison = self.compare_tafsir(surah, ayah, preferred_scholar_ids if preferred_scholar_ids else None)
        comparison["personalized"] = True
        comparison["user_preferences_applied"] = {
            "schools": [s.value for s in pref.preferred_schools],
            "methodologies": [m.value for m in pref.preferred_methodologies],
            "scholars": pref.preferred_scholars
        }

        return comparison

    def save_user_note(self, user_id: str, surah: int, ayah: int, note: str) -> Dict[str, Any]:
        """Save user's personal note on a verse"""
        if user_id not in self.user_preferences:
            self.create_user_preference(user_id)

        verse_key = f"{surah}:{ayah}"
        self.user_preferences[user_id].notes[verse_key] = note

        return {
            "user_id": user_id,
            "verse": verse_key,
            "note": note,
            "message": "Note saved successfully"
        }

    def get_user_notes(self, user_id: str) -> Dict[str, Any]:
        """Get all user notes"""
        pref = self.user_preferences.get(user_id)
        if not pref:
            return {"user_id": user_id, "notes": {}}

        return {
            "user_id": user_id,
            "notes": pref.notes,
            "total_notes": len(pref.notes)
        }

    def get_recommended_scholars_for_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get scholar recommendations based on topic of interest"""
        topic_lower = topic.lower()

        recommendations = []

        # Match specializations
        for scholar in self.scholars.values():
            relevance_score = 0
            matching_specializations = []

            for spec in scholar.specialization:
                if topic_lower in spec.lower():
                    relevance_score += 2
                    matching_specializations.append(spec)

            # Check methodology relevance
            if "legal" in topic_lower or "ruling" in topic_lower or "fiqh" in topic_lower:
                if TafsirMethodology.FIQHI in scholar.methodology:
                    relevance_score += 1

            if "spiritual" in topic_lower or "mystical" in topic_lower or "sufi" in topic_lower:
                if TafsirMethodology.ISHARI in scholar.methodology:
                    relevance_score += 1

            if "linguistic" in topic_lower or "arabic" in topic_lower or "rhetoric" in topic_lower:
                if TafsirMethodology.ADABI in scholar.methodology:
                    relevance_score += 1

            if "science" in topic_lower or "scientific" in topic_lower:
                if TafsirMethodology.ILMI in scholar.methodology:
                    relevance_score += 1

            if "hadith" in topic_lower or "narration" in topic_lower:
                if TafsirMethodology.BIL_MATHUR in scholar.methodology:
                    relevance_score += 1

            if relevance_score > 0:
                recommendations.append({
                    "scholar": self.get_scholar(scholar.id),
                    "relevance_score": relevance_score,
                    "matching_specializations": matching_specializations
                })

        # Sort by relevance
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

        return recommendations[:5]  # Top 5 recommendations

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall tafsir service statistics"""
        total_entries = sum(len(entries) for entries in self.tafsir_entries.values())

        return {
            "total_scholars": len(self.scholars),
            "total_tafsir_entries": total_entries,
            "verses_covered": len(self.tafsir_entries),
            "schools_of_thought": len(SchoolOfThought),
            "methodologies": len(TafsirMethodology),
            "eras": len(TafsirEra),
            "user_preferences": len(self.user_preferences),
            "scholars_by_era": {
                era.value: len([s for s in self.scholars.values() if s.era == era])
                for era in TafsirEra
            },
            "scholars_by_school": {
                school.value: len([s for s in self.scholars.values() if s.school == school])
                for school in SchoolOfThought
                if len([s for s in self.scholars.values() if s.school == school]) > 0
            }
        }


# Create singleton instance
tafsir_service = TafsirService()
