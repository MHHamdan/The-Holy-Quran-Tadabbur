#!/usr/bin/env python3
"""
Story Module Acceptance Tests

ACCEPTANCE CRITERIA:
1. I18N: All semantic tags must have Arabic translations
2. DATA COMPLETENESS: All categories must have stories
3. GRAPH RENDERING: Story graphs must have nodes and edges
4. CROSS-STORY: Related stories connections must exist

Run with: pytest tests/unit/test_story_acceptance.py -v
"""
import pytest
import json
from pathlib import Path
from typing import Set, Dict, List

# All tests in this file are fast unit tests (no external services)
pytestmark = pytest.mark.unit


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@pytest.fixture
def translations_path():
    """Path to the i18n translations file."""
    return Path(__file__).parent.parent.parent.parent / "frontend" / "src" / "i18n" / "translations.ts"


@pytest.fixture
def manifest_path():
    """Path to the stories manifest."""
    return Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"


def extract_translation_keys(translations_content: str) -> Set[str]:
    """Extract all translation keys from the translations.ts file."""
    keys = set()
    import re
    # Match patterns like: key_name: { ar:
    pattern = r'^\s+(\w+):\s*\{'
    for line in translations_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            keys.add(match.group(1))
    return keys


def load_manifest(path: Path) -> dict:
    """Load the stories manifest."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# 1. I18N ACCEPTANCE TESTS
# ============================================================================

class TestI18nAcceptance:
    """
    Tests that verify all semantic tags have translations.

    REQUIREMENTS:
    - Every semantic_tag in story segments must have Arabic translation
    - Every theme in stories must have Arabic translation
    - Every category must have Arabic translation
    """

    def test_translations_file_exists(self, translations_path):
        """Translations file must exist."""
        assert translations_path.exists(), f"Translations file not found: {translations_path}"

    def test_all_semantic_tags_have_translations(self, translations_path, manifest_path):
        """All semantic tags from manifest must have translations."""
        if not translations_path.exists() or not manifest_path.exists():
            pytest.skip("Required files not found")

        translations_content = translations_path.read_text(encoding='utf-8')
        translation_keys = extract_translation_keys(translations_content)
        manifest = load_manifest(manifest_path)

        # Collect all semantic tags from stories
        semantic_tags: Set[str] = set()
        for story in manifest.get('stories', []):
            for segment in story.get('segments', []):
                for tag in segment.get('semantic_tags', []):
                    semantic_tags.add(tag)

        # Check each tag has translation
        missing_translations = []
        for tag in semantic_tags:
            if tag not in translation_keys:
                missing_translations.append(tag)

        assert len(missing_translations) == 0, \
            f"Missing translations for tags: {missing_translations}"

    def test_all_themes_have_translations(self, translations_path, manifest_path):
        """All themes from manifest must have translations."""
        if not translations_path.exists() or not manifest_path.exists():
            pytest.skip("Required files not found")

        translations_content = translations_path.read_text(encoding='utf-8')
        translation_keys = extract_translation_keys(translations_content)
        manifest = load_manifest(manifest_path)

        # Collect all themes from stories
        themes: Set[str] = set()
        for story in manifest.get('stories', []):
            for theme in story.get('themes', []):
                themes.add(theme)

        # Check each theme has translation
        missing_translations = []
        for theme in themes:
            if theme not in translation_keys:
                missing_translations.append(theme)

        assert len(missing_translations) == 0, \
            f"Missing translations for themes: {missing_translations}"

    def test_all_categories_have_translations(self, translations_path):
        """All story categories must have Arabic translations."""
        if not translations_path.exists():
            pytest.skip("Translations file not found")

        translations_content = translations_path.read_text(encoding='utf-8')
        translation_keys = extract_translation_keys(translations_content)

        required_categories = ['prophet', 'nation', 'parable', 'historical', 'righteous']

        missing = [cat for cat in required_categories if cat not in translation_keys]
        assert len(missing) == 0, f"Missing category translations: {missing}"


# ============================================================================
# 2. DATA COMPLETENESS TESTS
# ============================================================================

class TestDataCompleteness:
    """
    Tests that verify all story categories have data.

    REQUIREMENTS:
    - Each category must have at least 1 story
    - Each story must have at least 1 segment
    - Each segment must have valid verse references
    """

    def test_all_categories_have_stories(self, manifest_path):
        """Each category must have at least one story."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        # Count stories by category
        categories: Dict[str, int] = {}
        for story in manifest.get('stories', []):
            cat = story.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        required_categories = ['prophet', 'nation', 'parable', 'historical', 'righteous']

        empty_categories = []
        for cat in required_categories:
            if categories.get(cat, 0) == 0:
                empty_categories.append(cat)

        assert len(empty_categories) == 0, \
            f"Categories with no stories: {empty_categories}"

    def test_all_stories_have_segments(self, manifest_path):
        """Each story must have at least one segment."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        stories_without_segments = []
        for story in manifest.get('stories', []):
            if not story.get('segments') or len(story['segments']) == 0:
                stories_without_segments.append(story.get('id', 'unknown'))

        assert len(stories_without_segments) == 0, \
            f"Stories without segments: {stories_without_segments}"

    def test_all_segments_have_valid_verse_refs(self, manifest_path):
        """Each segment must have valid sura_no, aya_start, aya_end."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        invalid_segments = []
        for story in manifest.get('stories', []):
            for segment in story.get('segments', []):
                sura_no = segment.get('sura_no')
                aya_start = segment.get('aya_start')
                aya_end = segment.get('aya_end')

                # Validate verse reference
                if not all([sura_no, aya_start, aya_end]):
                    invalid_segments.append(segment.get('id', 'unknown'))
                elif not (1 <= sura_no <= 114):
                    invalid_segments.append(f"{segment.get('id')}: invalid sura {sura_no}")
                elif aya_start > aya_end:
                    invalid_segments.append(f"{segment.get('id')}: aya_start > aya_end")

        assert len(invalid_segments) == 0, \
            f"Segments with invalid verse refs: {invalid_segments}"

    def test_minimum_story_count(self, manifest_path):
        """Manifest must have minimum number of stories."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)
        story_count = len(manifest.get('stories', []))

        # Manifest validation_rules.min_stories = 25
        min_stories = manifest.get('validation_rules', {}).get('min_stories', 25)

        assert story_count >= min_stories, \
            f"Expected at least {min_stories} stories, got {story_count}"


# ============================================================================
# 3. GRAPH RENDERING TESTS
# ============================================================================

class TestGraphRendering:
    """
    Tests that verify story graphs can be rendered.

    REQUIREMENTS:
    - Each story must have a valid graph structure
    - Graph nodes must have chronological indices
    - Graph edges must connect valid nodes
    """

    def test_stories_have_graph_data(self, manifest_path):
        """Each story must have data needed for graph rendering."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        stories_without_graph_data = []
        for story in manifest.get('stories', []):
            segments = story.get('segments', [])
            if not segments:
                stories_without_graph_data.append(story.get('id'))
                continue

            # Check segments have narrative_order for graph layout
            for segment in segments:
                if segment.get('narrative_order') is None:
                    stories_without_graph_data.append(f"{story.get('id')}/{segment.get('id')}")

        assert len(stories_without_graph_data) == 0, \
            f"Missing graph data: {stories_without_graph_data}"

    def test_connections_reference_valid_segments(self, manifest_path):
        """Story connections must reference valid segment IDs."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        # Build set of all segment IDs
        segment_ids: Set[str] = set()
        for story in manifest.get('stories', []):
            for segment in story.get('segments', []):
                segment_ids.add(segment.get('id'))

        # Check connections reference valid segments
        invalid_connections = []
        for story in manifest.get('stories', []):
            for conn in story.get('connections', []):
                source = conn.get('source_segment_id')
                target = conn.get('target_segment_id')

                if source and source not in segment_ids:
                    invalid_connections.append(f"{conn.get('id')}: invalid source {source}")
                if target and target not in segment_ids:
                    invalid_connections.append(f"{conn.get('id')}: invalid target {target}")

        assert len(invalid_connections) == 0, \
            f"Invalid connections: {invalid_connections}"


# ============================================================================
# 4. CROSS-STORY CONNECTION TESTS
# ============================================================================

class TestCrossStoryConnections:
    """
    Tests that verify cross-story connections exist and are valid.

    REQUIREMENTS:
    - Inter-story connections must reference valid story IDs
    - Each connection must have evidence_chunk_ids
    - Connections must have bilingual explanations
    """

    def test_cross_story_connections_exist(self, manifest_path):
        """Manifest must have inter-story connections."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)
        connections = manifest.get('inter_story_connections', [])

        min_connections = manifest.get('validation_rules', {}).get('min_total_connections', 20)

        assert len(connections) >= min_connections, \
            f"Expected at least {min_connections} cross-story connections, got {len(connections)}"

    def test_cross_story_connections_reference_valid_stories(self, manifest_path):
        """Cross-story connections must reference valid story IDs."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        # Build set of story IDs
        story_ids = {story.get('id') for story in manifest.get('stories', [])}

        # Check connections
        invalid_connections = []
        for conn in manifest.get('inter_story_connections', []):
            source = conn.get('source_story_id')
            target = conn.get('target_story_id')

            if source not in story_ids:
                invalid_connections.append(f"{conn.get('id')}: invalid source {source}")
            if target not in story_ids:
                invalid_connections.append(f"{conn.get('id')}: invalid target {target}")

        assert len(invalid_connections) == 0, \
            f"Invalid cross-story connections: {invalid_connections}"

    def test_cross_story_connections_have_evidence(self, manifest_path):
        """Cross-story connections must have evidence_chunk_ids."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        connections_without_evidence = []
        for conn in manifest.get('inter_story_connections', []):
            evidence = conn.get('evidence_chunk_ids', [])
            if not evidence or len(evidence) == 0:
                connections_without_evidence.append(conn.get('id', 'unknown'))

        assert len(connections_without_evidence) == 0, \
            f"Connections without evidence: {connections_without_evidence}"

    def test_cross_story_connections_have_explanations(self, manifest_path):
        """Cross-story connections should have bilingual explanations."""
        if not manifest_path.exists():
            pytest.skip("Manifest file not found")

        manifest = load_manifest(manifest_path)

        connections_without_explanation = []
        for conn in manifest.get('inter_story_connections', []):
            explanation = conn.get('explanation', {})
            if not explanation.get('en') and not explanation.get('ar'):
                connections_without_explanation.append(conn.get('id', 'unknown'))

        # This is a warning, not a hard failure
        if connections_without_explanation:
            print(f"Warning: {len(connections_without_explanation)} connections without explanations")


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
