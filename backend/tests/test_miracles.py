"""
Tests for Miracles & Verses Service
Comprehensive tests for Quranic miracles with tafsir from four Sunni madhabs
"""
import pytest
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from app.services.miracles_service import (
    MiraclesService,
    MiracleCategory,
    MiracleType,
    Madhab,
    VerificationStatus
)


class TestMiraclesService:
    """Test suite for MiraclesService"""

    @pytest.fixture
    def service(self):
        return MiraclesService()

    # ===== Basic Retrieval Tests =====

    def test_get_all_miracles(self, service):
        """Test getting all miracles"""
        result = service.get_all_miracles()
        assert "miracles" in result
        assert "total" in result
        assert "categories" in result
        assert len(result["miracles"]) > 0
        print(f"✓ Get all miracles passed - {result['total']} miracles")

    def test_get_all_miracles_with_category_filter(self, service):
        """Test filtering miracles by category"""
        result = service.get_all_miracles(category="prophetic")
        assert "miracles" in result
        # All miracles should be prophetic
        for miracle in result["miracles"]:
            assert miracle["category"] == "prophetic"
        print(f"✓ Category filter passed - {result['total']} prophetic miracles")

    def test_get_miracle_by_id(self, service):
        """Test getting a specific miracle"""
        result = service.get_miracle("musa_staff_serpent")
        assert "miracle" in result
        miracle = result["miracle"]
        assert miracle["id"] == "musa_staff_serpent"
        assert miracle["name_ar"] == "تحول عصا موسى إلى ثعبان"
        assert miracle["prophet_id"] == "musa"
        print("✓ Get miracle by ID passed")

    def test_get_nonexistent_miracle(self, service):
        """Test getting a miracle that doesn't exist"""
        result = service.get_miracle("nonexistent_miracle")
        assert "error" in result
        print("✓ Nonexistent miracle error handling passed")

    # ===== Prophet Miracles Tests =====

    def test_get_miracles_by_prophet(self, service):
        """Test getting miracles for a specific prophet"""
        result = service.get_miracles_by_prophet("musa")
        assert "prophet_id" in result
        assert result["prophet_id"] == "musa"
        assert "miracles" in result
        assert result["miracle_count"] >= 3  # At least staff, sea, hand
        print(f"✓ Prophet miracles passed - {result['miracle_count']} miracles for Musa")

    def test_get_prophets_with_miracles(self, service):
        """Test getting all prophets with miracles"""
        result = service.get_prophets_with_miracles()
        assert "prophets" in result
        assert len(result["prophets"]) > 0

        # Check each prophet has required fields
        for prophet in result["prophets"]:
            assert "prophet_id" in prophet
            assert "name_ar" in prophet
            assert "miracle_count" in prophet
        print(f"✓ Prophets with miracles passed - {result['total']} prophets")

    # ===== Category and Theme Tests =====

    def test_get_miracle_categories(self, service):
        """Test getting miracle categories"""
        result = service.get_miracle_categories()
        assert "categories" in result

        # Should have all enum categories
        category_ids = [c["id"] for c in result["categories"]]
        assert "prophetic" in category_ids
        assert "divine" in category_ids

        # Each category should have Arabic name
        for cat in result["categories"]:
            assert "name_ar" in cat
            assert "miracle_count" in cat
        print(f"✓ Categories passed - {len(result['categories'])} categories")

    def test_get_miracle_themes(self, service):
        """Test getting miracle themes"""
        result = service.get_miracle_themes()
        assert "themes" in result
        assert "total_themes" in result

        # Each theme should have counts
        for theme in result["themes"]:
            assert "id" in theme
            assert "name_ar" in theme
            assert "miracle_count" in theme
        print(f"✓ Themes passed - {result['total_themes']} themes")

    # ===== Tafsir Tests - Four Sunni Madhabs =====

    def test_tafsir_from_all_madhabs(self, service):
        """Test that miracles have tafsir from all four madhabs"""
        result = service.get_miracle("musa_staff_serpent")
        miracle = result["miracle"]

        # Get madhabs in tafsir references
        madhabs = {t["madhab"] for t in miracle["tafsir_references"]}

        # Should have all four Sunni madhabs
        assert "hanafi" in madhabs, "Missing Hanafi tafsir"
        assert "maliki" in madhabs, "Missing Maliki tafsir"
        assert "shafii" in madhabs, "Missing Shafi'i tafsir"
        assert "hanbali" in madhabs, "Missing Hanbali tafsir"
        print("✓ All four madhabs present in tafsir")

    def test_tafsir_scholar_info(self, service):
        """Test that tafsir has proper scholar information"""
        result = service.get_miracle("musa_parting_sea")
        miracle = result["miracle"]

        for tafsir in miracle["tafsir_references"]:
            assert "scholar_name_ar" in tafsir
            assert "scholar_name_en" in tafsir
            assert "book_name_ar" in tafsir
            assert "explanation_ar" in tafsir
            assert "madhab" in tafsir
        print("✓ Tafsir scholar info validation passed")

    def test_get_tafsir_sources(self, service):
        """Test getting all tafsir sources"""
        result = service.get_tafsir_sources()
        assert "sources" in result
        assert "by_madhab" in result

        # Should have sources grouped by madhab
        assert "hanafi" in result["by_madhab"]
        assert "maliki" in result["by_madhab"]
        assert "shafii" in result["by_madhab"]
        assert "hanbali" in result["by_madhab"]
        print(f"✓ Tafsir sources passed - {result['total']} sources")

    # ===== Verse Reference Tests =====

    def test_miracle_has_verses(self, service):
        """Test that miracles have proper verse references"""
        result = service.get_miracle("musa_staff_serpent")
        miracle = result["miracle"]

        assert "verses" in miracle
        assert len(miracle["verses"]) > 0

        for verse in miracle["verses"]:
            assert "surah_number" in verse
            assert "surah_name_ar" in verse
            assert "ayah_number" in verse
            assert "text_ar" in verse
            assert "text_en" in verse
            assert "relevance" in verse
        print(f"✓ Verse references passed - {len(miracle['verses'])} verses")

    # ===== Search Tests =====

    def test_keyword_search(self, service):
        """Test keyword search for miracles"""
        result = service.search_miracles(query="موسى")
        assert "results" in result
        assert len(result["results"]) > 0
        print(f"✓ Keyword search passed - {len(result['results'])} results for 'موسى'")

    def test_search_english(self, service):
        """Test search in English"""
        result = service.search_miracles(query="staff")
        assert "results" in result
        assert len(result["results"]) > 0
        print(f"✓ English search passed - {len(result['results'])} results for 'staff'")

    def test_semantic_search(self, service):
        """Test semantic search with embeddings"""
        result = service.semantic_search_miracles(query="معجزة النار", limit=5)
        assert "results" in result
        assert "embedding_dimension" in result
        assert result["embedding_dimension"] == 768
        print(f"✓ Semantic search passed - {len(result['results'])} results")

    # ===== Graph Visualization Tests =====

    def test_get_full_graph(self, service):
        """Test getting full miracle graph"""
        result = service.get_miracle_graph()
        assert "nodes" in result
        assert "edges" in result
        assert "total_nodes" in result
        assert "legend" in result

        # Should have different node types
        node_types = {n["type"] for n in result["nodes"]}
        assert "miracle" in node_types
        print(f"✓ Full graph passed - {result['total_nodes']} nodes, {result['total_edges']} edges")

    def test_get_centered_graph(self, service):
        """Test getting graph centered on a miracle"""
        result = service.get_miracle_graph(center_miracle_id="musa_staff_serpent")
        assert "nodes" in result

        # Find the center node
        center_found = any(n["id"] == "musa_staff_serpent" for n in result["nodes"])
        assert center_found, "Center miracle not in graph"
        print("✓ Centered graph passed")

    # ===== Feedback System Tests =====

    def test_submit_feedback(self, service):
        """Test submitting user feedback"""
        result = service.submit_feedback(
            miracle_id="musa_staff_serpent",
            user_id="test_user_123",
            feedback_type="insight",
            content_ar="ملاحظة تجريبية للاختبار",
            content_en="Test feedback for testing"
        )
        assert result.get("success") is True
        assert "feedback_id" in result
        print("✓ Submit feedback passed")

    def test_submit_feedback_invalid_miracle(self, service):
        """Test submitting feedback for nonexistent miracle"""
        result = service.submit_feedback(
            miracle_id="nonexistent",
            user_id="test_user",
            feedback_type="question",
            content_ar="سؤال"
        )
        assert "error" in result
        print("✓ Invalid miracle feedback handling passed")

    def test_get_miracle_feedback(self, service):
        """Test getting feedback for a miracle"""
        # First submit feedback
        service.submit_feedback(
            miracle_id="musa_parting_sea",
            user_id="test_user_456",
            feedback_type="addition",
            content_ar="إضافة للمحتوى"
        )

        result = service.get_miracle_feedback("musa_parting_sea")
        assert "feedback" in result
        assert "total" in result
        print("✓ Get feedback passed")

    # ===== Admin Dashboard Tests =====

    def test_admin_dashboard(self, service):
        """Test admin dashboard access"""
        result = service.get_admin_dashboard("admin")
        assert "statistics" in result
        assert "pending_feedback" in result

        stats = result["statistics"]
        assert "total_miracles" in stats
        assert "by_verification_status" in stats
        print(f"✓ Admin dashboard passed - {stats['total_miracles']} miracles")

    def test_admin_dashboard_unauthorized(self, service):
        """Test admin dashboard with unauthorized user"""
        result = service.get_admin_dashboard("regular_user")
        assert "error" in result
        print("✓ Unauthorized admin access blocked")

    def test_review_feedback(self, service):
        """Test admin reviewing feedback"""
        # First submit feedback
        submit_result = service.submit_feedback(
            miracle_id="musa_white_hand",
            user_id="test_user",
            feedback_type="correction",
            content_ar="تصحيح مقترح"
        )
        feedback_id = submit_result["feedback_id"]

        # Admin reviews it
        result = service.review_feedback(
            admin_id="admin",
            feedback_id=feedback_id,
            decision="accepted",
            notes="Good suggestion"
        )
        assert result.get("success") is True
        print("✓ Admin review feedback passed")

    # ===== Data Integrity Tests =====

    def test_miracle_has_all_fields(self, service):
        """Test that miracles have all required fields"""
        result = service.get_miracle("musa_staff_serpent")
        miracle = result["miracle"]

        required_fields = [
            "id", "name_ar", "name_en", "category", "miracle_type",
            "description_ar", "description_en", "significance_ar",
            "lessons_ar", "verses", "tafsir_references", "themes",
            "historical_context_ar", "verification_status"
        ]

        for field in required_fields:
            assert field in miracle, f"Missing field: {field}"
        print("✓ All required miracle fields present")

    def test_lessons_in_both_languages(self, service):
        """Test that miracles have lessons in both Arabic and English"""
        result = service.get_miracle("musa_parting_sea")
        miracle = result["miracle"]

        assert len(miracle["lessons_ar"]) > 0
        assert len(miracle["lessons_en"]) > 0
        assert len(miracle["lessons_ar"]) == len(miracle["lessons_en"])
        print("✓ Bilingual lessons verified")

    def test_related_miracles(self, service):
        """Test that related miracles link properly"""
        result = service.get_miracle("musa_staff_serpent")

        assert "related_miracles" in result
        assert len(result["related_miracles"]) > 0

        # Related miracles should have valid data
        for related in result["related_miracles"]:
            assert "id" in related
            assert "name_ar" in related
        print(f"✓ Related miracles passed - {len(result['related_miracles'])} related")


def run_all_tests():
    """Run all tests manually"""
    service = MiraclesService()
    test = TestMiraclesService()

    print("\n" + "="*60)
    print("Testing Miracles & Verses Service")
    print("="*60 + "\n")

    tests = [
        ("Get All Miracles", lambda: test.test_get_all_miracles(service)),
        ("Category Filter", lambda: test.test_get_all_miracles_with_category_filter(service)),
        ("Get Miracle by ID", lambda: test.test_get_miracle_by_id(service)),
        ("Nonexistent Miracle", lambda: test.test_get_nonexistent_miracle(service)),
        ("Prophet Miracles", lambda: test.test_get_miracles_by_prophet(service)),
        ("Prophets with Miracles", lambda: test.test_get_prophets_with_miracles(service)),
        ("Categories", lambda: test.test_get_miracle_categories(service)),
        ("Themes", lambda: test.test_get_miracle_themes(service)),
        ("Four Madhabs Tafsir", lambda: test.test_tafsir_from_all_madhabs(service)),
        ("Tafsir Scholar Info", lambda: test.test_tafsir_scholar_info(service)),
        ("Tafsir Sources", lambda: test.test_get_tafsir_sources(service)),
        ("Verse References", lambda: test.test_miracle_has_verses(service)),
        ("Keyword Search", lambda: test.test_keyword_search(service)),
        ("English Search", lambda: test.test_search_english(service)),
        ("Semantic Search", lambda: test.test_semantic_search(service)),
        ("Full Graph", lambda: test.test_get_full_graph(service)),
        ("Centered Graph", lambda: test.test_get_centered_graph(service)),
        ("Submit Feedback", lambda: test.test_submit_feedback(service)),
        ("Invalid Miracle Feedback", lambda: test.test_submit_feedback_invalid_miracle(service)),
        ("Get Feedback", lambda: test.test_get_miracle_feedback(service)),
        ("Admin Dashboard", lambda: test.test_admin_dashboard(service)),
        ("Unauthorized Admin", lambda: test.test_admin_dashboard_unauthorized(service)),
        ("Review Feedback", lambda: test.test_review_feedback(service)),
        ("All Required Fields", lambda: test.test_miracle_has_all_fields(service)),
        ("Bilingual Lessons", lambda: test.test_lessons_in_both_languages(service)),
        ("Related Miracles", lambda: test.test_related_miracles(service)),
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
