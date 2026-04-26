# Quran Stories — Scholar Review Checklist

Use this checklist when reviewing a story segment before setting `status = 'approved'`.

---

## Pre-Review (Automated)

Run before any human review begins:

```bash
npx tsx scripts/review-quran-stories-sunni.ts
npx tsx scripts/validate-quran-stories.ts
```

Both must exit with code 0 (or 0 errors, warnings allowed).

---

## Per-Segment Checklist

### 1. Verse Reference Accuracy
- [ ] `suraNo` and `ayahStart`/`ayahEnd` match the actual Quran text for this narrative unit
- [ ] The segment content does not draw from verses outside this range without declaring them in `quranReferences`
- [ ] No verse is misquoted or paraphrased in a way that changes meaning

### 2. Source Verification
- [ ] All `sourceIds` were actually consulted (not listed by assumption)
- [ ] At least one source is canonical (`ibn_kathir`, `tabari`, or `qurtubi`)
- [ ] `matchedEvidence` contains real chunk IDs from the `tafseer_chunks` table, not placeholder values
- [ ] No supporting-only source (`al_muyassar_ar`, `tafheem_mawdudi_en`) is listed in `reviewedAgainst`

### 3. Kids Summary Review
- [ ] Factually identical to the adults summary (no additional details, no omissions that change meaning)
- [ ] Language is age-appropriate (simple words, short sentences)
- [ ] No frightening imagery that goes beyond what the Quran itself states
- [ ] Arabic and English versions convey the same content

### 4. Adults Summary Review
- [ ] Accurately reflects the tafsir content of the listed sources
- [ ] No details added that cannot be traced to the verse range or canonical tafsir
- [ ] Scholarly context (e.g., different scholarly opinions) is noted where relevant
- [ ] Arabic and English versions convey the same content

### 5. Lessons Review
- [ ] Each lesson in `lessonsKids` and `lessonsAdults` is derivable from this segment's verse range
- [ ] No lesson is invented or inferred beyond what the tafsir supports
- [ ] Kids lessons use accessible language

### 6. Scholarly Disagreements
- [ ] All known disagreements among classical scholars on this segment are listed in `sunniReview.disagreementNotes`
- [ ] The summary text does not present a disputed point as settled fact
- [ ] If a detail is disputed (e.g., number, name, location), a note is present in `warnings`

### 7. Isra'iliyyat Check
- [ ] No detail from Jewish/Christian tradition is presented as Quranic fact without canonical tafsir grounding
- [ ] Any detail that originates from non-Quranic tradition is either:
  - Excluded from the summary, OR
  - Explicitly noted in `warnings` with "Not mentioned in the Quran; from tafsir tradition"

### 8. Final Sign-Off
- [ ] Set `sunniReview.status = 'approved'`
- [ ] Set `sunniReview.humanReviewRequired = false`
- [ ] Populate `sunniReview.matchedEvidence` with actual chunk IDs
- [ ] Record reviewer name and date in the relevant PR description (not in the code)

---

## Story-Level Checklist

After all segments in a story are approved:

- [ ] `relatedStories` connections have been verified — each `evidenceReferences` entry has real chunk IDs
- [ ] The story's `reliabilityLevel` accurately reflects the source strength:
  - `high`: All segments from Quran + Ibn Kathir/Tabari/Qurtubi
  - `medium`: Mix of canonical and verified sources
  - `low`: Primarily verified/supporting sources, limited canonical coverage
- [ ] `sourceIds` at the story level accurately reflect all sources used across segments

---

## Red Flags — Do Not Approve

If any of the following are present, do not approve and flag for editorial review:

- A segment claims the Quran says something the listed verse range does not say
- A proper noun (name, place) appears that is not in the Quran and not in the listed tafsir
- A number (years, people, distance) appears that differs from what the Quran states
- `matchedEvidence` is empty or contains placeholder strings like `"chunk_001"`
- The Arabic and English summaries describe different events or draw different conclusions

---

## UI Display — needs_review Content

These rules govern how the UI must render `needs_review` and `humanReviewRequired` content.
They are enforced by `TestUIReviewSafety` in `backend/tests/unit/tasmee/test_story_schema.py`
and `TestReviewSafetyAcceptance` in `backend/tests/unit/test_story_acceptance.py`.

### What must always be shown

- **Warning banner**: Every segment with `sunniReview.status === 'needs_review'` or
  `humanReviewRequired: true` must display a visible `AlertTriangle` banner labelled
  **"Pending Scholarly Review"**.
- **Human review flag**: If `humanReviewRequired: true`, the banner must include the additional
  line *"⚠ Human review required before publishing"*.
- **Missing evidence**: If `matchedEvidence` is empty and the segment is `needs_review`,
  display *"Source evidence not yet linked."*
- **Missing sources**: If `sourceIds` is empty, display *"No sources identified for this
  segment yet"* instead of hiding the sources row.

### What must never be shown

- The words "Approved", "Verified", or "Confirmed" as a badge or label for a `needs_review` segment.
- A `rejected` segment rendered as a normal story explanation (must `return null`).
- A review warning that is hidden or suppressed based on `audienceLevel`
  (kids and adults both see the same warning).

### Related Stories

- Related stories must display `evidenceReferences` (verse links) for each connection.
- If `evidenceReferences` is empty for a connection, show
  *"No Quranic evidence references for this connection"*.
- The entire related stories section carries a **"Pending Review"** badge until all
  connections are scholar-approved.

---

## Reference

- Source policy: `docs/sunni-source-review-policy.md`
- Methodology: `docs/quran-stories-methodology.md`
- Content policy: `docs/quran-content-policy.md`
- Type definitions: `frontend/src/types/quranStory.ts`
