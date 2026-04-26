# Phase Stories — Audit Report
_Generated: 2026-04-25_

---

## 1. Current Implementation Overview

### 1.1 Frontend Pages

| File | Route | Purpose |
|------|-------|---------|
| `frontend/src/pages/StoriesPage.tsx` | `/stories` | Story list with category filter + search |
| `frontend/src/pages/StoryDetailPage.tsx` | `/stories/:storyId` | Story detail with segment list, graph, themes, insights views |
| `frontend/src/pages/StoryAtlasPage.tsx` | `/story-atlas` | Atlas of story clusters (separate system) |
| `frontend/src/pages/StoryAtlasDetailPage.tsx` | `/story-atlas/:clusterId` | Cluster detail with events and graph |

### 1.2 Frontend Components

| File | Purpose |
|------|---------|
| `frontend/src/components/stories/RelatedStories.tsx` | Related stories via cross-story connections |
| `frontend/src/components/stories/StoryGraphView.tsx` | Network graph visualization |
| `frontend/src/components/stories/ThematicFlow.tsx` | Thematic flow chart |
| `frontend/src/components/stories/NarrativeInsights.tsx` | Narrative analysis insights |
| `frontend/src/components/stories/ThematicJourney.tsx` | Thematic journey component |

### 1.3 Backend Routes

| File | Mount | Purpose |
|------|-------|---------|
| `backend/app/api/routes/stories.py` | `/api/v1/stories` | List stories, get detail, graph, timeline, connections |
| `backend/app/api/routes/story_atlas.py` | `/api/v1/story-atlas` | List clusters, facets, cluster detail, graph, related |

### 1.4 Backend Models

| File | Tables | Purpose |
|------|--------|---------|
| `backend/app/models/story.py` | `stories`, `story_segments`, `story_connections`, `cross_story_connections`, `themes` | Core story structure |
| `backend/app/models/story_atlas.py` | `story_clusters`, `story_events`, `cluster_connections`, `related_clusters` | Extended atlas structure |

### 1.5 Data Files

| File | Purpose |
|------|---------|
| `data/manifests/stories.json` | 122-story manifest with verse references and evidence |
| `frontend/src/data/sourceRegistry.ts` | Source registry with 13 sources |

### 1.6 Seed Scripts

| File | Purpose |
|------|---------|
| `backend/scripts/ingest/seed_stories.py` | Seeds stories from manifest to DB |
| `backend/scripts/ingest/seed_story_atlas.py` | Seeds story atlas clusters |
| `backend/scripts/ingest/seed_story_graphs.py` | Seeds cross-story graph connections |

### 1.7 Existing Tests

| File | Purpose |
|------|---------|
| `backend/tests/unit/test_story_acceptance.py` | I18n, data completeness, graph rendering |
| `backend/tests/unit/test_story_atlas.py` | Story atlas unit tests |
| `backend/tests/unit/test_story_graph.py` | Story graph unit tests |

---

## 2. Current Data Structure (stories manifest)

```json
{
  "id": "story_musa",
  "name_ar": "قصة موسى عليه السلام",
  "name_en": "Story of Prophet Musa (Moses)",
  "category": "prophet",
  "main_figures": ["Musa", "Harun", "Firawn"],
  "themes": ["liberation", "miracles", "patience"],
  "summary_en": "...",
  "summary_ar": "...",
  "suras_mentioned": [2, 7, 10, 11, 17, 18, 20, 26, 27, 28, 40, 43, 44, 79],
  "segments": [
    {
      "id": "musa_birth",
      "narrative_order": 1,
      "aspect": "birth_and_rescue",
      "sura_no": 28,
      "aya_start": 7,
      "aya_end": 13,
      "summary_en": "...",
      "evidence": [
        { "source_id": "ibn_kathir", "chunk_id": "ibn_kathir:28:7-13", "needs_review": true }
      ]
    }
  ]
}
```

---

## 3. Story List (122 stories)

The manifest contains 122 stories including all major Quranic narratives. See `docs/quran-stories-inventory.md` for the full list with verse reference coverage.

---

## 4. Missing Features — Summary

### 4.1 Audience Levels — MISSING
- No `kids` / `adult` level in any story or segment
- `StoryDetailPage` has no audience level toggle
- Both simple and complex summaries are currently the same field (`summary_en` / `summary_ar`)
- Risk: adult explanations referencing tafsir concepts not suitable for children, and vice-versa

### 4.2 Segment Arabic Summaries — MOSTLY MISSING
- Segments only have `summary_en` (English only)
- Top-level stories have `summary_ar` and `summary_en`
- Segment-level `summary_ar` is absent in the manifest
- DB model supports `summary_ar` and `summary_en` on segments but they are not populated

### 4.3 Kids-Level Summaries — MISSING
- No `summary_kids_ar` or `summary_kids_en` fields anywhere
- No `lessons_ar` / `lessons_en` on story objects in manifest
- DB model does not have separate kids/adult fields

### 4.4 Sunni Source Review Metadata — MISSING
- No `sunniReview` status on any segment
- No `matchedEvidence` linking to approved tafsir sources
- No `humanReviewRequired` flag
- No rejection/needs_review workflow

### 4.5 Source ID Mismatch — CRITICAL GAP
- Manifest uses short IDs: `ibn_kathir`, `tabari`, `qurtubi`, `saadi`
- Source registry uses: `ibn_kathir_ar`, `ibn_kathir_en`
- Phase 2.5 `TRUSTED_SOURCE_IDS` accepts both forms (base + `_ar` / `_en`) — OK for RAG
- But story data validation scripts do not yet exist to enforce this on story content

### 4.6 Translation Risk — NEEDS LABELS
- `summary_en` fields in segments are **not labeled as translations** in the UI
- Story detail page displays them as plain text with no "Translation" warning
- Risk: users may confuse summaries with Quran text or authoritative tafsir

### 4.7 Validation Script — MISSING
- No `scripts/validate-quran-stories.ts` equivalent for story data
- No Sunni review report generator
- The existing `validate-quran-integrity.ts` does not check story data

### 4.8 Related Stories Evidence — PARTIAL
- `RelatedStories.tsx` fetches `CrossStoryConnection` objects from the DB
- `CrossStoryConnection` model has `evidence_chunk_ids` (required by DB constraint)
- But manifest's `connections` array format is not fully mapped to `evidenceReferences`
- Connection `strength` is stored but evidence quality varies

### 4.9 ProphetsMentioned / RelatedPlaces / RelatedPeople — MISSING
- Manifest has `main_figures` but no split of `prophetsMentioned` vs `relatedPeople`
- No `relatedPlaces` field in manifest or DB

### 4.10 Reliability Badge — MISSING in UI
- Story cards and detail page show no `reliabilityLevel` badge
- No indicator of `canonical` / `verified` / `needs_review` status per story

### 4.11 Audience Filter on Stories Page — MISSING
- `StoriesPage` has category filter but no audience level filter (kids/adult)
- No filter by prophet/person, surah, or theme combination

### 4.12 Story Segment `needs_review` Warning — MISSING in UI
- Evidence items have `needs_review: true` but this is not surfaced to users
- No visible warning when a segment's explanation is pending review

---

## 5. Hardcoded Explanations

- `summary_en` in segments is editorialized English prose, NOT tafsir text
- These are not labeled as sourced tafsir, just summaries
- They have `evidence` array but all `needs_review: true` — meaning they have not been validated against DB tafsir chunks

---

## 6. UI/UX Limitations

| Limitation | Details |
|-----------|---------|
| No audience toggle | Kids and adults see identical content |
| No source attribution per segment | Evidence is stored but not displayed |
| No "translation" label | Summaries not marked as non-Quran text |
| No needs_review warning | Users see unvalidated summaries with no disclaimer |
| No surah-based filter | Cannot filter stories by surah |
| No reliability badge | No visual indicator of content validation status |
| Story graph is heavy | React Flow visualization — loads for all stories |

---

## 7. Source Validation Gaps

| Gap | Risk |
|-----|------|
| Manifest source IDs (`ibn_kathir`) not in full form | Validation scripts may reject them |
| `needs_review: true` on all evidence | No story segment is fully validated |
| No sunniReview status field | Cannot programmatically block unreviewed content |
| `al_muyassar_ar` is `supporting` — cannot approve segments | Only `canonical`/`verified` should approve |

---

## 8. Recommended Implementation Plan

### Phase Stories-A — Data Model + Seed Data (this sprint)
1. Define `QuranStory` TypeScript type with audience levels and sunniReview
2. Create validated seed data for 8 priority stories
3. Add `validate-quran-stories.ts` script
4. Add Sunni review metadata to segments

### Phase Stories-B — UI Improvements
5. Add Kids/Adult toggle to `StoryDetailPage`
6. Add source attribution display per segment
7. Add `needs_review` warning to unvalidated segments
8. Add audience filter to `StoriesPage`
9. Add reliability badge to story cards

### Phase Stories-C — Engine + Tests
10. Add `getRelatedStories` function with evidence references
11. Add `review-quran-stories-sunni.ts` script
12. Add story schema validation tests
13. Run full validation suite

---

## 9. Risks Requiring Human Review

| Risk | Path |
|------|------|
| All 122 manifest segments have `needs_review: true` | `data/manifests/stories.json` |
| Source IDs in manifest not yet cross-validated against DB chunks | All story evidence |
| Kids summaries do not yet exist — will need scholarly review before production | — |
| Sunni review workflow is new — needs policy review before activating |  — |
| `tabari` is listed as `canonical` in TAFSIR_CATALOG but not in sourceRegistry as canonical | Verify |
