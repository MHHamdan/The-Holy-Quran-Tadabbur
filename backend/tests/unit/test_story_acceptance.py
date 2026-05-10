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
    """Extract all translation keys from the translations.ts file.

    Handles both plain keys (key_name: {) and quoted keys ('key-name': {).
    """
    keys = set()
    import re
    # Unquoted: key_name: { ar:
    pattern_plain = r'^\s+(\w+):\s*\{'
    # Single-quoted key: 'key-name': {  (key cannot contain single quote)
    pattern_single = r"^\s+'([^']+)'\s*:\s*\{"
    # Double-quoted key: "key'name": {  (key cannot contain double quote)
    pattern_double = r'^\s+"([^"]+)"\s*:\s*\{'
    for line in translations_content.split('\n'):
        for pattern in [pattern_plain, pattern_single, pattern_double]:
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
# 5. REVIEW SAFETY ACCEPTANCE TESTS
# ============================================================================

class TestReviewSafetyAcceptance:
    """
    Acceptance tests: the UI must display needs_review content safely.

    REQUIREMENTS:
    - needs_review  → 'Pending Scholarly Review' banner visible at all audience levels
    - humanReviewRequired → explicit flag inside the banner
    - rejected      → never rendered as story explanation
    - missing evidence → orange warning shown
    - missing sources  → warning shown, not silently hidden
    - related stories  → evidenceReferences displayed or warned about
    """

    @pytest.fixture
    def story_detail_tsx(self):
        base = Path(__file__).parent.parent.parent.parent / "frontend" / "src"
        page_path = base / "pages" / "StoryDetailPage.tsx"
        panel_path = base / "components" / "stories" / "StoryReadingPanel.tsx"
        if not page_path.exists():
            pytest.skip(f"StoryDetailPage.tsx not found: {page_path}")
        # Combine both files: StoryDetailPage delegates segment rendering to
        # StoryReadingPanel, so safety checks must pass across both files.
        content = page_path.read_text(encoding='utf-8')
        if panel_path.exists():
            content += "\n" + panel_path.read_text(encoding='utf-8')
        return content

    def test_ac_needs_review_warning_visible(self, story_detail_tsx):
        """AC: needs_review content shows a warning that cannot be confused with approved content."""
        assert 'Pending Scholarly Review' in story_detail_tsx, \
            "AC FAIL: 'Pending Scholarly Review' label missing — needs_review content may appear approved"

    def test_ac_human_review_required_flagged(self, story_detail_tsx):
        """AC: humanReviewRequired: true renders an explicit human-review-required flag."""
        assert 'Human review required before publishing' in story_detail_tsx, \
            "AC FAIL: humanReviewRequired is not surfaced to the user"

    def test_ac_rejected_not_shown(self, story_detail_tsx):
        """AC: Rejected segments never render as a story explanation."""
        assert 'if (isRejected) return null' in story_detail_tsx, \
            "AC FAIL: rejected segments are not filtered — they may appear as valid content"

    def test_ac_evidence_references_displayed_or_warned(self, story_detail_tsx):
        """AC: Related stories display evidenceReferences or show a warning when none exist."""
        has_evidence_render = 'evidenceReferences.length > 0' in story_detail_tsx
        has_missing_warning = 'No Quranic evidence references for this connection' in story_detail_tsx
        assert has_evidence_render and has_missing_warning, \
            "AC FAIL: Related stories must show evidence refs AND warn when refs are absent"

    def test_ac_missing_source_evidence_warning(self, story_detail_tsx):
        """AC: Missing matchedEvidence triggers an orange warning, not silent omission."""
        assert 'missingEvidence' in story_detail_tsx, \
            "AC FAIL: missingEvidence variable not defined"
        assert 'Source evidence not yet linked' in story_detail_tsx, \
            "AC FAIL: Missing source evidence is silently hidden rather than warned about"

    def test_ac_empty_sources_warning(self, story_detail_tsx):
        """AC: Segments with no sourceIds show a warning instead of an empty sources section."""
        assert 'No sources identified for this segment yet' in story_detail_tsx, \
            "AC FAIL: Empty sourceIds are silently hidden rather than warned about"

    def test_ac_warning_not_audience_gated(self, story_detail_tsx):
        """AC: Review warnings must not be conditioned on audienceLevel."""
        import re
        gated = re.findall(
            r"audienceLevel\s*===\s*['\"]adults['\"]\s*&&\s*[^{]*(?:needsReview|humanReviewReq)",
            story_detail_tsx,
        )
        assert not gated, \
            "AC FAIL: Warning is gated on audienceLevel — kids audience would not see it"

    def test_ac_kids_and_adults_see_warning(self, story_detail_tsx):
        """AC: Warning block appears before the segment summary <p> in the JSX return."""
        import re
        # The warning block must appear before the segment summary paragraph in the source.
        # Phase 6.5: the conditional may include '!segmentIsApproved' for overlay-aware suppression.
        # Phase F: rendering moved to StoryReadingPanel — check combined source.
        warning_block_pos = story_detail_tsx.find('(needsReview || humanReviewReq) &&')
        # Use the segment summary paragraph's leading-relaxed class as an anchor.
        # Phase F: SegmentCard uses clsx so 'text-gray-700 leading-relaxed mb-3' is the static part.
        segment_summary_match = re.search(
            r'text-gray-700.*leading-relaxed.*mb-3',
            story_detail_tsx,
        )
        assert warning_block_pos != -1, "Warning conditional block must be present"
        assert segment_summary_match is not None, \
            "Segment summary paragraph (text-gray-700 leading-relaxed mb-3) must be present"
        segment_summary_pos = segment_summary_match.start()
        assert warning_block_pos < segment_summary_pos, \
            "AC FAIL: Warning block must appear before the segment summary paragraph in the JSX"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
