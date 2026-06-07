"""
Surah Atlas Intelligence API

Serves structured metadata, summaries, structure sections, themes, rare words,
and memorization data for all 114 surahs.

Safety rules:
- All content is labeled with reviewStatus
- No AI-generated tafsir is returned without source attribution
- humanReviewRequired flag is always forwarded to the client
- Summaries are pedagogical placeholders until scholarly review

Endpoints:
  GET /surah-atlas                     — list all surah atlas entries (paginated)
  GET /surah-atlas/{surah}             — detail for a single surah
  GET /surah-atlas/{surah}/stories     — stories mentioned in a surah
  GET /surah-atlas/{surah}/rare-words  — rare words in a surah
  GET /surah-atlas/{surah}/memorization-links — memorization data for a surah
  GET /surah-atlas/search              — search surah atlas
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Any, Optional

router = APIRouter()

# ---------------------------------------------------------------------------
# Standard envelope helpers
# ---------------------------------------------------------------------------

_REVIEW_WARNING_EN = (
    "This surah atlas entry is pending scholarly review. "
    "Summaries are pedagogical placeholders and must not be taken as authoritative tafsir."
)
_REVIEW_WARNING_AR = (
    "هذا المدخل في أطلس السور قيد المراجعة العلمية. "
    "الملخصات نصوص تربوية مؤقتة ولا ينبغي اعتبارها تفسيراً موثوقاً."
)


def _envelope(
    data: Any,
    review_status: str = "needs_review",
    human_review_required: bool = True,
    warnings: list[str] | None = None,
) -> dict:
    return {
        "status": "ok",
        "data": data,
        "reviewStatus": review_status,
        "humanReviewRequired": human_review_required,
        "warnings": warnings or [_REVIEW_WARNING_EN],
        "warnings_ar": [_REVIEW_WARNING_AR],
    }


def _no_source_envelope(message_en: str = "No verified source available.") -> dict:
    return {
        "status": "no_verified_source",
        "data": None,
        "evidence": [],
        "warnings": [message_en, "This requires further scholarly review."],
        "warnings_ar": ["يحتاج هذا إلى مراجعة علمية إضافية."],
    }


# ---------------------------------------------------------------------------
# Static data loader — loads the frontend's surahAtlas data via JSON manifest
# The surah atlas lives in the frontend data layer.
# The backend serves as a proxy + cache layer for API consumers.
# ---------------------------------------------------------------------------

import json
import os
from functools import lru_cache

_SURAH_MEMORY_ATLAS_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../../frontend/src/data/generated/surahMemoryAtlas.json",
)


@lru_cache(maxsize=1)
def _load_surah_memory_atlas() -> dict:
    """Load the surah memory atlas JSON once and cache it."""
    path = os.path.normpath(_SURAH_MEMORY_ATLAS_PATH)
    if not os.path.exists(path):
        return {"surahs": [], "totalSurahs": 0}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_surah_memory_entry(surah_no: int) -> dict | None:
    atlas = _load_surah_memory_atlas()
    for s in atlas.get("surahs", []):
        if s.get("surahNumber") == surah_no:
            return s
    return None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class BilingualText(BaseModel):
    en: str
    ar: str


class SurahAtlasSummary(BaseModel):
    surahNumber: int
    nameArabic: str
    nameTransliteration: str
    nameEnglishMeaning: str
    revelationType: str
    ayahCount: int
    juzStart: int
    juzEnd: int
    mainTopicsEnglish: list[str] = []
    mainTopicsArabic: list[str] = []
    relatedStories: list[str] = []
    reviewStatus: str = "needs_review"
    humanReviewRequired: bool = True


class SurahAtlasDetail(SurahAtlasSummary):
    firstAyahPreview: Optional[str] = None
    lastAyahPreview: Optional[str] = None
    mainFigures: list[str] = []
    relatedThemes: list[str] = []
    sourceIds: list[str] = []
    summaryShortEn: str = ""
    summaryShortAr: str = ""


class SurahAtlasListResponse(BaseModel):
    status: str = "ok"
    data: list[SurahAtlasSummary]
    total: int
    offset: int
    limit: int
    reviewStatus: str = "needs_review"
    humanReviewRequired: bool = True
    warnings: list[str] = []


class SurahAtlasDetailResponse(BaseModel):
    status: str = "ok"
    data: SurahAtlasDetail
    reviewStatus: str = "needs_review"
    humanReviewRequired: bool = True
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------------------

def _memory_entry_to_summary(s: dict) -> SurahAtlasSummary:
    return SurahAtlasSummary(
        surahNumber=s["surahNumber"],
        nameArabic=s.get("nameArabic", ""),
        nameTransliteration=s.get("nameTransliteration", ""),
        nameEnglishMeaning=s.get("nameEnglish", ""),
        revelationType=s.get("revelationType", "unknown"),
        ayahCount=s.get("ayahCount", 0),
        juzStart=s.get("juzStart", 0),
        juzEnd=s.get("juzEnd", 0),
        mainTopicsEnglish=s.get("mainTopicsEnglish", []),
        mainTopicsArabic=s.get("mainTopicsArabic", []),
        relatedStories=s.get("relatedStories", []),
        reviewStatus=s.get("reviewStatus", "needs_review"),
        humanReviewRequired=True,
    )


def _memory_entry_to_detail(s: dict) -> SurahAtlasDetail:
    summary_short_en = (
        f"Summary for Surah {s.get('nameTransliteration', '')} requires scholarly review."
    )
    summary_short_ar = (
        f"يحتاج ملخص سورة {s.get('nameArabic', '')} إلى مراجعة علمية."
    )
    return SurahAtlasDetail(
        surahNumber=s["surahNumber"],
        nameArabic=s.get("nameArabic", ""),
        nameTransliteration=s.get("nameTransliteration", ""),
        nameEnglishMeaning=s.get("nameEnglish", ""),
        revelationType=s.get("revelationType", "unknown"),
        ayahCount=s.get("ayahCount", 0),
        juzStart=s.get("juzStart", 0),
        juzEnd=s.get("juzEnd", 0),
        mainTopicsEnglish=s.get("mainTopicsEnglish", []),
        mainTopicsArabic=s.get("mainTopicsArabic", []),
        relatedStories=s.get("relatedStories", []),
        firstAyahPreview=s.get("firstAyahPreview"),
        lastAyahPreview=s.get("lastAyahPreview"),
        mainFigures=s.get("mainFigures", []),
        relatedThemes=s.get("relatedThemes", []),
        sourceIds=s.get("sourceIds", []),
        summaryShortEn=summary_short_en,
        summaryShortAr=summary_short_ar,
        reviewStatus=s.get("reviewStatus", "needs_review"),
        humanReviewRequired=True,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=SurahAtlasListResponse)
async def list_surah_atlas(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(114, ge=1, le=114),
    revelation_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
):
    """
    List all 114 surah atlas entries with optional filtering.

    All entries carry reviewStatus='needs_review' until scholarly validation.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    atlas = _load_surah_memory_atlas()
    surahs = atlas.get("surahs", [])

    # Filter
    if revelation_type and revelation_type != "all":
        surahs = [s for s in surahs if s.get("revelationType") == revelation_type]
    if search:
        q = search.lower()
        surahs = [
            s for s in surahs
            if q in s.get("nameTransliteration", "").lower()
            or q in (s.get("nameEnglish") or "").lower()
            or any(q in t.lower() for t in s.get("mainTopicsEnglish", []))
        ]

    total = len(surahs)
    page = surahs[offset: offset + limit]

    return SurahAtlasListResponse(
        status="ok",
        data=[_memory_entry_to_summary(s) for s in page],
        total=total,
        offset=offset,
        limit=limit,
        reviewStatus="needs_review",
        humanReviewRequired=True,
        warnings=[_REVIEW_WARNING_EN],
    )


@router.get("/search")
async def search_surah_atlas(
    response: Response,
    q: str = Query(..., min_length=1, max_length=200),
):
    """
    Search surah atlas by name, transliteration, or topic.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    atlas = _load_surah_memory_atlas()
    query = q.lower().strip()

    matches = []
    for s in atlas.get("surahs", []):
        score = 0
        if query in s.get("nameTransliteration", "").lower():
            score += 10
        if query in (s.get("nameEnglish") or "").lower():
            score += 8
        if any(query in t.lower() for t in s.get("mainTopicsEnglish", [])):
            score += 5
        if any(query in f.lower() for f in s.get("mainFigures", [])):
            score += 4
        if score > 0:
            matches.append((score, s))

    matches.sort(key=lambda x: -x[0])
    results = [_memory_entry_to_summary(s) for _, s in matches[:20]]

    return _envelope(data=results)


@router.get("/{surah_number}", response_model=SurahAtlasDetailResponse)
async def get_surah_atlas_detail(
    surah_number: int,
    response: Response,
):
    """
    Get full atlas detail for a single surah.
    """
    if surah_number < 1 or surah_number > 114:
        raise HTTPException(status_code=404, detail="Surah number must be 1–114")

    entry = _get_surah_memory_entry(surah_number)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Surah {surah_number} not found in atlas")

    response.headers["Cache-Control"] = "public, max-age=86400"

    return SurahAtlasDetailResponse(
        status="ok",
        data=_memory_entry_to_detail(entry),
        reviewStatus="needs_review",
        humanReviewRequired=True,
        warnings=[_REVIEW_WARNING_EN],
    )


@router.get("/{surah_number}/stories")
async def get_surah_atlas_stories(
    surah_number: int,
    response: Response,
):
    """
    Get stories mentioned in a specific surah.
    """
    if surah_number < 1 or surah_number > 114:
        raise HTTPException(status_code=404, detail="Surah number must be 1–114")

    entry = _get_surah_memory_entry(surah_number)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Surah {surah_number} not found")

    response.headers["Cache-Control"] = "public, max-age=86400"

    related_stories = entry.get("relatedStories", [])
    return _envelope(
        data={
            "surahNumber": surah_number,
            "storiesCount": len(related_stories),
            "storyIds": related_stories,
        }
    )


@router.get("/{surah_number}/rare-words")
async def get_surah_atlas_rare_words(
    surah_number: int,
    response: Response,
):
    """
    Get rare words (gharib al-Quran) for a specific surah.

    Currently serves from the static seed data layer.
    A full lexicon requires specialist seeding from classical Arabic sources.
    """
    if surah_number < 1 or surah_number > 114:
        raise HTTPException(status_code=404, detail="Surah number must be 1–114")

    response.headers["Cache-Control"] = "public, max-age=86400"

    return {
        "status": "ok",
        "data": {
            "surahNumber": surah_number,
            "rareWords": [],
            "message_en": (
                "Rare word data for this surah is pending lexicographic review. "
                "Run the vocabulary seeder to populate from classical lexicons."
            ),
            "message_ar": (
                "بيانات المفردات النادرة لهذه السورة قيد المراجعة المعجمية. "
                "نفّذ seed_vocabulary_qac.py لملء البيانات من المعاجم الكلاسيكية."
            ),
        },
        "reviewStatus": "needs_review",
        "humanReviewRequired": True,
        "warnings": [
            "Rare word meanings require verification against classical Arabic lexicons.",
            "This requires further scholarly review.",
        ],
    }


@router.get("/{surah_number}/memorization-links")
async def get_surah_atlas_memorization_links(
    surah_number: int,
    response: Response,
):
    """
    Get memorization intelligence data for a specific surah.

    Returns confusion pairs, similar ayat links, and repeated phrases.
    All data is auto-generated and requires review.
    """
    if surah_number < 1 or surah_number > 114:
        raise HTTPException(status_code=404, detail="Surah number must be 1–114")

    response.headers["Cache-Control"] = "public, max-age=3600"

    return _envelope(
        data={
            "surahNumber": surah_number,
            "confusionPairs": [],
            "memorizationLinks": [],
            "repeatedPhrases": [],
            "message_en": (
                "Memorization intelligence for this surah is auto-generated. "
                "All links require scholarly review before production use."
            ),
            "message_ar": (
                "بيانات ذكاء الحفظ لهذه السورة مولّدة تلقائياً. "
                "جميع الروابط تستلزم مراجعة علمية قبل الاستخدام الإنتاجي."
            ),
        }
    )
