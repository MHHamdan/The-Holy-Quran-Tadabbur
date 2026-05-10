"""
Spiritual Guidance & Emotional Support API — Phase T / T2.

Public endpoints:
  POST /api/v1/therapy/ask          — classify emotion + return guidance cards
  POST /api/v1/therapy/chat         — QuranGPT conversational mode via RAG
  POST /api/v1/therapy/insights     — user emotional journey stats
  GET  /api/v1/therapy/themes       — list all healing themes
  GET  /api/v1/therapy/theme/{name} — explore a specific healing theme
  POST /api/v1/therapy/reflect      — save a personal reflection entry
  GET  /api/v1/therapy/emotions     — list all emotion categories

Rate-limited to 20 requests/min per IP (public, no auth required).

IMPORTANT DISCLAIMER — included in every response:
  This feature provides Quranic-grounded spiritual reflection.
  It is NOT a substitute for professional mental health care.
  If you are in crisis, please contact a qualified professional.
"""
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.rate_limit import therapy_rate_limit
from app.models.therapy import EmotionCategory, EMOTION_LABELS, TherapySession
from app.services.spiritual_guidance_service import (
    HEALING_THEMES,
    build_guidance_cards,
    classify_emotion,
    get_recommended_themes,
    get_theme_cards,
)
from app.services.tone_adapter import get_tone_profile, tone_directive as build_tone_directive


def _classify_with_confidence(message: str) -> tuple[str, float]:
    """
    Classify emotion and return (emotion, confidence).

    Calls the NLI classifier directly for English to capture the confidence
    score that classify_emotion() discards.  For Arabic or when the NLI
    classifier is disabled/unavailable, confidence is returned as 0.0 (keyword
    fallback signal).
    """
    from app.core.config import get_settings
    from app.services.emotion_classifier import get_classifier, is_arabic_dominant

    settings = get_settings()

    if settings.emotion_classifier_enabled and not is_arabic_dominant(message):
        clf = get_classifier(
            model_name=settings.emotion_model_name,
            confidence_threshold=settings.emotion_confidence_threshold,
        )
        emotion, confidence = clf.classify(message)
        if emotion:
            return emotion, confidence

    # Keyword path — classify_emotion handles Arabic routing internally too
    return classify_emotion(message), 0.0

router = APIRouter()

_DISCLAIMER_EN = (
    "This feature offers Quranic-grounded spiritual reflection to support your emotional "
    "well-being. It is not a substitute for professional mental health care. "
    "If you are experiencing a mental health crisis, please seek qualified professional help."
)
_DISCLAIMER_AR = (
    "تقدم هذه الميزة تأملات روحية مستندة إلى القرآن لدعم صحتك العاطفية. "
    "وهي ليست بديلاً عن الرعاية الصحية النفسية المتخصصة. "
    "إذا كنت تمر بأزمة نفسية، يُرجى طلب مساعدة متخصصة مؤهّلة."
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=1500, description="User's emotional message")
    language: str = Field("en", description="'en' or 'ar'")
    emotion_override: Optional[str] = Field(
        None,
        description="Manually specify emotion instead of auto-classifying",
    )
    # Phase T3 — personalization context
    previous_emotion: Optional[str] = Field(
        None, description="Last emotion from prior session (for personalised empathy)"
    )
    previous_theme: Optional[str] = Field(
        None, description="Last healing theme explored (for personalised follow-ups)"
    )
    reinforcement_index: int = Field(
        0, ge=0, le=9, description="Index into reinforcement bank (0–9) for message variety"
    )

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("en", "ar"):
            raise ValueError("language must be 'en' or 'ar'")
        return v

    @field_validator("emotion_override", "previous_emotion")
    @classmethod
    def valid_emotion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in [e.value for e in EmotionCategory]:
            raise ValueError(f"Unknown emotion: {v}")
        return v

    @field_validator("previous_theme")
    @classmethod
    def valid_theme(cls, v: Optional[str]) -> Optional[str]:
        from app.services.spiritual_guidance_service import HEALING_THEMES
        if v is not None and v not in HEALING_THEMES:
            raise ValueError(f"Unknown theme: {v}")
        return v


class GuidanceCard(BaseModel):
    reference: str
    surah: int
    ayah_start: int
    ayah_end: int
    surah_name_ar: str
    surah_name_en: str
    text_uthmani: str
    text_imlaei: str
    theme: str
    theme_ar: str
    theme_en: str
    lesson_en: str
    lesson_ar: str
    reflection_en: str
    reflection_ar: str
    dua_en: str
    dua_ar: str
    prophet_story: Optional[str] = None


class AskResponse(BaseModel):
    ok: bool = True
    session_id: str
    emotion: str
    emotion_label_en: str
    emotion_label_ar: str
    empathy_en: str
    empathy_ar: str
    reinforcement_en: str = ""
    reinforcement_ar: str = ""
    cards: List[GuidanceCard]
    recommended_themes: List[str]
    follow_up_prompts_en: List[str]
    follow_up_prompts_ar: List[str]
    # Phase T3
    suggested_theme: Optional[str] = None
    suggested_theme_reason_en: Optional[str] = None
    suggested_theme_reason_ar: Optional[str] = None
    personalization_note_en: Optional[str] = None
    personalization_note_ar: Optional[str] = None
    # Phase T4 — NLI classifier confidence (0.0 = keyword fallback was used)
    emotion_confidence: float = 0.0
    # Phase T5-C — adaptive tone profile label
    tone_profile: str = "mild"
    disclaimer_en: str = _DISCLAIMER_EN
    disclaimer_ar: str = _DISCLAIMER_AR


# ---------------------------------------------------------------------------
# Chat schemas (Phase T2)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=1500)
    language: str = Field("en", description="'en' or 'ar'")
    emotion_override: Optional[str] = Field(None)
    session_id: Optional[str] = Field(None, description="Conversation session ID for continuity")
    conversation_context: Optional[List[Dict[str, str]]] = Field(
        None, description="Prior turns [{role, content}]"
    )

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("en", "ar"):
            raise ValueError("language must be 'en' or 'ar'")
        return v

    @field_validator("emotion_override")
    @classmethod
    def valid_emotion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in [e.value for e in EmotionCategory]:
            raise ValueError(f"Unknown emotion: {v}")
        return v


class ChatCitation(BaseModel):
    source_id: str
    source_name: str
    verse_reference: str
    excerpt: str


class ChatResponse(BaseModel):
    ok: bool = True
    session_id: str
    emotion: str
    emotion_label_en: str
    emotion_label_ar: str
    answer: str
    answer_language: str
    citations: List[ChatCitation] = []
    related_verses: List[str] = []
    follow_up_suggestions: List[str] = []
    # Fallback cards when RAG unavailable
    fallback_cards: List[GuidanceCard] = []
    used_rag: bool = False
    # Phase T4
    emotion_confidence: float = 0.0
    # Phase T5-C
    tone_profile: str = "mild"
    disclaimer_en: str = _DISCLAIMER_EN
    disclaimer_ar: str = _DISCLAIMER_AR


# ---------------------------------------------------------------------------
# Insights schemas (Phase T2)
# ---------------------------------------------------------------------------

class InsightsRequest(BaseModel):
    session_ids: List[str] = Field(..., min_length=1, max_length=200)
    language: str = Field("en")

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("en", "ar"):
            raise ValueError("language must be 'en' or 'ar'")
        return v


class EmotionCount(BaseModel):
    emotion: str
    label_en: str
    label_ar: str
    count: int


class EmotionPoint(BaseModel):
    """One session entry in the ordered emotion timeline."""
    session_id: str
    emotion: str
    label_en: str
    label_ar: str
    theme: Optional[str] = None
    timestamp: str   # ISO-8601 datetime string


class InsightsResponse(BaseModel):
    ok: bool = True
    total_sessions: int
    emotion_distribution: List[EmotionCount]
    most_visited_theme: Optional[str] = None
    streak_days: int = 0
    top_emotion: Optional[str] = None
    top_emotion_label_en: Optional[str] = None
    top_emotion_label_ar: Optional[str] = None
    # Phase T3 — growth suggestions
    suggested_next_theme: Optional[str] = None
    growth_prompt_en: Optional[str] = None
    growth_prompt_ar: Optional[str] = None
    # Phase T5-B — emotional growth map
    emotion_timeline: List[EmotionPoint] = []
    trend: str = "stable"   # "improving" | "stable" | "challenging"


class ThemeInfo(BaseModel):
    key: str
    ar: str
    en: str
    desc_en: str
    desc_ar: str
    icon: str
    color: str


class ThemesResponse(BaseModel):
    ok: bool = True
    themes: List[ThemeInfo]


class ThemeDetailResponse(BaseModel):
    ok: bool = True
    theme: ThemeInfo
    cards: List[GuidanceCard]
    disclaimer_en: str = _DISCLAIMER_EN
    disclaimer_ar: str = _DISCLAIMER_AR


class ReflectRequest(BaseModel):
    session_id: str = Field(..., min_length=10, max_length=100)
    reflection: str = Field(..., min_length=1, max_length=3000)


class ReflectResponse(BaseModel):
    ok: bool = True
    message_en: str = "Your reflection has been saved."
    message_ar: str = "تم حفظ تأملك."


# ---------------------------------------------------------------------------
# Positive reinforcement messages per emotion (Phase T2)
# ---------------------------------------------------------------------------

_REINFORCEMENT: Dict[str, Dict[str, str]] = {
    EmotionCategory.ANXIETY: {
        "en": "Taking this step to seek reflection is itself an act of courage. Your heart is moving toward peace.",
        "ar": "إن إقدامك على طلب التأمل هو في حد ذاته شجاعة. قلبك يتجه نحو السكينة.",
    },
    EmotionCategory.SADNESS: {
        "en": "Reaching out in sadness is a sign of wisdom. The Quran has accompanied hearts in grief for centuries.",
        "ar": "التواصل في الحزن علامة حكمة. القرآن رافق القلوب الحزينة عبر قرون.",
    },
    EmotionCategory.GRIEF: {
        "en": "Your willingness to sit with grief and seek light within it is deeply honoured. Healing begins here.",
        "ar": "استعدادك لمواجهة الحزن وابتغاء النور فيه أمر يستحق الإجلال. الشفاء يبدأ هنا.",
    },
    EmotionCategory.FEAR: {
        "en": "Seeking guidance in fear is the beginning of trust. You are not alone in this.",
        "ar": "طلب الهداية في الخوف هو بداية التوكل. لست وحدك في هذا.",
    },
    EmotionCategory.LONELINESS: {
        "en": "The very act of reaching out shows your heart still seeks connection — and that is a beautiful thing.",
        "ar": "مجرد تواصلك يدل على أن قلبك لا يزال يبحث عن الارتباط — وهذا أمر جميل.",
    },
    EmotionCategory.HOPELESSNESS: {
        "en": "Hope can be very small and still be real. The fact that you are here means hope has not left you.",
        "ar": "يمكن أن يكون الأمل صغيراً جداً وما زال حقيقياً. حضورك هنا يعني أن الأمل لم يتركك.",
    },
    EmotionCategory.ANGER: {
        "en": "Bringing your anger to the Quran rather than letting it consume you is a profound act of self-care.",
        "ar": "إحضار غضبك إلى القرآن بدلاً من السماح له بابتلاعك هو عمل عميق من أعمال الرعاية الذاتية.",
    },
    EmotionCategory.STRESS: {
        "en": "Pausing to seek reflection amid pressure is exactly what the Quran invites you to do. Well done.",
        "ar": "التوقف لطلب التأمل وسط الضغط هو بالضبط ما يدعوك إليه القرآن. أحسنت.",
    },
    EmotionCategory.GUILT: {
        "en": "Guilt that leads you back to God is already the beginning of forgiveness. You are on the right path.",
        "ar": "الشعور بالذنب الذي يعيدك إلى الله هو بداية المغفرة. أنت على الطريق الصحيح.",
    },
    EmotionCategory.DOUBT: {
        "en": "The Quran was revealed for sincere seekers like you. Your questions are welcome here.",
        "ar": "نُزّل القرآن للباحثين الصادقين من أمثالك. تساؤلاتك مرحب بها هنا.",
    },
    EmotionCategory.GRATITUDE: {
        "en": "Gratitude shared multiplies. Your thankful heart is a gift — to yourself and to the world.",
        "ar": "الامتنان المُشارَك يتضاعف. قلبك الشاكر هبة — لك وللعالم.",
    },
    EmotionCategory.GENERAL: {
        "en": "Whatever brought you here, you are welcome. The Quran speaks to every human moment.",
        "ar": "مهما أحضرك إلى هنا، فأنت موضع ترحيب. القرآن يخاطب كل لحظة إنسانية.",
    },
}


# ---------------------------------------------------------------------------
# Empathy opening lines per emotion
# ---------------------------------------------------------------------------

_EMPATHY: dict[str, dict[str, str]] = {
    EmotionCategory.ANXIETY: {
        "en": "Feeling anxious is deeply human, and the Quran speaks directly to hearts that are troubled. Let's find some grounding together.",
        "ar": "القلق إنساني عميق، والقرآن يخاطب القلوب المضطربة مباشرةً. لنجد بعض الاطمئنان معاً.",
    },
    EmotionCategory.SADNESS: {
        "en": "I hear the sadness in your words. The Quran does not dismiss grief — it holds it gently and points toward light.",
        "ar": "أسمع الحزن في كلماتك. لا يُهمل القرآن الحزن — بل يحتضنه برفق ويشير نحو النور.",
    },
    EmotionCategory.GRIEF: {
        "en": "Grief is love with nowhere to go. The Quran honors that love and offers a place for it to rest.",
        "ar": "الحزن محبة لا مكان لها. يُكرّم القرآن تلك المحبة ويُقدّم لها مكاناً للراحة.",
    },
    EmotionCategory.FEAR: {
        "en": "Fear is a natural response, and your feelings are valid. The Quran offers an anchor that no storm can move.",
        "ar": "الخوف استجابة طبيعية ومشاعرك مشروعة. يُقدّم القرآن مرساة لا تُحرّكها أي عاصفة.",
    },
    EmotionCategory.LONELINESS: {
        "en": "You may feel alone right now — but the Quran holds a profound promise: Allah is nearer to you than you can imagine.",
        "ar": "ربما تشعر بالوحدة الآن — لكن القرآن يحمل وعداً عميقاً: الله أقرب إليك مما تتخيل.",
    },
    EmotionCategory.HOPELESSNESS: {
        "en": "When hope feels impossible, the Quran speaks the most clearly. It was revealed specifically for moments like this one.",
        "ar": "حين يبدو الأمل مستحيلاً، يتكلم القرآن بأوضح ما يكون. نُزّل خصيصاً للحظات كهذه.",
    },
    EmotionCategory.ANGER: {
        "en": "Anger carries information. The Quran doesn't ask you to suppress it — it offers a path to channel it wisely.",
        "ar": "الغضب يحمل معلومات. لا يطلب القرآن كبته — بل يُقدّم طريقاً لتوجيهه بحكمة.",
    },
    EmotionCategory.STRESS: {
        "en": "You are carrying a heavy load. The Quran reminds us that ease is woven into the fabric of hardship itself.",
        "ar": "أنت تحمل عبئاً ثقيلاً. يُذكّرنا القرآن بأن اليسر منسوج في نسيج المشقة ذاتها.",
    },
    EmotionCategory.GUILT: {
        "en": "The very fact that you feel guilt means you have a conscience. The Quran sees that conscience and responds with extraordinary mercy.",
        "ar": "حقيقة شعورك بالذنب تعني أن لديك ضميراً. يرى القرآن ذلك الضمير ويستجيب له برحمة استثنائية.",
    },
    EmotionCategory.DOUBT: {
        "en": "Questions and doubt are the companions of sincere seekers. The Quran invites reflection — it is not afraid of your questions.",
        "ar": "الأسئلة والشك رفيقا الباحثين بصدق. يدعو القرآن إلى التأمل — وليس خائفاً من تساؤلاتك.",
    },
    EmotionCategory.GRATITUDE: {
        "en": "Gratitude is a spiritual practice that expands what is good. The Quran nurtures that expansion beautifully.",
        "ar": "الشكر ممارسة روحية تُوسّع ما هو جيد. يُنمّي القرآن هذا التوسع بجمال.",
    },
    EmotionCategory.GENERAL: {
        "en": "Whatever you are carrying, the Quran is a book that speaks to the full range of human experience. Let's explore it together.",
        "ar": "مهما كنت تحمل، القرآن كتاب يخاطب النطاق الكامل للتجربة الإنسانية. لنستكشفه معاً.",
    },
}

# Phase T3 — expanded reinforcement bank (list of alternatives per emotion, index-selectable)
_REINFORCEMENT_BANK: Dict[str, List[Dict[str, str]]] = {
    EmotionCategory.ANXIETY: [
        {
            "en": "Taking this step to seek reflection is itself an act of courage. Your heart is moving toward peace.",
            "ar": "إن إقدامك على طلب التأمل هو في حد ذاته شجاعة. قلبك يتجه نحو السكينة.",
        },
        {
            "en": "Take solace in knowing that with every challenge, Allah's mercy is near. You are not carrying this alone.",
            "ar": "اطمئن فإن مع كل تحدٍّ رحمة الله قريبة. أنت لا تحمل هذا وحدك.",
        },
        {
            "en": "Peace is a destination your heart already knows. The Quran is the path.",
            "ar": "السلام وجهة يعرفها قلبك بالفعل. والقرآن هو الطريق.",
        },
    ],
    EmotionCategory.SADNESS: [
        {
            "en": "Reaching out in sadness is a sign of wisdom. The Quran has accompanied hearts in grief for centuries.",
            "ar": "التواصل في الحزن علامة حكمة. القرآن رافق القلوب الحزينة عبر قرون.",
        },
        {
            "en": "Your tears are not weakness — they are sincerity. Allah hears every sob and responds with light.",
            "ar": "دموعك ليست ضعفاً — بل هي صدق. الله يسمع كل نشيج ويستجيب بالنور.",
        },
        {
            "en": "Every wave of sadness carries within it the seed of something deeper and more beautiful.",
            "ar": "كل موجة حزن تحمل في طيّاتها بذرة شيء أعمق وأجمل.",
        },
    ],
    EmotionCategory.GRIEF: [
        {
            "en": "Your willingness to sit with grief and seek light within it is deeply honoured. Healing begins here.",
            "ar": "استعدادك لمواجهة الحزن وابتغاء النور فيه أمر يستحق الإجلال. الشفاء يبدأ هنا.",
        },
        {
            "en": "The Quran reminds us that every hardship comes with ease. Keep your heart strong — relief is written for you.",
            "ar": "يُذكّرنا القرآن بأن مع كل عسر يسراً. أبقِ قلبك قوياً — فالفرج مكتوب لك.",
        },
        {
            "en": "Those who grieve deeply also love deeply. That love is a gift — and Allah knows it.",
            "ar": "من يحزن بعمق يحب بعمق. وذلك الحب هبة — والله يعلمه.",
        },
    ],
    EmotionCategory.FEAR: [
        {
            "en": "Seeking guidance in fear is the beginning of trust. You are not alone in this.",
            "ar": "طلب الهداية في الخوف هو بداية التوكل. لست وحدك في هذا.",
        },
        {
            "en": "Courage is not the absence of fear — it is choosing to turn toward God despite it.",
            "ar": "الشجاعة ليست غياب الخوف — بل الاختيار بالتوجه إلى الله رغمه.",
        },
        {
            "en": "Allah is greater than any fear you carry. Let that truth settle gently into your heart.",
            "ar": "الله أكبر من أي خوف تحمله. دع هذه الحقيقة تستقر برفق في قلبك.",
        },
    ],
    EmotionCategory.LONELINESS: [
        {
            "en": "The very act of reaching out shows your heart still seeks connection — and that is a beautiful thing.",
            "ar": "مجرد تواصلك يدل على أن قلبك لا يزال يبحث عن الارتباط — وهذا أمر جميل.",
        },
        {
            "en": "You are never truly alone when the Quran is with you. Every verse is a companion.",
            "ar": "أنت لست وحيداً حقاً حين يكون القرآن معك. كل آية رفيقة.",
        },
        {
            "en": "Allah is closer to you than your own jugular vein. That closeness is real, even when it is hard to feel.",
            "ar": "الله أقرب إليك من حبل الوريد. هذا القرب حقيقي، حتى حين يصعب الإحساس به.",
        },
    ],
    EmotionCategory.HOPELESSNESS: [
        {
            "en": "Hope can be very small and still be real. The fact that you are here means hope has not left you.",
            "ar": "يمكن أن يكون الأمل صغيراً جداً وما زال حقيقياً. حضورك هنا يعني أن الأمل لم يتركك.",
        },
        {
            "en": "Even the smallest candle defeats complete darkness. Your reaching out today is that candle.",
            "ar": "حتى أصغر شمعة تهزم الظلام التام. تواصلك اليوم هو تلك الشمعة.",
        },
        {
            "en": "Do not despair of the mercy of Allah. It is wider than any darkness you have known.",
            "ar": "لا تقنط من رحمة الله. وهي أوسع من أي ظلام مررت به.",
        },
    ],
    EmotionCategory.ANGER: [
        {
            "en": "Bringing your anger to the Quran rather than letting it consume you is a profound act of self-care.",
            "ar": "إحضار غضبك إلى القرآن بدلاً من السماح له بابتلاعك هو عمل عميق من أعمال الرعاية الذاتية.",
        },
        {
            "en": "You have shown real strength by pausing and seeking wisdom. That is not easy, and it matters.",
            "ar": "لقد أظهرت قوة حقيقية بالتوقف وطلب الحكمة. هذا ليس سهلاً، وهو مهم.",
        },
        {
            "en": "The prophets felt anger too — and they brought it to God. You are in good company.",
            "ar": "شعر الأنبياء أيضاً بالغضب — وأحضروه إلى الله. أنت في صحبة طيبة.",
        },
    ],
    EmotionCategory.STRESS: [
        {
            "en": "Pausing to seek reflection amid pressure is exactly what the Quran invites you to do. Well done.",
            "ar": "التوقف لطلب التأمل وسط الضغط هو بالضبط ما يدعوك إليه القرآن. أحسنت.",
        },
        {
            "en": "You have shown great resilience. Trust that your patience will lead to ease.",
            "ar": "لقد أظهرت مرونة عظيمة. ثق أن صبرك سيقود إلى الراحة.",
        },
        {
            "en": "With every hardship there is ease — not after it, but within it. The Quran promises this.",
            "ar": "مع كل عسر يسر — لا بعده بل معه. القرآن يعد بذلك.",
        },
    ],
    EmotionCategory.GUILT: [
        {
            "en": "Guilt that leads you back to God is already the beginning of forgiveness. You are on the right path.",
            "ar": "الشعور بالذنب الذي يعيدك إلى الله هو بداية المغفرة. أنت على الطريق الصحيح.",
        },
        {
            "en": "No one is beyond the mercy of Allah. Not you, not anyone. That is the Quran's most radical promise.",
            "ar": "لا أحد خارج رحمة الله. لا أنت ولا أي أحد. هذا هو أكثر وعود القرآن جذرية.",
        },
        {
            "en": "Sincerity in seeking forgiveness is itself a form of worship. Allah accepts the sincere heart.",
            "ar": "الإخلاص في طلب المغفرة هو نفسه نوع من العبادة. الله يقبل القلب المخلص.",
        },
    ],
    EmotionCategory.DOUBT: [
        {
            "en": "The Quran was revealed for sincere seekers like you. Your questions are welcome here.",
            "ar": "نُزّل القرآن للباحثين الصادقين من أمثالك. تساؤلاتك مرحب بها هنا.",
        },
        {
            "en": "Doubt is not the opposite of faith — it is often its companion. The honest heart keeps asking.",
            "ar": "الشك ليس نقيض الإيمان — بل هو كثيراً رفيقه. القلب الصادق يواصل السؤال.",
        },
        {
            "en": "Ibrahim (AS) asked hard questions, and was called 'Khalilullah'. Your searching matters.",
            "ar": "سأل إبراهيم عليه السلام أسئلة صعبة، وسُمّي خليل الله. بحثك مهم.",
        },
    ],
    EmotionCategory.GRATITUDE: [
        {
            "en": "Gratitude shared multiplies. Your thankful heart is a gift — to yourself and to the world.",
            "ar": "الامتنان المُشارَك يتضاعف. قلبك الشاكر هبة — لك وللعالم.",
        },
        {
            "en": "When you remember Allah's blessings, you invite more of them. Keep that grateful heart open.",
            "ar": "حين تتذكر نعم الله تدعو المزيد منها. أبقِ ذلك القلب الشاكر منفتحاً.",
        },
        {
            "en": "Gratitude is a light that makes everything it touches brighter. Thank you for bringing it here.",
            "ar": "الامتنان نور يجعل كل ما يلمسه أشد إضاءة. شكراً لإحضاره إلى هنا.",
        },
    ],
    EmotionCategory.GENERAL: [
        {
            "en": "Whatever brought you here, you are welcome. The Quran speaks to every human moment.",
            "ar": "مهما أحضرك إلى هنا، فأنت موضع ترحيب. القرآن يخاطب كل لحظة إنسانية.",
        },
        {
            "en": "The act of seeking is itself beautiful. The Quran meets every seeker where they are.",
            "ar": "فعل البحث في حد ذاته جميل. القرآن يلتقي كل باحث حيث هو.",
        },
        {
            "en": "Your heart brought you here for a reason. Trust that impulse — it is already guiding you well.",
            "ar": "قلبك أحضرك إلى هنا لسبب. ثق بذلك الدافع — فهو يرشدك بالفعل.",
        },
    ],
}

# Phase T3 — suggested next theme per emotion
_EMOTION_SUGGESTED_THEME: Dict[str, str] = {
    EmotionCategory.ANXIETY:      "trust",
    EmotionCategory.SADNESS:      "hope",
    EmotionCategory.GRIEF:        "patience",
    EmotionCategory.FEAR:         "trust",
    EmotionCategory.LONELINESS:   "mercy",
    EmotionCategory.HOPELESSNESS: "hope",
    EmotionCategory.ANGER:        "forgiveness",
    EmotionCategory.STRESS:       "strength",
    EmotionCategory.GUILT:        "forgiveness",
    EmotionCategory.DOUBT:        "healing",
    EmotionCategory.GRATITUDE:    "gratitude",
    EmotionCategory.GENERAL:      "mercy",
}

_THEME_SUGGESTION_REASON: Dict[str, Dict[str, str]] = {
    "trust":       {"en": "Exploring tawakkul (trust in Allah) often brings peace to an anxious or fearful heart.", "ar": "استكشاف التوكل كثيراً ما يُضفي السكينة على القلب القلق أو الخائف."},
    "hope":        {"en": "The theme of hope (raja') is one of the Quran's most powerful medicines for sadness.", "ar": "موضوع الرجاء هو أحد أقوى أدوية القرآن للحزن واليأس."},
    "patience":    {"en": "Sabr (patience) has a special station in the Quran — promised unlimited reward.", "ar": "للصبر مقام خاص في القرآن — فله أجر بغير حساب."},
    "mercy":       {"en": "The Quran opens with mercy and is saturated with it — a good anchor for a lonely heart.", "ar": "يفتتح القرآن بالرحمة ويمتلئ بها — مرساة جيدة لقلب وحيد."},
    "forgiveness": {"en": "Exploring divine forgiveness can transform anger and guilt into relief and freedom.", "ar": "استكشاف المغفرة الإلهية يمكن أن يحوّل الغضب والذنب إلى ارتياح وتحرر."},
    "strength":    {"en": "The Quran speaks of strength as a spiritual gift given to those who endure.", "ar": "يتحدث القرآن عن القوة بوصفها هبة روحية تُمنح لمن يصبر."},
    "healing":     {"en": "The Quran describes itself as 'a healing for what is in the chests'. Let it work.", "ar": "يصف القرآن نفسه بأنه 'شفاء لما في الصدور'. دعه يعمل."},
    "gratitude":   {"en": "Shukr (gratitude) amplifies blessings and lifts the spirit in any emotional state.", "ar": "الشكر يضاعف النعم ويرفع الروح في أي حالة عاطفية."},
}

# Phase T3 — personalization callback phrases (when previous_emotion matches current)
_PERSONALIZATION_CALLBACK: Dict[str, Dict[str, str]] = {
    EmotionCategory.ANXIETY:      {"en": "Last time you sought guidance for anxiety — I'm glad you're back. Let's go deeper today.", "ar": "في المرة الأخيرة طلبت التوجيه للقلق — يسعدني عودتك. لنتعمق أكثر اليوم."},
    EmotionCategory.SADNESS:      {"en": "You've shared sadness with us before. Each return is a step toward healing.", "ar": "شاركتنا الحزن من قبل. كل عودة خطوة نحو الشفاء."},
    EmotionCategory.GRIEF:        {"en": "Grief takes its own time. You're still here, still seeking — that takes real courage.", "ar": "للحزن وقته الخاص. ما زلت هنا تبحث — وهذا يتطلب شجاعة حقيقية."},
    EmotionCategory.FEAR:         {"en": "Fear brought you back, and that's okay. Together we will find more Quranic anchors.", "ar": "الخوف أعادك، وهذا مقبول. سنجد معاً مزيداً من مراسي القرآن."},
    EmotionCategory.LONELINESS:   {"en": "You came back — that means the connection you found last time meant something.", "ar": "عدت — وهذا يعني أن الارتباط الذي وجدته في المرة الأخيرة كان ذا معنى."},
    EmotionCategory.HOPELESSNESS: {"en": "You returned — that is hope in action. Let's nurture it together.", "ar": "عدت — وهذا هو الأمل في العمل. دعنا نرعاه معاً."},
    EmotionCategory.ANGER:        {"en": "Bringing anger back to this space again shows wisdom. You're channelling it well.", "ar": "إعادة الغضب إلى هذه المساحة مجدداً يُظهر الحكمة. أنت توجّهه بشكل جيد."},
    EmotionCategory.STRESS:       {"en": "You've been under pressure for a while. I'm glad you keep returning for grounding.", "ar": "مررت بضغط مستمر. يسعدني أنك تواصل العودة للتثبّت."},
    EmotionCategory.GUILT:        {"en": "Returning after feeling guilt shows a heart that genuinely wants to grow.", "ar": "العودة بعد الشعور بالذنب تُظهر قلباً يريد حقاً أن يتطور."},
    EmotionCategory.DOUBT:        {"en": "Your questions brought you back. That persistent curiosity is a form of faith.", "ar": "أسئلتك أعادتك. ذلك الفضول المستمر هو نوع من الإيمان."},
    EmotionCategory.GRATITUDE:    {"en": "You came back with a grateful heart. That is a beautiful way to continue.", "ar": "عدت بقلب شاكر. هذه طريقة جميلة للمواصلة."},
    EmotionCategory.GENERAL:      {"en": "Welcome back. Each visit deepens the connection between your heart and the Quran.", "ar": "مرحباً بعودتك. كل زيارة تعمّق الصلة بين قلبك والقرآن."},
}

# Phase T3 — growth prompts for insights dashboard, keyed by top emotion
_GROWTH_PROMPTS: Dict[str, Dict[str, str]] = {
    "anxiety":      {"en": "You've been working through anxiety — consider exploring the 'Trust' theme to build deeper tawakkul.", "ar": "كنت تعمل على القلق — فكّر في استكشاف موضوع 'التوكل' لبناء توكل أعمق."},
    "sadness":      {"en": "Sadness has been your companion lately. Exploring 'Hope' can introduce a beautiful counter-melody.", "ar": "رافقك الحزن مؤخراً. استكشاف 'الرجاء' يمكن أن يُقدّم لحناً مضاداً جميلاً."},
    "grief":        {"en": "Grief is a long journey. Exploring 'Patience' may offer new resources for the road ahead.", "ar": "الحزن رحلة طويلة. استكشاف 'الصبر' قد يُقدّم موارد جديدة للطريق أمامك."},
    "fear":         {"en": "Fear has been present in your journey. The 'Trust' theme holds Quranic anchors for this.", "ar": "كان الخوف حاضراً في رحلتك. موضوع 'التوكل' يحمل مراسي قرآنية لهذا."},
    "loneliness":   {"en": "Loneliness can soften when Mercy surrounds it. Try exploring the 'Mercy' theme.", "ar": "الوحدة يمكن أن تلين حين تُحيط بها الرحمة. حاول استكشاف موضوع 'الرحمة'."},
    "hopelessness": {"en": "Hope is not lost — it is often hidden. The 'Hope' theme can help you find it.", "ar": "الأمل لم يُفقد — بل هو مخبّأ في الغالب. موضوع 'الرجاء' يمكن أن يساعدك."},
    "anger":        {"en": "Anger energy can be transformed. Exploring 'Forgiveness' — giving and receiving — may be liberating.", "ar": "طاقة الغضب يمكن تحويلها. استكشاف 'المغفرة' — إعطاءً وقبولاً — قد يكون محرراً."},
    "stress":       {"en": "You have been carrying a heavy load. Exploring 'Strength' can remind you of resources you have.", "ar": "كنت تحمل حملاً ثقيلاً. استكشاف 'القوة' يمكن أن يذكّرك بالموارد التي تمتلكها."},
    "guilt":        {"en": "After working with guilt, exploring 'Forgiveness' can open a door to a lighter self.", "ar": "بعد التعامل مع الذنب، يمكن لاستكشاف 'المغفرة' أن يفتح باباً لذات أخف."},
    "doubt":        {"en": "Questions are healthy. Exploring 'Healing' can help integrate doubt into a richer faith.", "ar": "الأسئلة صحية. يمكن لاستكشاف 'الشفاء' مساعدتك على دمج الشك في إيمان أغنى."},
    "gratitude":    {"en": "Your gratitude practice is growing. Deepen it through the full 'Gratitude' theme.", "ar": "ممارسة شكرك تنمو. عمّقها من خلال موضوع 'الشكر' بالكامل."},
    "general":      {"en": "You are exploring broadly. Try focusing on 'Mercy' this week — it connects all themes.", "ar": "أنت تستكشف بشكل واسع. جرّب التركيز على 'الرحمة' هذا الأسبوع."},
}


def _pick_reinforcement(emotion: str, index: int) -> Dict[str, str]:
    bank = _REINFORCEMENT_BANK.get(emotion, _REINFORCEMENT_BANK[EmotionCategory.GENERAL])
    return bank[index % len(bank)]


_FOLLOW_UPS: dict[str, dict[str, list[str]]] = {
    EmotionCategory.ANXIETY: {
        "en": [
            "Would you like to explore verses on trust in Allah (tawakkul)?",
            "Would you like a gentle reflection practice for tonight?",
            "Shall we look at the story of Prophet Ibrahim for courage in uncertainty?",
        ],
        "ar": [
            "هل تودّ استكشاف الآيات المتعلقة بالتوكل على الله؟",
            "هل تريد ممارسة تأمل لطيفة لهذه الليلة؟",
            "هل نتناول قصة النبي إبراهيم للشجاعة في مواجهة الغموض؟",
        ],
    },
    EmotionCategory.SADNESS: {
        "en": [
            "Would you like to explore the theme of hope (raja') in the Quran?",
            "Shall we read about Prophet Yaqub, who wept deeply yet never lost hope?",
            "Would you like verses that speak specifically about Allah's nearness?",
        ],
        "ar": [
            "هل تودّ استكشاف موضوع الرجاء في القرآن؟",
            "هل نقرأ عن النبي يعقوب الذي بكى بعمق ولم يفقد الأمل قط؟",
            "هل تريد آيات تتحدث تحديداً عن قرب الله؟",
        ],
    },
    EmotionCategory.GRIEF: {
        "en": [
            "Would you like to explore the story of Prophet Yaqub and Yusuf?",
            "Shall we look at Quranic verses on patience (sabr) in loss?",
            "Would you like a reflection on what it means to 'return to Allah'?",
        ],
        "ar": [
            "هل تودّ استكشاف قصة النبيين يعقوب ويوسف؟",
            "هل نستعرض الآيات القرآنية عن الصبر في الفقد؟",
            "هل تريد تأملاً حول معنى 'الرجوع إلى الله'؟",
        ],
    },
    EmotionCategory.FEAR: {
        "en": [
            "Would you like to explore verses on trust in Allah (tawakkul) as an antidote to fear?",
            "Shall we look at how the Prophet Musa faced fear — and what Allah said to him?",
            "Would you like a breathing-and-dhikr practice to calm fear in the moment?",
        ],
        "ar": [
            "هل تودّ استكشاف الآيات عن التوكل على الله كعلاج للخوف؟",
            "هل نتناول كيف واجه النبي موسى الخوف وما قاله الله له؟",
            "هل تريد ممارسة تنفس وذكر لتهدئة الخوف في اللحظة؟",
        ],
    },
    EmotionCategory.LONELINESS: {
        "en": [
            "Would you like verses on Allah being your closest companion?",
            "Shall we explore the story of Prophet Yunus (AS) in the darkness — and how he was answered?",
            "Would you like a reflection practice on divine presence?",
        ],
        "ar": [
            "هل تريد آيات عن كون الله رفيقك الأقرب؟",
            "هل نستكشف قصة النبي يونس في الظلمات وكيف استُجيب له؟",
            "هل تريد ممارسة تأمل عن الحضور الإلهي؟",
        ],
    },
    EmotionCategory.ANGER: {
        "en": [
            "Would you like Quranic guidance on controlling anger (kadhm al-ghaydh)?",
            "Shall we explore the virtue of forgiveness and how it frees the heart?",
            "Would you like verses on how the prophets transformed anger into wisdom?",
        ],
        "ar": [
            "هل تريد توجيهاً قرآنياً حول كظم الغيظ؟",
            "هل نستكشف فضيلة العفو وكيف يحرر القلب؟",
            "هل تريد آيات حول كيف حوّل الأنبياء الغضب إلى حكمة؟",
        ],
    },
    EmotionCategory.STRESS: {
        "en": [
            "Would you like verses specifically on ease after hardship (Surah Ash-Sharh)?",
            "Shall we look at how Prophet Muhammad ﷺ found stillness amid overwhelming pressure?",
            "Would you like a short dhikr routine to practise when stress peaks?",
        ],
        "ar": [
            "هل تريد آيات تحديداً عن اليسر بعد العسر (سورة الشرح)؟",
            "هل نتناول كيف وجد النبي محمد ﷺ السكينة وسط الضغط الشديد؟",
            "هل تريد روتيناً قصيراً من الذكر لممارسته عند ذروة التوتر؟",
        ],
    },
    EmotionCategory.GUILT: {
        "en": [
            "Would you like to read about Allah's infinite capacity for forgiveness?",
            "Shall we look at the story of Prophet Yunus and how he was forgiven completely?",
            "Would you like verses on tawbah (repentance) as a path to inner peace?",
        ],
        "ar": [
            "هل تريد أن تقرأ عن قدرة الله اللانهائية على المغفرة؟",
            "هل نتناول قصة النبي يونس وكيف غُفر له تماماً؟",
            "هل تريد آيات عن التوبة طريقاً إلى السلام الداخلي؟",
        ],
    },
    EmotionCategory.DOUBT: {
        "en": [
            "Would you like to explore Quranic verses that invite reflection and questioning?",
            "Shall we look at how the Quran addresses doubts about faith directly?",
            "Would you like to read about companions who asked hard questions — and were honoured for it?",
        ],
        "ar": [
            "هل تودّ استكشاف الآيات القرآنية التي تدعو إلى التأمل والتساؤل؟",
            "هل نتناول كيف يعالج القرآن الشكوك في الإيمان مباشرةً؟",
            "هل تريد أن تقرأ عن صحابة طرحوا أسئلة صعبة وكانوا موضع تكريم؟",
        ],
    },
    EmotionCategory.GRATITUDE: {
        "en": [
            "Would you like verses on how shukr (gratitude) multiplies blessings?",
            "Shall we explore the story of Prophet Sulayman and how he expressed gratitude for his gifts?",
            "Would you like a short daily gratitude practice rooted in Quranic language?",
        ],
        "ar": [
            "هل تريد آيات عن كيف يضاعف الشكر النعم؟",
            "هل نستكشف قصة النبي سليمان وكيف أعرب عن شكره لمواهبه؟",
            "هل تريد ممارسة يومية قصيرة للشكر متجذّرة في لغة القرآن؟",
        ],
    },
    EmotionCategory.HOPELESSNESS: {
        "en": [
            "Would you like to explore more verses on divine mercy?",
            "Shall we look at moments in the Quran when hope was restored?",
            "Would you like a simple daily practice to keep hope alive?",
        ],
        "ar": [
            "هل تودّ استكشاف المزيد من الآيات عن الرحمة الإلهية؟",
            "هل نتناول لحظات في القرآن حين عاد الأمل؟",
            "هل تريد ممارسة يومية بسيطة للإبقاء على الأمل؟",
        ],
    },
    EmotionCategory.GENERAL: {
        "en": [
            "Would you like to explore a healing theme in depth?",
            "Would you like to tell me more about what you are feeling?",
            "Shall we look at a specific Quranic story for guidance?",
        ],
        "ar": [
            "هل تودّ استكشاف موضوع شفائي بعمق؟",
            "هل تريد أن تخبرني المزيد عمّا تشعر به؟",
            "هل نستعرض قصة قرآنية محددة للتوجيه؟",
        ],
    },
}


def _follow_ups_for(emotion: str) -> dict[str, list[str]]:
    return _FOLLOW_UPS.get(emotion, _FOLLOW_UPS[EmotionCategory.GENERAL])


# ---------------------------------------------------------------------------
# Phase T5-B — growth map helpers
# ---------------------------------------------------------------------------

# Wellbeing score per emotion (higher = more at peace / positive)
_EMOTION_SCORE: Dict[str, float] = {
    "hopelessness": 0.0,
    "grief":        1.0,
    "fear":         1.5,
    "anger":        2.0,
    "guilt":        2.0,
    "loneliness":   2.0,
    "sadness":      2.0,
    "stress":       2.5,
    "anxiety":      2.5,
    "doubt":        3.0,
    "general":      3.5,
    "gratitude":    5.0,
}


def _compute_trend(timeline: List[EmotionPoint]) -> str:
    """
    Compare the last 3 sessions against the 3 before them.
    Returns 'improving', 'stable', or 'challenging'.
    """
    if len(timeline) < 4:
        return "stable"
    scores = [_EMOTION_SCORE.get(ep.emotion, 3.0) for ep in timeline]
    recent = scores[-3:]
    prior = scores[-6:-3] if len(scores) >= 6 else scores[:-3]
    if not prior:
        return "stable"
    avg_recent = sum(recent) / len(recent)
    avg_prior = sum(prior) / len(prior)
    if avg_recent > avg_prior + 0.4:
        return "improving"
    if avg_recent < avg_prior - 0.4:
        return "challenging"
    return "stable"


def _compute_streak(session_dates: list) -> int:
    """Count consecutive days (ending at today or yesterday) with at least one session."""
    from datetime import date, timedelta
    if not session_dates:
        return 0
    unique = sorted(set(session_dates), reverse=True)
    today = date.today()
    if unique[0] < today - timedelta(days=1):
        return 0
    streak = 1
    for i in range(1, len(unique)):
        if unique[i] == unique[i - 1] - timedelta(days=1):
            streak += 1
        else:
            break
    return streak


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask your heart — receive Quranic spiritual guidance",
    dependencies=[Depends(therapy_rate_limit)],
)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_async_session),
) -> AskResponse:
    """
    Classify the user's emotional state from their message and return
    personalised Quranic guidance cards with verses, lessons, reflections,
    and du'a suggestions.
    """
    if body.emotion_override:
        emotion, emotion_confidence = body.emotion_override, 1.0
    else:
        emotion, emotion_confidence = _classify_with_confidence(body.message)

    tone = get_tone_profile(emotion, emotion_confidence)
    cards_data = await build_guidance_cards(emotion, db, max_cards=3)

    labels = EMOTION_LABELS.get(emotion, {"en": emotion, "ar": emotion})
    empathy = _EMPATHY.get(emotion, _EMPATHY[EmotionCategory.GENERAL])
    reinforcement = _pick_reinforcement(emotion, body.reinforcement_index)
    follow_up = _follow_ups_for(emotion)

    # Phase T3 — personalization note when returning with the same emotion
    personalization_note_en: Optional[str] = None
    personalization_note_ar: Optional[str] = None
    if body.previous_emotion and body.previous_emotion == emotion:
        callback = _PERSONALIZATION_CALLBACK.get(emotion, _PERSONALIZATION_CALLBACK[EmotionCategory.GENERAL])
        personalization_note_en = callback["en"]
        personalization_note_ar = callback["ar"]

    # Phase T3 — suggested theme based on current emotion
    suggested_theme = _EMOTION_SUGGESTED_THEME.get(emotion)
    suggested_theme_reason_en: Optional[str] = None
    suggested_theme_reason_ar: Optional[str] = None
    if suggested_theme:
        reason = _THEME_SUGGESTION_REASON.get(suggested_theme, {})
        suggested_theme_reason_en = reason.get("en")
        suggested_theme_reason_ar = reason.get("ar")

    session_id = str(uuid.uuid4())
    verses_shown = json.dumps([c["reference"] for c in cards_data])

    session = TherapySession(
        session_id=session_id,
        emotion=emotion,
        theme=cards_data[0]["theme"] if cards_data else None,
        user_message=body.message[:500],
        verses_shown=verses_shown,
        language=body.language,
    )
    db.add(session)
    await db.commit()

    cards = [GuidanceCard(**c) for c in cards_data]

    return AskResponse(
        session_id=session_id,
        emotion=emotion,
        emotion_label_en=labels["en"],
        emotion_label_ar=labels["ar"],
        empathy_en=empathy["en"],
        empathy_ar=empathy["ar"],
        reinforcement_en=reinforcement["en"],
        reinforcement_ar=reinforcement["ar"],
        cards=cards,
        recommended_themes=get_recommended_themes(emotion),
        follow_up_prompts_en=follow_up["en"],
        follow_up_prompts_ar=follow_up["ar"],
        suggested_theme=suggested_theme,
        suggested_theme_reason_en=suggested_theme_reason_en,
        suggested_theme_reason_ar=suggested_theme_reason_ar,
        personalization_note_en=personalization_note_en,
        personalization_note_ar=personalization_note_ar,
        emotion_confidence=emotion_confidence,
        tone_profile=tone.label,
    )


@router.get(
    "/themes",
    response_model=ThemesResponse,
    summary="List all healing themes",
)
async def list_themes() -> ThemesResponse:
    """Return the catalogue of healing themes (Mercy, Patience, Hope, …)."""
    themes = [
        ThemeInfo(
            key=key,
            ar=meta["ar"],
            en=meta["en"],
            desc_en=meta["desc_en"],
            desc_ar=meta["desc_ar"],
            icon=meta["icon"],
            color=meta["color"],
        )
        for key, meta in HEALING_THEMES.items()
    ]
    return ThemesResponse(themes=themes)


@router.get(
    "/theme/{theme_name}",
    response_model=ThemeDetailResponse,
    summary="Explore a specific healing theme",
    dependencies=[Depends(therapy_rate_limit)],
)
async def explore_theme(
    theme_name: str = Path(..., description="Theme key, e.g. 'patience', 'mercy'"),
    db: AsyncSession = Depends(get_async_session),
) -> ThemeDetailResponse:
    """
    Return Quranic guidance cards for a specific healing theme.
    Useful for thematic exploration independent of a user's current emotion.
    """
    if theme_name not in HEALING_THEMES:
        raise HTTPException(
            status_code=404,
            detail=f"Theme '{theme_name}' not found. Available themes: {list(HEALING_THEMES.keys())}",
        )

    meta = HEALING_THEMES[theme_name]
    cards_data = await get_theme_cards(theme_name, db, max_cards=4)
    cards = [GuidanceCard(**c) for c in cards_data]

    return ThemeDetailResponse(
        theme=ThemeInfo(
            key=theme_name,
            ar=meta["ar"],
            en=meta["en"],
            desc_en=meta["desc_en"],
            desc_ar=meta["desc_ar"],
            icon=meta["icon"],
            color=meta["color"],
        ),
        cards=cards,
    )


@router.post(
    "/reflect",
    response_model=ReflectResponse,
    summary="Save a personal reflection to a therapy session",
    dependencies=[Depends(therapy_rate_limit)],
)
async def save_reflection(
    body: ReflectRequest,
    db: AsyncSession = Depends(get_async_session),
) -> ReflectResponse:
    """
    Attach a personal reflection note to an existing therapy session.
    Creates a lightweight journaling trail for the user.
    """
    from sqlalchemy import select as sa_select

    result = await db.execute(
        sa_select(TherapySession).where(TherapySession.session_id == body.session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session.reflection_logged = body.reflection[:3000]
    await db.commit()

    return ReflectResponse()


@router.get(
    "/emotions",
    summary="List all supported emotion categories",
)
async def list_emotions() -> dict:
    """Return all emotion categories with bilingual labels."""
    return {
        "ok": True,
        "emotions": [
            {
                "key": cat.value,
                "label_en": EMOTION_LABELS[cat]["en"],
                "label_ar": EMOTION_LABELS[cat]["ar"],
            }
            for cat in EmotionCategory
        ],
    }


# ---------------------------------------------------------------------------
# Phase T2: QuranGPT Chat mode
# ---------------------------------------------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="QuranGPT — tafsir-grounded emotional support conversation",
    dependencies=[Depends(therapy_rate_limit)],
)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
) -> ChatResponse:
    """
    Emotion-aware conversational endpoint.  Builds a spiritually grounded
    question from the user's message, runs it through the RAG pipeline, and
    returns a tafsir-backed answer.  Falls back to pre-curated guidance cards
    when the RAG pipeline / LLM is not configured.
    """
    from app.rag.pipeline import RAGPipeline
    from app.core.config import settings

    if body.emotion_override:
        emotion, emotion_confidence = body.emotion_override, 1.0
    else:
        emotion, emotion_confidence = _classify_with_confidence(body.message)

    tone = get_tone_profile(emotion, emotion_confidence)
    directive = build_tone_directive(emotion, emotion_confidence, body.language)

    labels = EMOTION_LABELS.get(emotion, {"en": emotion, "ar": emotion})
    session_id = body.session_id or str(uuid.uuid4())

    # Compose a Quran-focused spiritual question from the raw user message
    emotion_label = labels[body.language] if body.language in ("en", "ar") else labels["en"]
    if body.language == "ar":
        rag_question = (
            f"أشعر بـ{emotion_label}. "
            f"{body.message[:300]} "
            "ما الذي يقوله القرآن الكريم لمن يشعر بهذه المشاعر؟ "
            "اذكر الآيات والتفسير المناسب."
        )
    else:
        rag_question = (
            f"I am feeling {emotion_label}. {body.message[:300]} "
            "What does the Quran say to someone experiencing these feelings? "
            "Please include relevant verses and scholarly tafsir."
        )

    llm_available = False
    if settings.llm_provider == "claude" and settings.anthropic_api_key:
        llm_available = True
    elif settings.llm_provider == "ollama":
        import httpx as _httpx
        try:
            async with _httpx.AsyncClient(timeout=3.0) as _hc:
                _resp = await _hc.get(f"{settings.ollama_base_url}/api/tags")
                llm_available = _resp.status_code == 200
        except Exception:
            llm_available = False

    if llm_available:
        try:
            pipeline = RAGPipeline(db)
            result = await pipeline.query(
                question=rag_question,
                language=body.language,
                include_scholarly_debate=False,
                preferred_sources=[],
                max_sources=3,
                session_id=session_id,
                conversation_context=body.conversation_context,
                tone_directive=directive,
            )

            citations = [
                ChatCitation(
                    source_id=c.source_id,
                    source_name=c.source_name,
                    verse_reference=c.verse_reference,
                    excerpt=c.excerpt[:400],
                )
                for c in (result.citations or [])[:4]
            ]
            related_verses = [v.verse_reference for v in (result.related_verses or [])]
            follow_ups = list(result.follow_up_suggestions or [])[:3]

            # Record the session so it shows up in insights
            ts = TherapySession(
                session_id=session_id,
                emotion=emotion,
                theme=None,
                user_message=body.message[:500],
                verses_shown=json.dumps(related_verses[:5]),
                language=body.language,
            )
            db.add(ts)
            await db.commit()

            return ChatResponse(
                session_id=session_id,
                emotion=emotion,
                emotion_label_en=labels["en"],
                emotion_label_ar=labels["ar"],
                answer=result.answer,
                answer_language=result.answer_language or body.language,
                citations=citations,
                related_verses=related_verses,
                follow_up_suggestions=follow_ups,
                used_rag=True,
                emotion_confidence=emotion_confidence,
                tone_profile=tone.label,
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("RAG pipeline failed in /therapy/chat — falling back: %s", exc)

    # ---- Graceful fallback: pre-curated guidance cards ----
    cards_data = await build_guidance_cards(emotion, db, max_cards=3)
    empathy = _EMPATHY.get(emotion, _EMPATHY[EmotionCategory.GENERAL])
    fallback_answer = empathy[body.language] if body.language in ("en", "ar") else empathy["en"]

    ts = TherapySession(
        session_id=session_id,
        emotion=emotion,
        theme=cards_data[0]["theme"] if cards_data else None,
        user_message=body.message[:500],
        verses_shown=json.dumps([c["reference"] for c in cards_data]),
        language=body.language,
    )
    db.add(ts)
    await db.commit()

    return ChatResponse(
        session_id=session_id,
        emotion=emotion,
        emotion_label_en=labels["en"],
        emotion_label_ar=labels["ar"],
        answer=fallback_answer,
        answer_language=body.language,
        fallback_cards=[GuidanceCard(**c) for c in cards_data],
        used_rag=False,
        emotion_confidence=emotion_confidence,
        tone_profile=tone.label,
    )


# ---------------------------------------------------------------------------
# Phase T2: User Insights Dashboard
# ---------------------------------------------------------------------------

@router.post(
    "/insights",
    response_model=InsightsResponse,
    summary="Emotional journey insights for a set of session IDs",
    dependencies=[Depends(therapy_rate_limit)],
)
async def get_insights(
    body: InsightsRequest,
    db: AsyncSession = Depends(get_async_session),
) -> InsightsResponse:
    """
    Aggregate therapy session data for the provided session IDs and return
    an emotional journey summary: emotion distribution, most-visited theme,
    and top emotion.  All session IDs are client-generated, so this endpoint
    is privacy-preserving — no user account required.
    """
    from sqlalchemy import select as sa_select, func

    if not body.session_ids:
        return InsightsResponse(
            total_sessions=0,
            emotion_distribution=[],
        )

    # Limit to 200 session IDs to bound query size
    ids = body.session_ids[:200]

    result = await db.execute(
        sa_select(TherapySession.emotion, func.count(TherapySession.id).label("cnt"))
        .where(TherapySession.session_id.in_(ids))
        .group_by(TherapySession.emotion)
        .order_by(func.count(TherapySession.id).desc())
    )
    rows = result.all()

    total = sum(r.cnt for r in rows)
    distribution: List[EmotionCount] = []
    for row in rows:
        labels = EMOTION_LABELS.get(row.emotion, {"en": row.emotion, "ar": row.emotion})
        distribution.append(
            EmotionCount(
                emotion=row.emotion,
                label_en=labels["en"],
                label_ar=labels["ar"],
                count=row.cnt,
            )
        )

    top = distribution[0] if distribution else None

    # Most visited theme: look at the theme column
    theme_result = await db.execute(
        sa_select(TherapySession.theme, func.count(TherapySession.id).label("cnt"))
        .where(
            TherapySession.session_id.in_(ids),
            TherapySession.theme.is_not(None),
        )
        .group_by(TherapySession.theme)
        .order_by(func.count(TherapySession.id).desc())
        .limit(1)
    )
    theme_row = theme_result.first()

    # Phase T3 — growth prompts based on top emotion
    growth_prompt_en: Optional[str] = None
    growth_prompt_ar: Optional[str] = None
    suggested_next_theme: Optional[str] = None
    if top:
        gp = _GROWTH_PROMPTS.get(top.emotion, {})
        growth_prompt_en = gp.get("en")
        growth_prompt_ar = gp.get("ar")
        suggested_next_theme = _EMOTION_SUGGESTED_THEME.get(top.emotion)

    # Phase T5-B — ordered timeline for growth map
    from sqlalchemy import select as sa_select_t, asc as sa_asc
    timeline_result = await db.execute(
        sa_select(
            TherapySession.session_id,
            TherapySession.emotion,
            TherapySession.theme,
            TherapySession.created_at,
        )
        .where(TherapySession.session_id.in_(ids))
        .order_by(sa_asc(TherapySession.created_at))
        .limit(50)
    )
    timeline_rows = timeline_result.all()

    emotion_timeline: List[EmotionPoint] = []
    session_dates = []
    for row in timeline_rows:
        lbl = EMOTION_LABELS.get(row.emotion, {"en": row.emotion, "ar": row.emotion})
        emotion_timeline.append(
            EmotionPoint(
                session_id=row.session_id,
                emotion=row.emotion,
                label_en=lbl["en"],
                label_ar=lbl["ar"],
                theme=row.theme,
                timestamp=row.created_at.isoformat() if row.created_at else "",
            )
        )
        if row.created_at:
            session_dates.append(row.created_at.date())

    streak = _compute_streak(session_dates)
    trend = _compute_trend(emotion_timeline)

    return InsightsResponse(
        total_sessions=total,
        emotion_distribution=distribution,
        most_visited_theme=theme_row.theme if theme_row else None,
        streak_days=streak,
        top_emotion=top.emotion if top else None,
        top_emotion_label_en=top.label_en if top else None,
        top_emotion_label_ar=top.label_ar if top else None,
        suggested_next_theme=suggested_next_theme,
        growth_prompt_en=growth_prompt_en,
        growth_prompt_ar=growth_prompt_ar,
        emotion_timeline=emotion_timeline,
        trend=trend,
    )
