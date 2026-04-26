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

## What This Module Does Not Do

- Does not generate tafsir — all explanations are authored and source-attributed
- Does not translate Arabic Quran text — text is always fetched from the database
- Does not resolve scholarly disputes — disputed matters are preserved as `disagreementNotes`
- Does not include Isra'iliyyat unless explicitly verified in the canonical tafsir
- Does not store Arabic Quran text as string literals anywhere in the codebase
