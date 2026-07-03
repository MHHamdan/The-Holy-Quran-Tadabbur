#!/usr/bin/env python3
"""
Benchmark 1: Concept Retrieval (M2 — Benchmark Infrastructure).

Measures how well the platform retrieves relevant verses for natural
language concept queries, per artifacts/benchmarks.md.

Gold standard: the 60 human-curated concepts in the `concepts` table with
their `occurrences` verse ranges (data/concepts + seed_concepts.py — the
"curated_concepts.json verse membership" source named in the spec).

System under test: GET /api/v1/quran/search/semantic — the live serving
path (Qdrant quran_verses collection + multilingual-e5-large), so latency
numbers reflect what users experience.

Queries: for each eligible concept (>= MIN_GOLD_RANGES occurrence ranges),
one query per English label/alias and per Arabic label/alias — this doubles
as a cross-language retrieval test.

Metrics (targets from benchmarks.md):
  Recall@5 >= 0.75 · Recall@10 >= 0.85 · MRR >= 0.70 · nDCG@10 >= 0.72
  Latency P95 <= 500 ms

Usage:
    PYTHONPATH=backend .venv/bin/python backend/scripts/bench/bench_concept_retrieval.py \
        [--base-url http://localhost:8002] [--limit-concepts N] [--min-gold 3]

Output:
    reports/benchmarks/concept_retrieval_<date>.json   (machine-readable)
    reports/benchmarks/concept_retrieval_<date>.md     (human-readable)

Deterministic: no LLM calls, no random sampling.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from datetime import date
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "reports" / "benchmarks"

DB_URL = "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"

TARGETS = {
    "recall@5": 0.75,
    "recall@10": 0.85,
    "mrr": 0.70,
    "ndcg@10": 0.72,
    "latency_p95_ms": 500.0,
}


def load_gold_direct() -> list[dict]:
    """Tier A gold: direct theme -> verse ranges from `theme_segments`.

    This matches the benchmark spec exactly (e.g. sabr -> 2:155-157) but
    coverage is currently small (grows as theme curation proceeds); treat
    it as the primary quality signal.
    """
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        themes = conn.execute(text(
            "SELECT id, title_en, title_ar, short_title_en, short_title_ar, key_concepts "
            "FROM quranic_themes"
        )).mappings().all()
        segs = conn.execute(text(
            "SELECT theme_id, sura_no, ayah_start, ayah_end FROM theme_segments "
            "WHERE sura_no IS NOT NULL"
        )).mappings().all()

    ranges_by_theme: dict[str, list[tuple[int, int, int]]] = {}
    for s in segs:
        ranges_by_theme.setdefault(s["theme_id"], []).append(
            (s["sura_no"], s["ayah_start"], s["ayah_end"] or s["ayah_start"])
        )

    gold = []
    for t in themes:
        ranges = ranges_by_theme.get(t["id"], [])
        if not ranges:
            continue
        queries: list[tuple[str, str]] = []
        seen: set[str] = set()
        for q in [t["short_title_en"], t["title_en"]]:
            if q and q.lower() not in seen:
                seen.add(q.lower())
                queries.append((q, "en"))
        for q in [t["short_title_ar"], t["title_ar"], *(t["key_concepts"] or [])[:2]]:
            if q and q not in seen:
                seen.add(q)
                queries.append((q, "ar"))
        gold.append({
            "concept_id": t["id"],
            "label_en": t["title_en"],
            "gold_ranges": ranges,
            "queries": queries,
        })
    return gold


def load_gold(min_gold: int) -> list[dict]:
    """Tier B gold: concept -> story -> verse ranges (transitive proxy).

    The curated `occurrences` table links concepts to STORIES
    (ref_type='story'); verse ranges are resolved transitively through
    `story_segments`, which carry human-curated sura/aya ranges.
    """
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        concepts = conn.execute(text(
            "SELECT id, label_en, label_ar, aliases_en, aliases_ar FROM concepts"
        )).mappings().all()
        occ = conn.execute(text(
            "SELECT concept_id, ref_type, ref_id, sura_no, ayah_start, ayah_end "
            "FROM occurrences WHERE is_verified IS NOT FALSE"
        )).mappings().all()
        seg_rows = conn.execute(text(
            "SELECT story_id, sura_no, aya_start, aya_end FROM story_segments "
            "WHERE sura_no IS NOT NULL"
        )).mappings().all()

    ranges_by_story: dict[str, list[tuple[int, int, int]]] = {}
    for s in seg_rows:
        ranges_by_story.setdefault(s["story_id"], []).append(
            (s["sura_no"], s["aya_start"], s["aya_end"] or s["aya_start"])
        )

    ranges_by_concept: dict[str, list[tuple[int, int, int]]] = {}
    for o in occ:
        ranges: list[tuple[int, int, int]] = []
        if o["sura_no"] is not None:
            ranges = [(o["sura_no"], o["ayah_start"], o["ayah_end"] or o["ayah_start"])]
        elif o["ref_type"] == "story" and o["ref_id"] in ranges_by_story:
            ranges = ranges_by_story[o["ref_id"]]
        if ranges:
            bucket = ranges_by_concept.setdefault(o["concept_id"], [])
            for r in ranges:
                if r not in bucket:
                    bucket.append(r)

    gold = []
    for c in concepts:
        ranges = ranges_by_concept.get(c["id"], [])
        if len(ranges) < min_gold:
            continue
        queries: list[tuple[str, str]] = []  # (query, language)
        seen: set[str] = set()
        for q in [c["label_en"], *(c["aliases_en"] or [])]:
            if q and q.lower() not in seen:
                seen.add(q.lower())
                queries.append((q, "en"))
        for q in [c["label_ar"], *(c["aliases_ar"] or [])]:
            if q and q not in seen:
                seen.add(q)
                queries.append((q, "ar"))
        gold.append({
            "concept_id": c["id"],
            "label_en": c["label_en"],
            "gold_ranges": ranges,
            "queries": queries,
        })
    return gold


def is_hit(sura: int, aya: int, gold_ranges: list[tuple[int, int, int]]) -> bool:
    return any(s == sura and start <= aya <= end for s, start, end in gold_ranges)


def evaluate_query(
    client: httpx.Client, base_url: str, query: str, gold_ranges: list[tuple[int, int, int]]
) -> dict:
    t0 = time.monotonic()
    r = client.get(
        f"{base_url}/api/v1/quran/search/semantic",
        params={"query": query, "limit": 10, "min_score": 0.0},
        timeout=60.0,
    )
    latency_ms = (time.monotonic() - t0) * 1000
    r.raise_for_status()
    results = r.json().get("results", [])

    hits = [
        is_hit(res.get("sura_no"), res.get("aya_no"), gold_ranges)
        for res in results
    ]
    n_gold = len(gold_ranges)

    def recall_at(k: int) -> float:
        # Count distinct gold ranges hit within top-k (one hit per range).
        # Denominator capped at k: transitive gold sets (concept -> stories
        # -> segments) are far larger than k, so uncapped recall@k would be
        # bounded near zero regardless of retrieval quality.
        matched: set[int] = set()
        for res in results[:k]:
            for i, (s, a, b) in enumerate(gold_ranges):
                if res.get("sura_no") == s and a <= res.get("aya_no", -1) <= b:
                    matched.add(i)
        denom = min(n_gold, k)
        return len(matched) / denom if denom else 0.0

    rr = 0.0
    for rank, h in enumerate(hits, start=1):
        if h:
            rr = 1.0 / rank
            break

    dcg = sum(h / math.log2(rank + 1) for rank, h in enumerate(hits[:10], start=1))
    ideal_hits = min(n_gold, 10)
    idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0

    return {
        "query": query,
        "recall@5": recall_at(5),
        "recall@10": recall_at(10),
        "mrr": rr,
        "ndcg@10": ndcg,
        "latency_ms": round(latency_ms, 1),
        "top_refs": [f"{r.get('sura_no')}:{r.get('aya_no')}" for r in results[:5]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8002")
    parser.add_argument("--min-gold", type=int, default=3,
                        help="Min gold occurrence ranges for a concept to be included")
    parser.add_argument("--limit-concepts", type=int, default=None)
    args = parser.parse_args()

    tiers = {
        "direct": load_gold_direct(),
        "transitive": load_gold(args.min_gold),
    }
    if args.limit_concepts:
        tiers = {k: v[: args.limit_concepts] for k, v in tiers.items()}
    if not any(tiers.values()):
        print("No eligible concepts — is the DB seeded? (make seed-concepts / seed-themes)")
        return 1

    per_query: list[dict] = []
    with httpx.Client() as client:
        # Warm the embedding model so cold-start doesn't pollute latency.
        client.get(
            f"{args.base_url}/api/v1/quran/search/semantic",
            params={"query": "warmup", "limit": 1},
            timeout=120.0,
        )
        for tier, gold in tiers.items():
            n_queries = sum(len(c["queries"]) for c in gold)
            print(f"\n── Tier {tier}: {len(gold)} concepts, {n_queries} queries ──")
            for c in gold:
                for query, lang in c["queries"]:
                    res = evaluate_query(client, args.base_url, query, c["gold_ranges"])
                    res["concept_id"] = c["concept_id"]
                    res["language"] = lang
                    res["tier"] = tier
                    per_query.append(res)
                    print(f"  [{lang}] {query!r:40s} R@5={res['recall@5']:.2f} "
                          f"MRR={res['mrr']:.2f} {res['latency_ms']:.0f}ms")

    def agg(metric: str, subset: list[dict]) -> float:
        return statistics.mean(q[metric] for q in subset) if subset else 0.0

    def tier_summary(subset: list[dict]) -> dict:
        lat = sorted(q["latency_ms"] for q in subset)
        p95 = lat[int(len(lat) * 0.95) - 1] if lat else 0.0
        en = [q for q in subset if q["language"] == "en"]
        ar = [q for q in subset if q["language"] == "ar"]
        return {
            "queries": len(subset),
            "metrics": {
                "recall@5": round(agg("recall@5", subset), 4),
                "recall@10": round(agg("recall@10", subset), 4),
                "mrr": round(agg("mrr", subset), 4),
                "ndcg@10": round(agg("ndcg@10", subset), 4),
                "latency_p50_ms": round(statistics.median(lat), 1) if lat else 0.0,
                "latency_p95_ms": round(p95, 1),
            },
            "by_language": {
                "en": {m: round(agg(m, en), 4) for m in ("recall@5", "recall@10", "mrr", "ndcg@10")},
                "ar": {m: round(agg(m, ar), 4) for m in ("recall@5", "recall@10", "mrr", "ndcg@10")},
            },
        }

    summary = {
        "benchmark": "concept_retrieval",
        "date": date.today().isoformat(),
        "system": "GET /quran/search/semantic (Qdrant quran_verses + multilingual-e5-large)",
        "tiers": {
            tier: {"concepts": len(gold), **tier_summary([q for q in per_query if q["tier"] == tier])}
            for tier, gold in tiers.items()
        },
        "targets": TARGETS,
        "per_query": per_query,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    json_path = REPORT_DIR / f"concept_retrieval_{stamp}.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    def flag(name: str, value: float, higher_is_better: bool = True) -> str:
        target = TARGETS[name]
        ok = value >= target if higher_is_better else value <= target
        return "PASS" if ok else "FAIL"

    md = [
        f"# Benchmark 1: Concept Retrieval — {stamp}",
        "",
        f"System: `{summary['system']}`",
        "",
        "Tier **direct** = theme→verse gold from `theme_segments` (spec-faithful, "
        "small coverage). Tier **transitive** = concept→story→verse gold "
        "(coarse proxy, wide coverage). Recall@k denominators are capped at k.",
        "",
    ]
    for tier, ts in summary["tiers"].items():
        m = ts["metrics"]
        md += [
            f"## Tier: {tier} — {ts['concepts']} concepts, {ts['queries']} queries",
            "",
            "| Metric | Value | Target | Status |",
            "|---|---|---|---|",
            f"| Recall@5 | {m['recall@5']:.3f} | ≥ {TARGETS['recall@5']} | {flag('recall@5', m['recall@5'])} |",
            f"| Recall@10 | {m['recall@10']:.3f} | ≥ {TARGETS['recall@10']} | {flag('recall@10', m['recall@10'])} |",
            f"| MRR | {m['mrr']:.3f} | ≥ {TARGETS['mrr']} | {flag('mrr', m['mrr'])} |",
            f"| nDCG@10 | {m['ndcg@10']:.3f} | ≥ {TARGETS['ndcg@10']} | {flag('ndcg@10', m['ndcg@10'])} |",
            f"| Latency P50 | {m['latency_p50_ms']:.0f} ms | — | — |",
            f"| Latency P95 | {m['latency_p95_ms']:.0f} ms | ≤ {TARGETS['latency_p95_ms']:.0f} ms | {flag('latency_p95_ms', m['latency_p95_ms'], False)} |",
            "",
            "| Metric | EN | AR |",
            "|---|---|---|",
            *[
                f"| {name} | {ts['by_language']['en'][name]:.3f} | {ts['by_language']['ar'][name]:.3f} |"
                for name in ("recall@5", "recall@10", "mrr", "ndcg@10")
            ],
            "",
        ]
    md.append(f"Full per-query results: `{json_path.name}`\n")
    md_path = REPORT_DIR / f"concept_retrieval_{stamp}.md"
    md_path.write_text("\n".join(md))

    print("\n" + "=" * 60)
    for tier, ts in summary["tiers"].items():
        m = ts["metrics"]
        print(f"[{tier:10s}] R@5={m['recall@5']:.3f}  R@10={m['recall@10']:.3f}  "
              f"MRR={m['mrr']:.3f}  nDCG@10={m['ndcg@10']:.3f}  "
              f"P95={m['latency_p95_ms']:.0f}ms")
    print(f"Reports: {json_path}\n         {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
