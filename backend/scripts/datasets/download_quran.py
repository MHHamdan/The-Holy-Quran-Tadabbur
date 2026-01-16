#!/usr/bin/env python3
"""
Download Quran text from public API.

Downloads from api.alquran.cloud and transforms to expected format.
"""
import sys
import os
import json
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(2)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
ASSETS_DIR = PROJECT_ROOT / "assets"

# API endpoints
QURAN_API = "https://api.alquran.cloud/v1/quran/quran-uthmani"
QURAN_SIMPLE_API = "https://api.alquran.cloud/v1/quran/quran-simple"

# Page/Juz data (approximate - based on standard Madani mushaf)
# This maps verse IDs to page numbers
PAGE_DATA_URL = "https://api.alquran.cloud/v1/meta"


def download_quran_text() -> dict:
    """Download Quran text in Uthmani script."""
    print("  Downloading Uthmani text...")
    with httpx.Client(timeout=60.0) as client:
        response = client.get(QURAN_API)
        response.raise_for_status()
        return response.json()


def download_simple_text() -> dict:
    """Download Quran text in simple/imlaei script."""
    print("  Downloading simple text...")
    with httpx.Client(timeout=60.0) as client:
        response = client.get(QURAN_SIMPLE_API)
        response.raise_for_status()
        return response.json()


def download_metadata() -> dict:
    """Download Quran metadata (pages, juz, etc.)."""
    print("  Downloading metadata...")
    with httpx.Client(timeout=60.0) as client:
        response = client.get(PAGE_DATA_URL)
        response.raise_for_status()
        return response.json()


def transform_data(uthmani_data: dict, simple_data: dict, meta_data: dict) -> list:
    """Transform API data to expected format."""
    print("\n[2/3] Transforming data...")

    # Build simple text lookup
    simple_lookup = {}
    for sura in simple_data.get("data", {}).get("surahs", []):
        for ayah in sura.get("ayahs", []):
            simple_lookup[ayah["number"]] = ayah["text"]

    # Build page/juz lookup from metadata
    # The API provides sura/ayah references for pages and juz
    suras_meta = meta_data.get("data", {}).get("surahs", {}).get("references", [])

    # Create verse list
    verses = []
    verse_id = 0

    for sura in uthmani_data.get("data", {}).get("surahs", []):
        sura_no = sura["number"]
        sura_name_ar = sura["name"]
        sura_name_en = sura["englishName"]

        for ayah in sura.get("ayahs", []):
            verse_id += 1
            aya_no = ayah["numberInSurah"]
            global_number = ayah["number"]

            # Get page and juz from ayah data
            page = ayah.get("page", 1)
            juz = ayah.get("juz", 1)

            verse = {
                "id": verse_id,
                "sura_no": sura_no,
                "sura_name_ar": sura_name_ar,
                "sura_name_en": sura_name_en,
                "aya_no": aya_no,
                "aya_text": ayah["text"],
                "aya_text_emlaey": simple_lookup.get(global_number, ayah["text"]),
                "page": page,
                "jozz": juz,
                "line_start": None,
                "line_end": None,
            }
            verses.append(verse)

    print(f"  Transformed {len(verses)} verses")
    return verses


def save_data(verses: list, output_path: Path):
    """Save transformed data to JSON file."""
    print(f"\n[3/3] Saving to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    file_size = output_path.stat().st_size
    print(f"  Saved {file_size:,} bytes")


def main():
    """Main entry point."""
    print("=" * 60)
    print("QURAN DATA DOWNLOAD")
    print("=" * 60)

    start_time = time.time()

    try:
        # Download from API
        print("\n[1/3] Downloading from API...")
        uthmani_data = download_quran_text()
        time.sleep(1)  # Rate limiting
        simple_data = download_simple_text()
        time.sleep(1)
        meta_data = download_metadata()

        # Transform
        verses = transform_data(uthmani_data, simple_data, meta_data)

        # Validate
        if len(verses) != 6236:
            print(f"  WARNING: Expected 6236 verses, got {len(verses)}")

        # Save to assets directory (where manifest expects it)
        output_path = ASSETS_DIR / "hafs_smart_v8.json"
        save_data(verses, output_path)

        # Also save to raw directory
        raw_path = RAW_DIR / "quran_uthmani.json"
        save_data(verses, raw_path)

        duration = time.time() - start_time
        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print(f"  Verses downloaded: {len(verses)}")
        print(f"  Primary output: {output_path}")
        print(f"  Backup output: {raw_path}")
        print(f"  Duration: {duration:.1f}s")
        print("\nNext step: make seed-quran")
        print("=" * 60)

    except httpx.HTTPError as e:
        print(f"\nERROR: HTTP error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
