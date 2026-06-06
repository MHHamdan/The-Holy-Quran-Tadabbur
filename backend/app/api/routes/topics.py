"""
Quran Topic Discovery Atlas — API.

Endpoints:
    GET  /api/v1/quran/topics
    GET  /api/v1/quran/topics/{topic_id}
    GET  /api/v1/quran/topics/{topic_id}/ayahs
    GET  /api/v1/quran/topics/{topic_id}/related
    GET  /api/v1/quran/topics/{topic_id}/journey
    GET  /api/v1/quran/topics/surah/{surah_no}
    POST /api/v1/quran/topics/explain-link

Safety rules:
    - Responses NEVER include Quran text — only surah/ayah numbers.
    - Every record echoes reviewStatus and humanReviewRequired.
    - The explain-link endpoint composes deterministic, observational text
      only; if no trusted tafsir source is supplied, it returns the generic
      navigation explanation plus a `no_verified_source` warning.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path as FPath, Query, Response
from pydantic import BaseModel, Field, field_validator

from app.services.entity_connection_explainer import TRUSTED_TAFSIR_SOURCE_IDS

router = APIRouter()

# ---------------------------------------------------------------------------
# Files / cache
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_GENERATED_DIR = _REPO_ROOT / "frontend" / "src" / "data" / "generated"
_ATLAS_FILE = _GENERATED_DIR / "quranTopicAtlas.json"
_CLUSTERS_FILE = _GENERATED_DIR / "quranTopicClusters.json"
_GRAPH_FILE = _GENERATED_DIR / "quranTopicRelationGraph.json"

_TOPIC_ID_RE = re.compile(r"^topic_[a-z0-9_]+$")
_CACHE_HEADER = "public, max-age=3600"

VALID_ORDERS = {"mushaf", "surah", "story", "entity", "emotional"}


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "data_not_built",
                "message_en": f"Generated file missing: {path.name}. Run the topic build scripts.",
                "message_ar": "ملف بيانات الموضوعات غير موجود؛ يجب تشغيل سكربتات البناء أولاً.",
            },
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_atlas() -> Dict[str, Any]:
    return _read_json(_ATLAS_FILE)


@lru_cache(maxsize=1)
def _load_clusters() -> Dict[str, Any]:
    return _read_json(_CLUSTERS_FILE)


@lru_cache(maxsize=1)
def _load_graph() -> Dict[str, Any]:
    return _read_json(_GRAPH_FILE)


def _topic_index() -> Dict[str, Dict[str, Any]]:
    data = _load_atlas()
    return {t["topicId"]: t for t in data["topics"]}


def _validate_topic_id(topic_id: str) -> None:
    if not _TOPIC_ID_RE.match(topic_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_topic_id",
                "message_en": "Invalid topic_id format",
                "message_ar": "معرّف الموضوع غير صالح",
            },
        )
    if topic_id not in _topic_index():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "topic_not_found",
                "message_en": f"Topic not found: {topic_id}",
                "message_ar": "الموضوع غير موجود",
            },
        )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TopicSummary(BaseModel):
    topicId: str
    topicType: str
    labelArabic: str
    labelEnglish: str
    ayahCount: int
    surahCount: int
    reviewStatus: str


class TopicListResponse(BaseModel):
    total: int
    topics: List[TopicSummary]


class TopicAyahLinkOut(BaseModel):
    surahNumber: int
    ayahNumber: int
    linkType: str
    confidence: float
    evidenceReferences: List[Dict[str, Any]]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]


class TopicDetailResponse(BaseModel):
    topicId: str
    topicType: str
    labelArabic: str
    labelEnglish: str
    aliasesArabic: List[str]
    aliasesEnglish: List[str]
    parentTopicId: Optional[str] = None
    childTopicIds: List[str]
    relatedTopicIds: List[str]
    relatedEntities: List[str]
    relatedStories: List[str]
    relatedThemes: List[str]
    relatedEmotions: List[str]
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]
    ayahCount: int
    surahCount: int


class TopicAyahsResponse(BaseModel):
    topicId: str
    total: int
    links: List[TopicAyahLinkOut]


class TopicRelatedOut(BaseModel):
    relatedTopicIds: List[str]
    relatedClusterIds: List[str]
    sharedEntityIds: List[str]
    sharedStoryIds: List[str]
    sharedEmotionIds: List[str]


class TopicJourneySection(BaseModel):
    sectionId: str
    labelArabic: str
    labelEnglish: str
    order: str
    ayahReferences: List[Dict[str, Any]]
    reviewStatus: str
    warnings: List[str]


class TopicJourneyResponse(BaseModel):
    topicId: str
    order: str
    sections: List[TopicJourneySection]
    reviewStatus: str
    warnings: List[str]


class SurahTopicEntry(BaseModel):
    topicId: str
    topicType: str
    labelArabic: str
    labelEnglish: str
    ayahCount: int
    ayahs: List[int]


class SurahTopicsResponse(BaseModel):
    surahNumber: int
    totalTopics: int
    topics: List[SurahTopicEntry]


class ExplainTopicLinkPayload(BaseModel):
    topicId: str
    surahNumber: int
    ayahNumber: int
    language: str = "en"
    sourceIds: List[str] = Field(default_factory=list)

    @field_validator("topicId")
    @classmethod
    def _v_topic(cls, v: str) -> str:
        if not _TOPIC_ID_RE.match(v):
            raise ValueError("Invalid topicId format")
        return v

    @field_validator("language")
    @classmethod
    def _v_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("language must be 'ar' or 'en'")
        return v

    @field_validator("surahNumber")
    @classmethod
    def _v_sura(cls, v: int) -> int:
        if v < 1 or v > 114:
            raise ValueError("surahNumber out of range")
        return v

    @field_validator("ayahNumber")
    @classmethod
    def _v_ayah(cls, v: int) -> int:
        if v < 1:
            raise ValueError("ayahNumber must be ≥1")
        return v


class ExplainTopicLinkResponse(BaseModel):
    explanationArabic: str
    explanationEnglish: str
    topicId: str
    surahNumber: int
    ayahNumber: int
    matchedLinkType: Optional[str] = None
    sourceIds: List[str]
    warnings: List[str]
    reviewStatus: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/topics", response_model=TopicListResponse)
def list_topics(
    response: Response,
    topic_type: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> TopicListResponse:
    data = _load_atlas()
    items: List[TopicSummary] = []
    for t in data["topics"]:
        if topic_type and t["topicType"] != topic_type:
            continue
        ayahs = t.get("ayahLinks", [])
        surahs = {l["surahNumber"] for l in ayahs}
        items.append(
            TopicSummary(
                topicId=t["topicId"],
                topicType=t["topicType"],
                labelArabic=t["labelArabic"],
                labelEnglish=t["labelEnglish"],
                ayahCount=len(ayahs),
                surahCount=len(surahs),
                reviewStatus=t.get("reviewStatus", "needs_review"),
            )
        )
    items.sort(key=lambda x: x.ayahCount, reverse=True)
    response.headers["Cache-Control"] = _CACHE_HEADER
    return TopicListResponse(total=len(items), topics=items[offset : offset + limit])


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse)
def get_topic(
    response: Response,
    topic_id: str = FPath(...),
) -> TopicDetailResponse:
    _validate_topic_id(topic_id)
    t = _topic_index()[topic_id]
    ayahs = t.get("ayahLinks", [])
    surahs = {l["surahNumber"] for l in ayahs}
    response.headers["Cache-Control"] = _CACHE_HEADER
    return TopicDetailResponse(
        topicId=t["topicId"],
        topicType=t["topicType"],
        labelArabic=t["labelArabic"],
        labelEnglish=t["labelEnglish"],
        aliasesArabic=t.get("aliasesArabic", []),
        aliasesEnglish=t.get("aliasesEnglish", []),
        parentTopicId=t.get("parentTopicId"),
        childTopicIds=t.get("childTopicIds", []),
        relatedTopicIds=t.get("relatedTopicIds", []),
        relatedEntities=t.get("relatedEntities", []),
        relatedStories=t.get("relatedStories", []),
        relatedThemes=t.get("relatedThemes", []),
        relatedEmotions=t.get("relatedEmotions", []),
        sourceIds=t.get("sourceIds", []),
        reviewStatus=t.get("reviewStatus", "needs_review"),
        humanReviewRequired=bool(t.get("humanReviewRequired", True)),
        warnings=t.get("warnings", []),
        ayahCount=len(ayahs),
        surahCount=len(surahs),
    )


@router.get("/topics/{topic_id}/ayahs", response_model=TopicAyahsResponse)
def get_topic_ayahs(
    response: Response,
    topic_id: str = FPath(...),
    link_type: Optional[str] = Query(None),
    surah: Optional[int] = Query(None, ge=1, le=114),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> TopicAyahsResponse:
    _validate_topic_id(topic_id)
    t = _topic_index()[topic_id]
    links = t.get("ayahLinks", [])
    if link_type:
        links = [l for l in links if l["linkType"] == link_type]
    if surah:
        links = [l for l in links if l["surahNumber"] == surah]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return TopicAyahsResponse(
        topicId=topic_id,
        total=len(links),
        links=[TopicAyahLinkOut(**l) for l in links[offset : offset + limit]],
    )


@router.get("/topics/{topic_id}/related", response_model=TopicRelatedOut)
def get_topic_related(
    response: Response,
    topic_id: str = FPath(...),
) -> TopicRelatedOut:
    _validate_topic_id(topic_id)
    graph = _load_graph()
    clusters = _load_clusters()
    related_topics: List[str] = []
    seen = set()
    for e in graph["edges"]:
        if e["edgeType"] != "TOPIC_RELATED_TO_TOPIC":
            continue
        src = e["sourceNodeId"]
        tgt = e["targetNodeId"]
        if src == f"topic:{topic_id}":
            other = tgt
        elif tgt == f"topic:{topic_id}":
            other = src
        else:
            continue
        if other.startswith("topic:"):
            other_id = other[len("topic:") :]
            if other_id not in seen:
                seen.add(other_id)
                related_topics.append(other_id)
    related_clusters = [
        c["clusterId"] for c in clusters["clusters"] if topic_id in c["memberTopicIds"]
    ]
    t = _topic_index()[topic_id]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return TopicRelatedOut(
        relatedTopicIds=related_topics[:50],
        relatedClusterIds=related_clusters[:50],
        sharedEntityIds=t.get("relatedEntities", []),
        sharedStoryIds=t.get("relatedStories", []),
        sharedEmotionIds=t.get("relatedEmotions", []),
    )


@router.get("/topics/{topic_id}/journey", response_model=TopicJourneyResponse)
def get_topic_journey(
    response: Response,
    topic_id: str = FPath(...),
    order: str = Query("mushaf", description="mushaf | surah | story | entity | emotional"),
) -> TopicJourneyResponse:
    _validate_topic_id(topic_id)
    if order not in VALID_ORDERS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_order",
                "message_en": f"order must be one of {sorted(VALID_ORDERS)}",
                "message_ar": "قيمة order غير صالحة",
            },
        )
    t = _topic_index()[topic_id]
    links: List[Dict[str, Any]] = t.get("ayahLinks", [])
    sections: List[TopicJourneySection] = []

    def to_refs(ls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"surahNumber": l["surahNumber"], "ayahStart": l["ayahNumber"]} for l in ls]

    if order in ("mushaf", "surah"):
        by_surah: Dict[int, List[Dict[str, Any]]] = {}
        for l in links:
            by_surah.setdefault(l["surahNumber"], []).append(l)
        for s in sorted(by_surah.keys()):
            sections.append(
                TopicJourneySection(
                    sectionId=f"journey:{topic_id}:surah{s}",
                    labelArabic=f"سورة رقم {s}",
                    labelEnglish=f"Surah {s}",
                    order=order,
                    ayahReferences=to_refs(by_surah[s]),
                    reviewStatus="needs_review",
                    warnings=[],
                )
            )
    elif order == "story":
        by_story: Dict[str, List[Dict[str, Any]]] = {}
        for l in links:
            for ev in l.get("evidenceReferences", []):
                if ev.get("evidenceType") in ("entity_graph", "kg_edge", "coreference", "story_data"):
                    by_story.setdefault("story_connections", []).append(l)
                    break
            else:
                by_story.setdefault("keyword_only", []).append(l)
        for k, ls in by_story.items():
            sections.append(
                TopicJourneySection(
                    sectionId=f"journey:{topic_id}:story:{k}",
                    labelArabic="روابط قصصية" if k == "story_connections" else "روابط لفظية فقط",
                    labelEnglish="Story-derived links" if k == "story_connections" else "Keyword-only links",
                    order=order,
                    ayahReferences=to_refs(ls),
                    reviewStatus="needs_review",
                    warnings=["Story-derived ordering is heuristic; needs_review."],
                )
            )
    elif order == "entity":
        entity_ids = t.get("relatedEntities", []) or ["__no_entity__"]
        sections.append(
            TopicJourneySection(
                sectionId=f"journey:{topic_id}:entity",
                labelArabic="رحلة عبر الذوات",
                labelEnglish="Journey via related entities",
                order=order,
                ayahReferences=to_refs(links),
                reviewStatus="needs_review",
                warnings=[f"Entities: {', '.join(entity_ids)}"],
            )
        )
    elif order == "emotional":
        emotions = t.get("relatedEmotions", []) or ["__no_emotion__"]
        sections.append(
            TopicJourneySection(
                sectionId=f"journey:{topic_id}:emotional",
                labelArabic="رحلة وجدانية",
                labelEnglish="Emotional reflection journey",
                order=order,
                ayahReferences=to_refs(links),
                reviewStatus="needs_review",
                warnings=[f"Related emotions: {', '.join(emotions)}"],
            )
        )
    response.headers["Cache-Control"] = _CACHE_HEADER
    return TopicJourneyResponse(
        topicId=topic_id,
        order=order,
        sections=sections,
        reviewStatus="needs_review",
        warnings=[
            "Topic journey is observational. No tafsir is generated.",
        ],
    )


@router.get("/topics/surah/{surah_no}", response_model=SurahTopicsResponse)
def get_topics_for_surah(
    response: Response,
    surah_no: int = FPath(..., ge=1, le=114),
    limit: int = Query(200, ge=1, le=500),
) -> SurahTopicsResponse:
    data = _load_atlas()
    entries: List[SurahTopicEntry] = []
    for t in data["topics"]:
        ayahs_in_surah = sorted({l["ayahNumber"] for l in t.get("ayahLinks", []) if l["surahNumber"] == surah_no})
        if not ayahs_in_surah:
            continue
        entries.append(
            SurahTopicEntry(
                topicId=t["topicId"],
                topicType=t["topicType"],
                labelArabic=t["labelArabic"],
                labelEnglish=t["labelEnglish"],
                ayahCount=len(ayahs_in_surah),
                ayahs=ayahs_in_surah,
            )
        )
    entries.sort(key=lambda x: x.ayahCount, reverse=True)
    response.headers["Cache-Control"] = _CACHE_HEADER
    return SurahTopicsResponse(
        surahNumber=surah_no,
        totalTopics=len(entries),
        topics=entries[:limit],
    )


@router.post("/topics/explain-link", response_model=ExplainTopicLinkResponse)
def post_explain_topic_link(payload: ExplainTopicLinkPayload) -> ExplainTopicLinkResponse:
    """
    Return a safe, source-aware explanation of why an ayah is linked to a
    topic. Composes deterministic observational text; if no trusted tafsir
    source is supplied, includes a `no_verified_source` warning. Always
    returns ``reviewStatus="needs_review"``.
    """
    if payload.topicId not in _topic_index():
        raise HTTPException(status_code=404, detail={"error_code": "topic_not_found"})
    t = _topic_index()[payload.topicId]
    matched = next(
        (
            l
            for l in t.get("ayahLinks", [])
            if l["surahNumber"] == payload.surahNumber and l["ayahNumber"] == payload.ayahNumber
        ),
        None,
    )
    trusted = [sid for sid in payload.sourceIds if sid in TRUSTED_TAFSIR_SOURCE_IDS]
    untrusted_dropped = [sid for sid in payload.sourceIds if sid not in TRUSTED_TAFSIR_SOURCE_IDS]
    warnings: List[str] = []
    if matched:
        warnings.extend(matched.get("warnings", []))
    if untrusted_dropped:
        warnings.append("Dropped untrusted source IDs: " + ", ".join(sorted(set(untrusted_dropped))))
    if not trusted:
        warnings.append(
            "no_verified_source: explanation is observational only. Detailed interpretation requires verified tafsir review."
        )
    warnings.append("All inferred topic links default to needs_review.")

    link_type = matched["linkType"] if matched else None
    en = (
        f"Ayah {payload.surahNumber}:{payload.ayahNumber} is linked to topic "
        f"'{t['labelEnglish']}' by the navigation pipeline ({link_type or 'no direct match'}). "
        "This link is observational; detailed interpretation requires verified tafsir review."
    )
    ar = (
        f"الآية {payload.surahNumber}:{payload.ayahNumber} مرتبطة بالموضوع "
        f"«{t['labelArabic']}» عبر تصنيف ملاحظ ({link_type or 'لا يوجد ربط مباشر'}). "
        "هذا الربط ملاحظ ولا يمثل تفسيرًا؛ وتفصيل المعنى يتطلب مصادر تفسيرية معتمدة."
    )
    return ExplainTopicLinkResponse(
        explanationArabic=ar,
        explanationEnglish=en,
        topicId=payload.topicId,
        surahNumber=payload.surahNumber,
        ayahNumber=payload.ayahNumber,
        matchedLinkType=link_type,
        sourceIds=trusted,
        warnings=warnings,
        reviewStatus="needs_review",
    )


__all__ = ["router"]
