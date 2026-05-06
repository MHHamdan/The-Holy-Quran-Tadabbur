# Phase 5: Quran Knowledge Graph & Verse Similarity — Implementation

**Date:** 2026-04-27
**Status:** Complete

---

## 1. Why Hybrid KG + Semantic Search

Quranic similarity is not purely lexical. Two ayahs may be related because of:

- Shared story or story segment (structural, strongest signal)
- Shared prophet or person mentioned
- Shared theme or moral lesson
- Shared tafsir reference or cross-reference
- Shared semantic meaning (embedding similarity, weakest signal)

A single algorithm cannot capture all of these. Embeddings alone are unacceptable
because they can suggest plausible but unsupported meanings. A graph-based approach
keeps relationships explainable and source-backed.

---

## 2. Architecture

```
data/manifests/stories.json     → _KGIndex (in-memory)
data/concepts/curated_concepts.json  →  |
                                        ↓
                               VerseSimilarityService
                               (backend/app/services/verse_similarity.py)
                                        ↓
                               Multi-signal score per ayah pair
                                        ↓
                               KGSimilarityResponse (evidence-backed)

VerseEmbeddingService (Qdrant) → Experimental semantic candidates (when populated)

scripts/build-quran-knowledge-graph.ts → frontend/src/data/generated/quranKnowledgeGraph.json
scripts/validate-quran-knowledge-graph.ts → 13 integrity checks
```

---

## 3. Selected Algorithms

### 3.1 KG Index — Inverted Index (O(1) lookups)

`_KGIndex` builds inverted indices at startup:
- `ayah_stories[(sura, aya)]` → Set[story_id]
- `ayah_segments[(sura, aya)]` → Set[segment_id]
- `story_ayahs[story_id]` → Set[(sura, aya)]
- `ayah_concepts[(sura, aya)]` → Set[concept_id]
- `ayah_themes[(sura, aya)]` → Set[theme_id]
- `ayah_persons[(sura, aya)]` → Set[person_id]

Load time: ~200ms for 122 stories, 60 concepts.

### 3.2 Jaccard Similarity (shared neighbors)

For each candidate ayah pair, Jaccard coefficient measures overlap per signal type:

```
J(A, B) = |A ∩ B| / |A ∪ B|
```

Used for: story overlap, concept overlap, theme overlap, person overlap.

### 3.3 Weighted Multi-Signal Scoring

Final score is a weighted sum of all signals:

```python
WEIGHTS = {
    "story_segment": 0.28,  # Same story segment — strongest
    "story":         0.18,  # Same story, different segment
    "concept":       0.18,  # Shared curated concept
    "theme":         0.12,  # Shared curated theme
    "person":        0.10,  # Shared prophet / person
    "semantic":      0.08,  # Embedding cosine (experimental)
    "lexical":       0.04,  # Shared word roots (placeholder)
    "source_conf":   0.02,  # Source confidence bonus
}
```

### 3.4 Personalized Traversal (find_path)

BFS-style shortest path through KG nodes (1-hop and 2-hop):

```
ayah → story → ayah          (direct story connection)
ayah → concept → ayah        (concept bridge)
ayah → theme → ayah          (theme bridge)
ayah → story → inter_story → story → ayah  (2-hop cross-story)
```

### 3.5 Semantic Embedding (experimental candidate generation)

`VerseEmbeddingService.find_similar_to_verse()` queries Qdrant with the
verse's pre-computed embedding (multilingual-e5-large, 1024 dimensions).
Results are used only as candidates. If no other evidence exists, they are:
- hidden by default (`includeExperimental=False`)
- marked `experimental` with warnings when shown

---

## 4. Relation Types

| Type | Signal | Default Status |
|---|---|---|
| `SAME_STORY_SEGMENT` | Story manifest segment | `needs_review` |
| `SAME_STORY` | Story manifest cross-segment | `needs_review` |
| `SAME_PROPHET_OR_PERSON` | Curated concepts persons | `needs_review` |
| `SAME_THEME` | Curated concepts themes | `needs_review` |
| `SAME_CONCEPT` | Curated concepts | `needs_review` |
| `PARALLEL_EVENT_PATTERN` | Inter-story connection | `needs_review` |
| `SHARED_MORAL_LESSON` | Inter-story connection | `needs_review` |
| `CONTRASTS_WITH` | Inter-story connection | `needs_review` |
| `SEMANTICALLY_SIMILAR` | Qdrant embedding | `experimental` |

---

## 5. Scoring Model

Source-backed relations always score above semantic-only relations.
Same story segment (0.85 base weight) outscores same story (0.60).
Semantic embedding alone cannot achieve a score above `semantic weight × 1.0 = 0.08`.

Story-related ayahs with 3+ signals typically score 0.35–0.70.
Pure semantic candidates score 0–0.08.

---

## 6. Evidence Policy

Every public result (`needs_review`) must have at least one evidence item:
- `sourceId` from the active tafsir source list or `"story_manifest"` system marker
- `storyId` and/or `segmentId` for story-derived edges
- Source text references (`chunk_id`) when available from manifest

`experimental` results (semantic-only) may use `"system:embedding"` as sourceId.

---

## 7. Sunni Source Policy

Active tafsir sources for evidence:
- `ibn_kathir_ar` / `ibn_kathir_en` — Ibn Kathir
- `muyassar_ar` — Al-Muyassar
- `saadi_ar` / `saadi_en` — Al-Saadi
- `sahih_international` — Sahih International Translation
- `tafheem_en` — Tafheem ul-Quran

Pending license verification (not used for KG evidence yet):
- `tabari_ar`, `qurtubi_ar`, `baghawi_ar`

---

## 8. Experimental Relation Handling

When `includeExperimental=False` (default):
- Semantic-only results are silently dropped
- Only evidence-backed results are returned

When `includeExperimental=True`:
- Semantic results appear with `experimental` status
- Warning: "This connection is based on embedding similarity only and has not been verified by scholars."
- Arabic: "هذه الصلة مبنية على تشابه التضمين فحسب ولم يتحقق منها العلماء."

---

## 9. KG Generation Pipeline

Script: `scripts/build-quran-knowledge-graph.ts`

Inputs:
- `data/manifests/stories.json` — 122 stories, 20 inter-story connections
- `data/concepts/curated_concepts.json` — 60 concepts (persons, themes, miracles)
- `data/manifests/tafseer_sources.json` — source registry

Output: `frontend/src/data/generated/quranKnowledgeGraph.json`

Build result (2026-04-27):
- 503 nodes (story + segment + concept + theme + person nodes)
- 9,306 edges (8,909 SAME_STORY_SEGMENT + 195 SAME_STORY + 36 inter-story + 166 SAME_THEME)
- All edges: `needs_review`, `humanReviewRequired: true`
- No `approved` edges — human review required

---

## 10. Limitations

1. **Semantic similarity requires Qdrant population** — `index_verses()` must be run
   before embedding-based candidates appear. This is a one-time ingest step.

2. **Concept-to-ayah mapping is coarse** — Concepts are linked to story ayahs,
   not directly to individual ayahs. Verse-level concept tagging requires NER/NLP.

3. **No asbab or munasabah edges yet** — These require a dedicated approved source
   in the source registry before they can be generated.

4. **Root/lemma overlap not implemented** — Requires morphological analysis data.
   The `lexical` weight (0.04) is currently always 0.0.

5. **Story data is needs_review** — All 122 stories await scholarly verification.
   No edge can be `approved` until human review is complete.

---

## 11. Files Changed

| File | Change |
|---|---|
| `backend/app/services/verse_embedding_service.py` | Fixed `EMBEDDING_DIMENSION` from 384 to 1024 |
| `backend/app/services/advanced_similarity.py` | Wired `VerseEmbeddingService` for semantic scores |
| `backend/app/services/verse_similarity.py` | New KG-aware multi-signal similarity service |
| `frontend/src/types/quranKnowledgeGraph.ts` | New TypeScript KG type definitions |
| `scripts/build-quran-knowledge-graph.ts` | New KG generation pipeline |
| `scripts/validate-quran-knowledge-graph.ts` | New KG validation script (13 checks) |
| `backend/tests/unit/test_verse_similarity_kg.py` | 34 new unit tests for KG service |
| `backend/tests/unit/test_verse_embedding_service.py` | 7 new unit tests for embedding service |
| `docs/phase-5-kg-similarity-audit.md` | Phase 5 pre-implementation audit |
| `docs/quran-kg-relation-policy.md` | KG relation policy document |
| `docs/phase-5-kg-similarity-implementation.md` | This document |
| `docs/phase-5-similarity-test-cases.md` | Test case specifications |
| `frontend/src/data/generated/quranKnowledgeGraph.json` | Generated KG (9306 edges) |
| `docs/generated/quran-kg-summary.md` | KG build summary |
