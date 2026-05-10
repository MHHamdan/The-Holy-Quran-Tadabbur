"""
Phase T5-C — Emotionally Adaptive AI Tone.

Derives a ToneProfile from the classified emotion and NLI confidence score,
then supplies a tone directive string that is injected into the RAG system
prompt so the LLM adapts its register, depth, and pacing accordingly.

Severity tiers
--------------
DISTRESS   — hopelessness (always), grief / fear when confidence ≥ 0.65
             LLM is instructed to lead with unconditional presence, use
             short sentences, and avoid information overload.
MODERATE   — anxiety, sadness, guilt, loneliness, anger, stress, doubt,
             and lower-confidence grief / fear.
             LLM validates feelings first, then guides.
POSITIVE   — gratitude.
             LLM amplifies and deepens the positive state.
MILD       — general / fallback.
             LLM stays welcoming and exploratory.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Severity enum
# ---------------------------------------------------------------------------

class EmotionSeverity(str, Enum):
    DISTRESS = "distress"
    MODERATE = "moderate"
    POSITIVE = "positive"
    MILD = "mild"


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_ALWAYS_DISTRESS = frozenset({"hopelessness"})
_HIGH_DISTRESS_EMOTIONS = frozenset({"grief", "fear"})
_DISTRESS_CONFIDENCE_THRESHOLD = 0.65

_POSITIVE_EMOTIONS = frozenset({"gratitude"})
_MILD_EMOTIONS = frozenset({"general"})


# ---------------------------------------------------------------------------
# ToneProfile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToneProfile:
    severity: EmotionSeverity
    label: str                   # human-readable label for the frontend badge
    directive_en: str            # injected into RAG prompt for English
    directive_ar: str            # injected into RAG prompt for Arabic


# ---------------------------------------------------------------------------
# Tone directives (plain strings, NOT tafsir — platform meta-commentary)
# ---------------------------------------------------------------------------

_TONE_PROFILES: dict[EmotionSeverity, ToneProfile] = {
    EmotionSeverity.DISTRESS: ToneProfile(
        severity=EmotionSeverity.DISTRESS,
        label="gentle",
        directive_en=(
            "TONE INSTRUCTION: The user is in deep emotional distress. "
            "Lead with unconditional presence and warmth — acknowledge their pain sincerely "
            "in your first sentence before offering any guidance. "
            "Use short, gentle sentences. Keep the response focused and calming. "
            "Do not overwhelm with information. Compassion outweighs comprehensiveness here."
        ),
        directive_ar=(
            "تعليمات النبرة: المستخدم يمر بضائقة عاطفية عميقة. "
            "ابدأ بالحضور الكامل والدفء — اعترف بألمه بصدق في جملتك الأولى قبل أي توجيه. "
            "استخدم جملاً قصيرة ولطيفة. أبقِ الإجابة مركّزة وهادئة. "
            "تجنب إثقاله بالمعلومات. التعاطف يأتي قبل الشمولية هنا."
        ),
    ),
    EmotionSeverity.MODERATE: ToneProfile(
        severity=EmotionSeverity.MODERATE,
        label="supportive",
        directive_en=(
            "TONE INSTRUCTION: The user is experiencing a genuine emotional challenge. "
            "Validate their feelings warmly in your opening before moving to guidance. "
            "Balance empathy with Quranic substance. Be grounded, reassuring, and unhurried."
        ),
        directive_ar=(
            "تعليمات النبرة: يواجه المستخدم تحدياً عاطفياً حقيقياً. "
            "أكّد مشاعره بدفء في مقدمتك قبل الانتقال إلى التوجيه. "
            "وازن التعاطف مع المضمون القرآني. كن راسخاً ومطمئناً وغير مستعجل."
        ),
    ),
    EmotionSeverity.POSITIVE: ToneProfile(
        severity=EmotionSeverity.POSITIVE,
        label="celebratory",
        directive_en=(
            "TONE INSTRUCTION: The user is in a state of gratitude or spiritual positivity. "
            "Match their uplifted energy. Amplify what is good, deepen their reflection, "
            "and celebrate their spiritual connection with warmth and joy."
        ),
        directive_ar=(
            "تعليمات النبرة: المستخدم في حالة امتنان أو إيجابية روحية. "
            "طابق طاقته المرتفعة. ضاعف ما هو جيد وعمّق تأمله "
            "واحتفل بارتباطه الروحي بدفء وبهجة."
        ),
    ),
    EmotionSeverity.MILD: ToneProfile(
        severity=EmotionSeverity.MILD,
        label="welcoming",
        directive_en=(
            "TONE INSTRUCTION: The user is in a general or exploratory state. "
            "Be welcoming, open, and gently curious. Invite reflection without assuming "
            "any particular emotional weight or urgency."
        ),
        directive_ar=(
            "تعليمات النبرة: المستخدم في حالة عامة أو استكشافية. "
            "كن مرحباً ومنفتحاً وفضولياً بلطف. ادعُ إلى التأمل دون افتراض "
            "أي ثقل عاطفي أو إلحاح معين."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_severity(emotion: str, confidence: float = 0.0) -> EmotionSeverity:
    """
    Derive the emotional severity tier from an emotion key and NLI confidence.

    Parameters
    ----------
    emotion:
        An EmotionCategory.value string (e.g. 'anxiety', 'grief').
    confidence:
        NLI entailment confidence in [0.0, 1.0].  0.0 means keyword fallback was used.

    Returns
    -------
    EmotionSeverity
    """
    if not emotion or emotion in _MILD_EMOTIONS:
        return EmotionSeverity.MILD
    if emotion in _POSITIVE_EMOTIONS:
        return EmotionSeverity.POSITIVE
    if emotion in _ALWAYS_DISTRESS:
        return EmotionSeverity.DISTRESS
    if emotion in _HIGH_DISTRESS_EMOTIONS and confidence >= _DISTRESS_CONFIDENCE_THRESHOLD:
        return EmotionSeverity.DISTRESS
    return EmotionSeverity.MODERATE


def get_tone_profile(emotion: str, confidence: float = 0.0) -> ToneProfile:
    """
    Return the ToneProfile for an emotion + confidence pair.

    This is the single entry-point for callers in the therapy route.
    """
    severity = get_severity(emotion, confidence)
    return _TONE_PROFILES[severity]


def tone_directive(emotion: str, confidence: float, language: str) -> str:
    """
    Return the localised directive string ready to inject into a RAG prompt.

    Parameters
    ----------
    language:
        'ar' or 'en' (defaults to 'en' for any other value).
    """
    profile = get_tone_profile(emotion, confidence)
    return profile.directive_ar if language == "ar" else profile.directive_en
