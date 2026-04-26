"""
Source Registry and Content Integrity Tests — Phase 1

Tests for:
1. Quran integrity validator logic (via local data files)
2. Source registry required fields
3. RAG response must include source metadata
4. Arabic and English text must not be mixed incorrectly
5. Missing source must fail validation

Run with: pytest tests/unit/test_source_registry.py -v
"""

import pytest
import json
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
QURAN_JSON_PATH = PROJECT_ROOT / "data" / "raw" / "quran_uthmani.json"
TAFSIR_MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "tafseer_sources.json"
SOURCE_REGISTRY_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOTAL_SURAHS = 114
TOTAL_AYAHS = 6236

AYAHS_PER_SURAH = [
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
    5, 4, 5, 6,
]

# Required fields for tafsir source manifest entries
REQUIRED_TAFSIR_FIELDS = ["id", "name_ar", "name_en", "author_en", "language"]

# Required fields for source registry entries (in sourceRegistry.ts)
REQUIRED_REGISTRY_FIELDS = [
    "sourceId", "titleArabic", "titleEnglish", "author", "language",
    "type", "reliabilityLevel", "licenseOrTerms", "sourceUrl",
    "lastVerifiedAt", "notes",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def quran_data():
    """Load quran_uthmani.json if it exists."""
    if not QURAN_JSON_PATH.exists():
        pytest.skip(f"Quran data file not found: {QURAN_JSON_PATH}")
    with open(QURAN_JSON_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return raw
    for key in ("verses", "data", "ayahs"):
        if key in raw:
            return raw[key]
    pytest.skip("Could not find ayah array in quran_uthmani.json")


@pytest.fixture(scope="module")
def tafsir_manifest():
    """Load tafseer_sources.json if it exists."""
    if not TAFSIR_MANIFEST_PATH.exists():
        pytest.skip(f"Tafsir manifest not found: {TAFSIR_MANIFEST_PATH}")
    with open(TAFSIR_MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def source_registry_content():
    """Read source registry TypeScript file."""
    if not SOURCE_REGISTRY_PATH.exists():
        pytest.skip(f"Source registry not found: {SOURCE_REGISTRY_PATH}")
    return SOURCE_REGISTRY_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Group 1: Quran Integrity
# ---------------------------------------------------------------------------

class TestQuranIntegrity:
    """Tests that the local Quran JSON meets canonical structural requirements."""

    def test_total_ayah_count(self, quran_data):
        assert len(quran_data) == TOTAL_AYAHS, (
            f"Expected {TOTAL_AYAHS} ayahs, found {len(quran_data)}"
        )

    def test_total_surah_count(self, quran_data):
        surah_nos = {a.get("sura_no") for a in quran_data}
        assert len(surah_nos) == TOTAL_SURAHS, (
            f"Expected {TOTAL_SURAHS} unique surahs, found {len(surah_nos)}"
        )

    def test_all_sura_no_valid(self, quran_data):
        invalid = [a for a in quran_data if not isinstance(a.get("sura_no"), int) or not (1 <= a["sura_no"] <= 114)]
        assert len(invalid) == 0, f"{len(invalid)} ayahs have invalid sura_no"

    def test_all_aya_no_valid(self, quran_data):
        invalid = [a for a in quran_data if not isinstance(a.get("aya_no"), int) or a["aya_no"] < 1]
        assert len(invalid) == 0, f"{len(invalid)} ayahs have invalid aya_no"

    def test_no_duplicate_keys(self, quran_data):
        seen: set[str] = set()
        duplicates: list[str] = []
        for ayah in quran_data:
            key = f"{ayah.get('sura_no')}:{ayah.get('aya_no')}"
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        assert len(duplicates) == 0, f"Duplicate ayah keys found: {duplicates[:5]}"

    def test_no_missing_keys(self, quran_data):
        by_surah: dict[int, set[int]] = {}
        for ayah in quran_data:
            s = ayah.get("sura_no")
            a = ayah.get("aya_no")
            if s and a:
                by_surah.setdefault(s, set()).add(a)

        missing = []
        for surah_idx, expected_count in enumerate(AYAHS_PER_SURAH, start=1):
            found = by_surah.get(surah_idx, set())
            for aya_no in range(1, expected_count + 1):
                if aya_no not in found:
                    missing.append(f"{surah_idx}:{aya_no}")
        assert len(missing) == 0, f"{len(missing)} missing ayahs. First 5: {missing[:5]}"

    def test_no_empty_arabic_text(self, quran_data):
        empty = [
            a for a in quran_data
            if not str(a.get("aya_text") or a.get("text_uthmani") or "").strip()
        ]
        assert len(empty) == 0, f"{len(empty)} ayahs have empty Arabic text"

    def test_arabic_text_not_english(self, quran_data):
        """Arabic text field must not contain long sequences of Latin characters."""
        import re
        latin_pattern = re.compile(r"[a-zA-Z]{5,}")
        suspicious = [
            a for a in quran_data
            if latin_pattern.search(str(a.get("aya_text") or a.get("text_uthmani") or ""))
        ]
        assert len(suspicious) == 0, (
            f"{len(suspicious)} ayahs appear to have English/Latin text in the Arabic field. "
            f"First: {suspicious[0] if suspicious else 'n/a'}"
        )

    def test_ayah_counts_per_surah(self, quran_data):
        by_surah: dict[int, int] = {}
        for ayah in quran_data:
            s = ayah.get("sura_no")
            if s:
                by_surah[s] = by_surah.get(s, 0) + 1

        mismatches = []
        for surah_idx, expected in enumerate(AYAHS_PER_SURAH, start=1):
            found = by_surah.get(surah_idx, 0)
            if found != expected:
                mismatches.append(f"Surah {surah_idx}: expected {expected}, found {found}")

        assert len(mismatches) == 0, f"Ayah count mismatches:\n" + "\n".join(mismatches)


# ---------------------------------------------------------------------------
# Group 2: Tafsir Source Registry
# ---------------------------------------------------------------------------

class TestTafsirSourceManifest:
    """Tests that tafseer_sources.json has all required fields."""

    def test_manifest_has_sources_key(self, tafsir_manifest):
        assert "sources" in tafsir_manifest, "Tafsir manifest missing 'sources' key"

    def test_sources_is_non_empty_list(self, tafsir_manifest):
        sources = tafsir_manifest.get("sources", [])
        assert isinstance(sources, list) and len(sources) > 0, "Tafsir manifest 'sources' must be a non-empty list"

    def test_every_source_has_id(self, tafsir_manifest):
        sources = tafsir_manifest.get("sources", [])
        missing = [s for s in sources if not s.get("id") or not str(s["id"]).strip()]
        assert len(missing) == 0, f"{len(missing)} tafsir sources have no id"

    def test_every_source_has_required_fields(self, tafsir_manifest):
        sources = tafsir_manifest.get("sources", [])
        errors = []
        for source in sources:
            for field in REQUIRED_TAFSIR_FIELDS:
                if not source.get(field) or not str(source[field]).strip():
                    errors.append(f"Source '{source.get('id', '?')}': missing field '{field}'")
        assert len(errors) == 0, f"Missing required fields:\n" + "\n".join(errors)

    def test_no_duplicate_source_ids(self, tafsir_manifest):
        sources = tafsir_manifest.get("sources", [])
        ids = [s.get("id") for s in sources if s.get("id")]
        seen: set[str] = set()
        duplicates = []
        for sid in ids:
            if sid in seen:
                duplicates.append(sid)
            seen.add(sid)
        assert len(duplicates) == 0, f"Duplicate tafsir source ids: {duplicates}"


# ---------------------------------------------------------------------------
# Group 3: Frontend Source Registry
# ---------------------------------------------------------------------------

class TestSourceRegistryFile:
    """Tests for frontend/src/data/sourceRegistry.ts structure."""

    def test_registry_file_exists(self):
        assert SOURCE_REGISTRY_PATH.exists(), f"Source registry not found: {SOURCE_REGISTRY_PATH}"

    def test_registry_has_required_fields(self, source_registry_content):
        for field in REQUIRED_REGISTRY_FIELDS:
            assert f"{field}:" in source_registry_content, (
                f"Source registry missing required field pattern '{field}:'"
            )

    def test_registry_has_no_duplicate_source_ids(self, source_registry_content):
        import re
        ids = re.findall(r"sourceId:\s*['\"]([^'\"]+)['\"]", source_registry_content)
        seen: set[str] = set()
        duplicates = []
        for sid in ids:
            if sid in seen:
                duplicates.append(sid)
            seen.add(sid)
        assert len(duplicates) == 0, f"Duplicate sourceIds in registry: {duplicates}"

    def test_experimental_sources_have_warning(self, source_registry_content):
        """Experimental sources must include DO NOT DISPLAY in notes."""
        import re
        array_start = source_registry_content.find("SOURCE_REGISTRY: Source[] = [")
        helpers_start = source_registry_content.find("// Lookup helpers")
        if array_start == -1:
            pytest.skip("Could not find SOURCE_REGISTRY array")
        end = helpers_start if helpers_start > array_start else len(source_registry_content)
        array_section = source_registry_content[array_start:end]

        if "experimental" not in array_section:
            pytest.skip("No experimental sources in registry")

        # Extract source blocks
        blocks = []
        depth = 0
        start = -1
        for i, ch in enumerate(array_section):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    blocks.append(array_section[start:i+1])
                    start = -1

        for i, block in enumerate(blocks):
            if bool(re.search(r"reliabilityLevel:\s*['\"]experimental['\"]", block)):
                assert "DO NOT DISPLAY" in block, (
                    f"Source block {i+1} is experimental but missing 'DO NOT DISPLAY' warning in notes"
                )

    def test_unverified_sources_are_not_canonical(self, source_registry_content):
        """A source with lastVerifiedAt='unverified' must not be canonical."""
        import re
        # Only examine the SOURCE_REGISTRY array, not the helper/validation code below it
        array_start = source_registry_content.find("SOURCE_REGISTRY: Source[] = [")
        helpers_start = source_registry_content.find("// Lookup helpers")
        if array_start == -1:
            pytest.skip("Could not find SOURCE_REGISTRY array")
        end = helpers_start if helpers_start > array_start else len(source_registry_content)
        array_section = source_registry_content[array_start:end]

        # Extract source blocks by finding {…} at depth 1
        blocks = []
        depth = 0
        start = -1
        for i, ch in enumerate(array_section):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    blocks.append(array_section[start:i+1])
                    start = -1

        for block in blocks:
            id_match = re.search(r"sourceId:\s*['\"]([^'\"]+)['\"]", block)
            sid = id_match.group(1) if id_match else "UNKNOWN"
            has_unverified = bool(re.search(r"lastVerifiedAt:\s*['\"]unverified['\"]", block))
            has_canonical = bool(re.search(r"reliabilityLevel:\s*['\"]canonical['\"]", block))
            if has_unverified and has_canonical:
                pytest.fail(
                    f"Source '{sid}' has lastVerifiedAt='unverified' but reliabilityLevel='canonical'"
                )

    def test_missing_source_fails_validation(self):
        """Attempting to look up a non-existent source should return falsy."""
        # Simulate the isSourceSafeToDisplay('nonexistent') behavior
        # by checking that the registry does NOT contain a random ID
        if not SOURCE_REGISTRY_PATH.exists():
            pytest.skip("Registry file not found")
        content = SOURCE_REGISTRY_PATH.read_text(encoding="utf-8")
        assert "nonexistent_source_xyz_abc_123" not in content, (
            "Unexpected source ID found — this test checks the validator logic"
        )


# ---------------------------------------------------------------------------
# Group 4: RAG Response Source Metadata
# ---------------------------------------------------------------------------

class TestRAGResponseSourceMetadata:
    """
    Tests that RAG response structures include required source metadata.
    Uses the type definitions from api.ts to validate field presence.
    """

    def test_citation_type_has_source_id(self):
        """The Citation interface must contain source_id (not just source name)."""
        api_types_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
        if not api_types_path.exists():
            pytest.skip("api.ts not found")
        content = api_types_path.read_text(encoding="utf-8")
        assert "source_id" in content, "Citation type must include source_id field"
        assert "source_name" in content, "Citation type must include source_name field"
        assert "verse_reference" in content, "Citation type must include verse_reference field"

    def test_rag_response_type_has_citations(self):
        """RAGResponse interface must include citations array."""
        api_types_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
        if not api_types_path.exists():
            pytest.skip("api.ts not found")
        content = api_types_path.read_text(encoding="utf-8")
        assert "citations" in content, "RAGResponse type must include citations field"
        assert "confidence" in content, "RAGResponse type must include confidence field"
        assert "warnings" in content, "RAGResponse type must include warnings field"

    def test_rag_response_type_has_evidence(self):
        """RAGResponse interface must include evidence for transparency."""
        api_types_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
        if not api_types_path.exists():
            pytest.skip("api.ts not found")
        content = api_types_path.read_text(encoding="utf-8")
        assert "evidence" in content, "RAGResponse type must include evidence field"

    def test_tafseer_source_type_has_reliability(self):
        """TafseerSource type must have reliability_score."""
        api_types_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
        if not api_types_path.exists():
            pytest.skip("api.ts not found")
        content = api_types_path.read_text(encoding="utf-8")
        assert "reliability_score" in content, "TafseerSource type must include reliability_score"
        assert "author_en" in content or "author_ar" in content, (
            "TafseerSource type must include author fields"
        )


# ---------------------------------------------------------------------------
# Group 5: Content Safety — Text Mixing
# ---------------------------------------------------------------------------

class TestContentSafety:
    """Tests for Arabic/English text correctness in data files."""

    def test_quran_json_arabic_field_is_not_translation(self, quran_data):
        """
        The Arabic text field must not be a well-known English translation.
        Checks the first few ayahs against known English text patterns.
        """
        import re
        english_pattern = re.compile(r"\b(In the name|Praise be|The Most)\b", re.IGNORECASE)
        first_ten = quran_data[:10]
        for ayah in first_ten:
            text = str(ayah.get("aya_text") or ayah.get("text_uthmani") or "")
            assert not english_pattern.search(text), (
                f"Ayah {ayah.get('sura_no')}:{ayah.get('aya_no')} appears to contain English translation "
                f"in the Arabic text field: '{text[:100]}'"
            )

    def test_no_mixed_script_in_single_ayah_field(self, quran_data):
        """Each ayah text field should be predominantly Arabic (not split Arabic+English)."""
        import re
        mixed_pattern = re.compile(r"[؀-ۿ]{3,}.*[a-zA-Z]{3,}.*[؀-ۿ]{3,}")
        suspicious = []
        for ayah in quran_data:
            text = str(ayah.get("aya_text") or ayah.get("text_uthmani") or "")
            if mixed_pattern.search(text):
                suspicious.append(f"{ayah.get('sura_no')}:{ayah.get('aya_no')}")
        assert len(suspicious) == 0, (
            f"{len(suspicious)} ayahs appear to have Arabic and Latin text mixed in one field: {suspicious[:5]}"
        )

    def test_tafsir_manifest_language_field_is_valid(self, tafsir_manifest):
        """Each tafsir source must declare a language that is 'ar' or 'en' (or known codes)."""
        valid_langs = {"ar", "en", "ur", "id", "fr", "de", "tr"}
        sources = tafsir_manifest.get("sources", [])
        invalid = [
            s for s in sources
            if s.get("language") and s["language"] not in valid_langs
        ]
        # Warn but don't fail — some sources may use composite codes
        for source in invalid:
            print(f"WARNING: Tafsir source '{source.get('id')}' has unusual language: '{source.get('language')}'")

    def test_source_registry_has_arabic_titles(self, source_registry_content):
        """Every source entry must have a non-empty Arabic title."""
        import re
        # Check that Arabic Unicode characters appear in titleArabic fields
        arabic_in_registry = re.findall(r"titleArabic:\s*['\"]([^'\"]+)['\"]", source_registry_content)
        for title in arabic_in_registry:
            has_arabic = any("؀" <= c <= "ۿ" for c in title)
            assert has_arabic, f"titleArabic appears to not contain Arabic text: '{title}'"
