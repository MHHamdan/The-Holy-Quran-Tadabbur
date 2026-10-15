"""Store privacy declarations stay consistent with each other.

- The iOS privacy manifest (PrivacyInfo.xcprivacy) declares exactly the data
  types listed in the App Store table of docs/store/data-safety.md.
- It declares the File Timestamp required-reason API (C617.1) used by
  @capacitor/filesystem.
- Android keeps WebView storage out of backups and drops the exact-alarm
  permission.
"""
import plistlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
XCPRIVACY = ROOT / "frontend" / "ios" / "App" / "App" / "PrivacyInfo.xcprivacy"
DATA_SAFETY = ROOT / "docs" / "store" / "data-safety.md"
ANDROID_MAIN = ROOT / "frontend" / "android" / "app" / "src" / "main"

# App Store Connect label (as written in the doc) -> manifest constant
APPLE_TYPES = {
    "Audio Data": "NSPrivacyCollectedDataTypeAudioData",
    "Other User Content": "NSPrivacyCollectedDataTypeOtherUserContent",
    "Search History": "NSPrivacyCollectedDataTypeSearchHistory",
    "Coarse Location": "NSPrivacyCollectedDataTypeCoarseLocation",
    "Precise Location": "NSPrivacyCollectedDataTypePreciseLocation",
    "Sensitive Info": "NSPrivacyCollectedDataTypeSensitiveInfo",
    "Health": "NSPrivacyCollectedDataTypeHealth",
}

pytestmark = pytest.mark.skipif(not XCPRIVACY.exists(), reason="native projects not present")


def _manifest() -> dict:
    with XCPRIVACY.open("rb") as fh:
        return plistlib.load(fh)


def _doc_apple_types() -> set[str]:
    text = DATA_SAFETY.read_text(encoding="utf-8")
    section = text.split("## App Store Connect", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\|\s*([^|]+?)\s*\|\s*No\s*\|\s*No\s*\|", section, flags=re.M)
    return {APPLE_TYPES[r] for r in rows}


def test_manifest_data_types_match_store_doc():
    declared = {d["NSPrivacyCollectedDataType"] for d in _manifest()["NSPrivacyCollectedDataTypes"]}
    assert declared == _doc_apple_types()


def test_nothing_linked_or_tracking():
    manifest = _manifest()
    assert manifest["NSPrivacyTracking"] is False
    assert manifest["NSPrivacyTrackingDomains"] == []
    for entry in manifest["NSPrivacyCollectedDataTypes"]:
        assert entry["NSPrivacyCollectedDataTypeLinked"] is False
        assert entry["NSPrivacyCollectedDataTypeTracking"] is False


def test_file_timestamp_required_reason_declared():
    api = {d["NSPrivacyAccessedAPIType"]: d["NSPrivacyAccessedAPITypeReasons"]
           for d in _manifest()["NSPrivacyAccessedAPITypes"]}
    assert api.get("NSPrivacyAccessedAPICategoryFileTimestamp") == ["C617.1"]


def test_android_backup_excludes_webview_storage():
    manifest = (ANDROID_MAIN / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert 'android:dataExtractionRules="@xml/data_extraction_rules"' in manifest
    assert 'android:fullBackupContent="@xml/backup_rules"' in manifest
    rules = (ANDROID_MAIN / "res" / "xml" / "data_extraction_rules.xml").read_text(encoding="utf-8")
    for block in ("cloud-backup", "device-transfer"):
        body = rules.split(f"<{block}>", 1)[1].split(f"</{block}>", 1)[0]
        assert '<exclude domain="root" path="app_webview/" />' in body, block
    legacy = (ANDROID_MAIN / "res" / "xml" / "backup_rules.xml").read_text(encoding="utf-8")
    assert '<exclude domain="root" path="app_webview/" />' in legacy


def test_android_exact_alarm_permission_removed():
    manifest = (ANDROID_MAIN / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert re.search(
        r'<uses-permission android:name="android\.permission\.SCHEDULE_EXACT_ALARM"\s+tools:node="remove"',
        manifest,
    )
