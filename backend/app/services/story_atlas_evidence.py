"""
Story-atlas evidence: only enabled, licence-verified tafsir is ever cited.

``story_events.evidence`` is a list of ``{"source_id", "reference"}`` pointers
(optionally ``chunk_id``). An entry is public only when it resolves to a real
chunk of an enabled, licence-verified tafsir source that covers the cited
verse. Anything else (a disabled or blocked source such as the unlicensed
English Ibn Kathir, an unparsable reference, a verse the source has no
passage for) is dropped, and no free-text ``snippet`` is ever passed through:
evidence is a pointer to the tafsir, the text itself comes from the tafsir
reader.

The same rules are used three times:
- at read time by ``StoryAtlasService`` (defence in depth),
- by ``scripts/ingest/seed_story_atlas.py`` when it writes events,
- by alembic ``r4a1b2c3d4e5`` for rows already in the database.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from sqlalchemy import text

# A verse reference "S:A" or "S:A-B".
REF_RE = re.compile(r"^(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?$")

# Legacy citation -> the enabled edition of the *same work*. The English Ibn
# Kathir is a translation of the Arabic tafsir; citing the Arabic original at
# the same verse is the same tafsir. Another scholar is never substituted.
SAME_WORK_EDITION = {"ibn_kathir_en": "ibn_kathir_ar"}

PUBLIC_KEYS = ("source_id", "reference", "chunk_id")

# Indices of the candidate pointers that resolve to an enabled, licensed chunk.
_RESOLVE_SQL = """
SELECT r.i
  FROM unnest(CAST(:src AS text[]), CAST(:sura AS int[]), CAST(:a AS int[]),
              CAST(:b AS int[]), CAST(:cid AS text[])) WITH ORDINALITY AS r(src, s, a, b, cid, i)
 WHERE EXISTS (SELECT 1 FROM tafseer_sources ts
                WHERE ts.id = r.src AND ts.is_enabled = 1 AND ts.license_verified = 1)
   AND CASE WHEN r.cid IS NOT NULL
            THEN EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = r.cid AND c.source_id = r.src)
            ELSE EXISTS (SELECT 1 FROM tafseer_chunks c
                          WHERE c.source_id = r.src AND c.sura_no = r.s
                            AND c.aya_start <= r.b AND c.aya_end >= r.a) END
"""


def parse_reference(ref: Any) -> Optional[tuple[int, int, int]]:
    """'18:71' -> (18, 71, 71); '18:71-73' -> (18, 71, 73); else None."""
    m = REF_RE.match(str(ref or "").strip())
    if not m:
        return None
    s, a = int(m.group(1)), int(m.group(2))
    b = int(m.group(3)) if m.group(3) else a
    if not (1 <= s <= 114 and 1 <= a <= b <= 286):
        return None
    return s, a, b


def _candidate(entry: Any) -> Optional[dict]:
    """Public shape of one pointer, or None when it cannot be a pointer."""
    if not isinstance(entry, dict) or not entry.get("source_id"):
        return None
    out = {k: entry[k] for k in PUBLIC_KEYS if entry.get(k)}
    if "chunk_id" not in out and parse_reference(out.get("reference")) is None:
        return None
    return out


def _params(cands: list[dict]) -> dict:
    src, sura, a, b, cid = [], [], [], [], []
    for c in cands:
        ref = parse_reference(c.get("reference")) or (0, 0, 0)
        src.append(c["source_id"])
        sura.append(ref[0])
        a.append(ref[1])
        b.append(ref[2])
        cid.append(c.get("chunk_id"))
    return {"src": src, "sura": sura, "a": a, "b": b, "cid": cid}


def _split(evidence_lists: Iterable[Any]) -> tuple[list[list[Optional[dict]]], list[dict]]:
    shaped = [[_candidate(e) for e in (ev if isinstance(ev, list) else [])] for ev in evidence_lists]
    flat = [c for lst in shaped for c in lst if c is not None]
    return shaped, flat


def _rejoin(shaped: list[list[Optional[dict]]], ok: set[int]) -> list[list[dict]]:
    out, n = [], 0
    for lst in shaped:
        kept = []
        for c in lst:
            if c is None:
                continue
            n += 1  # ordinality is 1-based
            if n in ok:
                kept.append(c)
        out.append(kept)
    return out


async def filter_licensed_evidence(session, evidence_lists: list[Any]) -> list[list[dict]]:
    """Keep, per list, only the pointers that resolve to enabled, licensed tafsir."""
    shaped, flat = _split(evidence_lists)
    if not flat:
        return [[] for _ in shaped]
    rows = await session.execute(text(_RESOLVE_SQL), _params(flat))
    return _rejoin(shaped, {int(r[0]) for r in rows})


def remap_same_work(evidence: Any) -> list[Any]:
    """Point legacy citations at the enabled edition of the same work."""
    out = []
    for e in evidence if isinstance(evidence, list) else []:
        if isinstance(e, dict) and e.get("source_id") in SAME_WORK_EDITION:
            e = {k: v for k, v in e.items() if k not in ("chunk_id", "snippet")}
            e["source_id"] = SAME_WORK_EDITION[e["source_id"]]
        out.append(e)
    return out


def resolve_seed_evidence_sync(session, evidence_lists: list[Any]) -> list[list[dict]]:
    """Seeder variant (sync session): remap same-work legacy ids, then filter."""
    shaped, flat = _split([remap_same_work(ev) for ev in evidence_lists])
    if not flat:
        return [[] for _ in shaped]
    rows = session.execute(text(_RESOLVE_SQL), _params(flat))
    return _rejoin(shaped, {int(r[0]) for r in rows})
