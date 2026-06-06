"""
Entity-Centered Quran Narrative GraphRAG API.

Endpoints:
    GET  /api/v1/quran/entities
    GET  /api/v1/quran/entities/{entity_id}
    GET  /api/v1/quran/entities/{entity_id}/mentions
    GET  /api/v1/quran/entities/{entity_id}/relations
    GET  /api/v1/quran/entities/{entity_id}/journey?order=mushaf|story_world|revelation|thematic
    POST /api/v1/quran/entities/explain-connection

Safety rules (mirror docs/quran-content-policy.md):
    - Responses NEVER include Quran text — only surah/ayah numbers.
    - Every record echoes reviewStatus and humanReviewRequired so the UI can
      surface needs_review badges.
    - No tafsir is generated. The explain-connection endpoint delegates to
      `entity_connection_explainer` which only emits observational text.
    - All path params are validated against an allow-list pattern; entity IDs
      must already be present in the generated mentions file.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path as FPath, Query, Response
from pydantic import BaseModel, Field, field_validator

from app.services.entity_connection_explainer import (
    AyahRef,
    ExplainConnectionInput,
    TRUSTED_TAFSIR_SOURCE_IDS,
    explain_connection,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Data file locations (mirrors the frontend generated artifacts).
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_GENERATED_DIR = _REPO_ROOT / "frontend" / "src" / "data" / "generated"
_MENTIONS_FILE = _GENERATED_DIR / "quranEntityMentions.json"
_RELATIONS_FILE = _GENERATED_DIR / "quranEntityRelations.json"
_JOURNEYS_FILE = _GENERATED_DIR / "quranEntityJourneys.json"
_COREF_MENTIONS_FILE = _GENERATED_DIR / "quranCoreferenceMentions.json"
_COREF_CHAINS_FILE = _GENERATED_DIR / "quranCoreferenceChains.json"
_ENRICHED_RELATIONS_FILE = _GENERATED_DIR / "quranEntityRelationsEnriched.json"

# Allow-list for entity IDs. Must match the seed factory naming scheme.
_ENTITY_ID_RE = re.compile(r"^entity_[a-z0-9_]+$")

# Cache headers tuned for immutable generated data — invalidated on rebuild.
_CACHE_HEADER = "public, max-age=3600"

VALID_ORDERS = {"mushaf", "story_world", "revelation", "thematic"}
_ORDER_TO_STAGE = {
    "mushaf": "mushaf_order",
    "story_world": "story_world",
    "revelation": "revelation_order",
    "thematic": "thematic_order",
}


# ---------------------------------------------------------------------------
# Loader (cached)
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "data_not_built",
                "message_en": f"Generated file missing: {path.name}. Run the entity build scripts.",
                "message_ar": "ملف البيانات غير موجود؛ يجب تشغيل سكربتات البناء أولاً.",
            },
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_mentions() -> Dict[str, Any]:
    return _read_json(_MENTIONS_FILE)


@lru_cache(maxsize=1)
def _load_relations() -> Dict[str, Any]:
    return _read_json(_RELATIONS_FILE)


@lru_cache(maxsize=1)
def _load_journeys() -> Dict[str, Any]:
    return _read_json(_JOURNEYS_FILE)


@lru_cache(maxsize=1)
def _load_coref_mentions() -> Dict[str, Any]:
    return _read_json(_COREF_MENTIONS_FILE)


@lru_cache(maxsize=1)
def _load_coref_chains() -> Dict[str, Any]:
    return _read_json(_COREF_CHAINS_FILE)


@lru_cache(maxsize=1)
def _load_enriched_relations() -> Dict[str, Any]:
    return _read_json(_ENRICHED_RELATIONS_FILE)


def _entity_index() -> Dict[str, Dict[str, Any]]:
    data = _load_mentions()
    return {e["entityId"]: e for e in data["entities"]}


# ---------------------------------------------------------------------------
# Path-param validation
# ---------------------------------------------------------------------------


def _validate_entity_id(entity_id: str) -> None:
    if not _ENTITY_ID_RE.match(entity_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_entity_id",
                "message_en": "Invalid entity_id format",
                "message_ar": "معرّف الكيان غير صالح",
            },
        )
    if entity_id not in _entity_index():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "entity_not_found",
                "message_en": f"Entity not found: {entity_id}",
                "message_ar": "الكيان غير موجود",
            },
        )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class EntitySummary(BaseModel):
    entityId: str
    entityType: str
    labelArabic: str
    labelEnglish: str
    mentionCount: int


class EntityListResponse(BaseModel):
    total: int
    entities: List[EntitySummary]


class EntityMentionOut(BaseModel):
    surahNumber: int
    ayahNumber: int
    mentionType: str
    confidence: float
    matchedText: Optional[str] = None
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool


class EntityDetail(BaseModel):
    entityId: str
    entityType: str
    labelArabic: str
    labelEnglish: str
    mentionCount: int
    surahCount: int
    surahs: List[int]
    mentions: List[EntityMentionOut]
    relatedEntityIds: List[str] = Field(default_factory=list)
    reviewStatus: str = "needs_review"
    humanReviewRequired: bool = True


class EntityRelationOut(BaseModel):
    sourceEntityId: str
    targetEntityId: str
    relationType: str
    confidence: float
    evidenceReferences: List[Dict[str, Any]]
    sourceIds: List[str]
    explanationArabic: Optional[str] = None
    explanationEnglish: Optional[str] = None
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class RelationsResponse(BaseModel):
    entityId: str
    total: int
    relations: List[EntityRelationOut]


class JourneySectionOut(BaseModel):
    sectionId: str
    labelArabic: str
    labelEnglish: str
    themeKey: Optional[str] = None
    ayahReferences: List[Dict[str, Any]]
    notesArabic: Optional[str] = None
    notesEnglish: Optional[str] = None
    reviewStatus: str
    warnings: List[str]


class JourneyResponse(BaseModel):
    entityId: str
    stageType: str
    certainty: str
    sections: List[JourneySectionOut]
    reviewStatus: str
    sourceIds: List[str]
    warnings: List[str]


class ExplainConnectionRequest(BaseModel):
    entityId: str
    sourceReference: Dict[str, int]
    targetReference: Dict[str, int]
    relationTypes: List[str] = Field(default_factory=list)
    sourceIds: List[str] = Field(default_factory=list)
    language: str = "en"

    @field_validator("entityId")
    @classmethod
    def _v_entity(cls, v: str) -> str:
        if not _ENTITY_ID_RE.match(v):
            raise ValueError("Invalid entityId format")
        return v

    @field_validator("language")
    @classmethod
    def _v_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v

    @field_validator("sourceReference", "targetReference")
    @classmethod
    def _v_ref(cls, v: Dict[str, int]) -> Dict[str, int]:
        if "surahNumber" not in v or "ayahStart" not in v:
            raise ValueError("reference must include surahNumber and ayahStart")
        if not (1 <= int(v["surahNumber"]) <= 114):
            raise ValueError("surahNumber out of range")
        if int(v["ayahStart"]) < 1:
            raise ValueError("ayahStart must be ≥1")
        return v


class ExplainConnectionResponse(BaseModel):
    explanationArabic: str
    explanationEnglish: str
    tafsirEvidence: List[Dict[str, str]]
    warnings: List[str]
    reviewStatus: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    response: Response,
    entity_type: Optional[str] = Query(None, description="Filter by entityType"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> EntityListResponse:
    """List all entities with their mention counts. Filter by entity type."""
    data = _load_mentions()
    items = [
        EntitySummary(
            entityId=e["entityId"],
            entityType=e["entityType"],
            labelArabic=e["labelArabic"],
            labelEnglish=e["labelEnglish"],
            mentionCount=len(e.get("mentions", [])),
        )
        for e in data["entities"]
        if (not entity_type or e["entityType"] == entity_type)
    ]
    items.sort(key=lambda x: x.mentionCount, reverse=True)
    sliced = items[offset : offset + limit]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return EntityListResponse(total=len(items), entities=sliced)


@router.get("/entities/{entity_id}", response_model=EntityDetail)
def get_entity(
    response: Response,
    entity_id: str = FPath(..., description="Entity id"),
) -> EntityDetail:
    _validate_entity_id(entity_id)
    idx = _entity_index()
    e = idx[entity_id]
    mentions = e.get("mentions", [])
    surahs = sorted({m["surahNumber"] for m in mentions})
    # Build related-entity ID list from the relations file.
    rel_data = _load_relations()
    related: List[str] = []
    seen = set()
    for r in rel_data["relations"]:
        if r["sourceEntityId"] == entity_id and r["targetEntityId"] not in seen:
            seen.add(r["targetEntityId"])
            related.append(r["targetEntityId"])
    response.headers["Cache-Control"] = _CACHE_HEADER
    return EntityDetail(
        entityId=e["entityId"],
        entityType=e["entityType"],
        labelArabic=e["labelArabic"],
        labelEnglish=e["labelEnglish"],
        mentionCount=len(mentions),
        surahCount=len(surahs),
        surahs=surahs,
        mentions=[EntityMentionOut(**m) for m in mentions[:1000]],
        relatedEntityIds=related,
    )


@router.get("/entities/{entity_id}/mentions", response_model=List[EntityMentionOut])
def get_entity_mentions(
    response: Response,
    entity_id: str = FPath(...),
    surah: Optional[int] = Query(None, ge=1, le=114),
    mention_type: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> List[EntityMentionOut]:
    _validate_entity_id(entity_id)
    idx = _entity_index()
    ms: List[Dict[str, Any]] = idx[entity_id].get("mentions", [])
    if surah:
        ms = [m for m in ms if m["surahNumber"] == surah]
    if mention_type:
        ms = [m for m in ms if m["mentionType"] == mention_type]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return [EntityMentionOut(**m) for m in ms[offset : offset + limit]]


@router.get("/entities/{entity_id}/relations", response_model=RelationsResponse)
def get_entity_relations(
    response: Response,
    entity_id: str = FPath(...),
    relation_type: Optional[str] = Query(None),
    target_entity_id: Optional[str] = Query(None),
) -> RelationsResponse:
    _validate_entity_id(entity_id)
    if target_entity_id is not None and not _ENTITY_ID_RE.match(target_entity_id):
        raise HTTPException(status_code=400, detail={"error_code": "invalid_target_entity_id"})
    rel_data = _load_relations()
    out: List[EntityRelationOut] = []
    for r in rel_data["relations"]:
        if r["sourceEntityId"] != entity_id:
            continue
        if relation_type and r["relationType"] != relation_type:
            continue
        if target_entity_id and r["targetEntityId"] != target_entity_id:
            continue
        out.append(EntityRelationOut(**r))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return RelationsResponse(entityId=entity_id, total=len(out), relations=out)


@router.get("/entities/{entity_id}/journey", response_model=JourneyResponse)
def get_entity_journey(
    response: Response,
    entity_id: str = FPath(...),
    order: str = Query("mushaf", description="mushaf | story_world | revelation | thematic"),
) -> JourneyResponse:
    _validate_entity_id(entity_id)
    if order not in VALID_ORDERS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_order",
                "message_en": f"order must be one of {sorted(VALID_ORDERS)}",
                "message_ar": "قيمة order غير صالحة",
            },
        )
    stage = _ORDER_TO_STAGE[order]
    j_data = _load_journeys()
    stages = j_data["journeys"].get(entity_id, {})
    journey = stages.get(stage)
    if journey is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "journey_not_built",
                "message_en": f"Journey '{order}' not built for this entity.",
                "message_ar": "لا توجد رحلة لهذا الكيان بهذا الترتيب.",
            },
        )
    response.headers["Cache-Control"] = _CACHE_HEADER
    return JourneyResponse(**journey)


@router.post("/entities/explain-connection", response_model=ExplainConnectionResponse)
def post_explain_connection(payload: ExplainConnectionRequest) -> ExplainConnectionResponse:
    """
    Return a safe, source-aware explanation of why two ayahs are linked
    through a shared entity. The endpoint NEVER generates tafsir; if no
    trusted source is supplied, the response is a generic relation
    description plus a no_verified_source warning.
    """
    inp = ExplainConnectionInput(
        entity_id=payload.entityId,
        source_reference=AyahRef(
            surah_number=int(payload.sourceReference["surahNumber"]),
            ayah_start=int(payload.sourceReference["ayahStart"]),
            ayah_end=int(payload.sourceReference.get("ayahEnd") or 0) or None,
        ),
        target_reference=AyahRef(
            surah_number=int(payload.targetReference["surahNumber"]),
            ayah_start=int(payload.targetReference["ayahStart"]),
            ayah_end=int(payload.targetReference.get("ayahEnd") or 0) or None,
        ),
        relation_types=payload.relationTypes,
        source_ids=payload.sourceIds,
        language=payload.language,  # type: ignore[arg-type]
    )
    result = explain_connection(inp)
    return ExplainConnectionResponse(
        explanationArabic=result.explanation_arabic,
        explanationEnglish=result.explanation_english,
        tafsirEvidence=[
            {
                "sourceId": e.source_id,
                "reference": e.reference,
                "relationStatus": e.relation_status,
            }
            for e in result.tafsir_evidence
        ],
        warnings=result.warnings,
        reviewStatus=result.review_status,
    )


# ===========================================================================
# Phase U — Coreference, Implicit Entity Linking
# ===========================================================================


class CoreferenceMentionOut(BaseModel):
    mentionId: str
    surfaceType: str
    surfaceText: Optional[str] = None
    surahNumber: int
    ayahNumber: int
    candidateEntityIds: List[str]
    selectedEntityId: Optional[str] = None
    confidence: float
    resolutionMethod: str
    evidenceReferences: List[Dict[str, Any]]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class CoreferenceMentionsResponse(BaseModel):
    entityId: str
    total: int
    mentions: List[CoreferenceMentionOut]


class CoreferenceChainOut(BaseModel):
    chainId: str
    entityId: str
    mentions: List[str]
    surahScope: List[int]
    ayahRangeStart: str
    ayahRangeEnd: str
    chainType: str
    confidence: float
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class CoreferenceChainsResponse(BaseModel):
    entityId: str
    total: int
    chains: List[CoreferenceChainOut]


class ImplicitLinkOut(BaseModel):
    sourceEntityId: str
    targetEntityId: str
    edgeType: str
    mentionIds: List[str]
    evidenceReferences: List[Dict[str, Any]]
    sourceIds: List[str]
    confidence: float
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class ImplicitLinksResponse(BaseModel):
    entityId: str
    total: int
    links: List[ImplicitLinkOut]


class ResolveCoreferencePayload(BaseModel):
    entityId: str
    mentionId: str
    language: str = "en"
    sourceIds: List[str] = Field(default_factory=list)

    @field_validator("entityId")
    @classmethod
    def _v_entity(cls, v: str) -> str:
        if not _ENTITY_ID_RE.match(v):
            raise ValueError("Invalid entityId format")
        return v

    @field_validator("language")
    @classmethod
    def _v_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v

    @field_validator("mentionId")
    @classmethod
    def _v_mid(cls, v: str) -> str:
        if not re.match(r"^(cm|em)[a-z0-9_:]+$", v) and not re.match(r"^cm_\d{6}$", v):
            # The scanner emits cm_NNNNNN; entity-anchor IDs start with em:.
            raise ValueError("Invalid mentionId format")
        return v


class ResolveCoreferenceResponse(BaseModel):
    explanationArabic: str
    explanationEnglish: str
    candidateEntityId: str
    method: str
    confidence: float
    surfaceType: str
    surfaceText: Optional[str]
    evidenceReferences: List[Dict[str, Any]]
    sourceIds: List[str]
    warnings: List[str]
    reviewStatus: str


@router.get(
    "/entities/{entity_id}/coreference",
    response_model=CoreferenceMentionsResponse,
)
def get_entity_coreference(
    response: Response,
    entity_id: str = FPath(...),
    surface_type: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    review_status: Optional[str] = Query(None, description="needs_review | verified | rejected"),
) -> CoreferenceMentionsResponse:
    _validate_entity_id(entity_id)
    data = _load_coref_mentions()
    out: List[CoreferenceMentionOut] = []
    for m in data["mentions"]:
        if (m.get("selectedEntityId") or (m.get("candidateEntityIds") or [None])[0]) != entity_id:
            continue
        if surface_type and m["surfaceType"] != surface_type:
            continue
        if m["confidence"] < min_confidence:
            continue
        if review_status and m["reviewStatus"] != review_status:
            continue
        out.append(CoreferenceMentionOut(**m))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return CoreferenceMentionsResponse(entityId=entity_id, total=len(out), mentions=out)


@router.get(
    "/entities/{entity_id}/coreference-chains",
    response_model=CoreferenceChainsResponse,
)
def get_entity_coreference_chains(
    response: Response,
    entity_id: str = FPath(...),
    chain_type: Optional[str] = Query(None),
) -> CoreferenceChainsResponse:
    _validate_entity_id(entity_id)
    data = _load_coref_chains()
    out: List[CoreferenceChainOut] = []
    for c in data["chains"]:
        if c["entityId"] != entity_id:
            continue
        if chain_type and c["chainType"] != chain_type:
            continue
        out.append(CoreferenceChainOut(**c))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return CoreferenceChainsResponse(entityId=entity_id, total=len(out), chains=out)


@router.get(
    "/entities/{entity_id}/implicit-links",
    response_model=ImplicitLinksResponse,
)
def get_entity_implicit_links(
    response: Response,
    entity_id: str = FPath(...),
    edge_type: Optional[str] = Query(None),
) -> ImplicitLinksResponse:
    _validate_entity_id(entity_id)
    data = _load_enriched_relations()
    out: List[ImplicitLinkOut] = []
    for e in data.get("coreferenceEdges", []):
        if e["sourceEntityId"] != entity_id and e["targetEntityId"] != entity_id:
            continue
        if edge_type and e["edgeType"] != edge_type:
            continue
        out.append(ImplicitLinkOut(**e))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ImplicitLinksResponse(entityId=entity_id, total=len(out), links=out)


@router.post(
    "/entities/resolve-coreference-explanation",
    response_model=ResolveCoreferenceResponse,
)
def post_resolve_coreference_explanation(
    payload: ResolveCoreferencePayload,
) -> ResolveCoreferenceResponse:
    """
    Return a safe, source-aware explanation of WHY a coreference mention is
    linked to its candidate entity. The endpoint NEVER generates tafsir; if
    no trusted source is supplied, the response is a generic, observational
    explanation plus a `no_verified_source` warning. ``reviewStatus`` is
    always ``"needs_review"``.
    """
    data = _load_coref_mentions()
    mention: Optional[Dict[str, Any]] = next(
        (m for m in data["mentions"] if m["mentionId"] == payload.mentionId), None
    )
    if mention is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "coreference_mention_not_found",
                "message_en": "No coreference mention with that ID.",
                "message_ar": "لا توجد إحالة بهذا المعرّف.",
            },
        )
    candidate = mention.get("selectedEntityId") or (mention.get("candidateEntityIds") or [None])[0]
    if candidate != payload.entityId:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "entity_mismatch",
                "message_en": "Mention does not point to this entity.",
                "message_ar": "الإحالة لا تخص هذا الكيان.",
            },
        )

    # Compose explanation via the existing explainer (no tafsir generated).
    surah = int(mention["surahNumber"])
    ayah = int(mention["ayahNumber"])
    surface = mention.get("surfaceType", "implicit_context")
    trusted = [sid for sid in payload.sourceIds if sid in TRUSTED_TAFSIR_SOURCE_IDS]
    untrusted_dropped = [sid for sid in payload.sourceIds if sid not in TRUSTED_TAFSIR_SOURCE_IDS]
    warnings: List[str] = list(mention.get("warnings", []))
    warnings.append("All inferred coreference links default to needs_review.")
    if untrusted_dropped:
        warnings.append("Dropped untrusted source IDs: " + ", ".join(sorted(set(untrusted_dropped))))
    if not trusted:
        warnings.append(
            "no_verified_source: explanation is observational only. Detailed interpretation requires verified tafsir review."
        )

    if payload.language == "ar":
        ar = (
            f"الإحالة في الآية {surah}:{ayah} من نوع {surface}؛ "
            f"المرشّح: {payload.entityId}. "
            "هذا الربط ملاحظ ولا يمثّل تفسيرًا، ويحتاج إلى مراجعة علمية."
        )
        en = (
            f"Mention at {surah}:{ayah} of surfaceType '{surface}' suggests "
            f"candidate {payload.entityId}. This link is observational, not "
            "interpretive; scholarly review is required."
        )
    else:
        en = (
            f"Mention at {surah}:{ayah} of surfaceType '{surface}' suggests "
            f"candidate {payload.entityId}. This link is observational, not "
            "interpretive; scholarly review is required."
        )
        ar = (
            f"الإحالة في الآية {surah}:{ayah} من نوع {surface}؛ "
            f"المرشّح: {payload.entityId}. "
            "هذا الربط ملاحظ ولا يمثّل تفسيرًا، ويحتاج إلى مراجعة علمية."
        )

    return ResolveCoreferenceResponse(
        explanationArabic=ar,
        explanationEnglish=en,
        candidateEntityId=payload.entityId,
        method=mention.get("resolutionMethod", "rule_pattern"),
        confidence=float(mention.get("confidence", 0.0)),
        surfaceType=surface,
        surfaceText=mention.get("surfaceText"),
        evidenceReferences=mention.get("evidenceReferences", []),
        sourceIds=trusted,
        warnings=warnings,
        reviewStatus="needs_review",
    )


__all__ = ["router", "TRUSTED_TAFSIR_SOURCE_IDS"]
