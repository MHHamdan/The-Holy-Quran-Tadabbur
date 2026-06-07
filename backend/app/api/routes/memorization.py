"""
Memorization Intelligence API

Endpoints for helping memorizers navigate similar ayat, confusion pairs,
story recurrences, and phrase patterns across the Quran.

Safety rules:
- All similarity data is structural/textual, not theological interpretation
- Every link carries reviewStatus and humanReviewRequired
- Confusion pairs show differences factually, not interpretively
- No tafsir is generated; source IDs reference approved sources only

Endpoints:
  GET /memorization/similar-ayat/{surah}/{ayah}   — similar ayat for a verse
  GET /memorization/surah-links/{surah}           — memorization links for a surah
  GET /memorization/story-links/{storyId}         — story recurrence map
  GET /memorization/confusion-pairs               — all high-risk confusion pairs
  GET /memorization/repeated-phrases             — repeated Quranic phrases
  GET /memorization/status                        — module availability
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any, Optional

router = APIRouter()

# ---------------------------------------------------------------------------
# Standard response envelope
# ---------------------------------------------------------------------------

_REVIEW_WARNING_EN = (
    "All memorization intelligence data is auto-generated from structural/textual analysis. "
    "It requires scholarly review before use in formal Quran study."
)
_REVIEW_WARNING_AR = (
    "جميع بيانات ذكاء الحفظ مولّدة تلقائياً من التحليل البنوي/النصي. "
    "تستلزم مراجعة علمية قبل الاستخدام في الدراسة القرآنية الرسمية."
)


def _envelope(data: Any, warnings: list[str] | None = None) -> dict:
    return {
        "status": "ok",
        "data": data,
        "reviewStatus": "needs_review",
        "humanReviewRequired": True,
        "warnings": warnings or [_REVIEW_WARNING_EN],
        "warnings_ar": [_REVIEW_WARNING_AR],
    }


def _no_data_envelope(message_en: str) -> dict:
    return {
        "status": "no_verified_source",
        "data": None,
        "evidence": [],
        "warnings": [message_en, "This requires further scholarly review."],
        "warnings_ar": ["يحتاج هذا إلى مراجعة علمية إضافية."],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
async def memorization_status():
    """Module availability and dataset coverage status."""
    return {
        "module": "memorization_intelligence",
        "status": "partial",
        "available": True,
        "coverage": {
            "confusionPairs": "seed_data_only",
            "memorizationLinks": "seed_data_only",
            "repeatedPhrases": "seed_data_only",
            "storyRecurrences": "seed_data_only",
            "surahConnections": "not_yet_built",
        },
        "reviewStatus": "needs_review",
        "message_en": (
            "The memorization intelligence module contains seed data covering key confusion pairs "
            "and repeated phrases. Full coverage requires specialist lexicographic input."
        ),
        "message_ar": (
            "يحتوي وحدة ذكاء الحفظ على بيانات أولية تغطي أزواج الخلط الرئيسية والعبارات المتكررة. "
            "التغطية الكاملة تتطلب مدخلات معجمية متخصصة."
        ),
    }


@router.get("/similar-ayat/{surah}/{ayah}")
async def get_similar_ayat(
    surah: int,
    ayah: int,
    response: Response,
):
    """
    Get ayat similar to the given verse — useful for avoiding memorization confusion.

    Returns structural/textual similarities only. No theological interpretation.
    """
    if surah < 1 or surah > 114:
        raise HTTPException(status_code=422, detail="Surah must be 1–114")
    if ayah < 1:
        raise HTTPException(status_code=422, detail="Ayah must be >= 1")

    response.headers["Cache-Control"] = "public, max-age=3600"

    return _envelope(
        data={
            "surah": surah,
            "ayah": ayah,
            "similarAyat": [],
            "message_en": (
                f"Similar ayat data for {surah}:{ayah} is being built. "
                "Full similarity mapping requires lexicographic review."
            ),
            "message_ar": (
                f"بيانات الآيات المشابهة للآية {surah}:{ayah} قيد الإنشاء. "
                "رسم الخرائط الكاملة للتشابه يتطلب مراجعة معجمية."
            ),
        }
    )


@router.get("/surah-links/{surah}")
async def get_surah_memorization_links(
    surah: int,
    response: Response,
):
    """
    Get memorization links for a specific surah — similar surahs, confusion pairs, etc.
    """
    if surah < 1 or surah > 114:
        raise HTTPException(status_code=422, detail="Surah must be 1–114")

    response.headers["Cache-Control"] = "public, max-age=3600"

    return _envelope(
        data={
            "surah": surah,
            "links": [],
            "confusionPairs": [],
            "repeatedPhrases": [],
            "message_en": (
                f"Memorization links for Surah {surah} are available in the frontend data layer. "
                "See quranMemorizationLinks.ts for the current seed dataset."
            ),
            "message_ar": (
                f"روابط الحفظ لسورة {surah} متاحة في طبقة بيانات الواجهة الأمامية. "
                "انظر quranMemorizationLinks.ts للبيانات الأولية الحالية."
            ),
        }
    )


@router.get("/story-links/{story_id}")
async def get_story_memorization_links(
    story_id: str,
    response: Response,
):
    """
    Get story recurrence map — where a story appears across the Quran.
    """
    if not story_id.startswith("story_") or len(story_id) > 100:
        raise HTTPException(status_code=422, detail="Invalid story_id format")

    response.headers["Cache-Control"] = "public, max-age=86400"

    return _envelope(
        data={
            "storyId": story_id,
            "recurrences": [],
            "message_en": (
                f"Story recurrence data for {story_id} is available in the frontend data layer. "
                "See quranMemorizationLinks.ts STORY_RECURRENCES for the current map."
            ),
            "message_ar": (
                f"بيانات تكرار قصة {story_id} متاحة في طبقة بيانات الواجهة الأمامية."
            ),
        }
    )


@router.get("/confusion-pairs")
async def get_confusion_pairs(
    response: Response,
    risk_level: Optional[str] = Query(None, pattern=r"^(high|medium|low|all)$"),
    surah: Optional[int] = Query(None, ge=1, le=114),
):
    """
    Get all confusion pairs — ayat that memorizers commonly confuse.

    Filter by risk level (high/medium/low) or by surah.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    return _envelope(
        data={
            "confusionPairs": [],
            "filters": {"riskLevel": risk_level, "surah": surah},
            "message_en": (
                "Confusion pair data is available in the frontend layer. "
                "See quranMemorizationLinks.ts CONFUSION_PAIRS. "
                "Full DB-backed confusion pairs require lexicographic seeding."
            ),
            "message_ar": (
                "بيانات أزواج الخلط متاحة في طبقة الواجهة الأمامية. "
                "انظر CONFUSION_PAIRS في quranMemorizationLinks.ts."
            ),
        }
    )


@router.get("/repeated-phrases")
async def get_repeated_phrases(
    response: Response,
    surah: Optional[int] = Query(None, ge=1, le=114),
):
    """
    Get repeated Quranic phrases — useful as memorization anchors.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    return _envelope(
        data={
            "repeatedPhrases": [],
            "filters": {"surah": surah},
            "message_en": (
                "Repeated phrase data is available in the frontend layer. "
                "See quranMemorizationLinks.ts REPEATED_PHRASES."
            ),
            "message_ar": (
                "بيانات العبارات المتكررة متاحة في طبقة الواجهة الأمامية. "
                "انظر REPEATED_PHRASES في quranMemorizationLinks.ts."
            ),
        }
    )
