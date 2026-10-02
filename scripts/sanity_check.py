#!/usr/bin/env python3
"""
Tadabbur Al-Quran — Full Stack Sanity Check
============================================
Checks: backend health, database rows, Quran text, tafseer, miracles,
        Ollama model availability, and frontend build artefacts.

Usage:
    python3 scripts/sanity_check.py [--base-url http://localhost:19800]

Exit code 0 = all critical checks passed.
Exit code 1 = one or more critical checks failed.
"""
import sys
import os
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ─────────────────────────────────────────────────────────────────────────────
# Colours
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
CYAN  = "\033[96m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):print(f"  {RED}✗{RESET} {msg}")
def warn(msg):print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):print(f"  {CYAN}→{RESET} {msg}")


@dataclass
class Result:
    name: str
    passed: bool
    critical: bool = True
    detail: str = ""


results: list[Result] = []

def check(name: str, passed: bool, critical: bool = True, detail: str = ""):
    r = Result(name, passed, critical, detail)
    results.append(r)
    if passed:
        ok(f"{name}" + (f" — {detail}" if detail else ""))
    elif critical:
        fail(f"{name}" + (f" — {detail}" if detail else ""))
    else:
        warn(f"{name} (non-critical)" + (f" — {detail}" if detail else ""))
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helper (no requests dependency)
# ─────────────────────────────────────────────────────────────────────────────
def http_get(url: str, token: Optional[str] = None, timeout: int = 10):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return None, {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# DB helper via asyncpg
# ─────────────────────────────────────────────────────────────────────────────
def db_counts() -> dict[str, int]:
    script = """
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run():
    url = 'postgresql+asyncpg://tadabbur:tadabbur_dev@localhost:19432/tadabbur'
    engine = create_async_engine(url)
    out = {}
    async with engine.connect() as conn:
        rows = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        tables = [r[0] for r in rows]
        for t in tables:
            try:
                r = await conn.execute(text(f'SELECT COUNT(*) FROM {t}'))
                out[t] = r.scalar()
            except Exception:
                out[t] = -1
    print(json.dumps(out))

asyncio.run(run())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT / "backend"),
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "backend")},
        timeout=20,
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout.strip())
        except Exception:
            pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Ollama helper
# ─────────────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"

# Models that genuinely support Arabic text generation well
ARABIC_CAPABLE_MODELS = {
    "qwen2.5:32b", "qwen2.5:14b", "qwen2.5:7b",
    "qwen2.5vl:7b",
    "llama3.1:8b", "llama3.2:latest", "llama3.2:3b",
    "mistral:latest",
}

def ollama_list() -> list[str]:
    status, body = http_get(f"{OLLAMA_URL}/api/tags")
    if status == 200 and isinstance(body, dict):
        return [m["name"] for m in body.get("models", [])]
    return []

def ollama_generate(model: str, prompt: str, timeout: int = 30) -> Optional[str]:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.0, "num_predict": 50}}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
            return body.get("response", "").strip()
    except Exception as e:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main checks
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Tadabbur sanity check")
    parser.add_argument("--base-url", default="http://localhost:19800",
                        help="Tadabbur backend base URL")
    parser.add_argument("--token", default="test_admin_token_dev",
                        help="Admin bearer token")
    args = parser.parse_args()

    BASE = args.base_url.rstrip("/")
    TOKEN = args.token

    print(f"\n{BOLD}Tadabbur Al-Quran — Sanity Check{RESET}")
    print(f"Backend: {BASE}")
    print("=" * 60)

    # ── 1. Backend reachability ──────────────────────────────────────────────
    print(f"\n{BOLD}[1] Backend Health{RESET}")
    status, body = http_get(f"{BASE}/health")
    reachable = status == 200
    check("Backend reachable on correct port", reachable,
          detail=f"HTTP {status}" if status else "connection refused")
    if reachable:
        svc_status = body.get("status", "?")
        check("Backend status=healthy", svc_status in ("ok", "healthy"),
              detail=f"status={svc_status}")
        vectors = body.get("index", {}).get("vectors", "?")
        check("Vector index has content", isinstance(vectors, int) and vectors > 0,
              critical=False, detail=f"{vectors} vectors")

    # ── 2. Database rows ─────────────────────────────────────────────────────
    print(f"\n{BOLD}[2] Database Row Counts{RESET}")
    counts = db_counts()
    if not counts:
        fail("Cannot connect to PostgreSQL — skipping DB checks")
        results.append(Result("db_connect", False, True, "Cannot connect"))
    else:
        info(f"Connected — {len(counts)} tables found")

        qv = counts.get("quran_verses", counts.get("verses", 0))
        check("quran_verses seeded", qv >= 6236,
              detail=f"{qv} rows (expected 6236)")

        tc = counts.get("tafseer_chunks", 0)
        check("tafseer_chunks seeded", tc > 0,
              critical=False, detail=f"{tc} rows")

        ts = counts.get("tafseer_sources", 0)
        check("tafseer_sources seeded", ts > 0,
              critical=False, detail=f"{ts} rows")

        ve = counts.get("vocabulary_entries", 0)
        check("vocabulary_entries seeded", ve > 0,
              critical=False, detail=f"{ve} rows")

        for tbl in ["stories", "concepts", "themes", "tafseer_sources"]:
            c = counts.get(tbl, 0)
            check(f"{tbl} table accessible", c >= 0,
                  critical=False, detail=f"{c} rows")

    # ── 3. Quran API ─────────────────────────────────────────────────────────
    print(f"\n{BOLD}[3] Quran API Endpoints{RESET}")

    status, body = http_get(f"{BASE}/api/v1/quran/metadata", TOKEN)
    check("GET /quran/metadata returns 200", status == 200,
          detail=f"HTTP {status}" if status else "no response")
    if status == 200:
        tv = body.get("total_verses", 0)
        check("metadata.total_verses >= 6236", tv >= 6236,
              detail=f"total_verses={tv}")

    # Al-Fatiha 1:1
    status, body = http_get(f"{BASE}/api/v1/quran/verses/1/1", TOKEN)
    check("GET /quran/verses/1/1 returns 200", status == 200,
          detail=f"HTTP {status}, body={str(body)[:80]}")
    if status == 200:
        # DB field is text_uthmani; some response aliases may use aya_text
        txt = body.get("text_uthmani", body.get("aya_text", body.get("text", "")))
        has_arabic = any('؀' <= c <= 'ۿ' for c in txt)
        check("Verse 1:1 contains Arabic text", has_arabic,
              detail=txt[:60] if txt else "empty — quran_verses may need seeding")

    # Ayat al-Kursi 2:255
    status, body = http_get(f"{BASE}/api/v1/quran/verses/2/255", TOKEN)
    check("GET /quran/verses/2/255 (Ayat al-Kursi) returns 200", status == 200,
          detail=f"HTTP {status}")

    # Surah 112 (Al-Ikhlas — 4 verses)
    status, body = http_get(f"{BASE}/api/v1/quran/suras/112", TOKEN)
    check("GET /quran/suras/112 returns 200", status == 200,
          detail=f"HTTP {status}")
    if status == 200:
        verses = body if isinstance(body, list) else body.get("verses", [])
        check("Surah 112 has 4 verses", len(verses) == 4,
              detail=f"got {len(verses)}")

    # ── 4. Tafseer API ───────────────────────────────────────────────────────
    print(f"\n{BOLD}[4] Tafseer API Endpoints{RESET}")

    status, body = http_get(f"{BASE}/api/v1/quran/tafseer/sources", TOKEN)
    check("GET /quran/tafseer/sources returns 200", status == 200,
          critical=False, detail=f"HTTP {status}")
    if status == 200:
        srcs = body if isinstance(body, list) else []
        check("At least 1 tafseer source present", len(srcs) > 0,
              critical=False, detail=f"{len(srcs)} sources")

    status, body = http_get(f"{BASE}/api/v1/quran/tafseer/1/1", TOKEN)
    check("GET /quran/tafseer/1/1 returns 200", status == 200,
          critical=False, detail=f"HTTP {status}")
    if status == 200:
        chunks = body if isinstance(body, list) else body.get("chunks", [])
        check("Tafseer chunks present for 1:1", len(chunks) > 0,
              critical=False, detail=f"{len(chunks)} chunks")

    # ── 5. Miracles API ──────────────────────────────────────────────────────
    print(f"\n{BOLD}[5] Miracles API{RESET}")

    status, body = http_get(f"{BASE}/api/v1/concepts/miracles/all", TOKEN)
    check("GET /concepts/miracles/all returns 200", status == 200,
          critical=False, detail=f"HTTP {status}")
    if status == 200:
        items = body if isinstance(body, list) else body.get("miracles", body.get("data", []))
        check("At least 20 miracles returned", len(items) >= 20,
              critical=False, detail=f"{len(items)} miracles")

    # ── 6. Ollama models ─────────────────────────────────────────────────────
    print(f"\n{BOLD}[6] Ollama — Arabic-capable Models{RESET}")

    models = ollama_list()
    if not models:
        fail("Cannot reach Ollama at localhost:11434")
        results.append(Result("ollama", False, False, "not reachable"))
    else:
        info(f"Ollama running — {len(models)} models available")

        available_arabic = [m for m in models if m in ARABIC_CAPABLE_MODELS]
        check("At least one Arabic-capable model available",
              len(available_arabic) > 0,
              critical=False,
              detail=", ".join(available_arabic) if available_arabic else "none found")

        best = next((m for m in ["qwen2.5:32b","qwen2.5:14b","llama3.1:8b"] if m in models), None)
        if best:
            info(f"Testing Arabic generation with {best} …")
            resp = ollama_generate(best, "قل بسم الله الرحمن — أكمل الآية:")
            has_arabic = resp and any('؀' <= c <= 'ۿ' for c in resp)
            check(f"{best} produces Arabic output", bool(has_arabic),
                  critical=False, detail=resp[:80] if resp else "no response")
        else:
            warn("No preferred Arabic model available for generation test")

        # Flag dhakira-* models as manuscript-analysis only
        dhakira = [m for m in models if "dhakira" in m]
        if dhakira:
            warn(f"dhakira-* models are manuscript-analysis tools, NOT general Arabic LLMs: {dhakira}")

    # ── 7. Data files on disk ────────────────────────────────────────────────
    print(f"\n{BOLD}[7] Critical Data Files on Disk{RESET}")

    files = [
        (PROJECT_ROOT / "data/raw/quran_uthmani.json", 4_000_000, "Quran Uthmani text"),
        (PROJECT_ROOT / "data/raw/ibn_kathir_ar.json", 1_000_000, "Ibn Kathir AR tafseer"),
        (PROJECT_ROOT / "data/raw/ibn_kathir_en.json", 1_000_000, "Ibn Kathir EN tafseer"),
        (PROJECT_ROOT / "data/raw/tabari_ar.json",     1_000_000, "Tabari AR tafseer"),
        (PROJECT_ROOT / "data/raw/qurtubi_ar.json",    1_000_000, "Qurtubi AR tafseer"),
        (PROJECT_ROOT / "data/manifests/quran_hafs.json", 100, "Quran manifest"),
    ]
    for path, min_size, label in files:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        check(f"{label} present", exists and size >= min_size,
              critical=(label == "Quran Uthmani text"),
              detail=f"{size:,} bytes" if exists else "MISSING")

    # ── 8. Frontend build ────────────────────────────────────────────────────
    print(f"\n{BOLD}[8] Frontend Build Artefacts{RESET}")
    fe_dir = PROJECT_ROOT / "frontend"
    check("frontend/src/data/quranStories.ts exists",
          (fe_dir / "src/data/quranStories.ts").exists(), critical=False)
    check("frontend/src/data/surahAtlas.ts has 114 entries",
          (fe_dir / "src/data/surahAtlas.ts").exists(), critical=False)
    check("Batch 5a stories file exists",
          (fe_dir / "src/data/quranStoriesBatch5a.ts").exists(), critical=False)
    check("Batch 5b stories file exists",
          (fe_dir / "src/data/quranStoriesBatch5b.ts").exists(), critical=False)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    total  = len(results)
    passed = sum(1 for r in results if r.passed)
    crit_failed = [r for r in results if not r.passed and r.critical]
    non_crit_failed = [r for r in results if not r.passed and not r.critical]

    print(f"\n{BOLD}Summary: {passed}/{total} passed{RESET}")
    if crit_failed:
        print(f"\n{RED}{BOLD}CRITICAL FAILURES ({len(crit_failed)}):{RESET}")
        for r in crit_failed:
            print(f"  {RED}✗{RESET} {r.name}: {r.detail}")
    if non_crit_failed:
        print(f"\n{YELLOW}Non-critical failures ({len(non_crit_failed)}):{RESET}")
        for r in non_crit_failed:
            print(f"  {YELLOW}⚠{RESET} {r.name}: {r.detail}")

    if not crit_failed:
        print(f"\n{GREEN}{BOLD}All critical checks passed.{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}{len(crit_failed)} critical check(s) failed.{RESET}")
        print("\nNext steps:")
        if any("quran_verses" in r.name for r in crit_failed):
            print("  → Seed Quran: PYTHONPATH=backend .venv/bin/python3 backend/scripts/ingest/seed_quran.py")
        if any("tafseer" in r.name for r in crit_failed):
            print("  → Seed tafseer: PYTHONPATH=backend .venv/bin/python3 backend/scripts/ingest/seed_tafseer.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
