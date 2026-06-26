"""
Asbab al-Nuzul (Occasions of Revelation) API Routes.

Proxies alquran.cloud ar.wahidi edition — al-Wahidi's classical Asbab al-Nuzul
(d. 468 AH). Responses are cached 24 h with public Cache-Control headers so
the browser and any CDN layer serve them offline after the first fetch.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/asbab", tags=["Asbab al-Nuzul"])

_ALQURAN_BASE = "https://api.alquran.cloud/v1"
_WAHIDI_EDITION = "ar.wahidi"
_CACHE_SECONDS = 86400  # 24 h — content is immutable classical text


class AsbabVerse(BaseModel):
    surah: int
    ayah: int
    text: str


class SurahAsbabResponse(BaseModel):
    surah: int
    edition: str = "ar.wahidi"
    source_name: str = "أسباب النزول — أبو الحسن الواحدي (ت 468 هـ)"
    source_name_en: str = "Asbab al-Nuzul — Abu al-Hasan al-Wahidi (d. 468 AH)"
    verses: List[AsbabVerse]
    total_with_content: int


def _set_cache(response: Response) -> None:
    response.headers["Cache-Control"] = f"public, max-age={_CACHE_SECONDS}"
    response.headers["Vary"] = "Accept-Encoding"


def _extract_verses(data: dict, surah: int) -> List[AsbabVerse]:
    ayahs = data.get("data", {}).get("ayahs", [])
    results = []
    for a in ayahs:
        text = (a.get("text") or "").strip()
        if text:
            results.append(AsbabVerse(surah=surah, ayah=a["numberInSurah"], text=text))
    return results


@router.get("/{surah}", response_model=SurahAsbabResponse)
async def get_surah_asbab(surah: int, response: Response):
    """All occasions of revelation for a surah (verses with empty text omitted)."""
    if not 1 <= surah <= 114:
        raise HTTPException(status_code=400, detail="Surah must be 1–114")

    url = f"{_ALQURAN_BASE}/surah/{surah}/{_WAHIDI_EDITION}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("alquran.cloud %s → %s", url, exc.response.status_code)
        raise HTTPException(status_code=503, detail="Upstream asbab service unavailable")
    except Exception as exc:
        logger.error("asbab fetch surah=%d: %s", surah, exc)
        raise HTTPException(status_code=503, detail="Asbab al-Nuzul service unavailable")

    verses = _extract_verses(data, surah)
    _set_cache(response)
    return SurahAsbabResponse(surah=surah, verses=verses, total_with_content=len(verses))


@router.get("/{surah}/{ayah}", response_model=AsbabVerse)
async def get_verse_asbab(surah: int, ayah: int, response: Response):
    """Occasion of revelation for a single verse."""
    if not 1 <= surah <= 114:
        raise HTTPException(status_code=400, detail="Surah must be 1–114")
    if ayah < 1:
        raise HTTPException(status_code=400, detail="Ayah must be >= 1")

    url = f"{_ALQURAN_BASE}/ayah/{surah}:{ayah}/{_WAHIDI_EDITION}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("alquran.cloud %s → %s", url, exc.response.status_code)
        raise HTTPException(status_code=503, detail="Upstream asbab service unavailable")
    except Exception as exc:
        logger.error("asbab fetch %d:%d: %s", surah, ayah, exc)
        raise HTTPException(status_code=503, detail="Asbab al-Nuzul service unavailable")

    text = (data.get("data", {}).get("text") or "").strip()
    _set_cache(response)
    return AsbabVerse(surah=surah, ayah=ayah, text=text)
