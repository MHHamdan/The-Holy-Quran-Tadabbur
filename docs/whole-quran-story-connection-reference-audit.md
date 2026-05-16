# Whole-Quran Story Connection — Reference Audit

This document records the external references that informed the design of the
Whole-Quran Story Connection Atlas. It also documents which design ideas were
adopted, which were deferred for specialist review, and the source/citation
policy that governs the connection layer.

---

## 1. External references reviewed

Live web access was **not used** for this phase. All external references listed
below are entered as **deferred specialist-review items** — not as ingested
data. None of the following sources contribute text, tafsir, or factual
authority to the connection graph. They only inspire structure.

When a reference is later added to the platform, it must be added to
`frontend/src/data/sourceRegistry.ts` with a verified license and
`reliabilityLevel` and re-validated by `validate-quran-integrity.ts`.

| Reference | Why relevant | Status |
|---|---|---|
| Quranic Arabic Corpus (corpus.quran.com) | Named-entity extraction, root/lemma graph, person/place ontology | Already in `sourceRegistry.ts` as `quranic_arabic_corpus` (experimental, do not display); ingestion deferred |
| Tanzil (tanzil.net) revelation-order tables | Revelation-order metadata caveats | Not ingested; revelation order seed marked `needs_review` and only references scholar consensus disagreement |
| Altafsir.com / Tafsir Center | Source-grounded tafsir navigation, refusal of unsourced interpretation | Not ingested; design principle adopted — connection graph never emits interpretation |
| Al-Itqan fi Ulum al-Quran (Al-Suyuti) | Mushaf vs. revelation-order distinction | Used indirectly via `surah_atlas_metadata` source (already marked `needs_review`) |
| Standard Sunni tafsir works (Ibn Kathir, Tabari, Qurtubi, Saadi) | Story-grounded relation evidence | Already in registry as `ibn_kathir`/`ibn_kathir_ar`/`tafsir` tables — used as `sourceIds` on edges |

---

## 2. Design ideas adopted (inspiration only)

- **Entity taxonomy**: 12 entity categories (prophet, person, people_or_nation,
  place, animal, object, event, angel, jinn, title_or_role, family_relation,
  abstract_concept, unknown). Inspired by Quran ontology efforts, but each
  entity is defined locally and gated by review.
- **Explicit vs. contextual detection**: every detected match carries a
  `detectionType` of `explicit_name`, `alias_match`, `story_context`,
  `pronoun_context`, `tafsir_context`, or `manual_seed`. Only `explicit_name`
  and `manual_seed` can ever bypass `needs_review` and only when paired with
  reviewer sign-off.
- **Three chronology layers**: mushaf order (verified, from
  `data/raw/quran_uthmani.json`), story-world chronology (broad and cautious,
  `needs_review`), and revelation order (cited or marked `disputed`).
- **Edge evidence requirement**: every edge in the connection graph must carry
  at least one `evidenceReferences[]` entry referencing surah/ayah and one or
  more `sourceIds`.

---

## 3. What is safe to implement now

- Surah-by-surah scan that maps **explicit Arabic name strings and registered
  aliases** to ayah ranges (does not produce tafsir).
- Aggregation of detected entities into per-entity profiles and per-surah
  indexes.
- Building a connection graph whose nodes are surahs, ayah ranges, entities,
  stories, themes, and chronology groups. Edges reference existing
  `tafseer_chunks`, stories, or explicit ayah occurrences.
- Surfacing cross-surah occurrences ("Where else is this mentioned?") so long
  as each link cites its evidence and shows its review status.
- A read-only UI at `/story-atlas/connections` and a learning quiz that only
  draws from explicit, ayah-verified data points.

## 4. What requires specialist review

- All `story_context`, `pronoun_context`, and `tafsir_context` detections.
- All `chronologyType: revelation_order` claims beyond the entries marked as
  `disputed`.
- Any new entity not currently in `curated_concepts.json` or
  `quranStoryEntitySeeds.ts`.
- Translation of `chronologically_before` to absolute timeline statements.
- Promotion of any seed dictionary entry to `reviewedDictionary = true`.

## 5. Source / citation policy

1. The Quran text comes only from `data/raw/quran_uthmani.json`. Connection
   data **never** copies ayah text into JSON or TypeScript — only `surahNumber`
   and `ayahStart`/`ayahEnd`.
2. Every edge or candidate connection lists `sourceIds` that exist in
   `sourceRegistry.ts`.
3. The scan script uses the seed dictionary for **candidate** detection only;
   it never marks results as `verified` automatically.
4. The display layer must show review status, evidence, and warnings on every
   inferred connection.
5. External academic resources may inspire structure but are not added to the
   registry without license review.

## 6. Limitations

- The seed dictionary is a starting list. It does **not** cover every Arabic
  alias, pronoun reference, or contextual mention.
- Detection is string-based; it cannot reliably resolve pronouns, ellipsis, or
  asbab al-nuzul context.
- Revelation order is a long-standing area of scholarly disagreement; the
  chronology layer intentionally avoids claiming a single accepted order.
- The atlas does not replace tafsir or scholarly study. It is a navigation
  layer.
- No NER model is used; this is rule-based scanning only.

## 7. Future work (deferred)

- Importing Quranic Arabic Corpus morphology with verified licensing.
- Integrating asbab al-nuzul ("Asbab al-Nuzul" by al-Wahidi) as a separate,
  source-attributed layer.
- Integrating munasabah (inter-surah/inter-ayah coherence) literature with
  scholar review.
- Teacher mode with curated story-by-story walkthroughs.
- Printable story map and downloadable connection PDFs.
