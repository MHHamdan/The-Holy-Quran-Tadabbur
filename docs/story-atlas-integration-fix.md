# Story Atlas Integration Fix

This document describes the integration fix that resolved the empty
`/story-atlas` page and the divergence between `/stories` and
`/story-atlas`.

## Root cause (full audit in `story-atlas-empty-root-cause-audit.md`)

The frontend `/story-atlas` page depended exclusively on the backend
`GET /api/v1/story-atlas` endpoint, which crashed with
`AttributeError: 'ClusterSummary' object has no attribute 'summary_ar'`.
The frontend catch-all swallowed the error and rendered an empty grid.
A second, deeper issue: even with the backend healthy, the atlas page
would not consume any of the generated graph/atlas layers, leaving the
new prophet/entity/topic work invisible.

## Fix

### 1. Backend hotfix
`backend/app/services/story_atlas.py` — added `summary_ar: Optional[str]`
to the `ClusterSummary` dataclass and wired it through `_cluster_to_summary`.
The legacy DB-backed route now responds successfully (status 200 with
populated rows when the DB has clusters).

### 2. Canonical registry
`scripts/build-quran-story-registry.ts` builds
`frontend/src/data/generated/quranStoryRegistry.json` by merging:

- `data/manifests/stories.json` (122 authored stories)
- `frontend/src/data/generated/quranProphetStoryPages.json` (9 prophet pages)
- `frontend/src/data/generated/quranProphetsAtlas.json` (25 prophet profiles)
- entity / topic / KG layers (best-effort)

Every entry carries:
- `storyId`, bilingual titles
- canonical `category` (registry enum)
- `sourceType` (authored / prophet / entity / generated)
- `quranReferences` with `linkType` and per-reference `reviewStatus`
- counts (`segmentCount`, `surahCount`, `ayahRangeCount`)
- relation arrays (prophets, entities, topics, stories)
- `reviewStatus`, `humanReviewRequired`, `warnings`

### 3. Validator
`scripts/validate-quran-story-registry.ts` fails the build when:
- registry is empty,
- the manifest has stories but the registry doesn't,
- categories drift away from the canonical enum,
- a Phase X2 prophet page is missing,
- a reference has invalid surah/ayah numbers,
- a registry entry is marked `verified` without releasing
  `humanReviewRequired`.

### 4. Frontend page rewrite
`frontend/src/pages/StoryAtlasPage.tsx` now consumes the registry
locally through `storyRegistryAdapter`. Three states are explicit:

- *Loading* (suspense boundary)
- *Registry missing* — bilingual hint to run the generator
- *Filtered empty* — shown only after a filter or search yields no rows

A coverage dashboard renders next to the header so users (and reviewers)
can see total stories, prophet profiles, candidates, surahs covered,
prophets covered, ayah ranges, and review-pending counts.

### 5. Shared adapter
`frontend/src/utils/storyRegistryAdapter.ts` exposes the helpers used
by both `/stories` and `/story-atlas`:

```ts
getAllStoriesForCards()
getStoriesByCategory(cat)
searchStories(q)
getStoryDetailRoute(id)
getStoryReviewStatus(id)
getStorySourceType(id)
getCoverage()
isRegistryHealthy()
```

### 6. Backend registry API
`backend/app/api/routes/story_atlas_registry.py` serves the same JSON
under `/api/v1/quran/story-atlas`, `…/coverage`, `…/categories`,
`…/search`, `…/{storyId}`, `…/{storyId}/connections`. Returns 503 when
the generated file is missing — never silently empty.

### 7. Connection enrichment
`scripts/build-quran-story-atlas-connections.ts` produces 355 evidence-
backed candidate links (story → prophet / topic / entity / story / surah),
all `needs_review`.

## Regeneration playbook

```bash
npx tsx scripts/build-missing-prophet-story-pages.ts
npx tsx scripts/build-quran-story-registry.ts
npx tsx scripts/build-quran-story-atlas-connections.ts
npx tsx scripts/validate-quran-story-registry.ts
python -m pytest backend/tests/unit/test_quran_story_registry.py
```

The validator + tests gate registry health before any UI build.
