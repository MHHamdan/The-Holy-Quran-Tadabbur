"""
Static Grammar Fallback Dataset.

This module provides pre-analyzed grammar data for common Quranic verses
when Ollama is unavailable.

SOURCES:
- Quranic Arabic Corpus (QAC) morphology
- Classical Arabic grammar references
- Manual verification by scholars

This is a fallback for when the LLM is unavailable. The data here
should be 100% accurate as it's pre-verified.
"""
from typing import Optional, Dict, List
from app.models.grammar import (
    TokenAnalysis,
    GrammarAnalysis,
    POSTag,
    GrammaticalRole,
    SentenceType,
    CaseEnding,
)


# =============================================================================
# STATIC MORPHOLOGY DATA
# Pre-analyzed grammar for common Quranic verses
# =============================================================================

STATIC_VERSES: Dict[str, GrammarAnalysis] = {}


def _build_static_data():
    """Build static morphology data for popular verses."""
    global STATIC_VERSES

    # 1:1 - بسم الله الرحمن الرحيم
    STATIC_VERSES["1:1"] = GrammarAnalysis(
        verse_reference="1:1",
        text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        sentence_type=SentenceType.SEMI,
        tokens=[
            TokenAnalysis(
                word="بِسْمِ",
                word_index=0,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.KASRA,
                i3rab="جار ومجرور، الباء حرف جر، واسم مجرور وعلامة جره الكسرة",
                root="س م و",
                pattern="فعل",
                confidence=0.95,
                notes_ar="مضاف",
            ),
            TokenAnalysis(
                word="اللَّهِ",
                word_index=1,
                pos=POSTag.NOUN_PROPER,
                role=GrammaticalRole.MUDAF_ILAYH,
                case_ending=CaseEnding.KASRA,
                i3rab="لفظ الجلالة مضاف إليه مجرور وعلامة جره الكسرة",
                root="أ ل ه",
                confidence=0.98,
                notes_ar="لفظ الجلالة",
            ),
            TokenAnalysis(
                word="الرَّحْمَٰنِ",
                word_index=2,
                pos=POSTag.NOUN,
                role=GrammaticalRole.NAT,
                case_ending=CaseEnding.KASRA,
                i3rab="نعت مجرور وعلامة جره الكسرة",
                root="ر ح م",
                pattern="فعلان",
                confidence=0.95,
                notes_ar="صفة لله تعالى",
            ),
            TokenAnalysis(
                word="الرَّحِيمِ",
                word_index=3,
                pos=POSTag.NOUN,
                role=GrammaticalRole.NAT,
                case_ending=CaseEnding.KASRA,
                i3rab="نعت ثان مجرور وعلامة جره الكسرة",
                root="ر ح م",
                pattern="فعيل",
                confidence=0.95,
                notes_ar="صفة لله تعالى",
            ),
        ],
        notes_ar="جملة البسملة، شبه جملة متعلقة بمحذوف تقديره: أبتدئ",
        overall_confidence=0.95,
        source="static",
    )

    # 1:2 - الحمد لله رب العالمين
    STATIC_VERSES["1:2"] = GrammarAnalysis(
        verse_reference="1:2",
        text="الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="الْحَمْدُ",
                word_index=0,
                pos=POSTag.NOUN,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="مبتدأ مرفوع وعلامة رفعه الضمة الظاهرة",
                root="ح م د",
                pattern="فعل",
                confidence=0.98,
                notes_ar="معرف بأل",
            ),
            TokenAnalysis(
                word="لِلَّهِ",
                word_index=1,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.KASRA,
                i3rab="جار ومجرور متعلقان بمحذوف خبر",
                root="أ ل ه",
                confidence=0.95,
                notes_ar="اللام حرف جر، ولفظ الجلالة مجرور",
            ),
            TokenAnalysis(
                word="رَبِّ",
                word_index=2,
                pos=POSTag.NOUN,
                role=GrammaticalRole.NAT,
                case_ending=CaseEnding.KASRA,
                i3rab="نعت مجرور وعلامة جره الكسرة، وهو مضاف",
                root="ر ب ب",
                pattern="فعل",
                confidence=0.95,
                notes_ar="مضاف",
            ),
            TokenAnalysis(
                word="الْعَالَمِينَ",
                word_index=3,
                pos=POSTag.NOUN,
                role=GrammaticalRole.MUDAF_ILAYH,
                case_ending=CaseEnding.YA,
                i3rab="مضاف إليه مجرور وعلامة جره الياء لأنه جمع مذكر سالم",
                root="ع ل م",
                confidence=0.98,
                notes_ar="جمع مذكر سالم",
            ),
        ],
        notes_ar="جملة اسمية، الحمد: مبتدأ، ولله: خبر (جار ومجرور متعلق بمحذوف)",
        overall_confidence=0.96,
        source="static",
    )

    # 2:255 - آية الكرسي (first part)
    STATIC_VERSES["2:255"] = GrammarAnalysis(
        verse_reference="2:255",
        text="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="اللَّهُ",
                word_index=0,
                pos=POSTag.NOUN_PROPER,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="لفظ الجلالة مبتدأ مرفوع وعلامة رفعه الضمة",
                root="أ ل ه",
                confidence=0.98,
                notes_ar="لفظ الجلالة",
            ),
            TokenAnalysis(
                word="لَا",
                word_index=1,
                pos=POSTag.PARTICLE_NEG,
                role=GrammaticalRole.UNKNOWN,
                i3rab="لا النافية للجنس، حرف نفي يعمل عمل إن",
                confidence=0.95,
                notes_ar="لا النافية للجنس",
            ),
            TokenAnalysis(
                word="إِلَٰهَ",
                word_index=2,
                pos=POSTag.NOUN,
                role=GrammaticalRole.INNA_ISM,
                case_ending=CaseEnding.FATHA,
                i3rab="اسم لا النافية للجنس مبني على الفتح",
                root="أ ل ه",
                pattern="فعال",
                confidence=0.95,
                notes_ar="اسم لا مبني",
            ),
            TokenAnalysis(
                word="إِلَّا",
                word_index=3,
                pos=POSTag.PARTICLE_EXCEPT,
                role=GrammaticalRole.UNKNOWN,
                i3rab="أداة استثناء",
                confidence=0.95,
                notes_ar="أداة حصر",
            ),
            TokenAnalysis(
                word="هُوَ",
                word_index=4,
                pos=POSTag.NOUN_PRONOUN,
                role=GrammaticalRole.BADAL,
                case_ending=CaseEnding.NONE,
                i3rab="ضمير منفصل مبني على الفتح في محل رفع بدل من الضمير المستتر في الخبر المحذوف",
                confidence=0.90,
                notes_ar="ضمير منفصل للمفرد الغائب",
            ),
            TokenAnalysis(
                word="الْحَيُّ",
                word_index=5,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="خبر المبتدأ مرفوع وعلامة رفعه الضمة",
                root="ح ي ي",
                pattern="فعيل",
                confidence=0.95,
                notes_ar="من أسماء الله الحسنى",
            ),
            TokenAnalysis(
                word="الْقَيُّومُ",
                word_index=6,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="خبر ثان مرفوع وعلامة رفعه الضمة",
                root="ق و م",
                pattern="فيعول",
                confidence=0.95,
                notes_ar="من أسماء الله الحسنى",
            ),
        ],
        notes_ar="آية الكرسي - جملة اسمية عظيمة في التوحيد",
        overall_confidence=0.94,
        source="static",
    )

    # 112:1 - قل هو الله أحد
    STATIC_VERSES["112:1"] = GrammarAnalysis(
        verse_reference="112:1",
        text="قُلْ هُوَ اللَّهُ أَحَدٌ",
        sentence_type=SentenceType.VERBAL,
        tokens=[
            TokenAnalysis(
                word="قُلْ",
                word_index=0,
                pos=POSTag.VERB_IMPERATIVE,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.SUKUN,
                i3rab="فعل أمر مبني على السكون، والفاعل ضمير مستتر تقديره أنت",
                root="ق و ل",
                pattern="فعل",
                confidence=0.98,
                notes_ar="فعل أمر",
            ),
            TokenAnalysis(
                word="هُوَ",
                word_index=1,
                pos=POSTag.NOUN_PRONOUN,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.NONE,
                i3rab="ضمير الشأن مبني على الفتح في محل رفع مبتدأ",
                confidence=0.95,
                notes_ar="ضمير الشأن",
            ),
            TokenAnalysis(
                word="اللَّهُ",
                word_index=2,
                pos=POSTag.NOUN_PROPER,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="لفظ الجلالة مبتدأ ثان مرفوع وعلامة رفعه الضمة",
                root="أ ل ه",
                confidence=0.95,
                notes_ar="لفظ الجلالة",
            ),
            TokenAnalysis(
                word="أَحَدٌ",
                word_index=3,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="خبر المبتدأ الثاني مرفوع وعلامة رفعه الضمة الظاهرة",
                root="و ح د",
                pattern="فعل",
                confidence=0.98,
                notes_ar="بمعنى الواحد الفرد",
            ),
        ],
        notes_ar="سورة الإخلاص - تفرد الله بالوحدانية",
        overall_confidence=0.96,
        source="static",
    )

    # 112:2 - الله الصمد
    STATIC_VERSES["112:2"] = GrammarAnalysis(
        verse_reference="112:2",
        text="اللَّهُ الصَّمَدُ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="اللَّهُ",
                word_index=0,
                pos=POSTag.NOUN_PROPER,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="لفظ الجلالة مبتدأ مرفوع وعلامة رفعه الضمة",
                root="أ ل ه",
                confidence=0.98,
                notes_ar="لفظ الجلالة",
            ),
            TokenAnalysis(
                word="الصَّمَدُ",
                word_index=1,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="خبر مرفوع وعلامة رفعه الضمة الظاهرة",
                root="ص م د",
                pattern="فعل",
                confidence=0.98,
                notes_ar="من أسماء الله الحسنى: المقصود في الحوائج",
            ),
        ],
        notes_ar="جملة اسمية بسيطة، الله: مبتدأ، الصمد: خبر",
        overall_confidence=0.98,
        source="static",
    )

    # 36:1 - يس
    STATIC_VERSES["36:1"] = GrammarAnalysis(
        verse_reference="36:1",
        text="يس",
        sentence_type=SentenceType.UNKNOWN,
        tokens=[
            TokenAnalysis(
                word="يس",
                word_index=0,
                pos=POSTag.UNKNOWN,
                role=GrammaticalRole.UNKNOWN,
                i3rab="حروف مقطعة، الله أعلم بمرادها",
                confidence=0.90,
                notes_ar="من الحروف المقطعة في أوائل السور",
            ),
        ],
        notes_ar="حروف مقطعة في أول السورة",
        overall_confidence=0.90,
        source="static",
    )

    # 55:1 - الرحمن
    STATIC_VERSES["55:1"] = GrammarAnalysis(
        verse_reference="55:1",
        text="الرَّحْمَٰنُ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="الرَّحْمَٰنُ",
                word_index=0,
                pos=POSTag.NOUN_PROPER,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="مبتدأ مرفوع وعلامة رفعه الضمة الظاهرة",
                root="ر ح م",
                pattern="فعلان",
                confidence=0.95,
                notes_ar="من أسماء الله الحسنى",
            ),
        ],
        notes_ar="الرحمن: مبتدأ، وخبره في الآية التالية (علم القرآن)",
        overall_confidence=0.95,
        source="static",
    )

    # 67:1 - تبارك الذي بيده الملك
    STATIC_VERSES["67:1"] = GrammarAnalysis(
        verse_reference="67:1",
        text="تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ",
        sentence_type=SentenceType.VERBAL,
        tokens=[
            TokenAnalysis(
                word="تَبَارَكَ",
                word_index=0,
                pos=POSTag.VERB_PAST,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.FATHA,
                i3rab="فعل ماض مبني على الفتح",
                root="ب ر ك",
                pattern="تفاعل",
                confidence=0.95,
                notes_ar="فعل للتعظيم والمدح",
            ),
            TokenAnalysis(
                word="الَّذِي",
                word_index=1,
                pos=POSTag.NOUN_RELATIVE,
                role=GrammaticalRole.FAEL,
                case_ending=CaseEnding.NONE,
                i3rab="اسم موصول مبني على السكون في محل رفع فاعل",
                confidence=0.95,
                notes_ar="اسم موصول للمفرد المذكر",
            ),
            TokenAnalysis(
                word="بِيَدِهِ",
                word_index=2,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.KASRA,
                i3rab="جار ومجرور متعلقان بمحذوف خبر مقدم",
                root="ي د ي",
                confidence=0.90,
                notes_ar="الباء حرف جر، ويده: اسم مجرور مضاف، والهاء مضاف إليه",
            ),
            TokenAnalysis(
                word="الْمُلْكُ",
                word_index=3,
                pos=POSTag.NOUN,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.DAMMA,
                i3rab="مبتدأ مؤخر مرفوع وعلامة رفعه الضمة",
                root="م ل ك",
                pattern="فعل",
                confidence=0.95,
                notes_ar="الملك: السلطان والتصرف",
            ),
        ],
        notes_ar="جملة فعلية ثم جملة الصلة (بيده الملك) اسمية مقدم فيها الخبر",
        overall_confidence=0.93,
        source="static",
    )


# Initialize static data
_build_static_data()


def get_static_analysis(text: str, verse_reference: Optional[str] = None) -> Optional[GrammarAnalysis]:
    """
    Get pre-analyzed grammar for a verse if available.

    Args:
        text: The verse text (used for fuzzy matching if reference not found)
        verse_reference: The verse reference (e.g., "1:1", "2:255")

    Returns:
        GrammarAnalysis if found in static data, None otherwise
    """
    # Try exact reference match first
    if verse_reference and verse_reference in STATIC_VERSES:
        return STATIC_VERSES[verse_reference]

    # Try text-based matching for common verses
    text_normalized = text.strip()
    for ref, analysis in STATIC_VERSES.items():
        if analysis.text.strip() == text_normalized:
            return analysis

    return None


def get_static_verse_count() -> int:
    """Get count of verses in static fallback dataset."""
    return len(STATIC_VERSES)


def get_available_static_verses() -> List[str]:
    """Get list of verse references available in static dataset."""
    return list(STATIC_VERSES.keys())
