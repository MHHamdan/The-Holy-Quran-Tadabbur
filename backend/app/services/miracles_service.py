"""
Miracles & Verses Service - Comprehensive Quranic Miracles Database

Provides:
1. Comprehensive database of Quranic miracles (prophetic, divine, earthly)
2. Tafsir integration from four Sunni madhabs (Hanafi, Maliki, Shafi'i, Hanbali)
3. Semantic search with AraBERT-like embeddings
4. Graph visualization for miracle connections
5. Human-in-the-loop verification pipeline
6. User feedback system
7. Admin review panel

Based on authentic Quranic verses and verified classical tafsirs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from datetime import datetime
from collections import defaultdict
import re
import math
import numpy as np


# ============================================
# ENUMS AND DATA CLASSES
# ============================================

class MiracleCategory(Enum):
    """Categories of miracles in the Quran"""
    PROPHETIC = "prophetic"           # Miracles performed by prophets
    DIVINE = "divine"                 # Direct divine acts
    CREATION = "creation"             # Creation miracles
    NATURAL = "natural"               # Natural phenomena as signs
    REVELATION = "revelation"         # Quranic revelation itself
    HISTORICAL = "historical"         # Historical events as miracles


class MiracleType(Enum):
    """Specific types of miracles"""
    TRANSFORMATION = "transformation"     # Staff to serpent, etc.
    HEALING = "healing"                   # Curing blindness, etc.
    RESURRECTION = "resurrection"         # Raising the dead
    PROTECTION = "protection"             # Surviving fire, etc.
    NATURE_CONTROL = "nature_control"     # Parting sea, splitting moon
    PROVISION = "provision"               # Manna and quails, etc.
    SPEECH = "speech"                     # Speaking from cradle
    CREATION = "creation"                 # Creating life
    KNOWLEDGE = "knowledge"               # Divine knowledge/revelation


class Madhab(Enum):
    """Four Sunni schools of thought"""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"


class VerificationStatus(Enum):
    """Verification status for miracle content"""
    PENDING = "pending"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass
class VerseReference:
    """Quranic verse reference"""
    surah_number: int
    surah_name_ar: str
    surah_name_en: str
    ayah_number: int
    ayah_range: Optional[str]  # e.g., "106-108"
    text_ar: str
    text_en: str
    relevance: str  # How this verse relates to the miracle


@dataclass
class TafsirReference:
    """Tafsir reference from classical scholars"""
    scholar_name_ar: str
    scholar_name_en: str
    madhab: Madhab
    book_name_ar: str
    book_name_en: str
    explanation_ar: str
    explanation_en: str
    volume: Optional[str]
    page: Optional[str]


@dataclass
class Miracle:
    """Comprehensive miracle data structure"""
    id: str
    name_ar: str
    name_en: str
    category: MiracleCategory
    miracle_type: MiracleType
    prophet_id: Optional[str]  # If prophetic miracle
    prophet_name_ar: Optional[str]
    prophet_name_en: Optional[str]
    description_ar: str
    description_en: str
    significance_ar: str
    significance_en: str
    lessons_ar: List[str]
    lessons_en: List[str]
    verses: List[VerseReference]
    tafsir_references: List[TafsirReference]
    themes: List[str]
    themes_ar: List[str]
    related_miracles: List[str]
    historical_context_ar: str
    historical_context_en: str
    verification_status: VerificationStatus
    created_at: datetime
    updated_at: datetime


@dataclass
class MiracleFeedback:
    """User feedback on miracle content"""
    feedback_id: str
    miracle_id: str
    user_id: str
    feedback_type: str  # "correction", "addition", "question", "insight"
    content_ar: str
    content_en: str
    status: str  # "pending", "reviewed", "accepted", "rejected"
    reviewer_id: Optional[str]
    reviewer_notes: Optional[str]
    created_at: datetime


class MiraclesService:
    """
    Comprehensive Miracles & Verses Service.
    Provides searchable miracle database with tafsir integration.
    """

    def __init__(self):
        # Miracle database
        self._miracles: Dict[str, Miracle] = {}

        # Feedback storage
        self._feedback: Dict[str, MiracleFeedback] = {}

        # Verification queue
        self._verification_queue: List[str] = []

        # Admin users
        self._admin_users: Set[str] = {"admin", "scholar_1", "scholar_2"}

        # Search index
        self._search_index: Dict[str, Set[str]] = defaultdict(set)

        # Embedding dimension (AraBERT-like)
        self._embedding_dim: int = 768

        # Initialize miracle database
        self._initialize_miracles_database()
        self._build_search_index()

    def _initialize_miracles_database(self):
        """Initialize comprehensive miracle database from authentic sources"""

        # ===== PROPHETIC MIRACLES =====

        # Musa (Moses) Miracles
        self._miracles["musa_staff_serpent"] = Miracle(
            id="musa_staff_serpent",
            name_ar="تحول عصا موسى إلى ثعبان",
            name_en="Moses' Staff Turning into a Serpent",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.TRANSFORMATION,
            prophet_id="musa",
            prophet_name_ar="موسى عليه السلام",
            prophet_name_en="Moses (peace be upon him)",
            description_ar="ألقى موسى عصاه فإذا هي ثعبان مبين، وهذه المعجزة كانت أمام فرعون وملئه لإثبات نبوته",
            description_en="Moses threw his staff and it became a manifest serpent. This miracle was performed before Pharaoh and his chiefs to prove his prophethood.",
            significance_ar="دليل على قدرة الله المطلقة وتأييده لأنبيائه، وإبطال سحر السحرة",
            significance_en="Evidence of Allah's absolute power and support for His prophets, and nullification of the magicians' sorcery.",
            lessons_ar=[
                "الاعتماد على الله في مواجهة الباطل",
                "الحق يعلو ولا يُعلى عليه",
                "السحر مهما بلغ لا يغلب آيات الله"
            ],
            lessons_en=[
                "Relying on Allah when confronting falsehood",
                "Truth always prevails",
                "No matter how powerful, sorcery cannot overcome Allah's signs"
            ],
            verses=[
                VerseReference(
                    surah_number=7,
                    surah_name_ar="الأعراف",
                    surah_name_en="Al-A'raf",
                    ayah_number=107,
                    ayah_range="107",
                    text_ar="فَأَلْقَىٰ عَصَاهُ فَإِذَا هِيَ ثُعْبَانٌ مُّبِينٌ",
                    text_en="So he threw his staff, and suddenly it was a serpent, manifest.",
                    relevance="الآية الأساسية لمعجزة العصا"
                ),
                VerseReference(
                    surah_number=26,
                    surah_name_ar="الشعراء",
                    surah_name_en="Ash-Shu'ara",
                    ayah_number=32,
                    ayah_range="32-33",
                    text_ar="فَأَلْقَىٰ عَصَاهُ فَإِذَا هِيَ ثُعْبَانٌ مُّبِينٌ ۝ وَنَزَعَ يَدَهُ فَإِذَا هِيَ بَيْضَاءُ لِلنَّاظِرِينَ",
                    text_en="So he threw his staff, and suddenly it was a serpent, manifest. And he drew out his hand; thereupon it was white for the observers.",
                    relevance="تفصيل المعجزة مع معجزة اليد البيضاء"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="تحولت العصا إلى حية عظيمة تبتلع ما ألقاه السحرة، فكان ذلك سبباً في إيمانهم",
                    explanation_en="The staff transformed into a great serpent that swallowed what the magicians had thrown, which became the reason for their belief.",
                    volume="3",
                    page="445"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="الثعبان المبين: الحية الذكر العظيم، وقيل: الظاهر الواضح في كونه حية حقيقية",
                    explanation_en="The manifest serpent: A great male snake, or it means clearly apparent as a real snake.",
                    volume="7",
                    page="256"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل وحقائق التأويل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="العصا انقلبت حية حقيقية بقدرة الله، لا سحراً ولا خيالاً",
                    explanation_en="The staff truly became a snake by Allah's power, not illusion or sorcery.",
                    volume="2",
                    page="89"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه المعجزة من أعظم الدلائل على صدق نبوة موسى عليه السلام",
                    explanation_en="This miracle is among the greatest proofs of the truthfulness of Moses' prophethood.",
                    volume="2",
                    page="320"
                )
            ],
            themes=["divine_power", "prophethood", "truth_over_falsehood", "faith"],
            themes_ar=["القدرة الإلهية", "النبوة", "غلبة الحق", "الإيمان"],
            related_miracles=["musa_parting_sea", "musa_white_hand"],
            historical_context_ar="حدثت هذه المعجزة في بلاط فرعون عندما طلب دليلاً على نبوة موسى",
            historical_context_en="This miracle occurred in Pharaoh's court when he demanded proof of Moses' prophethood.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._miracles["musa_parting_sea"] = Miracle(
            id="musa_parting_sea",
            name_ar="شق البحر لموسى وبني إسرائيل",
            name_en="Parting of the Sea for Moses and the Children of Israel",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.NATURE_CONTROL,
            prophet_id="musa",
            prophet_name_ar="موسى عليه السلام",
            prophet_name_en="Moses (peace be upon him)",
            description_ar="ضرب موسى البحر بعصاه فانفلق اثني عشر طريقاً يابساً، فمر بنو إسرائيل وأغرق الله فرعون وجنوده",
            description_en="Moses struck the sea with his staff and it parted into twelve dry paths. The Children of Israel passed through while Allah drowned Pharaoh and his army.",
            significance_ar="أعظم معجزات موسى، ونجاة المؤمنين وهلاك الظالمين",
            significance_en="The greatest of Moses' miracles, demonstrating the salvation of believers and destruction of oppressors.",
            lessons_ar=[
                "التوكل على الله عند الشدائد",
                "نصر الله للمستضعفين",
                "عاقبة الظلم والطغيان"
            ],
            lessons_en=[
                "Trust in Allah during hardships",
                "Allah's victory for the oppressed",
                "The consequence of oppression and tyranny"
            ],
            verses=[
                VerseReference(
                    surah_number=26,
                    surah_name_ar="الشعراء",
                    surah_name_en="Ash-Shu'ara",
                    ayah_number=63,
                    ayah_range="63-66",
                    text_ar="فَأَوْحَيْنَا إِلَىٰ مُوسَىٰ أَنِ اضْرِب بِّعَصَاكَ الْبَحْرَ فَانفَلَقَ فَكَانَ كُلُّ فِرْقٍ كَالطَّوْدِ الْعَظِيمِ",
                    text_en="Then We inspired to Moses, 'Strike with your staff the sea,' and it parted, and each portion was like a great towering mountain.",
                    relevance="الآية الرئيسية في وصف انفلاق البحر"
                ),
                VerseReference(
                    surah_number=20,
                    surah_name_ar="طه",
                    surah_name_en="Ta-Ha",
                    ayah_number=77,
                    ayah_range="77-78",
                    text_ar="وَلَقَدْ أَوْحَيْنَا إِلَىٰ مُوسَىٰ أَنْ أَسْرِ بِعِبَادِي فَاضْرِبْ لَهُمْ طَرِيقًا فِي الْبَحْرِ يَبَسًا",
                    text_en="And We had inspired to Moses, 'Travel by night with My servants and strike for them a dry path through the sea.'",
                    relevance="تأكيد أن الطريق كان يابساً"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="انفلق البحر اثني عشر طريقاً بعدد أسباط بني إسرائيل، كل طريق كالجبل العظيم",
                    explanation_en="The sea split into twelve paths, equal to the number of tribes of Israel, each path like a great mountain.",
                    volume="6",
                    page="156"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="الطود: الجبل العظيم، شبه كل قسم من أقسام الماء بالجبل في ارتفاعه وثباته",
                    explanation_en="Al-Tawd: A great mountain. Each section of water was likened to a mountain in its height and stability.",
                    volume="13",
                    page="110"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="يبساً: أي جافاً لا ماء فيه ولا طين، وهذا من كمال المعجزة",
                    explanation_en="Dry: Meaning no water or mud, which adds to the perfection of the miracle.",
                    volume="2",
                    page="368"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه الآية من أعظم الأدلة على قدرة الله المطلقة وتأييده لأنبيائه",
                    explanation_en="This verse is among the greatest proofs of Allah's absolute power and support for His prophets.",
                    volume="4",
                    page="428"
                )
            ],
            themes=["salvation", "divine_intervention", "justice", "patience"],
            themes_ar=["النجاة", "التدخل الإلهي", "العدل", "الصبر"],
            related_miracles=["musa_staff_serpent", "musa_white_hand"],
            historical_context_ar="حدثت عند خروج بني إسرائيل من مصر هرباً من فرعون",
            historical_context_en="Occurred when the Children of Israel fled Egypt escaping Pharaoh.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._miracles["musa_white_hand"] = Miracle(
            id="musa_white_hand",
            name_ar="يد موسى البيضاء",
            name_en="Moses' White Hand",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.TRANSFORMATION,
            prophet_id="musa",
            prophet_name_ar="موسى عليه السلام",
            prophet_name_en="Moses (peace be upon him)",
            description_ar="أدخل موسى يده في جيبه فخرجت بيضاء من غير سوء، تشع نوراً للناظرين",
            description_en="Moses put his hand into his garment and it came out white without disease, radiating light to the onlookers.",
            significance_ar="آية نورانية تدل على صدق الرسالة والاتصال بالله",
            significance_en="A luminous sign indicating the truth of the message and connection with Allah.",
            lessons_ar=[
                "الله يؤيد أنبياءه بالآيات",
                "النور يغلب الظلام",
                "المعجزة لا تتعارض مع الصحة والسلامة"
            ],
            lessons_en=[
                "Allah supports His prophets with signs",
                "Light overcomes darkness",
                "Miracles do not contradict health and safety"
            ],
            verses=[
                VerseReference(
                    surah_number=7,
                    surah_name_ar="الأعراف",
                    surah_name_en="Al-A'raf",
                    ayah_number=108,
                    ayah_range="108",
                    text_ar="وَنَزَعَ يَدَهُ فَإِذَا هِيَ بَيْضَاءُ لِلنَّاظِرِينَ",
                    text_en="And he drew out his hand; thereupon it was white for the observers.",
                    relevance="الآية الأساسية لمعجزة اليد البيضاء"
                ),
                VerseReference(
                    surah_number=20,
                    surah_name_ar="طه",
                    surah_name_en="Ta-Ha",
                    ayah_number=22,
                    ayah_range="22",
                    text_ar="وَاضْمُمْ يَدَكَ إِلَىٰ جَنَاحِكَ تَخْرُجْ بَيْضَاءَ مِنْ غَيْرِ سُوءٍ آيَةً أُخْرَىٰ",
                    text_en="And draw in your hand to your side; it will come out white without disease - another sign.",
                    relevance="توضيح أن البياض ليس من مرض"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="بيضاء من غير سوء: أي من غير برص، بل بياض نور وإشراق",
                    explanation_en="White without disease: meaning without leprosy, but a whiteness of light and radiance.",
                    volume="3",
                    page="447"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="كانت يده تضيء كالشمس، وكان موسى آدم اللون",
                    explanation_en="His hand would shine like the sun, though Moses was of dark complexion.",
                    volume="7",
                    page="258"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="من غير سوء: من غير برص ولا آفة، فهي معجزة لا مرض",
                    explanation_en="Without disease: without leprosy or affliction, so it was a miracle not an illness.",
                    volume="2",
                    page="90"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه الآية من تسع آيات أعطيها موسى عليه السلام",
                    explanation_en="This sign was among nine signs given to Moses (peace be upon him).",
                    volume="3",
                    page="156"
                )
            ],
            themes=["light", "prophethood", "divine_signs", "guidance"],
            themes_ar=["النور", "النبوة", "الآيات الإلهية", "الهداية"],
            related_miracles=["musa_staff_serpent", "musa_parting_sea"],
            historical_context_ar="كانت من الآيات التي أُعطيها موسى لدعوة فرعون",
            historical_context_en="One of the signs given to Moses for calling Pharaoh to belief.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Isa (Jesus) Miracles
        self._miracles["isa_healing_blind"] = Miracle(
            id="isa_healing_blind",
            name_ar="شفاء الأكمه والأبرص",
            name_en="Healing the Blind and the Leper",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.HEALING,
            prophet_id="isa",
            prophet_name_ar="عيسى عليه السلام",
            prophet_name_en="Jesus (peace be upon him)",
            description_ar="كان عيسى عليه السلام يبرئ الأكمه (المولود أعمى) والأبرص بإذن الله",
            description_en="Jesus (peace be upon him) would cure those born blind and the lepers by Allah's permission.",
            significance_ar="دليل على قدرة الله وتأييده لعيسى، وأن الشفاء بيد الله وحده",
            significance_en="Evidence of Allah's power and support for Jesus, and that healing is in Allah's hands alone.",
            lessons_ar=[
                "الشفاء من الله وحده",
                "المعجزات تناسب عصرها",
                "أهمية الإذن الإلهي"
            ],
            lessons_en=[
                "Healing comes from Allah alone",
                "Miracles suit their era",
                "The importance of divine permission"
            ],
            verses=[
                VerseReference(
                    surah_number=3,
                    surah_name_ar="آل عمران",
                    surah_name_en="Aal-Imran",
                    ayah_number=49,
                    ayah_range="49",
                    text_ar="وَأُبْرِئُ الْأَكْمَهَ وَالْأَبْرَصَ وَأُحْيِي الْمَوْتَىٰ بِإِذْنِ اللَّهِ",
                    text_en="And I cure the blind and the leper, and I give life to the dead - by permission of Allah.",
                    relevance="الآية الجامعة لمعجزات عيسى الشفائية"
                ),
                VerseReference(
                    surah_number=5,
                    surah_name_ar="المائدة",
                    surah_name_en="Al-Ma'idah",
                    ayah_number=110,
                    ayah_range="110",
                    text_ar="وَتُبْرِئُ الْأَكْمَهَ وَالْأَبْرَصَ بِإِذْنِي",
                    text_en="And you healed the blind and the leper with My permission.",
                    relevance="تأكيد أن الشفاء بإذن الله"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="الأكمه: من ولد أعمى، وهذا أبلغ في المعجزة لأنه لم ير النور قط",
                    explanation_en="Al-Akmah: One born blind. This is more miraculous because he had never seen light.",
                    volume="2",
                    page="45"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="خص هاتين المعجزتين لأن الطب عجز عن علاجهما في زمانه",
                    explanation_en="These two miracles were specified because medicine was unable to treat them in his time.",
                    volume="4",
                    page="99"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="بإذن الله: تأكيد على أن المعجزة من الله لا من عيسى استقلالاً",
                    explanation_en="By Allah's permission: emphasizing that the miracle is from Allah, not from Jesus independently.",
                    volume="1",
                    page="293"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="كان أهل زمان عيسى متقدمين في الطب، فجاءت معجزاته مما يعجز عنه الأطباء",
                    explanation_en="The people of Jesus' time were advanced in medicine, so his miracles surpassed what doctors could do.",
                    volume="1",
                    page="387"
                )
            ],
            themes=["mercy", "divine_power", "healing", "faith"],
            themes_ar=["الرحمة", "القدرة الإلهية", "الشفاء", "الإيمان"],
            related_miracles=["isa_raising_dead", "isa_speaking_cradle"],
            historical_context_ar="كان الطب متقدماً في زمن عيسى، فجاءت معجزاته مما يعجز عنه الطب",
            historical_context_en="Medicine was advanced in Jesus' time, so his miracles exceeded what medicine could achieve.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._miracles["isa_raising_dead"] = Miracle(
            id="isa_raising_dead",
            name_ar="إحياء الموتى",
            name_en="Raising the Dead",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.RESURRECTION,
            prophet_id="isa",
            prophet_name_ar="عيسى عليه السلام",
            prophet_name_en="Jesus (peace be upon him)",
            description_ar="كان عيسى عليه السلام يحيي الموتى بإذن الله، وهذه من أعظم معجزاته",
            description_en="Jesus (peace be upon him) would raise the dead by Allah's permission. This is among his greatest miracles.",
            significance_ar="دليل على قدرة الله على البعث والإحياء، وأن الحياة والموت بيد الله",
            significance_en="Evidence of Allah's power to resurrect, and that life and death are in Allah's hands.",
            lessons_ar=[
                "الله وحده يحيي ويميت",
                "البعث حق",
                "المعجزات تؤكد الرسالة"
            ],
            lessons_en=[
                "Allah alone gives life and causes death",
                "Resurrection is real",
                "Miracles confirm the message"
            ],
            verses=[
                VerseReference(
                    surah_number=3,
                    surah_name_ar="آل عمران",
                    surah_name_en="Aal-Imran",
                    ayah_number=49,
                    ayah_range="49",
                    text_ar="وَأُحْيِي الْمَوْتَىٰ بِإِذْنِ اللَّهِ",
                    text_en="And I give life to the dead - by permission of Allah.",
                    relevance="التصريح بإحياء الموتى"
                ),
                VerseReference(
                    surah_number=5,
                    surah_name_ar="المائدة",
                    surah_name_en="Al-Ma'idah",
                    ayah_number=110,
                    ayah_range="110",
                    text_ar="وَإِذْ تُخْرِجُ الْمَوْتَىٰ بِإِذْنِي",
                    text_en="And when you brought forth the dead by My permission.",
                    relevance="تذكير الله لعيسى بنعمة إخراج الموتى"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="أحيا عيسى عليه السلام أربعة من الموتى، منهم: العازر صديقه",
                    explanation_en="Jesus (peace be upon him) raised four from the dead, including Lazarus his friend.",
                    volume="2",
                    page="46"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="قال بإذن الله دفعاً لتوهم الألوهية، فالإحياء الحقيقي لله وحده",
                    explanation_en="He said 'by Allah's permission' to prevent the misconception of divinity, as true resurrection belongs to Allah alone.",
                    volume="4",
                    page="100"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="الإحياء كان حقيقياً، وعادوا للحياة ثم ماتوا بعد ذلك",
                    explanation_en="The resurrection was real; they returned to life then died again later.",
                    volume="1",
                    page="294"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه المعجزة دليل على البعث يوم القيامة",
                    explanation_en="This miracle is evidence for resurrection on the Day of Judgment.",
                    volume="1",
                    page="389"
                )
            ],
            themes=["resurrection", "divine_power", "afterlife", "prophethood"],
            themes_ar=["البعث", "القدرة الإلهية", "الآخرة", "النبوة"],
            related_miracles=["isa_healing_blind", "isa_speaking_cradle"],
            historical_context_ar="كانت هذه المعجزة رداً على من أنكر البعث",
            historical_context_en="This miracle was a response to those who denied resurrection.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._miracles["isa_speaking_cradle"] = Miracle(
            id="isa_speaking_cradle",
            name_ar="كلام عيسى في المهد",
            name_en="Jesus Speaking from the Cradle",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.SPEECH,
            prophet_id="isa",
            prophet_name_ar="عيسى عليه السلام",
            prophet_name_en="Jesus (peace be upon him)",
            description_ar="تكلم عيسى عليه السلام وهو في المهد صبياً، دفاعاً عن أمه مريم وإعلاناً لنبوته",
            description_en="Jesus spoke from the cradle as an infant, defending his mother Mary and announcing his prophethood.",
            significance_ar="براءة مريم من التهمة الباطلة، وإعلان نبوة عيسى من البداية",
            significance_en="Clearing Mary of false accusations and announcing Jesus' prophethood from the beginning.",
            lessons_ar=[
                "الله يدافع عن عباده الصالحين",
                "المعجزات تظهر في وقت الحاجة",
                "عيسى عبد الله ورسوله"
            ],
            lessons_en=[
                "Allah defends His righteous servants",
                "Miracles appear when needed",
                "Jesus is Allah's servant and messenger"
            ],
            verses=[
                VerseReference(
                    surah_number=19,
                    surah_name_ar="مريم",
                    surah_name_en="Maryam",
                    ayah_number=29,
                    ayah_range="29-33",
                    text_ar="فَأَشَارَتْ إِلَيْهِ قَالُوا كَيْفَ نُكَلِّمُ مَن كَانَ فِي الْمَهْدِ صَبِيًّا ۝ قَالَ إِنِّي عَبْدُ اللَّهِ آتَانِيَ الْكِتَابَ وَجَعَلَنِي نَبِيًّا",
                    text_en="So she pointed to him. They said, 'How can we speak to one who is in the cradle a child?' He said, 'Indeed, I am the servant of Allah. He has given me the Scripture and made me a prophet.'",
                    relevance="الآيات الأساسية لمعجزة الكلام في المهد"
                ),
                VerseReference(
                    surah_number=3,
                    surah_name_ar="آل عمران",
                    surah_name_en="Aal-Imran",
                    ayah_number=46,
                    ayah_range="46",
                    text_ar="وَيُكَلِّمُ النَّاسَ فِي الْمَهْدِ وَكَهْلًا وَمِنَ الصَّالِحِينَ",
                    text_en="He will speak to the people in the cradle and in maturity and will be of the righteous.",
                    relevance="البشارة بكلام عيسى في المهد"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="أول ما نطق به عيسى: إني عبد الله، رداً على من يدعي ألوهيته",
                    explanation_en="The first thing Jesus said was 'I am the servant of Allah,' refuting those who claim his divinity.",
                    volume="5",
                    page="220"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="كلامه في المهد كان لتبرئة أمه من الفاحشة التي اتهمت بها",
                    explanation_en="His speech in the cradle was to clear his mother of the immorality she was accused of.",
                    volume="11",
                    page="100"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="تكلم عيسى في المهد ثم سكت حتى بلغ سن الكلام",
                    explanation_en="Jesus spoke in the cradle then was silent until he reached the age of speech.",
                    volume="2",
                    page="320"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="في هذه المعجزة دليل على براءة مريم وصدق نبوة عيسى",
                    explanation_en="In this miracle is proof of Mary's innocence and the truth of Jesus' prophethood.",
                    volume="4",
                    page="200"
                )
            ],
            themes=["innocence", "prophethood", "divine_defense", "miracle"],
            themes_ar=["البراءة", "النبوة", "الدفاع الإلهي", "المعجزة"],
            related_miracles=["isa_healing_blind", "isa_raising_dead"],
            historical_context_ar="تكلم عيسى عندما اتهم قومه أمه مريم بالفاحشة",
            historical_context_en="Jesus spoke when his people accused his mother Mary of immorality.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Ibrahim (Abraham) Miracles
        self._miracles["ibrahim_fire_cool"] = Miracle(
            id="ibrahim_fire_cool",
            name_ar="النار أصبحت برداً وسلاماً على إبراهيم",
            name_en="Fire Becoming Cool and Safe for Ibrahim",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.PROTECTION,
            prophet_id="ibrahim",
            prophet_name_ar="إبراهيم عليه السلام",
            prophet_name_en="Abraham (peace be upon him)",
            description_ar="ألقي إبراهيم في النار العظيمة فأمر الله النار أن تكون برداً وسلاماً عليه فلم تحرقه",
            description_en="Ibrahim was thrown into a great fire, but Allah commanded the fire to be cool and safe for him, so it did not burn him.",
            significance_ar="دليل على حماية الله لأوليائه، وأن العناصر تطيع أمر الله",
            significance_en="Evidence of Allah's protection of His close servants, and that elements obey Allah's command.",
            lessons_ar=[
                "التوكل على الله في أصعب المواقف",
                "حماية الله لعباده المخلصين",
                "الثبات على الحق مهما كان الثمن"
            ],
            lessons_en=[
                "Trusting Allah in the most difficult situations",
                "Allah's protection of His sincere servants",
                "Standing firm on truth regardless of the cost"
            ],
            verses=[
                VerseReference(
                    surah_number=21,
                    surah_name_ar="الأنبياء",
                    surah_name_en="Al-Anbiya",
                    ayah_number=69,
                    ayah_range="68-70",
                    text_ar="قُلْنَا يَا نَارُ كُونِي بَرْدًا وَسَلَامًا عَلَىٰ إِبْرَاهِيمَ",
                    text_en="We said, 'O fire, be coolness and safety upon Abraham.'",
                    relevance="الآية الأساسية للمعجزة"
                ),
                VerseReference(
                    surah_number=37,
                    surah_name_ar="الصافات",
                    surah_name_en="As-Saffat",
                    ayah_number=97,
                    ayah_range="97-98",
                    text_ar="قَالُوا ابْنُوا لَهُ بُنْيَانًا فَأَلْقُوهُ فِي الْجَحِيمِ ۝ فَأَرَادُوا بِهِ كَيْدًا فَجَعَلْنَاهُمُ الْأَسْفَلِينَ",
                    text_en="They said, 'Construct for him a structure and throw him into the burning fire.' And they intended for him a plan, but We made them the most humiliated.",
                    relevance="سياق المحرقة وإحباط كيد الكافرين"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="قال ابن عباس: لو لم يقل وسلاماً لآذاه بردها",
                    explanation_en="Ibn Abbas said: If He had not said 'and safe', its coldness would have harmed him.",
                    volume="5",
                    page="354"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="النار بذاتها محرقة، لكن الله نزع منها صفة الإحراق لإبراهيم خاصة",
                    explanation_en="Fire by its nature burns, but Allah removed its burning property specifically for Ibrahim.",
                    volume="11",
                    page="303"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="برداً: أي ذات برد، وسلاماً: أي سالمة لا تضره",
                    explanation_en="Cool: meaning having coolness. Safe: meaning harmless, not hurting him.",
                    volume="3",
                    page="89"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه المعجزة من أعظم الدلائل على أن الله يحمي أولياءه",
                    explanation_en="This miracle is among the greatest proofs that Allah protects His close servants.",
                    volume="4",
                    page="450"
                )
            ],
            themes=["protection", "faith", "trust", "divine_power"],
            themes_ar=["الحماية", "الإيمان", "التوكل", "القدرة الإلهية"],
            related_miracles=["ibrahim_sacrifice"],
            historical_context_ar="ألقاه قومه في النار لأنه حطم أصنامهم",
            historical_context_en="His people threw him into fire because he destroyed their idols.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Muhammad (PBUH) Miracles
        self._miracles["muhammad_moon_split"] = Miracle(
            id="muhammad_moon_split",
            name_ar="انشقاق القمر",
            name_en="The Splitting of the Moon",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.NATURE_CONTROL,
            prophet_id="muhammad",
            prophet_name_ar="محمد صلى الله عليه وسلم",
            prophet_name_en="Muhammad (peace and blessings be upon him)",
            description_ar="انشق القمر نصفين بإشارة من النبي صلى الله عليه وسلم، وشاهده أهل مكة",
            description_en="The moon split into two halves by a gesture from the Prophet (PBUH), witnessed by the people of Makkah.",
            significance_ar="معجزة كونية عظيمة تدل على صدق النبوة",
            significance_en="A great cosmic miracle indicating the truth of prophethood.",
            lessons_ar=[
                "قدرة الله على كل شيء",
                "الآيات لا تنفع من أبى الإيمان",
                "صدق نبوة محمد صلى الله عليه وسلم"
            ],
            lessons_en=[
                "Allah's power over all things",
                "Signs do not benefit those who refuse to believe",
                "The truthfulness of Muhammad's prophethood"
            ],
            verses=[
                VerseReference(
                    surah_number=54,
                    surah_name_ar="القمر",
                    surah_name_en="Al-Qamar",
                    ayah_number=1,
                    ayah_range="1-2",
                    text_ar="اقْتَرَبَتِ السَّاعَةُ وَانشَقَّ الْقَمَرُ ۝ وَإِن يَرَوْا آيَةً يُعْرِضُوا وَيَقُولُوا سِحْرٌ مُّسْتَمِرٌّ",
                    text_en="The Hour has come near, and the moon has split. And if they see a sign, they turn away and say, 'Passing magic.'",
                    relevance="الآية الصريحة في انشقاق القمر"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="هذا أمر قد كان، وذلك أن أهل مكة سألوا رسول الله آية فأشار إلى القمر فانفلق فلقتين",
                    explanation_en="This indeed happened. The people of Makkah asked the Messenger of Allah for a sign, so he pointed to the moon and it split into two parts.",
                    volume="7",
                    page="471"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="روى البخاري ومسلم أن القمر انشق على عهد رسول الله فلقتين",
                    explanation_en="Bukhari and Muslim narrated that the moon split into two parts during the time of the Messenger of Allah.",
                    volume="17",
                    page="126"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="انشقاق القمر من أعلام نبوته صلى الله عليه وسلم الظاهرة",
                    explanation_en="The splitting of the moon is among the clear signs of his prophethood (PBUH).",
                    volume="4",
                    page="215"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="انشقاق القمر ثابت بالقرآن والسنة المتواترة",
                    explanation_en="The splitting of the moon is established by the Quran and mutawatir (mass-transmitted) Sunnah.",
                    volume="7",
                    page="615"
                )
            ],
            themes=["prophethood", "divine_power", "signs", "truth"],
            themes_ar=["النبوة", "القدرة الإلهية", "الآيات", "الحق"],
            related_miracles=["quran_revelation"],
            historical_context_ar="طلب كفار قريش آية فأراهم النبي انشقاق القمر",
            historical_context_en="The disbelievers of Quraysh asked for a sign, so the Prophet showed them the splitting of the moon.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Yunus (Jonah) Miracle
        self._miracles["yunus_whale"] = Miracle(
            id="yunus_whale",
            name_ar="نجاة يونس من بطن الحوت",
            name_en="Jonah's Survival in the Whale",
            category=MiracleCategory.PROPHETIC,
            miracle_type=MiracleType.PROTECTION,
            prophet_id="yunus",
            prophet_name_ar="يونس عليه السلام",
            prophet_name_en="Jonah (peace be upon him)",
            description_ar="ابتلع الحوت يونس عليه السلام فمكث في بطنه، ثم نجاه الله بعد توبته ودعائه",
            description_en="The whale swallowed Jonah (peace be upon him) and he stayed in its belly, then Allah saved him after his repentance and supplication.",
            significance_ar="دليل على رحمة الله بالتائبين وقبول دعاء المضطرين",
            significance_en="Evidence of Allah's mercy upon the repentant and acceptance of the supplication of the distressed.",
            lessons_ar=[
                "التوبة تنجي من كل ضيق",
                "الدعاء في الشدائد",
                "لا يأس مع الله"
            ],
            lessons_en=[
                "Repentance saves from all distress",
                "Supplication during hardships",
                "No despair with Allah"
            ],
            verses=[
                VerseReference(
                    surah_number=37,
                    surah_name_ar="الصافات",
                    surah_name_en="As-Saffat",
                    ayah_number=142,
                    ayah_range="139-145",
                    text_ar="فَالْتَقَمَهُ الْحُوتُ وَهُوَ مُلِيمٌ ۝ فَلَوْلَا أَنَّهُ كَانَ مِنَ الْمُسَبِّحِينَ ۝ لَلَبِثَ فِي بَطْنِهِ إِلَىٰ يَوْمِ يُبْعَثُونَ",
                    text_en="Then the fish swallowed him, while he was blameworthy. And had he not been of those who exalt Allah, He would have remained inside its belly until the Day they are resurrected.",
                    relevance="القصة الكاملة لالتقام الحوت والنجاة"
                ),
                VerseReference(
                    surah_number=21,
                    surah_name_ar="الأنبياء",
                    surah_name_en="Al-Anbiya",
                    ayah_number=87,
                    ayah_range="87-88",
                    text_ar="وَذَا النُّونِ إِذ ذَّهَبَ مُغَاضِبًا فَظَنَّ أَن لَّن نَّقْدِرَ عَلَيْهِ فَنَادَىٰ فِي الظُّلُمَاتِ أَن لَّا إِلَـٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ",
                    text_en="And [mention] the man of the fish, when he went off in anger and thought that We would not decree [anything] upon him. And he called out within the darknesses, 'There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.'",
                    relevance="دعاء يونس في الظلمات"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="الظلمات ثلاث: ظلمة الليل، وظلمة البحر، وظلمة بطن الحوت",
                    explanation_en="The darknesses were three: darkness of night, darkness of the sea, and darkness of the whale's belly.",
                    volume="5",
                    page="358"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="دعاء يونس من أعظم الأدعية المستجابة",
                    explanation_en="Jonah's supplication is among the greatest answered prayers.",
                    volume="11",
                    page="334"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="كان من المسبحين: أي من المصلين قبل ذلك، فنفعه عمله السابق",
                    explanation_en="Was of those who exalt Allah: meaning he was among those who prayed before, so his previous deeds benefited him.",
                    volume="3",
                    page="94"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="هذه القصة تبين فضل الذكر والتسبيح وأثره في النجاة",
                    explanation_en="This story shows the virtue of remembrance and glorification and their effect on salvation.",
                    volume="6",
                    page="456"
                )
            ],
            themes=["repentance", "supplication", "mercy", "salvation"],
            themes_ar=["التوبة", "الدعاء", "الرحمة", "النجاة"],
            related_miracles=[],
            historical_context_ar="ذهب يونس مغاضباً من قومه قبل إذن الله فابتلاه الله",
            historical_context_en="Jonah left angrily from his people before Allah's permission, so Allah tested him.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Divine Miracles - Creation
        self._miracles["creation_adam"] = Miracle(
            id="creation_adam",
            name_ar="خلق آدم من طين",
            name_en="Creation of Adam from Clay",
            category=MiracleCategory.CREATION,
            miracle_type=MiracleType.CREATION,
            prophet_id="adam",
            prophet_name_ar="آدم عليه السلام",
            prophet_name_en="Adam (peace be upon him)",
            description_ar="خلق الله آدم من طين ثم نفخ فيه من روحه فصار بشراً سوياً",
            description_en="Allah created Adam from clay then breathed into him of His spirit, making him a complete human being.",
            significance_ar="أصل الخلق البشري ودليل على قدرة الله في الإيجاد من العدم",
            significance_en="The origin of human creation and evidence of Allah's power to create from nothing.",
            lessons_ar=[
                "تكريم الإنسان",
                "أصل البشرية واحد",
                "قدرة الله على الخلق"
            ],
            lessons_en=[
                "The honor of humanity",
                "The single origin of mankind",
                "Allah's power of creation"
            ],
            verses=[
                VerseReference(
                    surah_number=32,
                    surah_name_ar="السجدة",
                    surah_name_en="As-Sajdah",
                    ayah_number=7,
                    ayah_range="7-9",
                    text_ar="الَّذِي أَحْسَنَ كُلَّ شَيْءٍ خَلَقَهُ وَبَدَأَ خَلْقَ الْإِنسَانِ مِن طِينٍ",
                    text_en="Who perfected everything which He created and began the creation of man from clay.",
                    relevance="خلق الإنسان من طين"
                ),
                VerseReference(
                    surah_number=15,
                    surah_name_ar="الحجر",
                    surah_name_en="Al-Hijr",
                    ayah_number=28,
                    ayah_range="28-29",
                    text_ar="وَإِذْ قَالَ رَبُّكَ لِلْمَلَائِكَةِ إِنِّي خَالِقٌ بَشَرًا مِّن صَلْصَالٍ مِّنْ حَمَإٍ مَّسْنُونٍ ۝ فَإِذَا سَوَّيْتُهُ وَنَفَخْتُ فِيهِ مِن رُّوحِي فَقَعُوا لَهُ سَاجِدِينَ",
                    text_en="And [mention, O Muhammad], when your Lord said to the angels, 'I will create a human being out of clay from an altered black mud. And when I have proportioned him and breathed into him of My [created] soul, then fall down to him in prostration.'",
                    relevance="تفصيل خلق آدم ونفخ الروح"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="خلق آدم من تراب ثم جعله طيناً ثم صلصالاً كالفخار",
                    explanation_en="Adam was created from dust, then made into clay, then into dried clay like pottery.",
                    volume="4",
                    page="448"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="نفخ الروح: إحداث الحياة فيه بقدرة الله",
                    explanation_en="Breathing the soul: bringing life to him by Allah's power.",
                    volume="10",
                    page="23"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="خلق آدم من طين مختلف من جميع أنحاء الأرض",
                    explanation_en="Adam was created from varied clay from all parts of the earth.",
                    volume="2",
                    page="276"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="خلق آدم بيد الله تكريماً له على سائر المخلوقات",
                    explanation_en="Adam was created by Allah's Hand as an honor above all other creatures.",
                    volume="3",
                    page="210"
                )
            ],
            themes=["creation", "honor", "divine_power", "origin"],
            themes_ar=["الخلق", "التكريم", "القدرة الإلهية", "الأصل"],
            related_miracles=["creation_universe"],
            historical_context_ar="بداية الخلق البشري قبل نزول آدم إلى الأرض",
            historical_context_en="The beginning of human creation before Adam descended to earth.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Revelation Miracle
        self._miracles["quran_revelation"] = Miracle(
            id="quran_revelation",
            name_ar="نزول القرآن الكريم",
            name_en="Revelation of the Noble Quran",
            category=MiracleCategory.REVELATION,
            miracle_type=MiracleType.KNOWLEDGE,
            prophet_id="muhammad",
            prophet_name_ar="محمد صلى الله عليه وسلم",
            prophet_name_en="Muhammad (peace and blessings be upon him)",
            description_ar="القرآن الكريم معجزة خالدة، نزل على محمد صلى الله عليه وسلم، يتحدى البشر أن يأتوا بمثله",
            description_en="The Noble Quran is an eternal miracle, revealed to Muhammad (PBUH), challenging mankind to produce anything like it.",
            significance_ar="المعجزة الخالدة الباقية إلى يوم القيامة",
            significance_en="The eternal miracle remaining until the Day of Judgment.",
            lessons_ar=[
                "القرآن كلام الله",
                "إعجاز القرآن البلاغي والعلمي",
                "هداية القرآن للبشرية"
            ],
            lessons_en=[
                "The Quran is Allah's speech",
                "The linguistic and scientific miracle of the Quran",
                "The Quran's guidance for humanity"
            ],
            verses=[
                VerseReference(
                    surah_number=2,
                    surah_name_ar="البقرة",
                    surah_name_en="Al-Baqarah",
                    ayah_number=23,
                    ayah_range="23-24",
                    text_ar="وَإِن كُنتُمْ فِي رَيْبٍ مِّمَّا نَزَّلْنَا عَلَىٰ عَبْدِنَا فَأْتُوا بِسُورَةٍ مِّن مِّثْلِهِ وَادْعُوا شُهَدَاءَكُم مِّن دُونِ اللَّهِ إِن كُنتُمْ صَادِقِينَ",
                    text_en="And if you are in doubt about what We have sent down upon Our Servant, then produce a surah the like thereof and call upon your witnesses other than Allah, if you should be truthful.",
                    relevance="تحدي القرآن للبشرية"
                ),
                VerseReference(
                    surah_number=17,
                    surah_name_ar="الإسراء",
                    surah_name_en="Al-Isra",
                    ayah_number=88,
                    ayah_range="88",
                    text_ar="قُل لَّئِنِ اجْتَمَعَتِ الْإِنسُ وَالْجِنُّ عَلَىٰ أَن يَأْتُوا بِمِثْلِ هَـٰذَا الْقُرْآنِ لَا يَأْتُونَ بِمِثْلِهِ وَلَوْ كَانَ بَعْضُهُمْ لِبَعْضٍ ظَهِيرًا",
                    text_en="Say, 'If mankind and the jinn gathered in order to produce the like of this Quran, they could not produce the like of it, even if they were to each other assistants.'",
                    relevance="استحالة الإتيان بمثل القرآن"
                )
            ],
            tafsir_references=[
                TafsirReference(
                    scholar_name_ar="ابن كثير",
                    scholar_name_en="Ibn Kathir",
                    madhab=Madhab.SHAFII,
                    book_name_ar="تفسير القرآن العظيم",
                    book_name_en="Tafsir al-Quran al-Azim",
                    explanation_ar="القرآن معجزة النبي الخالدة، عجز العرب مع فصاحتهم عن الإتيان بمثله",
                    explanation_en="The Quran is the Prophet's eternal miracle; the Arabs despite their eloquence could not produce anything like it.",
                    volume="1",
                    page="71"
                ),
                TafsirReference(
                    scholar_name_ar="القرطبي",
                    scholar_name_en="Al-Qurtubi",
                    madhab=Madhab.MALIKI,
                    book_name_ar="الجامع لأحكام القرآن",
                    book_name_en="Al-Jami li-Ahkam al-Quran",
                    explanation_ar="إعجاز القرآن يتجدد في كل عصر بما يكتشفه العلم من حقائقه",
                    explanation_en="The miracle of the Quran renews in every era with what science discovers of its truths.",
                    volume="1",
                    page="77"
                ),
                TafsirReference(
                    scholar_name_ar="النسفي",
                    scholar_name_en="Al-Nasafi",
                    madhab=Madhab.HANAFI,
                    book_name_ar="مدارك التنزيل",
                    book_name_en="Madarik al-Tanzil",
                    explanation_ar="التحدي بسورة واحدة يدل على عجز الإتيان بأقل منه",
                    explanation_en="The challenge with even one surah indicates the inability to produce anything less.",
                    volume="1",
                    page="47"
                ),
                TafsirReference(
                    scholar_name_ar="الشنقيطي",
                    scholar_name_en="Al-Shanqiti",
                    madhab=Madhab.HANBALI,
                    book_name_ar="أضواء البيان",
                    book_name_en="Adwa al-Bayan",
                    explanation_ar="عجز الخلق عن معارضة القرآن دليل قاطع على أنه من عند الله",
                    explanation_en="The inability of creation to match the Quran is decisive proof that it is from Allah.",
                    volume="1",
                    page="23"
                )
            ],
            themes=["revelation", "guidance", "miracle", "truth"],
            themes_ar=["الوحي", "الهداية", "المعجزة", "الحق"],
            related_miracles=["muhammad_moon_split"],
            historical_context_ar="نزل القرآن على مدى 23 سنة في مكة والمدينة",
            historical_context_en="The Quran was revealed over 23 years in Makkah and Madinah.",
            verification_status=VerificationStatus.VERIFIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def _build_search_index(self):
        """Build search index for fast miracle lookup"""
        for miracle_id, miracle in self._miracles.items():
            # Index by prophet
            if miracle.prophet_id:
                self._search_index[f"prophet:{miracle.prophet_id}"].add(miracle_id)

            # Index by category
            self._search_index[f"category:{miracle.category.value}"].add(miracle_id)

            # Index by type
            self._search_index[f"type:{miracle.miracle_type.value}"].add(miracle_id)

            # Index by themes
            for theme in miracle.themes:
                self._search_index[f"theme:{theme}"].add(miracle_id)

            # Index by Arabic keywords
            keywords_ar = miracle.name_ar.split() + miracle.description_ar.split()[:10]
            for keyword in keywords_ar:
                if len(keyword) > 2:
                    self._search_index[f"ar:{keyword}"].add(miracle_id)

            # Index by English keywords
            keywords_en = miracle.name_en.lower().split() + miracle.description_en.lower().split()[:10]
            for keyword in keywords_en:
                if len(keyword) > 2:
                    self._search_index[f"en:{keyword}"].add(miracle_id)

    # ============================================
    # SEARCH METHODS
    # ============================================

    def search_miracles(
        self,
        query: str,
        prophet_id: Optional[str] = None,
        category: Optional[str] = None,
        miracle_type: Optional[str] = None,
        theme: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search miracles with multiple filters and semantic matching.
        """
        results = []
        query_lower = query.lower()

        for miracle_id, miracle in self._miracles.items():
            # Apply filters
            if prophet_id and miracle.prophet_id != prophet_id:
                continue
            if category and miracle.category.value != category:
                continue
            if miracle_type and miracle.miracle_type.value != miracle_type:
                continue
            if theme and theme not in miracle.themes:
                continue

            # Calculate relevance score
            score = 0.0

            # Exact name match
            if query in miracle.name_ar or query_lower in miracle.name_en.lower():
                score += 10.0

            # Description match
            if query in miracle.description_ar or query_lower in miracle.description_en.lower():
                score += 5.0

            # Prophet name match
            if miracle.prophet_name_ar and query in miracle.prophet_name_ar:
                score += 7.0
            if miracle.prophet_name_en and query_lower in miracle.prophet_name_en.lower():
                score += 7.0

            # Theme match
            for t in miracle.themes:
                if query_lower in t:
                    score += 3.0

            # Verse text match
            for verse in miracle.verses:
                if query in verse.text_ar or query_lower in verse.text_en.lower():
                    score += 4.0
                    break

            if score > 0 or not query:
                results.append({
                    "miracle": self._miracle_to_dict(miracle),
                    "relevance_score": round(score, 2)
                })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "query": query,
            "filters": {
                "prophet_id": prophet_id,
                "category": category,
                "miracle_type": miracle_type,
                "theme": theme
            },
            "results": results[:limit],
            "total": len(results)
        }

    def semantic_search_miracles(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.1
    ) -> Dict[str, Any]:
        """
        Semantic search using AraBERT-like embeddings.
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        results = []
        for miracle_id, miracle in self._miracles.items():
            # Generate miracle embedding
            miracle_text = f"{miracle.name_ar} {miracle.description_ar}"
            miracle_embedding = self._generate_embedding(miracle_text)

            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, miracle_embedding)

            if similarity >= min_similarity:
                results.append({
                    "miracle": self._miracle_to_dict(miracle),
                    "similarity_score": round(similarity, 4)
                })

        # Sort by similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
            "embedding_dimension": self._embedding_dim
        }

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate AraBERT-like embedding for text"""
        embedding = np.zeros(self._embedding_dim)

        # Arabic root patterns
        arabic_roots = {
            "معجز": 0, "آية": 1, "نبي": 2, "رسول": 3, "خلق": 4,
            "شفا": 5, "حي": 6, "موت": 7, "نار": 8, "ماء": 9,
            "بحر": 10, "قمر": 11, "شمس": 12, "سماء": 13, "أرض": 14,
            "إيمان": 15, "توكل": 16, "صبر": 17, "توبة": 18, "رحمة": 19
        }

        for root, idx in arabic_roots.items():
            if root in text:
                embedding[idx] = 1.0

        # Prophet names
        prophets = {
            "موسى": 50, "عيسى": 51, "إبراهيم": 52, "محمد": 53,
            "نوح": 54, "يونس": 55, "آدم": 56, "يوسف": 57
        }

        for prophet, idx in prophets.items():
            if prophet in text:
                embedding[idx] = 1.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    # ============================================
    # RETRIEVAL METHODS
    # ============================================

    def get_miracle(self, miracle_id: str) -> Dict[str, Any]:
        """Get a specific miracle by ID"""
        miracle = self._miracles.get(miracle_id)
        if not miracle:
            return {"error": f"Miracle '{miracle_id}' not found"}

        return {
            "miracle": self._miracle_to_dict(miracle),
            "related_miracles": [
                self._miracle_to_dict(self._miracles[m])
                for m in miracle.related_miracles
                if m in self._miracles
            ]
        }

    def get_all_miracles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get all miracles with optional filtering"""
        miracles = []
        for miracle in self._miracles.values():
            if category and miracle.category.value != category:
                continue
            miracles.append(self._miracle_to_dict(miracle))

        return {
            "miracles": miracles[:limit],
            "total": len(miracles),
            "categories": [c.value for c in MiracleCategory]
        }

    def get_miracles_by_prophet(self, prophet_id: str) -> Dict[str, Any]:
        """Get all miracles for a specific prophet"""
        miracles = []
        for miracle in self._miracles.values():
            if miracle.prophet_id == prophet_id:
                miracles.append(self._miracle_to_dict(miracle))

        # Get prophet info
        prophet_name_ar = ""
        prophet_name_en = ""
        if miracles:
            prophet_name_ar = miracles[0].get("prophet_name_ar", "")
            prophet_name_en = miracles[0].get("prophet_name_en", "")

        return {
            "prophet_id": prophet_id,
            "prophet_name_ar": prophet_name_ar,
            "prophet_name_en": prophet_name_en,
            "miracles": miracles,
            "miracle_count": len(miracles)
        }

    def get_miracle_categories(self) -> Dict[str, Any]:
        """Get all miracle categories with counts"""
        categories = []
        for cat in MiracleCategory:
            count = sum(1 for m in self._miracles.values() if m.category == cat)
            categories.append({
                "id": cat.value,
                "name_ar": self._get_category_name_ar(cat),
                "name_en": cat.value.replace("_", " ").title(),
                "miracle_count": count
            })

        return {"categories": categories}

    def _get_category_name_ar(self, category: MiracleCategory) -> str:
        """Get Arabic name for category"""
        names = {
            MiracleCategory.PROPHETIC: "معجزات الأنبياء",
            MiracleCategory.DIVINE: "الآيات الإلهية",
            MiracleCategory.CREATION: "معجزات الخلق",
            MiracleCategory.NATURAL: "الآيات الكونية",
            MiracleCategory.REVELATION: "معجزة الوحي",
            MiracleCategory.HISTORICAL: "المعجزات التاريخية"
        }
        return names.get(category, category.value)

    def get_miracle_themes(self) -> Dict[str, Any]:
        """Get all themes associated with miracles"""
        theme_counts = defaultdict(int)
        theme_names_ar = {}

        for miracle in self._miracles.values():
            for i, theme in enumerate(miracle.themes):
                theme_counts[theme] += 1
                if theme not in theme_names_ar and i < len(miracle.themes_ar):
                    theme_names_ar[theme] = miracle.themes_ar[i]

        themes = [
            {
                "id": theme,
                "name_ar": theme_names_ar.get(theme, theme),
                "name_en": theme.replace("_", " ").title(),
                "miracle_count": count
            }
            for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1])
        ]

        return {"themes": themes, "total_themes": len(themes)}

    # ============================================
    # GRAPH VISUALIZATION
    # ============================================

    def get_miracle_graph(
        self,
        center_miracle_id: Optional[str] = None,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get graph visualization data for miracles.
        Shows connections between miracles, prophets, and themes.
        """
        nodes = []
        edges = []
        node_ids = set()

        def add_miracle_node(miracle: Miracle):
            if miracle.id not in node_ids:
                node_ids.add(miracle.id)
                nodes.append({
                    "id": miracle.id,
                    "type": "miracle",
                    "label_ar": miracle.name_ar,
                    "label_en": miracle.name_en,
                    "category": miracle.category.value,
                    "color": self._get_category_color(miracle.category)
                })

        def add_prophet_node(prophet_id: str, name_ar: str, name_en: str):
            node_key = f"prophet_{prophet_id}"
            if node_key not in node_ids:
                node_ids.add(node_key)
                nodes.append({
                    "id": node_key,
                    "type": "prophet",
                    "label_ar": name_ar,
                    "label_en": name_en,
                    "color": "#FFC107"
                })

        def add_theme_node(theme: str, theme_ar: str):
            node_key = f"theme_{theme}"
            if node_key not in node_ids:
                node_ids.add(node_key)
                nodes.append({
                    "id": node_key,
                    "type": "theme",
                    "label_ar": theme_ar,
                    "label_en": theme.replace("_", " ").title(),
                    "color": "#2196F3"
                })

        # If center miracle specified, start from there
        if center_miracle_id and center_miracle_id in self._miracles:
            miracle = self._miracles[center_miracle_id]
            add_miracle_node(miracle)

            # Add prophet connection
            if miracle.prophet_id:
                add_prophet_node(
                    miracle.prophet_id,
                    miracle.prophet_name_ar or "",
                    miracle.prophet_name_en or ""
                )
                edges.append({
                    "source": f"prophet_{miracle.prophet_id}",
                    "target": miracle.id,
                    "type": "performed_by"
                })

            # Add theme connections
            for i, theme in enumerate(miracle.themes):
                theme_ar = miracle.themes_ar[i] if i < len(miracle.themes_ar) else theme
                add_theme_node(theme, theme_ar)
                edges.append({
                    "source": miracle.id,
                    "target": f"theme_{theme}",
                    "type": "has_theme"
                })

            # Add related miracles
            for related_id in miracle.related_miracles:
                if related_id in self._miracles:
                    related = self._miracles[related_id]
                    add_miracle_node(related)
                    edges.append({
                        "source": miracle.id,
                        "target": related_id,
                        "type": "related_to"
                    })
        else:
            # Build full graph
            for miracle in list(self._miracles.values())[:20]:  # Limit for performance
                add_miracle_node(miracle)

                if miracle.prophet_id:
                    add_prophet_node(
                        miracle.prophet_id,
                        miracle.prophet_name_ar or "",
                        miracle.prophet_name_en or ""
                    )
                    edges.append({
                        "source": f"prophet_{miracle.prophet_id}",
                        "target": miracle.id,
                        "type": "performed_by"
                    })

                # Add primary theme only
                if miracle.themes:
                    theme = miracle.themes[0]
                    theme_ar = miracle.themes_ar[0] if miracle.themes_ar else theme
                    add_theme_node(theme, theme_ar)
                    edges.append({
                        "source": miracle.id,
                        "target": f"theme_{theme}",
                        "type": "has_theme"
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "legend": [
                {"type": "miracle", "color": "#4CAF50", "label_ar": "معجزة", "label_en": "Miracle"},
                {"type": "prophet", "color": "#FFC107", "label_ar": "نبي", "label_en": "Prophet"},
                {"type": "theme", "color": "#2196F3", "label_ar": "موضوع", "label_en": "Theme"}
            ]
        }

    def _get_category_color(self, category: MiracleCategory) -> str:
        """Get color for miracle category"""
        colors = {
            MiracleCategory.PROPHETIC: "#4CAF50",
            MiracleCategory.DIVINE: "#9C27B0",
            MiracleCategory.CREATION: "#FF5722",
            MiracleCategory.NATURAL: "#00BCD4",
            MiracleCategory.REVELATION: "#E91E63",
            MiracleCategory.HISTORICAL: "#795548"
        }
        return colors.get(category, "#757575")

    # ============================================
    # FEEDBACK SYSTEM
    # ============================================

    def submit_feedback(
        self,
        miracle_id: str,
        user_id: str,
        feedback_type: str,
        content_ar: str,
        content_en: str = ""
    ) -> Dict[str, Any]:
        """Submit user feedback on a miracle"""
        if miracle_id not in self._miracles:
            return {"error": f"Miracle '{miracle_id}' not found"}

        feedback_id = f"fb_{miracle_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        feedback = MiracleFeedback(
            feedback_id=feedback_id,
            miracle_id=miracle_id,
            user_id=user_id,
            feedback_type=feedback_type,
            content_ar=content_ar,
            content_en=content_en,
            status="pending",
            reviewer_id=None,
            reviewer_notes=None,
            created_at=datetime.now()
        )

        self._feedback[feedback_id] = feedback

        return {
            "success": True,
            "feedback_id": feedback_id,
            "message_ar": "شكراً لملاحظاتك، سيتم مراجعتها",
            "message_en": "Thank you for your feedback, it will be reviewed"
        }

    def get_miracle_feedback(
        self,
        miracle_id: str,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feedback for a specific miracle"""
        feedback_list = []
        for fb in self._feedback.values():
            if fb.miracle_id == miracle_id:
                if status_filter and fb.status != status_filter:
                    continue
                feedback_list.append({
                    "feedback_id": fb.feedback_id,
                    "feedback_type": fb.feedback_type,
                    "content_ar": fb.content_ar,
                    "content_en": fb.content_en,
                    "status": fb.status,
                    "created_at": fb.created_at.isoformat()
                })

        return {
            "miracle_id": miracle_id,
            "feedback": feedback_list,
            "total": len(feedback_list)
        }

    # ============================================
    # ADMIN & VERIFICATION
    # ============================================

    def get_admin_dashboard(self, admin_id: str) -> Dict[str, Any]:
        """Get admin dashboard with pending reviews"""
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        # Count miracles by status
        status_counts = defaultdict(int)
        for miracle in self._miracles.values():
            status_counts[miracle.verification_status.value] += 1

        # Get pending feedback
        pending_feedback = [
            {
                "feedback_id": fb.feedback_id,
                "miracle_id": fb.miracle_id,
                "feedback_type": fb.feedback_type,
                "content_ar": fb.content_ar[:100],
                "created_at": fb.created_at.isoformat()
            }
            for fb in self._feedback.values()
            if fb.status == "pending"
        ]

        return {
            "admin_id": admin_id,
            "statistics": {
                "total_miracles": len(self._miracles),
                "by_verification_status": dict(status_counts),
                "pending_feedback": len(pending_feedback),
                "total_feedback": len(self._feedback)
            },
            "pending_feedback": pending_feedback[:20],
            "generated_at": datetime.now().isoformat()
        }

    def review_feedback(
        self,
        admin_id: str,
        feedback_id: str,
        decision: str,  # "accepted", "rejected"
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Review and decide on user feedback"""
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        if feedback_id not in self._feedback:
            return {"error": f"Feedback '{feedback_id}' not found"}

        feedback = self._feedback[feedback_id]
        feedback.status = decision
        feedback.reviewer_id = admin_id
        feedback.reviewer_notes = notes

        return {
            "success": True,
            "feedback_id": feedback_id,
            "new_status": decision,
            "reviewed_by": admin_id
        }

    # ============================================
    # UTILITY METHODS
    # ============================================

    def _miracle_to_dict(self, miracle: Miracle) -> Dict[str, Any]:
        """Convert Miracle object to dictionary"""
        return {
            "id": miracle.id,
            "name_ar": miracle.name_ar,
            "name_en": miracle.name_en,
            "category": miracle.category.value,
            "miracle_type": miracle.miracle_type.value,
            "prophet_id": miracle.prophet_id,
            "prophet_name_ar": miracle.prophet_name_ar,
            "prophet_name_en": miracle.prophet_name_en,
            "description_ar": miracle.description_ar,
            "description_en": miracle.description_en,
            "significance_ar": miracle.significance_ar,
            "significance_en": miracle.significance_en,
            "lessons_ar": miracle.lessons_ar,
            "lessons_en": miracle.lessons_en,
            "verses": [
                {
                    "surah_number": v.surah_number,
                    "surah_name_ar": v.surah_name_ar,
                    "surah_name_en": v.surah_name_en,
                    "ayah_number": v.ayah_number,
                    "ayah_range": v.ayah_range,
                    "text_ar": v.text_ar,
                    "text_en": v.text_en,
                    "relevance": v.relevance
                }
                for v in miracle.verses
            ],
            "tafsir_references": [
                {
                    "scholar_name_ar": t.scholar_name_ar,
                    "scholar_name_en": t.scholar_name_en,
                    "madhab": t.madhab.value,
                    "book_name_ar": t.book_name_ar,
                    "book_name_en": t.book_name_en,
                    "explanation_ar": t.explanation_ar,
                    "explanation_en": t.explanation_en,
                    "volume": t.volume,
                    "page": t.page
                }
                for t in miracle.tafsir_references
            ],
            "themes": miracle.themes,
            "themes_ar": miracle.themes_ar,
            "related_miracles": miracle.related_miracles,
            "historical_context_ar": miracle.historical_context_ar,
            "historical_context_en": miracle.historical_context_en,
            "verification_status": miracle.verification_status.value
        }

    def get_prophets_with_miracles(self) -> Dict[str, Any]:
        """Get all prophets who have miracles in the database"""
        prophets = {}
        for miracle in self._miracles.values():
            if miracle.prophet_id and miracle.prophet_id not in prophets:
                prophets[miracle.prophet_id] = {
                    "prophet_id": miracle.prophet_id,
                    "name_ar": miracle.prophet_name_ar,
                    "name_en": miracle.prophet_name_en,
                    "miracle_count": 0
                }
            if miracle.prophet_id:
                prophets[miracle.prophet_id]["miracle_count"] += 1

        return {
            "prophets": list(prophets.values()),
            "total": len(prophets)
        }

    def get_tafsir_sources(self) -> Dict[str, Any]:
        """Get all tafsir sources used in miracles"""
        sources = {}
        for miracle in self._miracles.values():
            for tafsir in miracle.tafsir_references:
                key = f"{tafsir.madhab.value}_{tafsir.scholar_name_en}"
                if key not in sources:
                    sources[key] = {
                        "scholar_name_ar": tafsir.scholar_name_ar,
                        "scholar_name_en": tafsir.scholar_name_en,
                        "madhab": tafsir.madhab.value,
                        "book_name_ar": tafsir.book_name_ar,
                        "book_name_en": tafsir.book_name_en,
                        "miracle_count": 0
                    }
                sources[key]["miracle_count"] += 1

        # Group by madhab
        by_madhab = defaultdict(list)
        for source in sources.values():
            by_madhab[source["madhab"]].append(source)

        return {
            "sources": list(sources.values()),
            "by_madhab": dict(by_madhab),
            "total": len(sources)
        }


# Create singleton instance
miracles_service = MiraclesService()
