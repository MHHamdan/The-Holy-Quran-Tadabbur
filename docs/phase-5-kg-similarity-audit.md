# Phase 5 Audit: Quran Knowledge Graph & Verse Similarity

**Audit Date:** 2026-04-27
**Status:** Pre-implementation audit — findings inform Phase 5 plan

---

## 1. Frontend Similarity UI

### Files
- `frontend/src/pages/SimilarityPage.tsx` — Full standalone page, fully implemented
- `frontend/src/components/quran/SimilarVersesPanel.tsx` — Embeddable panel widget

### Current Capabilities
- Arabic surah name parsing with 114-entry `SURAH_NAME_MAP`
- Arabic-to-Western digit normalization
- Verse resolution via `GET /quran/resolve` before similarity lookup
- `CandidateSelectionModal` for fuzzy-match disambiguation
- `ScoreBreakdown` and `MatchCard` components rendering all 7 score dimensions:
  jaccard, cosine, concept_overlap, grammatical, semantic, root_based, combined
- Filter controls: top_k, min_score, theme, exclude_same_sura, connection_type
- Calls `quranApi.getAdvancedSimilarity(sura, aya, options)`
- Popular verse shortcuts (آية الكرسي, البقرة 285, etc.)

### Status: Complete — no UI changes needed for Phase 5 core functionality.

---

## 2. Backend Similarity Endpoints

### File
`backend/app/api/routes/quran.py`

### Endpoints Implemented

| Endpoint | Service Used |
|---|---|
| `GET /similarity/fast/{sura}/{aya}` | FastSimilarityService (TF-IDF) |
| `GET /similarity/advanced/{sura}/{aya}` | AdvancedSimilarityService or FastSimilarityService |
| `GET /similarity/cross-sura/{sura}/{aya}` | Cross-surah connections |
| `GET /similarity/theme/{theme}` | Theme-based retrieval |
| `GET /similarity/connection-types` | Available connection types |
| `GET /similarity/cross-story/{prophet}` | Cross-story by prophet |
| `GET /similarity/story-mode/{theme}` | Story-mode narrative |
| `GET /similarity/story-themes` | Available story themes |

### Status: Complete — API surface is adequate. Semantic signal needs wiring.

---

## 3. Advanced Similarity Service

### File
`backend/app/services/advanced_similarity.py`

### Current Weights

```python
WEIGHTS = {
    "jaccard": 0.05,
    "contextual_jaccard": 0.15,
    "cosine": 0.05,
    "contextual_cosine": 0.15,
    "concept_overlap": 0.20,
    "grammatical": 0.08,
    "semantic": 0.10,    # BROKEN — always returns 0.0
    "root_based": 0.10,
    "prophetic": 0.07,
    "narrative": 0.05,
}
```

### Critical Gap
`_semantic_similarity()` always returns `0.0`. `VerseEmbeddingService.find_similar_to_verse()`
exists and uses Qdrant but is **never called** from `AdvancedSimilarityService`.

The semantic weight (0.10) is silently dropped and the remaining weights are renormalized,
meaning every verse comparison ignores embedding similarity entirely.

### Additional Data Available
- `THEME_LABELS_AR`: 35 themes with Arabic labels
- `PROPHETIC_THEMES`: 14 prophets with trials, themes, related_prophets, suras, moral_lessons
- `CROSS_STORY_THEMES`: 17 cross-story themes with keywords, stories, descriptions
- `CONTEXTUAL_SIGNIFICANCE`: weighted word importance for 40+ thematic terms

---

## 4. Fast Similarity Service

### File
`backend/app/services/fast_similarity.py`

### Implementation
- TF-IDF matrix as `np.ndarray` shape `(num_verses, vocab_size)`, float32, L2-normalized
- Dot product = cosine similarity after normalization
- `_verse_index: Dict[Tuple[int,int], int]` maps `(sura, aya)` → matrix row
- `_result_cache` with 5-minute TTL, max 1000 entries, LRU eviction
- `np.argpartition` for O(n) top-k

### Status: Working, but pure TF-IDF only — no thematic/story signals.

---

## 5. Verse Embedding Service

### File
`backend/app/services/verse_embedding_service.py`

### Implementation
- Model: `settings.embedding_model_multilingual` = `intfloat/multilingual-e5-large`
- **INCONSISTENCY:** `EMBEDDING_DIMENSION = 384` (MiniLM dimension) but config sets
  `embedding_dimension = 1024` (multilingual-e5-large dimension)
- Collection: `quran_verses` in Qdrant
- Point ID formula: `sura_no * 1000 + aya_no`
- Methods: `semantic_search()`, `find_similar_to_verse()`, `index_verses()`

### Gaps
1. `EMBEDDING_DIMENSION = 384` must be corrected to match config (1024) or the model changed
2. Qdrant collection may not be populated (ingest step `EMBED_CHUNKS` is a placeholder)
3. `find_similar_to_verse()` is never called from any similarity service

---

## 6. SurrealDB Knowledge Graph

### Files
- `backend/app/kg/schema.py` — Schema definition (version 1.1.0)
- `backend/app/kg/models.py` — KG data models

### Node Tables
`ayah`, `tafsir_chunk`, `story_cluster`, `story_event`, `person`, `place`, `concept_tag`

### Edge Tables
`has_event`, `mentions_ayah`, `explains`, `supported_by`, `involves`, `located_in`,
`next`, `thematic_link`, `tagged_with`

### Gap
`thematic_link` and `tagged_with` edges are not populated — concept ingestion
(`BUILD_KG_EDGES` step) is a placeholder handler.

---

## 7. Story Data

### Manifest
`data/manifests/stories.json` — 122 stories, v2.0.0

Each story has:
- `id`, `name_ar`, `name_en`, `category`, `main_figures`, `themes`
- `suras_mentioned`, `segments` (with sura_no, aya_start, aya_end, evidence)
- `connections` (intra-story segment connections)
- `evidence` (source references)

### Inter-Story Connections
`inter_story_connections` in manifest — **20 connections** with:
- `source_story_id`, `target_story_id`, `connection_type`
- `shared_theme`, `explanation` (ar/en), `evidence_chunk_ids`

### Frontend Stories
`frontend/src/data/quranStories.ts` — 8 seed stories, all `needs_review`

### Type System
`frontend/src/types/quranStory.ts` — fully typed with `RelatedStory[]`,
`StoryRelationType` (8 types), `StoryReliabilityLevel`

### Gap
Cross-story `relatedStories` links from manifest `inter_story_connections` are
not exposed via any API or included in frontend data.

---

## 8. Curated Concepts

### File
`data/concepts/curated_concepts.json` — 60 concepts

Categories: 20 persons, 7 nations, 6 places, 11 miracles, 12 themes, 4 moral_patterns

Each: `id`, `slug`, `label_ar`, `label_en`, `aliases_ar`, `aliases_en`, `description_ar`, `icon_hint`

### Gap
Not ingested into SurrealDB `concept_tag` table. `BUILD_KG_EDGES` step is placeholder.

---

## 9. Tests

### Existing Tests Related to Similarity/KG
- `backend/tests/unit/test_similarity_edges.py` — Elaboration/summarization edges
- `backend/tests/unit/test_kg_models.py` — KG model tests
- `backend/tests/unit/test_kg_orchestrator.py` — Orchestrator tests
- `backend/tests/unit/test_quran_aliases.py` — Alias resolution tests

### Missing Tests
- No unit tests for `AdvancedSimilarityService` (multi-layer scoring, WEIGHTS)
- No unit tests for `FastSimilarityService` (TF-IDF matrix, cosine similarity, caching)
- No unit tests for `VerseEmbeddingService` (dimension consistency)
- No tests for KG generation pipeline
- No tests for KG edge evidence validation

---

## 10. Scripts

### Current Scripts
- `scripts/validate-quran-integrity.ts`
- `scripts/validate-quran-stories.ts`
- `scripts/review-quran-stories-sunni.ts`

### Missing Scripts
- `scripts/build-quran-knowledge-graph.ts` — KG generation pipeline
- `scripts/validate-quran-knowledge-graph.ts` — KG validation

---

## Summary of Gaps (Priority Order)

| Priority | Gap | File |
|---|---|---|
| 1 | Semantic similarity not wired up | `advanced_similarity.py` |
| 2 | `EMBEDDING_DIMENSION = 384` inconsistent with config | `verse_embedding_service.py` |
| 3 | No TypeScript KG types | `frontend/src/types/quranKnowledgeGraph.ts` |
| 4 | No KG generation pipeline | `scripts/build-quran-knowledge-graph.ts` |
| 5 | No KG validation script | `scripts/validate-quran-knowledge-graph.ts` |
| 6 | Inter-story connections not exposed via API | new endpoint or KG service |
| 7 | Concept graph not populated | ingest pipeline |
| 8 | No unit tests for core similarity services | `backend/tests/unit/` |

---

## Recommended Implementation Plan

1. Fix `EMBEDDING_DIMENSION` in `verse_embedding_service.py`
2. Wire `VerseEmbeddingService.find_similar_to_verse()` into `AdvancedSimilarityService`
   with graceful fallback when Qdrant is unavailable
3. Create `frontend/src/types/quranKnowledgeGraph.ts` with full typed schema
4. Create `docs/quran-kg-relation-policy.md`
5. Create `backend/app/services/verse_similarity.py` — new hybrid scoring service
   using both KG edges and embedding similarity
6. Create `scripts/build-quran-knowledge-graph.ts` — generates KG JSON from existing data
7. Create `scripts/validate-quran-knowledge-graph.ts` — validates KG integrity
8. Add unit tests for new services
9. Create implementation and test case docs
