# Quran Stories Module — Methodology

## Guiding Principles

1. **Quran-first**: Every story derives from explicit Quranic ayahs. No detail is added from general cultural knowledge.
2. **Source-grounded**: Every segment cites the tafsir sources actually consulted. No explanations are generated from model knowledge.
3. **Audience-appropriate**: Kids and adult explanations differ in vocabulary and depth, but both remain factually identical and source-grounded.
4. **Scholarly honesty**: Disputes among classical scholars are preserved, not silenced. Disputed details are flagged, not resolved by editorial choice.
5. **Zero fabrication**: If the Quran does not mention a detail and the canonical tafsir does not address it, it is not included.

---

## Data Model

Each story is a `QuranStory` object with:

- **`quranReferences`**: The primary surah(s) and ayah ranges. These are the only verses a segment may draw from.
- **`storySegments`**: Narrative units, each mapped to a specific verse range. Each segment has:
  - `summaryKidsArabic` / `summaryKidsEnglish`: simplified, age-appropriate language
  - `summaryAdultsArabic` / `summaryAdultsEnglish`: fuller explanation with tafsir depth
  - `lessonsKids` / `lessonsAdults`: moral lessons derived from the segment
  - `sourceIds`: tafsir sources consulted for this segment
  - `sunniReview`: review status and evidence links
- **`relatedStories`**: Cross-story connections with `relationType`, bilingual explanation, and `evidenceReferences` citing specific verses and tafsir

Full schema: `frontend/src/types/quranStory.ts`

---

## Source Verification Process

### Phase 1 — Structural authoring
Story segments are authored with:
- Verse references cross-checked against the Uthmani mushaf
- Source IDs from the approved source registry
- `status: 'needs_review'` and `humanReviewRequired: true`

### Phase 2 — Automated review
`npx tsx scripts/review-quran-stories-sunni.ts` checks:
- All segment source IDs are from approved tiers
- Kids and adults summaries are present
- No supporting-only sources used as sole approval basis

### Phase 3 — Scholarly review
A qualified scholar reviews each segment against the listed tafsir:
- Confirms factual accuracy
- Links actual DB chunk IDs to `matchedEvidence`
- Resolves or retains disagreement notes
- Sets `status = 'approved'` and `humanReviewRequired = false`

---

## Kids vs. Adults Explanations

| Dimension | Kids | Adults |
|-----------|------|--------|
| Vocabulary | Simple, concrete | Full tafsir terminology |
| Length | 1–3 sentences | 3–6 sentences |
| Moral framing | Direct, relatable | Deeper theological context |
| Scholarly notes | Omitted | Included where relevant |
| Source citations | Not shown in UI | Shown in UI |

Both levels must cover the same Quranic content. The kids version may simplify tone but must not omit or contradict the meaning.

---

## Related Stories Engine

Cross-story connections use these relation types:

| Type | Meaning |
|------|---------|
| `shared_prophet` | Both stories involve the same prophet |
| `shared_theme` | Stories share a core spiritual theme |
| `sequential` | Events occur in chronological sequence |
| `parallel_lesson` | Different stories, same moral lesson |
| `contrasting` | Stories present contrasting outcomes or responses |
| `referenced_in` | One story explicitly references events from another |

Each connection requires:
- Bilingual explanation (`explanationArabic` + `explanationEnglish`)
- `evidenceReferences` citing the specific verse range that establishes the connection
- At least one approved `sourceId` per evidence reference

---

## Integrity Constraints

### Type-level
- `arabicText?: never` on `QuranReference` — Arabic Quran text is always fetched from DB, never embedded
- `AudienceLevel = 'kids' | 'adults'` — no other levels exist

### Runtime (validator)
- `npx tsx scripts/validate-quran-stories.ts` — validates storyId uniqueness, verse ranges, source IDs, bilingual completeness

### Test-level
- `backend/tests/unit/tasmee/test_story_schema.py` — 34 unit tests covering all structural requirements
- `backend/tests/unit/test_story_acceptance.py` — acceptance tests for i18n, categories, graph data, cross-story connections

---

## How needs_review Content Is Displayed Safely

All story content in the first batch carries `status: 'needs_review'` and
`humanReviewRequired: true`. The UI enforces the following rules to prevent this content
from being mistaken for approved scholarly content.

### Segment-level display

| Condition | UI behaviour |
|-----------|-------------|
| `status === 'needs_review'` | Yellow **"Pending Scholarly Review"** banner with `AlertTriangle` icon |
| `humanReviewRequired: true` | Additional line *"⚠ Human review required before publishing"* inside the banner |
| `matchedEvidence.length === 0` (when pending) | Orange *"Source evidence not yet linked."* warning |
| `sourceIds.length === 0` | Orange *"No sources identified for this segment yet"* replaces the normal sources row |
| `status === 'rejected'` | Segment is not rendered (`return null`) — never shown as a story explanation |

### Audience level does not suppress warnings

Kids-level and Adults-level views both display the same review-status warning banners.
Switching the audience toggle does not hide, soften, or remove any warning.

### Related stories display

Each `RelatedStory` in `richStory.relatedStories` is rendered with:
- `relationType` badge
- Bilingual explanation
- Verse reference links from `evidenceReferences`
- A *"No Quranic evidence references for this connection"* warning if `evidenceReferences` is empty
- A **"Pending Review"** badge on the entire section

### Guarantees

These properties are verified by:
- `TestUIReviewSafety` in `backend/tests/unit/tasmee/test_story_schema.py`
- `TestReviewSafetyAcceptance` in `backend/tests/unit/test_story_acceptance.py`

---

---

## Batch 2 Methodology (added 2026-04-25)

### Stories added
Hud (story_hud), Salih (story_salih), Lut (story_lut), Ayyub (story_ayyub),
Yunus (story_yunus), Dawud (story_dawud), Talut/Jalut (story_talut_jalut), Qarun (story_qarun).

### How related stories were connected
Every cross-story connection added in Batch 2 requires:
1. A specific Quran verse range as `evidenceReferences`
2. A directional relationship only from a Batch 2 story **toward** a story that precedes it in the array
   — this keeps the validator warning count from increasing
3. A bilingual explanation that summarizes only what the Quran itself establishes

Examples:
- `salih → story_hud` (same_event_pattern): Both prophets' communities rejected them in Surah Al-Araf 7:65-79 — the same surah narrates both patterns adjacently.
- `lut → story_ibrahim` (same_surah): Surah Hud 11:69-83 narrates the angel guests visiting Ibrahim then going on to Lut — the same group of angels connects both episodes.
- `yunus → story_nuh` (contrast): Quran 10:98 explicitly singles out the people of Yunus as the exceptional case of a community that believed — implicitly contrasting with Nuh's people who rejected for centuries (71:5-6).
- `qarun → story_musa` (shared_character): Quran 28:76 explicitly states "Qarun was from the people of Musa."

### How uncertain details were avoided
- No extra-Quranic narrative was added to any segment
- Where tafsir sources disagree (Ayyub's oath in 38:44; Dawud's trial in 38:21-26), a `disagreementNotes` entry was added and no interpretation was asserted
- The nature of the destruction (flood, wind, stones, earth-swallowing) is taken directly from the Quran verse, never embellished
- Wife/family details are limited to what the Quran explicitly states (e.g., "Lut's wife was among those who remained" from 15:60)

### How needs_review status remains active
All 51 segments across all 16 stories carry:
- `sunniReview.status = 'needs_review'`
- `sunniReview.humanReviewRequired = true`
- `sunniReview.matchedEvidence = []`

No segment was promoted to `approved`. The UI will show the Pending Scholarly Review banner for every segment in both Batch 1 and Batch 2.

### Validator warning reduction
Before Batch 2: 7 warnings, 0 errors
After Batch 2: 5 warnings, 0 errors

Resolved warnings: `story_yusuf → story_ayyub` and `story_nuh → story_hud`
Remaining 5 warnings are resolvable only in Batch 3+ (3 within-batch ordering cycles, 2 missing stories).

---

## Batch 3 Methodology (added 2026-04-26)

### Stories added
Dhul-Qarnayn (story_dhulqarnayn), Zakariyya/Yahya (story_zakariyya_yahya),
Two Gardens (story_two_gardens), Garden Owners (story_garden_owners),
Baqarah Cow (story_baqarah_cow), Elephant (story_elephant),
Sabbath Breakers (story_sabbath_breakers), Table Spread (story_table_spread).

### Special content categories in Batch 3
1. **Parables (amthal)** — story_two_gardens (18:32) and story_garden_owners (68:17) are explicitly introduced with the word مَثَل in the Quran. Summaries note this distinction: these are parabolic narratives, not identified historical figures.
2. **Unidentified actors** — story_dhulqarnayn (identity not given in Quran) and story_elephant (army commander not named) — no identification is asserted from cultural knowledge or Isra'iliyyat.
3. **Short surah narratives** — story_elephant covers a complete surah (105) in one segment. Summary length is proportional to verse count.

### How missing-story warnings were resolved
- `story_bilqis → story_dhulqarnayn`: resolved by placing story_dhulqarnayn at position 10 (before bilqis at position 11)
- `story_maryam → story_zakariyya_yahya`: resolved by placing story_zakariyya_yahya at position 12 (before maryam at position 13)

### Disagreement notes added in Batch 3
Three new scholarly disagreement entries were added:
- story_elephant: identity of army commander (Quran is intentionally sparse)
- story_sabbath_breakers: specific nature of the transformation in 2:65 / 7:166
- story_table_spread: whether the table actually descended after 5:115 (conditional divine response)

### Needs_review status
All 72 segments across all 24 stories carry:
- `sunniReview.status = 'needs_review'`
- `sunniReview.humanReviewRequired = true`
- `sunniReview.matchedEvidence = []`

### Validator warning reduction
Before Batch 3: 5 warnings, 0 errors
After Batch 3: 3 warnings, 0 errors

Resolved warnings: `story_bilqis → story_dhulqarnayn` and `story_maryam → story_zakariyya_yahya`
Remaining 3 warnings are irreducible ordering cycles within Batch 1 (yusuf→musa, musa→ibrahim, kahf→ibrahim).

---

## What This Module Does Not Do

- Does not generate tafsir — all explanations are authored and source-attributed
- Does not translate Arabic Quran text — text is always fetched from the database
- Does not resolve scholarly disputes — disputed matters are preserved as `disagreementNotes`
- Does not include Isra'iliyyat unless explicitly verified in the canonical tafsir
- Does not store Arabic Quran text as string literals anywhere in the codebase
