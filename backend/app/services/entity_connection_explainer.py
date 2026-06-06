"""
Entity Connection Explainer — safe, source-grounded explanation of why two
ayahs are connected through a shared entity.

Design rules (mirror docs/quran-content-policy.md and the entity-graph build):
- The service NEVER invents tafsir.
- If no verified tafsir source is available for the linked ayahs, the response
  is a generic relation explanation (not an interpretation) and the status is
  always ``needs_review``.
- If verified tafsir chunks are available, the service emits a short
  source-aware acknowledgement (no LLM rewrite) and lists the source IDs as
  ``tafsirEvidence`` entries with ``relationStatus="needs_review"`` until a
  reviewer signs off.
- The service does not call an LLM. It is a deterministic policy engine.
  RAG-based summarisation, if added later, must run through
  ``app/rag/source_validator.py`` first.

This module is pure: it does not touch the database. It is consumed by
``app/api/routes/entities.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# ---------------------------------------------------------------------------
# Trusted source IDs — must mirror ``frontend/src/data/sourceRegistry.ts``.
# Any sourceId not in this list is treated as untrusted and the request falls
# back to the generic relation explanation.
# ---------------------------------------------------------------------------

TRUSTED_TAFSIR_SOURCE_IDS = frozenset(
    {
        "ibn_kathir",
        "ibn_kathir_ar",
        "ibn_kathir_en",
        "tabari",
        "tabari_ar",
        "tabari_en",
        "qurtubi",
        "qurtubi_ar",
        "qurtubi_en",
    }
)

TRUSTED_QURAN_SOURCE_IDS = frozenset({"quran_uthmani_cloud"})

# ---------------------------------------------------------------------------
# Generic, language-aware explanations (NEVER tafsir).
# ---------------------------------------------------------------------------

GENERIC_EXPLANATION_AR = (
    "ترتبط هاتان الآيتان لأن السياق القرآني يجمع بينهما عبر هذه الذات. "
    "تفصيل المعنى التفسيري يتطلب مراجعة مصادر معتمدة."
)
GENERIC_EXPLANATION_EN = (
    "These ayahs are linked because the Quranic context joins them through "
    "this entity. Detailed interpretation requires verified tafsir review."
)

NO_VERIFIED_SOURCE_WARNING = (
    "no_verified_source: explanation is observational only. "
    "Detailed interpretation requires verified tafsir review."
)

DEFAULT_REVIEW_WARNING = (
    "All inferred connections default to needs_review until a reviewer signs off."
)

# ---------------------------------------------------------------------------
# Data classes (request / response)
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
class ExplainConnectionInput:
    entity_id: str
    source_reference: AyahRef
    target_reference: AyahRef
    relation_types: List[str]
    source_ids: List[str] = field(default_factory=list)
    language: Literal["ar", "en"] = "en"


@dataclass
class TafsirEvidenceEntry:
    source_id: str
    reference: str
    relation_status: Literal["verified", "needs_review"] = "needs_review"


@dataclass
class ExplainConnectionOutput:
    explanation_arabic: str
    explanation_english: str
    tafsir_evidence: List[TafsirEvidenceEntry]
    warnings: List[str]
    review_status: Literal["needs_review", "verified"]


# ---------------------------------------------------------------------------
# Policy helpers
# ---------------------------------------------------------------------------


def _filter_trusted_sources(source_ids: List[str]) -> List[str]:
    return [sid for sid in source_ids if sid in TRUSTED_TAFSIR_SOURCE_IDS]


def _relation_descriptor_en(rel: str) -> str:
    return {
        "mother_of": "shows a parent/child relationship",
        "son_of": "shows a parent/child relationship",
        "father_of": "shows a parent/child relationship",
        "daughter_of": "shows a parent/child relationship",
        "wife_of": "shows a spousal relationship",
        "husband_of": "shows a spousal relationship",
        "brother_of": "shows a sibling relationship",
        "sister_of": "shows a sibling relationship",
        "guardian_of": "shows a guardianship relationship",
        "family_of": "places both within the same family context",
        "same_story": "places both within the same Quranic narrative",
        "same_event": "links both to the same Quranic event",
        "same_surah_context": "places both inside the same surah passage",
        "theological_discussion": (
            "marks a theological clarification passage; interpretation must be "
            "deferred to verified tafsir"
        ),
        "chronological_before": "appears earlier in the curated reading order",
        "chronological_after": "appears later in the curated reading order",
        "related_theme": "shares a thematic link",
        "related_tafsir": "shares a tafsir-based link",
        "mentioned_with": "co-mentions both entities in the same ayah",
    }.get(rel, "links both entities in a Quranic context")


def _relation_descriptor_ar(rel: str) -> str:
    return {
        "mother_of": "علاقة أمومة/بنوة",
        "son_of": "علاقة أمومة/بنوة",
        "father_of": "علاقة أبوة/بنوة",
        "daughter_of": "علاقة أبوة/بنوة",
        "wife_of": "علاقة زوجية",
        "husband_of": "علاقة زوجية",
        "brother_of": "علاقة أخوّة",
        "sister_of": "علاقة أخوّة",
        "guardian_of": "علاقة كفالة",
        "family_of": "ضمن سياق العائلة نفسها",
        "same_story": "ضمن قصة قرآنية واحدة",
        "same_event": "ضمن حدث قرآني واحد",
        "same_surah_context": "ضمن مقطع واحد من السورة",
        "theological_discussion": (
            "مقطع بياني عقدي؛ يجب أن يُترك التفسير إلى مصادر معتمدة"
        ),
        "chronological_before": "ترتيب القراءة المقترح يضعها قبل الأخرى",
        "chronological_after": "ترتيب القراءة المقترح يضعها بعد الأخرى",
        "related_theme": "ارتباط محوري",
        "related_tafsir": "ارتباط تفسيري",
        "mentioned_with": "ذكر مشترك في نفس الآية",
    }.get(rel, "ارتباط قرآني")


def _compose_explanations(
    inp: ExplainConnectionInput, trusted: List[str]
) -> tuple[str, str]:
    """Build observational explanations grounded in the relation type list."""
    src = inp.source_reference.reference_str()
    tgt = inp.target_reference.reference_str()

    if not inp.relation_types:
        rels_en = "a Quranic context"
        rels_ar = "سياق قرآني"
    else:
        rels_en = "; ".join(_relation_descriptor_en(r) for r in inp.relation_types)
        rels_ar = "؛ ".join(_relation_descriptor_ar(r) for r in inp.relation_types)

    en = (
        f"Surah/ayah {src} and {tgt} are linked through entity {inp.entity_id}. "
        f"The recorded relation {rels_en}."
    )
    ar = (
        f"الآيتان {src} و {tgt} ترتبطان عبر الذات {inp.entity_id}. "
        f"العلاقة المسجلة: {rels_ar}."
    )
    if trusted:
        en += " Verified tafsir sources are listed as evidence — see the source registry."
        ar += " المصادر التفسيرية المعتمدة مذكورة في حقل الأدلة."
    else:
        en += " " + GENERIC_EXPLANATION_EN
        ar += " " + GENERIC_EXPLANATION_AR
    return ar, en


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def explain_connection(inp: ExplainConnectionInput) -> ExplainConnectionOutput:
    """
    Build a safe, source-aware explanation of why ``source_reference`` and
    ``target_reference`` are linked via ``entity_id``.

    - Untrusted ``source_ids`` are dropped silently and a
      ``no_verified_source`` warning is added.
    - The explanation is always observational; no tafsir is generated.
    - ``review_status`` is always ``"needs_review"`` from this service.
    """
    warnings: List[str] = [DEFAULT_REVIEW_WARNING]
    trusted = _filter_trusted_sources(inp.source_ids)
    untrusted_dropped = [sid for sid in inp.source_ids if sid not in TRUSTED_TAFSIR_SOURCE_IDS]
    if untrusted_dropped:
        warnings.append(
            "Dropped untrusted source IDs: " + ", ".join(sorted(set(untrusted_dropped)))
        )
    if not trusted:
        warnings.append(NO_VERIFIED_SOURCE_WARNING)

    if "theological_discussion" in inp.relation_types:
        warnings.append(
            "Theological-clarification passage: interpretation must defer to "
            "verified tafsir; do not display AI-generated conclusions."
        )

    ar, en = _compose_explanations(inp, trusted)

    evidence: List[TafsirEvidenceEntry] = [
        TafsirEvidenceEntry(
            source_id=sid,
            reference=f"{inp.source_reference.reference_str()} ↔ {inp.target_reference.reference_str()}",
            relation_status="needs_review",
        )
        for sid in trusted
    ]

    return ExplainConnectionOutput(
        explanation_arabic=ar,
        explanation_english=en,
        tafsir_evidence=evidence,
        warnings=warnings,
        review_status="needs_review",
    )


__all__ = [
    "AyahRef",
    "ExplainConnectionInput",
    "ExplainConnectionOutput",
    "TafsirEvidenceEntry",
    "TRUSTED_TAFSIR_SOURCE_IDS",
    "TRUSTED_QURAN_SOURCE_IDS",
    "explain_connection",
    "NO_VERIFIED_SOURCE_WARNING",
    "DEFAULT_REVIEW_WARNING",
    "ExplainProphetRelationInput",
    "ExplainProphetRelationOutput",
    "explain_prophet_relation",
    "PROPHET_RELATION_TYPES",
]


# ===========================================================================
# Phase X — Prophet relation explainer
#
# A prophet-aware variant of explain_connection that takes two prophet IDs
# and a prophet-relation type. The same safety rules apply: no AI tafsir,
# observational explanation only, source IDs filtered through the trusted
# allowlist, and review_status always emits "needs_review".
# ===========================================================================


PROPHET_RELATION_TYPES = frozenset(
    {
        "family_relation",
        "same_people",
        "same_place",
        "similar_trial",
        "shared_theme",
        "chronological_sequence",
        "mentioned_together",
        "mission_parallel",
        "scripture_relation",
        "needs_review",
    }
)


_PROPHET_RELATION_AR = {
    "family_relation": "صلة قرابة موثقة في الآيات المرفقة",
    "same_people": "تشاركٌ في نفس القوم أو الأمة",
    "same_place": "تشاركٌ في نفس المكان القرآني",
    "similar_trial": "ابتلاء أو محنة متشابهة في السياق القرآني",
    "shared_theme": "اشتراكٌ في موضوع قرآني",
    "chronological_sequence": "تتابعٌ في الترتيب القصصي الإرشادي",
    "mentioned_together": "ذُكِرا معاً في نفس المقطع",
    "mission_parallel": "تشابهٌ في الرسالة أو الدعوة",
    "scripture_relation": "ارتباطٌ بكتاب سماوي مشترك",
    "needs_review": "علاقة قيد المراجعة",
}

_PROPHET_RELATION_EN = {
    "family_relation": "documented family relation in the cited ayahs",
    "same_people": "addressed the same people or nation",
    "same_place": "linked to the same Quranic place",
    "similar_trial": "faced a similar Quranic trial or challenge",
    "shared_theme": "share a Quranic theme",
    "chronological_sequence": "appear in sequence within the guided reading order",
    "mentioned_together": "are mentioned together in the same passage",
    "mission_parallel": "carry a parallel prophetic mission",
    "scripture_relation": "are linked through a shared scripture",
    "needs_review": "relation is pending scholarly review",
}


@dataclass
class ExplainProphetRelationInput:
    source_prophet_id: str
    target_prophet_id: str
    relation_type: str
    ayah_references: List[AyahRef] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    language: Literal["ar", "en"] = "en"


@dataclass
class ExplainProphetRelationOutput:
    explanation_arabic: str
    explanation_english: str
    evidence_references: List[AyahRef]
    tafsir_evidence: List[TafsirEvidenceEntry]
    warnings: List[str]
    review_status: Literal["needs_review", "verified"]


def explain_prophet_relation(
    inp: ExplainProphetRelationInput,
) -> ExplainProphetRelationOutput:
    """
    Return a safe, observational explanation of why two prophets are related.

    - Untrusted source IDs are dropped with a ``no_verified_source`` warning.
    - The explanation NEVER includes AI tafsir.
    - ``review_status`` is always ``"needs_review"``.
    - ``evidence_references`` MUST be non-empty for the result to be useful;
      the caller is encouraged to pass at least one AyahRef.
    """
    warnings: List[str] = [DEFAULT_REVIEW_WARNING]

    if inp.relation_type not in PROPHET_RELATION_TYPES:
        warnings.append(
            f"Unknown prophet relation_type='{inp.relation_type}'; falling back to needs_review."
        )
        relation_label_ar = _PROPHET_RELATION_AR["needs_review"]
        relation_label_en = _PROPHET_RELATION_EN["needs_review"]
    else:
        relation_label_ar = _PROPHET_RELATION_AR[inp.relation_type]
        relation_label_en = _PROPHET_RELATION_EN[inp.relation_type]

    trusted = _filter_trusted_sources(inp.source_ids)
    dropped = sorted(set(inp.source_ids) - set(trusted))
    if dropped:
        warnings.append("Dropped untrusted source IDs: " + ", ".join(dropped))
    if not trusted:
        warnings.append(NO_VERIFIED_SOURCE_WARNING)

    if not inp.ayah_references:
        warnings.append(
            "no_evidence_references: relation explanation is generic — pass at "
            "least one AyahRef for a properly anchored explanation."
        )

    refs_str = (
        ", ".join(r.reference_str() for r in inp.ayah_references[:8]) or "—"
    )

    ar = (
        f"العلاقة بين النبي {inp.source_prophet_id} والنبي {inp.target_prophet_id}: "
        f"{relation_label_ar}. الآيات المرفقة: {refs_str}. "
        + (
            "مذكورة في المصادر المعتمدة." if trusted else GENERIC_EXPLANATION_AR
        )
    )
    en = (
        f"Relation between {inp.source_prophet_id} and {inp.target_prophet_id}: "
        f"{relation_label_en}. Cited ayahs: {refs_str}. "
        + (
            "Backed by verified tafsir sources." if trusted else GENERIC_EXPLANATION_EN
        )
    )

    evidence = [
        TafsirEvidenceEntry(
            source_id=sid,
            reference=refs_str,
            relation_status="needs_review",
        )
        for sid in trusted
    ]

    return ExplainProphetRelationOutput(
        explanation_arabic=ar,
        explanation_english=en,
        evidence_references=list(inp.ayah_references),
        tafsir_evidence=evidence,
        warnings=warnings,
        review_status="needs_review",
    )
