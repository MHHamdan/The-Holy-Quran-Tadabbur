# Quran Story Chronology Policy

This policy governs how the Tadabbur Al-Quran platform treats time, sequence,
and order across the connection atlas.

---

## 1. Three orders, not one

Always distinguish:

1. **Mushaf order** — the printed sequence of surahs and ayahs in the
   `mushaf`. This is the only order that is fully verified and uncontested.
2. **Story-world chronology** — the narrative order of prophets and events
   inside the stories of the Quran. The Quran tells these stories
   thematically, not chronologically. Even broad ordering is approximate.
3. **Revelation order (نزول)** — the order in which surahs and ayahs were
   revealed to the Prophet ﷺ. Scholars differ on the order, and many surahs
   are composite (revealed in parts).

Never display these orderings as a single timeline. The UI keeps them in
separate views and labels each one with the appropriate caveat.

## 2. Sources

- Mushaf order is taken from `data/raw/quran_uthmani.json` and validated by
  `validate-quran-integrity.ts`.
- Story-world chronology lives in
  `frontend/src/data/quranStoryChronologySeeds.ts` (`STORY_WORLD_CHRONOLOGY`).
  It maps prophets to broad bands (primordial → antediluvian → ancient
  Arabia → patriarchs → Israelite → kingdom → late Israelite → prophetic era).
- Revelation order lives in `REVELATION_ORDER_SEEDS`. Each entry cites at
  least one source in `sourceIds` and is `reviewStatus: 'needs_review'`.

## 3. Certainty levels

Every chronology entry carries a `certainty` field:

- `high` — Quran-internal explicit ordering, or near-universal scholarly
  agreement (e.g. Surah Al-Alaq as the first revealed).
- `medium` — Sunni-mainstream agreement, with minor disagreement on details.
- `low` — Plausible but contested.
- `disputed` — Scholars actively differ; do not display as fact.

## 4. Display rules

- Story-world chronology is shown as **bands**, not arrows between
  individuals. We do not draw a line from "Adam → Nuh → Hud → Salih →
  Ibrahim" because some gaps are unknown.
- Revelation order is shown with an explicit warning banner:
  - Arabic: "هذا الترتيب تقريبي أو محل مراجعة عند وجود خلاف."
  - English: "This order is approximate or requires review where scholarly
    disagreement exists."
- Disputed entries are rendered with a yellow `needs_review` badge and a
  link to the source citation.

## 5. Rules for the validator

`validate-quran-story-chronology.ts` enforces:

- Every story-world entry has a `chronologicalGroup`-style `itemId` that
  some entity references.
- Every revelation-order entry has either at least one `sourceIds` entry or
  `certainty: 'disputed'`.
- No revelation-order entry is `reviewStatus: 'verified'` without source +
  reviewer sign-off.
- No `chronologyType: 'story_world'` entry uses an absolute year.

## 6. Why this is conservative

Quran scholarship is rigorous about not making definitive claims that
overstep the evidence. This platform treats chronology as an aid to
exploration, not a substitute for scholarly study. When in doubt, the
default presentation is the mushaf order.

## 7. Future work

- Integrate Al-Wahidi's *Asbab al-Nuzul* with source-attributed mapping.
- Add per-ayah revelation-order layer (currently surah-level only).
- Reviewer workflow to promote individual chronology entries from
  `needs_review` to `verified` with stored reviewer ID.
