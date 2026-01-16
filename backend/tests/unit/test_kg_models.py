"""
Unit tests for Knowledge Graph Pydantic models.

Tests validation rules for:
- Arabic content requirements
- Ayah range validation
- Provenance fields
- Evidence requirements
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.kg.models import (
    Ayah,
    TafsirChunk,
    StoryCluster,
    StoryEvent,
    Person,
    Place,
    ConceptTag,
    EvidenceSource,
    AyahSpan,
    GraphNode,
    GraphEdge,
    VectorHit,
    GraphPath,
    HybridEvidenceItem,
    IngestRun,
    IngestStep,
    IngestStatus,
    StepStatus,
    PersonKind,
    PlaceBasis,
    TagCategory,
    StoryCategory,
    NarrativeRole,
)


# =============================================================================
# AYAH MODEL TESTS
# =============================================================================

class TestAyahModel:
    """Tests for Ayah model validation."""

    def test_valid_ayah(self):
        """Valid ayah should pass validation."""
        ayah = Ayah(
            sura=18,
            ayah=83,
            text_ar="وَيَسْأَلُونَكَ عَن ذِي الْقَرْنَيْنِ",
        )
        assert ayah.sura == 18
        assert ayah.ayah == 83
        assert len(ayah.text_ar) > 0

    def test_invalid_sura_too_low(self):
        """Sura number < 1 should fail."""
        with pytest.raises(ValidationError) as exc_info:
            Ayah(sura=0, ayah=1, text_ar="آية")
        assert "sura" in str(exc_info.value)

    def test_invalid_sura_too_high(self):
        """Sura number > 114 should fail."""
        with pytest.raises(ValidationError) as exc_info:
            Ayah(sura=115, ayah=1, text_ar="آية")
        assert "sura" in str(exc_info.value)

    def test_invalid_aya_too_low(self):
        """Aya number < 1 should fail."""
        with pytest.raises(ValidationError) as exc_info:
            Ayah(sura=1, ayah=0, text_ar="آية")
        assert "ayah" in str(exc_info.value).lower()

    def test_text_ar_requires_arabic(self):
        """text_ar must contain Arabic characters."""
        with pytest.raises(ValidationError) as exc_info:
            Ayah(sura=1, ayah=1, text_ar="English only")
        assert "Arabic" in str(exc_info.value)

    def test_optional_fields(self):
        """Optional fields should have sensible defaults."""
        ayah = Ayah(sura=1, ayah=1, text_ar="بسم الله")
        assert ayah.text_en is None
        assert ayah.juz is None
        assert ayah.mushaf_page is None


# =============================================================================
# TAFSIR CHUNK TESTS
# =============================================================================

class TestTafsirChunkModel:
    """Tests for TafsirChunk model validation."""

    def test_valid_chunk(self):
        """Valid chunk should pass validation."""
        chunk = TafsirChunk(
            source_id="tabari",
            source_name="Tafsir al-Tabari",
            source_name_ar="تفسير الطبري",
            sura_no=18,
            ayah_start=83,
            ayah_end=84,
            verse_reference="18:83-84",
            lang="ar",
            text="تفسير الآية",
        )
        assert chunk.source_id == "tabari"
        assert chunk.sura_no == 18

    def test_invalid_lang(self):
        """Lang must be 'ar' or 'en'."""
        with pytest.raises(ValidationError) as exc_info:
            TafsirChunk(
                source_id="test",
                source_name="Test",
                source_name_ar="اختبار",
                sura_no=1,
                ayah_start=1,
                ayah_end=1,
                verse_reference="1:1",
                lang="fr",  # Invalid
                text="test",
            )
        assert "lang" in str(exc_info.value)

    def test_ayah_range_validation(self):
        """ayah_end must be >= ayah_start."""
        with pytest.raises(ValidationError) as exc_info:
            TafsirChunk(
                source_id="test",
                source_name="Test",
                source_name_ar="اختبار",
                sura_no=1,
                ayah_start=5,
                ayah_end=3,  # Invalid: end < start
                verse_reference="1:5-3",
                lang="ar",
                text="test",
            )
        assert "ayah_end" in str(exc_info.value)


# =============================================================================
# STORY CLUSTER TESTS
# =============================================================================

class TestStoryClusterModel:
    """Tests for StoryCluster model validation."""

    def test_valid_cluster(self):
        """Valid cluster should pass validation."""
        cluster = StoryCluster(
            slug="dhul_qarnayn",
            title_ar="قصة ذي القرنين",
            title_en="Story of Dhul-Qarnayn",
            category=StoryCategory.NAMED_CHAR,
        )
        assert cluster.slug == "dhul_qarnayn"
        assert "القرنين" in cluster.title_ar

    def test_invalid_slug_uppercase(self):
        """Slug must be lowercase with underscores only."""
        with pytest.raises(ValidationError) as exc_info:
            StoryCluster(
                slug="DhulQarnayn",  # Invalid: has uppercase
                title_ar="قصة",
                title_en="Story",
                category=StoryCategory.PROPHET,
            )
        assert "slug" in str(exc_info.value)

    def test_invalid_slug_spaces(self):
        """Slug cannot contain spaces."""
        with pytest.raises(ValidationError) as exc_info:
            StoryCluster(
                slug="dhul qarnayn",  # Invalid: has space
                title_ar="قصة",
                title_en="Story",
                category=StoryCategory.PROPHET,
            )
        assert "slug" in str(exc_info.value)

    def test_valid_slug_with_numbers(self):
        """Slug can contain numbers."""
        cluster = StoryCluster(
            slug="story_part_1",
            title_ar="قصة",
            title_en="Story",
            category=StoryCategory.PARABLE,
        )
        assert cluster.slug == "story_part_1"

    def test_title_ar_requires_arabic(self):
        """title_ar must contain Arabic characters."""
        with pytest.raises(ValidationError) as exc_info:
            StoryCluster(
                slug="test",
                title_ar="Only English",  # Invalid
                title_en="Story",
                category=StoryCategory.PROPHET,
            )
        assert "Arabic" in str(exc_info.value)

    def test_ayah_spans_structure(self):
        """Ayah spans should use AyahSpan model."""
        cluster = StoryCluster(
            slug="test_story",
            title_ar="قصة",
            title_en="Story",
            category=StoryCategory.PROPHET,
            ayah_spans=[
                AyahSpan(sura=18, start=83, end=98),
                AyahSpan(sura=21, start=51, end=73),
            ],
        )
        assert len(cluster.ayah_spans) == 2
        assert cluster.ayah_spans[0].sura == 18


# =============================================================================
# STORY EVENT TESTS
# =============================================================================

class TestStoryEventModel:
    """Tests for StoryEvent model validation."""

    def test_valid_event_with_evidence(self):
        """Valid event with evidence should pass."""
        event = StoryEvent(
            cluster_id="story_cluster:dhul_qarnayn",
            slug="journey_east",
            title_ar="رحلته إلى المشرق",
            title_en="Journey to the East",
            narrative_role=NarrativeRole.MIGRATION,
            chronological_index=1,
            sura_no=18,
            ayah_start=83,
            ayah_end=86,
            verse_reference="18:83-86",
            summary_ar="سافر ذو القرنين إلى المشرق",
            summary_en="Dhul-Qarnayn traveled east",
            evidence=[
                EvidenceSource(
                    source_id="tabari",
                    chunk_id="chunk:abc123",
                    snippet="قال الطبري...",
                )
            ],
        )
        assert event.slug == "journey_east"
        assert len(event.evidence) == 1

    def test_arabic_summary_required(self):
        """Summary in Arabic must contain Arabic characters."""
        with pytest.raises(ValidationError) as exc_info:
            StoryEvent(
                cluster_id="story_cluster:test",
                slug="test_event",
                title_ar="عنوان",
                title_en="Title",
                narrative_role=NarrativeRole.INTRODUCTION,
                chronological_index=1,
                sura_no=1,
                ayah_start=1,
                ayah_end=1,
                verse_reference="1:1",
                summary_ar="This is only English text",  # Invalid
                summary_en="Summary",
                evidence=[
                    EvidenceSource(source_id="test", chunk_id="chunk:1"),
                ],
            )
        assert "Arabic" in str(exc_info.value)

    def test_valid_arabic_summary(self):
        """Summary with Arabic text should pass."""
        event = StoryEvent(
            cluster_id="story_cluster:test",
            slug="test_event",
            title_ar="عنوان",
            title_en="Title",
            narrative_role=NarrativeRole.DIALOGUE,
            chronological_index=1,
            sura_no=1,
            ayah_start=1,
            ayah_end=1,
            verse_reference="1:1",
            summary_ar="ملخص الحدث بالعربية",
            summary_en="Summary in English",
            evidence=[
                EvidenceSource(source_id="test", chunk_id="chunk:1"),
            ],
        )
        assert "ملخص" in event.summary_ar


# =============================================================================
# PERSON MODEL TESTS
# =============================================================================

class TestPersonModel:
    """Tests for Person model validation."""

    def test_valid_person(self):
        """Valid person should pass validation."""
        person = Person(
            slug="dhul_qarnayn",
            name_ar="ذو القرنين",
            name_en="Dhul-Qarnayn",
            kind=PersonKind.NAMED,
        )
        assert person.slug == "dhul_qarnayn"
        assert "القرنين" in person.name_ar

    def test_prophet_kind(self):
        """Person with prophet kind should work."""
        person = Person(
            slug="musa",
            name_ar="موسى",
            name_en="Moses",
            kind=PersonKind.PROPHET,
        )
        assert person.kind == PersonKind.PROPHET


# =============================================================================
# PLACE MODEL TESTS
# =============================================================================

class TestPlaceModel:
    """Tests for Place model validation."""

    def test_valid_place(self):
        """Valid place should pass validation."""
        place = Place(
            slug="setting_sun",
            name_ar="مغرب الشمس",
            name_en="Setting of the Sun",
            basis=PlaceBasis.EXPLICIT,
        )
        assert place.slug == "setting_sun"

    def test_coordinates_optional(self):
        """Coordinates should be optional."""
        place = Place(
            slug="makkah",
            name_ar="مكة",
            name_en="Makkah",
            basis=PlaceBasis.EXPLICIT,
            coordinates={"lat": 21.4225, "lng": 39.8262},
        )
        assert place.coordinates["lat"] == 21.4225


# =============================================================================
# CONCEPT TAG TESTS
# =============================================================================

class TestConceptTagModel:
    """Tests for ConceptTag model validation."""

    def test_valid_concept(self):
        """Valid concept tag should pass."""
        concept = ConceptTag(
            key="divine_power",
            label_ar="القدرة الإلهية",
            label_en="Divine Power",
            category=TagCategory.THEOLOGICAL,
        )
        assert concept.key == "divine_power"
        assert "القدرة" in concept.label_ar

    def test_arabic_label_required(self):
        """Arabic label must contain Arabic characters."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptTag(
                key="test",
                label_ar="Only English",  # Invalid
                label_en="Test",
                category=TagCategory.THEME,
            )
        assert "Arabic" in str(exc_info.value)


# =============================================================================
# AYAH SPAN TESTS
# =============================================================================

class TestAyahSpanModel:
    """Tests for AyahSpan model validation."""

    def test_valid_span(self):
        """Valid span should pass."""
        span = AyahSpan(sura=18, start=83, end=98)
        assert span.sura == 18
        assert span.start == 83
        assert span.end == 98

    def test_single_ayah_span(self):
        """Single ayah span (start == end) should pass."""
        span = AyahSpan(sura=1, start=1, end=1)
        assert span.to_reference() == "1:1"

    def test_range_reference(self):
        """Range should generate proper reference."""
        span = AyahSpan(sura=18, start=83, end=98)
        assert span.to_reference() == "18:83-98"

    def test_invalid_range(self):
        """end < start should fail."""
        with pytest.raises(ValidationError) as exc_info:
            AyahSpan(sura=18, start=98, end=83)
        assert "end" in str(exc_info.value)


# =============================================================================
# GRAPH VISUALIZATION TESTS
# =============================================================================

class TestGraphVisualizationModels:
    """Tests for graph visualization models."""

    def test_graph_node(self):
        """GraphNode should serialize correctly."""
        node = GraphNode(
            id="story_event:dhul_qarnayn:journey_east",
            type="event",
            label="رحلته إلى المشرق",
            data={"chronological_index": 1},
            position={"x": 0, "y": 120},
        )
        assert node.id.startswith("story_event:")
        assert node.position["y"] == 120

    def test_graph_edge(self):
        """GraphEdge should capture relationship."""
        edge = GraphEdge(
            source="story_event:e1",
            target="story_event:e2",
            type="next",
            label="immediate",
            data={"is_chronological": True},
        )
        assert edge.type == "next"
        assert edge.data["is_chronological"]


# =============================================================================
# HYBRID RETRIEVAL TESTS
# =============================================================================

class TestHybridRetrievalModels:
    """Tests for hybrid retrieval models."""

    def test_vector_hit(self):
        """VectorHit should capture vector search result."""
        hit = VectorHit(
            chunk_id="tafsir_chunk:tabari:18:83:abc",
            score=0.89,
            rank=1,
        )
        assert hit.score == 0.89
        assert hit.rank == 1

    def test_graph_path(self):
        """GraphPath should capture traversal."""
        path = GraphPath(
            chunk_id="chunk:abc",
            ayah_ids=["ayah:18:83", "ayah:18:84"],
            event_ids=["story_event:dq:e1"],
            cluster_id="story_cluster:dhul_qarnayn",
        )
        assert len(path.ayah_ids) == 2
        assert path.cluster_id is not None

    def test_hybrid_evidence_item(self):
        """HybridEvidenceItem should combine vector and graph."""
        evidence = HybridEvidenceItem(
            chunk_id="chunk:abc",
            source_id="tabari",
            source_name="Tafsir al-Tabari",
            source_name_ar="تفسير الطبري",
            verse_reference="18:83-84",
            sura_no=18,
            ayah_start=83,
            ayah_end=84,
            content="تفسير الآية",
            relevance_score=0.89,
            vector_rank=1,
            vector_score=0.89,
        )
        assert evidence.relevance_score == 0.89
        assert evidence.source_id == "tabari"


# =============================================================================
# INGESTION TRACKING TESTS
# =============================================================================

class TestIngestTrackingModels:
    """Tests for ingestion tracking models."""

    def test_ingest_run(self):
        """IngestRun should track run metadata."""
        run = IngestRun(
            run_id="20240115_123456_abc123",
            started_at=datetime.utcnow(),
            status=IngestStatus.RUNNING,
            steps_planned=["embed_chunks", "upsert_qdrant"],
            steps_completed=[],
        )
        assert run.status == IngestStatus.RUNNING
        assert len(run.steps_planned) == 2
        assert run.finished_at is None

    def test_ingest_step(self):
        """IngestStep should track step progress."""
        step = IngestStep(
            run_id="run_123",
            step_name="embed_chunks",
            started_at=datetime.utcnow(),
            status=StepStatus.RUNNING,
        )
        assert step.status == StepStatus.RUNNING
        assert step.records_processed == 0

    def test_ingest_step_completed(self):
        """Completed step should have metrics."""
        step = IngestStep(
            run_id="run_123",
            step_name="embed_chunks",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            status=StepStatus.COMPLETED,
            records_processed=1000,
            records_created=500,
            records_updated=300,
            records_skipped=200,
        )
        assert step.status == StepStatus.COMPLETED
        assert step.records_processed == 1000
        assert step.records_created + step.records_updated + step.records_skipped == 1000


# =============================================================================
# PROVENANCE TESTS
# =============================================================================

class TestProvenanceFields:
    """Tests for provenance tracking in models."""

    def test_story_cluster_provenance(self):
        """StoryCluster should have provenance fields."""
        cluster = StoryCluster(
            slug="test_story",
            title_ar="قصة",
            title_en="Story",
            category=StoryCategory.PROPHET,
        )
        assert cluster.created_at is not None
        assert cluster.version == "1.0.0"

    def test_ayah_provenance(self):
        """Ayah should have provenance fields."""
        ayah = Ayah(
            sura=1,
            ayah=1,
            text_ar="بسم الله الرحمن الرحيم",
        )
        assert ayah.created_at is not None
        assert ayah.source == "curated"
