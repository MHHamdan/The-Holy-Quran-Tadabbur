# Phase 5.6 – Path Explanation Audit

**Date:** 2026-04-27  
**Status:** Implementation complete (Phase 5.6)

---

## Where `find_path()` exists

`backend/app/services/verse_similarity.py` — method `VerseSimilarityService.find_path()` (line 517).

### Current return shape (pre-5.6)

```python
[
  {"nodeId": "ayah:12:18", "nodeType": "ayah", "label": "12:18"},
  {"nodeId": "story:yusuf", "nodeType": "story", "label": "Story of Yusuf", "edgeType": "SAME_STORY"},
  {"nodeId": "ayah:12:83", "nodeType": "ayah", "label": "12:83", "edgeType": "SAME_STORY"},
]
```

Issues before 5.6:
- Checks story overlap before segment overlap (less specific)
- No `labelArabic` field for story/segment nodes
- Returns raw dicts with no status/warning information
- Never called from `find_similar()` — path never attached to results

---

## Why `pathExplanation` was not populated (pre-5.6)

1. `find_similar()` never called `find_path()` for any candidate ayah.
2. `KGSimilarityResult` dataclass had no `pathExplanation` field.
3. Backend Pydantic models (`KGRelatedAyahResponse`) had no `pathExplanation` field.
4. Frontend `KGRelatedAyah` interface had no `pathExplanation` field.
5. `PathExplanation` TypeScript interface was a stub (`nodes: string[], edges: string[]`).
6. `KGSimilaritySection.tsx` had no UI to display path data.

---

## Frontend support status (pre-5.6)

| Item | Status |
|---|---|
| `PathExplanation` type in `quranKnowledgeGraph.ts` | Stub — `nodes: string[], edges: string[]` |
| `KGRelatedAyah.pathExplanation` in `api.ts` | Missing |
| Path display in `KGSimilaritySection.tsx` | Not implemented |
| Translation keys for path nodes | Partial (only `similarity_path_explanation` key existed) |

---

## Backend API support status (pre-5.6)

| Item | Status |
|---|---|
| `find_path()` method | Exists, functional |
| `pathExplanation` in `KGSimilarityResult` | Missing |
| `KGPathExplanationResponse` Pydantic model | Missing |
| `pathExplanation` in `KGRelatedAyahResponse` | Missing |
| Route handler maps path to response | Not implemented |

---

## Safety risks identified

1. **Arabic label leakage** — if story `name_ar` is fetched and displayed, it must be a story title (not Quran text). Verified: `name_ar` fields in `stories.json` are short story titles like "قصة يوسف", not ayah text.

2. **No Quran text in path nodes** — Ayah nodes are referenced only by `surahNumber:ayahNumber`. Text is fetched separately at runtime by the Mushaf view. Enforced by: path nodes contain no `text_uthmani` or `text_imlaei`.

3. **Status inflation** — path edges must never claim `approved` status. All story/concept-based paths are `needs_review`. Enforced by: `PathEdge.relationStatus` hardcoded to `NEEDS_REVIEW` for all current path types.

4. **Experimental paths hidden** — if a path contains experimental edges (semantic-only), it must be hidden unless `showExperimental` is ON. Enforced by: `find_path()` does not return semantic edges; only story/concept/theme paths are generated.

5. **Max path length** — paths longer than 4 nodes are truncated to prevent large response payloads. Enforced in `_build_path_explanation()`.

6. **No tafsir invention** — path explanations are generic, relation-type based strings. No scholarly meaning is asserted. Enforced by `_build_path_text()`.

---

## Planned implementation (Phase 5.6)

### Backend
1. Add `PathNode`, `PathEdge`, `PathExplanation` dataclasses to `verse_similarity.py`
2. Update `find_path()`: check segments before stories; add `labelArabic` to story/segment nodes
3. Add `_build_path_text()`: safe generic bilingual explanation based on edge types
4. Add `_build_path_explanation()` method: converts raw path steps to `PathExplanation`
5. Update `find_similar()`: populate `pathExplanation` for top-k results only
6. Add `KGPathNodeResponse`, `KGPathEdgeResponse`, `KGPathExplanationResponse` Pydantic models
7. Update `KGRelatedAyahResponse` and route handler to include `pathExplanation`

### Frontend
1. Update `PathExplanation` interface in `quranKnowledgeGraph.ts` to full contract
2. Add `KGPathNode`, `KGPathEdge`, `KGPathExplanation` to `api.ts`
3. Add `pathExplanation?: KGPathExplanation` to `KGRelatedAyah`
4. Add `PathExplanationCard` component in `KGSimilaritySection.tsx`
5. Wire `PathExplanationCard` into `KGRelatedAyahCard` expanded view
6. Add translation keys for path nodes, connection, and warnings

### Tests
1. New test file: `backend/tests/unit/test_verse_similarity_paths.py`
2. Tests: pathExplanation populated, omitted when no path, no Quran text, needs_review warning, max path length

---

## Path explanation contract (implemented)

```json
{
  "nodes": [
    { "id": "ayah:12:18", "type": "ayah", "surahNumber": 12, "ayahNumber": 18 },
    { "id": "story_segment:yusuf:01", "type": "story_segment", "labelEnglish": "Story of Yusuf", "labelArabic": "قصة يوسف" },
    { "id": "ayah:12:83", "type": "ayah", "surahNumber": 12, "ayahNumber": 83 }
  ],
  "edges": [
    { "sourceNodeId": "ayah:12:18", "targetNodeId": "story_segment:yusuf:01", "edgeType": "SAME_STORY_SEGMENT", "relationStatus": "needs_review", "humanReviewRequired": true },
    { "sourceNodeId": "story_segment:yusuf:01", "targetNodeId": "ayah:12:83", "edgeType": "SAME_STORY_SEGMENT", "relationStatus": "needs_review", "humanReviewRequired": true }
  ],
  "explanationArabic": "ترتبط هاتان الآيتان من خلال مقطع من القصة القرآنية نفسها، وهذه الصلة تحتاج إلى مراجعة علمية.",
  "explanationEnglish": "These ayahs are connected through the same Quranic story segment. This relation is pending scholarly review.",
  "warnings": ["This connection path is derived from Quranic story and concept data and awaits scholarly review."]
}
```
