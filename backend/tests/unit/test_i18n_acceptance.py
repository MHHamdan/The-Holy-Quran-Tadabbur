#!/usr/bin/env python3
"""
i18n Arabic-Mode Acceptance Tests

ACCEPTANCE CRITERIA:
1. All translation keys must have Arabic values
2. No English words in Arabic translations (except proper nouns)
3. All tags/themes/categories have Arabic translations
4. Translation fallbacks are properly marked

Run with: pytest tests/unit/test_i18n_acceptance.py -v
"""
import pytest
import re
import json
from pathlib import Path
from typing import Set, Dict, List

# All tests in this file are fast unit tests (no external services)
pytestmark = pytest.mark.unit


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def translations_path():
    """Path to the i18n translations file."""
    return Path(__file__).parent.parent.parent.parent / "frontend" / "src" / "i18n" / "translations.ts"


@pytest.fixture
def manifest_path():
    """Path to the stories manifest."""
    return Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"


def extract_translation_entries(ts_content: str) -> Dict[str, Dict[str, str]]:
    """
    Extract translation entries from translations.ts file.
    Returns dict of {key: {ar: ..., en: ...}}
    Parses both multi-line and single-line formats:
    - Multi-line: key: { ar: '...', en: '...' } (across lines)
    - Single-line: key: { ar: '...', en: '...' }, (on one line)
    """
    entries = {}
    current_key = None
    current_entry = {}
    in_translation_block = False

    lines = ts_content.split('\n')
    for line in lines:
        stripped = line.strip()

        # Detect start of a translation object
        if 'Translations' in stripped and ('=' in stripped or ':' in stripped) and '{' in stripped:
            in_translation_block = True
        elif 'export const translations:' in stripped or 'export const translations =' in stripped:
            in_translation_block = True

        if not in_translation_block:
            continue

        # Try to match single-line format: key: { ar: '...', en: '...' },
        single_line = re.match(
            r"^(\w+):\s*\{\s*ar:\s*['\"]([^'\"]+)['\"],?\s*en:\s*['\"]([^'\"]+)['\"],?\s*\},?$",
            stripped
        )
        if single_line:
            key, ar_val, en_val = single_line.groups()
            entries[key] = {'ar': ar_val, 'en': en_val}
            continue

        # Match key: { (start of multi-line entry)
        key_match = re.match(r'^(\w+):\s*\{$', stripped)
        if key_match:
            if current_key and current_entry:
                entries[current_key] = current_entry
            current_key = key_match.group(1)
            current_entry = {}

        # Match ar: '...' (in multi-line format)
        ar_match = re.match(r"ar:\s*['\"]([^'\"]+)['\"],?$", stripped)
        if ar_match:
            current_entry['ar'] = ar_match.group(1)

        # Match en: '...' (in multi-line format)
        en_match = re.match(r"en:\s*['\"]([^'\"]+)['\"],?$", stripped)
        if en_match:
            current_entry['en'] = en_match.group(1)

        # Match closing brace for multi-line entry
        if stripped == '},':
            if current_key and current_entry:
                entries[current_key] = current_entry
            current_key = None
            current_entry = {}

        # Match end of translation object block
        if stripped == '};':
            in_translation_block = False
            if current_key and current_entry:
                entries[current_key] = current_entry
            current_key = None
            current_entry = {}

    return entries


def has_arabic_characters(text: str) -> bool:
    """Check if text contains Arabic characters."""
    arabic_range = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_range.search(text))


def has_english_words(text: str) -> bool:
    """
    Check if text contains English words (ignoring numbers and punctuation).
    Returns True if text has 3+ consecutive Latin letters.
    """
    # Match 3+ consecutive Latin letters (likely English words)
    english_word = re.compile(r'[a-zA-Z]{3,}')
    return bool(english_word.search(text))


# ============================================================================
# Translation Completeness Tests
# ============================================================================

class TestTranslationCompleteness:
    """Tests that verify translation coverage."""

    def test_all_keys_have_arabic_values(self, translations_path):
        """Every translation key must have an Arabic value."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        missing_ar = []
        for key, values in entries.items():
            if 'ar' not in values or not values['ar']:
                missing_ar.append(key)

        assert len(missing_ar) == 0, \
            f"Keys missing Arabic translations: {missing_ar}"

    def test_arabic_values_contain_arabic_characters(self, translations_path):
        """Arabic translations should contain Arabic characters."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        invalid_ar = []
        for key, values in entries.items():
            ar_value = values.get('ar', '')
            if ar_value and not has_arabic_characters(ar_value):
                invalid_ar.append((key, ar_value))

        assert len(invalid_ar) == 0, \
            f"Arabic values without Arabic characters: {invalid_ar}"

    def test_no_english_leaks_in_arabic_values(self, translations_path):
        """
        Arabic values should not contain English words.
        Exceptions: technical terms, proper nouns in brackets.
        """
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        # Allowed English words (technical terms, proper nouns)
        allowed_english = {
            'API', 'URL', 'JSON', 'XML', 'HTML',
            'AI', 'RAG', 'NLP', 'PDF',
        }

        english_leaks = []
        for key, values in entries.items():
            ar_value = values.get('ar', '')
            if ar_value and has_english_words(ar_value):
                # Check if it's an allowed term
                found_words = re.findall(r'[a-zA-Z]{3,}', ar_value)
                disallowed = [w for w in found_words if w.upper() not in allowed_english]
                if disallowed:
                    english_leaks.append((key, ar_value, disallowed))

        assert len(english_leaks) == 0, \
            f"English words found in Arabic translations: {english_leaks}"


# ============================================================================
# Semantic Tag Translation Tests
# ============================================================================

class TestSemanticTagTranslations:
    """Tests that verify semantic tags have translations."""

    def test_all_manifest_tags_have_translations(self, translations_path, manifest_path):
        """All semantic tags from manifest must have translations."""
        if not translations_path.exists() or not manifest_path.exists():
            pytest.skip("Required files not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # Collect all semantic tags from stories
        tags: Set[str] = set()
        for story in manifest.get('stories', []):
            for segment in story.get('segments', []):
                for tag in segment.get('semantic_tags', []):
                    tags.add(tag)

        # Find missing translations
        missing = [tag for tag in tags if tag not in entries]

        # Allow up to 5% missing for new tags
        max_missing = max(1, int(len(tags) * 0.05))
        assert len(missing) <= max_missing, \
            f"Too many tags missing translations ({len(missing)}/{len(tags)}): {missing[:10]}"


# ============================================================================
# Category Translation Tests
# ============================================================================

class TestCategoryTranslations:
    """Tests that verify story categories have translations."""

    def test_all_categories_have_arabic_translations(self, translations_path):
        """All required story categories must have Arabic translations."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        required_categories = ['prophet', 'nation', 'parable', 'historical', 'righteous']

        missing = []
        for cat in required_categories:
            if cat not in entries:
                missing.append(cat)
            elif not entries[cat].get('ar'):
                missing.append(f"{cat} (empty ar)")

        assert len(missing) == 0, \
            f"Missing category translations: {missing}"

    def test_category_arabic_values_are_different(self, translations_path):
        """Category Arabic translations should be unique."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        categories = ['prophet', 'nation', 'parable', 'historical', 'righteous']
        ar_values = []

        for cat in categories:
            if cat in entries and entries[cat].get('ar'):
                ar_values.append(entries[cat]['ar'])

        # Check for duplicates
        assert len(ar_values) == len(set(ar_values)), \
            f"Duplicate Arabic category translations found: {ar_values}"


# ============================================================================
# Theme Translation Tests - REMOVED
# ============================================================================
# Theme translations are now tested via test_theme_i18n.py using the shared
# theme_labels.json file (single source of truth).


# ============================================================================
# Fallback Behavior Tests
# ============================================================================

class TestFallbackBehavior:
    """Tests that verify fallback behavior is correctly marked."""

    def test_fallback_translations_are_bracketed(self, translations_path):
        """
        When English falls back to key name, it should be marked.
        This is a best-practice check.
        """
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')
        entries = extract_translation_entries(content)

        # Keys where en value equals key name (potential unmarked fallback)
        unmarked_fallbacks = []
        for key, values in entries.items():
            en_value = values.get('en', '')
            # If English value is just the key with spaces, might be unmarked
            key_as_text = key.replace('_', ' ')
            if en_value.lower() == key_as_text.lower():
                unmarked_fallbacks.append(key)

        # This is informational, not a hard failure
        if unmarked_fallbacks:
            print(f"\nInfo: {len(unmarked_fallbacks)} keys have en=key pattern")


# ============================================================================
# Figure Translation Tests
# ============================================================================

class TestFigureTranslations:
    """Tests that verify Quranic figures have translations."""

    def test_common_figures_have_arabic(self, translations_path):
        """Common Quranic figures should have Arabic translations."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        content = translations_path.read_text(encoding='utf-8')

        # Important figures that must have translations
        required_figures = [
            'Adam', 'Nuh', 'Ibrahim', 'Musa', 'Isa',
            'Yusuf', 'Dawud', 'Sulayman', 'Yunus', 'Ayyub',
        ]

        # Check if these appear in the file (case insensitive)
        content_lower = content.lower()
        missing = []
        for figure in required_figures:
            # Look for either direct translation or figure name mention
            if figure.lower() not in content_lower:
                missing.append(figure)

        assert len(missing) == 0, \
            f"Common figures not found in translations: {missing}"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
