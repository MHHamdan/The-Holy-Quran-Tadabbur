# Whole-Quran Story Connection — Current-State Audit

Snapshot date: 2026-05-16

This audit was produced from a direct read of the live repo (not from memory).
It records the existing story coverage, KG support, and major gaps that the
Whole-Quran Story Connection Atlas needs to fill.

---

## 1. Story coverage today

- **Total stories** (`frontend/src/data/quranStories.ts`): **33** (`QURAN_STORIES_FIRST_BATCH`)
- **Segments total**: 101 across all 33 stories (count of `segmentId:` entries)
- **Story IDs present**: `story_yusuf`, `story_musa`, `story_kahf`,
  `story_ibrahim`, `story_nuh`, `story_bilqis`, `story_maryam`, `story_luqman`,
  `story_ayyub`, `story_hud`, `story_salih`, `story_lut`, `story_yunus`,
  `story_dawud`, `story_talut_jalut`, `story_qarun`, `story_dhulqarnayn`,
  `story_zakariyya_yahya`, `story_two_gardens`, `story_garden_owners`,
  `story_sabbath_breakers`, `story_elephant`, `story_baqarah_cow`,
  `story_table_spread`, `story_adam`, `story_shuayb`, `story_habil_qabil`,
  `story_idris`, `story_ismail`, `story_khidr_musa`, `story_isa`,
  `story_ukhdud`, `story_qarya`.
- **Manifest** (`data/manifests/stories.json`): 122+ entries — broader than the
  rendered front-end list. Used as the canonical story-id source for the
  knowledge graph.

## 2. Existing Quran data

- `data/raw/quran_uthmani.json`: 6,236 ayahs, 114 surahs (verified by
  `validate-quran-integrity.ts`). Canonical Quran source.
- `data/raw/{ibn_kathir,jalalayn,muyassar,qurtubi,tabari}_*.json`: tafsir
  chunks.
- `assets/hafs_smart_v8.json`: supporting Hafs backup.

## 3. Existing knowledge graph and overlay

- `frontend/src/data/generated/quranKnowledgeGraph.json`: 201k+ lines
  (story/concept/source edges with `relationStatus`).
- `frontend/src/data/generated/reviewStatusOverlay.json`: overlay map
  (currently empty for story_segment/related_story/kg_relation/source_evidence
  /disagreement_note categories — version 1).
- `frontend/src/data/generated/surahMemoryAtlas.json`: per-surah memory atlas
  with `revelationType`, length, `storyLinks` (uses `storyNames` table).

## 4. Surahs with vs. without story links

Detected from `frontend/src/data/quranStories.ts` segment surah numbers (each
story segment has a `surahNumber` field). Surahs that appear in at least one
segment in `QURAN_STORIES_FIRST_BATCH`:

```
2, 3, 4, 5, 6, 7, 10, 11, 12, 14, 15, 17, 18, 19, 20, 21, 23, 25, 26, 27, 28,
29, 31, 32, 33, 36, 37, 38, 40, 41, 43, 44, 45, 46, 50, 51, 53, 54, 55, 57,
68, 71, 85, 105
```

Surahs with **no** story-segment link in the current data:

```
1, 8, 9, 13, 16, 22, 24, 30, 34, 35, 39, 42, 47, 48, 49, 52, 56, 58, 59, 60,
61, 62, 63, 64, 65, 66, 67, 69, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
82, 83, 84, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101,
102, 103, 104, 106, 107, 108, 109, 110, 111, 112, 113, 114
```

(70 surahs without an explicit segment link — many of these still mention
named entities in passing, which is exactly what the scan layer is meant to
surface.)

## 5. Prophets / persons indexed

- `data/concepts/curated_concepts.json` lists 20 persons (Adam, Nuh, Ibrahim,
  Musa, Isa, Yusuf, Dawud, Sulayman, Ayyub, Yunus, Lut, Hud, Salih, Shuayb,
  Maryam, Luqman, Firawn, Iblis, Dhul-Qarnayn, Qarun) and 7 nations.
- The story files use prophet/character names but **without a stable
  entity-id taxonomy** beyond the curated concepts.

## 6. Entities NOT yet indexed

- Prophets/messengers in the seed registry but missing from `curated_concepts`:
  Idris, Ismail, Ishaq, Yaqub, Yahya, Zakariyya, Harun, Muhammad ﷺ, Dhul-Kifl.
- Animals (cow, she-camel, hoopoe, ants, dog of the cave, whale, birds,
  spider, bee, elephant, crow, snake).
- Objects/events (Ark, staff, tablets, table spread, throne of Bilqis, two
  gardens, wall of Dhul-Qarnayn, sea crossing, flood, fire, virgin birth,
  cow of Bani Israel).
- Many places: Madinah/Yathrib, Babylon, Saba, Arafat, Safa, Marwah, Al-Ahqaf,
  Cave (already in concepts as `place_cave`).
- Title/role figures: Talut, Jalut, Haman, Bilqis, Ashab al-Kahf, Abu Lahab,
  Ashab al-Ukhdud, Ashab al-Fil, Ashab al-Rass.

## 7. Current validators

- `validate-quran-integrity.ts` — Quran/source registry integrity.
- `validate-quran-stories.ts` — story-data shape.
- `validate-quran-knowledge-graph.ts` — generated KG shape.
- `validate-surah-memory-atlas.ts` — atlas shape.
- `validate-review-status-overlay.ts` and `validate-review-tasks.ts` — review
  workflow.
- **Missing**: validator for story connection scan, story connection graph,
  and story chronology.

## 8. Current scripts

- `build-quran-knowledge-graph.ts` (existing builder, story+concept based).
- `build-surah-memory-atlas.ts`.
- `review-quran-stories-sunni.ts`, `generate-review-tasks.ts`,
  `propagate-review-status.ts`.
- **Missing**: surah-by-surah scan, story-connection graph builder.

## 9. Story Atlas UI today

- Route `/story-atlas` → `StoryAtlasPage` (cluster grid).
- Route `/story-atlas/:clusterId` → `StoryAtlasDetailPage` (Cytoscape lazy
  graph, narrative tabs).
- Layout nav links to `/story-atlas`.
- **No route yet** for `/story-atlas/connections` — to be added.

## 10. Major gaps

1. No coverage map for the **70 surahs without story segments** even when
   they reference prophets and nations explicitly.
2. No machine-readable cross-surah index of entity appearances.
3. No chronology layer that separates mushaf order, revelation order, and
   story-world order.
4. No "where else is this mentioned?" panel.
5. No connection quiz / learning loop tied to entity occurrences.
6. No validator preventing approved connections without evidence references.
7. Repeated narrative passages (Musa appears across ~30+ surahs; Ibrahim
   across ~25+) are not surfaced visually as comparison.
