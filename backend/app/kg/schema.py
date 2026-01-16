"""
SurrealDB Knowledge Graph Schema Definitions.

This module defines the schema for the Quranic Knowledge Graph using SurrealQL.
All entities have provenance fields for traceability and idempotency.

RECORD ID STRATEGY:
- ayah:{sura}:{ayah}                          # e.g., ayah:18:83
- tafsir_chunk:{source}:{sura}:{range}:{hash} # e.g., tafsir_chunk:tabari:18:83-84:abc123
- story_cluster:{slug}                         # e.g., story_cluster:musa_pharaoh
- story_event:{cluster}:{event_slug}           # e.g., story_event:musa_pharaoh:staff_miracle
- person:{slug}                                # e.g., person:musa
- place:{slug}                                 # e.g., place:egypt
- concept_tag:{key}                            # e.g., concept_tag:patience
- ingest_run:{run_id}                          # e.g., ingest_run:20240106_143022_abc123
- ingest_step:{run_id}:{step_name}             # e.g., ingest_step:20240106_143022_abc123:embed_chunks
- embedding_record:{surreal_id_hash}           # Links SurrealDB to Qdrant

EDGE TYPES:
- HAS_EVENT: story_cluster -> story_event
- MENTIONS_AYAH: story_event -> ayah
- EXPLAINS: tafsir_chunk -> ayah
- SUPPORTED_BY: story_event -> tafsir_chunk
- INVOLVES: story_event -> person
- LOCATED_IN: story_event -> place
- NEXT: story_event -> story_event (chronological)
- THEMATIC_LINK: story_event -> story_event (thematic)
- TAGGED_WITH: story_event -> concept_tag
"""

# =============================================================================
# SCHEMA DEFINITIONS (SurrealQL)
# =============================================================================

SCHEMA_DEFINITIONS = """
-- ============================================================================
-- NAMESPACE AND DATABASE
-- ============================================================================
DEFINE NAMESPACE IF NOT EXISTS tadabbur;
USE NS tadabbur;
DEFINE DATABASE IF NOT EXISTS quran_kg;
USE DB quran_kg;

-- ============================================================================
-- FULL-TEXT SEARCH ANALYZERS
-- ============================================================================
-- Arabic analyzer (basic tokenization + lowercase - SurrealDB 1.5 limited stemmer support)
DEFINE ANALYZER IF NOT EXISTS arabic_analyzer TOKENIZERS blank, class FILTERS lowercase;
-- English analyzer with stemming
DEFINE ANALYZER IF NOT EXISTS english_analyzer TOKENIZERS blank, class FILTERS lowercase, snowball(english);

-- ============================================================================
-- A) CORE ENTITY TABLES (NODES)
-- ============================================================================

-- Ayah: Individual Quranic verses
DEFINE TABLE ayah SCHEMAFULL;
DEFINE FIELD sura ON ayah TYPE int ASSERT $value >= 1 AND $value <= 114;
DEFINE FIELD ayah ON ayah TYPE int ASSERT $value >= 1;
DEFINE FIELD text_ar ON ayah TYPE string;
DEFINE FIELD text_en ON ayah TYPE option<string>;
DEFINE FIELD mushaf_page ON ayah TYPE option<int>;
DEFINE FIELD juz ON ayah TYPE option<int>;
DEFINE FIELD hizb ON ayah TYPE option<int>;
-- Provenance
DEFINE FIELD _hash ON ayah TYPE string;
DEFINE FIELD _version ON ayah TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON ayah TYPE string DEFAULT "quran_uthmani";
DEFINE FIELD _created_at ON ayah TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON ayah TYPE datetime DEFAULT time::now();
DEFINE FIELD _ingest_run_id ON ayah TYPE option<string>;
-- Indexes
DEFINE INDEX ayah_sura_ayah ON ayah FIELDS sura, ayah UNIQUE;
DEFINE INDEX ayah_page ON ayah FIELDS mushaf_page;
DEFINE INDEX ayah_juz ON ayah FIELDS juz;

-- Tafsir Chunk: Segments of tafsir text linked to verses
DEFINE TABLE tafsir_chunk SCHEMAFULL;
DEFINE FIELD source_id ON tafsir_chunk TYPE string;
DEFINE FIELD source_name ON tafsir_chunk TYPE string;
DEFINE FIELD source_name_ar ON tafsir_chunk TYPE string;
DEFINE FIELD sura_no ON tafsir_chunk TYPE int ASSERT $value >= 1 AND $value <= 114;
DEFINE FIELD ayah_start ON tafsir_chunk TYPE int ASSERT $value >= 1;
DEFINE FIELD ayah_end ON tafsir_chunk TYPE int ASSERT $value >= 1;
DEFINE FIELD verse_reference ON tafsir_chunk TYPE string;
DEFINE FIELD lang ON tafsir_chunk TYPE string ASSERT $value IN ["ar", "en"];
DEFINE FIELD text ON tafsir_chunk TYPE string;
DEFINE FIELD methodology ON tafsir_chunk TYPE option<string>;
DEFINE FIELD scholarly_consensus ON tafsir_chunk TYPE option<string>;
DEFINE FIELD license_type ON tafsir_chunk TYPE option<string>;
-- Provenance
DEFINE FIELD _hash ON tafsir_chunk TYPE string;
DEFINE FIELD _version ON tafsir_chunk TYPE string;
DEFINE FIELD _source ON tafsir_chunk TYPE string;
DEFINE FIELD _retrieval_ts ON tafsir_chunk TYPE option<datetime>;
DEFINE FIELD _created_at ON tafsir_chunk TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON tafsir_chunk TYPE datetime DEFAULT time::now();
DEFINE FIELD _ingest_run_id ON tafsir_chunk TYPE option<string>;
-- Indexes
DEFINE INDEX chunk_source ON tafsir_chunk FIELDS source_id;
DEFINE INDEX chunk_verse ON tafsir_chunk FIELDS sura_no, ayah_start, ayah_end;
DEFINE INDEX chunk_hash ON tafsir_chunk FIELDS _hash;
DEFINE INDEX chunk_lang ON tafsir_chunk FIELDS lang;

-- Story Cluster: Grouping of related story events
DEFINE TABLE story_cluster SCHEMAFULL;
DEFINE FIELD slug ON story_cluster TYPE string;
DEFINE FIELD title_ar ON story_cluster TYPE string;
DEFINE FIELD title_en ON story_cluster TYPE string;
DEFINE FIELD short_title_ar ON story_cluster TYPE option<string>;
DEFINE FIELD short_title_en ON story_cluster TYPE option<string>;
DEFINE FIELD category ON story_cluster TYPE string;
DEFINE FIELD era ON story_cluster TYPE option<string>;
DEFINE FIELD era_basis ON story_cluster TYPE option<string>;
DEFINE FIELD time_description_ar ON story_cluster TYPE option<string>;
DEFINE FIELD time_description_en ON story_cluster TYPE option<string>;
DEFINE FIELD main_persons ON story_cluster TYPE array<string> DEFAULT [];
DEFINE FIELD groups ON story_cluster TYPE array<string> DEFAULT [];
DEFINE FIELD places ON story_cluster TYPE array<object> DEFAULT [];
DEFINE FIELD tags ON story_cluster TYPE array<string> DEFAULT [];
DEFINE FIELD ayah_spans ON story_cluster TYPE array<object>;
DEFINE FIELD primary_sura ON story_cluster TYPE option<int>;
DEFINE FIELD total_verses ON story_cluster TYPE option<int>;
DEFINE FIELD suras_mentioned ON story_cluster TYPE array<int> DEFAULT [];
DEFINE FIELD summary_ar ON story_cluster TYPE option<string>;
DEFINE FIELD summary_en ON story_cluster TYPE option<string>;
DEFINE FIELD lessons_ar ON story_cluster TYPE array<string> DEFAULT [];
DEFINE FIELD lessons_en ON story_cluster TYPE array<string> DEFAULT [];
DEFINE FIELD is_complete ON story_cluster TYPE bool DEFAULT false;
DEFINE FIELD event_count ON story_cluster TYPE int DEFAULT 0;
-- Provenance
DEFINE FIELD _hash ON story_cluster TYPE string;
DEFINE FIELD _version ON story_cluster TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON story_cluster TYPE string DEFAULT "curated";
DEFINE FIELD _created_at ON story_cluster TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON story_cluster TYPE datetime DEFAULT time::now();
DEFINE FIELD _ingest_run_id ON story_cluster TYPE option<string>;
-- Indexes
DEFINE INDEX cluster_slug ON story_cluster FIELDS slug UNIQUE;
DEFINE INDEX cluster_category ON story_cluster FIELDS category;
DEFINE INDEX cluster_era ON story_cluster FIELDS era;
DEFINE INDEX cluster_sura ON story_cluster FIELDS primary_sura;
-- Full-text search indexes
DEFINE INDEX cluster_title_ar_search ON story_cluster FIELDS title_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX cluster_title_en_search ON story_cluster FIELDS title_en SEARCH ANALYZER english_analyzer BM25;
DEFINE INDEX cluster_summary_ar_search ON story_cluster FIELDS summary_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX cluster_summary_en_search ON story_cluster FIELDS summary_en SEARCH ANALYZER english_analyzer BM25;

-- Story Event: Individual events within a story cluster
DEFINE TABLE story_event SCHEMAFULL;
DEFINE FIELD cluster_id ON story_event TYPE record<story_cluster>;
DEFINE FIELD slug ON story_event TYPE string;
DEFINE FIELD title_ar ON story_event TYPE string;
DEFINE FIELD title_en ON story_event TYPE string;
DEFINE FIELD narrative_role ON story_event TYPE string;
DEFINE FIELD chronological_index ON story_event TYPE int;
DEFINE FIELD is_entry_point ON story_event TYPE bool DEFAULT false;
DEFINE FIELD sura_no ON story_event TYPE int ASSERT $value >= 1 AND $value <= 114;
DEFINE FIELD ayah_start ON story_event TYPE int ASSERT $value >= 1;
DEFINE FIELD ayah_end ON story_event TYPE int ASSERT $value >= 1;
DEFINE FIELD verse_reference ON story_event TYPE string;
DEFINE FIELD summary_ar ON story_event TYPE string;
DEFINE FIELD summary_en ON story_event TYPE string;
DEFINE FIELD memorization_cue_ar ON story_event TYPE option<string>;
DEFINE FIELD memorization_cue_en ON story_event TYPE option<string>;
DEFINE FIELD semantic_tags ON story_event TYPE array<string> DEFAULT [];
DEFINE FIELD evidence ON story_event TYPE array<object>;
-- Provenance
DEFINE FIELD _hash ON story_event TYPE string;
DEFINE FIELD _version ON story_event TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON story_event TYPE string DEFAULT "generated";
DEFINE FIELD _created_at ON story_event TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON story_event TYPE datetime DEFAULT time::now();
DEFINE FIELD _ingest_run_id ON story_event TYPE option<string>;
-- Indexes
DEFINE INDEX event_cluster ON story_event FIELDS cluster_id;
DEFINE INDEX event_chrono ON story_event FIELDS cluster_id, chronological_index;
DEFINE INDEX event_verse ON story_event FIELDS sura_no, ayah_start, ayah_end;
DEFINE INDEX event_role ON story_event FIELDS narrative_role;
-- Full-text search indexes
DEFINE INDEX event_title_ar_search ON story_event FIELDS title_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX event_title_en_search ON story_event FIELDS title_en SEARCH ANALYZER english_analyzer BM25;
DEFINE INDEX event_summary_ar_search ON story_event FIELDS summary_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX event_summary_en_search ON story_event FIELDS summary_en SEARCH ANALYZER english_analyzer BM25;

-- Person: Named individuals in Quranic narratives
DEFINE TABLE person SCHEMAFULL;
DEFINE FIELD name_ar ON person TYPE string;
DEFINE FIELD name_en ON person TYPE string;
DEFINE FIELD kind ON person TYPE string ASSERT $value IN ["prophet", "named", "group", "angel"];
DEFINE FIELD aliases_ar ON person TYPE array<string> DEFAULT [];
DEFINE FIELD aliases_en ON person TYPE array<string> DEFAULT [];
DEFINE FIELD description_ar ON person TYPE option<string>;
DEFINE FIELD description_en ON person TYPE option<string>;
-- Provenance
DEFINE FIELD _hash ON person TYPE string;
DEFINE FIELD _version ON person TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON person TYPE string DEFAULT "curated";
DEFINE FIELD _created_at ON person TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON person TYPE datetime DEFAULT time::now();
-- Indexes
DEFINE INDEX person_name_ar ON person FIELDS name_ar;
DEFINE INDEX person_name_en ON person FIELDS name_en;
DEFINE INDEX person_kind ON person FIELDS kind;
-- Full-text search indexes
DEFINE INDEX person_name_ar_search ON person FIELDS name_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX person_name_en_search ON person FIELDS name_en SEARCH ANALYZER english_analyzer BM25;

-- Place: Locations mentioned in Quran
DEFINE TABLE place SCHEMAFULL;
DEFINE FIELD name_ar ON place TYPE string;
DEFINE FIELD name_en ON place TYPE string;
DEFINE FIELD basis ON place TYPE string ASSERT $value IN ["explicit", "tafsir_inferred", "unknown"];
DEFINE FIELD aliases_ar ON place TYPE array<string> DEFAULT [];
DEFINE FIELD aliases_en ON place TYPE array<string> DEFAULT [];
DEFINE FIELD description_ar ON place TYPE option<string>;
DEFINE FIELD description_en ON place TYPE option<string>;
DEFINE FIELD coordinates ON place TYPE option<object>;
-- Provenance
DEFINE FIELD _hash ON place TYPE string;
DEFINE FIELD _version ON place TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON place TYPE string DEFAULT "curated";
DEFINE FIELD _created_at ON place TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON place TYPE datetime DEFAULT time::now();
-- Indexes
DEFINE INDEX place_name_ar ON place FIELDS name_ar;
DEFINE INDEX place_name_en ON place FIELDS name_en;
DEFINE INDEX place_basis ON place FIELDS basis;

-- Concept Tag: Bilingual semantic tags for i18n
DEFINE TABLE concept_tag SCHEMAFULL;
DEFINE FIELD key ON concept_tag TYPE string;
DEFINE FIELD label_ar ON concept_tag TYPE string;
DEFINE FIELD label_en ON concept_tag TYPE string;
DEFINE FIELD category ON concept_tag TYPE string ASSERT $value IN ["theme", "moral", "miracle", "rhetorical", "historical", "theological"];
DEFINE FIELD description_ar ON concept_tag TYPE option<string>;
DEFINE FIELD description_en ON concept_tag TYPE option<string>;
DEFINE FIELD icon_hint ON concept_tag TYPE option<string>;
DEFINE FIELD aliases ON concept_tag TYPE array<string> DEFAULT [];
-- Provenance
DEFINE FIELD _hash ON concept_tag TYPE string;
DEFINE FIELD _version ON concept_tag TYPE string DEFAULT "1.0.0";
DEFINE FIELD _source ON concept_tag TYPE string DEFAULT "curated";
DEFINE FIELD _created_at ON concept_tag TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON concept_tag TYPE datetime DEFAULT time::now();
-- Indexes
DEFINE INDEX tag_key ON concept_tag FIELDS key UNIQUE;
DEFINE INDEX tag_category ON concept_tag FIELDS category;
-- Full-text search indexes for semantic search
DEFINE INDEX tag_label_ar_search ON concept_tag FIELDS label_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX tag_label_en_search ON concept_tag FIELDS label_en SEARCH ANALYZER english_analyzer BM25;
DEFINE INDEX tag_desc_ar_search ON concept_tag FIELDS description_ar SEARCH ANALYZER arabic_analyzer BM25;
DEFINE INDEX tag_desc_en_search ON concept_tag FIELDS description_en SEARCH ANALYZER english_analyzer BM25;

-- ============================================================================
-- B) EDGE RELATION TABLES
-- ============================================================================

-- HAS_EVENT: story_cluster -> story_event
DEFINE TABLE has_event SCHEMAFULL TYPE RELATION IN story_cluster OUT story_event;
DEFINE FIELD order ON has_event TYPE int;
DEFINE FIELD _created_at ON has_event TYPE datetime DEFAULT time::now();

-- MENTIONS_AYAH: story_event -> ayah
DEFINE TABLE mentions_ayah SCHEMAFULL TYPE RELATION IN story_event OUT ayah;
DEFINE FIELD is_primary ON mentions_ayah TYPE bool DEFAULT false;
DEFINE FIELD _created_at ON mentions_ayah TYPE datetime DEFAULT time::now();

-- EXPLAINS: tafsir_chunk -> ayah
DEFINE TABLE explains SCHEMAFULL TYPE RELATION IN tafsir_chunk OUT ayah;
DEFINE FIELD _created_at ON explains TYPE datetime DEFAULT time::now();

-- SUPPORTED_BY: story_event -> tafsir_chunk
DEFINE TABLE supported_by SCHEMAFULL TYPE RELATION IN story_event OUT tafsir_chunk;
DEFINE FIELD relevance ON supported_by TYPE float DEFAULT 1.0;
DEFINE FIELD snippet ON supported_by TYPE option<string>;
DEFINE FIELD _created_at ON supported_by TYPE datetime DEFAULT time::now();

-- INVOLVES: story_event -> person
DEFINE TABLE involves SCHEMAFULL TYPE RELATION IN story_event OUT person;
DEFINE FIELD role ON involves TYPE option<string>;
DEFINE FIELD _created_at ON involves TYPE datetime DEFAULT time::now();

-- LOCATED_IN: story_event -> place
DEFINE TABLE located_in SCHEMAFULL TYPE RELATION IN story_event OUT place;
DEFINE FIELD certainty ON located_in TYPE string DEFAULT "explicit";
DEFINE FIELD _created_at ON located_in TYPE datetime DEFAULT time::now();

-- NEXT: story_event -> story_event (chronological chain)
DEFINE TABLE next SCHEMAFULL TYPE RELATION IN story_event OUT story_event;
DEFINE FIELD gap_type ON next TYPE option<string>;
DEFINE FIELD _created_at ON next TYPE datetime DEFAULT time::now();

-- THEMATIC_LINK: story_event -> story_event (non-chronological)
DEFINE TABLE thematic_link SCHEMAFULL TYPE RELATION IN story_event OUT story_event;
DEFINE FIELD reason ON thematic_link TYPE string;
DEFINE FIELD reason_ar ON thematic_link TYPE option<string>;
DEFINE FIELD strength ON thematic_link TYPE float DEFAULT 0.5;
DEFINE FIELD confidence ON thematic_link TYPE float DEFAULT 0.5;
DEFINE FIELD evidence_chunk_ids ON thematic_link TYPE array<string> DEFAULT [];
DEFINE FIELD _created_at ON thematic_link TYPE datetime DEFAULT time::now();

-- TAGGED_WITH: story_event -> concept_tag
DEFINE TABLE tagged_with SCHEMAFULL TYPE RELATION IN story_event OUT concept_tag;
DEFINE FIELD weight ON tagged_with TYPE float DEFAULT 1.0;
DEFINE FIELD _created_at ON tagged_with TYPE datetime DEFAULT time::now();

-- ============================================================================
-- C) INGESTION TRACKING TABLES
-- ============================================================================

-- Ingest Run: Top-level execution record
DEFINE TABLE ingest_run SCHEMAFULL;
DEFINE FIELD run_id ON ingest_run TYPE string;
DEFINE FIELD started_at ON ingest_run TYPE datetime;
DEFINE FIELD finished_at ON ingest_run TYPE option<datetime>;
DEFINE FIELD git_sha ON ingest_run TYPE option<string>;
DEFINE FIELD config_hash ON ingest_run TYPE option<string>;
DEFINE FIELD status ON ingest_run TYPE string ASSERT $value IN ["running", "completed", "failed", "cancelled"];
DEFINE FIELD steps_planned ON ingest_run TYPE array<string> DEFAULT [];
DEFINE FIELD steps_completed ON ingest_run TYPE array<string> DEFAULT [];
DEFINE FIELD error_message ON ingest_run TYPE option<string>;
DEFINE FIELD metrics ON ingest_run TYPE object DEFAULT {};
-- Indexes
DEFINE INDEX run_id_idx ON ingest_run FIELDS run_id UNIQUE;
DEFINE INDEX run_status ON ingest_run FIELDS status;
DEFINE INDEX run_started ON ingest_run FIELDS started_at;

-- Ingest Step: Individual step within a run
DEFINE TABLE ingest_step SCHEMAFULL;
DEFINE FIELD run_id ON ingest_step TYPE string;
DEFINE FIELD step_name ON ingest_step TYPE string;
DEFINE FIELD started_at ON ingest_step TYPE datetime;
DEFINE FIELD finished_at ON ingest_step TYPE option<datetime>;
DEFINE FIELD status ON ingest_step TYPE string ASSERT $value IN ["pending", "running", "completed", "failed", "skipped"];
DEFINE FIELD records_processed ON ingest_step TYPE int DEFAULT 0;
DEFINE FIELD records_created ON ingest_step TYPE int DEFAULT 0;
DEFINE FIELD records_updated ON ingest_step TYPE int DEFAULT 0;
DEFINE FIELD records_skipped ON ingest_step TYPE int DEFAULT 0;
DEFINE FIELD error_message ON ingest_step TYPE option<string>;
DEFINE FIELD metrics ON ingest_step TYPE object DEFAULT {};
-- Indexes
DEFINE INDEX step_run ON ingest_step FIELDS run_id;
DEFINE INDEX step_name_idx ON ingest_step FIELDS step_name;
DEFINE INDEX step_run_name ON ingest_step FIELDS run_id, step_name UNIQUE;

-- Ingest Record State: Per-record tracking for idempotency
DEFINE TABLE ingest_record_state SCHEMAFULL;
DEFINE FIELD record_id ON ingest_record_state TYPE string;
DEFINE FIELD record_type ON ingest_record_state TYPE string;
DEFINE FIELD last_run_id ON ingest_record_state TYPE string;
DEFINE FIELD content_hash ON ingest_record_state TYPE string;
DEFINE FIELD steps ON ingest_record_state TYPE object DEFAULT {};
DEFINE FIELD _updated_at ON ingest_record_state TYPE datetime DEFAULT time::now();
-- Indexes
DEFINE INDEX record_state_id ON ingest_record_state FIELDS record_id UNIQUE;
DEFINE INDEX record_state_type ON ingest_record_state FIELDS record_type;
DEFINE INDEX record_state_hash ON ingest_record_state FIELDS content_hash;

-- ============================================================================
-- D) VECTOR EMBEDDING REGISTRY
-- ============================================================================

-- Embedding Record: Links SurrealDB records to Qdrant vectors
DEFINE TABLE embedding_record SCHEMAFULL;
DEFINE FIELD surreal_id ON embedding_record TYPE string;
DEFINE FIELD surreal_table ON embedding_record TYPE string;
DEFINE FIELD vector_db ON embedding_record TYPE string DEFAULT "qdrant";
DEFINE FIELD vector_collection ON embedding_record TYPE string;
DEFINE FIELD vector_id ON embedding_record TYPE string;
DEFINE FIELD model_name ON embedding_record TYPE string;
DEFINE FIELD model_dim ON embedding_record TYPE int;
DEFINE FIELD content_hash ON embedding_record TYPE string;
DEFINE FIELD _created_at ON embedding_record TYPE datetime DEFAULT time::now();
DEFINE FIELD _updated_at ON embedding_record TYPE datetime DEFAULT time::now();
-- Indexes
DEFINE INDEX emb_surreal ON embedding_record FIELDS surreal_id UNIQUE;
DEFINE INDEX emb_vector ON embedding_record FIELDS vector_db, vector_collection, vector_id;
DEFINE INDEX emb_hash ON embedding_record FIELDS content_hash;
""";


# =============================================================================
# COMMON GRAPH QUERIES
# =============================================================================

QUERY_STORY_WITH_EVENTS = """
-- Get story cluster with all events and their edges
LET $cluster = SELECT * FROM story_cluster WHERE id = $cluster_id;
LET $events = SELECT * FROM story_event WHERE cluster_id = $cluster_id ORDER BY chronological_index;
LET $next_edges = SELECT * FROM next WHERE in IN $events.id;
LET $thematic_edges = SELECT * FROM thematic_link WHERE in IN $events.id OR out IN $events.id;
RETURN {
    cluster: $cluster[0],
    events: $events,
    next_edges: $next_edges,
    thematic_edges: $thematic_edges
};
""";

QUERY_EVENT_WITH_CONTEXT = """
-- Get event with all related entities
LET $event = SELECT * FROM story_event WHERE id = $event_id;
LET $ayahs = SELECT * FROM ayah WHERE <-mentions_ayah<-(story_event WHERE id = $event_id);
LET $chunks = SELECT * FROM tafsir_chunk WHERE <-supported_by<-(story_event WHERE id = $event_id);
LET $persons = SELECT * FROM person WHERE <-involves<-(story_event WHERE id = $event_id);
LET $places = SELECT * FROM place WHERE <-located_in<-(story_event WHERE id = $event_id);
LET $tags = SELECT * FROM concept_tag WHERE <-tagged_with<-(story_event WHERE id = $event_id);
RETURN {
    event: $event[0],
    ayahs: $ayahs,
    tafsir_chunks: $chunks,
    persons: $persons,
    places: $places,
    tags: $tags
};
""";

QUERY_CHUNKS_FOR_AYAH = """
-- Get all tafsir chunks explaining an ayah
SELECT * FROM tafsir_chunk WHERE ->explains->(ayah WHERE id = $ayah_id);
""";

QUERY_EVENTS_FOR_PERSON = """
-- Get all events involving a person
SELECT * FROM story_event WHERE ->involves->(person WHERE id = $person_id)
ORDER BY chronological_index;
""";

QUERY_TIMELINE = """
-- Get chronological timeline for a cluster
SELECT
    id,
    chronological_index as index,
    title_ar,
    title_en,
    verse_reference,
    narrative_role,
    summary_ar,
    summary_en,
    semantic_tags,
    is_entry_point,
    memorization_cue_ar,
    memorization_cue_en
FROM story_event
WHERE cluster_id = $cluster_id
ORDER BY chronological_index;
""";

QUERY_GRAPH_NODES_EDGES = """
-- Get nodes and edges for graph visualization
LET $events = SELECT * FROM story_event WHERE cluster_id = $cluster_id;
LET $next = SELECT in, out, gap_type FROM next WHERE in IN $events.id;
LET $thematic = SELECT in, out, reason, reason_ar, strength, confidence FROM thematic_link
    WHERE in IN $events.id AND out IN $events.id;
RETURN {
    nodes: $events,
    chronological_edges: $next,
    thematic_edges: $thematic
};
""";

QUERY_HYBRID_EVIDENCE = """
-- Get evidence for a set of chunk IDs with graph context
LET $chunks = SELECT * FROM tafsir_chunk WHERE id IN $chunk_ids;
LET $ayahs = SELECT * FROM ayah WHERE <-explains<-(tafsir_chunk WHERE id IN $chunk_ids);
LET $events = SELECT * FROM story_event WHERE ->supported_by->(tafsir_chunk WHERE id IN $chunk_ids);
LET $clusters = SELECT * FROM story_cluster WHERE id IN $events.cluster_id;
RETURN {
    chunks: $chunks,
    related_ayahs: $ayahs,
    related_events: $events,
    related_clusters: $clusters
};
""";

# =============================================================================
# SCHEMA VERSION
# =============================================================================

SCHEMA_VERSION = "1.1.0"  # Added full-text search indexes for semantic search


def get_schema_sql() -> str:
    """Return the full schema definition SQL."""
    return SCHEMA_DEFINITIONS


def get_query(name: str) -> str:
    """Get a named query template."""
    queries = {
        "story_with_events": QUERY_STORY_WITH_EVENTS,
        "event_with_context": QUERY_EVENT_WITH_CONTEXT,
        "chunks_for_ayah": QUERY_CHUNKS_FOR_AYAH,
        "events_for_person": QUERY_EVENTS_FOR_PERSON,
        "timeline": QUERY_TIMELINE,
        "graph_nodes_edges": QUERY_GRAPH_NODES_EDGES,
        "hybrid_evidence": QUERY_HYBRID_EVIDENCE,
    }
    if name not in queries:
        raise ValueError(f"Unknown query: {name}. Available: {list(queries.keys())}")
    return queries[name]
