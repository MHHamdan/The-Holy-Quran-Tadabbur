"""
Asbab al-Nuzul (Occasions of Revelation) API Routes.

Proxies alquran.cloud ar.wahidi edition — al-Wahidi's classical Asbab al-Nuzul
(d. 468 AH). Each surah is fetched upstream at most once per 24 h per worker
(in-process TTL cache keyed by surah); single-verse lookups are served from
the cached surah. Responses also carry a 24 h public Cache-Control header so
the browser and any CDN layer can serve them offline after the first fetch.
If a refresh fails, the last good copy is served rather than an error.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/asbab", tags=["Asbab al-Nuzul"])

_ALQURAN_BASE = "https://api.alquran.cloud/v1"
_WAHIDI_EDITION = "ar.wahidi"
_CACHE_SECONDS = 86400  # 24 h — content is immutable classical text
_TIMEOUT = httpx.Timeout(10.0, connect=3.0)

# surah -> (fetched_at monotonic, [(ayah, text), ...] for every ayah)
_cache: Dict[int, Tuple[float, List[Tuple[int, str]]]] = {}
_locks: Dict[int, asyncio.Lock] = {}
_client: Optional[httpx.AsyncClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None


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


def _http_error(status: int, code: str, en: str, ar: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error_code": code, "message_en": en, "message_ar": ar})


_UNAVAILABLE = ("asbab_unavailable", "The Asbab al-Nuzul service is temporarily unavailable.",
                "خدمة أسباب النزول غير متاحة مؤقتاً.")


def _set_cache(response: Response) -> None:
    response.headers["Cache-Control"] = f"public, max-age={_CACHE_SECONDS}"
    response.headers["Vary"] = "Accept-Encoding"


def _get_client() -> httpx.AsyncClient:
    """One shared client per event loop (connection reuse across requests)."""
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client_loop is not loop or _client.is_closed:
        _client = httpx.AsyncClient(timeout=_TIMEOUT)
        _client_loop = loop
    return _client


def _parse_ayahs(data: dict) -> List[Tuple[int, str]]:
    return [
        (int(a["numberInSurah"]), (a.get("text") or "").strip())
        for a in data.get("data", {}).get("ayahs", [])
    ]


async def _surah_ayahs(surah: int) -> List[Tuple[int, str]]:
    """All ayahs (with possibly empty text) of a surah, cached for 24 h."""
    hit = _cache.get(surah)
    if hit and time.monotonic() - hit[0] < _CACHE_SECONDS:
        return hit[1]

    lock = _locks.setdefault(surah, asyncio.Lock())
    async with lock:
        hit = _cache.get(surah)
        if hit and time.monotonic() - hit[0] < _CACHE_SECONDS:
            return hit[1]
        url = f"{_ALQURAN_BASE}/surah/{surah}/{_WAHIDI_EDITION}"
        try:
            r = await _get_client().get(url)
            r.raise_for_status()
            ayahs = _parse_ayahs(r.json())
            if not ayahs:
                raise ValueError("empty ayah list")
        except Exception as exc:
            logger.warning("asbab fetch surah=%d failed: %s", surah, type(exc).__name__)
            if hit:  # stale but valid classical text beats an error page
                return hit[1]
            raise _http_error(503, *_UNAVAILABLE)
        _cache[surah] = (time.monotonic(), ayahs)
        return ayahs


@router.get("/{surah}", response_model=SurahAsbabResponse)
async def get_surah_asbab(surah: int, response: Response):
    """All occasions of revelation for a surah (verses with empty text omitted)."""
    if not 1 <= surah <= 114:
        raise _http_error(400, "invalid_surah", "Surah must be 1–114", "رقم السورة يجب أن يكون بين 1 و114")

    ayahs = await _surah_ayahs(surah)
    verses = [AsbabVerse(surah=surah, ayah=n, text=t) for n, t in ayahs if t]
    _set_cache(response)
    return SurahAsbabResponse(surah=surah, verses=verses, total_with_content=len(verses))


@router.get("/{surah}/{ayah}", response_model=AsbabVerse)
async def get_verse_asbab(surah: int, ayah: int, response: Response):
    """Occasion of revelation for a single verse (empty text when none is recorded)."""
    if not 1 <= surah <= 114:
        raise _http_error(400, "invalid_surah", "Surah must be 1–114", "رقم السورة يجب أن يكون بين 1 و114")
    if ayah < 1:
        raise _http_error(400, "invalid_ayah", "Ayah must be >= 1", "رقم الآية يجب أن يكون 1 أو أكثر")

    ayahs = await _surah_ayahs(surah)
    text = next((t for n, t in ayahs if n == ayah), None)
    if text is None:
        raise _http_error(404, "verse_not_found", "This verse does not exist in the surah.",
                          "هذه الآية غير موجودة في السورة.")
    _set_cache(response)
    return AsbabVerse(surah=surah, ayah=ayah, text=text)
