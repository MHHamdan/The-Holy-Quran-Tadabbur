# Story Atlas Empty — Root Cause Audit

**Date**: 2026-05-17
**Branch**: phase-w-asma-allah-atlas
**Symptom**: `http://172.24.50.21:3000/story-atlas` shows `"0 قصة متاحة"` and `"لا توجد قصص مطابقة للبحث"` even when `/stories` returns content.

---

## TL;DR — Root Cause

The frontend page `frontend/src/pages/StoryAtlasPage.tsx` is **wholly dependent on a backend API call** (`GET /api/v1/story-atlas`) that **crashes server-side** because of a Pydantic / dataclass mismatch:

- `backend/app/services/story_atlas.py:70-83` defines `ClusterSummary` **without** a `summary_ar` field.
- `backend/app/api/routes/story_atlas.py:229` reads `c.summary_ar` when building `ClusterSummaryResponse`.
- Result: every list request returns
  ```
  500 Internal — 'ClusterSummary' object has no attribute 'summary_ar'
  ```
  (verified by `curl http://localhost:8002/api/v1/story-atlas?limit=2`).

The frontend `try/catch` swallows the error, leaves `clusters: []` and `total: 0`, and renders the empty-state.

Even after the backend bug is fixed, the atlas would still be sparse because the **`story_clusters` DB table is populated independently from `quranStories.ts`**, and there is no canonical merge layer joining the rich generated graph layers (`quranProphetStoryPages`, `quranProphetsAtlas`, `quranEntityMentions`, `quranTopicAtlas`, …) with the authored stories.

Hence both fixes are required:

1. Repair the backend bug.
2. Build a canonical **`quranStoryRegistry.json`** that merges authored + generated layers and is consumable by the frontend **without depending on the DB**.

---

## Detailed Findings

### 1. Data sources used by each page

| Page              | File                                          | Data source                                             |
| ----------------- | --------------------------------------------- | ------------------------------------------------------- |
| `/stories`        | `frontend/src/pages/StoriesPage.tsx`          | `storiesApi.listStories()` → `GET /api/v1/stories/`     |
| `/story-atlas`    | `frontend/src/pages/StoryAtlasPage.tsx`       | `storyAtlasApi.listClusters()` → `GET /api/v1/story-atlas` |
| `/stories/:id`    | `frontend/src/pages/StoryDetailPage.tsx`      | backend `/stories/{id}` + local `quranStories.ts`       |

`/stories` works because the backend table `stories` has rows. `/story-atlas` fails because the route raises 500 from the missing `summary_ar` attribute.

### 2. Backend bug location

`backend/app/services/story_atlas.py:69-83`
```python
@dataclass
class ClusterSummary:
    ...
    summary_en: Optional[str]
    # NOTE: summary_ar is missing
```

`backend/app/services/story_atlas.py:466-481` — `_cluster_to_summary` never assigns `summary_ar` either.

`backend/app/api/routes/story_atlas.py:215-232` — the response builder reads `summary_ar=c.summary_ar` → `AttributeError`.

This is a regression introduced when `summary_ar` was added to the response schema without updating the dataclass.

### 3. Categories drift

`StoryAtlasPage.tsx` category IDs (`prophet, prophetic, prophetic_sira, named_char, nation, parable, historical, unseen`) **do not** match the seven categories accepted by `/stories` (`prophet, parable, nation, historical, unseen, righteous`). Once the registry exists we will use one unified enum across both pages:

```
prophet | prophetic_sirah | person | nation | parable | historical |
unseen  | compact_profile | needs_review
```

with backwards-compatible aliasing for legacy DB rows (`named_char → person`, `prophetic_sira → prophetic_sirah`, `righteous → person`).

### 4. Generated data layers are not consumed by the atlas

The following files exist and are well-formed, but the atlas page reads none of them:

| File                                                    | Records |
| ------------------------------------------------------- | ------- |
| `quranProphetsAtlas.json`                               | 25 profiles |
| `quranProphetStoryPages.json`                           | 9 prophet pages |
| `quranEntityMentions.json`                              | 90 entities, 1115 mentions |
| `quranEntityRelations.json`                             | 1705 relations |
| `quranTopicAtlas.json`                                  | 70 topics, 5307 ayah links |
| `quranKnowledgeGraph.json`                              | 503 nodes, 9306 edges |
| `quranStoryConnections.json`                            | 114 surahs, 80 entity occurrences, 55 cross-surah links |

`StoryAtlasPage` reads none of these — so even if the DB layer were healthy, the atlas would never expose the new graph/atlas layers.

### 5. Stale "missing prophets" flag

`quranProphetsAtlas.json.summary.prophetsMissingStoryPages` still lists 8 prophets, but `quranProphetStoryPages.json.prophetIdsCovered` already covers 9 (Ishaq, Yaqub, Harun, Dhul-Kifl, Ilyas, Al-Yasa, Sulayman, Muhammad ﷺ, Ismail). The atlas was generated **before** the story-pages script and the summary was not refreshed. Re-running `build-quran-prophets-atlas.ts` after the story-pages script writes the corrected flags.

### 6. Filters & empty state confusion

`StoryAtlasPage` shows the empty-state on **any** scenario where the API returns `total=0` — including server errors — so the user cannot distinguish *"no matching stories"* from *"backend is broken"*. The fix adds three distinct states: loading, registry-load-failure (with a regenerate hint), and *no-results-after-filters*.

---

## Proposed Fix (multi-step)

1. **Backend hotfix**: add `summary_ar: Optional[str]` to `ClusterSummary` and pass it from `_cluster_to_summary`. This restores the existing DB-backed list.
2. **Canonical registry**: write `scripts/build-quran-story-registry.ts` that merges authored stories + prophet pages + prophets atlas + entity/topic graphs into a single `frontend/src/data/generated/quranStoryRegistry.json`.
3. **Validator**: `scripts/validate-quran-story-registry.ts` — fails the build if the atlas would render 0 while the registry has stories.
4. **Frontend rewrite**: `StoryAtlasPage` consumes the canonical registry (local-first) with optional backend enrichment. The page no longer goes empty when the backend is down.
5. **Shared adapter**: `frontend/src/utils/storyRegistryAdapter.ts` consumed by both `StoriesPage` and `StoryAtlasPage`.
6. **Backend registry API**: new endpoints serve the same registry JSON so the API and frontend agree by construction.
7. **Coverage dashboard** added to `/story-atlas` so emptiness can no longer happen silently.

All generated/contextual links default to `reviewStatus: "needs_review"` and `humanReviewRequired: true`.
