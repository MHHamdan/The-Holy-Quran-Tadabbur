"""
Quranic Calls Atlas API — Phase Y

Serves the pre-generated atlas data (scan + classify + graph JSON files).
No Quran text is generated, modified, or inferred here.
All caller/function/tone fields carry reviewStatus=needs_review.
"""

from __future__ import annotations

import json
import math
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# ─── Data loading (cached) ─────────────────────────────────────────────────────

FRONTEND_SRC = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "src" / "data" / "generated"

ATLAS_PATH = FRONTEND_SRC / "quranicCallsAtlas.json"
CLASSIFIED_PATH = FRONTEND_SRC / "quranicCallsClassified.json"
GRAPH_PATH = FRONTEND_SRC / "quranicCallRelationGraph.json"


@lru_cache(maxsize=1)
def _load_atlas() -> dict[str, Any]:
    if not ATLAS_PATH.exists():
        return {"calls": [], "statistics": {}, "totalCalls": 0, "totalAyahsWithCalls": 0}
    return json.loads(ATLAS_PATH.read_text("utf-8"))


@lru_cache(maxsize=1)
def _load_classified() -> dict[str, Any]:
    if not CLASSIFIED_PATH.exists():
        return {"calls": [], "totalClassified": 0, "classificationSummary": {}}
    return json.loads(CLASSIFIED_PATH.read_text("utf-8"))


@lru_cache(maxsize=1)
def _load_graph() -> dict[str, Any]:
    if not GRAPH_PATH.exists():
        return {"nodes": [], "edges": [], "totalNodes": 0, "totalEdges": 0}
    return json.loads(GRAPH_PATH.read_text("utf-8"))


def _calls_list() -> list[dict[str, Any]]:
    classified = _load_classified()
    if classified["calls"]:
        return classified["calls"]
    return _load_atlas()["calls"]


# ─── Pydantic response models ──────────────────────────────────────────────────

class CallerInfo(BaseModel):
    callerType: str
    callerEntityId: Optional[str] = None
    labelArabic: Optional[str] = None
    labelEnglish: Optional[str] = None
    confidence: float
    reviewStatus: str


class AddresseeInfo(BaseModel):
    addresseeType: str
    entityId: Optional[str] = None
    labelArabic: str
    labelEnglish: str
    confidence: float
    reviewStatus: str


class QuranicCallItem(BaseModel):
    callId: str
    surahNumber: int
    ayahNumber: int
    ayahReference: str
    surahNameAr: str
    surahNameEn: str
    ayahTextUthmani: str
    callText: Optional[str] = None
    callPattern: str
    caller: CallerInfo
    addressee: AddresseeInfo
    callFunction: str
    tone: str
    relatedTopics: list[str]
    relatedProphets: list[str]
    confidence: float
    reviewStatus: str
    humanReviewRequired: bool
    warnings: list[str]
    classificationMethod: Optional[str] = None


class PagedCallsResponse(BaseModel):
    items: list[QuranicCallItem]
    total: int
    page: int
    pageSize: int
    totalPages: int
    latency_ms: float


class StatisticsResponse(BaseModel):
    totalCalls: int
    totalAyahsWithCalls: int
    directYaCalls: int
    supplicationCalls: int
    indirectCalls: int
    needsReview: int
    verified: int
    byPattern: dict[str, int]
    byAddresseeType: dict[str, int]
    byCallerType: dict[str, int]
    topSurahs: list[dict]
    bySurah: dict[int, int]
    latency_ms: float


class GraphResponse(BaseModel):
    totalNodes: int
    totalEdges: int
    nodes: list[dict]
    edges: list[dict]
    summary: dict
    latency_ms: float


# ─── Helpers ───────────────────────────────────────────────────────────────────

_ARABIC_DIACRITIC_RE = re.compile(
    r"[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ]"
)


def _strip(text: str) -> str:
    return _ARABIC_DIACRITIC_RE.sub("", text)


def _to_item(c: dict) -> QuranicCallItem:
    return QuranicCallItem(
        callId=c["callId"],
        surahNumber=c["surahNumber"],
        ayahNumber=c["ayahNumber"],
        ayahReference=c["ayahReference"],
        surahNameAr=c["surahNameAr"],
        surahNameEn=c["surahNameEn"],
        ayahTextUthmani=c["ayahTextUthmani"],
        callText=c.get("callText"),
        callPattern=c["callPattern"],
        caller=CallerInfo(**c["caller"]),
        addressee=AddresseeInfo(**c["addressee"]),
        callFunction=c.get("callFunction", "needs_review"),
        tone=c.get("tone", "needs_review"),
        relatedTopics=c.get("relatedTopics", []),
        relatedProphets=c.get("relatedProphets", []),
        confidence=c.get("confidence", 0.0),
        reviewStatus=c.get("reviewStatus", "needs_review"),
        humanReviewRequired=c.get("humanReviewRequired", True),
        warnings=c.get("warnings", []),
        classificationMethod=c.get("classificationMethod"),
    )


def _paginate(items: list, page: int, page_size: int) -> tuple[list, int, int]:
    total = len(items)
    total_pages = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return items[start : start + page_size], total, total_pages


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/list", response_model=PagedCallsResponse)
async def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    call_pattern: Optional[str] = Query(None),
    addressee_type: Optional[str] = Query(None),
    caller_type: Optional[str] = Query(None),
    call_function: Optional[str] = Query(None),
    tone: Optional[str] = Query(None),
    surah: Optional[int] = Query(None, ge=1, le=114),
    review_status: Optional[str] = Query(None),
    direct_only: bool = Query(False),
):
    """List all detected Quranic calls with optional filters and pagination."""
    t0 = time.monotonic()
    calls = _calls_list()

    DIRECT_PATTERNS = {
        "ya_direct", "ya_ayyuhal", "ya_ayatuha", "ya_bani", "ya_qawmi",
        "ya_ibadi", "ya_ahl", "ya_rabbi", "ya_abati", "ya_bunayya",
        "ya_prophet_name", "ya_lament", "ya_wish",
    }

    filtered = [
        c for c in calls
        if (call_pattern is None or c["callPattern"] == call_pattern)
        and (addressee_type is None or c["addressee"]["addresseeType"] == addressee_type)
        and (caller_type is None or c["caller"]["callerType"] == caller_type)
        and (call_function is None or c.get("callFunction") == call_function)
        and (tone is None or c.get("tone") == tone)
        and (surah is None or c["surahNumber"] == surah)
        and (review_status is None or c.get("reviewStatus") == review_status)
        and (not direct_only or c["callPattern"] in DIRECT_PATTERNS)
    ]

    page_items, total, total_pages = _paginate(filtered, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/detail/{call_id}", response_model=QuranicCallItem)
async def get_call_detail(call_id: str):
    """Get a single call by its callId."""
    if not re.fullmatch(r"call_\d+_\d+_\d+", call_id):
        raise HTTPException(status_code=400, detail="Invalid call_id format")
    for c in _calls_list():
        if c["callId"] == call_id:
            return _to_item(c)
    raise HTTPException(status_code=404, detail=f"Call {call_id!r} not found")


@router.get("/by-surah/{surah_number}", response_model=PagedCallsResponse)
async def calls_by_surah(
    surah_number: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Get all calls for a specific surah."""
    if not (1 <= surah_number <= 114):
        raise HTTPException(status_code=400, detail="surah_number must be 1–114")
    t0 = time.monotonic()
    calls = [c for c in _calls_list() if c["surahNumber"] == surah_number]
    page_items, total, total_pages = _paginate(calls, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/by-audience/{addressee_type}", response_model=PagedCallsResponse)
async def calls_by_audience(
    addressee_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    """Get all calls by addressee type (e.g. believers, mankind, prophet)."""
    VALID = {
        "believers", "mankind", "disbelievers", "people_of_book", "bani_israel",
        "prophet", "specific_person", "people_or_nation", "family_member",
        "soul", "jinn", "allah", "unknown",
    }
    if addressee_type not in VALID:
        raise HTTPException(status_code=400, detail=f"Unknown addressee_type: {addressee_type!r}")
    t0 = time.monotonic()
    calls = [c for c in _calls_list() if c["addressee"]["addresseeType"] == addressee_type]
    page_items, total, total_pages = _paginate(calls, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/by-caller/{caller_type}", response_model=PagedCallsResponse)
async def calls_by_caller(
    caller_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    """Get all calls by caller type."""
    VALID = {
        "allah", "prophet", "angel", "believer", "disbeliever",
        "people_group", "family_member", "jinn", "narrative_speaker", "unknown",
    }
    if caller_type not in VALID:
        raise HTTPException(status_code=400, detail=f"Unknown caller_type: {caller_type!r}")
    t0 = time.monotonic()
    calls = [c for c in _calls_list() if c["caller"]["callerType"] == caller_type]
    page_items, total, total_pages = _paginate(calls, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/by-function/{call_function}", response_model=PagedCallsResponse)
async def calls_by_function(
    call_function: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    """Get all calls by call function."""
    t0 = time.monotonic()
    calls = [c for c in _calls_list() if c.get("callFunction") == call_function]
    page_items, total, total_pages = _paginate(calls, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/search", response_model=PagedCallsResponse)
async def search_calls(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """Search calls by query string (matches against stripped ayah text and surah names)."""
    t0 = time.monotonic()
    q_stripped = _strip(q).strip()
    if not q_stripped:
        raise HTTPException(status_code=400, detail="Query must contain non-diacritic text")
    results = [
        c for c in _calls_list()
        if q_stripped in _strip(c.get("ayahTextUthmani", ""))
        or q_stripped.lower() in c.get("surahNameEn", "").lower()
        or q_stripped in c.get("surahNameAr", "")
        or q_stripped in c.get("callPattern", "")
        or q_stripped in c["addressee"].get("labelArabic", "")
    ]
    page_items, total, total_pages = _paginate(results, page, page_size)
    return PagedCallsResponse(
        items=[_to_item(c) for c in page_items],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Atlas-level statistics: totals by pattern, addressee, caller, top surahs."""
    t0 = time.monotonic()
    atlas = _load_atlas()
    stats = atlas.get("statistics", {})
    # Build per-surah call count from the full calls list
    by_surah: dict[int, int] = {}
    for c in _calls_list():
        sn = c.get("surahNumber")
        if isinstance(sn, int):
            by_surah[sn] = by_surah.get(sn, 0) + 1

    return StatisticsResponse(
        totalCalls=atlas.get("totalCalls", 0),
        totalAyahsWithCalls=atlas.get("totalAyahsWithCalls", 0),
        directYaCalls=stats.get("directYaCalls", 0),
        supplicationCalls=stats.get("supplicationCalls", 0),
        indirectCalls=stats.get("indirectCalls", 0),
        needsReview=stats.get("needsReview", 0),
        verified=stats.get("verified", 0),
        byPattern=stats.get("byPattern", {}),
        byAddresseeType=stats.get("byAddresseeType", {}),
        byCallerType=stats.get("byCallerType", {}),
        topSurahs=stats.get("topSurahs", []),
        bySurah=by_surah,
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/graph", response_model=GraphResponse)
async def get_relation_graph(
    max_nodes: int = Query(300, ge=10, le=1000),
    node_type: Optional[str] = Query(None),
):
    """Return the relation graph (optionally filtered by node type, capped at max_nodes)."""
    t0 = time.monotonic()
    graph = _load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if node_type:
        allowed_ids = {n["nodeId"] for n in nodes if n.get("nodeType") == node_type}
        nodes = [n for n in nodes if n["nodeId"] in allowed_ids]
        edges = [e for e in edges if e["sourceId"] in allowed_ids or e["targetId"] in allowed_ids]

    # Cap node count for response size
    if len(nodes) > max_nodes:
        kept_ids = {n["nodeId"] for n in nodes[:max_nodes]}
        nodes = nodes[:max_nodes]
        edges = [e for e in edges if e["sourceId"] in kept_ids and e["targetId"] in kept_ids]

    return GraphResponse(
        totalNodes=graph.get("totalNodes", 0),
        totalEdges=graph.get("totalEdges", 0),
        nodes=nodes,
        edges=edges,
        summary=graph.get("summary", {}),
        latency_ms=round((time.monotonic() - t0) * 1000, 2),
    )


@router.get("/explain/{call_id}")
async def explain_call(call_id: str):
    """
    Plain-language explanation of a specific call.

    IMPORTANT: This endpoint provides only pattern-based information.
    No tafsir or theological meaning is generated here.
    For tafsir content, use the /tafsir endpoint with the ayah reference.
    """
    if not re.fullmatch(r"call_\d+_\d+_\d+", call_id):
        raise HTTPException(status_code=400, detail="Invalid call_id format")

    call = next((c for c in _calls_list() if c["callId"] == call_id), None)
    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id!r} not found")

    pattern_descriptions = {
        "ya_ayyuhal":      "يا أيها — formal address to a group (masculine)",
        "ya_ayatuha":      "يا أيتها — formal address to a group (feminine)",
        "ya_bani":         "يا بني — address to a lineage or community",
        "ya_qawmi":        "يا قوم — address to a people or nation",
        "ya_ibadi":        "يا عبادي — Allah's address to His servants",
        "ya_ahl":          "يا أهل — address to a people of a place or scripture",
        "ya_rabbi":        "يا رب — supplicatory address to Allah",
        "ya_abati":        "يا أبت — address to a father",
        "ya_bunayya":      "يا بني — address to a dear son",
        "ya_prophet_name": "يا + prophet name — direct address to a prophet",
        "ya_lament":       "يا ويلتى / يا حسرة — exclamation of grief or lament",
        "ya_wish":         "يا ليت — rhetorical wish or regret",
        "ya_direct":       "يا — direct vocative address",
        "supplication":    "ربنا / ربي — supplication to Allah (without يا)",
        "indirect_address":"Inferred address — no explicit vocative detected",
        "dialogue_address":"Address within a Quranic narrative/dialogue",
        "unknown":         "Pattern undetermined — requires contextual review",
    }

    pattern_label = pattern_descriptions.get(call["callPattern"], call["callPattern"])

    return {
        "callId": call_id,
        "ayahReference": call["ayahReference"],
        "surahNameEn": call["surahNameEn"],
        "surahNameAr": call["surahNameAr"],
        "callPattern": call["callPattern"],
        "patternDescription": pattern_label,
        "addressee": call["addressee"],
        "caller": call["caller"],
        "callFunction": call.get("callFunction", "needs_review"),
        "tone": call.get("tone", "needs_review"),
        "confidence": call.get("confidence", 0.0),
        "reviewStatus": "needs_review",
        "humanReviewRequired": True,
        "disclaimer": (
            "This explanation is derived from pattern matching only. "
            "It is NOT a tafsir or religious ruling. "
            "All classifications require human scholarly review. "
            "For tafsir content, use the /tafsir endpoint with this ayah reference."
        ),
    }
