# Quran Story Registry — Methodology

## Goal

The registry is the **single source of truth** for what counts as a
Quran-derived story in this platform. It serves both `/stories` (a
friendly story-card page) and `/story-atlas` (an advanced graph index).
Anything that displays a story should ultimately read from this file.

## Inputs

| Source | Path | Role |
|---|---|---|
| Authored story manifest | `data/manifests/stories.json` | Primary source — 122 stories with segments, themes, evidence |
| Prophet story pages | `frontend/src/data/generated/quranProphetStoryPages.json` | Fills prophet gaps (9 pages incl. compact profiles + Muhammad ﷺ mission summary) |
| Prophets atlas | `frontend/src/data/generated/quranProphetsAtlas.json` | Provides prophet ↔ story mapping |
| Entity mentions / relations | `quranEntityMentions.json` / `quranEntityRelations.json` | Used by connections builder |
| Topic atlas | `quranTopicAtlas.json` | Used for topic enrichment |
| Knowledge graph | `quranKnowledgeGraph.json` | Optional augmentation |

## Output

`frontend/src/data/generated/quranStoryRegistry.json` — see
`frontend/src/types/quranStoryRegistry.ts` for the exact shape.

`docs/generated/quran-story-registry-summary.md` — machine-generated
summary with totals and category counts.

## Canonical category enum

```
prophet | prophetic_sirah | person | nation | parable | historical |
unseen  | compact_profile | needs_review
```

Legacy category names (`prophetic`, `prophetic_sira`, `named_char`,
`righteous`, `companions`, `battles`, `mission_summary`) are folded into
the enum via `REGISTRY_CATEGORY_ALIASES` so the UI is stable across data
versions.

## Source-type semantics

| sourceType | Origin | Verified ever? |
|---|---|---|
| `authored_story` | manifest (human-curated) | yes after scholarly review |
| `prophet_story_page` | generated from atlas | needs_review |
| `entity_story_cluster` | candidate from entity graph | needs_review |
| `generated_candidate` | candidate from heuristics | needs_review |

## Review safety rules

1. No Quran text in the registry. Surah / ayah numbers only.
2. Every `quranReference` carries an explicit `linkType` and
   `reviewStatus`.
3. Authored stories with at least one segment have
   `reviewStatus = needs_review` (the segments themselves carry their
   own status from `quranStories.ts`). Stories with no segments are
   marked `missing_metadata`.
4. Prophet story pages always start `needs_review`. They are never
   promoted to `verified` without releasing `humanReviewRequired`.
5. Connection candidates from heuristics never include interpretive
   text — only evidence references.

## How to regenerate

```bash
npx tsx scripts/build-missing-prophet-story-pages.ts
npx tsx scripts/build-quran-story-registry.ts
npx tsx scripts/validate-quran-story-registry.ts
npx tsx scripts/build-quran-story-atlas-connections.ts
```

The validator must exit 0 before merging registry changes.
