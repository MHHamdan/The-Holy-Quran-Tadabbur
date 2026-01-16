"""
Story Atlas Tests - Ensuring data quality and graph consistency.

TEST REQUIREMENTS:
==================
1. Atlas contains >= 30 clusters
2. Each cluster has >= 1 ayah_span
3. Each event has non-empty title + summary
4. Each event has >= 1 evidence snippet from enabled source
5. Graph has valid chronological path (no cycles in chrono edges)
6. Place/time basis rules enforced (explicit/inferred/unknown)

These tests validate the Story Atlas dataset quality.
"""
import json
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Test database URL
DATABASE_URL = "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for tests."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestClusterCoverage:
    """Test cluster coverage requirements."""

    def test_atlas_has_at_least_30_clusters(self, db_session):
        """Atlas must contain >= 30 clusters."""
        result = db_session.execute(text("SELECT COUNT(*) FROM story_clusters"))
        count = result.scalar()
        assert count >= 30, f"Expected >= 30 clusters, got {count}"

    def test_all_clusters_have_ayah_spans(self, db_session):
        """Every cluster must have at least 1 ayah span."""
        result = db_session.execute(text("""
            SELECT id, title_en, ayah_spans
            FROM story_clusters
            WHERE ayah_spans IS NULL OR jsonb_array_length(ayah_spans) = 0
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Clusters without ayah_spans: {[r[0] for r in missing]}"

    def test_all_clusters_have_category(self, db_session):
        """Every cluster must have a category."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE category IS NULL OR category = ''
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Clusters without category: {[r[0] for r in missing]}"

    def test_clusters_have_titles(self, db_session):
        """Every cluster must have both Arabic and English titles."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters
            WHERE title_ar IS NULL OR title_en IS NULL
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Clusters without titles: {[r[0] for r in missing]}"


class TestClusterCategories:
    """Test cluster category distribution."""

    def test_has_prophet_stories(self, db_session):
        """Atlas must have prophet stories."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_clusters WHERE category = 'prophet'
        """))
        count = result.scalar()
        assert count >= 5, f"Expected >= 5 prophet clusters, got {count}"

    def test_has_nation_stories(self, db_session):
        """Atlas must have nation stories."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_clusters WHERE category = 'nation'
        """))
        count = result.scalar()
        assert count >= 2, f"Expected >= 2 nation clusters, got {count}"

    def test_has_parables(self, db_session):
        """Atlas must have parables."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_clusters WHERE category = 'parable'
        """))
        count = result.scalar()
        assert count >= 1, f"Expected >= 1 parable cluster, got {count}"


class TestEventQuality:
    """Test event data quality."""

    def test_events_have_titles(self, db_session):
        """Every event must have both Arabic and English titles."""
        result = db_session.execute(text("""
            SELECT id FROM story_events
            WHERE title_ar IS NULL OR title_ar = ''
               OR title_en IS NULL OR title_en = ''
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without titles: {[r[0] for r in missing]}"

    def test_events_have_summaries(self, db_session):
        """Every event must have summaries."""
        result = db_session.execute(text("""
            SELECT id FROM story_events
            WHERE summary_ar IS NULL OR summary_ar = ''
               OR summary_en IS NULL OR summary_en = ''
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without summaries: {[r[0] for r in missing]}"

    def test_events_have_narrative_role(self, db_session):
        """Every event must have a narrative role."""
        result = db_session.execute(text("""
            SELECT id FROM story_events
            WHERE narrative_role IS NULL OR narrative_role = ''
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without narrative_role: {[r[0] for r in missing]}"

    def test_events_have_chronological_index(self, db_session):
        """Every event must have a chronological index."""
        result = db_session.execute(text("""
            SELECT id FROM story_events WHERE chronological_index IS NULL
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without chronological_index: {[r[0] for r in missing]}"

    def test_events_have_verse_reference(self, db_session):
        """Every event must have valid verse reference."""
        result = db_session.execute(text("""
            SELECT id FROM story_events
            WHERE sura_no IS NULL OR aya_start IS NULL OR aya_end IS NULL
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without verse reference: {[r[0] for r in missing]}"


class TestEvidenceGrounding:
    """Test that all events have evidence grounding."""

    def test_all_events_have_evidence(self, db_session):
        """Every event must have at least 1 evidence citation."""
        result = db_session.execute(text("""
            SELECT id, evidence FROM story_events
            WHERE evidence IS NULL OR jsonb_array_length(evidence) = 0
        """))
        missing = result.fetchall()
        assert len(missing) == 0, f"Events without evidence: {[r[0] for r in missing]}"

    def test_evidence_has_source_id(self, db_session):
        """Each evidence item must have a source_id."""
        result = db_session.execute(text("""
            SELECT id, evidence FROM story_events
            WHERE evidence IS NOT NULL AND jsonb_array_length(evidence) > 0
        """))
        events = result.fetchall()

        missing_source = []
        for event_id, evidence in events:
            for ev in evidence:
                if not ev.get("source_id"):
                    missing_source.append(event_id)
                    break

        assert len(missing_source) == 0, f"Events with evidence missing source_id: {missing_source}"


class TestChronologicalDAG:
    """Test that chronological edges form a DAG (no cycles)."""

    def test_chronological_edges_form_dag(self, db_session):
        """Chronological edges must not form cycles."""
        # Get all chronological edges
        result = db_session.execute(text("""
            SELECT source_event_id, target_event_id
            FROM event_connections
            WHERE is_chronological = true
        """))
        edges = result.fetchall()

        # Build adjacency list
        adj = {}
        all_nodes = set()
        for source, target in edges:
            if source not in adj:
                adj[source] = []
            adj[source].append(target)
            all_nodes.add(source)
            all_nodes.add(target)

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in all_nodes:
            if node not in visited:
                if has_cycle(node):
                    pytest.fail(f"Cycle detected in chronological edges starting from {node}")

    def test_chronological_order_consistent(self, db_session):
        """Chronological edges must respect chronological_index ordering."""
        result = db_session.execute(text("""
            SELECT
                ec.source_event_id,
                ec.target_event_id,
                se_source.chronological_index as source_idx,
                se_target.chronological_index as target_idx
            FROM event_connections ec
            JOIN story_events se_source ON ec.source_event_id = se_source.id
            JOIN story_events se_target ON ec.target_event_id = se_target.id
            WHERE ec.is_chronological = true
              AND se_source.chronological_index >= se_target.chronological_index
        """))
        violations = result.fetchall()

        assert len(violations) == 0, f"Chronological order violations: {violations}"


class TestPlaceTimeBasis:
    """Test that place/time basis rules are enforced."""

    def test_era_basis_is_valid(self, db_session):
        """Era basis must be explicit, inferred, or unknown."""
        valid_bases = ['explicit', 'inferred', 'unknown']
        result = db_session.execute(text("""
            SELECT id, era_basis FROM story_clusters
            WHERE era_basis IS NOT NULL AND era_basis NOT IN ('explicit', 'inferred', 'unknown')
        """))
        invalid = result.fetchall()
        assert len(invalid) == 0, f"Invalid era_basis values: {invalid}"

    def test_places_have_basis(self, db_session):
        """Each place must have a basis (explicit, inferred, or unknown)."""
        result = db_session.execute(text("""
            SELECT id, places FROM story_clusters
            WHERE places IS NOT NULL AND jsonb_array_length(places) > 0
        """))
        clusters = result.fetchall()

        missing_basis = []
        for cluster_id, places in clusters:
            for place in places:
                if "basis" not in place:
                    missing_basis.append(f"{cluster_id}: {place.get('name', 'unknown')}")

        assert len(missing_basis) == 0, f"Places without basis: {missing_basis}"


class TestAlKahfCoverage:
    """Test that Al-Kahf stories are covered (as per requirements)."""

    def test_has_cave_sleepers(self, db_session):
        """Atlas must have Cave Sleepers story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_cave_sleepers'
        """))
        assert result.fetchone() is not None, "Missing cluster_cave_sleepers"

    def test_has_two_gardens(self, db_session):
        """Atlas must have Two Gardens parable."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_two_gardens'
        """))
        assert result.fetchone() is not None, "Missing cluster_two_gardens"

    def test_has_musa_khidr(self, db_session):
        """Atlas must have Musa & Khidr story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_musa_khidr'
        """))
        assert result.fetchone() is not None, "Missing cluster_musa_khidr"

    def test_has_dhulqarnayn(self, db_session):
        """Atlas must have Dhul-Qarnayn story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_dhulqarnayn'
        """))
        assert result.fetchone() is not None, "Missing cluster_dhulqarnayn"


class TestMajorStories:
    """Test that major stories are present."""

    def test_has_yusuf(self, db_session):
        """Atlas must have Yusuf story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_yusuf'
        """))
        assert result.fetchone() is not None, "Missing cluster_yusuf"

    def test_has_musa_pharaoh(self, db_session):
        """Atlas must have Musa & Pharaoh story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_musa_pharaoh'
        """))
        assert result.fetchone() is not None, "Missing cluster_musa_pharaoh"

    def test_has_nuh(self, db_session):
        """Atlas must have Nuh story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_nuh'
        """))
        assert result.fetchone() is not None, "Missing cluster_nuh"

    def test_has_ibrahim(self, db_session):
        """Atlas must have Ibrahim story."""
        result = db_session.execute(text("""
            SELECT id FROM story_clusters WHERE id = 'cluster_ibrahim'
        """))
        assert result.fetchone() is not None, "Missing cluster_ibrahim"


class TestEventCounts:
    """Test event counts for key stories."""

    def test_yusuf_has_events(self, db_session):
        """Yusuf cluster must have events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE cluster_id = 'cluster_yusuf'
        """))
        count = result.scalar()
        assert count >= 10, f"Expected >= 10 Yusuf events, got {count}"

    def test_dhulqarnayn_has_events(self, db_session):
        """Dhul-Qarnayn cluster must have events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE cluster_id = 'cluster_dhulqarnayn'
        """))
        count = result.scalar()
        assert count >= 6, f"Expected >= 6 Dhul-Qarnayn events, got {count}"

    def test_nuh_has_events(self, db_session):
        """Nuh cluster must have events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE cluster_id = 'cluster_nuh'
        """))
        count = result.scalar()
        assert count >= 5, f"Expected >= 5 Nuh events, got {count}"


class TestNarrativeRoles:
    """Test narrative role distribution."""

    def test_has_introduction_events(self, db_session):
        """Atlas must have introduction events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE narrative_role = 'introduction'
        """))
        count = result.scalar()
        assert count >= 5, f"Expected >= 5 introduction events, got {count}"

    def test_has_trial_events(self, db_session):
        """Atlas must have trial events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE narrative_role = 'trial'
        """))
        count = result.scalar()
        assert count >= 3, f"Expected >= 3 trial events, got {count}"

    def test_has_outcome_events(self, db_session):
        """Atlas must have outcome events."""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM story_events WHERE narrative_role = 'outcome'
        """))
        count = result.scalar()
        assert count >= 5, f"Expected >= 5 outcome events, got {count}"


class TestEntryPoints:
    """Test entry point requirements."""

    def test_clusters_with_events_have_entry_point(self, db_session):
        """Clusters with events should have an entry point."""
        result = db_session.execute(text("""
            SELECT cluster_id
            FROM story_events
            GROUP BY cluster_id
            HAVING COUNT(*) > 0
               AND SUM(CASE WHEN is_entry_point THEN 1 ELSE 0 END) = 0
        """))
        missing = result.fetchall()
        # This is a warning, not a hard failure
        if len(missing) > 0:
            print(f"Warning: Clusters without explicit entry points: {[r[0] for r in missing]}")
