#!/usr/bin/env python3
"""
Content coverage and provenance report (release gates RG-04, RG-28).

Computes, deterministically, from the Postgres DB and the repository data:
  * Qur'an text: surahs, ayat, DB text == canonical Tanzil text
  * translations: ayat covered / 6236 per edition, with licence
  * tafsir: ayat covered / 6236 per DB source (chunk ranges), licence status,
    user visibility; plus the externally proxied editions of the reader panel
  * audio: reciters x per-verse URL scheme (optional stream probe)
  * stories, themes, concepts: counts, ayah coverage, evidence coverage
  * duas / adhkar: citation coverage and exact match against canonical text
  * UI i18n (frontend/src/i18n/translations.ts): ar/en parity and quality
  * provenance: every enabled religious source has title, author, language,
    source and licence

Usage:
  python3 scripts/content_coverage_report.py [--out report.json] [--probe-audio]

Reads DATABASE_URL from the environment or from .env. Needs `npx tsx` for the
TypeScript data modules. Output is sorted and contains no timestamps unless
--probe-audio is passed (network results can vary).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOTAL_AYAT = 6236
TOTAL_SURAHS = 114
AR_LETTER = re.compile(r"[ء-يٱ-ۓ]")
VERSE_SEP = " ۝ "


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        sys.exit("DATABASE_URL not set")
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url)


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def ts_dump() -> dict:
    """Evaluate the TypeScript data modules with tsx and return them as JSON."""
    fe = ROOT / "frontend" / "src"
    code = f"""
import * as i18n from '{fe}/i18n/translations.ts';
import {{ QURANIC_DUAS }} from '{fe}/data/quranicDuas.ts';
import {{ ADHKAR }} from '{fe}/data/adhkar.ts';
import {{ SOURCE_REGISTRY }} from '{fe}/data/sourceRegistry.ts';
import {{ TAFSIR_EDITIONS }} from '{fe}/components/quran/tafsirEditions.tsx';
const dicts: Record<string, unknown> = {{}};
for (const [k, v] of Object.entries(i18n)) if (v && typeof v === 'object') dicts[k] = v;
console.log(JSON.stringify({{ i18n: dicts, duas: QURANIC_DUAS, adhkar: ADHKAR,
  registry: SOURCE_REGISTRY, panelEditions: TAFSIR_EDITIONS }}));
"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "dump.ts"
        f.write_text(code)
        out = subprocess.run(
            ["npx", "--yes", "tsx", str(f)], cwd=ROOT / "frontend",
            capture_output=True, text=True, timeout=300,
        )
    if out.returncode != 0:
        sys.exit(f"tsx failed: {out.stderr[-2000:]}")
    line = [l for l in out.stdout.splitlines() if l.startswith("{")][-1]
    return json.loads(line)


def expand(sura, a, b, valid: set) -> set:
    if sura is None or a is None:
        return set()
    b = a if b is None else b
    return {(sura, x) for x in range(a, b + 1) if (sura, x) in valid}


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

async def quran_section(c, tanzil):
    rows = await c.fetch("select id, sura_no, aya_no, text_uthmani from quran_verses")
    canon = {(v["sura_no"], v["aya_no"]): v["aya_text"] for v in tanzil["verses"]}
    db = {(r["sura_no"], r["aya_no"]): r["text_uthmani"] for r in rows}
    exact = sum(1 for k, t in canon.items() if db.get(k) == t)
    mism = sorted(f"{s}:{a}" for (s, a), t in canon.items() if db.get((s, a)) != t)
    return {
        "canonical_file": "data/raw/quran_tanzil.json",
        "canonical_surahs": len({k[0] for k in canon}),
        "canonical_ayat": len(canon),
        "db_surahs": len({k[0] for k in db}),
        "db_ayat": len(db),
        "db_empty_text": sum(1 for t in db.values() if not (t or "").strip()),
        "db_exact_match_canonical": exact,
        "db_exact_match_pct": pct(exact, len(canon)),
        "db_mismatch_refs_sample": mism[:20],
    }, {r["id"]: (r["sura_no"], r["aya_no"]) for r in rows}, set(db)


async def translations_section(c, id2ref):
    manifest = load_json("data/manifests/translation_sources.json")
    m_ed = {e["key"]: e for e in manifest.get("editions", [])}
    eds = await c.fetch("select * from translation_editions order by key")
    cov = await c.fetch(
        "select translator, count(distinct verse_id) n from translations "
        "where coalesce(btrim(text),'') <> '' group by translator"
    )
    covd = {r["translator"]: r["n"] for r in cov}
    out = []
    for e in eds:
        n = covd.get(e["key"], 0)
        out.append({
            "key": e["key"], "language": e["language"], "title": e["title"],
            "translator": e["translator_name"], "version": e["version"],
            "source_url": e["source_url"], "licence": e["license"],
            "licence_status": manifest.get("license_status"),
            "in_manifest": e["key"] in m_ed, "is_default": e["is_default"],
            "ayat_covered": n, "coverage_pct": pct(n, TOTAL_AYAT),
        })
    orphan = sorted(set(covd) - {e["key"] for e in eds})
    return {"editions": out, "edition_count": len(out),
            "editions_at_100pct": sum(1 for e in out if e["ayat_covered"] == TOTAL_AYAT),
            "translator_keys_without_edition_row": orphan,
            "manifest_editions_missing_in_db": sorted(set(m_ed) - {e["key"] for e in eds})}


async def tafsir_section(c, valid, ts):
    manifest = load_json("data/manifests/tafseer_sources.json")
    m_src = {s["id"]: s for s in manifest["sources"]}
    srcs = await c.fetch("select * from tafseer_sources order by id")
    chunks = await c.fetch(
        "select source_id, sura_no, aya_start, aya_end from tafseer_chunks "
        "where coalesce(btrim(content_ar),'') <> '' or coalesce(btrim(content_en),'') <> ''"
    )
    per = defaultdict(set)
    bad = Counter()
    for r in chunks:
        e = expand(r["sura_no"], r["aya_start"], r["aya_end"], valid)
        if not e:
            bad[r["source_id"]] += 1
        per[r["source_id"]] |= e
    db_sources = []
    for s in srcs:
        n = len(per.get(s["id"], ()))
        ml = (m_src.get(s["id"]) or {}).get("license") or {}
        visible = bool(s["is_enabled"]) and bool(s["license_verified"])
        db_sources.append({
            "id": s["id"], "title": s["name_en"], "author": s["author_en"],
            "language": s["language"], "enabled": bool(s["is_enabled"]),
            "user_visible_db_routes": visible,
            "db_licence": s["license"], "db_licence_type": s["license_type"],
            "db_licence_verified": bool(s["license_verified"]),
            "manifest_status": (m_src.get(s["id"]) or {}).get("status"),
            "manifest_licence_type": ml.get("type"),
            "manifest_licence_url": ml.get("license_url"),
            "manifest_has_provenance": bool((m_src.get(s["id"]) or {}).get("provenance")),
            "in_manifest_enabled_ids": s["id"] in manifest.get("enabled_ids", []),
            "ayat_covered": n, "coverage_pct": pct(n, TOTAL_AYAT),
            "missing_ayat": TOTAL_AYAT - n,
            "chunks_with_invalid_range": bad.get(s["id"], 0),
        })
    db_ids = {s["id"] for s in srcs}
    enabled_ids = manifest.get("enabled_ids", [])
    # externally proxied editions shown in the reader's tafsir panel
    reg = {r["sourceId"]: r for r in ts["registry"]}
    panel = []
    for e in ts["panelEditions"]:
        dbid = e.get("db_source_id")
        guess = dbid or f"{e['id']}_ar"
        ml = (m_src.get(guess) or {}).get("license") or {}
        panel.append({
            "id": e["id"], "db_source_id": dbid, "title": e["name_en"],
            "author": e["author_en"], "language": e["language"], "host": e["source"],
            "registry_entry": dbid in reg if dbid else False,
            "footer_licence_shown": (reg[dbid]["licenseOrTerms"] if dbid in reg else "not yet recorded"),
            "manifest_id_checked": guess, "manifest_status": (m_src.get(guess) or {}).get("status"),
            "manifest_licence_type": ml.get("type"),
        })
    return {
        "db_sources": db_sources,
        "enabled_sources": [s["id"] for s in db_sources if s["enabled"]],
        "enabled_full_quran_ge_99pct": {s["id"]: s["coverage_pct"] >= 99.0 for s in db_sources if s["enabled"]},
        "manifest_enabled_ids": enabled_ids,
        "manifest_enabled_ids_missing_in_db": sorted(set(enabled_ids) - db_ids),
        "db_enabled_not_in_manifest_enabled_ids": sorted(
            s["id"] for s in db_sources if s["enabled"] and s["id"] not in enabled_ids),
        "reader_panel_editions_external": panel,
    }


def audio_section(probe: bool):
    sys.path.insert(0, str(ROOT / "backend"))
    from app.services import audio_service as au  # noqa: E402

    counts = au.SURAH_VERSE_COUNTS
    reciters = []
    for key, info in sorted(au.RECITERS.items(), key=lambda kv: kv[1].id):
        reciters.append({
            "id": info.id, "name_en": info.name_en, "style": info.style,
            "primary_scheme": f"{au.EVERYAYAH_BASE}/{info.everyayah_folder}/{{SSS}}{{AAA}}.mp3",
            "fallback_scheme": (f"{au.ALQURAN_CLOUD_BASE}/{info.alquran_cloud_bitrate}/"
                                f"{info.alquran_cloud_id}/{{absolute}}.mp3") if info.alquran_cloud_id else None,
            "verse_urls_constructible": sum(counts),
        })
    res = {
        "reciters": reciters, "reciter_count": len(reciters),
        "surah_verse_table_total": sum(counts), "surah_verse_table_surahs": len(counts),
        "verse_url_coverage_pct": pct(sum(counts), TOTAL_AYAT) if len(counts) == TOTAL_SURAHS else 0.0,
        "stream_probe": None,
    }
    if probe:
        import httpx
        samples = [(1, 1), (2, 255), (2, 286), (18, 110), (114, 6)]
        probe_out = []
        with httpx.Client(timeout=15, follow_redirects=True) as cl:
            for r, (key, info) in zip(reciters, sorted(au.RECITERS.items(), key=lambda kv: kv[1].id)):
                for s, a in samples:
                    url = f"{au.EVERYAYAH_BASE}/{info.everyayah_folder}/{s:03d}{a:03d}.mp3"
                    try:
                        resp = cl.head(url)
                        st, ct = resp.status_code, resp.headers.get("content-type", "")
                    except Exception as ex:  # network unavailable etc.
                        st, ct = f"error:{type(ex).__name__}", ""
                    probe_out.append({"reciter": info.id, "ref": f"{s}:{a}", "status": st, "content_type": ct})
        ok = sum(1 for p in probe_out if p["status"] == 200 and "audio" in p["content_type"])
        res["stream_probe"] = {"checked": len(probe_out), "ok_audio": ok, "results": probe_out}
    return res


async def stories_section(c, valid):
    stories = await c.fetchval("select count(*) from stories")
    segs = await c.fetch("select id, story_id, sura_no, aya_start, aya_end, evidence_sources, "
                         "evidence_chunk_ids from story_segments")
    ayat, valid_ref, with_ev = set(), 0, 0
    for s in segs:
        e = expand(s["sura_no"], s["aya_start"], s["aya_end"], valid)
        if e:
            valid_ref += 1
        ayat |= e
        if s["evidence_chunk_ids"]:
            with_ev += 1
    ev = await c.fetchrow(
        "with ids as (select distinct unnest(evidence_chunk_ids) cid from story_segments) "
        "select count(*) total, count(c.chunk_id) resolved, "
        "count(*) filter (where s.is_enabled = 1) enabled_src, "
        "count(*) filter (where s.is_enabled = 0) disabled_src "
        "from ids left join tafseer_chunks c on c.chunk_id = ids.cid "
        "left join tafseer_sources s on s.id = c.source_id")
    ev_src = await c.fetch(
        "select e->>'source_id' sid, count(*) n from story_segments, jsonb_array_elements("
        "case when jsonb_typeof(evidence_sources)='array' then evidence_sources else '[]'::jsonb end) e "
        "group by 1 order by 1")
    rel = {}
    for t in ("story_connections", "cross_story_connections", "event_connections", "theme_connections"):
        r = await c.fetchrow(f"select count(*) n, count(*) filter (where cardinality(evidence_chunk_ids) > 0) ev from {t}")
        ids = await c.fetchrow(
            f"with ids as (select distinct unnest(evidence_chunk_ids) cid from {t}) "
            "select count(*) total, count(c.chunk_id) resolved, "
            "count(*) filter (where s.is_enabled = 1) enabled_src, "
            "count(*) filter (where ids.cid like '%\\_en:%' or ids.cid like 'ibn_kathir_en%' "
            "or ids.cid like 'jalalayn_en%') disabled_prefix "
            "from ids left join tafseer_chunks c on c.chunk_id = ids.cid "
            "left join tafseer_sources s on s.id = c.source_id")
        rel[t] = {"total": r["n"], "with_evidence": r["ev"], "evidence_pct": pct(r["ev"], r["n"]),
                  "distinct_evidence_ids": ids["total"], "ids_resolving_to_chunk": ids["resolved"],
                  "ids_resolving_to_enabled_source": ids["enabled_src"],
                  "ids_naming_disabled_en_source": ids["disabled_prefix"]}
    r = await c.fetchrow("select count(*) n, count(*) filter (where evidence is not null and "
                         "evidence::text not in ('null','[]','{}')) ev from story_events")
    rel["story_events"] = {"total": r["n"], "with_evidence": r["ev"], "evidence_pct": pct(r["ev"], r["n"])}
    stories_with_segments = len({s["story_id"] for s in segs})
    return {
        "stories": stories, "stories_with_segments": stories_with_segments,
        "segments": len(segs), "segments_valid_ayah_ref": valid_ref,
        "segments_with_evidence_chunks": with_ev,
        "segments_with_evidence_chunks_pct": pct(with_ev, len(segs)),
        "distinct_linked_ayat": len(ayat), "distinct_linked_ayat_pct": pct(len(ayat), TOTAL_AYAT),
        "evidence_chunk_ids": dict(ev),
        "evidence_sources_cited": {r["sid"]: r["n"] for r in ev_src},
        "relations": rel,
    }


async def themes_section(c, valid):
    themes = await c.fetch("select id, segment_count from quranic_themes")
    segs = await c.fetch("select theme_id, sura_no, ayah_start, ayah_end, evidence_sources, "
                         "evidence_chunk_ids, is_verified from theme_segments")
    ayat = set()
    sourced = 0
    for s in segs:
        ayat |= expand(s["sura_no"], s["ayah_start"], s["ayah_end"], valid)
        if s["evidence_chunk_ids"] or (s["evidence_sources"] and s["evidence_sources"] not in ("[]", "null")):
            sourced += 1
    with_seg = len({s["theme_id"] for s in segs})
    legacy = await c.fetchval("select count(*) from themes")
    ev = await c.fetchrow(
        "with ids as (select distinct unnest(evidence_chunk_ids) cid from theme_segments) "
        "select count(*) total, count(c.chunk_id) resolved from ids "
        "left join tafseer_chunks c on c.chunk_id = ids.cid")
    return {
        "quranic_themes": len(themes), "themes_with_segments": with_seg,
        "themes_with_segments_pct": pct(with_seg, len(themes)),
        "theme_segments": len(segs), "sourced_segments": sourced,
        "verified_segments": sum(1 for s in segs if s["is_verified"]),
        "distinct_ayat": len(ayat), "distinct_ayat_pct": pct(len(ayat), TOTAL_AYAT),
        "legacy_themes_table": legacy,
        "distinct_evidence_ids": ev["total"], "evidence_ids_resolving_to_chunk": ev["resolved"],
    }


async def concepts_section(c, valid):
    n = await c.fetchval("select count(*) from concepts")
    assoc = await c.fetch("select evidence_refs, has_sufficient_evidence from associations")
    with_ayah = sum(1 for a in assoc if (json.loads(a["evidence_refs"]) if isinstance(a["evidence_refs"], str)
                                          else (a["evidence_refs"] or {})).get("ayah_refs"))
    occ = await c.fetch("select concept_id, sura_no, ayah_start, ayah_end, evidence_chunk_ids, is_verified from occurrences")
    ayat = set()
    for o in occ:
        ayat |= expand(o["sura_no"], o["ayah_start"], o["ayah_end"], valid)
    curated = load_json("data/concepts/curated_concepts.json")
    curated_n = len(curated.get("concepts", curated)) if isinstance(curated, (dict, list)) else None
    return {
        "concepts": n, "curated_file_concepts": curated_n,
        "concepts_with_occurrences": len({o["concept_id"] for o in occ}),
        "relationships": len(assoc),
        "relationships_sufficient_evidence": sum(1 for a in assoc if a["has_sufficient_evidence"]),
        "relationships_with_ayah_refs": with_ayah,
        "occurrences": len(occ),
        "occurrences_with_ayah_ref": sum(1 for o in occ if o["sura_no"] is not None),
        "occurrences_with_evidence_chunks": sum(1 for o in occ if o["evidence_chunk_ids"]),
        "occurrences_verified": sum(1 for o in occ if o["is_verified"]),
        "citation_coverage_pct": pct(sum(1 for o in occ if o["sura_no"] is not None or o["evidence_chunk_ids"]), len(occ)),
        "distinct_ayat": len(ayat),
    }


def segment_in_verse(seg: str, verse: str) -> bool:
    return f" {seg.strip()} " in f" {verse.strip()} "


def duas_section(ts, tanzil):
    canon = {(v["sura_no"], v["aya_no"]): v["aya_text"] for v in tanzil["verses"]}
    simple = {(v["sura_no"], v["aya_no"]): v["aya_text_emlaey"] for v in tanzil["verses"]}
    names = {v["sura_no"]: v["sura_name_en"] for v in tanzil["verses"]}
    duas = ts["duas"]
    cited = exact = full = 0
    fails = []
    for d in duas:
        s, a = d.get("surah"), d.get("ayah")
        b = d.get("ayahEnd") or a
        ok_ref = bool(s and a and all((s, x) in canon for x in range(a, b + 1)) and d.get("surahNameEn"))
        cited += ok_ref
        segs = (d.get("ayatUthmani") or "").split(VERSE_SEP)
        good = ok_ref and len(segs) == (b - a + 1) and all(
            seg and segment_in_verse(seg, canon[(s, a + i)]) for i, seg in enumerate(segs))
        exact += good
        if good and all(seg.strip() == canon[(s, a + i)].strip() for i, seg in enumerate(segs)):
            full += 1
        if not good:
            fails.append(d.get("id"))
    # backend export parity
    be = load_json("backend/app/data/duas.json")["duas"]
    fe = {d["id"]: d for d in duas}
    be_mismatch = sorted(x["id"] for x in be if x["id"] not in fe or x.get("excerptUthmani") != fe[x["id"]].get("ayatUthmani"))
    # adhkar
    adh = ts["adhkar"]
    q_adh = [x for x in adh if x.get("quranRefs")]
    nq_adh = [x for x in adh if not x.get("quranRefs")]
    q_ok = 0
    q_fail = []
    for x in q_adh:
        refs = x["quranRefs"]
        verses = [canon.get((r["surah"], i)) for r in refs for i in range(r["from"], r["to"] + 1)]
        verses_s = [simple.get((r["surah"], i)) for r in refs for i in range(r["from"], r["to"] + 1)]
        txt = (x.get("arabicPhrase") or "").strip()
        pool = [" ".join(verses), " ".join(verses_s)] if all(verses) else []
        segs = [t for t in txt.split(VERSE_SEP.strip()) if t.strip()]
        # each ' ۝ '-separated segment must be a word-aligned run of the
        # referenced verses (Uthmani or Simple Tanzil text, verbatim)
        if pool and segs and all(any(segment_in_verse(seg, p) for p in pool) for seg in segs):
            q_ok += 1
        else:
            q_fail.append(x.get("id"))
    coll = re.compile(r"(Bukhari|Muslim|Abu Dawud|Ab[uū] D[aā]w[uū]d|Tirmidhi|Nasa|Ibn Majah|Ahmad|Muwatta|Hakim|Hisn)", re.I)
    num = re.compile(r"\d")
    nq_ref = sum(1 for x in nq_adh if (x.get("sourceRef") or "").strip())
    nq_coll_num = sum(1 for x in nq_adh if coll.search(x.get("sourceRef") or "") and num.search(x.get("sourceRef") or ""))
    # therapy panel (not exported: count by source text)
    panel_src = (ROOT / "frontend/src/components/therapy/PropheticDuasPanel.tsx").read_text(encoding="utf-8")
    p_total = len(re.findall(r"^\s+name_en:", panel_src, re.M))
    p_quranic = len(re.findall(r"is_quranic:\s*true", panel_src))
    p_hadith = len(re.findall(r"^\s+hadith:\s*\{", panel_src, re.M))
    return {
        "quranic_duas": {
            "total": len(duas), "citation_valid": cited, "citation_pct": pct(cited, len(duas)),
            "text_exact_match_canonical": exact, "exact_match_pct": pct(exact, len(duas)),
            "full_verse_entries": full, "excerpt_entries": exact - full,
            "exact_match_failures": fails,
            "backend_duas_json_count": len(be), "backend_vs_frontend_text_mismatch": be_mismatch,
        },
        "adhkar": {
            "total": len(adh), "quranic": len(q_adh), "non_quranic": len(nq_adh),
            "quranic_text_matches_canonical": q_ok,
            "quranic_text_mismatch_ids": q_fail,
            "non_quranic_with_source_ref": nq_ref,
            "non_quranic_with_collection_and_number": nq_coll_num,
            "non_quranic_citation_pct": pct(nq_ref, len(nq_adh)),
            "non_quranic_structured_citation_pct": pct(nq_coll_num, len(nq_adh)),
        },
        "therapy_prophetic_duas_panel": {
            "total": p_total, "quranic": p_quranic, "non_quranic": p_total - p_quranic,
            "non_quranic_with_structured_hadith": p_hadith,
            "note": "non-Quranic entries render only with a structured hadith source (isDisplayableNote)",
        },
        "all_duas_total": len(duas) + len(adh) + p_total,
        "all_quranic": len(duas) + len(q_adh) + p_quranic,
        "all_non_quranic": len(nq_adh) + (p_total - p_quranic),
    }


def i18n_section(ts):
    src = (ROOT / "frontend/src/i18n/translations.ts").read_text(encoding="utf-8")
    out = {}
    for name, d in sorted(ts["i18n"].items()):
        keys = sorted(d)
        miss_ar = [k for k in keys if "ar" not in d[k]]
        miss_en = [k for k in keys if "en" not in d[k]]
        empty_ar = [k for k in keys if not str(d[k].get("ar", "")).strip()]
        empty_en = [k for k in keys if not str(d[k].get("en", "")).strip()]
        ar_no_ar = [k for k in keys if str(d[k].get("ar", "")).strip() and not AR_LETTER.search(str(d[k]["ar"]))]
        en_has_ar = [k for k in keys if AR_LETTER.search(str(d[k].get("en", "")))]
        same = [k for k in keys if d[k].get("ar") == d[k].get("en") and str(d[k].get("ar", "")).strip()]
        out[name] = {
            "keys": len(keys), "missing_ar": len(miss_ar), "missing_en": len(miss_en),
            "empty_ar": empty_ar, "empty_en": empty_en,
            "ar_without_arabic_letters": ar_no_ar, "en_with_arabic_letters": en_has_ar,
            "ar_equals_en": same,
        }
    # duplicate keys in the main object literal (later definition silently wins)
    main = src[src.index("export const translations"):src.index("export const categoryTranslations")]
    defs = re.findall(r"^  ([A-Za-z0-9_]+): \{", main, re.M)
    dups = sorted(k for k, v in Counter(defs).items() if v > 1)
    # t('key') calls whose key is not defined
    used = set()
    for p in (ROOT / "frontend/src").rglob("*.ts*"):
        if "i18n" in p.parts or "__tests__" in p.parts or ".test." in p.name:
            continue
        used |= set(re.findall(r"\bt\(\s*'([A-Za-z0-9_]+)'", p.read_text(encoding="utf-8", errors="ignore")))
    defined = set(ts["i18n"].get("translations", {}))
    missing_used = sorted(used - defined)
    main_d = out.get("translations", {})
    total = main_d.get("keys", 0)
    parity_ok = total - main_d.get("missing_ar", 0) - main_d.get("missing_en", 0) \
        - len(main_d.get("empty_ar", [])) - len(main_d.get("empty_en", []))
    return {
        "dictionaries": out,
        "translations_duplicate_keys": dups,
        "t_calls_distinct_keys": len(used),
        "t_calls_undefined_keys": missing_used,
        "translations_parity_pct": pct(parity_ok, total),
    }


async def provenance_section(c, ts):
    issues = []
    checked = []

    def check(kind, sid, title, author, language, source, licence, licence_ok=True):
        miss = [f for f, v in (("title", title), ("author", author), ("language", language),
                                ("source", source), ("licence", licence)) if not (v and str(v).strip())]
        if not licence_ok:
            miss.append("licence_not_verified")
        checked.append({"kind": kind, "id": sid, "missing": miss})
        if miss:
            issues.append({"kind": kind, "id": sid, "missing": miss})

    manifest = load_json("data/manifests/tafseer_sources.json")
    m_src = {s["id"]: s for s in manifest["sources"]}
    for s in await c.fetch("select * from tafseer_sources where is_enabled = 1 order by id"):
        m = m_src.get(s["id"]) or {}
        lic = m.get("license") or {}
        prov = m.get("provenance") or {}
        source = s["source_url"] or prov.get("dataset_url") or (m.get("api_source") or {}).get("base_url")
        lic_ok = bool(s["license_verified"]) and lic.get("type") not in (None, "pending_verification") \
            and "NEED" not in str(lic.get("license_url") or "") and m.get("status") != "pending_user_input"
        check("tafsir_db_enabled", s["id"], s["name_en"], s["author_en"], s["language"], source,
              s["license"], lic_ok)
    for sid in manifest.get("enabled_ids", []):
        m = m_src.get(sid) or {}
        lic = m.get("license") or {}
        check("tafsir_manifest_enabled", sid, m.get("name_en"), m.get("author_en"), m.get("language"),
              (m.get("provenance") or {}).get("dataset_url") or (m.get("api_source") or {}).get("base_url")
              or lic.get("tos_url"),
              lic.get("type"), lic.get("type") not in (None, "pending_verification"))
    tm = load_json("data/manifests/translation_sources.json")
    for e in await c.fetch("select * from translation_editions order by key"):
        check("translation_edition", e["key"], e["title"], e["translator_name"], e["language"],
              e["source_url"], e["license"], tm.get("license_status") == "verified")
    qh = load_json("data/manifests/quran_hafs.json")
    check("quran_text", "quran_hafs", qh.get("name"), qh.get("citation_en"), qh.get("language"),
          qh.get("license_url"), qh.get("license"), qh.get("license_status") == "verified")
    reg = {r["sourceId"]: r for r in ts["registry"]}
    for e in ts["panelEditions"]:
        dbid = e.get("db_source_id")
        r = reg.get(dbid) if dbid else None
        m = m_src.get(dbid or f"{e['id']}_ar") or {}
        lic_type = (m.get("license") or {}).get("type")
        check("reader_panel_external_tafsir", e["id"], e["name_en"], e["author_en"], e["language"],
              e["source"], r["licenseOrTerms"] if r else None,
              bool(r) and lic_type not in (None, "pending_verification"))
    rel_types = {"quran_text", "tafsir", "translation", "audio", "lexicon"}
    lic_status = Counter()
    for r in ts["registry"]:
        if r["type"] not in rel_types:
            continue
        lic_status[r.get("licenseStatus") or "unset"] += 1
        miss = [f for f in ("titleEnglish", "author", "language", "sourceUrl", "licenseOrTerms") if not str(r.get(f) or "").strip()]
        if miss:
            issues.append({"kind": "registry_entry", "id": r["sourceId"], "missing": miss})
    return {
        "checked": len(checked), "with_issues": len(issues),
        "complete_pct": pct(len(checked) - sum(1 for i in issues if i["kind"] != "registry_entry"), len(checked)),
        "issues": issues,
        "registry_religious_entries_licence_status": dict(sorted(lic_status.items())),
    }


# ---------------------------------------------------------------------------

async def main_async(args):
    import asyncpg

    tanzil = load_json("data/raw/quran_tanzil.json")
    ts = ts_dump()
    c = await asyncpg.connect(db_url())
    try:
        quran, id2ref, valid = await quran_section(c, tanzil)
        report = {
            "repo_head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                        capture_output=True, text=True).stdout.strip(),
            "quran": quran,
            "translations": await translations_section(c, id2ref),
            "tafsir": await tafsir_section(c, valid, ts),
            "audio": audio_section(args.probe_audio),
            "stories": await stories_section(c, valid),
            "themes": await themes_section(c, valid),
            "concepts": await concepts_section(c, valid),
            "duas": duas_section(ts, tanzil),
            "i18n": i18n_section(ts),
            "provenance": await provenance_section(c, ts),
        }
    finally:
        await c.close()
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", help="write JSON here as well as stdout")
    ap.add_argument("--probe-audio", action="store_true", help="HEAD-request sample verse audio per reciter")
    args = ap.parse_args()
    report = asyncio.run(main_async(args))
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
