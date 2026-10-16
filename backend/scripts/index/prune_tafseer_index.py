#!/usr/bin/env python3
"""
Prune stale points from the Qdrant tafseer collection.

A point is stale when it can no longer stand for a retrievable DB passage:

  orphan        payload chunk_id is missing or not in tafseer_chunks
  mismatch      payload source_id differs from the DB row's source
  placeholder   payload or DB text is a 'لا يوجد تفسير' placeholder (the
                vector embeds the placeholder even if the DB row was fixed)
  duplicate     a second point for a chunk that already has one
  unknown       source_id not in tafseer_sources
  disabled      source is_enabled != 1
  unlicensed    source enabled but license_verified != 1 (only deleted with
                --include-unlicensed: licences can be re-verified, and
                re-embedding costs HF credit; retrieval already ignores them)

Dry-run by default: prints per-source counts and coverage. ``--apply``
deletes the stale points and sets is_embedded=0 on DB chunks whose vector was
removed, so ``scripts/index/index_tafseer.py`` re-embeds them later. Nothing
is embedded here and no Hugging Face call is made.

Usage:
  python scripts/index/prune_tafseer_index.py            # dry run
  python scripts/index/prune_tafseer_index.py --apply
  python scripts/index/prune_tafseer_index.py --apply --include-unlicensed

Environment: DATABASE_URL, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.rag.retrieval import is_placeholder_text  # noqa: E402

SCROLL_PAGE = 1000
DELETE_BATCH = 500
ALWAYS_DELETE = ("orphan", "mismatch", "placeholder", "duplicate", "unknown", "disabled")


@dataclass
class SourceRow:
    is_enabled: int
    license_verified: int


@dataclass
class ChunkRow:
    id: int
    source_id: str
    has_text: bool      # some non-empty commentary
    placeholder: bool   # DB text is a placeholder

    @property
    def indexable(self) -> bool:
        return self.has_text and not self.placeholder


@dataclass
class Plan:
    """Classification of every point plus the coverage it implies."""
    reasons: Dict[object, str] = field(default_factory=dict)          # point id -> reason
    by_source: Dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    kept_chunks: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    total_points: int = 0

    def to_delete(self, include_unlicensed: bool, only: Optional[Set[str]] = None) -> List[object]:
        allowed = set(ALWAYS_DELETE) | ({"unlicensed"} if include_unlicensed else set())
        if only is not None:
            allowed &= only
        return [pid for pid, r in self.reasons.items() if r in allowed]


def classify(
    points: Iterable[dict],
    sources: Dict[str, SourceRow],
    chunks: Dict[str, ChunkRow],
) -> Plan:
    """Pure classification (no I/O) so it can be unit-tested."""
    plan = Plan()
    seen_chunk: Dict[str, object] = {}
    for point in points:
        plan.total_points += 1
        pid = point["id"]
        payload = point.get("payload") or {}
        source_id = payload.get("source_id") or "<none>"
        chunk_id = payload.get("chunk_id")
        texts = [payload.get("content_ar"), payload.get("content_en")]

        src = sources.get(source_id)
        row = chunks.get(str(chunk_id)) if chunk_id else None
        if src is None:
            reason = "unknown"
        elif src.is_enabled != 1:
            reason = "disabled"
        elif row is None:
            reason = "orphan"
        elif row.source_id != source_id:
            reason = "mismatch"
        elif any(is_placeholder_text(t) for t in texts if t) or row.placeholder:
            reason = "placeholder"
        elif str(chunk_id) in seen_chunk:
            reason = "duplicate"
        elif src.license_verified != 1:
            reason = "unlicensed"
        else:
            reason = "ok"

        plan.by_source[source_id][reason] += 1
        if reason == "ok":
            seen_chunk[str(chunk_id)] = pid
            plan.kept_chunks[source_id].add(str(chunk_id))
        else:
            plan.reasons[pid] = reason
    return plan


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _sync_db_url() -> str:
    url = os.getenv("DATABASE_URL", settings.database_url)
    return url.replace("postgresql+asyncpg://", "postgresql://")


def load_db() -> Tuple[Dict[str, SourceRow], Dict[str, ChunkRow]]:
    import psycopg2

    with psycopg2.connect(_sync_db_url(), connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, COALESCE(is_enabled, 0), COALESCE(license_verified, 0) FROM tafseer_sources")
        sources = {sid: SourceRow(int(en), int(lic)) for sid, en, lic in cur.fetchall()}
        cur.execute("SELECT id, chunk_id, source_id, content_ar, content_en FROM tafseer_chunks")
        chunks = {}
        for pk, chunk_id, source_id, ar, en in cur.fetchall():
            texts = [t for t in (ar, en) if t and t.strip()]
            chunks[chunk_id] = ChunkRow(pk, source_id, bool(texts), any(is_placeholder_text(t) for t in texts))
    return sources, chunks


def scroll_points(client: httpx.Client, base: str, collection: str) -> List[dict]:
    points: List[dict] = []
    offset = None
    while True:
        body = {
            "limit": SCROLL_PAGE,
            "with_payload": ["chunk_id", "source_id", "content_ar", "content_en"],
            "with_vector": False,
        }
        if offset is not None:
            body["offset"] = offset
        r = client.post(f"{base}/collections/{collection}/points/scroll", json=body)
        r.raise_for_status()
        result = r.json()["result"]
        points.extend(result.get("points", []))
        offset = result.get("next_page_offset")
        if offset is None:
            return points


def delete_points(client: httpx.Client, base: str, collection: str, ids: List[object]) -> None:
    for start in range(0, len(ids), DELETE_BATCH):
        batch = ids[start:start + DELETE_BATCH]
        r = client.post(
            f"{base}/collections/{collection}/points/delete",
            params={"wait": "true"},
            json={"points": batch},
        )
        r.raise_for_status()


def reset_is_embedded(chunk_pks: List[int]) -> int:
    if not chunk_pks:
        return 0
    import psycopg2

    with psycopg2.connect(_sync_db_url(), connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE tafseer_chunks SET is_embedded = 0 WHERE id = ANY(%s) AND is_embedded <> 0",
            (chunk_pks,),
        )
        return cur.rowcount


def report(plan: Plan, sources: Dict[str, SourceRow], chunks: Dict[str, ChunkRow], title: str) -> None:
    db_usable = Counter(c.source_id for c in chunks.values() if c.indexable)
    reasons = ["ok", "unlicensed", *ALWAYS_DELETE]
    print(f"\n== {title}: {plan.total_points} points ==")
    header = f"{'source':<16}{'enabled':>8}{'licensed':>9}" + "".join(f"{r:>12}" for r in reasons) + f"{'coverage':>22}"
    print(header)
    for sid in sorted(set(plan.by_source) | set(sources)):
        src = sources.get(sid)
        counts = plan.by_source.get(sid, Counter())
        covered = len(plan.kept_chunks.get(sid, ())) + (counts["unlicensed"] if src and src.license_verified != 1 else 0)
        total = db_usable.get(sid, 0)
        cov = f"{covered}/{total} ({100 * covered / total:.1f}%)" if total else "-"
        print(
            f"{sid:<16}{(src.is_enabled if src else '-'):>8}{(src.license_verified if src else '-'):>9}"
            + "".join(f"{counts[r]:>12}" for r in reasons)
            + f"{cov:>22}"
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prune stale Qdrant tafseer points (dry-run by default)")
    parser.add_argument("--apply", action="store_true", help="delete the stale points")
    parser.add_argument("--include-unlicensed", action="store_true",
                        help="also delete points of enabled sources whose licence is not verified")
    parser.add_argument("--only", type=lambda v: {r.strip() for r in v.split(",") if r.strip()},
                        help="restrict deletion to these reasons, comma-separated (e.g. orphan,placeholder: "
                             "keeps disabled-source vectors, which retrieval already ignores, for a later re-enable)")
    args = parser.parse_args(argv)

    collection = os.getenv("QDRANT_COLLECTION", settings.qdrant_collection_tafseer)
    base = f"http://{os.getenv('QDRANT_HOST', settings.qdrant_host)}:{os.getenv('QDRANT_PORT', settings.qdrant_port)}"

    sources, chunks = load_db()
    with httpx.Client(timeout=60.0) as client:
        points = scroll_points(client, base, collection)
        plan = classify(points, sources, chunks)
        report(plan, sources, chunks, f"{collection} BEFORE")

        doomed = plan.to_delete(args.include_unlicensed, args.only)
        by_reason = Counter(plan.reasons[p] for p in doomed)
        print(f"\nStale points to delete: {len(doomed)} {dict(by_reason)}")
        if not args.apply:
            print("Dry run: nothing deleted. Re-run with --apply to delete.")
            return 0

        # chunks whose only vector is being removed must be re-embedded later
        pk_by_chunk = {cid: row.id for cid, row in chunks.items()}
        doomed_set = set(doomed)
        lost: Set[int] = set()
        for point in points:
            if point["id"] in doomed_set:
                cid = str((point.get("payload") or {}).get("chunk_id") or "")
                if cid in pk_by_chunk and cid not in plan.kept_chunks.get(chunks[cid].source_id, set()):
                    lost.add(pk_by_chunk[cid])

        delete_points(client, base, collection, doomed)
        reset = reset_is_embedded(sorted(lost))
        print(f"Deleted {len(doomed)} points; reset is_embedded on {reset} chunks.")

        after = classify(scroll_points(client, base, collection), sources, chunks)
        report(after, sources, chunks, f"{collection} AFTER")
    return 0


if __name__ == "__main__":
    sys.exit(main())
