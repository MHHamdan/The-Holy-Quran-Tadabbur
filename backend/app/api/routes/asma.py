"""
Asmā' Allah al-Ḥusnā Atlas API — Phase W.

Endpoints:
    GET  /api/v1/quran/asma
    GET  /api/v1/quran/asma/categories
    GET  /api/v1/quran/asma/search?q=
    GET  /api/v1/quran/asma/{name_id}
    GET  /api/v1/quran/asma/{name_id}/occurrences
    GET  /api/v1/quran/asma/{name_id}/pairings

Safety rules:
    - Responses NEVER include Quran text — only surah/ayah numbers + the
      short normalised `matchedForm`.
    - Every record echoes reviewStatus and humanReviewRequired.
    - Verified meanings are NOT returned unless reviewer-promoted.
    - If a meaning is unavailable, the API does NOT invent one; clients are
      expected to render the safe missing-source message.
    - The basmalah-counting policy is exposed at /asma so the UI can show
      reviewers exactly how counts are derived.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path as FPath, Query, Response
from pydantic import BaseModel

router = APIRouter()

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ATLAS_FILE = _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "asmaAllahAtlas.json"

_NAME_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_CACHE_HEADER = "public, max-age=3600"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "data_not_built",
                "message_en": f"Generated file missing: {path.name}. Run scripts/build-asma-allah-atlas.ts.",
                "message_ar": "ملف بيانات الأسماء غير موجود؛ يجب تشغيل سكربت البناء أولاً.",
            },
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_atlas() -> Dict[str, Any]:
    return _read_json(_ATLAS_FILE)


def _name_index() -> Dict[str, Dict[str, Any]]:
    atlas = _load_atlas()
    idx: Dict[str, Dict[str, Any]] = {n["nameId"]: n for n in atlas["names"]}
    # Include the standalone Divine Name "Allah" so detail/occurrence/pairing
    # routes still resolve it even though it lives outside the 99-Names list.
    divine = atlas.get("divineNameAllah")
    if divine and divine.get("nameId"):
        idx[divine["nameId"]] = divine
    return idx


def _validate_name_id(name_id: str) -> None:
    if not _NAME_ID_RE.match(name_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_name_id",
                "message_en": "Invalid name_id format",
                "message_ar": "معرّف الاسم غير صالح",
            },
        )
    if name_id not in _name_index():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "asma_name_not_found",
                "message_en": f"Name not found: {name_id}",
                "message_ar": "الاسم غير موجود",
            },
        )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class BasmalahPolicyOut(BaseModel):
    countBasmalaInFatihah: bool
    excludeRepeatedSurahOpeningBasmalah: bool
    notes: str


class AsmaPrimaryReference(BaseModel):
    surahNumber: int
    ayahStart: int
    ayahEnd: Optional[int] = None
    note: Optional[str] = None
    ayahText: Optional[str] = None


class AsmaNameSummary(BaseModel):
    nameId: str
    arabicName: str
    transliteration: str
    englishName: Optional[str] = None
    category: str
    occurrenceCount: int
    surahCount: int
    reviewStatus: str
    warningCount: int = 0
    primaryQuranicReferences: List[AsmaPrimaryReference] = []


class AsmaCategoryEntry(BaseModel):
    category: str
    names: int
    countedOccurrences: int
    labelArabic: str
    labelEnglish: str


class AsmaDivineNameOut(BaseModel):
    nameId: str
    arabicName: str
    transliteration: str
    englishName: Optional[str] = None
    occurrenceCount: int
    surahCount: int
    reviewStatus: str
    warningCount: int = 0
    labelArabic: str = "اسم الجلالة"
    labelEnglish: str = "The Divine Name"
    separateFromListNoteArabic: str = (
        "اسم الجلالة منفصل عن قائمة الأسماء الـ99"
    )
    separateFromListNoteEnglish: str = (
        "The Divine Name Allah is shown separately from the 99 Names list."
    )


class AsmaListResponse(BaseModel):
    total: int
    traditionalNamesCount: int
    divineNameAllahIncluded: bool
    allDisplayCount: int
    quranEvidenceNamesCount: int
    zeroExactOccurrenceNamesCount: int
    basmalahPolicy: BasmalahPolicyOut
    categories: List[AsmaCategoryEntry]
    names: List[AsmaNameSummary]
    divineNameAllah: Optional[AsmaDivineNameOut] = None


class AsmaOccurrenceOut(BaseModel):
    surahNumber: int
    ayahNumber: int
    matchedForm: str
    matchType: str
    isBasmalah: bool
    counted: bool
    confidence: float
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool


class AsmaPairingOut(BaseModel):
    firstNameId: str
    secondNameId: str
    occurrenceCount: int
    ayahReferences: List[Dict[str, Any]]
    reviewStatus: str


class AsmaDetailResponse(BaseModel):
    nameId: str
    arabicName: str
    transliteration: str
    englishName: Optional[str] = None
    rootArabic: Optional[str] = None
    category: str
    meaningArabic: Optional[str] = None
    meaningEnglish: Optional[str] = None
    shortReflectionArabic: Optional[str] = None
    shortReflectionEnglish: Optional[str] = None
    occurrenceCount: int
    surahCount: int
    firstOccurrence: Optional[Dict[str, Any]] = None
    lastOccurrence: Optional[Dict[str, Any]] = None
    commonPairings: List[AsmaPairingOut]
    relatedTopics: List[str]
    relatedEntities: List[str]
    sourceIds: List[str]
    reviewStatus: str
    humanReviewRequired: bool
    warnings: List[str]
    basmalahPolicy: BasmalahPolicyOut
    missingMeaningMessage: Dict[str, str]
    primaryQuranicReferences: List[AsmaPrimaryReference] = []


class AsmaOccurrencesResponse(BaseModel):
    nameId: str
    total: int
    occurrences: List[AsmaOccurrenceOut]
    excludedBasmalahCount: int


class AsmaPairingsResponse(BaseModel):
    nameId: str
    total: int
    pairings: List[AsmaPairingOut]


class AsmaCategoriesResponse(BaseModel):
    total: int
    traditionalNamesCount: int
    divineNameAllahIncluded: bool
    allDisplayCount: int
    basmalahPolicy: BasmalahPolicyOut
    categories: List[AsmaCategoryEntry]
    divineNameAllah: Optional[AsmaDivineNameOut] = None


_CATEGORY_LABELS: Dict[str, Dict[str, str]] = {
    "dhat": {"ar": "الذات", "en": "Essence"},
    "jamal": {"ar": "الجمال", "en": "Beauty"},
    "jalal": {"ar": "الجلال", "en": "Majesty"},
    "kamal": {"ar": "الكمال", "en": "Perfection"},
    "afaal": {"ar": "الأفعال", "en": "Actions"},
    "unknown": {"ar": "غير مصنف", "en": "Unclassified"},
}


def _categories_with_labels(atlas: Dict[str, Any]) -> List[AsmaCategoryEntry]:
    return [
        AsmaCategoryEntry(
            category=c["category"],
            names=c["names"],
            countedOccurrences=c["countedOccurrences"],
            labelArabic=_CATEGORY_LABELS.get(c["category"], {"ar": c["category"]})["ar"],
            labelEnglish=_CATEGORY_LABELS.get(c["category"], {"en": c["category"]})["en"],
        )
        for c in atlas["categoryCounts"]
    ]


def _primary_refs(n: Dict[str, Any]) -> List[AsmaPrimaryReference]:
    """Coerce atlas primaryQuranicReferences into the API schema."""
    raw = n.get("primaryQuranicReferences") or []
    out: List[AsmaPrimaryReference] = []
    for r in raw:
        try:
            out.append(
                AsmaPrimaryReference(
                    surahNumber=int(r["surahNumber"]),
                    ayahStart=int(r["ayahStart"]),
                    ayahEnd=r.get("ayahEnd"),
                    note=r.get("note"),
                    ayahText=r.get("ayahText"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _row_from_name(n: Dict[str, Any]) -> AsmaNameSummary:
    return AsmaNameSummary(
        nameId=n["nameId"],
        arabicName=n["arabicName"],
        transliteration=n["transliteration"],
        englishName=n.get("englishName"),
        category=n["category"],
        occurrenceCount=n["occurrenceCount"],
        surahCount=n["surahCount"],
        reviewStatus=n.get("reviewStatus", "needs_review"),
        warningCount=len(n.get("warnings", [])),
        primaryQuranicReferences=_primary_refs(n),
    )


def _divine_name_payload(atlas: Dict[str, Any]) -> Optional[AsmaDivineNameOut]:
    divine = atlas.get("divineNameAllah")
    if not divine:
        return None
    return AsmaDivineNameOut(
        nameId=divine["nameId"],
        arabicName=divine["arabicName"],
        transliteration=divine["transliteration"],
        englishName=divine.get("englishName"),
        occurrenceCount=int(divine.get("occurrenceCount", 0)),
        surahCount=int(divine.get("surahCount", 0)),
        reviewStatus=divine.get("reviewStatus", "needs_review"),
        warningCount=len(divine.get("warnings", [])),
    )


def _missing_meaning_msg() -> Dict[str, str]:
    return {
        "ar": "لا يتوفر معنى موثوق لهذا الاسم حالياً.",
        "en": "No verified meaning is available for this Name yet.",
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/asma", response_model=AsmaListResponse)
def list_asma(
    response: Response,
    category: Optional[str] = Query(None),
    has_occurrences: Optional[bool] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AsmaListResponse:
    atlas = _load_atlas()
    rows: List[AsmaNameSummary] = []
    for n in atlas["names"]:
        if category and n["category"] != category:
            continue
        if has_occurrences is True and n["occurrenceCount"] == 0:
            continue
        if has_occurrences is False and n["occurrenceCount"] > 0:
            continue
        rows.append(_row_from_name(n))
    rows.sort(key=lambda r: (-r.occurrenceCount, r.nameId))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaListResponse(
        total=len(rows),
        traditionalNamesCount=int(atlas.get("traditionalNamesCount", 99)),
        divineNameAllahIncluded=bool(atlas.get("divineNameAllahIncluded", False)),
        allDisplayCount=int(atlas.get("allDisplayCount", atlas["totalNames"])),
        quranEvidenceNamesCount=int(atlas.get("quranEvidenceNamesCount", 0)),
        zeroExactOccurrenceNamesCount=int(atlas.get("zeroExactOccurrenceNamesCount", 0)),
        basmalahPolicy=BasmalahPolicyOut(**atlas["basmalahPolicy"]),
        categories=_categories_with_labels(atlas),
        names=rows[offset : offset + limit],
        divineNameAllah=_divine_name_payload(atlas),
    )


@router.get("/asma/categories", response_model=AsmaCategoriesResponse)
def list_asma_categories(response: Response) -> AsmaCategoriesResponse:
    atlas = _load_atlas()
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaCategoriesResponse(
        total=atlas["totalNames"],
        traditionalNamesCount=int(atlas.get("traditionalNamesCount", 99)),
        divineNameAllahIncluded=bool(atlas.get("divineNameAllahIncluded", False)),
        allDisplayCount=int(atlas.get("allDisplayCount", atlas["totalNames"])),
        basmalahPolicy=BasmalahPolicyOut(**atlas["basmalahPolicy"]),
        categories=_categories_with_labels(atlas),
        divineNameAllah=_divine_name_payload(atlas),
    )


@router.get("/asma/search", response_model=AsmaListResponse)
def search_asma(
    response: Response,
    q: str = Query(..., min_length=1, max_length=80),
    limit: int = Query(50, ge=1, le=200),
) -> AsmaListResponse:
    atlas = _load_atlas()
    ql = q.lower()
    rows: List[AsmaNameSummary] = []
    searchable = list(atlas["names"])
    divine = atlas.get("divineNameAllah")
    if divine:
        searchable.append(divine)
    for n in searchable:
        if (
            ql in n["nameId"].lower()
            or ql in n["transliteration"].lower()
            or (n.get("englishName") and ql in n["englishName"].lower())
            or q in n["arabicName"]
        ):
            rows.append(_row_from_name(n))
    rows.sort(key=lambda r: (-r.occurrenceCount, r.nameId))
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaListResponse(
        total=len(rows),
        traditionalNamesCount=int(atlas.get("traditionalNamesCount", 99)),
        divineNameAllahIncluded=bool(atlas.get("divineNameAllahIncluded", False)),
        allDisplayCount=int(atlas.get("allDisplayCount", atlas["totalNames"])),
        quranEvidenceNamesCount=int(atlas.get("quranEvidenceNamesCount", 0)),
        zeroExactOccurrenceNamesCount=int(atlas.get("zeroExactOccurrenceNamesCount", 0)),
        basmalahPolicy=BasmalahPolicyOut(**atlas["basmalahPolicy"]),
        categories=_categories_with_labels(atlas),
        names=rows[:limit],
        divineNameAllah=_divine_name_payload(atlas),
    )


@router.get("/asma/{name_id}", response_model=AsmaDetailResponse)
def get_asma_name(
    response: Response,
    name_id: str = FPath(...),
) -> AsmaDetailResponse:
    _validate_name_id(name_id)
    atlas = _load_atlas()
    n = _name_index()[name_id]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaDetailResponse(
        nameId=n["nameId"],
        arabicName=n["arabicName"],
        transliteration=n["transliteration"],
        englishName=n.get("englishName"),
        rootArabic=n.get("rootArabic"),
        category=n["category"],
        meaningArabic=n.get("meaningArabic"),
        meaningEnglish=n.get("meaningEnglish"),
        shortReflectionArabic=n.get("shortReflectionArabic"),
        shortReflectionEnglish=n.get("shortReflectionEnglish"),
        occurrenceCount=n["occurrenceCount"],
        surahCount=n["surahCount"],
        firstOccurrence=n.get("firstOccurrence"),
        lastOccurrence=n.get("lastOccurrence"),
        commonPairings=[AsmaPairingOut(**p) for p in n.get("commonPairings", [])],
        relatedTopics=n.get("relatedTopics", []),
        relatedEntities=n.get("relatedEntities", []),
        sourceIds=n.get("sourceIds", []),
        reviewStatus=n.get("reviewStatus", "needs_review"),
        humanReviewRequired=bool(n.get("humanReviewRequired", True)),
        warnings=n.get("warnings", []),
        basmalahPolicy=BasmalahPolicyOut(**atlas["basmalahPolicy"]),
        missingMeaningMessage=_missing_meaning_msg(),
        primaryQuranicReferences=_primary_refs(n),
    )


@router.get("/asma/{name_id}/occurrences", response_model=AsmaOccurrencesResponse)
def get_asma_occurrences(
    response: Response,
    name_id: str = FPath(...),
    surah: Optional[int] = Query(None, ge=1, le=114),
    include_excluded: bool = Query(True, description="Include basmalah-excluded occurrences"),
    counted_only: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> AsmaOccurrencesResponse:
    _validate_name_id(name_id)
    n = _name_index()[name_id]
    occs = list(n.get("quranOccurrences", []))
    if surah:
        occs = [o for o in occs if o["surahNumber"] == surah]
    excluded_count = sum(1 for o in occs if not o.get("counted", False))
    if not include_excluded or counted_only:
        occs = [o for o in occs if o.get("counted", False)]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaOccurrencesResponse(
        nameId=name_id,
        total=len(occs),
        excludedBasmalahCount=excluded_count,
        occurrences=[AsmaOccurrenceOut(**o) for o in occs[offset : offset + limit]],
    )


@router.get("/asma/{name_id}/pairings", response_model=AsmaPairingsResponse)
def get_asma_pairings(
    response: Response,
    name_id: str = FPath(...),
) -> AsmaPairingsResponse:
    _validate_name_id(name_id)
    n = _name_index()[name_id]
    pairings = n.get("commonPairings", [])
    response.headers["Cache-Control"] = _CACHE_HEADER
    return AsmaPairingsResponse(
        nameId=name_id,
        total=len(pairings),
        pairings=[AsmaPairingOut(**p) for p in pairings],
    )


__all__ = ["router"]
