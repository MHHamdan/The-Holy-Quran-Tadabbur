# Phase 5: Similarity Test Cases

**Date:** 2026-04-27

These test cases specify expected behavior for the KG-based verse similarity system.

---

## 1. Yusuf Patience Ayahs

**Query:** Surah 12 (Yusuf), any ayah in story_yusuf segments

**Expected relation type:** `SAME_STORY_SEGMENT` or `SAME_STORY`
**Expected evidence source:** `ibn_kathir` (from story manifest segments)
**Expected warning:** "All story-based relations await scholarly review."
**Expected status:** `needs_review`
**Expected humanReviewRequired:** `true`

**Explanation should contain:** Reference to "story of Yusuf" or "قصة يوسف" — not invented tafsir

---

## 2. Musa / Firawn Ayahs

**Query:** Any ayah in `story_musa_firawn` segments

**Expected relation type:** `SAME_STORY_SEGMENT` for ayahs in the same segment
**Expected relation type:** `SAME_STORY` for ayahs in different segments
**Expected evidence source:** `ibn_kathir`
**Expected status:** `needs_review`

**Same-prophet test:** Ayahs mentioning Musa from different stories (e.g., `story_musa_firawn`
and `story_musa_khidr`) should connect via `SAME_PROPHET_OR_PERSON` when person overlap exists.

---

## 3. People of the Cave (Ashab al-Kahf)

**Query:** Surah 18 ayahs in story_ashab_kahf segments

**Expected relation type:** `SAME_STORY_SEGMENT`
**Expected evidence source:** Story manifest evidence
**Expected status:** `needs_review`

---

## 4. Maryam / Zakariyya Related Ayahs

**Query:** Ayahs in stories covering Maryam and Zakariyya

**Expected:** `SAME_THEME` or `SAME_STORY` if both appear in the same story
**Expected evidence source:** Story manifest
**Expected status:** `needs_review`
**Note:** If the stories are separate but linked, `inter_story_connections` may produce
`PARALLEL_EVENT_PATTERN` or continuation edges.

---

## 5. Qarun and Owner of Two Gardens

**Query:** Ayahs in story_qarun and story_two_gardens

**Expected:** `SAME_THEME` (both involve wealth/arrogance)
**Expected:** Inter-story edge if `inter_story_connections` links them
**Expected status:** `needs_review`

---

## 6. Hud/Salih/Nuh/Lut Prophet Rejection Pattern

**Query:** Ayahs in stories of Hud, Salih, Nuh, Lut

**Expected:** `SAME_PROPHET_OR_PERSON` for single-prophet ayahs
**Expected:** `PARALLEL_EVENT_PATTERN` if inter_story_connections links rejection patterns
**Expected status:** `needs_review`

**Same-theme test:** All four stories should share theme `punishment` or `prophets`.
Theme-based edges should appear for representative ayahs.

---

## 7. Ayat al-Kursi — Allah's Names/Attributes

**Query:** 2:255 (Ayat al-Kursi)

**Note:** This ayah is not currently in a story segment in the manifest.
**Expected:** Limited story-based edges (ayah may not appear in segments)
**Expected:** If embedding similarity is enabled (Qdrant populated), semantic candidates
may appear as `experimental`
**Expected:** No religious interpretation invented in explanations

**Guardrail test:** The explanation for any returned relation must NOT contain invented
statements about the meaning of Ayat al-Kursi's relationship to other ayahs.

---

## 8. Adjacent Ayah Test

**Query:** Any ayah with an adjacent ayah (same story segment)

**Expected:** Adjacent same-segment ayahs score highest (`SAME_STORY_SEGMENT`)
**Expected:** Adjacent same-story ayahs (different segments) score lower (`SAME_STORY`)
**Expected:** Adjacent same-surah ayahs with no story/concept relation score lowest

**Guardrail:** Adjacency alone (`ADJACENT_AYAH` rule) must not produce `needs_review` or
`approved` edges — adjacency is `experimental` or excluded when no other evidence exists.

---

## 9. Same-Surah-Only Weak Relation Test

**Query:** Two ayahs in the same surah with no shared story/concept/theme

**Expected:** Score below `min_score=0.20` default threshold
**Expected:** Not returned in default results
**Expected:** If returned, status must be `experimental`
**Expected:** No story or concept evidence items

**Guardrail:** Same-surah alone must not produce a `needs_review` result.

---

## 10. Unrelated Ayahs Test

**Query:** Ayah from a surah with no story coverage (e.g., surah 96, ayah 5)

**Expected:** Empty result set when `require_evidence=True` (default)
**Expected:** No fabricated connections
**Expected:** No semantic-only results unless `includeExperimental=True`

---

## 11. Invalid Verse Test

**Query:** 115:1 (surah 115 does not exist)

**Expected:** Empty result set
**Expected:** No exception, safe error handling
**Expected:** No Quran text mutation

---

## 12. Path Explanation Test

**Query:** find_path(2, 30, 7, 11) — both ayahs are in story_adam (both stories reference Adam)

**Expected:** Path with ≥ 2 steps through a story node
**Expected:** Each step has `nodeId`, `nodeType`, `label`
**Expected:** Step labels do not contain invented tafsir

---

## Acceptance Criteria Summary

| Test Case | Criterion | Required |
|---|---|---|
| All tests | Quran text unchanged | Yes |
| All tests | KG edges have evidence | Yes |
| Tests 8, 9 | Semantic-only edges hidden by default | Yes |
| Test 7 | `includeExperimental=False` by default | Yes |
| Tests 1–6 | Story-derived edges reference validated stories | Yes |
| All tests | Source IDs validated | Yes |
| All tests | KG validator passes | Yes |
| All tests | Full backend tests pass | Yes |
| All tests | UI shows why ayahs are related | Yes |
| All tests | UI shows review/safety warnings | Yes |
