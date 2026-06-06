"""
Prophet Storytelling Service — safe, source-grounded narrative explanations
for the Quran Prophets Atlas (Phase X).

Design rules (mirror docs/quran-content-policy.md and the prophet-list policy):
    - The service NEVER generates tafsir from general knowledge.
    - If trusted tafsir source IDs are supplied, the service emits a brief,
      source-aware summary that references the source IDs and is marked
      ``needs_review``.
    - If no trusted source is supplied, the service emits a generic
      *navigation summary* (not a story) and marks the response
      ``no_verified_source``.
    - The service does not call an LLM directly. RAG summarisation, if added
      later, must run through ``app/rag/source_validator.py`` first.
    - Every storage object the service returns carries ``reviewStatus`` and
      ``humanReviewRequired`` — the consumer is expected to surface those.

Consumed by:
    - ``app/api/routes/prophets.py`` (POST /prophets/{id}/storytelling)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from app.services.entity_connection_explainer import (
    TRUSTED_TAFSIR_SOURCE_IDS,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AyahRef:
    surah_number: int
    ayah_start: int
    ayah_end: Optional[int] = None

    def reference_str(self) -> str:
        if self.ayah_end and self.ayah_end != self.ayah_start:
            return f"{self.surah_number}:{self.ayah_start}-{self.ayah_end}"
        return f"{self.surah_number}:{self.ayah_start}"


@dataclass
class ProphetStorytellingInput:
    prophet_id: str
    journey_type: Literal[
        "mushaf_order",
        "story_world_order",
        "revelation_order",
        "thematic_order",
        "learning_order",
    ]
    ayah_references: List[AyahRef]
    related_entity_ids: List[str] = field(default_factory=list)
    related_topic_ids: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    language: Literal["ar", "en"] = "en"


@dataclass
class ProphetStorytellingStage:
    stage_id: str
    explanation_arabic: str
    explanation_english: str
    ayah_references: List[AyahRef]
    source_evidence: List[str]
    warnings: List[str]
    review_status: Literal["needs_review", "verified", "no_verified_source"]


@dataclass
class ProphetStorytellingOutput:
    summary_arabic: str
    summary_english: str
    stages: List[ProphetStorytellingStage]
    follow_up_questions_arabic: List[str]
    follow_up_questions_english: List[str]
    related_stories: List[str]
    related_prophets: List[str]
    review_status: Literal["needs_review", "verified", "no_verified_source"]
    human_review_required: bool
    warnings: List[str]
    # Phase X2 — explicit output-mode label so the UI can label what the
    # response actually is. Defaults to the conservative mode.
    output_mode: Literal[
        "evidence_only",
        "navigation_summary",
        "source_backed_tafsir_summary",
        "no_verified_source",
    ] = "no_verified_source"
    follow_up_actions: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_REVIEW_WARNING = (
    "All AI-assisted storytelling defaults to needs_review until reviewed."
)

NO_VERIFIED_SOURCE_WARNING = (
    "no_verified_source: storytelling is a navigation summary only; "
    "detailed tafsir requires verified-source review."
)

DISPUTED_CHRONOLOGY_WARNING = (
    "Guided reading order is not a definitive historical chronology."
)

GENERIC_NAVIGATION_AR = (
    "تجمع هذه الآيات لأنها تذكر هذا النبي وقومه/سياقه في القرآن. "
    "هذا تصفّح إرشادي وليس تفسيراً؛ التفصيل يحتاج مصادر معتمدة."
)
GENERIC_NAVIGATION_EN = (
    "These ayahs are grouped because they mention this prophet and his people "
    "or surrounding context in the Quran. This is a navigation summary, not "
    "tafsir; details require verified-source review."
)


JOURNEY_LABEL_AR = {
    "mushaf_order": "الترتيب المصحفي",
    "story_world_order": "الترتيب القصصي الإرشادي",
    "revelation_order": "ترتيب النزول",
    "thematic_order": "الترتيب الموضوعي",
    "learning_order": "ترتيب تعلّمي",
}
JOURNEY_LABEL_EN = {
    "mushaf_order": "Mushaf order",
    "story_world_order": "Guided reading (story-world) order",
    "revelation_order": "Revelation order",
    "thematic_order": "Thematic order",
    "learning_order": "Learning order",
}


# ---------------------------------------------------------------------------
# Policy helpers
# ---------------------------------------------------------------------------


def _filter_trusted(source_ids: List[str]) -> List[str]:
    """Return only trusted tafsir source IDs (case-sensitive match)."""
    return [sid for sid in source_ids if sid in TRUSTED_TAFSIR_SOURCE_IDS]


def _ayah_summary(refs: List[AyahRef]) -> str:
    """Build a short ayah-list summary (no Arabic text)."""
    if not refs:
        return ""
    parts = [r.reference_str() for r in refs[:8]]
    extra = "" if len(refs) <= 8 else f" + {len(refs) - 8} more"
    return ", ".join(parts) + extra


def _build_summary(
    inp: ProphetStorytellingInput, trusted: List[str]
) -> tuple[str, str]:
    label_ar = JOURNEY_LABEL_AR[inp.journey_type]
    label_en = JOURNEY_LABEL_EN[inp.journey_type]
    refs = _ayah_summary(inp.ayah_references)

    if trusted:
        ar = (
            f"ملخص قراءة هذا النبي وفق {label_ar} يستند إلى مصادر تفسيرية معتمدة "
            f"({', '.join(trusted)}). الآيات المرجعية: {refs}."
        )
        en = (
            f"Reading summary for this prophet in the {label_en} draws on verified "
            f"tafsir sources ({', '.join(trusted)}). Referenced ayahs: {refs}."
        )
    else:
        ar = (
            f"{label_ar}: {GENERIC_NAVIGATION_AR} "
            + (f"الآيات: {refs}." if refs else "")
        )
        en = (
            f"{label_en}: {GENERIC_NAVIGATION_EN} "
            + (f"Ayahs: {refs}." if refs else "")
        )
    return ar.strip(), en.strip()


def _follow_up_questions(
    inp: ProphetStorytellingInput,
) -> tuple[List[str], List[str]]:
    ar = [
        f"أين ذُكر هذا النبي في القرآن غير هذه الآيات؟",
        f"من هم القوم أو الأشخاص المرتبطون بقصته في القرآن؟",
        f"ما الموضوعات القرآنية التي تتكرر في قصته؟",
        f"كيف ترتبط قصته بقصص الأنبياء الآخرين؟",
    ]
    en = [
        "Where else is this prophet mentioned in the Quran?",
        "Who are the people or figures connected to his story in the Quran?",
        "What Quranic themes recur in his story?",
        "How does his story relate to other prophets' stories?",
    ]
    return ar, en


def _stage_explanation(
    inp: ProphetStorytellingInput, trusted: List[str], stage_idx: int
) -> tuple[str, str]:
    """Per-stage explanation: same policy as the summary, slightly shorter."""
    label_ar = JOURNEY_LABEL_AR[inp.journey_type]
    label_en = JOURNEY_LABEL_EN[inp.journey_type]
    if trusted:
        ar = (
            f"مرحلة {stage_idx + 1} ضمن {label_ar} — تستند إلى المصادر: {', '.join(trusted)}."
        )
        en = (
            f"Stage {stage_idx + 1} within {label_en} — backed by sources: {', '.join(trusted)}."
        )
    else:
        ar = (
            f"مرحلة {stage_idx + 1} ضمن {label_ar} — تصفّح إرشادي بدون تفسير معتمد."
        )
        en = (
            f"Stage {stage_idx + 1} within {label_en} — navigation only, no verified tafsir."
        )
    return ar, en


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase X2 — limited-coverage prophet handling
# ---------------------------------------------------------------------------


# Compact-profile prophets (Quran detail is sparse) — always evidence_only or
# navigation_summary regardless of supplied source IDs.
_COMPACT_PROFILE_IDS = frozenset({"prophet_dhulkifl", "prophet_alyasa"})

# Muhammad ﷺ — Quranic mission profile only, NOT full seerah. Tafsir
# summarisation may surface trusted Quran-anchored context, but never a
# biographical narrative.
_MISSION_SUMMARY_IDS = frozenset({"prophet_muhammad"})

_MUHAMMAD_NOT_FULL_BIOGRAPHY_AR = (
    "هذه الصفحة تعرض الشواهد القرآنية فقط ولا تمثل سيرة كاملة للنبي ﷺ."
)
_MUHAMMAD_NOT_FULL_BIOGRAPHY_EN = (
    "This page presents Quranic evidence only and is not a full biography of the Prophet ﷺ."
)

_LIMITED_QURAN_DETAIL_AR = (
    "القرآن لا يفصّل قصة هذا النبي؛ هذا ملف موجز."
)
_LIMITED_QURAN_DETAIL_EN = (
    "The Quran does not narrate this prophet in detail; this is a compact profile."
)


_DEFAULT_FOLLOW_UP_ACTIONS = [
    "view_related_ayahs",
    "see_related_prophet",
    "explore_related_topic",
    "open_in_mushaf",
    "ask_tafsir_assistant_with_sources",
]


def _evidence_only_summary(
    inp: ProphetStorytellingInput,
) -> tuple[str, str]:
    refs = _ayah_summary(inp.ayah_references)
    ar = (
        f"الشواهد القرآنية لهذا النبي: {refs or '—'}. "
        f"لم يتم إنتاج أي ملخص سردي في هذا الوضع — فقط مراجع آيات."
    )
    en = (
        f"Quranic evidence for this prophet: {refs or '—'}. "
        f"No narrative summary is produced in evidence-only mode — references only."
    )
    return ar, en


def build_prophet_storytelling(
    inp: ProphetStorytellingInput,
) -> ProphetStorytellingOutput:
    """
    Build a safe storytelling explanation for a prophet journey.

    Output modes (Phase X2):
      - evidence_only: ayah list + no narrative (compact-profile prophets
        or explicit caller request via ``relatedEntityIds=["mode:evidence_only"]``).
      - navigation_summary: bilingual navigation summary, no tafsir.
      - source_backed_tafsir_summary: navigation summary with trusted tafsir
        source IDs cited. NEVER full tafsir from the AI alone.
      - no_verified_source: returned when no trusted source is supplied AND
        the prophet is not a compact-profile prophet that can run on
        evidence alone.

    The result's ``review_status`` is always ``"needs_review"`` (never
    ``"verified"``) except when the mode is ``no_verified_source``.
    """
    warnings: List[str] = [DEFAULT_REVIEW_WARNING]
    if inp.journey_type == "story_world_order":
        warnings.append(DISPUTED_CHRONOLOGY_WARNING)

    trusted = _filter_trusted(inp.source_ids)
    dropped = sorted(set(inp.source_ids) - set(trusted))
    if dropped:
        warnings.append("Dropped untrusted source IDs: " + ", ".join(dropped))

    # Mode selection
    is_compact = inp.prophet_id in _COMPACT_PROFILE_IDS
    is_mission = inp.prophet_id in _MISSION_SUMMARY_IDS

    if is_compact:
        # Compact-profile prophets always run in evidence_only or
        # navigation_summary mode regardless of supplied source IDs.
        warnings.append(_LIMITED_QURAN_DETAIL_AR)
        warnings.append(_LIMITED_QURAN_DETAIL_EN)
        if inp.ayah_references:
            output_mode = "navigation_summary"
            review_status: Literal[
                "needs_review", "verified", "no_verified_source"
            ] = "needs_review"
            summary_ar, summary_en = _build_summary(inp, [])
        else:
            output_mode = "evidence_only"
            review_status = "needs_review"
            summary_ar, summary_en = _evidence_only_summary(inp)
    elif is_mission:
        # Muhammad ﷺ — Quranic mission profile only.
        warnings.append(_MUHAMMAD_NOT_FULL_BIOGRAPHY_AR)
        warnings.append(_MUHAMMAD_NOT_FULL_BIOGRAPHY_EN)
        if trusted:
            output_mode = "source_backed_tafsir_summary"
            review_status = "needs_review"
            summary_ar, summary_en = _build_summary(inp, trusted)
        else:
            output_mode = "navigation_summary"
            review_status = "needs_review"
            summary_ar, summary_en = _build_summary(inp, [])
    else:
        # Regular prophet
        if trusted:
            output_mode = "source_backed_tafsir_summary"
            review_status = "needs_review"
            summary_ar, summary_en = _build_summary(inp, trusted)
        elif inp.ayah_references:
            output_mode = "navigation_summary"
            review_status = "needs_review"
            warnings.append(NO_VERIFIED_SOURCE_WARNING)
            summary_ar, summary_en = _build_summary(inp, [])
        else:
            output_mode = "no_verified_source"
            review_status = "no_verified_source"
            warnings.append(NO_VERIFIED_SOURCE_WARNING)
            summary_ar, summary_en = _build_summary(inp, [])

    stages: List[ProphetStorytellingStage] = []
    chunk_size = max(1, (len(inp.ayah_references) + 5) // 6)
    if inp.ayah_references:
        for i in range(0, len(inp.ayah_references), chunk_size):
            chunk = inp.ayah_references[i : i + chunk_size]
            ar, en = _stage_explanation(inp, trusted, i // chunk_size)
            stages.append(
                ProphetStorytellingStage(
                    stage_id=f"storytelling:{inp.prophet_id}:{inp.journey_type}:{i // chunk_size + 1}",
                    explanation_arabic=ar,
                    explanation_english=en,
                    ayah_references=chunk,
                    source_evidence=trusted,
                    warnings=([NO_VERIFIED_SOURCE_WARNING] if not trusted else []),
                    review_status=review_status,
                )
            )

    fu_ar, fu_en = _follow_up_questions(inp)

    return ProphetStorytellingOutput(
        summary_arabic=summary_ar,
        summary_english=summary_en,
        stages=stages,
        follow_up_questions_arabic=fu_ar,
        follow_up_questions_english=fu_en,
        related_stories=[],
        related_prophets=[],
        review_status=review_status,
        human_review_required=True,
        warnings=warnings,
        output_mode=output_mode,
        follow_up_actions=_DEFAULT_FOLLOW_UP_ACTIONS,
    )


__all__ = [
    "AyahRef",
    "ProphetStorytellingInput",
    "ProphetStorytellingOutput",
    "ProphetStorytellingStage",
    "build_prophet_storytelling",
    "DEFAULT_REVIEW_WARNING",
    "NO_VERIFIED_SOURCE_WARNING",
    "DISPUTED_CHRONOLOGY_WARNING",
]
