# Whole-Quran Story Connection — Implementation Notes

This document describes how the Whole-Quran Story Connection Atlas is built,
end to end. It points to the code rather than restating it.

---

## 1. Pipeline

```
data/raw/quran_uthmani.json         (canonical Quran text, read-only)
frontend/src/data/quranStoryEntitySeeds.ts    (candidate dictionary)
frontend/src/data/quranStoryChronologySeeds.ts (chronology seeds)
frontend/src/data/quranStories.ts             (curated stories)
                │
                ▼
scripts/scan-quran-story-connections.ts
  → frontend/src/data/generated/quranStoryConnections.json
  → docs/generated/quran-story-connections-summary.md
                │
                ▼
scripts/build-quran-story-connection-graph.ts
  → frontend/src/data/generated/quranStoryConnectionGraph.json
  → docs/generated/quran-story-connection-graph-summary.md
                │
                ▼
frontend/src/pages/StoryAtlasConnectionsPage.tsx (UI)
frontend/src/components/stories/WhereElseMentionedPanel.tsx
frontend/src/components/stories/ConnectionQuiz.tsx
                │
                ▼
scripts/validate-quran-story-connections.ts
scripts/validate-quran-story-connection-graph.ts
scripts/validate-quran-story-chronology.ts
backend/tests/unit/test_quran_story_connections.py
```

## 2. Methodology

1. **Surah-by-surah scan**. The scanner iterates all 6236 ayahs, normalises
   Arabic by stripping tashkeel/dagger-alif/small-letter marks and unifying
   common alif/ya/hamza/teh-marbuta forms, then matches the seed
   dictionary's normalised aliases.
2. **Word-boundary discipline**. The alias must end at a word boundary
   (non-Arabic letter) to avoid `الرس` matching `الرسول`. Leading
   attachment is permitted because Arabic clitics (و، ف، ل، ب، ك) routinely
   prefix nouns.
3. **Cluster grouping**. Adjacent ayahs (≤ 3 ayah gap) with overlapping
   entity sets become a candidate story cluster. Clusters are mapped back to
   existing `QURAN_STORIES_FIRST_BATCH` entries if the surah/ayah range
   intersects.
4. **Cross-surah aggregation**. Any entity that appears in ≥ 2 surahs
   becomes a `CrossSurahLink` with edge type `REPEATED_NARRATIVE` (when the
   entity has known stories) or `SAME_ENTITY`.
5. **Graph build**. The graph node set is `{surahs, ayah_ranges, entities,
   stories, segments, chronology groups}`. Edges include
   `MENTIONED_IN`, `APPEARS_IN_SURAH`, `PART_OF_STORY`, `SAME_EVENT`,
   `REPEATED_NARRATIVE`, `CHRONOLOGICALLY_BEFORE`, `REVELATION_ORDER_BEFORE`.
6. **Validators**. Three validators (scan, graph, chronology) enforce
   structural integrity and refuse approved relations without evidence.
7. **UI**. A read-only page at `/story-atlas/connections` exposes the five
   sections specified by the implementation plan.

## 3. Explicit vs. contextual matching

- `explicit_name` and `manual_seed` are the only detections that can be
  promoted to verified status — but only after reviewer sign-off.
- `alias_match` is what the scanner emits today; it always lives in
  `needs_review`.
- `story_context`, `pronoun_context`, and `tafsir_context` are reserved for
  future work (NER + tafsir-grounded extraction). The schema is in place but
  no scanner emits them today.

## 4. Source policy

All evidence cites `sourceIds` registered in
`frontend/src/data/sourceRegistry.ts`. The scanner and graph builder use
`concepts_dictionary` and `stories_manifest` (internal mappings) for
dictionary-derived edges and rely on the per-story `sourceIds` for
story-derived edges.

External research-grade resources (Quranic Arabic Corpus, Asbab al-Nuzul,
munasabah works) are not ingested yet. They are tracked as deferred
specialist-review items in
`docs/whole-quran-story-connection-reference-audit.md`.

## 5. Known limitations

- Detection is rule-based and string-only — no NER.
- The seed dictionary is hand-written; it is intentionally cautious and
  flagged `reviewedDictionary: false` for every entry.
- Some entities have generic aliases (الرسول, العزيز, الشيطان) — the
  scanner records candidate matches but marks them `needs_review`.
- Chronology data is broad and disputed where applicable.

## 6. Operational commands

```bash
npx tsx scripts/scan-quran-story-connections.ts
npx tsx scripts/build-quran-story-connection-graph.ts
npx tsx scripts/validate-quran-story-connections.ts
npx tsx scripts/validate-quran-story-connection-graph.ts
npx tsx scripts/validate-quran-story-chronology.ts
python -m pytest backend/tests/unit/test_quran_story_connections.py
```

## 7. Future improvements

- Quranic Arabic Corpus morphology import with verified GPL-compatible
  license.
- Trained NER model with Quran-domain training data.
- Tafsir-grounded contextual linking (asbab al-nuzul, munasabah).
- Teacher mode with curated walkthroughs.
- Printable story map export.
