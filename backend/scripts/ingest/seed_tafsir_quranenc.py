#!/usr/bin/env python3
"""
Seed tafsir from QuranEnc.com: al-Mukhtasar (English, Arabic) and al-Muyassar.

After the English translations of Ibn Kathir and al-Jalalayn were disabled
(no licence), English readers have no tafsir. QuranEnc publishes these works
through the same API as its translations, whose republication terms are:
verbatim text, credit the publisher and QuranEnc.com, state the version, keep
the notes, track the latest version, no inappropriate ads. Whether those terms
cover these tafsir keys is NOT yet confirmed (english_mokhtasar is missing
from /translations/list), so:

- every source is written with license_verified=0 and is_enabled=0 unless
  data/manifests/tafseer_sources.json records a verified licence for it and
  lists it in enabled_ids (the owner does that after QuranEnc confirms);
- mukhtasar_en is additionally behind FEATURE_MUKHTASAR_EN in the compare
  service, so enabling the row alone does not publish it.

Text is stored verbatim (the English begins with the ayah number, e.g.
'255. ...', and is kept so). The API's arabic_text is not stored: the Qur'an
text always comes from Tanzil. Footnotes, when present, follow the text after
a blank line. Raw responses are cached in data/raw/tafsir/quranenc/<key>.json
with the fetch time and a SHA-256 of the content, which serves as the version
because QuranEnc does not list these keys with a version number.

Usage:
    python backend/scripts/ingest/seed_tafsir_quranenc.py --dry-run          # download + verify only
    python backend/scripts/ingest/seed_tafsir_quranenc.py                    # mukhtasar_en, mukhtasar_ar
    python backend/scripts/ingest/seed_tafsir_quranenc.py --replace-muyassar # also swap muyassar_ar to QuranEnc, one transaction
    python backend/scripts/ingest/seed_tafsir_quranenc.py --refresh          # ignore the cache
    python backend/scripts/ingest/seed_tafsir_quranenc.py --spot-check 5     # compare N random cached ayat with the live API
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = REPO_ROOT / "data" / "raw" / "tafsir" / "quranenc"
API_BASE = "https://quranenc.com/api/v1"
TOTAL_VERSES = 6236
TOTAL_SURAS = 114
TERMS = (
    "QuranEnc.com republication terms: verbatim text (no modification, addition "
    "or deletion); credit the publisher and QuranEnc.com; state the version; keep "
    "the notes; track the latest version; no inappropriate advertising. Coverage "
    "of this tafsir key pending confirmation from QuranEnc."
)

# QuranEnc key -> tafseer_sources row
SOURCES: dict[str, dict] = {
    "english_mokhtasar": {
        "id": "mukhtasar_en",
        "name_ar": "المختصر في التفسير (إنجليزي)",
        "name_en": "Al-Mukhtasar fi al-Tafsir (English)",
        "author_ar": "مركز تفسير للدراسات القرآنية",
        "author_en": "Tafsir Center for Quranic Studies",
        "translator": "Tafsir Center for Quranic Studies (English edition, via QuranEnc.com)",
        "language": "en",
        "era": "contemporary",
        "methodology": "concise",
    },
    "arabic_mokhtasar": {
        "id": "mukhtasar_ar",
        "name_ar": "المختصر في التفسير",
        "name_en": "Al-Mukhtasar fi al-Tafsir",
        "author_ar": "مركز تفسير للدراسات القرآنية",
        "author_en": "Tafsir Center for Quranic Studies",
        "translator": None,
        "language": "ar",
        "era": "contemporary",
        "methodology": "concise",
    },
    "arabic_moyassar": {
        "id": "muyassar_ar",
        "name_ar": "التفسير الميسر",
        "name_en": "Al-Tafsir Al-Muyassar",
        "author_ar": "مجمع الملك فهد لطباعة المصحف الشريف",
        "author_en": "King Fahd Complex for Printing the Holy Quran",
        "translator": None,
        "language": "ar",
        "era": "modern",
        "methodology": "simplified",
    },
}
DEFAULT_KEYS = ["english_mokhtasar", "arabic_mokhtasar"]


def fetch_sura(session: requests.Session, key: str, sura: int) -> list[dict]:
    for attempt in range(4):
        try:
            resp = session.get(f"{API_BASE}/translation/sura/{key}/{sura}", timeout=60)
            resp.raise_for_status()
            return resp.json()["result"]
        except (requests.RequestException, KeyError, ValueError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def download(session: requests.Session, key: str) -> dict:
    with ThreadPoolExecutor(max_workers=4) as pool:
        suras = list(pool.map(lambda s: fetch_sura(session, key, s), range(1, TOTAL_SURAS + 1)))
    verses = [
        {
            "sura": int(v["sura"]),
            "aya": int(v["aya"]),
            "text": v["translation"],
            "footnotes": v.get("footnotes") or None,
        }
        for sura in suras
        for v in sura
    ]
    digest = hashlib.sha256(json.dumps(verses, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "key": key,
        "source": f"{API_BASE}/translation/sura/{key}/{{sura}}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_sha256": digest,
        "verses": verses,
    }


def load_or_download(session: requests.Session, key: str, refresh: bool) -> dict:
    cache = CACHE_DIR / f"{key}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    data = download(session, key)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:  # data/ is read-only in the production image
        print(f"  {key}: not cached ({exc.strerror})")
    return data


def verify(data: dict) -> None:
    """Every verse exactly once, no empty text."""
    seen = [(v["sura"], v["aya"]) for v in data["verses"]]
    if len(seen) != TOTAL_VERSES or len(set(seen)) != TOTAL_VERSES:
        raise ValueError(f"{data['key']}: {len(seen)} rows, {len(set(seen))} distinct (expected {TOTAL_VERSES})")
    empty = [k for k, v in zip(seen, data["verses"]) if not v["text"].strip()]
    if empty:
        raise ValueError(f"{data['key']}: empty text at {empty[:5]}")


def stored_text(v: dict) -> str:
    """Verbatim text, footnotes after a blank line (kept, as the terms require)."""
    return v["text"] if not v["footnotes"] else f"{v['text']}\n\n{v['footnotes']}"


def spot_check(session: requests.Session, data: dict, n: int) -> list[tuple[int, int, bool]]:
    """Compare n random cached ayat with the live per-ayah API, byte for byte."""
    out = []
    for v in random.sample(data["verses"], n):
        resp = session.get(f"{API_BASE}/translation/aya/{data['key']}/{v['sura']}/{v['aya']}", timeout=30)
        resp.raise_for_status()
        live = resp.json()["result"]["translation"]
        out.append((v["sura"], v["aya"], live == v["text"]))
    return out


def write(db, key: str, data: dict, replace: bool) -> None:
    from sqlalchemy import text as sql
    from seed_tafseer import generate_chunk_id, load_licence_state

    meta = SOURCES[key]
    sid = meta["id"]
    state = load_licence_state(sid)
    verified = 1 if state["verified"] else 0
    enabled = 1 if state["verified"] and state["enabled"] else 0
    verse_ids = {(s, a): i for i, s, a in db.execute(sql("SELECT id, sura_no, aya_no FROM quran_verses")).all()}

    if replace:
        db.execute(sql("DELETE FROM tafseer_chunks WHERE source_id = :sid"), {"sid": sid})
    elif db.execute(sql("SELECT 1 FROM tafseer_chunks WHERE source_id = :sid LIMIT 1"), {"sid": sid}).first():
        raise SystemExit(f"{sid} already has chunks; pass --replace-muyassar (muyassar_ar) or delete them first")

    db.execute(sql(
        """
        INSERT INTO tafseer_sources
            (id, name_ar, name_en, author_ar, author_en, translator, era, methodology, language,
             version, source_url, cdn_url, version_tag, retrieval_timestamp, data_hash, ayah_count,
             license_type, license, license_url, license_verified, reliability_score,
             is_primary_source, is_enabled, created_at, updated_at)
        VALUES (:id, :name_ar, :name_en, :author_ar, :author_en, :translator, :era, :methodology, :language,
                :version, 'https://quranenc.com', :cdn_url, :version, :ts, :hash, :count,
                :license_type, :license, 'https://quranenc.com/en/home/api/', :verified, 0.9,
                1, :enabled, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            name_ar = EXCLUDED.name_ar, name_en = EXCLUDED.name_en,
            author_ar = EXCLUDED.author_ar, author_en = EXCLUDED.author_en,
            translator = EXCLUDED.translator, version = EXCLUDED.version,
            source_url = EXCLUDED.source_url, cdn_url = EXCLUDED.cdn_url,
            version_tag = EXCLUDED.version_tag, retrieval_timestamp = EXCLUDED.retrieval_timestamp,
            data_hash = EXCLUDED.data_hash, ayah_count = EXCLUDED.ayah_count,
            license_type = EXCLUDED.license_type, license = EXCLUDED.license,
            license_url = EXCLUDED.license_url, license_verified = EXCLUDED.license_verified,
            is_enabled = EXCLUDED.is_enabled, updated_at = NOW()
        """
    ), {
        **{k: meta[k] for k in ("name_ar", "name_en", "author_ar", "author_en", "translator", "era", "methodology", "language")},
        "id": sid,
        "version": f"quranenc-sha256:{data['content_sha256'][:16]}",
        "cdn_url": data["source"],
        "ts": data["fetched_at"],
        "hash": data["content_sha256"],
        "count": TOTAL_VERSES,
        "license_type": "quranenc_terms" if verified else "pending_verification",
        "license": TERMS[:200],
        "verified": verified,
        "enabled": enabled,
    })

    column = "content_en" if meta["language"] == "en" else "content_ar"
    rows = []
    for v in data["verses"]:
        body = stored_text(v)
        vid = verse_ids[(v["sura"], v["aya"])]
        rows.append({
            "chunk_id": generate_chunk_id(sid, v["sura"], v["aya"]),
            "sid": sid, "vid": vid, "sura": v["sura"], "aya": v["aya"],
            "content": body, "words": len(body.split()), "chars": len(body),
        })
    db.execute(sql(
        f"""
        INSERT INTO tafseer_chunks
            (chunk_id, source_id, verse_start_id, verse_end_id, sura_no, aya_start, aya_end,
             {column}, word_count, char_count, is_embedded)
        VALUES (:chunk_id, :sid, :vid, :vid, :sura, :aya, :aya, :content, :words, :chars, 0)
        """
    ), rows)
    print(f"  {sid}: {len(rows)} chunks, license_verified={verified}, is_enabled={enabled}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help=f"QuranEnc keys (default: {' '.join(DEFAULT_KEYS)})")
    ap.add_argument("--dry-run", action="store_true", help="download and verify only")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache")
    ap.add_argument("--replace-muyassar", action="store_true",
                    help="also load arabic_moyassar, replacing the muyassar_ar chunks in one transaction")
    ap.add_argument("--spot-check", type=int, default=0, metavar="N", help="compare N cached ayat with the live API")
    args = ap.parse_args()

    keys = args.keys or list(DEFAULT_KEYS)
    if args.replace_muyassar and "arabic_moyassar" not in keys:
        keys.append("arabic_moyassar")
    unknown = [k for k in keys if k not in SOURCES]
    if unknown:
        raise SystemExit(f"unknown keys: {unknown}; known: {list(SOURCES)}")

    session = requests.Session()
    session.headers["User-Agent"] = "Tadabbur/1.0 (tafsir seeding)"
    loaded = {}
    for key in keys:
        data = load_or_download(session, key, args.refresh)
        verify(data)
        loaded[key] = data
        print(f"  {key}: {len(data['verses'])} ayat verified, sha256 {data['content_sha256'][:16]}")
        if args.spot_check:
            checks = spot_check(session, data, args.spot_check)
            print(f"  {key}: spot check {checks}")
            if not all(ok for _, _, ok in checks):
                raise SystemExit(f"{key}: cached text differs from the live API")

    if args.dry_run:
        return 0

    from app.db.database import SyncSessionLocal

    with SyncSessionLocal() as db:
        with db.begin():  # one transaction: all keys, including the muyassar swap
            for key, data in loaded.items():
                write(db, key, data, replace=(key == "arabic_moyassar"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
