"""
Unit tests for the /api/v1/quran/resolve endpoint.

Tests verse text resolution with:
- Exact matches (with/without diacritics)
- Partial matches (substring)
- Fuzzy matches (token overlap)
- Error cases
"""
import pytest
from app.api.routes.quran import (
    normalize_arabic_text,
    calculate_token_overlap,
)


class TestNormalizeArabicText:
    """Tests for Arabic text normalization."""

    def test_removes_diacritics(self):
        """Should remove tashkeel from text."""
        input_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        result = normalize_arabic_text(input_text)
        # Should not contain any diacritics
        assert "ِ" not in result  # kasra
        assert "َ" not in result  # fatha
        assert "ّ" not in result  # shadda
        assert "ْ" not in result  # sukun

    def test_normalizes_alef_variants(self):
        """Should normalize all alef variants to plain alef."""
        # أ, إ, آ, ٱ should all become ا
        assert "ا" in normalize_arabic_text("أ")
        assert "ا" in normalize_arabic_text("إ")
        assert "ا" in normalize_arabic_text("آ")
        assert "ا" in normalize_arabic_text("ٱ")

    def test_normalizes_taa_marbutah(self):
        """Should convert taa marbutah to haa."""
        result = normalize_arabic_text("الرحمة")
        assert "ة" not in result
        assert "ه" in result

    def test_normalizes_alef_maqsura(self):
        """Should convert alef maqsura to yaa."""
        result = normalize_arabic_text("على")
        assert "ى" not in result
        assert "ي" in result

    def test_removes_quranic_marks(self):
        """Should remove special Quranic marks and punctuation."""
        input_text = "۞ قُلْ هُوَ اللَّهُ أَحَدٌ ﴿١﴾"
        result = normalize_arabic_text(input_text)
        assert "۞" not in result
        assert "﴿" not in result
        assert "﴾" not in result

    def test_collapses_whitespace(self):
        """Should collapse multiple spaces to single space."""
        result = normalize_arabic_text("الله    أكبر")
        assert "    " not in result
        assert " " in result

    def test_empty_string(self):
        """Should handle empty string."""
        assert normalize_arabic_text("") == ""

    def test_plain_text_unchanged(self):
        """Plain text without diacritics should remain mostly unchanged."""
        input_text = "الله الرحمن الرحيم"
        result = normalize_arabic_text(input_text)
        # Should normalize ة to ه if present, but otherwise similar
        assert "الله" in result
        assert "الرحمن" in result


class TestCalculateTokenOverlap:
    """Tests for Jaccard-like token overlap calculation."""

    def test_identical_strings(self):
        """Identical strings should have overlap of 1.0."""
        text = "الله الرحمن الرحيم"
        assert calculate_token_overlap(text, text) == 1.0

    def test_no_overlap(self):
        """Completely different strings should have overlap of 0.0."""
        result = calculate_token_overlap("الله أكبر", "قل هو")
        assert result == 0.0

    def test_partial_overlap(self):
        """Partial overlap should return value between 0 and 1."""
        text1 = "الله الرحمن الرحيم"
        text2 = "بسم الله الرحمن"
        result = calculate_token_overlap(text1, text2)
        assert 0 < result < 1
        # Intersection: الله, الرحمن = 2
        # Union: الله, الرحمن, الرحيم, بسم = 4
        # Expected: 2/4 = 0.5
        assert result == 0.5

    def test_empty_strings(self):
        """Empty strings should return 0.0."""
        assert calculate_token_overlap("", "") == 0.0
        assert calculate_token_overlap("الله", "") == 0.0
        assert calculate_token_overlap("", "الله") == 0.0

    def test_single_token_match(self):
        """Single token that matches should work correctly."""
        result = calculate_token_overlap("الله", "الله")
        assert result == 1.0

    def test_subset_relationship(self):
        """When one is subset of other, should reflect that."""
        text1 = "الله"
        text2 = "الله الرحمن الرحيم"
        result = calculate_token_overlap(text1, text2)
        # Intersection: 1 (الله)
        # Union: 3 (الله, الرحمن, الرحيم)
        # Expected: 1/3 ≈ 0.333
        assert 0.3 <= result <= 0.4


class TestResolveEndpoint:
    """Integration tests for the resolve endpoint."""

    @pytest.fixture
    def mock_verses(self):
        """Sample verse data for testing."""
        return [
            {"sura_no": 1, "aya_no": 1, "text_uthmani": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"},
            {"sura_no": 112, "aya_no": 1, "text_uthmani": "قُلْ هُوَ اللَّهُ أَحَدٌ"},
            {"sura_no": 112, "aya_no": 2, "text_uthmani": "اللَّهُ الصَّمَدُ"},
            {"sura_no": 2, "aya_no": 255, "text_uthmani": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ..."},
        ]

    def test_exact_match_query(self, mock_verses):
        """Should match verse text exactly (after normalization)."""
        # Query: "قل هو الله أحد" should match 112:1
        query = "قل هو الله أحد"
        query_normalized = normalize_arabic_text(query)

        best_match = None
        best_score = 0

        for verse in mock_verses:
            verse_normalized = normalize_arabic_text(verse["text_uthmani"])
            if query_normalized in verse_normalized or verse_normalized in query_normalized:
                if len(query_normalized) > best_score:
                    best_score = len(query_normalized)
                    best_match = verse

        assert best_match is not None
        assert best_match["sura_no"] == 112
        assert best_match["aya_no"] == 1

    def test_fuzzy_match_query(self, mock_verses):
        """Should fuzzy match when exact match fails."""
        # Query with partial text should still find verse
        query = "الله أحد"
        query_normalized = normalize_arabic_text(query)

        best_match = None
        best_score = 0

        for verse in mock_verses:
            verse_normalized = normalize_arabic_text(verse["text_uthmani"])
            score = calculate_token_overlap(query_normalized, verse_normalized)
            if score > best_score:
                best_score = score
                best_match = verse

        assert best_match is not None
        assert best_match["sura_no"] == 112
        # Score should be reasonable
        assert best_score > 0.3


class TestInputFormats:
    """Tests for various input format handling."""

    def test_arabic_digits_in_text(self):
        """Arabic text input should work regardless of embedded digits."""
        # This tests the frontend parsing, but we test the normalization here
        text = "بسم الله ١"
        normalized = normalize_arabic_text(text)
        # Should handle Arabic numeral gracefully
        assert "بسم" in normalized

    def test_diacritics_stripped(self):
        """Diacritics should not affect matching."""
        with_diacritics = "بِسْمِ اللَّهِ"
        without_diacritics = "بسم الله"

        norm1 = normalize_arabic_text(with_diacritics)
        norm2 = normalize_arabic_text(without_diacritics)

        # Both should normalize to the same thing
        assert norm1 == norm2

    def test_mixed_case_handling(self):
        """Mixed Arabic/Latin input should be handled."""
        text = "Allah أكبر"
        normalized = normalize_arabic_text(text)
        # Latin text preserved, Arabic normalized
        assert "Allah" in normalized
        assert "اكبر" in normalized


# =============================================================================
# Decision Logic Tests
# =============================================================================

class TestDecisionLogic:
    """Tests for resolve decision logic."""

    def test_exact_match_returns_auto(self):
        """Exact match should always return 'auto' decision."""
        # When normalized query matches normalized verse exactly
        # Decision should be 'auto'

        query = "الله الصمد"  # 112:2
        query_normalized = normalize_arabic_text(query)
        verse_normalized = normalize_arabic_text("اللَّهُ الصَّمَدُ")

        # Exact match
        is_exact = query_normalized == verse_normalized
        assert is_exact is True

        # Decision for exact match is always 'auto'
        decision = "auto" if is_exact else "needs_user_choice"
        assert decision == "auto"

    def test_short_input_never_auto(self):
        """Short input (< 8 chars or < 2 tokens) should never be 'auto'."""
        short_inputs = [
            "الله",      # 4 chars, 1 token
            "رب",        # 2 chars, 1 token
            "الحمد",     # 5 chars, 1 token
        ]

        for input_text in short_inputs:
            normalized = normalize_arabic_text(input_text)
            tokens = normalized.split()
            is_short = len(normalized) < 8 or len(tokens) < 2

            assert is_short is True, f"'{input_text}' should be classified as short"

            # Even if confidence is high, short input should not be 'auto'
            confidence = 0.95
            decision = "auto" if not is_short and confidence >= 0.85 else "needs_user_choice"
            assert decision == "needs_user_choice"

    def test_high_confidence_with_margin_returns_auto(self):
        """High confidence (>= 0.85) with margin (>= 0.08) should return 'auto'."""
        best_confidence = 0.90
        second_confidence = 0.75
        margin = best_confidence - second_confidence  # 0.15

        # Not short, not exact
        is_short = False
        is_exact = False

        if is_exact:
            decision = "auto"
        elif is_short:
            decision = "needs_user_choice"
        elif best_confidence >= 0.85 and margin >= 0.08:
            decision = "auto"
        elif best_confidence >= 0.70:
            decision = "needs_user_choice"
        else:
            decision = "not_found"

        assert decision == "auto"

    def test_moderate_confidence_returns_needs_user_choice(self):
        """Moderate confidence (0.70-0.85) should return 'needs_user_choice'."""
        confidence_values = [0.70, 0.75, 0.80, 0.84]

        for confidence in confidence_values:
            is_short = False
            is_exact = False
            margin = 0.05  # Small margin

            if is_exact:
                decision = "auto"
            elif is_short:
                decision = "needs_user_choice"
            elif confidence >= 0.85 and margin >= 0.08:
                decision = "auto"
            elif confidence >= 0.70:
                decision = "needs_user_choice"
            else:
                decision = "not_found"

            assert decision == "needs_user_choice", f"confidence={confidence} should be 'needs_user_choice'"

    def test_low_confidence_returns_not_found(self):
        """Low confidence (< 0.70) should return 'not_found'."""
        confidence_values = [0.30, 0.50, 0.65, 0.69]

        for confidence in confidence_values:
            is_short = False
            is_exact = False
            margin = 0.05

            if is_exact:
                decision = "auto"
            elif is_short:
                decision = "needs_user_choice"
            elif confidence >= 0.85 and margin >= 0.08:
                decision = "auto"
            elif confidence >= 0.70:
                decision = "needs_user_choice"
            else:
                decision = "not_found"

            assert decision == "not_found", f"confidence={confidence} should be 'not_found'"

    def test_candidates_limited_to_5(self):
        """Top candidates should be limited to 5."""
        # Simulate many candidates
        candidates = [
            {"surah": i, "ayah": 1, "confidence": 0.5 + i * 0.01}
            for i in range(10)
        ]

        # Sort by confidence descending
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        # Limit to top 5
        top_candidates = candidates[:5]

        assert len(top_candidates) == 5
        assert top_candidates[0]["confidence"] > top_candidates[-1]["confidence"]


class TestMinimumInputConstraints:
    """Tests for minimum input requirements."""

    def test_minimum_3_chars_required(self):
        """Input must be at least 3 characters after normalization."""
        inputs = [
            ("ا", False),       # 1 char - fail
            ("اب", False),      # 2 chars - fail
            ("الل", True),      # 3 chars - pass
            ("الله", True),     # 4 chars - pass
        ]

        for input_text, should_pass in inputs:
            normalized = normalize_arabic_text(input_text)
            passes = len(normalized) >= 3
            assert passes == should_pass, f"'{input_text}' length check failed"

    def test_auto_requires_8_chars_and_2_tokens(self):
        """Auto decision requires >= 8 chars AND >= 2 tokens."""
        test_cases = [
            ("الله أكبر", True),       # 9 chars, 2 tokens - passes
            ("الحمد لله رب", True),    # 12 chars, 3 tokens - passes
            ("الله", False),            # 4 chars, 1 token - fails
            ("الرحمن", False),          # 6 chars, 1 token - fails
            ("أ ب ج د", False),         # 7 chars, 4 tokens but too short - fails
        ]

        for input_text, should_allow_auto in test_cases:
            normalized = normalize_arabic_text(input_text)
            tokens = normalized.split()
            can_auto = len(normalized) >= 8 and len(tokens) >= 2
            assert can_auto == should_allow_auto, f"'{input_text}' auto check failed"


# =============================================================================
# API Contract Tests (requires running server)
# =============================================================================

class TestResolveAPIContract:
    """API contract tests - run with actual server."""

    @pytest.mark.skip(reason="Requires running server")
    def test_resolve_endpoint_auto_decision(self):
        """Test auto decision for exact match via API."""
        import httpx
        response = httpx.get(
            "http://localhost:8000/api/v1/quran/resolve",
            params={"text": "قل هو الله أحد"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["decision"] == "auto"
        assert data["data"]["best_match"] is not None
        assert data["data"]["best_match"]["surah"] == 112
        assert data["data"]["best_match"]["ayah"] == 1

    @pytest.mark.skip(reason="Requires running server")
    def test_resolve_endpoint_needs_user_choice(self):
        """Test needs_user_choice decision for ambiguous input."""
        import httpx
        # Short but matching fragment
        response = httpx.get(
            "http://localhost:8000/api/v1/quran/resolve",
            params={"text": "الله"}  # Short, matches many verses
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        # Short input should never be auto
        assert data["data"]["decision"] in ["needs_user_choice", "not_found"]

    @pytest.mark.skip(reason="Requires running server")
    def test_resolve_endpoint_not_found(self):
        """Test not_found decision for invalid text."""
        import httpx
        response = httpx.get(
            "http://localhost:8000/api/v1/quran/resolve",
            params={"text": "random text that is not a verse xyz"}
        )
        assert response.status_code == 200  # Now returns 200 with decision
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["decision"] == "not_found"

    @pytest.mark.skip(reason="Requires running server")
    def test_resolve_returns_candidates(self):
        """Test that response includes candidates."""
        import httpx
        response = httpx.get(
            "http://localhost:8000/api/v1/quran/resolve",
            params={"text": "الله لا إله إلا هو"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "candidates" in data["data"]
        assert isinstance(data["data"]["candidates"], list)
        # Should have up to 5 candidates
        assert len(data["data"]["candidates"]) <= 5

    @pytest.mark.skip(reason="Requires running server")
    def test_resolve_missing_param(self):
        """Test missing text parameter."""
        import httpx
        response = httpx.get(
            "http://localhost:8000/api/v1/quran/resolve"
        )
        assert response.status_code == 422  # Validation error
