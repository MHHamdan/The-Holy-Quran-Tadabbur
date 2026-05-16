# Quran Story Connection — Review Guide

This guide is for specialists (Quran/tafsir reviewers) approving or rejecting
candidate connections produced by the Whole-Quran Story Connection Atlas.

---

## 1. What the system gives you

For each surah the system surfaces:

- A list of **candidate entities** detected by alias matching.
- **Story cluster candidates** — adjacent ayahs that share entities.
- **Cross-surah links** — entities appearing in more than one surah.
- Optional links to existing curated stories from
  `frontend/src/data/quranStories.ts`.

Every item carries:

- `detectionType` (e.g. `alias_match`)
- `confidence` (0..1)
- `reviewStatus` (always `needs_review` from the scanner)
- `humanReviewRequired: true`

## 2. What the system never claims

- It does **not** make interpretive claims.
- It does **not** identify pronoun references.
- It does **not** assert chronology beyond the broad bands documented in
  `docs/quran-story-chronology-policy.md`.
- It does **not** quote Quranic text.

## 3. How to review a candidate

1. Open `/story-atlas/connections` and pick the surah or entity you want to
   examine.
2. Open the corresponding ayah in `/quran/:suraNo`.
3. Cross-reference at least one approved tafsir from the source registry.
4. Decide: `verified`, `needs_review` (leave as-is), or `rejected`.
5. Open `/admin/review` and persist the decision via the review-workflow
   tool. The reviewer ID is stored alongside the verdict.

## 4. Approval criteria

A reviewer may mark a connection `verified` only if:

1. The Arabic text of the cited ayah explicitly names the entity, or
2. At least two registered tafsir sources independently identify the entity
   at that location, and
3. The connection is non-interpretive (it does not claim a moral, ruling, or
   meaning), and
4. The reviewer has recorded their reviewer ID in the workflow tool.

## 5. Rejection criteria

A reviewer should mark a connection `rejected` if:

- The match is a false positive from an ambiguous alias (e.g. "الرسول"
  matching a general reference to the messenger when the verse is about a
  different prophet).
- The match assumes a pronoun resolution that scholars dispute.
- The match relies on tafsir from a source not in `sourceRegistry.ts`.

## 6. Bulk-approval is forbidden

There is no API for bulk-approval. Every promotion is per-edge, per-reviewer.
The validator (`validate-quran-story-connection-graph.ts`) will reject any
verified edge that lacks evidence.

## 7. Reporting issues

If the scanner is producing many false positives for a given alias, file the
issue with:

- the entity ID,
- the offending alias,
- one or more example ayahs.

The likely fix is to tighten or remove the alias in
`frontend/src/data/quranStoryEntitySeeds.ts` and rerun the scanner.

## 8. Audit trail

All scan outputs are timestamped (`generatedAt` in the JSON). Re-running
the scanner regenerates the output but does not retroactively change
reviewer decisions stored in the review-workflow tool.
