"""
Quran Question Classifier — Pre-Generation Safety Gate

Classifies user questions BEFORE retrieval/generation so the system knows
whether to answer, refuse, clarify, or route to a specific module.

Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
           Prof. Dr. Abdulrahman Al-Shehri — Principle: AI must not issue fatwa.

Design principles:
  - Rule-based only — transparent, deterministic, testable, no LLM dependency.
  - Arabic and English patterns — bilingual Quranic platform.
  - Classification is pre-generation (defense layer 1).
  - QuranAnswerGuard remains active post-generation (defense layer 2).
  - No content is generated or modified here.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Intent constants
# ---------------------------------------------------------------------------

INTENT_FATWA_LIKE             = "fatwa_like"
INTENT_SCIENTIFIC_MIRACLE     = "scientific_miracle_claim"
INTENT_QIRAAT                 = "qiraat"
INTENT_MORPHOLOGY             = "morphology"
INTENT_IRAB                   = "irab"
INTENT_VOCABULARY             = "vocabulary_meaning"
INTENT_MUNASABAH              = "munasabah"
INTENT_SIMILARITY             = "similarity"
INTENT_STORY                  = "story"
INTENT_THEMATIC_TAFSIR        = "thematic_tafsir"
INTENT_TAFSIR_SUMMARY         = "tafsir_summary"
INTENT_GENERAL                = "general_question"
INTENT_NEEDS_CLARIFICATION    = "needs_clarification"
INTENT_UNSUPPORTED            = "unsupported"

# Route-to constants
ROUTE_RAG          = "rag"
ROUTE_SEARCH       = "search"
ROUTE_STORIES      = "stories"
ROUTE_SIMILARITY   = "similarity"
ROUTE_VOCABULARY   = "vocabulary"
ROUTE_IRAB         = "irab"
ROUTE_MORPHOLOGY   = "morphology"
ROUTE_REFUSAL      = "safe_refusal"
ROUTE_CLARIFICATION = "clarification"

# Risk levels
RISK_LOW    = "low"
RISK_MEDIUM = "medium"
RISK_HIGH   = "high"

# ---------------------------------------------------------------------------
# Bilingual safe-response messages
# ---------------------------------------------------------------------------

FATWA_REFUSAL_EN = (
    "I cannot issue a fatwa. I can only show documented information from "
    "available sources. Please consult qualified scholars for religious rulings."
)
FATWA_REFUSAL_AR = (
    "لا أستطيع إصدار فتوى. يمكنني فقط عرض معلومات موثقة من المصادر المتاحة، "
    "وينبغي الرجوع إلى أهل العلم في مسائل الفتوى."
)

SCIENTIFIC_CAUTION_EN = (
    "Connecting an ayah to scientific theories requires specialized scholarly "
    "and scientific review. This is presented as a contemporary reflection, "
    "not a definitive tafsir position."
)
SCIENTIFIC_CAUTION_AR = (
    "الربط بين الآية والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة. "
    "هذا الطرح تأمل معاصر وليس موقفًا تفسيريًا قطعيًا."
)

UNSUPPORTED_EN = "No verified source available for this answer."
UNSUPPORTED_AR = "لا يوجد مصدر موثوق متاح لهذه الإجابة."

CLARIFICATION_EN = (
    "Please specify the ayah or topic more clearly so I can search "
    "the verified sources."
)
CLARIFICATION_AR = (
    "يرجى تحديد الآية أو الموضوع بشكل أوضح حتى أستطيع البحث في "
    "المصادر الموثوقة."
)

# Module-not-available fallback (vocabulary / i'rab / morphology / qiraat)
MODULE_UNAVAILABLE_EN = (
    "This feature requires a verified source that is not yet available on "
    "this platform. The answer will be retrieved from general tafsir sources where possible."
)
MODULE_UNAVAILABLE_AR = (
    "هذه الميزة تحتاج إلى مصدر موثوق لم يتوفر بعد على هذه المنصة. "
    "سيتم البحث في مصادر التفسير العامة حيث أمكن."
)

# ---------------------------------------------------------------------------
# Classification result
# ---------------------------------------------------------------------------

@dataclass
class QuestionClassification:
    """
    Classification of a user question before retrieval/generation.

    Fields map directly to the Phase C schema defined in the task spec.
    """
    intent: str                        # One of INTENT_* constants
    language: str                      # "ar" | "en" | "mixed"
    risk_level: str                    # "low" | "medium" | "high"
    requires_source: bool              # Must have at least one verified source
    requires_scholar_review: bool      # Needs human scholarly review before approval
    allowed_to_generate: bool          # False = skip LLM entirely
    route_to: str                      # One of ROUTE_* constants
    warnings: List[str] = field(default_factory=list)  # Bilingual caution messages


# ---------------------------------------------------------------------------
# Keyword pattern sets
# ---------------------------------------------------------------------------

# 1. Fatwa-like — highest priority, hard block
_FATWA_AR = frozenset({
    "ما حكم", "هل يجوز", "هل يحل", "هل يحرم", "هل يباح",
    "أفتني", "فتوى", "فتاوى", "حلال أم حرام", "هل علي إثم",
    "حكم الشرع", "الحكم الشرعي", "هل يجوز لي", "ما حكم الشرع",
    "أريد فتوى", "هل هذا محرم", "هل هذا حلال",
})
_FATWA_EN = frozenset({
    "is it permissible", "is it haram", "is it halal", "give me a fatwa",
    "what is the ruling", "am i sinful", "is it forbidden", "is it allowed",
    "am i allowed", "religious ruling", "fatwa", "is this haram",
    "is this halal", "is this permissible", "can i do", "should i do",
    "is it a sin", "is it prohibited",
})

# 2. Scientific miracle claims
_SCIENTIFIC_AR = frozenset({
    "الإعجاز العلمي", "إعجاز علمي", "هل هذه الآية تثبت", "هل القرآن يثبت",
    "الانفجار الكبير", "نظرية علمية", "الطب الحديث", "الفيزياء", "الجيولوجيا",
    "الفلك", "علم الأحياء", "علم الأجنة", "توسع الكون", "الجبال أوتاد",
    "يثبت العلم", "أثبت العلم", "العلم يثبت", "علميًا ثبت", "دليل علمي",
})
_SCIENTIFIC_EN = frozenset({
    "scientific miracle", "does this verse prove", "does the quran prove",
    "big bang", "modern science", "physics", "geology", "biology",
    "embryology", "astronomy", "expanding universe", "mountains as pegs",
    "science proves", "science confirms", "scientifically proven",
    "scientific proof", "scientific evidence", "proven by science",
    "quran predicted", "quran mentions",
})

# 3. Qira'at (recitation variants)
_QIRAAT_AR = frozenset({
    "القراءات", "قراءة قرآنية", "قراءات متواترة", "قراءة شاذة",
    "قراء", "قراءة ورش", "قراءة حفص", "قراءة نافع", "روايات القراءة",
})
_QIRAAT_EN = frozenset({
    "qiraat", "qira'at", "recitation variant", "reading variant",
    "quranic recitation", "warsh", "hafs recitation", "nafi", "quranic reading",
})

# 4. Morphology / tasreef
_MORPHOLOGY_AR = frozenset({
    "تصريف", "الصرف", "الجذر", "الوزن الصرفي", "اشتقاق",
    "وزن الكلمة", "اشتقاق الكلمة",
})
_MORPHOLOGY_EN = frozenset({
    "morphology", "word root", "word pattern", "lemma", "tasreef",
    "root of the word", "root form", "derivation",
})

# 5. I'rab / grammatical analysis
_IRAB_AR = frozenset({
    "إعراب", "أعرب", "النحو", "محل الإعراب", "إعراب الآية",
    "إعراب الكلمة", "موقع الكلمة من الإعراب",
})
_IRAB_EN = frozenset({
    "i'rab", "irab", "parse this word", "grammatical analysis",
    "syntax", "grammatical parsing", "parse the verse",
})

# 6. Vocabulary / gharib al-Quran
_VOCAB_AR = frozenset({
    "معنى كلمة", "ما معنى كلمة", "غريب القرآن", "مفردة قرآنية",
    "معنى مفردة", "تعريف كلمة", "ما دلالة", "دلالة الكلمة",
})
_VOCAB_EN = frozenset({
    "meaning of the word", "vocabulary", "quranic word", "difficult word",
    "word meaning", "what does the word", "explain the word",
    "gharib", "gharib al-quran",
})

# 7. Munasabah / contextual relationships
_MUNASABAH_AR = frozenset({
    "المناسبة", "مناسبة الآيات", "العلاقة بين الآيات",
    "علاقة أول السورة بآخرها", "السياق القرآني", "ترابط الآيات",
    "ترابط السور", "مناسبة السور",
})
_MUNASABAH_EN = frozenset({
    "relationship between ayahs", "relationship between verses", "contextual relationship",
    "connection between verses", "beginning and ending of surah", "verse connection",
    "surah relation", "munasabah", "context of verses",
    # partial phrase: "relationship between" + anything Quran-related
    "relationship between the ayahs", "relationship between these ayahs",
    "relationship between these verses",
})

# 8. Verse similarity
_SIMILARITY_AR = frozenset({
    "صلة الآيات", "آيات مشابهة", "آيات مرتبطة", "آيات متشابهة",
    "الآيات المتعلقة", "آيات قريبة",
    # definite-article forms (with ال prefix)
    "مشابهة", "متشابهة", "مترابطة",
})
_SIMILARITY_EN = frozenset({
    "related ayahs", "similar verses", "verse similarity", "similar ayahs",
    "connected verses", "verses like this",
})

# 9. Story / Quranic narratives
_STORY_AR = frozenset({
    "قصة", "قصص القرآن", "أصحاب", "قوم", "نبي", "أنبياء",
    "حكاية", "رواية", "قصة سيدنا", "ذكر القرآن",
})
_STORY_EN = frozenset({
    "story of", "quran story", "people of", "companions of",
    "prophet story", "narrative of", "tale of", "story about prophet",
})

# 10. Thematic tafsir
_THEMATIC_AR = frozenset({
    "موضوع", "التفسير الموضوعي", "آيات عن", "كيف تناول القرآن",
    "ما قاله القرآن عن", "الآيات التي تتحدث عن", "آيات الصبر",
    "آيات الرحمة", "آيات التقوى",
    # Healing / guidance patterns
    "آيات للتخلص", "آيات لعلاج", "آيات لـ", "آيات عن الهم",
    "آيات عن الحزن", "آيات عن القلق", "آيات عن الخوف",
    "كيف أتخلص", "كيف أتغلب", "علاج الهم", "علاج الحزن",
    "للتخلص من", "للتغلب على", "بر الوالدين", "آيات عن الرزق",
    "دعاء الاستخارة", "آيات عن الصبر", "آيات عن التوكل",
    "آيات الشفاء", "آيات الراحة", "آيات الطمأنينة",
})
_THEMATIC_EN = frozenset({
    "theme", "thematic tafsir", "verses about", "what does the quran say about",
    "quran on the topic of", "all verses about", "quran teachings on",
    "verses for", "verses to", "verses on", "quran verses about",
    "verses relieving", "verses for anxiety", "verses for grief",
    "verses for healing", "quran on anxiety", "quran on grief",
    "quran on sadness", "quran on hope", "quran on patience",
    "verses for relief", "help with", "verses for parents",
})

# 11. Tafsir / verse meaning (broad)
_TAFSIR_AR = frozenset({
    "تفسير", "معنى الآية", "اشرح الآية", "ماذا تعني", "ما معنى",
    "فسر", "شرح", "تأويل", "مراد الآية",
})
_TAFSIR_EN = frozenset({
    "tafsir", "tafseer", "explain this ayah", "meaning of this verse",
    "what does this ayah mean", "explain verse", "interpret",
    "what does this verse mean", "explanation of", "exegesis",
})

# Clearly non-Quranic topics (for unsupported classification)
_UNSUPPORTED_TOPICS = frozenset({
    "weather forecast", "stock market", "football", "soccer", "recipe",
    "movie", "dating", "politics", "election", "cryptocurrency",
    "bitcoin", "programming", "code", "python script",
})

# Arabic script detector
_ARABIC_SCRIPT = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿ]+')


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class QuranQuestionClassifier:
    """
    Deterministic rule-based classifier for Quranic questions.

    Classification priority (highest to lowest):
      1. fatwa_like           — hard block, no generation
      2. scientific_miracle   — allowed with caution labels
      3. qiraat               — route to module (fallback to RAG + warning)
      4. morphology           — route to module (fallback to RAG + warning)
      5. irab                 — route to module (fallback to RAG + warning)
      6. vocabulary_meaning   — route to module (fallback to RAG + warning)
      7. munasabah            — route to RAG with needs_review flag
      8. similarity           — route to similarity module
      9. story                — route to stories module
     10. thematic_tafsir      — route to RAG (thematic retrieval)
     11. tafsir_summary       — route to RAG (standard)
     12. needs_clarification  — request clarification (no generation)
     13. unsupported          — safe refusal (non-Quranic topic)
     14. general_question     — route to RAG (default)
    """

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def classify(self, question: str) -> QuestionClassification:
        """
        Classify a user question.

        Args:
            question: Raw user input (Arabic, English, or mixed).

        Returns:
            QuestionClassification with routing and safety metadata.
        """
        q = question.strip()
        q_lower = q.lower()
        language = self._detect_language(q)

        # Priority-ordered checks
        if self._matches_any(q_lower, _FATWA_AR | _FATWA_EN):
            return QuestionClassification(
                intent=INTENT_FATWA_LIKE,
                language=language,
                risk_level=RISK_HIGH,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=False,
                route_to=ROUTE_REFUSAL,
                warnings=[FATWA_REFUSAL_EN, FATWA_REFUSAL_AR],
            )

        if self._matches_any(q_lower, _SCIENTIFIC_AR | _SCIENTIFIC_EN):
            return QuestionClassification(
                intent=INTENT_SCIENTIFIC_MIRACLE,
                language=language,
                risk_level=RISK_HIGH,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[SCIENTIFIC_CAUTION_EN, SCIENTIFIC_CAUTION_AR],
            )

        if self._matches_any(q_lower, _QIRAAT_AR | _QIRAAT_EN):
            return QuestionClassification(
                intent=INTENT_QIRAAT,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _MORPHOLOGY_AR | _MORPHOLOGY_EN):
            return QuestionClassification(
                intent=INTENT_MORPHOLOGY,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _IRAB_AR | _IRAB_EN):
            return QuestionClassification(
                intent=INTENT_IRAB,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _VOCAB_AR | _VOCAB_EN):
            return QuestionClassification(
                intent=INTENT_VOCABULARY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[MODULE_UNAVAILABLE_EN, MODULE_UNAVAILABLE_AR],
            )

        if self._matches_any(q_lower, _MUNASABAH_AR | _MUNASABAH_EN):
            return QuestionClassification(
                intent=INTENT_MUNASABAH,
                language=language,
                risk_level=RISK_MEDIUM,
                requires_source=True,
                requires_scholar_review=True,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        if self._matches_any(q_lower, _SIMILARITY_AR | _SIMILARITY_EN):
            return QuestionClassification(
                intent=INTENT_SIMILARITY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_SIMILARITY,
                warnings=[],
            )

        if self._matches_any(q_lower, _STORY_AR | _STORY_EN):
            return QuestionClassification(
                intent=INTENT_STORY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_STORIES,
                warnings=[],
            )

        if self._matches_any(q_lower, _THEMATIC_AR | _THEMATIC_EN):
            return QuestionClassification(
                intent=INTENT_THEMATIC_TAFSIR,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        if self._matches_any(q_lower, _TAFSIR_AR | _TAFSIR_EN):
            return QuestionClassification(
                intent=INTENT_TAFSIR_SUMMARY,
                language=language,
                risk_level=RISK_LOW,
                requires_source=True,
                requires_scholar_review=False,
                allowed_to_generate=True,
                route_to=ROUTE_RAG,
                warnings=[],
            )

        # Non-Quranic topic → unsupported
        if self._matches_any(q_lower, _UNSUPPORTED_TOPICS):
            return QuestionClassification(
                intent=INTENT_UNSUPPORTED,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=False,
                route_to=ROUTE_REFUSAL,
                warnings=[UNSUPPORTED_EN, UNSUPPORTED_AR],
            )

        # Very short queries that lack enough context
        if len(q.split()) < 3:
            return QuestionClassification(
                intent=INTENT_NEEDS_CLARIFICATION,
                language=language,
                risk_level=RISK_LOW,
                requires_source=False,
                requires_scholar_review=False,
                allowed_to_generate=False,
                route_to=ROUTE_CLARIFICATION,
                warnings=[CLARIFICATION_EN, CLARIFICATION_AR],
            )

        # Default: general question — send to RAG
        return QuestionClassification(
            intent=INTENT_GENERAL,
            language=language,
            risk_level=RISK_LOW,
            requires_source=True,
            requires_scholar_review=False,
            allowed_to_generate=True,
            route_to=ROUTE_RAG,
            warnings=[],
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _detect_language(self, text: str) -> str:
        has_arabic = bool(_ARABIC_SCRIPT.search(text))
        # Rough heuristic: if >30% chars are ASCII letters → likely English present
        ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
        has_english = ascii_letters > len(text) * 0.3
        if has_arabic and has_english:
            return "mixed"
        if has_arabic:
            return "ar"
        return "en"

    @staticmethod
    def _matches_any(text_lower: str, patterns: frozenset) -> bool:
        """Return True if any pattern appears as a substring of the lowercased text."""
        return any(p.lower() in text_lower for p in patterns)


# ---------------------------------------------------------------------------
# Helper: map classifier intent → QueryIntent (for backward-compatible pipeline)
# ---------------------------------------------------------------------------

def classifier_intent_to_query_intent(intent: str):
    """
    Map a fine-grained classifier intent to the legacy QueryIntent enum value
    used by RAG retrieval, expansion, and generation.

    Returns the string value (not the enum) to avoid import cycles.
    """
    _MAP = {
        INTENT_FATWA_LIKE:          "ruling",
        INTENT_SCIENTIFIC_MIRACLE:  "verse_meaning",
        INTENT_QIRAAT:              "linguistic",
        INTENT_MORPHOLOGY:          "linguistic",
        INTENT_IRAB:                "linguistic",
        INTENT_VOCABULARY:          "linguistic",
        INTENT_MUNASABAH:           "verse_meaning",
        INTENT_SIMILARITY:          "verse_meaning",
        INTENT_STORY:               "story_exploration",
        INTENT_THEMATIC_TAFSIR:     "theme_search",
        INTENT_TAFSIR_SUMMARY:      "verse_meaning",
        INTENT_GENERAL:             "verse_meaning",
        INTENT_NEEDS_CLARIFICATION: "unknown",
        INTENT_UNSUPPORTED:         "unknown",
    }
    return _MAP.get(intent, "verse_meaning")


# Module-level singleton
quran_question_classifier = QuranQuestionClassifier()
