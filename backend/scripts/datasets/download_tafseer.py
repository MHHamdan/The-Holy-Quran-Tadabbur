#!/usr/bin/env python3
"""
Download tafseer sources with license-safe handling.

Features:
  - CDN-based sources: Fast download from spa5k/tafsir_api (jsdelivr CDN)
  - API-based sources: Rate-limited fetching with caching (fallback)
  - File-based sources: Download only if license verified
  - Pending sources: Skip and report what user needs to provide
  - Cache management: Respect cache duration from manifest

CDN Source (Primary - No Rate Limits):
  https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/{tafsir-name}/{surah}.json

Exit codes:
  0 - All available sources downloaded successfully
  1 - Some sources failed (excluding pending_user_input)
  2 - Configuration error
"""
import sys
import os
import json
import time
import hashlib
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache" / "tafseer_api"

# Quran structure: 114 surahs
SURAH_AYAH_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6
]

# CDN tafsir mapping: our source_id -> spa5k tafsir folder name
# Source: https://github.com/spa5k/tafsir_api
CDN_TAFSIR_MAP = {
    # English
    "ibn_kathir_en": "en-tafisr-ibn-kathir",  # Note: typo in original repo name
    "ibn_abbas_en": "en-tafsir-ibn-abbas",
    "jalalayn_en": "en-al-jalalayn",
    "maarif_ul_quran_en": "en-tafsir-maarif-ul-quran",
    "tustari_en": "en-tafsir-al-tustari",
    "kashani_en": "en-kashani-tafsir",
    "qushairi_en": "en-al-qushairi-tafsir",
    "asbab_nuzul_en": "en-asbab-al-nuzul-by-al-wahidi",
    # Arabic
    "ibn_kathir_ar": "ar-tafsir-ibn-kathir",
    "muyassar_ar": "ar-tafsir-muyassar",
    "qurtubi_ar": "ar-tafseer-al-qurtubi",
    "tabari_ar": "ar-tafsir-al-tabari",
    "baghawi_ar": "ar-tafsir-al-baghawi",
    "saddi_ar": "ar-tafseer-al-saddi",
    "tanwir_ar": "ar-tafseer-tanwir-al-miqbas",
    "wasit_ar": "ar-tafsir-al-wasit",
    # Urdu
    "ibn_kathir_ur": "ur-tafseer-ibn-e-kaseer",
    "bayan_ur": "ur-tafsir-bayan-ul-quran",
    # Bengali
    "ibn_kathir_bn": "bn-tafseer-ibn-e-kaseer",
    "fathul_majid_bn": "bn-tafisr-fathul-majid",
}

CDN_BASE_URL = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir"


@dataclass
class DownloadResult:
    """Result of a download attempt."""
    source_id: str
    success: bool
    status: str  # 'downloaded', 'cached', 'skipped_pending', 'failed'
    message: str
    ayahs_fetched: int = 0
    cache_hits: int = 0


class TafseerDownloader:
    """Downloads tafseer sources with rate limiting and caching."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.results: list[DownloadResult] = []
        self._last_request_time = 0.0

    def _load_manifest(self) -> dict:
        """Load tafseer manifest."""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_cache_path(self, source_id: str, surah: int, ayah: int) -> Path:
        """Get cache file path for an ayah."""
        return CACHE_DIR / source_id / f"s{surah:03d}_a{ayah:03d}.json"

    def _is_cache_valid(self, cache_path: Path, max_age_hours: int) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=max_age_hours)

    def _read_cache(self, cache_path: Path) -> Optional[dict]:
        """Read cached response."""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _write_cache(self, cache_path: Path, data: dict) -> None:
        """Write response to cache."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def _rate_limit(self, requests_per_second: float) -> None:
        """Enforce rate limiting."""
        min_interval = 1.0 / requests_per_second
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    async def _fetch_api_tafseer(
        self,
        session: aiohttp.ClientSession,
        source: dict,
        surah: int,
        ayah: int
    ) -> Optional[dict]:
        """Fetch single ayah tafseer from API."""
        api_config = source.get("api_source", {})
        base_url = api_config.get("base_url", "")
        tafsir_id = api_config.get("tafsir_id")
        rate_limit = api_config.get("rate_limit_requests_per_second", 2)

        if not base_url or not tafsir_id:
            return None

        # Check cache first
        cache_hours = api_config.get("cache_duration_hours", 168)
        cache_path = self._get_cache_path(source["id"], surah, ayah)

        if self._is_cache_valid(cache_path, cache_hours):
            return self._read_cache(cache_path)

        # Rate limit
        await self._rate_limit(rate_limit)

        # Fetch from API
        url = f"{base_url}/{tafsir_id}/{surah}/{ayah}"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Normalize response
                    result = {
                        "surah": surah,
                        "ayah": ayah,
                        "text": data.get("text", data.get("tafsir", "")),
                        "source_id": source["id"],
                        "fetched_at": datetime.now().isoformat()
                    }
                    # Cache the response
                    self._write_cache(cache_path, result)
                    return result
                elif response.status == 404:
                    # Ayah not available in this tafseer
                    return None
                else:
                    print(f"    API error for {surah}:{ayah}: HTTP {response.status}")
                    return None
        except asyncio.TimeoutError:
            print(f"    Timeout for {surah}:{ayah}")
            return None
        except Exception as e:
            print(f"    Error for {surah}:{ayah}: {str(e)}")
            return None

    async def download_cdn_source(self, source_id: str, cdn_name: str) -> DownloadResult:
        """Download tafseer from spa5k CDN (fast, no rate limits)."""
        print(f"\n  Downloading: {source_id} (via CDN)")
        print(f"    CDN source: {cdn_name}")

        all_tafseer = []
        failed_surahs = []

        async with aiohttp.ClientSession() as session:
            for surah in range(1, 115):
                url = f"{CDN_BASE_URL}/{cdn_name}/{surah}.json"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            data = await response.json()
                            ayahs = data.get("ayahs", [])
                            for ayah_data in ayahs:
                                all_tafseer.append({
                                    "surah": ayah_data.get("surah", surah),
                                    "ayah": ayah_data.get("ayah"),
                                    "text": ayah_data.get("text", ""),
                                    "source_id": source_id
                                })
                            if surah % 20 == 0:
                                print(f"    Downloaded surah {surah}/114")
                        else:
                            failed_surahs.append(surah)
                            print(f"    Failed surah {surah}: HTTP {response.status}")
                except Exception as e:
                    failed_surahs.append(surah)
                    print(f"    Error surah {surah}: {str(e)}")

        if not all_tafseer:
            return DownloadResult(
                source_id=source_id,
                success=False,
                status="failed",
                message="No data downloaded from CDN"
            )

        # Save to raw directory
        output_path = RAW_DIR / f"{source_id}.json"
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_tafseer, f, ensure_ascii=False, indent=2)

        msg = f"Downloaded {len(all_tafseer)} ayahs from CDN"
        if failed_surahs:
            msg += f" ({len(failed_surahs)} surahs failed)"

        return DownloadResult(
            source_id=source_id,
            success=True,
            status="downloaded",
            message=msg,
            ayahs_fetched=len(all_tafseer)
        )

    async def download_api_source(self, source: dict) -> DownloadResult:
        """Download an API-based tafseer source."""
        source_id = source["id"]
        name = source.get("name_en", source_id)
        print(f"\n  Downloading: {name} (via API)")

        api_config = source.get("api_source", {})
        cache_hours = api_config.get("cache_duration_hours", 168)

        # Create cache directory
        source_cache_dir = CACHE_DIR / source_id
        source_cache_dir.mkdir(parents=True, exist_ok=True)

        # Check how many are already cached
        cached_count = 0
        for surah_idx, ayah_count in enumerate(SURAH_AYAH_COUNTS, 1):
            for ayah in range(1, ayah_count + 1):
                cache_path = self._get_cache_path(source_id, surah_idx, ayah)
                if self._is_cache_valid(cache_path, cache_hours):
                    cached_count += 1

        total_ayahs = sum(SURAH_AYAH_COUNTS)
        if cached_count == total_ayahs:
            return DownloadResult(
                source_id=source_id,
                success=True,
                status="cached",
                message=f"All {total_ayahs} ayahs cached (valid for {cache_hours}h)",
                ayahs_fetched=0,
                cache_hits=total_ayahs
            )

        print(f"    Cached: {cached_count}/{total_ayahs} ayahs")
        print(f"    Fetching remaining {total_ayahs - cached_count} ayahs...")

        # Fetch remaining ayahs
        fetched_count = 0
        failed_count = 0

        async with aiohttp.ClientSession() as session:
            for surah_idx, ayah_count in enumerate(SURAH_AYAH_COUNTS, 1):
                surah_fetched = 0
                for ayah in range(1, ayah_count + 1):
                    cache_path = self._get_cache_path(source_id, surah_idx, ayah)
                    if not self._is_cache_valid(cache_path, cache_hours):
                        result = await self._fetch_api_tafseer(session, source, surah_idx, ayah)
                        if result:
                            fetched_count += 1
                            surah_fetched += 1
                        else:
                            failed_count += 1

                if surah_fetched > 0:
                    print(f"    Surah {surah_idx}: fetched {surah_fetched} ayahs")

        # Compile final output
        output_path = RAW_DIR / f"{source_id}.json"
        all_tafseer = []

        for surah_idx, ayah_count in enumerate(SURAH_AYAH_COUNTS, 1):
            for ayah in range(1, ayah_count + 1):
                cache_path = self._get_cache_path(source_id, surah_idx, ayah)
                cached = self._read_cache(cache_path)
                if cached:
                    all_tafseer.append(cached)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_tafseer, f, ensure_ascii=False, indent=2)

        return DownloadResult(
            source_id=source_id,
            success=True,
            status="downloaded",
            message=f"Fetched {fetched_count} ayahs, {cached_count} from cache, {failed_count} failed",
            ayahs_fetched=fetched_count,
            cache_hits=cached_count
        )

    async def download_file_source(self, source: dict) -> DownloadResult:
        """Download a file-based tafseer source."""
        source_id = source["id"]
        name = source.get("name_en", source_id)
        download_info = source.get("download", {})

        url = download_info.get("url", "")
        license_info = download_info.get("license", "")

        # Check if source needs user input
        if url == "NEED_USER_PROVIDED_SOURCE_URL" or license_info == "NEED_LICENSE_VERIFICATION":
            return DownloadResult(
                source_id=source_id,
                success=False,
                status="skipped_pending",
                message=f"Requires user input: URL={url}, License={license_info}"
            )

        print(f"\n  Downloading: {name}")
        print(f"    URL: {url}")
        print(f"    License: {license_info}")

        output_path = RAW_DIR / f"{source_id}.{download_info.get('format', 'json')}"

        # Check if already downloaded
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"    Already downloaded: {size:,} bytes")
            return DownloadResult(
                source_id=source_id,
                success=True,
                status="cached",
                message=f"Already downloaded ({size:,} bytes)"
            )

        # Download file
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        content = await response.text()
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        size = output_path.stat().st_size
                        print(f"    Downloaded: {size:,} bytes")

                        return DownloadResult(
                            source_id=source_id,
                            success=True,
                            status="downloaded",
                            message=f"Downloaded {size:,} bytes"
                        )
                    else:
                        return DownloadResult(
                            source_id=source_id,
                            success=False,
                            status="failed",
                            message=f"HTTP {response.status}"
                        )
        except Exception as e:
            return DownloadResult(
                source_id=source_id,
                success=False,
                status="failed",
                message=str(e)
            )

    async def download_source(self, source: dict) -> DownloadResult:
        """Download a single tafseer source."""
        source_id = source["id"]
        status = source.get("status", "unknown")

        # Try CDN first (fastest, no rate limits)
        if source_id in CDN_TAFSIR_MAP:
            cdn_name = CDN_TAFSIR_MAP[source_id]
            return await self.download_cdn_source(source_id, cdn_name)

        if status == "pending_user_input":
            return DownloadResult(
                source_id=source_id,
                success=False,
                status="skipped_pending",
                message="Waiting for user-provided source URL and license"
            )
        elif status == "available_via_api":
            return await self.download_api_source(source)
        elif status == "available":
            return await self.download_file_source(source)
        else:
            return DownloadResult(
                source_id=source_id,
                success=False,
                status="skipped_pending",
                message=f"Unknown status: {status}"
            )

    async def download_all(self, source_ids: Optional[list[str]] = None) -> list[DownloadResult]:
        """Download all (or specified) tafseer sources."""
        results = []

        # If specific sources requested
        if source_ids:
            for source_id in source_ids:
                # Check if it's a CDN source
                if source_id in CDN_TAFSIR_MAP:
                    cdn_name = CDN_TAFSIR_MAP[source_id]
                    result = await self.download_cdn_source(source_id, cdn_name)
                else:
                    # Look in manifest
                    sources = self.manifest.get("sources", [])
                    source = next((s for s in sources if s["id"] == source_id), None)
                    if source:
                        result = await self.download_source(source)
                    else:
                        result = DownloadResult(
                            source_id=source_id,
                            success=False,
                            status="failed",
                            message=f"Source not found: {source_id}"
                        )
                results.append(result)
                self.results.append(result)
        else:
            # Download all manifest sources
            sources = self.manifest.get("sources", [])
            for source in sources:
                result = await self.download_source(source)
                results.append(result)
                self.results.append(result)

        return results

    def print_summary(self) -> int:
        """Print download summary and return exit code."""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)

        downloaded = [r for r in self.results if r.status == "downloaded"]
        cached = [r for r in self.results if r.status == "cached"]
        pending = [r for r in self.results if r.status == "skipped_pending"]
        failed = [r for r in self.results if r.status == "failed"]

        print(f"\n  Downloaded: {len(downloaded)}")
        for r in downloaded:
            print(f"    - {r.source_id}: {r.message}")

        print(f"\n  Cached: {len(cached)}")
        for r in cached:
            print(f"    - {r.source_id}: {r.message}")

        print(f"\n  Pending User Input: {len(pending)}")
        for r in pending:
            print(f"    - {r.source_id}: {r.message}")

        print(f"\n  Failed: {len(failed)}")
        for r in failed:
            print(f"    - {r.source_id}: {r.message}")

        print("\n" + "=" * 60)

        if failed:
            print("RESULT: PARTIAL FAILURE")
            return 1
        elif pending:
            print("RESULT: SUCCESS (some sources pending user input)")
            return 0
        else:
            print("RESULT: SUCCESS")
            return 0


async def main():
    """Main entry point."""
    print("=" * 60)
    print("TAFSEER DOWNLOAD")
    print("=" * 60)

    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Load manifest
    manifest_path = MANIFESTS_DIR / "tafseer_sources.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(2)

    # Parse command line args
    source_ids = None
    if len(sys.argv) > 1:
        source_ids = sys.argv[1:]
        print(f"Downloading specific sources: {source_ids}")

    # Download
    downloader = TafseerDownloader(manifest_path)
    await downloader.download_all(source_ids)

    # Print summary and exit
    exit_code = downloader.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
