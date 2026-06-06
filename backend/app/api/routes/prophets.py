"""
Quran Prophets Atlas API (Phase X).

Endpoints (all under /api/v1/quran):
    GET  /prophets
    GET  /prophets/{prophet_id}
    GET  /prophets/{prophet_id}/ayahs
    GET  /prophets/{prophet_id}/stories
    GET  /prophets/{prophet_id}/relations
    GET  /prophets/{prophet_id}/journey?order=mushaf|story_world|thematic|learning|revelation
    POST /prophets/{prophet_id}/storytelling
    POST /prophets/explain-relation

Safety:
    - Responses NEVER include Quran text — only surah/ayah numbers.
    - Every record echoes reviewStatus and humanReviewRequired so the UI
      can render needs_review badges.
    - The atlas is read from the generated file; mutations require a
      rebuild via scripts/build-quran-prophets-atlas.ts.
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
    ExplainProphetRelationInput,
    PROPHET_RELATION_TYPES,
    explain_prophet_relation,
)
from app.services.prophet_storytelling_service import (
    AyahRef as StorytellingAyahRef,
    ProphetStorytellingInput,
    build_prophet_storytelling,
)


router = APIRouter()

# ---------------------------------------------------------------------------
# Data file location
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ATLAS_FILE = (
    _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetsAtlas.json"
)
_STORY_PAGES_FILE = (
    _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetStoryPages.json"
)
_CONTEXTUAL_LINKS_FILE = (
    _REPO_ROOT
    / "frontend"
    / "src"
    / "data"
    / "generated"
    / "quranProphetContextualLinks.json"
)

_PROPHET_ID_RE = re.compile(r"^prophet_[a-z0-9_]+$")
_CACHE_HEADER = "public, max-age=3600"

_VALID_ORDERS = {"mushaf", "story_world", "revelation", "thematic", "learning"}
_ORDER_TO_JOURNEY = {
    "mushaf": "mushaf_order",
    "story_world": "story_world_order",
    "revelation": "revelation_order",
    "thematic": "thematic_order",
    "learning": "learning_order",
}


# ---------------------------------------------------------------------------
# Atlas loader (cached)
# ---------------------------------------------------------------------------


def _read_atlas() -> Dict[str, Any]:
    if not _ATLAS_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "data_not_built",
                "message_en": (
                    "quranProphetsAtlas.json is missing. Run "
                    "`npx tsx scripts/build-quran-prophets-atlas.ts` to build it."
                ),
                "message_ar": "ملف أطلس الأنبياء غير موجود؛ شغّل سكربت البناء أولاً.",
            },
        )
    return json.loads(_ATLAS_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_atlas() -> Dict[str, Any]:
    return _read_atlas()


@lru_cache(maxsize=1)
def _load_story_pages() -> Dict[str, Any]:
    if not _STORY_PAGES_FILE.exists():
        return {"version": "0", "pages": [], "totalPages": 0, "prophetIdsCovered": []}
    return json.loads(_STORY_PAGES_FILE.read_text(encoding="utf-8"))


def _story_page_index() -> Dict[str, Dict[str, Any]]:
    return {p["prophetId"]: p for p in _load_story_pages().get("pages", [])}


@lru_cache(maxsize=1)
def _load_contextual_links() -> Dict[str, Any]:
    if not _CONTEXTUAL_LINKS_FILE.exists():
        return {"version": "0", "links": [], "totalLinks": 0}
    return json.loads(_CONTEXTUAL_LINKS_FILE.read_text(encoding="utf-8"))


def _profile_index() -> Dict[str, Dict[str, Any]]:
    return {p["prophetId"]: p for p in _load_atlas()["profiles"]}


def _validate_prophet_id(prophet_id: str) -> Dict[str, Any]:
    if not _PROPHET_ID_RE.match(prophet_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_prophet_id",
                "message_en": "Invalid prophet_id format",
                "message_ar": "معرّف النبي غير صالح",
            },
        )
    idx = _profile_index()
    if prophet_id not in idx:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "prophet_not_found",
                "message_en": f"Prophet not found: {prophet_id}",
                "message_ar": "النبي غير موجود في الأطلس",
            },
        )
    return idx[prophet_id]


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------


class ProphetSummary(BaseModel):
    prophetId: str
    nameArabic: str
    nameEnglish: str
    transliteration: str
    quranMentionCount: int
    surahCount: int
    explicitMentionCount: int
    contextualMentionCount: int
    storyIdCount: int
    relatedProphetCount: int
    reviewStatus: str
    humanReviewRequired: bool


class ProphetListResponse(BaseModel):
    total: int
    prophets: List[ProphetSummary]


class ProphetAyahLink(BaseModel):
    surahNumber: int
    ayahNumber: int
    linkType: str
    confidence: float
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str] = Field(default_factory=list)


class ProphetRelation(BaseModel):
    sourceProphetId: str
    targetProphetId: str
    relationType: str
    evidenceReferences: List[Dict[str, Any]]
    explanationArabic: Optional[str] = None
    explanationEnglish: Optional[str] = None
    confidence: float
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str] = Field(default_factory=list)


class ProphetJourneyStage(BaseModel):
    stageId: str
    orderIndex: int
    labelArabic: str
    labelEnglish: str
    ayahReferences: List[Dict[str, Any]]
    relatedEntities: List[str]
    relatedTopics: List[str]
    storytellingArabic: Optional[str] = None
    storytellingEnglish: Optional[str] = None
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str] = Field(default_factory=list)


class ProphetJourney(BaseModel):
    journeyId: str
    prophetId: str
    journeyType: str
    titleArabic: str
    titleEnglish: str
    stages: List[ProphetJourneyStage]
    certainty: str
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str] = Field(default_factory=list)


class ProphetProfileResponse(BaseModel):
    prophetId: str
    nameArabic: str
    nameEnglish: str
    transliteration: str
    aliasesArabic: List[str]
    aliasesEnglish: List[str]
    quranMentionCount: int
    surahCount: int
    explicitMentions: List[ProphetAyahLink]
    contextualMentions: List[ProphetAyahLink]
    coreferenceMentions: List[ProphetAyahLink]
    storyIds: List[str]
    relatedEntities: List[str]
    relatedPeopleOrNations: List[str]
    relatedPlaces: List[str]
    relatedAnimals: List[str]
    relatedObjects: List[str]
    relatedEvents: List[str]
    relatedTopics: List[str]
    relatedProphets: List[ProphetRelation]
    journeys: List[ProphetJourney]
    storytellingSummaryArabic: Optional[str] = None
    storytellingSummaryEnglish: Optional[str] = None
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str] = Field(default_factory=list)


class ProphetAyahsResponse(BaseModel):
    prophetId: str
    total: int
    explicit: List[ProphetAyahLink]
    contextual: List[ProphetAyahLink]
    coreference: List[ProphetAyahLink]


class ProphetStoriesResponse(BaseModel):
    prophetId: str
    storyIds: List[str]


class ProphetRelationsResponse(BaseModel):
    prophetId: str
    total: int
    relations: List[ProphetRelation]


# ---------------------------------------------------------------------------
# Storytelling request / response
# ---------------------------------------------------------------------------


class StorytellingAyahRefIn(BaseModel):
    surahNumber: int
    ayahStart: int
    ayahEnd: Optional[int] = None

    @field_validator("surahNumber")
    @classmethod
    def _v_surah(cls, v: int) -> int:
        if not (1 <= v <= 114):
            raise ValueError("surahNumber out of range")
        return v

    @field_validator("ayahStart")
    @classmethod
    def _v_start(cls, v: int) -> int:
        if v < 1:
            raise ValueError("ayahStart must be ≥ 1")
        return v


class StorytellingRequest(BaseModel):
    journeyType: str = "mushaf_order"
    ayahReferences: List[StorytellingAyahRefIn]
    relatedEntityIds: List[str] = Field(default_factory=list)
    relatedTopicIds: List[str] = Field(default_factory=list)
    sourceIds: List[str] = Field(default_factory=list)
    language: str = "en"

    @field_validator("language")
    @classmethod
    def _v_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v

    @field_validator("journeyType")
    @classmethod
    def _v_journey(cls, v: str) -> str:
        if v not in {
            "mushaf_order",
            "story_world_order",
            "revelation_order",
            "thematic_order",
            "learning_order",
        }:
            raise ValueError("Invalid journeyType")
        return v


class StorytellingStageOut(BaseModel):
    stageId: str
    explanationArabic: str
    explanationEnglish: str
    ayahReferences: List[Dict[str, Any]]
    sourceEvidence: List[str]
    warnings: List[str]
    reviewStatus: str


class StorytellingResponse(BaseModel):
    summaryArabic: str
    summaryEnglish: str
    stages: List[StorytellingStageOut]
    followUpQuestionsArabic: List[str]
    followUpQuestionsEnglish: List[str]
    relatedStories: List[str]
    relatedProphets: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


# ---------------------------------------------------------------------------
# Explain-relation request / response
# ---------------------------------------------------------------------------


class ExplainRelationAyahRef(BaseModel):
    surahNumber: int
    ayahStart: int
    ayahEnd: Optional[int] = None

    @field_validator("surahNumber")
    @classmethod
    def _v_surah(cls, v: int) -> int:
        if not (1 <= v <= 114):
            raise ValueError("surahNumber out of range")
        return v


class ExplainRelationRequest(BaseModel):
    sourceProphetId: str
    targetProphetId: str
    relationType: str
    ayahReferences: List[ExplainRelationAyahRef] = Field(default_factory=list)
    sourceIds: List[str] = Field(default_factory=list)
    language: str = "en"

    @field_validator("sourceProphetId", "targetProphetId")
    @classmethod
    def _v_pid(cls, v: str) -> str:
        if not _PROPHET_ID_RE.match(v):
            raise ValueError("Invalid prophet_id")
        return v

    @field_validator("language")
    @classmethod
    def _v_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v


class ExplainRelationResponse(BaseModel):
    explanationArabic: str
    explanationEnglish: str
    evidenceReferences: List[Dict[str, Any]]
    tafsirEvidence: List[Dict[str, str]]
    warnings: List[str]
    reviewStatus: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class ProphetStoryReferenceOut(BaseModel):
    surahNumber: int
    ayahStart: int
    ayahEnd: Optional[int] = None
    linkType: str
    confidence: float
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool


class ProphetStorySectionOut(BaseModel):
    sectionId: str
    labelArabic: str
    labelEnglish: str
    ayahReferences: List[Dict[str, Any]]
    sectionType: str
    summaryArabic: Optional[str] = None
    summaryEnglish: Optional[str] = None
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class ProphetChronologyNoteOut(BaseModel):
    chronologyType: str
    noteArabic: str
    noteEnglish: str
    certainty: str
    sourceIds: List[str]
    reviewStatus: str


class ProphetStoryPageOut(BaseModel):
    storyPageId: str
    prophetId: str
    titleArabic: str
    titleEnglish: str
    pageType: str
    quranReferences: List[ProphetStoryReferenceOut]
    storySections: List[ProphetStorySectionOut]
    relatedProphets: List[str]
    relatedFigures: List[str]
    relatedPlaces: List[str]
    relatedNations: List[str]
    relatedObjects: List[str]
    relatedTopics: List[str]
    chronologyNotes: List[ProphetChronologyNoteOut]
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class ProphetContextualLinkOut(BaseModel):
    prophetId: str
    surahNumber: int
    ayahNumber: int
    linkType: str
    confidence: float
    evidenceReferences: List[Dict[str, Any]]
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    rationale: str
    warnings: List[str]


class ProphetContextualLinksResponse(BaseModel):
    prophetId: str
    total: int
    links: List[ProphetContextualLinkOut]


class ProphetMissingCoverageEntry(BaseModel):
    prophetId: str
    nameEnglish: str
    pageType: Optional[str] = None
    hasStoryPage: bool
    storyIdCount: int
    explicitMentionCount: int
    warnings: List[str]


class ProphetMissingCoverageResponse(BaseModel):
    total: int
    coverage: List[ProphetMissingCoverageEntry]


@router.get(
    "/prophets/missing-coverage", response_model=ProphetMissingCoverageResponse
)
def get_missing_coverage(response: Response) -> ProphetMissingCoverageResponse:
    """
    Per-prophet coverage status: has a story page? what type?
    Declared BEFORE the dynamic ``/prophets/{prophet_id}`` routes so the
    static path wins the match.
    """
    profiles = _load_atlas()["profiles"]
    pages = _story_page_index()
    out: List[ProphetMissingCoverageEntry] = []
    for p in profiles:
        sp = pages.get(p["prophetId"])
        out.append(
            ProphetMissingCoverageEntry(
                prophetId=p["prophetId"],
                nameEnglish=p["nameEnglish"],
                pageType=(sp or {}).get("pageType"),
                hasStoryPage=bool(sp),
                storyIdCount=len(p.get("storyIds", [])),
                explicitMentionCount=len(p.get("explicitMentions", [])),
                warnings=p.get("warnings", []),
            )
        )
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetMissingCoverageResponse(total=len(out), coverage=out)


@router.post("/prophets/explain-relation", response_model=ExplainRelationResponse)
def post_explain_relation(payload: ExplainRelationRequest) -> ExplainRelationResponse:
    """
    Explain why two prophets are related. Observational only — never tafsir.
    Declared BEFORE the dynamic ``/prophets/{prophet_id}`` routes so the
    static path wins the match.
    """
    if payload.relationType not in PROPHET_RELATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_relation_type",
                "message_en": f"relationType must be one of {sorted(PROPHET_RELATION_TYPES)}",
                "message_ar": "نوع العلاقة غير صالح",
            },
        )

    inp = ExplainProphetRelationInput(
        source_prophet_id=payload.sourceProphetId,
        target_prophet_id=payload.targetProphetId,
        relation_type=payload.relationType,
        ayah_references=[
            AyahRef(
                surah_number=r.surahNumber,
                ayah_start=r.ayahStart,
                ayah_end=r.ayahEnd,
            )
            for r in payload.ayahReferences
        ],
        source_ids=payload.sourceIds,
        language=payload.language,  # type: ignore[arg-type]
    )
    result = explain_prophet_relation(inp)
    return ExplainRelationResponse(
        explanationArabic=result.explanation_arabic,
        explanationEnglish=result.explanation_english,
        evidenceReferences=[
            {
                "surahNumber": r.surah_number,
                "ayahStart": r.ayah_start,
                "ayahEnd": r.ayah_end,
            }
            for r in result.evidence_references
        ],
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


@router.get("/prophets", response_model=ProphetListResponse)
def list_prophets(response: Response) -> ProphetListResponse:
    """List the canonical 25 prophets."""
    profiles = _load_atlas()["profiles"]
    items = [
        ProphetSummary(
            prophetId=p["prophetId"],
            nameArabic=p["nameArabic"],
            nameEnglish=p["nameEnglish"],
            transliteration=p["transliteration"],
            quranMentionCount=p["quranMentionCount"],
            surahCount=p["surahCount"],
            explicitMentionCount=len(p["explicitMentions"]),
            contextualMentionCount=len(p["contextualMentions"]),
            storyIdCount=len(p["storyIds"]),
            relatedProphetCount=len(p["relatedProphets"]),
            reviewStatus=p["reviewStatus"],
            humanReviewRequired=p["humanReviewRequired"],
        )
        for p in profiles
    ]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetListResponse(total=len(items), prophets=items)


@router.get("/prophets/{prophet_id}", response_model=ProphetProfileResponse)
def get_prophet(
    response: Response,
    prophet_id: str = FPath(..., description="Prophet ID"),
) -> ProphetProfileResponse:
    profile = _validate_prophet_id(prophet_id)
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetProfileResponse(**profile)


@router.get("/prophets/{prophet_id}/ayahs", response_model=ProphetAyahsResponse)
def get_prophet_ayahs(
    response: Response,
    prophet_id: str = FPath(...),
    link_type: Optional[str] = Query(None, description="Filter by linkType"),
) -> ProphetAyahsResponse:
    profile = _validate_prophet_id(prophet_id)
    explicit = profile.get("explicitMentions", [])
    contextual = profile.get("contextualMentions", [])
    coref = profile.get("coreferenceMentions", [])
    if link_type:
        explicit = [m for m in explicit if m["linkType"] == link_type]
        contextual = [m for m in contextual if m["linkType"] == link_type]
        coref = [m for m in coref if m["linkType"] == link_type]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetAyahsResponse(
        prophetId=prophet_id,
        total=len(explicit) + len(contextual) + len(coref),
        explicit=[ProphetAyahLink(**m) for m in explicit],
        contextual=[ProphetAyahLink(**m) for m in contextual],
        coreference=[ProphetAyahLink(**m) for m in coref],
    )


@router.get("/prophets/{prophet_id}/stories", response_model=ProphetStoriesResponse)
def get_prophet_stories(
    response: Response,
    prophet_id: str = FPath(...),
) -> ProphetStoriesResponse:
    profile = _validate_prophet_id(prophet_id)
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetStoriesResponse(
        prophetId=prophet_id, storyIds=profile.get("storyIds", [])
    )


@router.get("/prophets/{prophet_id}/relations", response_model=ProphetRelationsResponse)
def get_prophet_relations(
    response: Response,
    prophet_id: str = FPath(...),
    relation_type: Optional[str] = Query(None),
    target_prophet_id: Optional[str] = Query(None),
) -> ProphetRelationsResponse:
    profile = _validate_prophet_id(prophet_id)
    rels = profile.get("relatedProphets", [])
    if relation_type:
        rels = [r for r in rels if r["relationType"] == relation_type]
    if target_prophet_id:
        if not _PROPHET_ID_RE.match(target_prophet_id):
            raise HTTPException(status_code=400, detail={"error_code": "invalid_target_prophet_id"})
        rels = [r for r in rels if r["targetProphetId"] == target_prophet_id]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetRelationsResponse(
        prophetId=prophet_id, total=len(rels), relations=[ProphetRelation(**r) for r in rels]
    )


@router.get("/prophets/{prophet_id}/journey", response_model=ProphetJourney)
def get_prophet_journey(
    response: Response,
    prophet_id: str = FPath(...),
    order: str = Query("mushaf", description="mushaf | story_world | revelation | thematic | learning"),
) -> ProphetJourney:
    profile = _validate_prophet_id(prophet_id)
    if order not in _VALID_ORDERS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_order",
                "message_en": f"order must be one of {sorted(_VALID_ORDERS)}",
                "message_ar": "قيمة order غير صالحة",
            },
        )
    target = _ORDER_TO_JOURNEY[order]
    for j in profile.get("journeys", []):
        if j["journeyType"] == target:
            response.headers["Cache-Control"] = _CACHE_HEADER
            return ProphetJourney(**j)
    raise HTTPException(
        status_code=404,
        detail={
            "error_code": "journey_not_built",
            "message_en": f"Journey '{order}' not built for prophet '{prophet_id}'.",
            "message_ar": "لا توجد رحلة لهذا النبي بهذا الترتيب.",
        },
    )


@router.post(
    "/prophets/{prophet_id}/storytelling", response_model=StorytellingResponse
)
def post_prophet_storytelling(
    prophet_id: str = FPath(...),
    payload: StorytellingRequest = ...,
) -> StorytellingResponse:
    _validate_prophet_id(prophet_id)
    inp = ProphetStorytellingInput(
        prophet_id=prophet_id,
        journey_type=payload.journeyType,  # type: ignore[arg-type]
        ayah_references=[
            StorytellingAyahRef(
                surah_number=r.surahNumber,
                ayah_start=r.ayahStart,
                ayah_end=r.ayahEnd,
            )
            for r in payload.ayahReferences
        ],
        related_entity_ids=payload.relatedEntityIds,
        related_topic_ids=payload.relatedTopicIds,
        source_ids=payload.sourceIds,
        language=payload.language,  # type: ignore[arg-type]
    )
    result = build_prophet_storytelling(inp)
    return StorytellingResponse(
        summaryArabic=result.summary_arabic,
        summaryEnglish=result.summary_english,
        stages=[
            StorytellingStageOut(
                stageId=s.stage_id,
                explanationArabic=s.explanation_arabic,
                explanationEnglish=s.explanation_english,
                ayahReferences=[
                    {
                        "surahNumber": ar.surah_number,
                        "ayahStart": ar.ayah_start,
                        "ayahEnd": ar.ayah_end,
                    }
                    for ar in s.ayah_references
                ],
                sourceEvidence=s.source_evidence,
                warnings=s.warnings,
                reviewStatus=s.review_status,
            )
            for s in result.stages
        ],
        followUpQuestionsArabic=result.follow_up_questions_arabic,
        followUpQuestionsEnglish=result.follow_up_questions_english,
        relatedStories=result.related_stories,
        relatedProphets=result.related_prophets,
        reviewStatus=result.review_status,
        humanReviewRequired=result.human_review_required,
        warnings=result.warnings,
    )


# ===========================================================================
# Phase X2 — Story page, contextual links, and storytelling-safe endpoints
# ===========================================================================


@router.get(
    "/prophets/{prophet_id}/story-page", response_model=ProphetStoryPageOut
)
def get_prophet_story_page(
    response: Response,
    prophet_id: str = FPath(..., description="Prophet ID"),
) -> ProphetStoryPageOut:
    _validate_prophet_id(prophet_id)
    pages = _story_page_index()
    page = pages.get(prophet_id)
    if page is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "story_page_not_built",
                "message_en": (
                    f"No story page is built for prophet '{prophet_id}'. "
                    "Run scripts/build-missing-prophet-story-pages.ts or "
                    "register the prophet under a curated story."
                ),
                "message_ar": "لا توجد صفحة قصة لهذا النبي.",
            },
        )
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetStoryPageOut(**page)


@router.get(
    "/prophets/{prophet_id}/contextual-links",
    response_model=ProphetContextualLinksResponse,
)
def get_prophet_contextual_links(
    response: Response,
    prophet_id: str = FPath(...),
    link_type: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> ProphetContextualLinksResponse:
    _validate_prophet_id(prophet_id)
    links = _load_contextual_links().get("links", [])
    items = [l for l in links if l["prophetId"] == prophet_id]
    if link_type:
        items = [l for l in items if l["linkType"] == link_type]
    items = items[:limit]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return ProphetContextualLinksResponse(
        prophetId=prophet_id,
        total=len(items),
        links=[ProphetContextualLinkOut(**l) for l in items],
    )


class StorytellingSafeResponse(StorytellingResponse):
    outputMode: str = "no_verified_source"
    followUpActions: List[str] = Field(default_factory=list)


@router.post(
    "/prophets/{prophet_id}/storytelling-safe",
    response_model=StorytellingSafeResponse,
)
def post_prophet_storytelling_safe(
    prophet_id: str = FPath(...),
    payload: StorytellingRequest = ...,
) -> StorytellingSafeResponse:
    """
    Safer variant of the storytelling endpoint: surfaces the
    ``outputMode`` (one of the 4 Phase X2 modes) and the follow-up
    action keys so the UI can render targeted buttons.
    """
    _validate_prophet_id(prophet_id)
    inp = ProphetStorytellingInput(
        prophet_id=prophet_id,
        journey_type=payload.journeyType,  # type: ignore[arg-type]
        ayah_references=[
            StorytellingAyahRef(
                surah_number=r.surahNumber,
                ayah_start=r.ayahStart,
                ayah_end=r.ayahEnd,
            )
            for r in payload.ayahReferences
        ],
        related_entity_ids=payload.relatedEntityIds,
        related_topic_ids=payload.relatedTopicIds,
        source_ids=payload.sourceIds,
        language=payload.language,  # type: ignore[arg-type]
    )
    result = build_prophet_storytelling(inp)
    return StorytellingSafeResponse(
        summaryArabic=result.summary_arabic,
        summaryEnglish=result.summary_english,
        stages=[
            StorytellingStageOut(
                stageId=s.stage_id,
                explanationArabic=s.explanation_arabic,
                explanationEnglish=s.explanation_english,
                ayahReferences=[
                    {
                        "surahNumber": ar.surah_number,
                        "ayahStart": ar.ayah_start,
                        "ayahEnd": ar.ayah_end,
                    }
                    for ar in s.ayah_references
                ],
                sourceEvidence=s.source_evidence,
                warnings=s.warnings,
                reviewStatus=s.review_status,
            )
            for s in result.stages
        ],
        followUpQuestionsArabic=result.follow_up_questions_arabic,
        followUpQuestionsEnglish=result.follow_up_questions_english,
        relatedStories=result.related_stories,
        relatedProphets=result.related_prophets,
        reviewStatus=result.review_status,
        humanReviewRequired=result.human_review_required,
        warnings=result.warnings,
        outputMode=result.output_mode,
        followUpActions=result.follow_up_actions,
    )

