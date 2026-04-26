# Sunni Source Review Policy — Quran Stories Module

## Purpose

Every story segment displayed in the Tadabbur platform must be traceable to verified classical Sunni tafsir. This policy defines which sources are trusted, the review workflow, and the standards required before a segment can be marked `approved`.

---

## Source Tiers

### Canonical Sources (highest authority)

These sources are the primary approval basis. A segment can only reach `approved` status if at least one canonical or verified source appears in `reviewedAgainst`.

| Source ID | Scholar | Title |
|-----------|---------|-------|
| `ibn_kathir` / `ibn_kathir_ar` / `ibn_kathir_en` | Ibn Kathir (d. 774 AH) | Tafsir al-Qur'an al-Azim |
| `tabari` / `tabari_ar` / `tabari_en` | al-Tabari (d. 310 AH) | Jami' al-Bayan |
| `qurtubi` / `qurtubi_ar` / `qurtubi_en` | al-Qurtubi (d. 671 AH) | al-Jami' li-Ahkam al-Qur'an |

### Verified Sources (supporting authority)

These sources may appear in `reviewedAgainst` alongside canonical sources, but cannot be the sole basis for approval.

| Source ID | Scholar | Title |
|-----------|---------|-------|
| `saadi` / `saadi_ar` / `saadi_en` | al-Sa'di (d. 1376 AH) | Taysir al-Karim al-Rahman |
| `baghawi` / `baghawi_ar` / `baghawi_en` | al-Baghawi (d. 516 AH) | Ma'alim al-Tanzil |

### Supporting-Only Sources

These may inform background context but **must not appear in `reviewedAgainst`**. A segment listing them as the sole basis cannot be approved.

| Source ID | Notes |
|-----------|-------|
| `al_muyassar_ar` / `muyassar` | Summary tafsir; useful for clarity, not for approval |
| `tafheem_mawdudi_en` | Modern commentary; not from classical Sunni canon |

---

## Segment Status Definitions

| Status | Meaning | Display in UI |
|--------|---------|---------------|
| `needs_review` | Awaiting scholarly verification | Yellow review notice shown |
| `approved` | Verified against canonical/verified source | Normal display |
| `rejected` | Contains information not supported by approved sources | Must not be displayed |

All segments in the first batch ship as `needs_review` with `humanReviewRequired: true`.

---

## Approval Requirements

A segment may only be set to `approved` when all of the following are satisfied:

1. `reviewedAgainst` contains at least one canonical or verified source ID
2. `matchedEvidence` is populated with actual DB chunk IDs from the `tafseer_chunks` table
3. A qualified scholar has reviewed the segment text against the listed tafsir
4. `humanReviewRequired` is set to `false` after scholarly sign-off
5. Kids and adults summaries both accurately reflect the tafsir content without addition or embellishment

---

## What May Never Appear in Story Content

- Isra'iliyyat (stories from Jewish/Christian tradition) presented as Quranic fact
- Details attributed to "tradition" or "history" without a traceable Quranic or hadith source
- Names, numbers, or locations not mentioned in the Quran and not verified in tafsir
  - Exception: `warnings` field may note "Bilqis is not named in the Quran" while still presenting the story
- Arabic Quran text hardcoded as string literals (always fetched from DB)
- Invented moral lessons not present in the tafsir

---

## Scholarly Disagreement Handling

When classical scholars disagree (e.g., number of sleepers in Kahf, prophet status of Luqman):

1. Add each disagreement to `sunniReview.disagreementNotes`
2. Present the mainstream position in the summary
3. Note the disagreement in the UI's review banner
4. Do not present one opinion as settled fact

---

## Review Workflow

```
Segment authored as needs_review
        ↓
Automated review script checks structure (scripts/review-quran-stories-sunni.ts)
        ↓
Human scholar reviews segment against listed tafsir
        ↓
Scholar links actual DB chunk IDs → matchedEvidence populated
        ↓
Scholar sets status = 'approved', humanReviewRequired = false
        ↓
Segment displayed normally in UI
```

---

## Running the Automated Review

```bash
npx tsx scripts/review-quran-stories-sunni.ts
```

Output: `docs/generated/story-sunni-review-report.md`

Exit code 0 = review completed (may still have warnings/info notes)  
Exit code 1 = structural errors found (missing summaries, unknown sources)

---

## References

- Full content policy: `docs/quran-content-policy.md`
- Source registry: `frontend/src/data/sourceRegistry.ts`
- Phase 2.5 source validation: `docs/phase-2-5-strict-source-validation.md`
- Story type definitions: `frontend/src/types/quranStory.ts`
