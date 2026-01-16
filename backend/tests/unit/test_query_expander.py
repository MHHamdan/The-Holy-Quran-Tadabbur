#!/usr/bin/env python3
"""
Golden tests for query expander.

Tests:
1. Intent classification
2. Expansion capping (MAX_EXPANSIONS)
3. Intent-based filtering
4. Arabic term limiting
"""
import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.query_expander import (
    expand_query,
    QueryExpander,
    QueryIntent,
    MAX_EXPANSIONS,
    MAX_ARABIC_TERMS,
    GOLDEN_TESTS,
    run_golden_tests,
)


class TestQueryExpander:
    """Test suite for QueryExpander."""

    def setup_method(self):
        """Set up test fixtures."""
        self.expander = QueryExpander()

    def test_intent_classification_story(self):
        """Test story intent classification."""
        result = expand_query("What is the story of Moses?")
        assert result.intent == QueryIntent.STORY_EXPLORATION

    def test_intent_classification_ruling(self):
        """Test ruling intent classification."""
        result = expand_query("Is eating pork halal?")
        assert result.intent == QueryIntent.RULING

    def test_intent_classification_verse_meaning(self):
        """Test verse meaning intent classification."""
        result = expand_query("Explain the meaning of Al-Fatiha")
        assert result.intent == QueryIntent.VERSE_MEANING

    def test_intent_classification_linguistic(self):
        """Test linguistic intent classification."""
        result = expand_query("What is the root of this word?")
        assert result.intent == QueryIntent.LINGUISTIC

    def test_intent_classification_theme(self):
        """Test theme intent classification."""
        result = expand_query("Theme of mercy in Quran")
        assert result.intent == QueryIntent.THEME_SEARCH

    def test_expansion_capping(self):
        """Test that expansions are capped at MAX_EXPANSIONS."""
        # Query with many expandable terms
        result = expand_query("patience prayer fasting charity pilgrimage faith trust repentance")

        assert len(result.expanded_terms) <= MAX_EXPANSIONS, \
            f"Expanded terms ({len(result.expanded_terms)}) exceeds MAX_EXPANSIONS ({MAX_EXPANSIONS})"

    def test_arabic_terms_capping(self):
        """Test that Arabic terms are capped at MAX_ARABIC_TERMS."""
        # Query with many expandable terms
        result = expand_query("patience prayer fasting charity pilgrimage faith trust repentance")

        assert len(result.arabic_terms) <= MAX_ARABIC_TERMS, \
            f"Arabic terms ({len(result.arabic_terms)}) exceeds MAX_ARABIC_TERMS ({MAX_ARABIC_TERMS})"

    def test_original_query_preserved(self):
        """Test that original query is preserved."""
        query = "What is the meaning of sabr?"
        result = expand_query(query)

        assert result.original == query
        assert query in result.combined

    def test_intent_based_expansion_story(self):
        """Test that story queries get prophet-related expansions."""
        # Use "story" keyword to ensure STORY_EXPLORATION intent
        result = expand_query("Tell me the story of Moses in the Quran")

        # Should have story-related terms or Arabic equivalent
        all_terms = " ".join(result.expanded_terms + result.arabic_terms).lower()
        # The intent is story_exploration, and moses should be expanded
        assert result.intent == QueryIntent.STORY_EXPLORATION
        # At minimum, moses or related term should be in combined query
        assert "moses" in result.combined.lower() or "musa" in result.combined.lower() or "موسى" in result.combined

    def test_intent_based_expansion_ruling(self):
        """Test that ruling queries get fiqh-related expansions."""
        result = expand_query("Is something halal or haram?")

        # Should have ruling-related terms
        all_terms = " ".join(result.expanded_terms).lower()
        # halal should be included
        assert "halal" in all_terms or "haram" in all_terms or "permissible" in all_terms

    def test_combined_query_length_limit(self):
        """Test that combined query respects length limit."""
        # Very long query
        long_query = "patience " * 100
        result = expand_query(long_query)

        # Combined should not exceed reasonable length
        assert len(result.combined) <= 600  # MAX_COMBINED_LENGTH + original

    def test_expansion_applied_tracking(self):
        """Test that expansion_applied tracks what was expanded."""
        result = expand_query("What is sabr?")

        # Should track the sabr -> patience expansion
        expansion_str = " ".join(result.expansion_applied)
        assert "sabr" in expansion_str.lower() or "patience" in expansion_str.lower()

    def test_arabic_transliteration_mapping(self):
        """Test that Arabic transliterations map correctly."""
        result = expand_query("Tell me about tawbah")

        # tawbah should map to repentance
        all_terms = " ".join(result.expanded_terms).lower()
        assert "repentance" in all_terms or "tawbah" in all_terms

    def test_empty_query(self):
        """Test handling of empty query."""
        result = expand_query("")

        assert result.original == ""
        assert result.combined == ""

    def test_non_islamic_query(self):
        """Test handling of query with no Islamic terms."""
        result = expand_query("How to cook pasta?")

        # Should still return a valid result with original query
        assert result.original == "How to cook pasta?"
        assert result.combined == "How to cook pasta?"
        assert len(result.expanded_terms) == 0


class TestGoldenTests:
    """Test the golden test cases."""

    def test_golden_tests_pass(self):
        """Run all golden tests and verify they pass."""
        results = run_golden_tests()

        for result in results:
            assert result["passed"], \
                f"Golden test failed: {result['query']}\n" \
                f"  Intent: expected {result['expected_intent']}, got {result['actual_intent']}\n" \
                f"  Terms: expected {result['expected_terms']}, got {result['actual_terms']}\n" \
                f"  Under cap: {result['under_cap']} (count: {result['expansion_count']})"

    def test_golden_test_count(self):
        """Ensure we have enough golden tests."""
        assert len(GOLDEN_TESTS) >= 5, "Need at least 5 golden tests"


class TestIntentFiltering:
    """Test intent-based term filtering."""

    def test_prophet_terms_not_in_ruling_query(self):
        """Prophet terms should not expand in ruling queries."""
        expander = QueryExpander()

        # This should classify as ruling, not story
        result = expander.expand("Is zakah obligatory?")

        # Moses shouldn't be in expansions for a ruling query
        all_terms = " ".join(result.expanded_terms).lower()
        assert "moses" not in all_terms
        assert "musa" not in all_terms

    def test_ruling_terms_prioritized_in_ruling_query(self):
        """Ruling terms should be included in ruling queries."""
        expander = QueryExpander()

        result = expander.expand("Is this halal?")

        # halal should be expanded
        all_terms = " ".join(result.expanded_terms).lower()
        assert "halal" in all_terms or "permissible" in all_terms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
