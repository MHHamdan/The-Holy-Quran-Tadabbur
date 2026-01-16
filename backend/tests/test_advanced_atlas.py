"""
Tests for Advanced Atlas Service - FANG Level Features
"""
import pytest
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from app.services.advanced_atlas_service import AdvancedAtlasService


class TestAdvancedAtlasService:
    """Test suite for Advanced Atlas Service"""

    @pytest.fixture
    def service(self):
        return AdvancedAtlasService()

    # ===== Verification Pipeline Tests =====

    def test_create_verification_task(self, service):
        """Test creating verification task"""
        result = service.create_verification_task(
            story_id="musa",
            task_type="accuracy",
            issues_found=["Missing tafsir reference"],
            ai_confidence=0.75
        )
        assert result.get("success") is True
        assert "task_id" in result
        print("✓ Create verification task passed")

    def test_get_verification_queue(self, service):
        """Test getting verification queue"""
        # First create a task
        service.create_verification_task(
            story_id="adam",
            task_type="completeness",
            issues_found=["Summary too short"],
            ai_confidence=0.6
        )

        result = service.get_verification_queue(admin_id="admin")
        assert "queue" in result
        assert "total_pending" in result
        print(f"✓ Verification queue passed - {result['total_pending']} pending")

    def test_flag_story_for_review(self, service):
        """Test flagging story for review"""
        result = service.flag_story_for_review(
            story_id="ibrahim",
            user_id="test_user",
            reason="Incomplete events",
            details="Missing the story of building Kaaba"
        )
        assert result.get("success") is True
        print("✓ Flag story passed")

    def test_auto_verify_story(self, service):
        """Test auto verification"""
        result = service.auto_verify_story("musa")
        assert "ai_confidence" in result
        assert "issues_found" in result
        assert "recommendation" in result
        print(f"✓ Auto verify passed - confidence: {result['ai_confidence']}")

    # ===== Semantic Search Tests =====

    def test_detect_query_intent(self, service):
        """Test query intent detection"""
        # Test story search intent
        result = service.detect_query_intent("قصة موسى")
        assert "primary_intent" in result
        assert "detected_concepts" in result
        print(f"✓ Intent detection passed - intent: {result['primary_intent']}")

    def test_semantic_search(self, service):
        """Test semantic search"""
        result = service.semantic_search("الصبر والتوكل", limit=5)
        assert "results" in result
        assert "intent" in result
        print(f"✓ Semantic search passed - {len(result['results'])} results")

    def test_expand_query(self, service):
        """Test query expansion"""
        result = service.expand_query("صبر")
        assert "expanded_queries" in result
        assert "related_concepts" in result
        assert len(result["expanded_queries"]) > 1
        print(f"✓ Query expansion passed - {len(result['expanded_queries'])} expansions")

    # ===== Personalization Tests =====

    def test_create_user_profile(self, service):
        """Test creating user profile"""
        result = service.create_user_profile(
            user_id="test_learner",
            learning_goal="story_exploration",
            preferred_language="ar",
            themes_of_interest=["patience", "faith"]
        )
        assert result.get("success") is True
        print("✓ Create user profile passed")

    def test_track_interaction(self, service):
        """Test tracking user interaction"""
        # First create profile
        service.create_user_profile(
            user_id="tracker_test",
            learning_goal="comprehension"
        )

        result = service.track_interaction(
            user_id="tracker_test",
            interaction_type="complete",
            story_id="adam",
            time_spent_seconds=300,
            themes_explored=["creation", "repentance"]
        )
        assert result.get("success") is True
        print(f"✓ Track interaction passed - streak: {result.get('current_streak')}")

    def test_sm2_review(self, service):
        """Test SM2 spaced repetition"""
        # Create profile and complete a story
        service.create_user_profile(
            user_id="sm2_test",
            learning_goal="memorization"
        )
        service.track_interaction(
            user_id="sm2_test",
            interaction_type="complete",
            story_id="nuh"
        )

        result = service.calculate_sm2_review(
            user_id="sm2_test",
            story_id="nuh",
            quality=4
        )
        assert "new_interval_days" in result
        assert "next_review" in result
        print(f"✓ SM2 review passed - interval: {result['new_interval_days']} days")

    def test_personalized_recommendations(self, service):
        """Test personalized recommendations"""
        # Create profile with interests
        service.create_user_profile(
            user_id="rec_test",
            learning_goal="story_exploration",
            themes_of_interest=["patience", "trust"]
        )

        result = service.get_personalized_recommendations(user_id="rec_test", limit=5)
        assert "recommendations" in result
        assert "learning_goal" in result
        print(f"✓ Personalized recommendations passed - {len(result['recommendations'])} recs")

    def test_learning_goal_content(self, service):
        """Test learning goal content"""
        service.create_user_profile(
            user_id="goal_test",
            learning_goal="tafsir_study"
        )

        result = service.get_learning_goal_content(user_id="goal_test")
        assert "goal" in result
        assert "goal_description_ar" in result
        assert "recommended_approach" in result
        print("✓ Learning goal content passed")

    # ===== Knowledge Graph Tests =====

    def test_explore_deep_relationships(self, service):
        """Test deep relationship exploration"""
        result = service.explore_deep_relationships(
            entity_id="musa",
            entity_type="prophet",
            depth=2
        )
        assert "entity" in result
        assert "direct_connections" in result
        print("✓ Deep relationships passed")

    def test_theme_progression(self, service):
        """Test theme progression"""
        result = service.get_theme_progression("patience")
        assert "theme" in result
        assert "stories_chronological" in result
        print(f"✓ Theme progression passed - {len(result['stories_chronological'])} stories")

    def test_interactive_graph_explore(self, service):
        """Test interactive graph exploration"""
        result = service.explore_graph_interactive(
            start_node="adam",
            node_type="story",
            exploration_mode="connected",
            depth=2
        )
        assert "nodes" in result
        assert "edges" in result
        print(f"✓ Interactive explore passed - {len(result['nodes'])} nodes")

    def test_thematic_journey(self, service):
        """Test thematic journey"""
        result = service.get_thematic_journey("faith")
        assert "theme" in result
        assert "path" in result
        assert "connections" in result
        print(f"✓ Thematic journey passed - {len(result['path'])} steps")

    # ===== Scalability Tests =====

    def test_cache_warmup(self, service):
        """Test cache warmup"""
        result = service.warm_up_cache(["stories", "themes"])
        assert result.get("success") is True
        assert "warmed_data_types" in result
        print(f"✓ Cache warmup passed - warmed: {result['warmed_data_types']}")

    def test_performance_stats(self, service):
        """Test performance statistics"""
        # First warm cache
        service.warm_up_cache()

        result = service.get_performance_stats()
        assert "cache_stats" in result
        assert "active_users" in result
        print(f"✓ Performance stats passed - hit rate: {result['cache_stats']['hit_rate']}")

    # ===== FANG v2 ENHANCED TESTS =====

    def test_ml_predict_verification(self, service):
        """Test ML prediction for story verification"""
        result = service.ml_predict_verification("musa")
        assert "ml_prediction_score" in result
        assert "recommendation" in result
        assert "confidence" in result
        print(f"✓ ML prediction passed - score: {result['ml_prediction_score']}")

    def test_detect_edge_cases(self, service):
        """Test edge case detection"""
        result = service.detect_edge_cases("musa")
        assert "edge_cases_detected" in result
        assert "risk_level" in result
        assert "madhab_coverage" in result
        print(f"✓ Edge case detection passed - risk: {result['risk_level']}")

    def test_auto_categorize_story(self, service):
        """Test auto-categorization with ML and edge case detection"""
        result = service.auto_categorize_story("musa")
        assert "ml_prediction" in result
        assert "edge_cases" in result
        assert "final_recommendation" in result
        print(f"✓ Auto-categorize passed - {result['final_recommendation']}")

    def test_admin_dashboard(self, service):
        """Test admin dashboard"""
        result = service.get_admin_dashboard("admin")
        assert "verification_queue" in result
        assert "statistics" in result
        assert "ml_model_status" in result
        print("✓ Admin dashboard passed")

    def test_semantic_search_with_embeddings(self, service):
        """Test AraBERT-like semantic search"""
        result = service.semantic_search_with_embeddings("صبر موسى", limit=5)
        assert "results" in result
        assert "embedding_dimension" in result
        assert result["embedding_dimension"] == 768
        print(f"✓ AraBERT semantic search passed - {len(result['results'])} results")

    def test_generate_arabert_embedding(self, service):
        """Test AraBERT embedding generation"""
        embedding = service.generate_arabert_embedding("قصة موسى والصبر")
        assert len(embedding) == 768
        print("✓ AraBERT embedding generation passed")

    def test_compute_semantic_similarity(self, service):
        """Test semantic similarity computation"""
        similarity = service.compute_semantic_similarity(
            "صبر موسى",
            "صبر أيوب"
        )
        assert 0 <= similarity <= 1
        print(f"✓ Semantic similarity passed - score: {round(similarity, 4)}")

    def test_adaptive_recommendations(self, service):
        """Test adaptive learning recommendations"""
        # First create a profile with interactions
        service.create_user_profile(
            user_id="adaptive_test",
            learning_goal="story_exploration",
            themes_of_interest=["patience", "faith"]
        )
        service.track_interaction(
            user_id="adaptive_test",
            interaction_type="complete",
            story_id="adam",
            themes_explored=["creation", "repentance"]
        )

        result = service.get_adaptive_recommendations(user_id="adaptive_test")
        assert "recommendations" in result
        assert "adaptation_factors" in result
        print(f"✓ Adaptive recommendations passed - {len(result['recommendations'])} recs")

    def test_update_learning_path(self, service):
        """Test learning path adaptation"""
        service.create_user_profile(
            user_id="path_test",
            learning_goal="comprehension"
        )

        result = service.update_learning_path(
            user_id="path_test",
            feedback_type="liked",
            story_id="musa"
        )
        assert result.get("success") is True
        print("✓ Learning path update passed")

    def test_auto_scaling_evaluation(self, service):
        """Test auto-scaling evaluation"""
        # Record some requests
        for i in range(15):
            service.record_request(f"/api/stories/{i}", 50.0 + i * 5)

        result = service.evaluate_scaling_need()
        assert "scaling_needed" in result
        assert "metrics" in result or "reason" in result
        print("✓ Auto-scaling evaluation passed")

    def test_cache_optimization_report(self, service):
        """Test cache optimization report"""
        result = service.get_cache_optimization_report()
        assert "current_hit_rate" in result
        assert "recommendations" in result
        print(f"✓ Cache optimization report passed - hit rate: {result['current_hit_rate']}")

    def test_create_graph_session(self, service):
        """Test graph session creation"""
        result = service.create_graph_session("test_user")
        assert "session_id" in result
        assert result.get("created") is True
        print("✓ Graph session creation passed")

    def test_graph_zoom(self, service):
        """Test graph zoom functionality"""
        session = service.create_graph_session("zoom_test_user")
        session_id = session["session_id"]

        result = service.graph_zoom(session_id, zoom_level=2.0, center_node="musa")
        assert result.get("zoom_level") == 2.0
        assert result.get("view_type") == "detail"
        print("✓ Graph zoom passed")

    def test_graph_explore_node(self, service):
        """Test interactive node exploration"""
        session = service.create_graph_session("explore_test_user")
        session_id = session["session_id"]

        result = service.graph_explore_node(session_id, "musa", "story", expand=True)
        assert "node" in result
        assert "connection_count" in result
        print(f"✓ Node exploration passed - {result['connection_count']} connections")

    def test_visualization_data(self, service):
        """Test visualization-ready data generation"""
        result = service.get_visualization_data(
            center_node="adam",
            node_type="story",
            depth=2,
            layout="force"
        )
        assert "nodes" in result
        assert "edges" in result
        assert "legend" in result
        print(f"✓ Visualization data passed - {len(result['nodes'])} nodes")

    def test_temporal_relationships(self, service):
        """Test temporal relationship retrieval"""
        result = service.get_temporal_relationships("musa")
        assert "predecessors" in result
        assert "successors" in result
        assert "era" in result
        print(f"✓ Temporal relationships passed - era: {result['era']}")

    def test_causal_chain(self, service):
        """Test causal chain retrieval"""
        result = service.get_causal_chain("adam_sin", direction="both")
        assert "causes" in result
        assert "effects" in result
        assert "lessons" in result
        print(f"✓ Causal chain passed - {len(result['lessons'])} lessons")

    def test_relationship_path(self, service):
        """Test BFS relationship path finding"""
        result = service.get_relationship_path("adam", "musa", max_hops=10)
        assert "found" in result
        if result["found"]:
            assert "path" in result
            print(f"✓ Relationship path passed - {len(result['path'])} hops")
        else:
            print("✓ Relationship path passed - no path in range")

    def test_explore_journey(self, service):
        """Test journey exploration"""
        result = service.explore_journey("ibrahim", journey_type="chronological")
        assert "steps" in result
        assert "total_entities" in result
        print(f"✓ Journey exploration passed - {result['total_entities']} entities")


def run_all_tests():
    """Run all tests manually"""
    service = AdvancedAtlasService()
    test = TestAdvancedAtlasService()

    print("\n" + "="*60)
    print("Testing Advanced Atlas Service - FANG Level Features v2.0")
    print("="*60 + "\n")

    tests = [
        # Original tests
        ("Create Verification Task", lambda: test.test_create_verification_task(service)),
        ("Verification Queue", lambda: test.test_get_verification_queue(service)),
        ("Flag Story", lambda: test.test_flag_story_for_review(service)),
        ("Auto Verify", lambda: test.test_auto_verify_story(service)),
        ("Intent Detection", lambda: test.test_detect_query_intent(service)),
        ("Semantic Search", lambda: test.test_semantic_search(service)),
        ("Query Expansion", lambda: test.test_expand_query(service)),
        ("Create User Profile", lambda: test.test_create_user_profile(service)),
        ("Track Interaction", lambda: test.test_track_interaction(service)),
        ("SM2 Review", lambda: test.test_sm2_review(service)),
        ("Personalized Recommendations", lambda: test.test_personalized_recommendations(service)),
        ("Learning Goal Content", lambda: test.test_learning_goal_content(service)),
        ("Deep Relationships", lambda: test.test_explore_deep_relationships(service)),
        ("Theme Progression", lambda: test.test_theme_progression(service)),
        ("Interactive Explore", lambda: test.test_interactive_graph_explore(service)),
        ("Thematic Journey", lambda: test.test_thematic_journey(service)),
        ("Cache Warmup", lambda: test.test_cache_warmup(service)),
        ("Performance Stats", lambda: test.test_performance_stats(service)),
        # FANG v2 Enhanced tests
        ("ML Prediction", lambda: test.test_ml_predict_verification(service)),
        ("Edge Case Detection", lambda: test.test_detect_edge_cases(service)),
        ("Auto Categorize", lambda: test.test_auto_categorize_story(service)),
        ("Admin Dashboard", lambda: test.test_admin_dashboard(service)),
        ("AraBERT Semantic Search", lambda: test.test_semantic_search_with_embeddings(service)),
        ("AraBERT Embedding", lambda: test.test_generate_arabert_embedding(service)),
        ("Semantic Similarity", lambda: test.test_compute_semantic_similarity(service)),
        ("Adaptive Recommendations", lambda: test.test_adaptive_recommendations(service)),
        ("Learning Path Update", lambda: test.test_update_learning_path(service)),
        ("Auto-Scaling Evaluation", lambda: test.test_auto_scaling_evaluation(service)),
        ("Cache Optimization", lambda: test.test_cache_optimization_report(service)),
        ("Graph Session", lambda: test.test_create_graph_session(service)),
        ("Graph Zoom", lambda: test.test_graph_zoom(service)),
        ("Node Exploration", lambda: test.test_graph_explore_node(service)),
        ("Visualization Data", lambda: test.test_visualization_data(service)),
        ("Temporal Relationships", lambda: test.test_temporal_relationships(service)),
        ("Causal Chain", lambda: test.test_causal_chain(service)),
        ("Relationship Path", lambda: test.test_relationship_path(service)),
        ("Journey Exploration", lambda: test.test_explore_journey(service)),
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
