"""
Crisis classifier for the therapy page.

Detects user inputs that signal **acute risk** (suicidal ideation,
self-harm, abuse, severe hopelessness) and returns a structured signal
that the therapy router uses to gate spiritual-content selection.

Safety stance:
    - Errors on the side of TRIGGERING. False positives are cheap
      (the user simply also sees a hotline). False negatives can cost
      a life.
    - Does NOT diagnose. Returns a `level` ∈ {none, elevated, crisis}
      and a `reasons` list — no clinical labels.
    - Hotline data is sourced and static (see
      `docs/therapy-source-research.md` for citations).

Important: the keyword sets below are intentionally inclusive. They
were compiled from the user-facing strings present in
`spiritual_guidance_service._SADNESS_KEYWORDS` /
`_HOPELESSNESS_KEYWORDS` and extended with explicit suicide /
self-harm / abuse vocabulary. We do not pull from medical literature
verbatim because we don't need symptom lists — we need acute risk
markers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Hotline table — citations in docs/therapy-source-research.md
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrisisHotline:
    region_code: str            # ISO country / "INTL" / "MUSLIM"
    region_name_en: str
    region_name_ar: str
    number: str
    organisation_en: str
    organisation_ar: str
    url: str
    is_muslim_specific: bool = False


CRISIS_HOTLINES: List[CrisisHotline] = [
    CrisisHotline(
        region_code="US",
        region_name_en="United States",
        region_name_ar="الولايات المتحدة",
        number="988",
        organisation_en="988 Suicide & Crisis Lifeline (call/text/chat)",
        organisation_ar="خط الإنقاذ من الانتحار والأزمات 988",
        url="https://988lifeline.org",
    ),
    CrisisHotline(
        region_code="GB",
        region_name_en="United Kingdom & Ireland",
        region_name_ar="المملكة المتحدة وأيرلندا",
        number="116 123",
        organisation_en="Samaritans (24/7)",
        organisation_ar="منظمة Samaritans للدعم النفسي",
        url="https://www.samaritans.org",
    ),
    CrisisHotline(
        region_code="SA",
        region_name_en="Saudi Arabia",
        region_name_ar="المملكة العربية السعودية",
        number="920033360",
        organisation_en="National Center for Mental Health Promotion",
        organisation_ar="المركز الوطني لتعزيز الصحة النفسية",
        url="https://icarewellbeing.com/crisis-hotline-mental-health-uae/",
    ),
    CrisisHotline(
        region_code="INTL",
        region_name_en="Worldwide (175+ countries)",
        region_name_ar="عالمياً (أكثر من 175 دولة)",
        number="findahelpline.com",
        organisation_en="Find A Helpline — search by country & language",
        organisation_ar="دليل خطوط المساعدة حسب الدولة واللغة",
        url="https://findahelpline.com",
    ),
    CrisisHotline(
        region_code="INTL",
        region_name_en="Worldwide",
        region_name_ar="عالمياً",
        number="befrienders.org",
        organisation_en="Befrienders Worldwide volunteer crisis lines",
        organisation_ar="خطوط الأزمات التطوعية حول العالم",
        url="https://befrienders.org",
    ),
    CrisisHotline(
        region_code="MUSLIM",
        region_name_en="Muslim-integrated tele-therapy (Khalil Center)",
        region_name_ar="علاج نفسي إسلامي عبر الإنترنت — مركز خليل",
        number="khalilcenter.com",
        organisation_en="Khalil Center — Islamic spiritual + psychological care",
        organisation_ar="مركز خليل للرعاية النفسية والروحية المتكاملة",
        url="https://khalilcenter.com",
        is_muslim_specific=True,
    ),
    CrisisHotline(
        region_code="MUSLIM",
        region_name_en="Muslim youth — Naseeha Helpline",
        region_name_ar="مساعدة الشباب المسلم — خط نصيحة",
        number="naseeha.org",
        organisation_en="Confidential phone/text/chat for Muslim youth",
        organisation_ar="دعم سري عبر الهاتف والرسائل للشباب المسلم",
        url="https://www.naseeha.org",
        is_muslim_specific=True,
    ),
]


# ---------------------------------------------------------------------------
# Trigger vocabularies (English + Arabic)
#
# Tier 1 — `_HARD_TRIGGERS`: phrases that ALONE escalate to crisis.
# Tier 2 — `_SOFT_TRIGGERS`: phrases that escalate to "elevated" alone,
#                            and to "crisis" if any tier-1 also matches.
# ---------------------------------------------------------------------------

_HARD_TRIGGERS_EN = (
    "kill myself", "want to die", "end my life", "ending my life",
    "suicide", "suicidal", "take my own life", "i will die",
    "no reason to live", "better off dead", "wish i was dead",
    "wish i were dead", "wanna die", "want to be dead",
    "hang myself", "overdose", "jump off", "shoot myself",
    "cut myself", "cutting myself", "self harm", "self-harm",
    "hurt myself",
)

_HARD_TRIGGERS_AR = (
    "أريد أن أموت", "اريد الموت", "أتمنى الموت", "أنهي حياتي",
    "أقتل نفسي", "اقتل نفسي", "انتحار", "انتحر",
    "سأنتحر", "ساقتل نفسي", "أؤذي نفسي", "اذي نفسي",
    "ايذاء النفس", "لا أريد العيش", "لا اريد العيش",
    "أتمنى لو مت", "ليتني مت", "ليتني أموت",
)

_SOFT_TRIGGERS_EN = (
    "can't go on", "cant go on", "nothing matters",
    "no one cares", "give up", "giving up", "hopeless",
    "i hate my life", "i'm done", "im done", "tired of living",
    "tired of life", "abuse", "being abused", "hit me",
    "beats me", "rape", "raped", "assault",
)

_SOFT_TRIGGERS_AR = (
    "ما عاد فيني", "لا أستطيع الاستمرار", "لا استطيع الاستمرار",
    "لا أحد يهتم", "ما حد يهمه", "تعبت من الحياة",
    "كرهت حياتي", "كرهت الحياة", "ضاعت حياتي",
    "يعنفني", "يضربني", "يضربونني",
    "اغتصاب", "اعتداء", "تحرش",
)


def _compile(words: tuple[str, ...]) -> List[re.Pattern[str]]:
    """Compile case-insensitive boundary patterns for Latin-script phrases."""
    return [
        re.compile(
            rf"(?:^|[\s\.,;:!\?\-])({re.escape(w)})(?:$|[\s\.,;:!\?\-])",
            re.IGNORECASE,
        )
        for w in words
    ]


# Arabic morphology (definite article ال, conjunctions و / ف, prepositions ب / ل
# fusing to the next word) makes Latin-style word boundaries unreliable. For
# Arabic triggers we use plain substring matching — false positives are
# acceptable per the safety stance.
_HARD_PATTERNS = _compile(_HARD_TRIGGERS_EN)
_SOFT_PATTERNS = _compile(_SOFT_TRIGGERS_EN)
_HARD_AR_SUBSTRINGS = tuple(_HARD_TRIGGERS_AR)
_SOFT_AR_SUBSTRINGS = tuple(_SOFT_TRIGGERS_AR)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@dataclass
class CrisisAssessment:
    """Result of running the classifier."""
    level: str                     # "none" | "elevated" | "crisis"
    reasons: List[str] = field(default_factory=list)
    suggested_hotlines: List[CrisisHotline] = field(default_factory=list)

    @property
    def is_crisis(self) -> bool:
        return self.level == "crisis"

    @property
    def is_elevated(self) -> bool:
        return self.level in ("elevated", "crisis")


def classify_crisis(text: str) -> CrisisAssessment:
    """Return a CrisisAssessment for the user-provided text.

    The classifier is intentionally conservative:
      - 1+ hard-trigger phrase → ``crisis``
      - 1+ soft-trigger phrase → ``elevated`` (or ``crisis`` if combined
        with any hard trigger)
      - otherwise → ``none``

    When `level != "none"`, a non-empty list of hotlines is returned so
    the UI can always render at least one safety resource.
    """
    if not text:
        return CrisisAssessment(level="none")

    normalised = f" {text.strip()} "  # padding so boundary regex matches at edges

    hard_hits: List[str] = []
    soft_hits: List[str] = []

    for pat in _HARD_PATTERNS:
        m = pat.search(normalised)
        if m:
            hard_hits.append(m.group(1).strip())
    for pat in _SOFT_PATTERNS:
        m = pat.search(normalised)
        if m:
            soft_hits.append(m.group(1).strip())

    # Arabic: substring search to handle prefix morphology.
    for w in _HARD_AR_SUBSTRINGS:
        if w in text:
            hard_hits.append(w)
    for w in _SOFT_AR_SUBSTRINGS:
        if w in text:
            soft_hits.append(w)

    if hard_hits:
        return CrisisAssessment(
            level="crisis",
            reasons=[f"trigger: {t}" for t in hard_hits[:5]],
            suggested_hotlines=list(CRISIS_HOTLINES),
        )
    if soft_hits:
        return CrisisAssessment(
            level="elevated",
            reasons=[f"signal: {t}" for t in soft_hits[:5]],
            # In "elevated" mode we surface the international directory +
            # the Muslim-specific options only — to keep the banner short.
            suggested_hotlines=[h for h in CRISIS_HOTLINES if h.region_code in ("INTL", "MUSLIM")],
        )

    return CrisisAssessment(level="none")


# ---------------------------------------------------------------------------
# Bilingual banner text
# ---------------------------------------------------------------------------

CRISIS_BANNER_EN = (
    "We care about your safety. If you are thinking about ending your life "
    "or hurting yourself, please reach out to a crisis line now — you are "
    "not alone. Spiritual support from the Quran is meaningful, but in this "
    "moment please speak to a trained professional."
)

CRISIS_BANNER_AR = (
    "سلامتك تهمنا. إذا كنت تفكر في إنهاء حياتك أو إيذاء نفسك، يرجى التواصل "
    "مع أحد خطوط الأزمات الآن — لست وحدك. الدعم الروحي من القرآن مفيد، "
    "ولكن في هذه اللحظة يرجى التحدث إلى مختص مدرب."
)

ELEVATED_BANNER_EN = (
    "It sounds like you are carrying something heavy. Please consider "
    "reaching out to someone who can support you — a trusted friend, a "
    "mental-health professional, or one of the helplines below."
)

ELEVATED_BANNER_AR = (
    "يبدو أنك تحمل شيئاً ثقيلاً. يرجى التفكير في التواصل مع شخص يمكنه دعمك "
    "— صديق موثوق، أو مختص نفسي، أو أحد خطوط المساعدة أدناه."
)


def banner_text(level: str, language: str) -> Optional[str]:
    if level == "crisis":
        return CRISIS_BANNER_AR if language == "ar" else CRISIS_BANNER_EN
    if level == "elevated":
        return ELEVATED_BANNER_AR if language == "ar" else ELEVATED_BANNER_EN
    return None


__all__ = [
    "CrisisAssessment",
    "CrisisHotline",
    "CRISIS_HOTLINES",
    "classify_crisis",
    "banner_text",
    "CRISIS_BANNER_EN",
    "CRISIS_BANNER_AR",
    "ELEVATED_BANNER_EN",
    "ELEVATED_BANNER_AR",
]
