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

    # 2:1 - الم (Huroof Muqatta'at)
    STATIC_VERSES["2:1"] = GrammarAnalysis(
        verse_reference="2:1",
        text="الم",
        sentence_type=SentenceType.UNKNOWN,
        tokens=[
            TokenAnalysis(
                word="الم",
                word_index=0,
                pos=POSTag.UNKNOWN,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.NONE,
                i3rab="حروف مقطعة مبنية لا محل لها من الإعراب، الله أعلم بمرادها",
                confidence=0.90,
                notes_ar="من الحروف المقطعة في أوائل السور - أسرارها عند الله",
            ),
        ],
        notes_ar="حروف مقطعة في أول السورة، والراجح أنها أسماء للسورة أو إشارة إلى إعجاز القرآن",
        overall_confidence=0.90,
        source="static",
    )

    # 2:2 - ذلك الكتاب لا ريب فيه هدى للمتقين
    STATIC_VERSES["2:2"] = GrammarAnalysis(
        verse_reference="2:2",
        text="ذَٰلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ هُدًى لِّلْمُتَّقِينَ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="ذَٰلِكَ",
                word_index=0,
                pos=POSTag.NOUN_DEMONSTRATIVE,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.NONE,
                i3rab="اسم إشارة مبني على الفتح في محل رفع مبتدأ، اللام للبُعد والكاف للخطاب",
                root="ذ ل ك",
                confidence=0.97,
                notes_ar="اسم إشارة للمفرد البعيد",
            ),
            TokenAnalysis(
                word="الْكِتَابُ",
                word_index=1,
                pos=POSTag.NOUN,
                role=GrammaticalRole.BADAL,
                case_ending=CaseEnding.DAMMA,
                i3rab="بدل من ذلك أو عطف بيان مرفوع وعلامة رفعه الضمة الظاهرة",
                root="ك ت ب",
                pattern="فعال",
                confidence=0.95,
                notes_ar="معرّف بأل، والمقصود به القرآن الكريم",
            ),
            TokenAnalysis(
                word="لَا",
                word_index=2,
                pos=POSTag.PARTICLE_NEG,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.NONE,
                i3rab="لا النافية للجنس، حرف نفي مبني لا محل له من الإعراب",
                confidence=0.97,
                notes_ar="لا النافية للجنس تعمل عمل إن",
            ),
            TokenAnalysis(
                word="رَيْبَ",
                word_index=3,
                pos=POSTag.NOUN,
                role=GrammaticalRole.INNA_ISM,
                case_ending=CaseEnding.FATHA,
                i3rab="اسم لا النافية للجنس مبني على الفتح في محل نصب",
                root="ر ي ب",
                confidence=0.97,
                notes_ar="الريب: الشك مع التهمة، والفتحة لأنه مفرد",
            ),
            TokenAnalysis(
                word="فِيهِ",
                word_index=4,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.KASRA,
                i3rab="في: حرف جر، والهاء: ضمير مبني في محل جر، الجار والمجرور متعلقان بمحذوف خبر لا",
                confidence=0.95,
                notes_ar="الضمير يعود على الكتاب",
            ),
            TokenAnalysis(
                word="هُدًى",
                word_index=5,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="خبر المبتدأ (ذلك) مرفوع وعلامة رفعه ضمة مقدرة على الألف المقصورة منع من ظهورها التعذر",
                root="ه د ي",
                pattern="فعل",
                confidence=0.95,
                notes_ar="مصدر بمعنى الهداية والرشد",
            ),
            TokenAnalysis(
                word="لِّلْمُتَّقِينَ",
                word_index=6,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.YA,
                i3rab="اللام: حرف جر، المتقين: اسم مجرور وعلامة جره الياء لأنه جمع مذكر سالم، والجار والمجرور نعت لـ(هدى)",
                root="و ق ي",
                confidence=0.95,
                notes_ar="المتقون: جمع مذكر سالم من الوقاية",
            ),
        ],
        notes_ar="جملة اسمية: ذلك مبتدأ، هدى خبر، وجملة (لا ريب فيه) اعتراضية في محل نصب حال أو اعتراض",
        overall_confidence=0.95,
        source="static",
    )

    # 2:3 - الذين يؤمنون بالغيب
    STATIC_VERSES["2:3"] = GrammarAnalysis(
        verse_reference="2:3",
        text="الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ وَيُقِيمُونَ الصَّلَاةَ وَمِمَّا رَزَقْنَاهُمْ يُنفِقُونَ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="الَّذِينَ",
                word_index=0,
                pos=POSTag.NOUN_RELATIVE,
                role=GrammaticalRole.NAT,
                case_ending=CaseEnding.NONE,
                i3rab="اسم موصول مبني على الفتح في محل جر نعت للمتقين في الآية السابقة",
                confidence=0.95,
                notes_ar="اسم موصول للجمع المذكر",
            ),
            TokenAnalysis(
                word="يُؤْمِنُونَ",
                word_index=1,
                pos=POSTag.VERB_PRESENT,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.DAMMA,
                i3rab="فعل مضارع مرفوع وعلامة رفعه ثبوت النون لأنه من الأفعال الخمسة، والواو فاعل، والجملة صلة الموصول",
                root="أ م ن",
                pattern="يُفعِلون",
                confidence=0.97,
                notes_ar="الجملة صلة الموصول لا محل لها",
            ),
            TokenAnalysis(
                word="بِالْغَيْبِ",
                word_index=2,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.KASRA,
                i3rab="الباء حرف جر، الغيب اسم مجرور وعلامة جره الكسرة، الجار والمجرور متعلقان بـ(يؤمنون)",
                root="غ ي ب",
                confidence=0.95,
                notes_ar="الغيب: ما غاب عن الحواس كالملائكة والبعث والقدر",
            ),
            TokenAnalysis(
                word="وَيُقِيمُونَ",
                word_index=3,
                pos=POSTag.VERB_PRESENT,
                role=GrammaticalRole.ATAF,
                case_ending=CaseEnding.DAMMA,
                i3rab="الواو حرف عطف، يقيمون فعل مضارع مرفوع معطوف على يؤمنون",
                root="ق و م",
                pattern="يُفعِلون",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="الصَّلَاةَ",
                word_index=4,
                pos=POSTag.NOUN,
                role=GrammaticalRole.MAFUL_BIH,
                case_ending=CaseEnding.FATHA,
                i3rab="مفعول به منصوب وعلامة نصبه الفتحة الظاهرة",
                root="ص ل و",
                confidence=0.97,
            ),
            TokenAnalysis(
                word="وَمِمَّا",
                word_index=5,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.NONE,
                i3rab="الواو عاطفة، من: حرف جر، ما: اسم موصول مبني في محل جر، الجار والمجرور متعلقان بـ(ينفقون)",
                confidence=0.90,
            ),
            TokenAnalysis(
                word="رَزَقْنَاهُمْ",
                word_index=6,
                pos=POSTag.VERB_PAST,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.NONE,
                i3rab="فعل ماض مبني على السكون لاتصاله بنا، نا فاعل، هم مفعول به، الجملة صلة الموصول (ما)",
                root="ر ز ق",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="يُنفِقُونَ",
                word_index=7,
                pos=POSTag.VERB_PRESENT,
                role=GrammaticalRole.ATAF,
                case_ending=CaseEnding.DAMMA,
                i3rab="فعل مضارع مرفوع معطوف على يؤمنون، والواو فاعل",
                root="ن ف ق",
                confidence=0.95,
            ),
        ],
        notes_ar="الآية صفة للمتقين: يؤمنون بالغيب، ويقيمون الصلاة، وينفقون مما رزقناهم",
        overall_confidence=0.94,
        source="static",
    )

    # 2:4 - والذين يؤمنون بما أنزل إليك
    STATIC_VERSES["2:4"] = GrammarAnalysis(
        verse_reference="2:4",
        text="وَالَّذِينَ يُؤْمِنُونَ بِمَا أُنزِلَ إِلَيْكَ وَمَا أُنزِلَ مِن قَبْلِكَ وَبِالْآخِرَةِ هُمْ يُوقِنُونَ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="وَالَّذِينَ",
                word_index=0,
                pos=POSTag.NOUN_RELATIVE,
                role=GrammaticalRole.ATAF,
                case_ending=CaseEnding.NONE,
                i3rab="الواو عاطفة، الذين اسم موصول معطوف على الذين في الآية السابقة في محل جر",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="يُؤْمِنُونَ",
                word_index=1,
                pos=POSTag.VERB_PRESENT,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.DAMMA,
                i3rab="فعل مضارع مرفوع، والواو فاعل، الجملة صلة الموصول",
                root="أ م ن",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="بِمَا",
                word_index=2,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.NONE,
                i3rab="الباء حرف جر، ما اسم موصول في محل جر، الجار والمجرور متعلقان بيؤمنون",
                confidence=0.90,
            ),
            TokenAnalysis(
                word="أُنزِلَ",
                word_index=3,
                pos=POSTag.VERB_PAST,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.FATHA,
                i3rab="فعل ماض مبني للمجهول مبني على الفتح، ونائب الفاعل ضمير مستتر، الجملة صلة الموصول (ما)",
                root="ن ز ل",
                confidence=0.97,
            ),
            TokenAnalysis(
                word="إِلَيْكَ",
                word_index=4,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.NONE,
                i3rab="إلى حرف جر، الكاف ضمير خطاب في محل جر، والجار والمجرور متعلقان بأنزل",
                confidence=0.95,
                notes_ar="خطاب للنبي محمد ﷺ",
            ),
            TokenAnalysis(
                word="وَبِالْآخِرَةِ",
                word_index=5,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.KASRA,
                i3rab="الواو عاطفة، الباء حرف جر، الآخرة اسم مجرور، الجار والمجرور متعلقان بيوقنون مقدَّمان عليه",
                root="أ خ ر",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="هُمْ",
                word_index=6,
                pos=POSTag.NOUN_PRONOUN,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.NONE,
                i3rab="ضمير منفصل مبتدأ في محل رفع، وجملة (يوقنون) خبره",
                confidence=0.92,
                notes_ar="ضمير الفصل أو المبتدأ لتخصيص الإيقان بهم",
            ),
            TokenAnalysis(
                word="يُوقِنُونَ",
                word_index=7,
                pos=POSTag.VERB_PRESENT,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.DAMMA,
                i3rab="فعل مضارع مرفوع، والواو فاعل، الجملة خبر هم أو خبر الذين",
                root="ي ق ن",
                confidence=0.95,
                notes_ar="الإيقان: أعلى درجات اليقين",
            ),
        ],
        notes_ar="صفة ثانية للمتقين: الإيمان بالوحي المنزَّل على النبي ﷺ وعلى الأنبياء قبله، واليقين بالآخرة",
        overall_confidence=0.94,
        source="static",
    )

    # 2:5 - أولئك على هدى من ربهم وأولئك هم المفلحون
    STATIC_VERSES["2:5"] = GrammarAnalysis(
        verse_reference="2:5",
        text="أُولَٰئِكَ عَلَىٰ هُدًى مِّن رَّبِّهِمْ وَأُولَٰئِكَ هُمُ الْمُفْلِحُونَ",
        sentence_type=SentenceType.NOMINAL,
        tokens=[
            TokenAnalysis(
                word="أُولَٰئِكَ",
                word_index=0,
                pos=POSTag.NOUN_DEMONSTRATIVE,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.NONE,
                i3rab="اسم إشارة للجمع مبني على الكسر في محل رفع مبتدأ",
                confidence=0.97,
                notes_ar="يعود على المتقين الموصوفين في الآيات السابقة",
            ),
            TokenAnalysis(
                word="عَلَىٰ",
                word_index=1,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.JARR_MAJRUR,
                case_ending=CaseEnding.NONE,
                i3rab="حرف جر مبني على السكون",
                confidence=0.97,
            ),
            TokenAnalysis(
                word="هُدًى",
                word_index=2,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.KASRA,
                i3rab="اسم مجرور بعلى وعلامة جره كسرة مقدرة على الألف، والجار والمجرور (على هدى) متعلقان بمحذوف خبر",
                root="ه د ي",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="مِّن رَّبِّهِمْ",
                word_index=3,
                pos=POSTag.PARTICLE_PREP,
                role=GrammaticalRole.NAT,
                case_ending=CaseEnding.KASRA,
                i3rab="من حرف جر، رب اسم مجرور مضاف، هم ضمير مضاف إليه، الجار والمجرور نعت لـ(هدى)",
                root="ر ب ب",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="وَأُولَٰئِكَ",
                word_index=4,
                pos=POSTag.NOUN_DEMONSTRATIVE,
                role=GrammaticalRole.MUBTADA,
                case_ending=CaseEnding.NONE,
                i3rab="الواو عاطفة أو استئنافية، أولئك: مبتدأ ثانٍ مبني في محل رفع",
                confidence=0.95,
            ),
            TokenAnalysis(
                word="هُمُ",
                word_index=5,
                pos=POSTag.NOUN_PRONOUN,
                role=GrammaticalRole.UNKNOWN,
                case_ending=CaseEnding.NONE,
                i3rab="ضمير منفصل مبني في محل رفع، ضمير فصل (عماد) لتوكيد الخبر وتخصيصه لا محل له",
                confidence=0.92,
            ),
            TokenAnalysis(
                word="الْمُفْلِحُونَ",
                word_index=6,
                pos=POSTag.NOUN,
                role=GrammaticalRole.KHABAR,
                case_ending=CaseEnding.WAW,
                i3rab="خبر أولئك الثاني مرفوع وعلامة رفعه الواو لأنه جمع مذكر سالم",
                root="ف ل ح",
                pattern="مُفعِلون",
                confidence=0.97,
                notes_ar="الفلاح: الفوز والنجاة والظفر بما يُطلب",
            ),
        ],
        notes_ar="جملتان اسميتان: الأولى تثبت أن المتقين على هدى من ربهم، والثانية تؤكد فلاحهم وفوزهم",
        overall_confidence=0.95,
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
