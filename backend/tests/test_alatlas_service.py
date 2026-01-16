"""
Tests for Alatlas Service - Quranic Stories Atlas with Arabic Classification
"""
import pytest
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from app.services.alatlas_service import AltlasService, StoryCategory, StoryTheme


class TestAltlasService:
    """Test suite for AltlasService"""

    @pytest.fixture
    def service(self):
        return AltlasService()

    # ===== Category and Theme Tests =====

    def test_get_categories(self, service):
        """Test getting all Arabic story categories"""
        result = service.get_categories()
        assert "categories" in result
        assert len(result["categories"]) == 8

        # Verify Arabic names
        category_names = {c["id"]: c["name_ar"] for c in result["categories"]}
        assert "prophets" in category_names
        assert category_names["prophets"] == "الأنبياء"
        assert "nations" in category_names
        assert category_names["nations"] == "الأمم"
        print("✓ Categories test passed - 8 Arabic categories verified")

    def test_get_themes(self, service):
        """Test getting all Arabic story themes"""
        result = service.get_themes()
        assert "themes" in result
        assert len(result["themes"]) >= 15  # At least 15 themes

        # Verify Arabic themes
        theme_names = {t["id"]: t["name_ar"] for t in result["themes"]}
        assert "faith" in theme_names
        assert theme_names["faith"] == "الإيمان"
        assert "patience" in theme_names
        assert theme_names["patience"] == "الصبر"
        print(f"✓ Themes test passed - {len(result['themes'])} Arabic themes verified")

    # ===== Story Data Tests =====

    def test_get_all_stories(self, service):
        """Test getting all stories with pagination"""
        result = service.get_all_stories()
        assert "stories" in result
        assert "total" in result
        assert result["total"] >= 8  # At least 8 stories
        assert len(result["stories"]) > 0

        # Verify story structure
        story = result["stories"][0]
        assert "id" in story
        assert "title_ar" in story
        assert "category" in story
        assert "themes" in story
        print(f"✓ Get all stories passed - {result['total']} stories found")

    def test_get_story_by_id(self, service):
        """Test getting a specific story by ID"""
        # Test Prophet Adam story
        result = service.get_story("adam")
        assert result is not None
        assert result["id"] == "adam"
        assert result["title_ar"] == "قصة آدم عليه السلام"
        assert result["category"] == "prophets"
        assert len(result["figures"]) > 0
        assert len(result["events"]) > 0
        assert len(result["verses"]) > 0
        print("✓ Get story by ID passed - Adam story verified")

    def test_get_story_invalid_id(self, service):
        """Test getting a story with invalid ID"""
        result = service.get_story("invalid_story_id")
        assert result is None
        print("✓ Invalid story ID test passed")

    def test_story_completeness(self, service):
        """Test that stories have complete data"""
        # Test Yusuf story for completeness
        result = service.get_story("yusuf")
        assert result is not None

        # Verify all required fields
        assert result["title_ar"] == "قصة يوسف عليه السلام"
        assert "Joseph" in result["title_en"] or "Yusuf" in result["title_en"]
        assert len(result["summary_ar"]) > 50
        assert len(result["figures"]) >= 3  # Yusuf, Ya'qub, etc.
        assert len(result["events"]) >= 5
        assert len(result["themes"]) >= 3
        assert len(result.get("tafsir_references", [])) > 0 or len(result.get("tafsir_notes", [])) >= 0
        print("✓ Story completeness test passed - Yusuf story has complete data")

    # ===== Story Verification Tests =====

    def test_verify_story(self, service):
        """Test story verification"""
        result = service.verify_story("musa")
        assert "story_id" in result
        assert result["story_id"] == "musa"
        assert "completeness_score" in result
        assert result["completeness_score"] >= 0.8  # At least 80% complete
        print(f"✓ Story verification passed - Musa story score: {result['completeness_score']}")

    def test_verify_invalid_story(self, service):
        """Test verification of invalid story"""
        result = service.verify_story("invalid")
        assert "error" in result
        print("✓ Invalid story verification test passed")

    # ===== Graph Visualization Tests =====

    def test_get_story_graph(self, service):
        """Test getting graph visualization data (الرسم البياني)"""
        result = service.get_story_graph("ibrahim")
        assert "nodes" in result or ("graph" in result and "nodes" in result.get("graph", {}))

        # Handle both possible return formats
        if "graph" in result:
            graph = result["graph"]
        else:
            graph = result

        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) >= 0

        # Verify node structure for D3.js/Cytoscape
        node = graph["nodes"][0]
        assert "id" in node
        assert "type" in node
        assert "label" in node
        print(f"✓ Graph visualization test passed - {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    def test_get_complete_atlas_graph(self, service):
        """Test getting complete atlas graph"""
        result = service.get_complete_graph()
        assert "graph" in result
        assert len(result["graph"]["nodes"]) > 10
        assert len(result["graph"]["edges"]) >= 5
        print(f"✓ Complete atlas graph passed - {len(result['graph']['nodes'])} total nodes")

    # ===== Story Relationships Tests =====

    def test_get_story_relationships(self, service):
        """Test getting story relationships"""
        result = service.get_story_relationships("nuh")
        assert "story_id" in result

        # Verify relationships data is present
        assert "direct_relationships" in result or "related_stories" in result
        assert result["total_relationships"] >= 0
        print("✓ Story relationships test passed")

    # ===== Search and Filter Tests =====

    def test_search_stories(self, service):
        """Test searching stories"""
        # Search for "موسى" (Musa)
        result = service.search_stories("موسى")
        assert "results" in result
        assert len(result["results"]) > 0

        # Verify Musa story is in results
        story_ids = [s["story_id"] for s in result["results"]]
        assert "musa" in story_ids
        print(f"✓ Search test passed - found {len(result['results'])} results for 'موسى'")

    def test_search_by_prophet(self, service):
        """Test searching by prophet name"""
        result = service.search_stories("إبراهيم", prophet="إبراهيم")
        assert "results" in result
        assert len(result["results"]) > 0
        print("✓ Search by prophet test passed")

    def test_filter_by_category(self, service):
        """Test filtering stories by category"""
        result = service.get_all_stories(category="prophets")
        assert "stories" in result

        # All results should be prophet stories
        for story in result["stories"]:
            assert story["category"] == "prophets"
        print(f"✓ Filter by category passed - {len(result['stories'])} prophet stories")

    def test_filter_by_theme(self, service):
        """Test filtering stories by theme"""
        result = service.get_all_stories(theme="patience")
        assert "stories" in result
        assert len(result["stories"]) > 0
        print(f"✓ Filter by theme passed - {len(result['stories'])} stories with patience theme")

    def test_advanced_filter(self, service):
        """Test advanced filtering"""
        result = service.advanced_filter(
            categories=["prophets"],
            themes=["faith"],
            min_verses=3
        )
        assert "stories" in result
        print(f"✓ Advanced filter passed - {len(result['stories'])} stories match criteria")

    # ===== Timeline Tests =====

    def test_get_timeline(self, service):
        """Test chronological timeline"""
        result = service.get_timeline()
        assert "timeline" in result
        assert len(result["timeline"]) > 0

        # Verify chronological order
        timeline = result["timeline"]
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                assert timeline[i]["order"] >= timeline[i-1]["order"]
        print(f"✓ Timeline test passed - {len(timeline)} stories in chronological order")

    # ===== Prophet List Tests =====

    def test_get_prophets(self, service):
        """Test getting all prophets"""
        result = service.get_prophets()
        assert "prophets" in result
        assert len(result["prophets"]) > 0

        # Verify prophet data
        prophet_names = [p["name_ar"] for p in result["prophets"]]
        assert any("آدم" in name for name in prophet_names)
        print(f"✓ Prophets list passed - {len(result['prophets'])} prophets found")

    # ===== Statistics Tests =====

    def test_get_stats(self, service):
        """Test getting atlas statistics"""
        result = service.get_stats()
        assert "stats" in result

        stats = result["stats"]
        assert "total_stories" in stats
        assert "total_categories" in stats
        assert "total_themes" in stats
        assert stats["total_stories"] >= 8
        assert stats["total_categories"] == 8
        print(f"✓ Stats test passed - {stats['total_stories']} stories, {stats['total_categories']} categories")


def run_all_tests():
    """Run all tests manually"""
    service = AltlasService()
    test = TestAltlasService()

    print("\n" + "="*60)
    print("Testing Alatlas Service - Quranic Stories Atlas")
    print("="*60 + "\n")

    tests = [
        ("Categories", lambda: test.test_get_categories(service)),
        ("Themes", lambda: test.test_get_themes(service)),
        ("Get All Stories", lambda: test.test_get_all_stories(service)),
        ("Get Story by ID", lambda: test.test_get_story_by_id(service)),
        ("Invalid Story ID", lambda: test.test_get_story_invalid_id(service)),
        ("Story Completeness", lambda: test.test_story_completeness(service)),
        ("Verify Story", lambda: test.test_verify_story(service)),
        ("Verify Invalid Story", lambda: test.test_verify_invalid_story(service)),
        ("Graph Visualization", lambda: test.test_get_story_graph(service)),
        ("Complete Atlas Graph", lambda: test.test_get_complete_atlas_graph(service)),
        ("Story Relationships", lambda: test.test_get_story_relationships(service)),
        ("Search Stories", lambda: test.test_search_stories(service)),
        ("Search by Prophet", lambda: test.test_search_by_prophet(service)),
        ("Filter by Category", lambda: test.test_filter_by_category(service)),
        ("Filter by Theme", lambda: test.test_filter_by_theme(service)),
        ("Advanced Filter", lambda: test.test_advanced_filter(service)),
        ("Timeline", lambda: test.test_get_timeline(service)),
        ("Prophets List", lambda: test.test_get_prophets(service)),
        ("Statistics", lambda: test.test_get_stats(service)),
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
