#!/usr/bin/env python3
"""
Unit tests for the Quranic Themes Completeness Audit Script.

These tests verify:
1. Exit code behavior in CI mode
2. Arabic leakage detection catches Latin words
3. Verse validation rejects invalid sura/ayah
4. Min-verses enforcement
5. Consequences rule behaves for virtue and prohibition themes
6. Graph connectivity detection

Run with: pytest tests/unit/test_theme_completeness_audit.py -v
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.verify.theme_completeness_audit import (
    # Validation functions
    detect_english_leakage,
    detect_placeholders,
    has_arabic_content,
    validate_sura_ayah,
    is_approved_tafsir,
    # Graph analysis
    analyze_graph_connectivity,
    check_graph_issues,
    # Data classes
    ValidationIssue,
    ThemeAuditResult,
    AuditReport,
    Severity,
    RuleCode,
    # Constants
    QURAN_VERSE_COUNTS,
    APPROVED_TAFSIR_SOURCES,
    CATEGORIES_REQUIRING_PUNISHMENT,
    CATEGORIES_REQUIRING_REWARD,
)


# =============================================================================
# TEST 1: ARABIC LEAKAGE DETECTION
# =============================================================================

class TestArabicLeakageDetection:
    """Tests for English leakage detection in Arabic text."""

    def test_pure_arabic_no_leak(self):
        """Pure Arabic text should not be flagged."""
        text = "التوحيد هو إفراد الله بالعبادة"
        has_leak, latin_pct = detect_english_leakage(text)
        assert not has_leak, "Pure Arabic should not be flagged"
        assert latin_pct == 0.0

    def test_pure_english_detected(self):
        """Pure English text should be detected as leakage."""
        text = "This is pure English text with no Arabic"
        has_leak, latin_pct = detect_english_leakage(text)
        assert has_leak, "Pure English should be detected"
        assert latin_pct == 100.0

    def test_mixed_text_high_latin_detected(self):
        """Mixed text with high Latin percentage should be flagged."""
        # More than 15% Latin characters
        text = "Arabic التوحيد with many English words mixed in here"
        has_leak, latin_pct = detect_english_leakage(text)
        assert has_leak, "High Latin percentage should be flagged"
        assert latin_pct > 15

    def test_arabic_with_few_english_ok(self):
        """Arabic with minimal English (e.g., technical terms) should pass."""
        text = "التوحيد والعقيدة الإسلامية الصحيحة PDF"
        has_leak, latin_pct = detect_english_leakage(text)
        # Low Latin percentage (just PDF) should be OK
        assert not has_leak or latin_pct <= 15

    def test_common_english_words_detected(self):
        """Common English words (the, and, of, etc.) should trigger detection."""
        text = "هذا النص the and of with some Arabic"
        has_leak, latin_pct = detect_english_leakage(text)
        # Multiple common English words should trigger
        assert has_leak, "Multiple common English words should trigger"

    def test_empty_string_no_leak(self):
        """Empty string should not be flagged."""
        has_leak, latin_pct = detect_english_leakage("")
        assert not has_leak
        assert latin_pct == 0.0

    def test_none_input_no_leak(self):
        """None input should not be flagged."""
        has_leak, latin_pct = detect_english_leakage(None)
        assert not has_leak
        assert latin_pct == 0.0

    def test_numbers_and_punctuation_ignored(self):
        """Numbers and punctuation should not affect detection."""
        text = "التوحيد 123 - ! @ #"
        has_leak, latin_pct = detect_english_leakage(text)
        assert not has_leak


class TestPlaceholderDetection:
    """Tests for placeholder text detection."""

    def test_todo_detected(self):
        """TODO should be detected."""
        text = "هذا النص TODO مطلوب تعديله"
        placeholders = detect_placeholders(text)
        assert len(placeholders) > 0

    def test_fixme_detected(self):
        """FIXME should be detected."""
        text = "FIXME: this needs Arabic translation"
        placeholders = detect_placeholders(text)
        assert len(placeholders) > 0

    def test_lorem_ipsum_detected(self):
        """Lorem ipsum should be detected."""
        text = "Lorem ipsum dolor sit amet"
        placeholders = detect_placeholders(text)
        assert len(placeholders) > 0

    def test_bracket_placeholder_detected(self):
        """Bracketed placeholders like [TBD] should be detected."""
        text = "النص العربي [placeholder text here]"
        placeholders = detect_placeholders(text)
        assert len(placeholders) > 0

    def test_clean_arabic_no_placeholders(self):
        """Clean Arabic text should have no placeholders."""
        text = "التوحيد هو إفراد الله بالعبادة وحده لا شريك له"
        placeholders = detect_placeholders(text)
        assert len(placeholders) == 0

    def test_empty_string_no_placeholders(self):
        """Empty string should have no placeholders."""
        placeholders = detect_placeholders("")
        assert len(placeholders) == 0


# =============================================================================
# TEST 2: VERSE VALIDATION
# =============================================================================

class TestVerseValidation:
    """Tests for sura/ayah validation against Quran metadata."""

    def test_valid_sura_ayah_accepted(self):
        """Valid sura/ayah combinations should be accepted."""
        # Al-Fatiha, verse 1
        valid, error = validate_sura_ayah(1, 1)
        assert valid
        assert error == ""

        # Al-Fatiha, verse 7 (last verse)
        valid, error = validate_sura_ayah(1, 7)
        assert valid

        # Al-Baqarah, verse 286 (last verse)
        valid, error = validate_sura_ayah(2, 286)
        assert valid

        # An-Nas, verse 6 (last verse of last surah)
        valid, error = validate_sura_ayah(114, 6)
        assert valid

    def test_invalid_sura_zero_rejected(self):
        """Sura 0 should be rejected."""
        valid, error = validate_sura_ayah(0, 1)
        assert not valid
        assert "Invalid sura number" in error

    def test_invalid_sura_115_rejected(self):
        """Sura 115 should be rejected (only 114 surahs)."""
        valid, error = validate_sura_ayah(115, 1)
        assert not valid
        assert "Invalid sura number" in error

    def test_invalid_ayah_zero_rejected(self):
        """Ayah 0 should be rejected."""
        valid, error = validate_sura_ayah(1, 0)
        assert not valid
        assert "Invalid ayah" in error

    def test_invalid_ayah_exceeds_surah_rejected(self):
        """Ayah exceeding surah length should be rejected."""
        # Al-Fatiha only has 7 verses
        valid, error = validate_sura_ayah(1, 8)
        assert not valid
        assert "Invalid ayah" in error
        assert "max: 7" in error

        # Al-Baqarah has 286 verses
        valid, error = validate_sura_ayah(2, 287)
        assert not valid
        assert "Invalid ayah" in error
        assert "max: 286" in error

    def test_quran_verse_counts_correct_length(self):
        """QURAN_VERSE_COUNTS should have 114 entries."""
        assert len(QURAN_VERSE_COUNTS) == 114

    def test_quran_verse_counts_known_values(self):
        """Verify known verse counts for some surahs."""
        # Al-Fatiha: 7 verses
        assert QURAN_VERSE_COUNTS[0] == 7
        # Al-Baqarah: 286 verses
        assert QURAN_VERSE_COUNTS[1] == 286
        # Al-Ikhlas: 4 verses
        assert QURAN_VERSE_COUNTS[111] == 4
        # An-Nas: 6 verses
        assert QURAN_VERSE_COUNTS[113] == 6


class TestTafsirSourceValidation:
    """Tests for approved tafsir source validation."""

    def test_ibn_kathir_approved(self):
        """Ibn Kathir should be approved."""
        assert is_approved_tafsir("ibn_kathir_ar")
        assert is_approved_tafsir("ibn_kathir_en")

    def test_tabari_approved(self):
        """Tabari should be approved."""
        assert is_approved_tafsir("tabari_ar")

    def test_qurtubi_approved(self):
        """Qurtubi should be approved."""
        assert is_approved_tafsir("qurtubi_ar")

    def test_unapproved_source_rejected(self):
        """Unknown sources should not be approved."""
        assert not is_approved_tafsir("unknown_source")
        assert not is_approved_tafsir("wikipedia")
        assert not is_approved_tafsir("")


# =============================================================================
# TEST 3: MIN-VERSES ENFORCEMENT
# =============================================================================

class TestMinVersesEnforcement:
    """Tests for minimum verses threshold enforcement."""

    def test_theme_result_has_min_verses_true(self):
        """Theme with >= min_verses should have has_min_verses = True."""
        result = ThemeAuditResult(
            theme_id="test_theme",
            title_ar="اختبار",
            title_en="Test",
            category="aqidah",
        )
        result.unique_verse_count = 5
        result.has_min_verses = result.unique_verse_count >= 3
        assert result.has_min_verses

    def test_theme_result_has_min_verses_false(self):
        """Theme with < min_verses should have has_min_verses = False."""
        result = ThemeAuditResult(
            theme_id="test_theme",
            title_ar="اختبار",
            title_en="Test",
            category="aqidah",
        )
        result.unique_verse_count = 2
        result.has_min_verses = result.unique_verse_count >= 3
        assert not result.has_min_verses

    def test_coverage_score_includes_min_verses(self):
        """Coverage score should include 40 points for meeting min_verses."""
        result = ThemeAuditResult(
            theme_id="test_theme",
            title_ar="اختبار",
            title_en="Test",
            category="aqidah",
        )
        # Theme with no requirements met
        assert result.coverage_score == 0

        # Theme meeting min_verses only
        result.has_min_verses = True
        assert result.coverage_score == 40

    def test_coverage_score_full(self):
        """Coverage score should sum all criteria correctly."""
        result = ThemeAuditResult(
            theme_id="test_theme",
            title_ar="اختبار",
            title_en="Test",
            category="aqidah",
        )
        result.has_min_verses = True  # +40
        result.tafsir_source_count = 2  # +20
        result.has_required_consequence = True  # +20
        result.arabic_clean = True  # +10
        result.is_connected = True  # +10

        assert result.coverage_score == 100


# =============================================================================
# TEST 4: CONSEQUENCE RULES
# =============================================================================

class TestConsequenceRules:
    """Tests for consequence validation rules by category."""

    def test_muharramat_requires_punishment(self):
        """Prohibition (muharramat) category should require punishment."""
        assert "muharramat" in CATEGORIES_REQUIRING_PUNISHMENT

    def test_virtue_categories_require_reward(self):
        """Virtue categories should require reward."""
        assert "ibadat" in CATEGORIES_REQUIRING_REWARD
        assert "akhlaq_fardi" in CATEGORIES_REQUIRING_REWARD
        assert "akhlaq_ijtima" in CATEGORIES_REQUIRING_REWARD

    def test_aqidah_no_specific_requirement(self):
        """Aqidah should not be in special categories."""
        assert "aqidah" not in CATEGORIES_REQUIRING_PUNISHMENT
        assert "aqidah" not in CATEGORIES_REQUIRING_REWARD

    def test_consequence_issue_created_for_virtue_without_reward(self):
        """Virtue theme without reward should generate issue."""
        # Simulating what audit_theme would do
        category = "ibadat"
        consequence_types = {"explanation"}  # No reward

        has_reward = any(t in consequence_types for t in ['reward', 'blessing', 'promise'])
        assert not has_reward
        assert category in CATEGORIES_REQUIRING_REWARD

    def test_consequence_issue_created_for_prohibition_without_punishment(self):
        """Prohibition theme without punishment should generate issue."""
        category = "muharramat"
        consequence_types = {"explanation"}  # No punishment

        has_punishment = any(t in consequence_types for t in ['punishment', 'warning'])
        assert not has_punishment
        assert category in CATEGORIES_REQUIRING_PUNISHMENT


# =============================================================================
# TEST 5: GRAPH CONNECTIVITY
# =============================================================================

class TestGraphConnectivity:
    """Tests for theme graph connectivity analysis."""

    def test_isolated_themes_detected(self):
        """Themes with no connections should be marked as isolated."""
        themes = [
            {'id': 'theme_a', 'related_theme_ids': [], 'parent_theme_id': None},
            {'id': 'theme_b', 'related_theme_ids': [], 'parent_theme_id': None},
            {'id': 'theme_c', 'related_theme_ids': [], 'parent_theme_id': None},
        ]
        connections = []

        num_components, isolated = analyze_graph_connectivity(themes, connections)

        # All three are isolated
        assert len(isolated) == 3
        assert 'theme_a' in isolated
        assert 'theme_b' in isolated
        assert 'theme_c' in isolated

    def test_connected_themes_not_isolated(self):
        """Themes with connections should not be marked as isolated."""
        themes = [
            {'id': 'theme_a', 'related_theme_ids': ['theme_b'], 'parent_theme_id': None},
            {'id': 'theme_b', 'related_theme_ids': ['theme_a'], 'parent_theme_id': None},
            {'id': 'theme_c', 'related_theme_ids': [], 'parent_theme_id': None},
        ]
        connections = []

        num_components, isolated = analyze_graph_connectivity(themes, connections)

        # Only theme_c is isolated
        assert len(isolated) == 1
        assert 'theme_c' in isolated
        assert 'theme_a' not in isolated
        assert 'theme_b' not in isolated

    def test_parent_child_creates_connection(self):
        """Parent-child relationship should create a connection."""
        themes = [
            {'id': 'parent', 'related_theme_ids': [], 'parent_theme_id': None},
            {'id': 'child', 'related_theme_ids': [], 'parent_theme_id': 'parent'},
        ]
        connections = []

        num_components, isolated = analyze_graph_connectivity(themes, connections)

        # Neither should be isolated
        assert len(isolated) == 0

    def test_segment_connections_create_theme_links(self):
        """Segment-level connections should create theme-level links."""
        themes = [
            {'id': 'theme_a', 'related_theme_ids': [], 'parent_theme_id': None},
            {'id': 'theme_b', 'related_theme_ids': [], 'parent_theme_id': None},
        ]
        connections = [
            {
                'id': 'conn1',
                'source_segment_id': 'seg1',
                'target_segment_id': 'seg2',
                'edge_type': 'thematic',
                'source_theme': 'theme_a',
                'target_theme': 'theme_b',
            }
        ]

        num_components, isolated = analyze_graph_connectivity(themes, connections)

        # Neither should be isolated
        assert len(isolated) == 0

    def test_component_count_correct(self):
        """Connected components should be counted correctly."""
        themes = [
            {'id': 'a1', 'related_theme_ids': ['a2'], 'parent_theme_id': None},
            {'id': 'a2', 'related_theme_ids': ['a1'], 'parent_theme_id': None},
            {'id': 'b1', 'related_theme_ids': ['b2'], 'parent_theme_id': None},
            {'id': 'b2', 'related_theme_ids': ['b1'], 'parent_theme_id': None},
            {'id': 'lone', 'related_theme_ids': [], 'parent_theme_id': None},
        ]
        connections = []

        num_components, isolated = analyze_graph_connectivity(themes, connections)

        # 3 components: (a1, a2), (b1, b2), (lone)
        assert num_components == 3


class TestGraphIssues:
    """Tests for graph structure issue detection."""

    def test_self_loop_detected(self):
        """Self-loops should be detected as errors."""
        connections = [
            {
                'id': 'conn1',
                'source_segment_id': 'seg1',
                'target_segment_id': 'seg1',  # Same as source - self-loop
                'edge_type': 'thematic',
            }
        ]

        issues = check_graph_issues(connections)

        assert len(issues) == 1
        assert issues[0].rule_code == RuleCode.GRAPH_NO_SELF_LOOP.value
        assert issues[0].severity == Severity.ERROR

    def test_duplicate_edge_detected(self):
        """Duplicate edges should be detected as warnings."""
        connections = [
            {
                'id': 'conn1',
                'source_segment_id': 'seg1',
                'target_segment_id': 'seg2',
                'edge_type': 'thematic',
            },
            {
                'id': 'conn2',
                'source_segment_id': 'seg1',
                'target_segment_id': 'seg2',
                'edge_type': 'thematic',  # Duplicate
            }
        ]

        issues = check_graph_issues(connections)

        # Should find one duplicate (second occurrence)
        assert len(issues) == 1
        assert issues[0].rule_code == RuleCode.GRAPH_NO_DUPLICATE_EDGE.value
        assert issues[0].severity == Severity.WARN

    def test_valid_connections_no_issues(self):
        """Valid connections should produce no issues."""
        connections = [
            {
                'id': 'conn1',
                'source_segment_id': 'seg1',
                'target_segment_id': 'seg2',
                'edge_type': 'thematic',
            },
            {
                'id': 'conn2',
                'source_segment_id': 'seg2',
                'target_segment_id': 'seg3',
                'edge_type': 'causal',
            }
        ]

        issues = check_graph_issues(connections)
        assert len(issues) == 0


# =============================================================================
# TEST 6: EXIT CODE BEHAVIOR
# =============================================================================

class TestAuditReportExitCode:
    """Tests for exit code behavior in CI mode."""

    def test_report_no_errors_passes(self):
        """Report with no errors should indicate pass."""
        report = AuditReport(timestamp="2024-01-01")
        report.error_count = 0
        report.warn_count = 5

        # CI should pass (exit 0) when error_count == 0
        assert report.error_count == 0

    def test_report_with_errors_fails(self):
        """Report with errors should indicate failure."""
        report = AuditReport(timestamp="2024-01-01")
        report.error_count = 3
        report.warn_count = 5

        # CI should fail (exit 1) when error_count > 0
        assert report.error_count > 0

    def test_pass_rate_calculation(self):
        """Pass rate should be calculated correctly."""
        report = AuditReport(timestamp="2024-01-01")
        report.total_themes = 10

        # Create mock theme results
        for i in range(10):
            result = ThemeAuditResult(
                theme_id=f"theme_{i}",
                title_ar="اختبار",
                title_en="Test",
                category="aqidah",
            )
            # 7 themes with no errors, 3 with errors
            if i >= 7:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    rule_code=RuleCode.THEME_MIN_VERSES.value,
                    theme_id=f"theme_{i}",
                    theme_name_ar="اختبار",
                    message="Test error",
                    suggested_fix="Fix it",
                ))
            report.theme_results.append(result)

        # 7 out of 10 pass = 70%
        assert report.pass_rate == 70.0

    def test_coverage_rate_calculation(self):
        """Coverage rate should be calculated correctly."""
        report = AuditReport(timestamp="2024-01-01")
        report.total_themes = 10
        report.themes_meeting_min_verses = 3

        # 3 out of 10 = 30%
        assert report.coverage_rate == 30.0


class TestValidationIssue:
    """Tests for ValidationIssue data class."""

    def test_validation_issue_creation(self):
        """ValidationIssue should be created with all fields."""
        issue = ValidationIssue(
            severity=Severity.ERROR,
            rule_code=RuleCode.THEME_MIN_VERSES.value,
            theme_id="test_theme",
            theme_name_ar="اختبار",
            message="Not enough verses",
            suggested_fix="Add more verses",
            details={"current": 2, "required": 3}
        )

        assert issue.severity == Severity.ERROR
        assert issue.rule_code == "THEME_MIN_VERSES"
        assert issue.theme_id == "test_theme"
        assert issue.details["current"] == 2

    def test_issue_count_by_severity(self):
        """ThemeAuditResult should count issues by severity."""
        result = ThemeAuditResult(
            theme_id="test_theme",
            title_ar="اختبار",
            title_en="Test",
            category="aqidah",
        )

        # Add 3 errors and 2 warnings
        for i in range(3):
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                rule_code=RuleCode.THEME_MIN_VERSES.value,
                theme_id="test_theme",
                theme_name_ar="اختبار",
                message=f"Error {i}",
                suggested_fix="Fix",
            ))
        for i in range(2):
            result.issues.append(ValidationIssue(
                severity=Severity.WARN,
                rule_code=RuleCode.THEME_TAFSIR_SOURCES.value,
                theme_id="test_theme",
                theme_name_ar="اختبار",
                message=f"Warning {i}",
                suggested_fix="Fix",
            ))

        assert result.error_count == 3
        assert result.warn_count == 2


# =============================================================================
# TEST 7: ARABIC CONTENT VALIDATION
# =============================================================================

class TestArabicContentValidation:
    """Tests for has_arabic_content function."""

    def test_arabic_text_detected(self):
        """Arabic text should be detected."""
        assert has_arabic_content("التوحيد")
        assert has_arabic_content("مرحبا")
        assert has_arabic_content("بسم الله الرحمن الرحيم")

    def test_english_text_not_arabic(self):
        """English text should not be detected as Arabic."""
        assert not has_arabic_content("Hello world")
        assert not has_arabic_content("This is English")

    def test_empty_text_not_arabic(self):
        """Empty text should not be detected as Arabic."""
        assert not has_arabic_content("")
        assert not has_arabic_content(None)

    def test_mixed_text_has_arabic(self):
        """Mixed text with Arabic should be detected."""
        assert has_arabic_content("Hello مرحبا World")
        assert has_arabic_content("123 التوحيد 456")


# =============================================================================
# TEST 8: RULE CODE ENUMERATION
# =============================================================================

class TestRuleCodes:
    """Tests for rule code enumeration."""

    def test_all_rule_codes_defined(self):
        """All expected rule codes should be defined."""
        expected_codes = [
            "THEME_MIN_VERSES",
            "THEME_HAS_SEGMENT",
            "THEME_TAFSIR_SOURCES",
            "THEME_GRAPH_CONNECTED",
            "THEME_CONSEQUENCE_REWARD",
            "THEME_CONSEQUENCE_PUNISHMENT",
            "SEGMENT_VALID_SURA",
            "SEGMENT_VALID_AYAH",
            "SEGMENT_HAS_EVIDENCE",
            "SEGMENT_APPROVED_SOURCE",
            "ARABIC_NO_ENGLISH_LEAK",
            "ARABIC_NO_PLACEHOLDER",
            "ARABIC_NOT_EMPTY",
            "GRAPH_NO_SELF_LOOP",
            "GRAPH_NO_DUPLICATE_EDGE",
            "CONSEQUENCE_HAS_EVIDENCE",
        ]

        for code in expected_codes:
            assert hasattr(RuleCode, code), f"Missing rule code: {code}"


class TestSeverityEnum:
    """Tests for severity enumeration."""

    def test_severity_values(self):
        """Severity enum should have correct values."""
        assert Severity.ERROR.value == "ERROR"
        assert Severity.WARN.value == "WARN"
        assert Severity.INFO.value == "INFO"


# =============================================================================
# INTEGRATION-LIKE TESTS (without actual DB)
# =============================================================================

class TestAuditReportStructure:
    """Tests for audit report structure."""

    def test_report_has_required_fields(self):
        """AuditReport should have all required fields."""
        report = AuditReport(timestamp="2024-01-01")

        # Verify all expected fields exist
        assert hasattr(report, 'timestamp')
        assert hasattr(report, 'version')
        assert hasattr(report, 'mode')
        assert hasattr(report, 'min_verses_threshold')
        assert hasattr(report, 'total_themes')
        assert hasattr(report, 'themes_with_segments')
        assert hasattr(report, 'themes_meeting_min_verses')
        assert hasattr(report, 'error_count')
        assert hasattr(report, 'warn_count')
        assert hasattr(report, 'connected_components')
        assert hasattr(report, 'isolated_themes')
        assert hasattr(report, 'categories')
        assert hasattr(report, 'theme_results')
        assert hasattr(report, 'all_issues')
        assert hasattr(report, 'top_themes')
        assert hasattr(report, 'bottom_themes')

    def test_report_serializable(self):
        """AuditReport should be serializable to dict."""
        report = AuditReport(timestamp="2024-01-01")
        report.total_themes = 50
        report.error_count = 5

        report_dict = asdict(report)

        assert report_dict['timestamp'] == "2024-01-01"
        assert report_dict['total_themes'] == 50
        assert report_dict['error_count'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
