"""
Seed mushaf_words table — King Fahd Mushaf word-level page/line layout

Fetches word positions (page, line) from qurancdn.com API for all 604 pages
and stores them in the mushaf_words table.  This is a one-time seed that
makes the platform independent of qurancdn at runtime.

Usage:
    python backend/scripts/ingest/seed_mushaf_words.py            # all 604 pages
    python backend/scripts/ingest/seed_mushaf_words.py --page 1   # single page
    python backend/scripts/ingest/seed_mushaf_words.py --dry-run  # parse only
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from app.db.database import SyncSessionLocal

QURANCDN_BASE = "https://api.qurancdn.com/api/qdc"
WORD_FIELDS = "text_uthmani,line_number,page_number"
TOTAL_PAGES = 604

VALID_CHAR_TYPES = {"word", "end", "hizb", "sajda", "rub", "page"}


def fetch_page_words(page: int, session: requests.Session) -> list[dict]:
    """Return all words (+ end markers) on a Mushaf page from qurancdn."""
    url = (
        f"{QURANCDN_BASE}/verses/by_page/{page}"
        f"?words=true&word_fields={WORD_FIELDS}&per_page=500"
    )
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows: list[dict] = []
    order = 1
    for verse in data.get("verses", []):
        sura_str, aya_str = verse["verse_key"].split(":")
        sura_no = int(sura_str)
        aya_no = int(aya_str)

        for w in verse.get("words", []):
            raw_type = w.get("char_type_name", "word")
            char_type = raw_type if raw_type in VALID_CHAR_TYPES else "word"
            text_val = w.get("text_uthmani", "")
            line_no = w.get("line_number")
            wp = w.get("position", 0)

            if not text_val or line_no is None:
                continue

            rows.append(
                {
                    "page_no": page,
                    "line_no": int(line_no),
                    "word_order": order,
                    "sura_no": sura_no,
                    "aya_no": aya_no,
                    "word_pos": int(wp),
                    "text_uthmani": text_val,
                    "char_type": char_type,
                }
            )
            order += 1

    return rows


def seed_page(page: int, db, http: requests.Session, dry_run: bool) -> int:
    rows = fetch_page_words(page, http)
    if dry_run or not rows:
        return len(rows)

    db.execute(
        text(
            """
            INSERT INTO mushaf_words
                (page_no, line_no, word_order, sura_no, aya_no, word_pos,
                 text_uthmani, char_type)
            VALUES
                (:page_no, :line_no, :word_order, :sura_no, :aya_no, :word_pos,
                 :text_uthmani, :char_type)
            ON CONFLICT (page_no, word_order) DO UPDATE
                SET line_no      = EXCLUDED.line_no,
                    sura_no      = EXCLUDED.sura_no,
                    aya_no       = EXCLUDED.aya_no,
                    word_pos     = EXCLUDED.word_pos,
                    text_uthmani = EXCLUDED.text_uthmani,
                    char_type    = EXCLUDED.char_type
            """
        ),
        rows,
    )
    db.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed mushaf_words table")
    parser.add_argument("--page", type=int, help="Seed a single page (1-604)")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
    args = parser.parse_args()

    pages = [args.page] if args.page else list(range(1, TOTAL_PAGES + 1))

    print(f"Seeding mushaf_words — {len(pages)} page(s)  |  dry_run={args.dry_run}")

    http = requests.Session()
    http.headers["User-Agent"] = "Tadabbur-Mushaf-Seed/1.0"

    total_words = 0
    db = SyncSessionLocal() if not args.dry_run else None
    try:
        for page in pages:
            try:
                n = seed_page(page, db, http, args.dry_run)
                total_words += n
                if page % 50 == 0 or page == pages[-1]:
                    print(f"  Page {page:3d} … {n} words  (total so far: {total_words})")
            except Exception as exc:
                print(f"  Page {page:3d} FAILED: {exc}", file=sys.stderr)
                time.sleep(2)
            # Light rate limiting
            time.sleep(0.1)
    finally:
        if db:
            db.close()

    print(f"\nDone — {total_words} words written to mushaf_words")


if __name__ == "__main__":
    main()
