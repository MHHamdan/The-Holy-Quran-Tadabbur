#!/usr/bin/env python3
"""
Verify downloaded datasets exist and are valid.

Checks:
  - Files exist
  - File sizes are reasonable
  - Files are readable (UTF-8)
  - Basic structure validation

Exit codes:
  0 - All downloads verified
  1 - One or more downloads failed verification
"""
import sys
import os
import json
import hashlib
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"
RAW_DIR = DATA_DIR / "raw"


def verify_file_exists(path: Path) -> tuple[bool, str]:
    """Check if file exists."""
    if path.exists():
        return True, f"File exists: {path}"
    return False, f"File not found: {path}"


def verify_file_size(path: Path, min_bytes: int) -> tuple[bool, str]:
    """Check if file is at least min_bytes."""
    if not path.exists():
        return False, f"File not found: {path}"

    size = path.stat().st_size
    if size >= min_bytes:
        return True, f"File size OK: {size:,} bytes (min: {min_bytes:,})"
    return False, f"File too small: {size:,} bytes (min: {min_bytes:,})"


def verify_utf8_readable(path: Path) -> tuple[bool, str]:
    """Check if file is readable as UTF-8."""
    if not path.exists():
        return False, f"File not found: {path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Read first 10KB to verify encoding
            sample = f.read(10240)
            if len(sample) > 0:
                return True, "File is readable as UTF-8"
            return False, "File is empty"
    except UnicodeDecodeError as e:
        return False, f"UTF-8 encoding error: {str(e)}"
    except Exception as e:
        return False, f"Read error: {str(e)}"


def verify_json_structure(path: Path, required_fields: list = None) -> tuple[bool, str]:
    """Verify JSON is valid and has required fields."""
    if not path.exists():
        return False, f"File not found: {path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            if len(data) == 0:
                return False, "JSON array is empty"
            sample = data[0]
        elif isinstance(data, dict):
            sample = data
        else:
            return False, f"Unexpected JSON type: {type(data)}"

        if required_fields:
            missing = [f for f in required_fields if f not in sample]
            if missing:
                return False, f"Missing required fields: {missing}"

        return True, f"JSON structure valid, {len(data) if isinstance(data, list) else 'dict'} items"
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def verify_checksum(path: Path, expected_sha256: str) -> tuple[bool, str]:
    """Verify file SHA256 checksum."""
    if not path.exists():
        return False, f"File not found: {path}"

    if not expected_sha256:
        return True, "No checksum provided, skipping"

    try:
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        actual = sha256.hexdigest()

        if actual == expected_sha256.lower():
            return True, f"Checksum verified: {actual[:16]}..."
        return False, f"Checksum mismatch: expected {expected_sha256[:16]}... got {actual[:16]}..."
    except Exception as e:
        return False, f"Checksum error: {str(e)}"


def verify_quran_data() -> list[tuple[str, bool, str]]:
    """Verify Quran data files."""
    results = []

    # Check manifest
    manifest_path = MANIFESTS_DIR / "quran_hafs.json"
    passed, msg = verify_file_exists(manifest_path)
    results.append(("Quran manifest exists", passed, msg))

    if not passed:
        return results

    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Check for local source first (from existing project)
    local_source = None
    for source in manifest.get("sources", []):
        if source.get("is_primary") and "path" in source:
            local_source = source
            break

    if local_source:
        local_path = (MANIFESTS_DIR / local_source["path"]).resolve()
        passed, msg = verify_file_exists(local_path)
        results.append(("Quran source file exists", passed, msg))

        if passed:
            # Verify size
            min_size = manifest.get("validation", {}).get("min_file_size_bytes", 100000)
            passed, msg = verify_file_size(local_path, min_size)
            results.append(("Quran file size", passed, msg))

            # Verify UTF-8
            passed, msg = verify_utf8_readable(local_path)
            results.append(("Quran file encoding", passed, msg))

            # Verify JSON structure
            required = manifest.get("validation", {}).get("required_fields", [])
            passed, msg = verify_json_structure(local_path, required)
            results.append(("Quran JSON structure", passed, msg))

            # Verify verse count if possible
            if passed:
                try:
                    with open(local_path, 'r') as f:
                        data = json.load(f)
                    expected_count = manifest.get("expected_structure", {}).get("total_verses", 6236)
                    actual_count = len(data) if isinstance(data, list) else 0
                    if actual_count == expected_count:
                        results.append(("Quran verse count", True, f"Verified: {actual_count} verses"))
                    else:
                        results.append(("Quran verse count", False, f"Expected {expected_count}, got {actual_count}"))
                except Exception as e:
                    results.append(("Quran verse count", False, str(e)))
    else:
        results.append(("Quran source file", False, "No local primary source found - NEED USER-PROVIDED SOURCE"))

    return results


def verify_tafseer_data() -> list[tuple[str, bool, str]]:
    """Verify tafseer data files."""
    results = []

    # Check manifest
    manifest_path = MANIFESTS_DIR / "tafseer_sources.json"
    passed, msg = verify_file_exists(manifest_path)
    results.append(("Tafseer manifest exists", passed, msg))

    if not passed:
        return results

    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Check each source based on status
    for source in manifest.get("sources", []):
        source_id = source.get("id", "unknown")
        source_name = source.get("name_en", source_id)
        status = source.get("status", "unknown")

        if status == "pending_user_input":
            # Pending sources - report but don't fail
            download_info = source.get("download", {})
            fallback = source.get("fallback", {})
            required = fallback.get("required_fields", ["source_url", "license"])
            results.append((
                f"Tafseer: {source_name}",
                False,
                f"PENDING USER INPUT - need: {', '.join(required)}"
            ))

        elif status == "available_via_api":
            # API sources - check cache directory
            cache_dir = DATA_DIR / "cache" / "tafseer_api" / source_id
            raw_path = RAW_DIR / f"{source_id}.json"

            if raw_path.exists():
                passed, msg = verify_file_size(raw_path, 10000)
                if passed:
                    # Verify structure
                    passed, msg = verify_json_structure(raw_path)
                    if passed:
                        try:
                            with open(raw_path, 'r') as f:
                                data = json.load(f)
                            ayah_count = len(data) if isinstance(data, list) else 0
                            # Full Quran has 6236 ayahs
                            coverage = (ayah_count / 6236) * 100
                            min_coverage = source.get("validation", {}).get("min_ayah_coverage", 0.90) * 100
                            if coverage >= min_coverage:
                                results.append((
                                    f"Tafseer: {source_name}",
                                    True,
                                    f"Downloaded via API: {ayah_count} ayahs ({coverage:.1f}% coverage)"
                                ))
                            else:
                                results.append((
                                    f"Tafseer: {source_name}",
                                    False,
                                    f"Incomplete: {ayah_count} ayahs ({coverage:.1f}% < {min_coverage}%)"
                                ))
                        except Exception as e:
                            results.append((
                                f"Tafseer: {source_name}",
                                False,
                                f"Parse error: {str(e)}"
                            ))
                    else:
                        results.append((f"Tafseer: {source_name}", False, msg))
                else:
                    results.append((f"Tafseer: {source_name}", False, msg))
            elif cache_dir.exists():
                # Check cache files
                cache_files = list(cache_dir.glob("*.json"))
                if cache_files:
                    coverage = (len(cache_files) / 6236) * 100
                    results.append((
                        f"Tafseer: {source_name}",
                        True,
                        f"Cached: {len(cache_files)} ayahs ({coverage:.1f}% coverage)"
                    ))
                else:
                    results.append((
                        f"Tafseer: {source_name}",
                        False,
                        "API source - not downloaded yet (run download_tafseer.py)"
                    ))
            else:
                results.append((
                    f"Tafseer: {source_name}",
                    False,
                    "API source - not downloaded yet (run download_tafseer.py)"
                ))

        elif status == "available":
            # File-based sources - check download
            download_info = source.get("download", {})
            url = download_info.get("url", "")

            if url == "NEED_USER_PROVIDED_SOURCE_URL":
                results.append((
                    f"Tafseer: {source_name}",
                    False,
                    "NEED USER-PROVIDED SOURCE URL"
                ))
            else:
                file_format = download_info.get("format", "json")
                raw_path = RAW_DIR / f"{source_id}.{file_format}"

                if raw_path.exists():
                    min_size = source.get("validation", {}).get("min_file_size_bytes", 1000)
                    passed, msg = verify_file_size(raw_path, min_size)
                    if passed:
                        results.append((
                            f"Tafseer: {source_name}",
                            True,
                            f"Downloaded: {raw_path.stat().st_size:,} bytes"
                        ))
                    else:
                        results.append((f"Tafseer: {source_name}", False, msg))
                else:
                    results.append((
                        f"Tafseer: {source_name}",
                        False,
                        f"Not downloaded: {raw_path}"
                    ))

        else:
            results.append((
                f"Tafseer: {source_name}",
                False,
                f"Unknown status: {status}"
            ))

    # Check placeholder sources
    for placeholder in manifest.get("placeholder_sources", []):
        source_name = placeholder.get("name_en", placeholder.get("id", "unknown"))
        priority = placeholder.get("priority", "medium")
        results.append((
            f"Tafseer (placeholder): {source_name}",
            False,
            f"PENDING USER INPUT (priority: {priority})"
        ))

    return results


def verify_stories_data() -> list[tuple[str, bool, str]]:
    """Verify stories manifest."""
    results = []

    manifest_path = MANIFESTS_DIR / "stories.json"
    passed, msg = verify_file_exists(manifest_path)
    results.append(("Stories manifest exists", passed, msg))

    if passed:
        passed, msg = verify_json_structure(manifest_path, ["stories"])
        results.append(("Stories manifest structure", passed, msg))

        # Count stories
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            story_count = len(data.get("stories", []))
            results.append(("Stories count", True, f"{story_count} stories defined"))
        except Exception as e:
            results.append(("Stories count", False, str(e)))

    return results


def main():
    """Run all download verifications."""
    print("=" * 60)
    print("DOWNLOAD VERIFICATION")
    print("=" * 60)

    all_results = []
    all_passed = True

    # Verify directories exist
    print("\n[1/4] Checking directories...")
    for dir_path in [DATA_DIR, MANIFESTS_DIR, RAW_DIR]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
        else:
            print(f"  Exists: {dir_path}")

    # Verify Quran data
    print("\n[2/4] Verifying Quran data...")
    results = verify_quran_data()
    for name, passed, msg in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        print(f"         {msg}")
        if not passed:
            all_passed = False
    all_results.extend(results)

    # Verify Tafseer data
    print("\n[3/4] Verifying Tafseer data...")
    results = verify_tafseer_data()
    for name, passed, msg in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        print(f"         {msg}")
        if not passed:
            all_passed = False
    all_results.extend(results)

    # Verify Stories data
    print("\n[4/4] Verifying Stories data...")
    results = verify_stories_data()
    for name, passed, msg in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        print(f"         {msg}")
        if not passed:
            all_passed = False
    all_results.extend(results)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, p, _ in all_results if p)
    total_count = len(all_results)
    print(f"  Passed: {passed_count}/{total_count}")

    print("\n" + "=" * 60)

    if all_passed:
        print("OVERALL: PASS - All downloads verified")
        print("=" * 60)
        sys.exit(0)
    else:
        print("OVERALL: FAIL - Some downloads need attention")
        print("=" * 60)
        print("\nREMEDIATION:")
        print("  1. Check manifest files for NEED_USER_PROVIDED_SOURCE_URL")
        print("  2. Provide valid URLs and licenses for missing sources")
        print("  3. Run download script: python scripts/datasets/download.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
