"""
Tests for Enhanced Alatlas Service Features
"""
import pytest
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from app.services.alatlas_service import AltlasService


class TestEnhancedAltlasService:
    """Test suite for enhanced AltlasService features"""

    @pytest.fixture
    def service(self):
        return AltlasService()

    # ===== Enhanced Search Tests =====

    def test_fuzzy_search(self, service):
        """Test fuzzy search with typo tolerance"""
        # Search with slight variation
        results = service.fuzzy_search("موسا", threshold=0.5)  # typo in موسى
        assert len(results) > 0
        print(f"✓ Fuzzy search passed - found {len(results)} results")

    def test_advanced_search(self, service):
        """Test advanced search with filters"""
        result = service.search_advanced(
            query="موسى",
            categories=["prophets"],
            fuzzy=True
        )
        assert "results" in result
        assert "expanded_queries" in result
        assert len(result["results"]) > 0
        print(f"✓ Advanced search passed - {len(result['results'])} results")

    def test_search_by_theme_and_prophet(self, service):
        """Test searching by theme and prophet combination"""
        result = service.search_by_theme_and_prophet(
            theme="patience",
            prophet="موسى"
        )
        assert "results" in result
        print(f"✓ Search by theme/prophet passed - {len(result['results'])} results")

    # ===== Dynamic Theme & Category Tests =====

    def test_dynamic_themes(self, service):
        """Test dynamic theme retrieval"""
        result = service.get_dynamic_themes()
        assert "themes" in result
        assert "last_updated" in result

        # Check theme has related themes
        themes = result["themes"]
        assert len(themes) > 0
        theme = themes[0]
        assert "story_count" in theme
        assert "related_themes" in theme
        print(f"✓ Dynamic themes passed - {len(themes)} themes with stats")

    def test_dynamic_categories(self, service):
        """Test dynamic category retrieval"""
        result = service.get_dynamic_categories()
        assert "categories" in result
        assert "last_updated" in result

        # Check category has theme distribution
        categories = result["categories"]
        assert len(categories) > 0
        cat = categories[0]
        assert "themes_distribution" in cat
        print(f"✓ Dynamic categories passed - {len(categories)} categories with stats")

    # ===== Enhanced Graph Visualization Tests =====

    def test_expanded_graph(self, service):
        """Test expanded graph with themes and events"""
        result = service.get_expanded_graph(
            include_themes=True,
            include_events=True,
            color_by_theme=True
        )
        assert "graph" in result
        assert "node_types" in result
        assert "theme_colors" in result

        node_types = result["node_types"]
        assert "story" in node_types
        assert "prophet" in node_types
        assert "theme" in node_types
        print(f"✓ Expanded graph passed - {result['total_nodes']} nodes, {result['total_edges']} edges")

    def test_thematic_path_finding(self, service):
        """Test BFS pathfinding between stories"""
        result = service.find_thematic_path("adam", "musa", max_depth=5)
        assert "found" in result
        assert "path" in result

        if result["found"]:
            assert len(result["path"]) >= 2
            print(f"✓ Thematic path found - {result['path_length']} steps")
        else:
            print("✓ Thematic path test passed - no path within depth")

    # ===== Story Completeness Verification Tests =====

    def test_verify_completeness(self, service):
        """Test comprehensive completeness verification"""
        result = service.verify_completeness("musa")
        assert "overall_score" in result
        assert "sections" in result
        assert "completeness_level" in result

        # Check sections exist
        sections = result["sections"]
        assert "basic_info" in sections
        assert "themes" in sections
        assert "figures" in sections
        assert "events" in sections
        print(f"✓ Completeness verification passed - score: {result['overall_score']}")

    def test_update_story(self, service):
        """Test story update functionality"""
        result = service.update_story("adam", {
            "key_lessons_ar": ["الصبر على البلاء", "التوبة من الذنب"]
        })
        assert result.get("success") is True or "updated_fields" in result
        print("✓ Story update passed")

    # ===== User Feedback Tests =====

    def test_submit_feedback(self, service):
        """Test feedback submission"""
        result = service.submit_story_feedback(
            story_id="musa",
            user_id="test_user_123",
            rating=5,
            accuracy_rating=5,
            completeness_rating=4,
            comment="قصة رائعة ومفيدة"
        )
        assert result.get("success") is True
        print("✓ Feedback submission passed")

    def test_get_feedback(self, service):
        """Test feedback retrieval"""
        # First submit feedback
        service.submit_story_feedback(
            story_id="adam",
            user_id="test_user_456",
            rating=4,
            accuracy_rating=4,
            completeness_rating=4
        )

        result = service.get_story_feedback("adam")
        assert "feedback_stats" in result
        print("✓ Feedback retrieval passed")

    # ===== Content Expansion Tests =====

    def test_prophet_details(self, service):
        """Test prophet details retrieval"""
        result = service.get_prophet_details("musa")
        assert "prophet" in result
        assert "stories" in result
        assert "events" in result

        prophet = result["prophet"]
        assert "name_ar" in prophet
        assert "name_en" in prophet
        print(f"✓ Prophet details passed - {result['total_stories']} stories, {result['total_events']} events")

    def test_get_all_events(self, service):
        """Test getting all events"""
        result = service.get_all_events(limit=50)
        assert "events" in result
        assert "total" in result
        assert len(result["events"]) > 0
        print(f"✓ Get all events passed - {result['total']} events")

    # ===== User Journey Tests =====

    def test_save_user_journey(self, service):
        """Test saving user journey"""
        result = service.save_user_journey(
            user_id="test_user_journey",
            current_story_id="adam",
            themes_explored=["creation", "repentance"],
            time_spent_seconds=300
        )
        assert result.get("success") is True
        print("✓ User journey save passed")

    def test_get_user_progress(self, service):
        """Test getting user progress"""
        # First save a journey
        service.save_user_journey(
            user_id="test_user_progress",
            current_story_id="musa",
            themes_explored=["patience", "faith"],
            time_spent_seconds=600
        )

        result = service.get_user_progress("test_user_progress")
        assert "progress" in result
        print("✓ User progress retrieval passed")

    # ===== Multilingual & Tafsir Tests =====

    def test_available_languages(self, service):
        """Test getting available languages"""
        result = service.get_available_languages()
        assert "languages" in result
        assert "default_language" in result

        languages = result["languages"]
        ar_lang = next((l for l in languages if l["code"] == "ar"), None)
        assert ar_lang is not None
        assert ar_lang["is_primary"] is True
        print(f"✓ Languages test passed - {len(languages)} languages")

    def test_story_with_tafsir(self, service):
        """Test getting story with tafsir"""
        result = service.get_story_with_tafsir("adam", language="ar")
        assert "tafsir_integration" in result
        assert "display_title" in result
        assert "language" in result

        tafsir = result["tafsir_integration"]
        assert "available_sources" in tafsir
        print("✓ Story with tafsir passed")

    # ===== Recommendations Tests =====

    def test_recommendations(self, service):
        """Test story recommendations"""
        result = service.get_recommendations(
            current_story_id="adam",
            based_on="mixed",
            limit=5
        )
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        rec = result["recommendations"][0]
        assert "story_id" in rec
        assert "reason" in rec
        print(f"✓ Recommendations passed - {len(result['recommendations'])} recommendations")

    # ===== Caching Tests =====

    def test_cached_stories(self, service):
        """Test cached story retrieval"""
        # First call - should build cache
        result1 = service.get_cached_stories(force_refresh=True)
        assert "data" in result1
        assert "from_cache" in result1
        assert result1["from_cache"] is False

        # Second call - should use cache
        result2 = service.get_cached_stories()
        assert result2["from_cache"] is True
        print("✓ Caching test passed")

    def test_cache_stats(self, service):
        """Test cache statistics"""
        # Ensure cache has data
        service.get_cached_stories(force_refresh=True)

        result = service.get_cache_stats()
        assert "total_cached_items" in result
        assert "cache_entries" in result
        print(f"✓ Cache stats passed - {result['total_cached_items']} items cached")

    def test_clear_cache(self, service):
        """Test cache clearing"""
        # First populate cache
        service.get_cached_stories(force_refresh=True)

        result = service.clear_cache()
        assert result["success"] is True
        print("✓ Cache clear passed")


def run_all_tests():
    """Run all tests manually"""
    service = AltlasService()
    test = TestEnhancedAltlasService()

    print("\n" + "="*60)
    print("Testing Enhanced Alatlas Service Features")
    print("="*60 + "\n")

    tests = [
        ("Fuzzy Search", lambda: test.test_fuzzy_search(service)),
        ("Advanced Search", lambda: test.test_advanced_search(service)),
        ("Search Theme/Prophet", lambda: test.test_search_by_theme_and_prophet(service)),
        ("Dynamic Themes", lambda: test.test_dynamic_themes(service)),
        ("Dynamic Categories", lambda: test.test_dynamic_categories(service)),
        ("Expanded Graph", lambda: test.test_expanded_graph(service)),
        ("Thematic Path Finding", lambda: test.test_thematic_path_finding(service)),
        ("Completeness Verification", lambda: test.test_verify_completeness(service)),
        ("Story Update", lambda: test.test_update_story(service)),
        ("Submit Feedback", lambda: test.test_submit_feedback(service)),
        ("Get Feedback", lambda: test.test_get_feedback(service)),
        ("Prophet Details", lambda: test.test_prophet_details(service)),
        ("All Events", lambda: test.test_get_all_events(service)),
        ("Save User Journey", lambda: test.test_save_user_journey(service)),
        ("User Progress", lambda: test.test_get_user_progress(service)),
        ("Available Languages", lambda: test.test_available_languages(service)),
        ("Story with Tafsir", lambda: test.test_story_with_tafsir(service)),
        ("Recommendations", lambda: test.test_recommendations(service)),
        ("Cached Stories", lambda: test.test_cached_stories(service)),
        ("Cache Stats", lambda: test.test_cache_stats(service)),
        ("Clear Cache", lambda: test.test_clear_cache(service)),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {name} FAILED: {str(e)}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
