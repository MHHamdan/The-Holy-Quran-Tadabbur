# Quran Story Entity Taxonomy

This file describes the entity taxonomy used by the Whole-Quran Story
Connection Atlas. The TypeScript types live in
`frontend/src/types/quranStoryConnection.ts`; the seed dictionary lives in
`frontend/src/data/quranStoryEntitySeeds.ts`.

---

## 1. Entity types

| Type | Examples |
|---|---|
| `prophet` | Adam, Nuh, Ibrahim, Musa, Isa, Muhammad ﷺ, Dhul-Kifl |
| `person` | Maryam, Firawn, Haman, Qarun, Talut, Bilqis, Luqman |
| `people_or_nation` | Bani Israel, Aad, Thamud, Madyan, Quraysh, Ashab al-Kahf |
| `place` | Makkah, Madinah, Egypt, Sinai, Babylon, Saba, Al-Ahqaf |
| `animal` | Cow, she-camel, hoopoe, ants, dog of the cave, whale, bee |
| `object` | Ark, staff of Musa, tablets, table spread, throne of Bilqis |
| `event` | Sea crossing, flood, fire of Ibrahim, virgin birth |
| `angel` | Jibreel, Mikail, Angel of Death |
| `jinn` | Reserved |
| `title_or_role` | Reserved |
| `family_relation` | Reserved |
| `abstract_concept` | Reserved (use existing concept graph instead) |
| `unknown` | Fallback only |

## 2. Detection types and their semantics

| `detectionType` | Confidence | Default `reviewStatus` | Use |
|---|---|---|---|
| `explicit_name` | 0.95 | needs_review (until reviewer) | Named explicitly with a non-ambiguous alias |
| `alias_match` | 0.70 | needs_review | Common-form alias match (current scanner default) |
| `story_context` | 0.50 | needs_review | Story-data-derived inference; not produced by current scanner |
| `pronoun_context` | 0.35 | needs_review | Pronoun resolution; future work |
| `tafsir_context` | 0.60 | needs_review | Tafsir-grounded extraction; future work |
| `manual_seed` | 0.85 | needs_review | Hand-entered manual link by an editor |

The scanner never emits `verified` automatically. Promotion happens only in
the reviewer workflow.

## 3. Entity record schema

```ts
interface QuranStoryEntity {
  entityId: string;
  type: QuranStoryEntityType;
  labelArabic: string;
  labelEnglish: string;
  aliasesArabic: string[];
  aliasesEnglish: string[];
  transliterations?: string[];
  quranReferences: QuranEntityReference[];
  relatedStories: string[];
  relatedEntities: string[];
  relatedThemes: string[];
  chronologicalGroup?: string;
  notesArabic?: string;
  notesEnglish?: string;
  warnings: string[];
  reviewedDictionary: boolean;
}
```

## 4. Rules

1. Every entity has at least one Arabic alias. Aliases are stored without
   diacritics (the scanner normalises both sides before comparing).
2. Short or generic aliases must list a warning in `warnings[]` so the
   scanner and downstream display can flag the occurrence as low-confidence.
3. `reviewedDictionary` is `false` for every seed entry until a scholar
   approves it through the review workflow. UI must show the
   `needs_review` badge when this is `false`.
4. `chronologicalGroup` IDs must exist in
   `frontend/src/data/quranStoryChronologySeeds.ts`.
5. `relatedStories[]` IDs must exist in
   `frontend/src/data/quranStories.ts` (`QURAN_STORIES_FIRST_BATCH`).
6. `relatedEntities[]` IDs must exist as another `entityId` in the seed
   list — circular references are allowed.
7. The Arabic label is human-readable (e.g., "آدم عليه السلام"); aliases
   are the surface forms used in the corpus.

## 5. Why so many `needs_review`?

Because Quranic interpretation is not a string-matching problem. The seed
dictionary's role is to surface candidate matches for review, not to make
authoritative claims about whom a verse refers to. A reviewer
(`/admin/review`) is the only authority that can flip a record from
`needs_review` to `verified`.
