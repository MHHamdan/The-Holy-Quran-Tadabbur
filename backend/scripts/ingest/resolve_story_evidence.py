#!/usr/bin/env python3
"""
Resolve story tafsir evidence to real tafseer_chunks ids.

data/manifests/stories.json cites evidence with legacy, human-readable ids
such as ``ibn_kathir:2:30-33`` and source ids {ibn_kathir, tabari, qurtubi,
saadi}. None of them exist in ``tafseer_chunks`` (hash chunk ids; source ids
ibn_kathir_ar / ibn_kathir_en / tabari_ar / qurtubi_ar / ...), so
``story_segments.evidence_chunk_ids`` was NULL for every row and the UI could
only show bare "ibn_kathir" chips.

This script maps each legacy citation to the chunks of the corresponding
corpus sources that cover the cited ayah range, and writes the chunk ids to:

  - story_segments.evidence_chunk_ids
  - cross_story_connections.evidence_chunk_ids

Rules:
  - Legacy -> corpus mapping only ({ibn_kathir: [ibn_kathir_ar, ibn_kathir_en],
    tabari: [tabari_ar], qurtubi: [qurtubi_ar]}). A legacy source with no
    corpus counterpart (saadi) is DROPPED with a warning — another tafsir is
    never substituted for it.
  - Only sources that are enabled in tafseer_sources are used.
  - No tafsir text is generated or copied; only ids are written.
  - Idempotent: re-running recomputes the same ids from the manifest.

Usage:
  python scripts/ingest/resolve_story_evidence.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
MANIFEST = PROJECT_ROOT / "data" / "manifests" / "stories.json"

# Legacy manifest source id -> tafseer_chunks source ids.
LEGACY_SOURCE_MAP: Dict[str, Tuple[str, ...]] = {
    "ibn_kathir": ("ibn_kathir_ar", "ibn_kathir_en"),
    "tabari": ("tabari_ar",),
    "qurtubi": ("qurtubi_ar",),
}
# Legacy sources that have no corpus counterpart: dropped, never substituted.
UNAVAILABLE_LEGACY_SOURCES = frozenset({"saadi"})

_REF_RE = re.compile(r"^(?:(?P<src>[a-z_]+):)?(?P<s>\d{1,3}):(?P<a>\d{1,3})(?:-(?P<b>\d{1,3}))?$")

Citation = Tuple[str, int, int, int]  # (legacy_source, sura, aya_start, aya_end)


def parse_ref(ref: str) -> Optional[Tuple[Optional[str], int, int, int]]:
    """Parse ``src:S:A-B`` / ``S:A-B`` / ``S:A`` into (src|None, S, A, B)."""
    m = _REF_RE.match((ref or "").strip())
    if not m:
        return None
    s, a = int(m.group("s")), int(m.group("a"))
    b = int(m.group("b")) if m.group("b") else a
    if not (1 <= s <= 114) or a < 1 or b < a:
        return None
    return m.group("src"), s, a, b


def segment_citations(segment: dict) -> List[Citation]:
    """Legacy citations of one manifest segment (source + ayah range)."""
    out: List[Citation] = []
    for ev in segment.get("evidence") or []:
        src = ev.get("source_id")
        parsed = parse_ref(ev.get("ayah_ref") or "") or parse_ref(ev.get("chunk_id") or "")
        if not src or not parsed:
            continue
        _, s, a, b = parsed
        out.append((src, s, a, b))
    return out


def connection_citations(conn: dict) -> List[Citation]:
    """Legacy citations of one inter_story connection (``src:S:A-B`` strings)."""
    out: List[Citation] = []
    for ref in conn.get("evidence_chunk_ids") or []:
        parsed = parse_ref(ref)
        if not parsed or not parsed[0]:
            continue
        src, s, a, b = parsed
        out.append((src, s, a, b))
    return out


def corpus_sources_for(legacy: str, enabled: Iterable[str]) -> Tuple[str, ...]:
    enabled_set = set(enabled)
    return tuple(s for s in LEGACY_SOURCE_MAP.get(legacy, ()) if s in enabled_set)


def plan(manifest: dict) -> Tuple[Dict[str, List[Citation]], Dict[Tuple[str, str, str], List[Citation]], List[str]]:
    """Return (segment_id -> citations, (src_story, tgt_story, type) -> citations, warnings)."""
    warnings: List[str] = []
    seg_plan: Dict[str, List[Citation]] = {}
    dropped = defaultdict(int)
    for story in manifest.get("stories", []):
        for seg in story.get("segments", []):
            cits = []
            for c in segment_citations(seg):
                if c[0] in UNAVAILABLE_LEGACY_SOURCES or c[0] not in LEGACY_SOURCE_MAP:
                    dropped[c[0]] += 1
                    continue
                cits.append(c)
            seg_plan[seg["id"]] = cits
    conn_plan: Dict[Tuple[str, str, str], List[Citation]] = {}
    for conn in manifest.get("inter_story_connections", []):
        cits = [c for c in connection_citations(conn) if c[0] in LEGACY_SOURCE_MAP]
        key = (conn["source_story_id"], conn["target_story_id"], conn.get("connection_type", "thematic"))
        conn_plan[key] = cits
        if conn.get("bidirectional"):
            conn_plan[(key[1], key[0], key[2])] = cits
    for src, n in sorted(dropped.items()):
        warnings.append(f"dropped {n} citation(s) of '{src}': no corpus source (not substituted)")
    return seg_plan, conn_plan, warnings


def _db_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url)


def _chunk_ids(cur, sources: Sequence[str], sura: int, a: int, b: int) -> List[str]:
    if not sources:
        return []
    cur.execute(
        """
        SELECT chunk_id FROM tafseer_chunks
        WHERE source_id = ANY(%s) AND sura_no = %s AND aya_start <= %s AND aya_end >= %s
        ORDER BY source_id, aya_start, chunk_order
        """,
        (list(sources), sura, b, a),
    )
    return [r[0] for r in cur.fetchall()]


def resolve(dry_run: bool = False) -> int:
    import psycopg2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seg_plan, conn_plan, warnings = plan(manifest)
    for w in warnings:
        print(f"  WARNING: {w}")

    conn = psycopg2.connect(_db_url())
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tafseer_sources WHERE is_enabled = 1")
        enabled = [r[0] for r in cur.fetchall()]

        def resolve_citations(cits: List[Citation]) -> List[str]:
            ids: List[str] = []
            for legacy, s, a, b in cits:
                for cid in _chunk_ids(cur, corpus_sources_for(legacy, enabled), s, a, b):
                    if cid not in ids:
                        ids.append(cid)
            return ids

        cur.execute("SELECT id FROM story_segments")
        db_segments = {r[0] for r in cur.fetchall()}
        seg_updates = 0
        seg_with_evidence = 0
        for seg_id, cits in seg_plan.items():
            if seg_id not in db_segments:
                continue
            ids = resolve_citations(cits)
            if ids:
                seg_with_evidence += 1
            if not dry_run:
                cur.execute(
                    "UPDATE story_segments SET evidence_chunk_ids = %s WHERE id = %s",
                    (ids or None, seg_id),
                )
            seg_updates += 1

        cur.execute("SELECT id, source_story_id, target_story_id, connection_type FROM cross_story_connections")
        conn_updates = 0
        for row_id, src, tgt, ctype in cur.fetchall():
            cits = conn_plan.get((src, tgt, ctype))
            if cits is None:
                continue
            ids = resolve_citations(cits)
            if not dry_run and ids:
                cur.execute(
                    "UPDATE cross_story_connections SET evidence_chunk_ids = %s WHERE id = %s",
                    (ids, row_id),
                )
            conn_updates += 1 if ids else 0

        if dry_run:
            conn.rollback()
        else:
            conn.commit()
        print(
            f"  segments: {seg_updates} in DB, {seg_with_evidence} with resolved evidence; "
            f"cross-story connections updated: {conn_updates}{' (dry run)' if dry_run else ''}"
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(resolve(dry_run="--dry-run" in sys.argv))
