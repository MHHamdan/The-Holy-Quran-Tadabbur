# Knowledge Graph Migration Plan

## PHASE 0: Current → Target Map

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CURRENT STATE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ PostgreSQL   │    │   Qdrant     │    │  On-demand   │          │
│  │  (Relational)│    │  (Vector)    │    │   Graphs     │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│  ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐          │
│  │ • stories    │    │ tafseer_     │    │ Computed at  │          │
│  │ • segments   │    │   chunks     │    │ request time │          │
│  │ • clusters   │    │ (1024-dim)   │    │ from JOINs   │          │
│  │ • events     │    │              │    │              │          │
│  │ • concepts   │    │ quran_verses │    │ No caching   │          │
│  │ • tafseer    │    │ (1024-dim)   │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                      │
│  ISSUES:                                                            │
│  ✗ No native graph traversal (expensive JOINs)                      │
│  ✗ No ingestion tracking (can't resume, no idempotency)             │
│  ✗ Vector-to-graph disconnected (separate queries needed)           │
│  ✗ Tags not bilingual (English leakage in Arabic mode)              │
│  ✗ No provenance on all records                                     │
│  ✗ No debug traceability for evidence paths                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TARGET STATE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    SurrealDB Knowledge Graph                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │ NODES                    │ EDGES                        │ │   │
│  │  │ • ayah                   │ • HAS_EVENT                  │ │   │
│  │  │ • tafsir_chunk           │ • MENTIONS_AYAH              │ │   │
│  │  │ • story_cluster          │ • EXPLAINS                   │ │   │
│  │  │ • story_event            │ • SUPPORTED_BY               │ │   │
│  │  │ • person                 │ • INVOLVES                   │ │   │
│  │  │ • place                  │ • LOCATED_IN                 │ │   │
│  │  │ • concept_tag            │ • NEXT (chronological)       │ │   │
│  │  │                          │ • THEMATIC_LINK              │ │   │
│  │  └─────────────────────────────────────────────────────────┘ │   │
│  │                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │ INGESTION TRACKING                                      │ │   │
│  │  │ • ingest_run (run_id, git_sha, timestamps)              │ │   │
│  │  │ • ingest_step (run_id, step_name, metrics)              │ │   │
│  │  │ • ingest_record_state (record hash, step status)        │ │   │
│  │  └─────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           │ surreal_id link                          │
│                           ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        Qdrant Vectors                         │   │
│  │  • tafseer_chunks (with surreal_id in payload)               │   │
│  │  • quran_verses                                               │   │
│  │  • EmbeddingRegistry in SurrealDB tracks all embeddings      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   Hybrid Retrieval Pipeline                   │   │
│  │  1. Vector search → top K chunks                              │   │
│  │  2. Graph expansion → neighbors via edges                     │   │
│  │  3. Combined scoring → vector_sim + graph_relevance           │   │
│  │  4. Evidence tracing → full path from query to answer         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  BENEFITS:                                                          │
│  ✓ Native graph traversal (O(1) edge lookup)                        │
│  ✓ Idempotent ingestion with hash-based skip                        │
│  ✓ Vector→graph bridge via surreal_id                               │
│  ✓ Full i18n with concept_tag bilingual labels                      │
│  ✓ Provenance on every record                                       │
│  ✓ Debug endpoint showing full evidence path                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Migration Strategy

```
STEP 1: Add SurrealDB alongside PostgreSQL (parallel write)
        PostgreSQL remains source of truth initially

STEP 2: Build ingestion pipeline that writes to both
        Track record hashes for idempotency

STEP 3: Implement vector→graph bridge
        Update Qdrant payloads with surreal_id

STEP 4: Switch retrieval to hybrid (vector + graph)
        PostgreSQL becomes read fallback only

STEP 5: Migrate graph queries to SurrealDB
        Story graphs, timelines, concept maps

STEP 6: Deprecate PostgreSQL graph tables
        Keep only for legacy API compatibility
```

---

## Data Mapping

| Current (PostgreSQL)     | Target (SurrealDB)       | Notes                          |
|--------------------------|--------------------------|--------------------------------|
| quran_verses             | ayah:sura:ayah           | Add mushaf_page, juz, hizb     |
| tafseer_chunks           | tafsir_chunk:id          | Add hash, version_tag          |
| tafseer_sources          | Metadata on chunks       | Denormalized for query perf    |
| story_clusters           | story_cluster:id         | Add provenance fields          |
| story_events             | story_event:id           | Add evidence JSONB             |
| story_connections        | NEXT, THEMATIC_LINK edges| Native graph edges             |
| event_connections        | Same edge types          | In SurrealDB                   |
| concepts                 | concept_tag:id           | Bilingual labels               |
| occurrences              | MENTIONS edges           | Typed by ref_type              |
| associations             | RELATED_TO edges         | With relation_type attribute   |
| (none)                   | ingest_run               | NEW: run tracking              |
| (none)                   | ingest_step              | NEW: step tracking             |
| (none)                   | ingest_record_state      | NEW: per-record state          |
| (none)                   | embedding_record         | NEW: vector registry           |

---

## Key Design Decisions

### 1. Record ID Strategy

```
Format: table:namespace:identifier

Examples:
  ayah:18:83                    # Sura 18, Ayah 83
  tafsir_chunk:tabari:18:83-84:v1:abc123  # Source:range:version:hash_prefix
  story_cluster:musa_pharaoh
  story_event:musa_pharaoh:staff_miracle
  person:musa
  place:egypt
  concept_tag:patience
```

### 2. Provenance Fields (on all records)

```javascript
{
  _hash: string,           // SHA256 of content
  _version: string,        // Semantic version or git sha
  _source: string,         // Where data came from
  _created_at: datetime,
  _updated_at: datetime,
  _ingest_run_id: string   // Which run created/updated this
}
```

### 3. Edge Attributes

All edges carry metadata for explainability:

```javascript
{
  _type: string,           // Edge type (NEXT, EXPLAINS, etc.)
  _strength: float,        // 0.0-1.0
  _confidence: float,      // 0.0-1.0
  _evidence: [chunk_ids],  // Grounding
  _created_at: datetime
}
```

---

## Files to Create

```
app/
├── kg/
│   ├── __init__.py
│   ├── client.py           # SurrealDB async client
│   ├── schema.py           # Schema definitions (SurrealQL)
│   ├── models.py           # Pydantic models for KG entities
│   ├── queries.py          # Common graph queries
│   └── bridge.py           # Vector-to-graph bridge
├── ingest/
│   ├── __init__.py
│   ├── orchestrator.py     # Run management
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── base.py         # Step base class
│   │   ├── ingest_sources.py
│   │   ├── normalize_ayah.py
│   │   ├── chunk_tafsir.py
│   │   ├── embed_chunks.py
│   │   ├── upsert_qdrant.py
│   │   ├── build_kg_edges.py
│   │   ├── build_story_events.py
│   │   └── validate.py
│   └── cli.py              # CLI entry point
├── api/routes/
│   └── kg.py               # KG API endpoints
```
