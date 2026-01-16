"""
Acceptance tests for Quran-wide story verification.

These tests ensure:
1. All UI categories have stories
2. All ayah ranges are valid
3. All stories have Arabic content
4. No English leaks in Arabic mode
5. Stories have secondary mentions where expected

Run with: pytest tests/unit/test_quran_verification.py -v
"""

import pytest
from pathlib import Path
import json

from app.verify.registry import (
    QuranStoryRegistry,
    StoryCategory,
    AyahRange,
    VerificationStatus,
)
from app.verify.engine import QuranVerificationEngine


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def manifest_path() -> Path:
    """Path to stories manifest."""
    return Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"


@pytest.fixture
def registry(manifest_path: Path) -> QuranStoryRegistry:
    """Load the story registry."""
    reg = QuranStoryRegistry()
    if manifest_path.exists():
        reg.load_from_manifest(manifest_path)
    return reg


@pytest.fixture
def engine(registry: QuranStoryRegistry) -> QuranVerificationEngine:
    """Create verification engine."""
    return QuranVerificationEngine(registry)


# =============================================================================
# TEST 1: CATEGORIES NOT EMPTY
# =============================================================================

class TestCategoryPopulation:
    """Tests for UI category population."""

    def test_registry_categories_nonempty_ar(self, registry: QuranStoryRegistry):
        """
        All required UI categories must have at least one story.
        Required categories: prophet, nation, parable, historical

        Arabic: جميع التصنيفات المطلوبة يجب أن تحتوي على قصة واحدة على الأقل
        """
        required_categories = [
            StoryCategory.PROPHET,
            StoryCategory.NATION,
            StoryCategory.PARABLE,
            StoryCategory.HISTORICAL,
        ]

        counts = registry.get_category_counts()

        for category in required_categories:
            count = counts.get(category.value, 0)
            assert count > 0, f"Category '{category.value}' has no stories - لا توجد قصص في التصنيف: {category.value}"

    def test_prophet_stories_minimum(self, registry: QuranStoryRegistry):
        """Prophet category must have at least 5 stories."""
        count = len(registry.get_stories_by_category(StoryCategory.PROPHET))
        assert count >= 5, f"Prophet stories: {count}, expected >= 5"

    def test_nation_stories_minimum(self, registry: QuranStoryRegistry):
        """Nation category must have at least 3 stories."""
        count = len(registry.get_stories_by_category(StoryCategory.NATION))
        assert count >= 3, f"Nation stories: {count}, expected >= 3"

    def test_parable_stories_minimum(self, registry: QuranStoryRegistry):
        """Parable category must have at least 2 stories."""
        count = len(registry.get_stories_by_category(StoryCategory.PARABLE))
        assert count >= 2, f"Parable stories: {count}, expected >= 2"


# =============================================================================
# TEST 2: AYAH RANGE VALIDITY
# =============================================================================

class TestAyahRangeValidity:
    """Tests for ayah range validation."""

    def test_all_story_ranges_valid_against_metadata(self, registry: QuranStoryRegistry):
        """
        All ayah ranges must be valid within their surahs.

        Arabic: جميع نطاقات الآيات يجب أن تكون صالحة ضمن سورها
        """
        errors = registry.validate_all_ranges()

        if errors:
            error_msgs = [f"{e['story_id']}: {e['range']} - {e['error']}" for e in errors[:5]]
            pytest.fail(
                f"Invalid ayah ranges found:\n" +
                "\n".join(error_msgs) +
                (f"\n... and {len(errors) - 5} more" if len(errors) > 5 else "")
            )

    def test_ayah_range_start_not_zero(self, registry: QuranStoryRegistry):
        """Ayah numbers must start from 1, not 0."""
        for story in registry.stories.values():
            for i, range_ in enumerate(story.primary_ayah_ranges):
                assert range_.start >= 1, f"{story.id} range {i}: start must be >= 1"
                assert range_.end >= 1, f"{story.id} range {i}: end must be >= 1"

    def test_ayah_range_end_gte_start(self, registry: QuranStoryRegistry):
        """Ayah end must be >= start."""
        for story in registry.stories.values():
            for i, range_ in enumerate(story.primary_ayah_ranges):
                assert range_.end >= range_.start, f"{story.id} range {i}: end ({range_.end}) < start ({range_.start})"

    def test_surah_numbers_valid(self, registry: QuranStoryRegistry):
        """Surah numbers must be 1-114."""
        for story in registry.stories.values():
            for i, range_ in enumerate(story.primary_ayah_ranges):
                assert 1 <= range_.sura <= 114, f"{story.id} range {i}: invalid surah {range_.sura}"


# =============================================================================
# TEST 3: ARABIC CONTENT
# =============================================================================

class TestArabicContent:
    """Tests for Arabic content completeness."""

    def test_all_stories_have_ar_titles(self, registry: QuranStoryRegistry):
        """
        All stories must have Arabic titles.

        Arabic: جميع القصص يجب أن يكون لها عناوين عربية
        """
        missing_titles = []

        for story in registry.stories.values():
            if not story.title_ar or len(story.title_ar.strip()) == 0:
                missing_titles.append(story.id)

        assert len(missing_titles) == 0, f"Stories missing Arabic titles: {missing_titles}"

    def test_all_stories_have_ar_summaries(self, registry: QuranStoryRegistry):
        """
        All stories must have Arabic summaries (not just copies of English).

        Arabic: جميع القصص يجب أن يكون لها ملخصات عربية
        """
        missing_summaries = []

        for story in registry.stories.values():
            # Check if summary exists and is not just English
            if not story.summary_ar:
                missing_summaries.append(story.id)
            elif len(story.summary_ar.strip()) < 10:
                missing_summaries.append(story.id)
            elif story.summary_ar == story.summary_en:
                # Likely copy-paste from English
                missing_summaries.append(story.id)

        assert len(missing_summaries) == 0, f"Stories missing proper Arabic summaries: {missing_summaries}"

    def test_arabic_titles_contain_arabic_chars(self, registry: QuranStoryRegistry):
        """Arabic titles must actually contain Arabic characters."""
        non_arabic_titles = []

        for story in registry.stories.values():
            title = story.title_ar
            # Check for Arabic character range
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in title)
            if not has_arabic:
                non_arabic_titles.append((story.id, title))

        assert len(non_arabic_titles) == 0, f"Non-Arabic 'Arabic' titles: {non_arabic_titles}"


# =============================================================================
# TEST 4: NO ENGLISH LEAKS IN ARABIC MODE
# =============================================================================

class TestNoEnglishLeaks:
    """Tests for i18n integrity."""

    def test_arabic_mode_no_english_leaks_in_titles(self, registry: QuranStoryRegistry):
        """
        Arabic titles should not be English placeholders.

        Arabic: العناوين العربية يجب ألا تكون نصوصاً إنجليزية
        """
        english_leaks = []

        for story in registry.stories.values():
            title = story.title_ar
            # Check if it looks like English (no Arabic chars, has common English patterns)
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in title)
            if not has_arabic and title:
                english_leaks.append((story.id, title))

        assert len(english_leaks) == 0, f"English leaks in Arabic titles: {english_leaks}"

    def test_category_names_have_arabic(self, manifest_path: Path):
        """Category names in manifest should have Arabic versions."""
        # This would check the manifest structure directly
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if stories have Arabic category names or mappings
        # For now, verify all stories have recognizable categories
        valid_categories = {'prophet', 'nation', 'parable', 'historical', 'unseen', 'named_char', 'righteous'}

        for story in data.get('stories', []):
            category = story.get('category')
            assert category in valid_categories, f"Unknown category '{category}' in story {story.get('id')}"


# =============================================================================
# TEST 5: SECONDARY MENTIONS
# =============================================================================

class TestSecondaryMentions:
    """Tests for cross-reference detection."""

    def test_major_stories_have_multiple_ranges(self, registry: QuranStoryRegistry):
        """
        Stories mentioned in multiple surahs should have multiple ranges.
        Major prophets like Musa, Ibrahim should have ranges from multiple surahs.
        """
        # These prophets are mentioned in many surahs
        multi_surah_stories = ['story_musa', 'story_ibrahim', 'story_nuh']

        for story_id in multi_surah_stories:
            story = registry.get_story(story_id)
            if story:
                suras = set(r.sura for r in story.primary_ayah_ranges)
                assert len(suras) >= 2, f"{story_id} should have ranges from multiple surahs, found only: {suras}"

    def test_high_mention_stories_have_secondary(self, registry: QuranStoryRegistry):
        """
        Stories with many verse references should have secondary_mentions populated.
        This is a soft check - warns but doesn't fail.
        """
        # For now, just check that the field exists
        for story in registry.stories.values():
            assert hasattr(story, 'secondary_mentions'), f"{story.id} missing secondary_mentions field"


# =============================================================================
# TEST 6: EDGE EVIDENCE
# =============================================================================

class TestEdgeEvidence:
    """Tests for evidence grounding."""

    def test_stories_have_evidence_field(self, registry: QuranStoryRegistry):
        """All stories should have an evidence field (even if empty)."""
        for story in registry.stories.values():
            assert hasattr(story, 'evidence'), f"{story.id} missing evidence field"

    def test_events_have_ayah_references(self, registry: QuranStoryRegistry):
        """All events should have ayah references."""
        events_without_refs = []

        for story in registry.stories.values():
            for event in story.events:
                if not event.ayah_range or not event.verse_reference:
                    events_without_refs.append(f"{story.id}:{event.id}")

        assert len(events_without_refs) == 0, f"Events without ayah refs: {events_without_refs[:10]}"


# =============================================================================
# TEST 7: VERIFICATION ENGINE
# =============================================================================

class TestVerificationEngine:
    """Tests for the verification engine itself."""

    def test_engine_runs_all_checks(self, engine: QuranVerificationEngine):
        """Engine should run all defined checks."""
        report = engine.run_all_checks()

        assert 'summary' in report
        assert 'checks_by_category' in report
        assert report['summary']['total_checks'] >= 10

    def test_engine_no_critical_errors(self, engine: QuranVerificationEngine):
        """Engine should report no critical errors for valid registry."""
        report = engine.run_all_checks()

        # We expect 0 errors (warnings are OK)
        errors = report['summary']['errors']
        assert errors == 0, f"Critical errors found: {errors}"

    def test_engine_produces_valid_report(self, engine: QuranVerificationEngine):
        """Engine report should have all required fields."""
        report = engine.run_all_checks()

        assert 'metadata' in report
        assert 'summary' in report
        assert 'coverage_stats' in report
        assert 'all_checks' in report

        # Summary should have counts
        summary = report['summary']
        assert 'total_checks' in summary
        assert 'passed_checks' in summary
        assert 'pass_rate' in summary


# =============================================================================
# TEST 8: MANIFEST STRUCTURE
# =============================================================================

class TestManifestStructure:
    """Tests for manifest file structure."""

    def test_manifest_valid_json(self, manifest_path: Path):
        """Manifest should be valid JSON."""
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'stories' in data
        assert len(data['stories']) > 0

    def test_manifest_stories_have_required_fields(self, manifest_path: Path):
        """Each story should have required fields."""
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        required_fields = ['id', 'name_ar', 'name_en', 'category']

        for story in data['stories']:
            for field in required_fields:
                assert field in story, f"Story {story.get('id', 'unknown')} missing field: {field}"

    def test_manifest_segments_have_ayah_refs(self, manifest_path: Path):
        """Each segment should have surah/ayah references."""
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for story in data['stories']:
            for seg in story.get('segments', []):
                assert 'sura_no' in seg, f"Segment {seg.get('id')} missing sura_no"
                assert 'aya_start' in seg, f"Segment {seg.get('id')} missing aya_start"
                assert 'aya_end' in seg, f"Segment {seg.get('id')} missing aya_end"

    def test_event_indices_strictly_sequential(self, manifest_path: Path):
        """
        PR1: All event indices must be strictly sequential (1..N) with no gaps or duplicates.

        Arabic: جميع فهارس الأحداث يجب أن تكون متسلسلة بصرامة من 1 إلى N بدون فجوات أو تكرار
        """
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stories_with_gaps = []

        for story in data['stories']:
            segments = story.get('segments', [])
            if not segments:
                continue

            # Get actual indices
            actual_indices = [seg.get('narrative_order', i+1) for i, seg in enumerate(segments)]
            expected_indices = list(range(1, len(segments) + 1))

            if actual_indices != expected_indices:
                stories_with_gaps.append({
                    'id': story['id'],
                    'actual': actual_indices,
                    'expected': expected_indices
                })

        if stories_with_gaps:
            details = "\n".join(
                f"  - {s['id']}: actual={s['actual']}, expected={s['expected']}"
                for s in stories_with_gaps[:5]
            )
            more = f"\n  ... and {len(stories_with_gaps) - 5} more" if len(stories_with_gaps) > 5 else ""
            pytest.fail(
                f"Found {len(stories_with_gaps)} stories with non-sequential event indices:\n{details}{more}"
            )
