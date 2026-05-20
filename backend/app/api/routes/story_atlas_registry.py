"""
Story Atlas Registry API — serves the canonical Quran Story Registry built
by `scripts/build-quran-story-registry.ts`.

Endpoints:
    GET /api/v1/quran/story-atlas                        — full registry, optionally filtered
    GET /api/v1/quran/story-atlas/coverage               — coverage summary only
    GET /api/v1/quran/story-atlas/categories             — canonical category enum
    GET /api/v1/quran/story-atlas/search?q=              — search registry
    GET /api/v1/quran/story-atlas/{story_id}             — single entry
    GET /api/v1/quran/story-atlas/{story_id}/connections — connections for one story

Safety:
    - Never embeds Quran text.
    - Returns 503 if the generated JSON files are missing (so callers know
      to run the builder); never returns an empty list silently.
    - Categories returned to clients exactly match the registry enum so
      filters in the UI cannot drift.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path as FPath, Query, Response

router = APIRouter()

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REGISTRY_FILE = _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryRegistry.json"
_CONNECTIONS_FILE = _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryAtlasConnections.json"
_CROSS_REFS_FILE = _REPO_ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryCrossReferences.json"

_STORY_ID_RE = re.compile(r"^[a-zA-Z0-9_:-]+$")
_CACHE_HEADER = "public, max-age=300"


def _read_json(path: Path, builder_hint: str) -> Dict[str, Any]:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "data_not_built",
                "message_en": f"Generated file missing: {path.name}. Run {builder_hint}.",
                "message_ar": "ملف السجل غير موجود؛ يرجى تشغيل سكربت البناء.",
            },
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, Any]:
    return _read_json(_REGISTRY_FILE, "scripts/build-quran-story-registry.ts")


@lru_cache(maxsize=1)
def _load_connections() -> Dict[str, Any]:
    return _read_json(
        _CONNECTIONS_FILE,
        "scripts/build-quran-story-atlas-connections.ts",
    )


@lru_cache(maxsize=1)
def _load_cross_refs() -> Dict[str, Any]:
    return _read_json(
        _CROSS_REFS_FILE,
        "scripts/build-quran-story-cross-references.ts",
    )


def _validate_story_id(story_id: str) -> None:
    if not _STORY_ID_RE.match(story_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_story_id",
                "message_en": "Invalid story_id format",
                "message_ar": "معرّف القصة غير صالح",
            },
        )


def _filter_stories(
    stories: List[Dict[str, Any]],
    category: Optional[str],
    prophet: Optional[str],
    search: Optional[str],
) -> List[Dict[str, Any]]:
    result = stories
    if category and category != "all":
        result = [s for s in result if s.get("category") == category]
    if prophet:
        result = [s for s in result if prophet in (s.get("relatedProphets") or [])]
    if search:
        q = search.strip().lower()
        if q:
            result = [
                s
                for s in result
                if q in (s.get("titleArabic", "") or "").lower()
                or q in (s.get("titleEnglish", "") or "").lower()
                or q in (s.get("storyId", "") or "").lower()
                or any(q in (p or "").lower() for p in s.get("relatedProphets", []))
                or any(q in (e or "").lower() for e in s.get("relatedEntities", []))
                or any(q in (t or "").lower() for t in s.get("relatedTopics", []))
            ]
    return result


@router.get("/story-atlas")
def list_registry(
    response: Response,
    category: Optional[str] = Query(None, description="Registry category filter"),
    prophet: Optional[str] = Query(None, description="Filter by prophetId"),
    search: Optional[str] = Query(None, description="Search title / id / prophet / entity"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """List registry entries (canonical, registry-backed)."""
    registry = _load_registry()
    stories = registry.get("stories", []) or []
    filtered = _filter_stories(stories, category, prophet, search)
    total = len(filtered)
    sliced = filtered[offset : offset + limit]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return {
        "version": registry.get("version"),
        "generatedAt": registry.get("generatedAt"),
        "categories": registry.get("categories", []),
        "coverage": registry.get("coverage", {}),
        "total": total,
        "offset": offset,
        "limit": limit,
        "stories": sliced,
        "warnings": registry.get("warnings", []),
    }


@router.get("/story-atlas/coverage")
def get_coverage(response: Response) -> Dict[str, Any]:
    registry = _load_registry()
    response.headers["Cache-Control"] = _CACHE_HEADER
    return {
        "version": registry.get("version"),
        "generatedAt": registry.get("generatedAt"),
        "coverage": registry.get("coverage", {}),
        "warnings": registry.get("warnings", []),
    }


@router.get("/story-atlas/categories")
def get_categories(response: Response) -> Dict[str, Any]:
    registry = _load_registry()
    response.headers["Cache-Control"] = _CACHE_HEADER
    categories = registry.get("categories", [])
    # Compute count per category from the registry itself.
    counts: Dict[str, int] = {c: 0 for c in categories}
    for s in registry.get("stories", []) or []:
        c = s.get("category")
        if c in counts:
            counts[c] += 1
        else:
            counts[c] = counts.get(c, 0) + 1
    return {"categories": categories, "counts": counts}


@router.get("/story-atlas/search")
def search_registry(
    response: Response,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    registry = _load_registry()
    stories = registry.get("stories", []) or []
    matched = _filter_stories(stories, None, None, q)[:limit]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return {"query": q, "total": len(matched), "stories": matched}


@router.get("/story-atlas/{story_id}")
def get_story(
    response: Response,
    story_id: str = FPath(..., description="storyId from the registry"),
) -> Dict[str, Any]:
    _validate_story_id(story_id)
    registry = _load_registry()
    for s in registry.get("stories", []) or []:
        if s.get("storyId") == story_id:
            response.headers["Cache-Control"] = _CACHE_HEADER
            return s
    raise HTTPException(status_code=404, detail="Story not found in registry")


@router.get("/story-atlas/{story_id}/connections")
def get_story_connections(
    response: Response,
    story_id: str = FPath(..., description="storyId from the registry"),
) -> Dict[str, Any]:
    _validate_story_id(story_id)
    connections = _load_connections()
    items = [
        c
        for c in (connections.get("connections", []) or [])
        if c.get("sourceStoryId") == story_id
    ]
    response.headers["Cache-Control"] = _CACHE_HEADER
    return {
        "version": connections.get("version"),
        "generatedAt": connections.get("generatedAt"),
        "storyId": story_id,
        "total": len(items),
        "connections": items,
        "warnings": connections.get("warnings", []),
    }


@router.get("/story-atlas/{story_id}/cross-references")
def get_story_cross_references(
    response: Response,
    story_id: str = FPath(..., description="storyId from the registry"),
) -> Dict[str, Any]:
    """Return the evidence-backed cross-references for a story.

    Includes the strongest peer storyIds (from the neighbours index) plus
    the full edge objects with `evidence` so the UI can show *why* two
    stories are correlated (same prophet, overlapping ayahs, etc.).
    """
    _validate_story_id(story_id)
    registry = _load_registry()
    if not any(s.get("storyId") == story_id for s in (registry.get("stories", []) or [])):
        raise HTTPException(status_code=404, detail="Story not found in registry")

    cross = _load_cross_refs()
    edges_all = cross.get("edges", []) or []
    edges = [
        e
        for e in edges_all
        if e.get("sourceStoryId") == story_id or e.get("targetStoryId") == story_id
    ]
    edges.sort(key=lambda e: e.get("score", 0.0), reverse=True)

    neighbours = (cross.get("neighboursByStory") or {}).get(story_id, [])

    response.headers["Cache-Control"] = _CACHE_HEADER
    return {
        "version": cross.get("version"),
        "generatedAt": cross.get("generatedAt"),
        "storyId": story_id,
        "total": len(edges),
        "neighbours": neighbours,
        "edges": edges,
        "warnings": cross.get("warnings", []),
    }


@router.get("/story-atlas/cross-references/overview")
def get_cross_references_overview(response: Response) -> Dict[str, Any]:
    """Return registry-wide cross-reference stats for the dashboard."""
    cross = _load_cross_refs()
    response.headers["Cache-Control"] = _CACHE_HEADER
    return {
        "version": cross.get("version"),
        "generatedAt": cross.get("generatedAt"),
        "stats": cross.get("stats", {}),
        "weights": cross.get("weights", {}),
        "minScore": cross.get("minScore"),
        "warnings": cross.get("warnings", []),
    }
