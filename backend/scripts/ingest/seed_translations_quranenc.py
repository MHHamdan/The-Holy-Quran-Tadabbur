"""
Seed verse translations from QuranEnc.com.

QuranEnc is the only bulk translation source found with an affirmative
republication grant (https://quranenc.com/en/home/api/). Its terms, which this
script and the reader UI honour:

  1. no modification, addition or deletion   -> text and footnotes stored verbatim
  2. name the publisher and QuranEnc.com      -> translation_editions.attribution
  3. state the version number                 -> translation_editions.version
  4. keep the transcript information          -> footnotes column
  6. track the latest version                 -> re-run this script; it upserts

Raw API responses are cached under data/raw/translations/quranenc/<key>.json
(part of the data bundle, not git) so a reseed does not need the network.
The list of editions lives in data/manifests/translation_sources.json.

Usage:
    python backend/scripts/ingest/seed_translations_quranenc.py                 # every edition in the manifest
    python backend/scripts/ingest/seed_translations_quranenc.py english_saheeh  # one edition
    python backend/scripts/ingest/seed_translations_quranenc.py --refresh       # ignore the cache, re-download
    python backend/scripts/ingest/seed_translations_quranenc.py --dry-run       # fetch and verify only
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from app.db.database import SyncSessionLocal

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "data" / "manifests" / "translation_sources.json"
CACHE_DIR = REPO_ROOT / "data" / "raw" / "translations" / "quranenc"

API_BASE = "https://quranenc.com/api/v1"
TOTAL_VERSES = 6236
TOTAL_SURAS = 114


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def fetch_catalogue(session: requests.Session) -> dict[str, dict]:
    resp = session.get(f"{API_BASE}/translations/list", params={"localization": "en"}, timeout=30)
    resp.raise_for_status()
    return {t["key"]: t for t in resp.json()["translations"]}


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


def download_edition(session: requests.Session, key: str, meta: dict) -> dict:
    with ThreadPoolExecutor(max_workers=4) as pool:
        suras = list(pool.map(lambda s: fetch_sura(session, key, s), range(1, TOTAL_SURAS + 1)))
    verses = [
        {
            "sura": int(v["sura"]),
            "aya": int(v["aya"]),
            "translation": v["translation"],
            "footnotes": v.get("footnotes") or None,
        }
        for sura in suras
        for v in sura
    ]
    return {
        "key": key,
        "version": meta["version"],
        "last_update": meta.get("last_update"),
        "title": meta["title"],
        "language_iso_code": meta["language_iso_code"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "verses": verses,
    }


def load_or_download(session: requests.Session, key: str, meta: dict, refresh: bool) -> dict:
    cache = CACHE_DIR / f"{key}.json"
    if cache.exists() and not refresh:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if cached.get("version") == meta["version"]:
            return cached
        print(f"  {key}: cached v{cached.get('version')} is stale, upstream is v{meta['version']}")
    data = download_edition(session, key, meta)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:  # data/ is mounted read-only in the production image
        print(f"  {key}: not cached ({exc.strerror})")
    return data


def verify(data: dict, verse_ids: dict[tuple[int, int], int]) -> None:
    """Every Qur'an verse exactly once, nothing extra, no empty text."""
    seen = {(v["sura"], v["aya"]) for v in data["verses"]}
    if len(data["verses"]) != TOTAL_VERSES or seen != set(verse_ids):
        missing = sorted(set(verse_ids) - seen)[:5]
        extra = sorted(seen - set(verse_ids))[:5]
        raise ValueError(
            f"{data['key']}: {len(data['verses'])} rows, missing {missing}, unexpected {extra}"
        )
    empty = [(v["sura"], v["aya"]) for v in data["verses"] if not v["translation"].strip()]
    if empty:
        raise ValueError(f"{data['key']}: empty translation at {empty[:5]}")


def upsert(db, edition: dict, data: dict, verse_ids: dict[tuple[int, int], int], is_default: bool) -> None:
    key = data["key"]
    db.execute(
        text(
            """
            INSERT INTO translation_editions
                (key, language, title, translator_name, version, source_id, source_url,
                 license, attribution, verse_count, is_default, fetched_at, created_at, updated_at)
            VALUES (:key, :language, :title, :translator_name, :version, 'quranenc', :source_url,
                    :license, :attribution, :verse_count, :is_default, :fetched_at, NOW(), NOW())
            ON CONFLICT (key) DO UPDATE SET
                language = EXCLUDED.language, title = EXCLUDED.title,
                translator_name = EXCLUDED.translator_name, version = EXCLUDED.version,
                source_url = EXCLUDED.source_url, license = EXCLUDED.license,
                attribution = EXCLUDED.attribution, verse_count = EXCLUDED.verse_count,
                is_default = EXCLUDED.is_default, fetched_at = EXCLUDED.fetched_at,
                updated_at = NOW()
            """
        ),
        {
            "key": key,
            "language": data["language_iso_code"],
            "title": data["title"],
            "translator_name": edition.get("translator_name"),
            "version": data["version"],
            "source_url": f"https://quranenc.com/en/browse/{key}",
            "license": edition["license"],
            "attribution": (
                f"{data['title']}, version {data['version']}. "
                f"Published by QuranEnc.com (https://quranenc.com/en/browse/{key}); "
                "reproduced without modification."
            ),
            "verse_count": len(data["verses"]),
            "is_default": is_default,
            "fetched_at": data["fetched_at"],
        },
    )
    rows = [
        {
            "verse_id": verse_ids[(v["sura"], v["aya"])],
            "language": data["language_iso_code"],
            "translator": key,
            "text": v["translation"],
            "footnotes": v["footnotes"],
            "version": data["version"],
        }
        for v in data["verses"]
    ]
    db.execute(
        text(
            """
            INSERT INTO translations
                (verse_id, language, translator, text, footnotes, source_id, edition_version,
                 confidence, needs_review, created_at, updated_at)
            VALUES (:verse_id, :language, :translator, :text, :footnotes, 'quranenc', :version,
                    100, 0, NOW(), NOW())
            ON CONFLICT (verse_id, language, translator) DO UPDATE SET
                text = EXCLUDED.text, footnotes = EXCLUDED.footnotes,
                source_id = EXCLUDED.source_id, edition_version = EXCLUDED.edition_version,
                updated_at = NOW()
            """
        ),
        rows,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keys", nargs="*", help="edition keys (default: every edition in the manifest)")
    parser.add_argument("--refresh", action="store_true", help="re-download even if the cache is current")
    parser.add_argument("--dry-run", action="store_true", help="fetch and verify, do not write the database")
    args = parser.parse_args()

    manifest = load_manifest()
    editions = {e["key"]: e for e in manifest["editions"]}
    keys = args.keys or list(editions)
    unknown = [k for k in keys if k not in editions]
    if unknown:
        print(f"Not in {MANIFEST.relative_to(REPO_ROOT)}: {unknown}")
        return 2

    http = requests.Session()
    http.headers["User-Agent"] = "Tadabbur-AI translation seeder"
    catalogue = fetch_catalogue(http)

    db = SyncSessionLocal()
    try:
        verse_ids = {
            (s, a): vid
            for vid, s, a in db.execute(text("SELECT id, sura_no, aya_no FROM quran_verses")).all()
        }
        if len(verse_ids) != TOTAL_VERSES:
            print(f"quran_verses has {len(verse_ids)} rows, expected {TOTAL_VERSES}; seed the Qur'an first")
            return 1

        for key in keys:
            if key not in catalogue:
                print(f"  {key}: no longer published by QuranEnc, skipped")
                continue
            data = load_or_download(http, key, catalogue[key], args.refresh)
            verify(data, verse_ids)
            if args.dry_run:
                print(f"  {key} v{data['version']}: {len(data['verses'])} verses OK (dry run)")
                continue
            upsert(db, editions[key], data, verse_ids, key in manifest["defaults"].values())
            db.commit()
            print(f"  {key} v{data['version']}: {len(data['verses'])} verses seeded")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
