#!/usr/bin/env python3
"""
Theme i18n Completeness Tests

Validates that theme_labels.json (the single source of truth) has complete
Arabic and English labels for all themes.

This test uses the shared theme_labels.json file rather than parsing
frontend translation files directly.

Run with: pytest tests/unit/test_theme_i18n.py -v
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Set
import re

pytestmark = pytest.mark.unit


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def theme_labels_path():
    """Path to the shared theme labels file."""
    return Path(__file__).parent.parent.parent / "app" / "data" / "themes" / "theme_labels.json"


@pytest.fixture
def theme_labels(theme_labels_path) -> Dict:
    """Load theme labels from JSON."""
    if not theme_labels_path.exists():
        pytest.skip(f"Theme labels file not found: {theme_labels_path}")

    with open(theme_labels_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('labels', {})


@pytest.fixture
def manifest_path():
    """Path to the stories manifest."""
    return Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"


# ============================================================================
# Core Acceptance Tests
# ============================================================================

class TestThemeLabelCompleteness:
    """Tests ensuring all themes have complete translations in shared labels file."""

    def test_labels_file_exists(self, theme_labels_path):
        """The theme_labels.json file must exist."""
        assert theme_labels_path.exists(), f"Missing theme labels file: {theme_labels_path}"

    def test_labels_file_valid_json(self, theme_labels_path):
        """The theme_labels.json file must be valid JSON."""
        with open(theme_labels_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # Raises JSONDecodeError if invalid

        assert 'labels' in data, "Missing 'labels' key in theme_labels.json"
        assert isinstance(data['labels'], dict), "'labels' must be an object"

    def test_all_themes_have_ar_and_en(self, theme_labels):
        """
        Every theme must have both Arabic and English translations.

        This test prevents:
        - Missing translations showing as theme_id in UI
        - Placeholder text appearing to users
        - Arabic users seeing English-only labels
        """
        missing_arabic = []
        missing_english = []

        for theme_id, label in theme_labels.items():
            ar_label = label.get('title_ar', '')
            en_label = label.get('title_en', '')

            if not ar_label or not ar_label.strip():
                missing_arabic.append(theme_id)
            if not en_label or not en_label.strip():
                missing_english.append(theme_id)

        errors = []
        if missing_arabic:
            errors.append(f"Themes missing Arabic labels: {missing_arabic}")
        if missing_english:
            errors.append(f"Themes missing English labels: {missing_english}")

        assert len(errors) == 0, "\n".join(errors)

    def test_all_themes_have_required_fields(self, theme_labels):
        """Every theme must have all required fields."""
        required_fields = ['title_ar', 'title_en', 'category', 'slug']
        missing_fields = []

        for theme_id, label in theme_labels.items():
            for field in required_fields:
                if field not in label or not label[field]:
                    missing_fields.append(f"{theme_id}: missing '{field}'")

        assert len(missing_fields) == 0, \
            f"Missing required fields:\n" + "\n".join(missing_fields)

    def test_theme_arabic_labels_contain_arabic(self, theme_labels):
        """Arabic labels must actually contain Arabic characters."""
        non_arabic_labels = []
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for theme_id, label in theme_labels.items():
            ar_label = label.get('title_ar', '')
            if ar_label and not arabic_pattern.search(ar_label):
                non_arabic_labels.append(f"{theme_id}: '{ar_label}'")

        assert len(non_arabic_labels) == 0, \
            f"Arabic labels without Arabic characters: {non_arabic_labels}"

    def test_theme_labels_not_placeholders(self, theme_labels):
        """Theme labels must not be placeholder text."""
        placeholder_patterns = [
            r'^TODO',
            r'^FIXME',
            r'^\[.*\]$',  # [placeholder]
            r'^TBD',
            r'^N/A',
            r'^missing',
        ]

        placeholders_found = []

        for theme_id, label in theme_labels.items():
            for lang_key in ['title_ar', 'title_en']:
                label_text = label.get(lang_key, '')
                for pattern in placeholder_patterns:
                    if re.match(pattern, label_text, re.IGNORECASE):
                        placeholders_found.append(f"{theme_id}.{lang_key}: '{label_text}'")

        assert len(placeholders_found) == 0, \
            f"Placeholder text found in theme labels: {placeholders_found}"

    def test_theme_ids_follow_convention(self, theme_labels):
        """All theme IDs must start with 'theme_'."""
        invalid_ids = []

        for theme_id in theme_labels.keys():
            if not theme_id.startswith('theme_'):
                invalid_ids.append(theme_id)

        assert len(invalid_ids) == 0, \
            f"Invalid theme ID format (should start with 'theme_'): {invalid_ids}"

    def test_categories_are_valid(self, theme_labels):
        """All categories must be from the valid set."""
        valid_categories = {
            'aqidah', 'iman', 'ibadat',
            'akhlaq_fardi', 'akhlaq_ijtima',
            'muharramat', 'sunan_ilahiyyah',
        }

        invalid_categories = []

        for theme_id, label in theme_labels.items():
            category = label.get('category', '')
            if category not in valid_categories:
                invalid_categories.append(f"{theme_id}: '{category}'")

        assert len(invalid_categories) == 0, \
            f"Invalid categories: {invalid_categories}"


class TestThemeLabelQuality:
    """Tests for translation quality standards."""

    def test_arabic_labels_are_substantive(self, theme_labels):
        """Arabic labels should be substantive (not just transliteration)."""
        short_labels = []

        for theme_id, label in theme_labels.items():
            ar_label = label.get('title_ar', '')
            # Arabic labels should typically be at least 2 characters
            if ar_label and len(ar_label.strip()) < 2:
                short_labels.append(f"{theme_id}: '{ar_label}'")

        assert len(short_labels) == 0, \
            f"Arabic labels too short (possibly incomplete): {short_labels}"

    def test_minimum_theme_count(self, theme_labels):
        """There should be a minimum number of themes defined."""
        MIN_THEMES = 40  # We expect at least 40 themes

        assert len(theme_labels) >= MIN_THEMES, \
            f"Only {len(theme_labels)} themes defined, expected at least {MIN_THEMES}"

    def test_all_categories_represented(self, theme_labels):
        """All expected categories should have at least one theme."""
        expected_categories = {
            'aqidah', 'iman', 'ibadat',
            'akhlaq_fardi', 'akhlaq_ijtima',
            'muharramat', 'sunan_ilahiyyah',
        }

        present_categories = set()
        for label in theme_labels.values():
            present_categories.add(label.get('category', ''))

        missing = expected_categories - present_categories

        assert len(missing) == 0, \
            f"Missing themes in categories: {missing}"
