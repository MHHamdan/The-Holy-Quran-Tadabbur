"""
Quranic Duʿā API — serves the static dua catalogue with server-side filtering.

All data is derived from exact Quranic references (Hafs ʿan ʿĀṣim).
No AI-generated content. Source: frontend/src/data/quranicDuas.ts (same dataset).

Rate-limited to 30 requests/min per IP.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.rate_limit import InMemoryRateLimiter, _get_client_ip, _make_429_response

logger = logging.getLogger(__name__)

router = APIRouter()

_duas_limiter = InMemoryRateLimiter(max_requests=30, window_seconds=60)


async def _rate_limit(request: Request) -> None:
    ip = _get_client_ip(request)
    allowed, retry_after = _duas_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Duas rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


# ── Static catalogue ──────────────────────────────────────────────────────────
# Generated from frontend/src/data/quranicDuas.ts, the curated source of truth,
# by scripts/export-duas-to-backend.ts. Regenerate after editing that dataset;
# never hand-edit duas.json and never paste Quranic Arabic into this module.

_DUAS_PATH = Path(__file__).resolve().parents[2] / "data" / "duas.json"


def _load_duas() -> list[dict]:
    """Load the generated catalogue, failing loudly if it is missing."""
    try:
        with _DUAS_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        raise RuntimeError(
            f"Dua catalogue not found at {_DUAS_PATH}. "
            "Run: npx tsx scripts/export-duas-to-backend.ts"
        ) from None

    duas = payload.get("duas", [])
    if not duas:
        raise RuntimeError(f"Dua catalogue at {_DUAS_PATH} is empty.")

    logger.info("Loaded %d duas from %s", len(duas), _DUAS_PATH.name)
    return duas


_DUAS: list[dict] = _load_duas()


# ── Pydantic schema ───────────────────────────────────────────────────────────

class DuaOut(BaseModel):
    id: str
    surah: int
    ayah: int
    ayahEnd: Optional[int] = None
    category: str
    prophet: Optional[str] = None
    titleEn: str
    titleAr: str
    surahNameEn: str
    surahNameAr: str
    meaningEn: str
    meaningAr: str
    occasions: list[str]
    tags: list[str]


class DuaListOut(BaseModel):
    count: int
    duas: list[DuaOut]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get('', response_model=DuaListOut, dependencies=[Depends(_rate_limit)])
async def list_duas(
    response: Response,
    category: Optional[str] = Query(None, description="Filter by category slug"),
    prophet:  Optional[str] = Query(None, description="Filter by prophet name"),
    occasion: Optional[str] = Query(None, description="Filter by occasion slug"),
    q:        Optional[str] = Query(None, max_length=120, description="Full-text search (English + Arabic)"),
) -> DuaListOut:
    """Return the full Quranic Duʿā catalogue with optional server-side filtering."""
    results = _DUAS

    if category:
        cat = category.lower().strip()
        results = [d for d in results if d['category'] == cat]

    if prophet:
        proph = prophet.strip()
        results = [d for d in results if (d.get('prophet') or '').lower() == proph.lower()]

    if occasion:
        occ = occasion.lower().strip()
        results = [d for d in results if occ in d.get('occasions', [])]

    if q:
        needle = q.lower()
        results = [
            d for d in results
            if (needle in d['titleEn'].lower()
                or needle in d['titleAr']
                or needle in d['meaningEn'].lower()
                or needle in d['meaningAr']
                or any(needle in t for t in d.get('tags', []))
                or needle in d['surahNameEn'].lower()
                or needle in (d.get('prophet') or '').lower())
        ]

    response.headers["Cache-Control"] = "public, max-age=86400"
    return DuaListOut(count=len(results), duas=[DuaOut(**d) for d in results])
