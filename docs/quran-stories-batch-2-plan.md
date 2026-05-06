# Quran Stories — Batch 2 Plan
_Date: 2026-04-25_

---

## 1. Current State (Batch 1)

**8 stories in QURAN_STORIES_FIRST_BATCH:**
`story_yusuf`, `story_musa`, `story_kahf`, `story_ibrahim`, `story_nuh`,
`story_bilqis`, `story_maryam`, `story_luqman`

**Validator output before Batch 2 — 7 warnings, 0 errors:**

| Warning | Type | Resolvable by Batch 2? |
|---------|------|------------------------|
| `story_yusuf → story_musa` | Forward reference (both in Batch 1) | No — ordering cycle |
| `story_yusuf → story_ayyub` | Missing story | **Yes** — adding `story_ayyub` |
| `story_musa → story_ibrahim` | Forward reference (both in Batch 1) | No — ordering cycle |
| `story_kahf → story_ibrahim` | Forward reference (both in Batch 1) | No — ordering cycle |
| `story_nuh → story_hud` | Missing story | **Yes** — adding `story_hud` |
| `story_bilqis → story_dhulqarnayn` | Missing, not in Batch 2 | No — Batch 3+ |
| `story_maryam → story_zakariyya_yahya` | Missing, not in Batch 2 | No — Batch 3+ |

**Warnings after Batch 2: 5 (down from 7)**

---

## 2. Missing StoryIds to Resolve (Batch 2 Priority)

| Missing storyId | Referenced by | Priority |
|----------------|--------------|----------|
| `story_ayyub` | `story_yusuf` | High — resolves existing warning |
| `story_hud` | `story_nuh` | High — resolves existing warning |
| `story_salih` | (related to hud, thematic) | High |
| `story_lut` | (related to ibrahim, same surah Hud) | High |
| `story_yunus` | (related to nuh, contrast theme) | Medium |
| `story_dawud` | (related to bilqis/sulayman, chronological) | Medium |
| `story_talut_jalut` | (shares Dawud) | Medium |
| `story_qarun` | (shared character with Musa, explicit in 28:76) | Medium |

---

## 3. Batch 2 Stories

### 1. Story of Hud عليه السلام and Aad (`story_hud`)
| Field | Value |
|-------|-------|
| Slug | `hud` |
| Arabic title | قصة هود عليه السلام |
| English title | Story of Prophet Hud and Aad |
| References | 7:65-72, 11:50-60, 26:123-140, 46:21-26 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 2. Story of Salih عليه السلام and Thamud (`story_salih`)
| Field | Value |
|-------|-------|
| Slug | `salih` |
| Arabic title | قصة صالح عليه السلام |
| English title | Story of Prophet Salih and Thamud |
| References | 7:73-79, 11:61-68, 26:141-159, 54:23-31 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 3. Story of Lut عليه السلام (`story_lut`)
| Field | Value |
|-------|-------|
| Slug | `lut` |
| Arabic title | قصة لوط عليه السلام |
| English title | Story of Prophet Lut (Lot) |
| References | 7:80-84, 11:77-83, 15:61-77, 26:160-175 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 4. Story of Ayyub عليه السلام (`story_ayyub`)
| Field | Value |
|-------|-------|
| Slug | `ayyub` |
| Arabic title | قصة أيوب عليه السلام |
| English title | Story of Prophet Ayyub (Job) |
| References | 21:83-84, 38:41-44 |
| Segments | 2 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | 38:44 references an oath — classical scholars differ; do not assert |

### 5. Story of Yunus عليه السلام (`story_yunus`)
| Field | Value |
|-------|-------|
| Slug | `yunus` |
| Arabic title | قصة يونس عليه السلام |
| English title | Story of Prophet Yunus (Jonah) |
| References | 37:139-148, 21:87-88, 10:98, 68:48-50 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 6. Story of Dawud عليه السلام (`story_dawud`)
| Field | Value |
|-------|-------|
| Slug | `dawud` |
| Arabic title | قصة داود عليه السلام |
| English title | Story of Prophet Dawud (David) |
| References | 34:10-11, 21:78-80, 38:17-26, 2:251 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | 38:24 references an incident — classical scholars note the context carefully |

### 7. Talut and Jalut (`story_talut_jalut`)
| Field | Value |
|-------|-------|
| Slug | `talut-jalut` |
| Arabic title | قصة طالوت وجالوت |
| English title | Story of Talut and Jalut (Saul and Goliath) |
| References | 2:246-251 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 8. Story of Qarun (`story_qarun`)
| Field | Value |
|-------|-------|
| Slug | `qarun` |
| Arabic title | قصة قارون |
| English title | Story of Qarun (Korah) |
| References | 28:76-82, 29:39, 40:24 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

---

## 4. Array Order for Minimal Warnings

The QURAN_STORIES_FIRST_BATCH array is reordered to place stories before the stories that reference them:

```
Position  Story               Resolves
1         story_ayyub         (needed by story_yusuf at pos 4)
2         story_hud           (needed by story_nuh at pos 9)
3         story_salih         
4         story_yusuf         (yusuf→ayyub: RESOLVED; yusuf→musa: still forward)
5         story_musa          (musa→yusuf: RESOLVED; musa→ibrahim: still forward)
6         story_kahf          (kahf→ibrahim: still forward)
7         story_ibrahim       (ibrahim→musa: RESOLVED; ibrahim→kahf: RESOLVED)
8         story_lut           (lut→ibrahim: RESOLVED)
9         story_nuh           (nuh→hud: RESOLVED!)
10        story_bilqis        (bilqis→dhulqarnayn: still missing)
11        story_maryam        (maryam→zakariyya_yahya: still missing)
12        story_luqman        (luqman→ibrahim: RESOLVED)
13        story_yunus         (yunus→nuh: RESOLVED)
14        story_dawud         (dawud→bilqis: RESOLVED)
15        story_talut_jalut   (talut→dawud: RESOLVED; talut→musa: RESOLVED)
16        story_qarun         (qarun→musa: RESOLVED)
```

---

## 5. Evidence-Backed Cross-Story Connections Added in Batch 2

| Connection | relationType | Evidence | New warning? |
|-----------|-------------|---------|-------------|
| salih → story_hud | same_event_pattern | 7:65-72 (hud), 7:73-79 (salih) | No (hud before salih) |
| lut → story_ibrahim | same_surah | 11:69-76 (ibrahim guests), 11:77-83 (lut guests) | No (ibrahim before lut) |
| yunus → story_nuh | contrast | 10:98 (yunus people believe), 71:5-6 (nuh people reject) | No (nuh before yunus) |
| dawud → story_bilqis | chronological | 34:10-12 (dawud then sulayman in Saba) | No (bilqis before dawud) |
| talut_jalut → story_dawud | shared_character | 2:251 (dawud kills jalut) | No (dawud before talut) |
| talut_jalut → story_musa | same_theme | 2:246-248 (bani israel, divine choice) | No (musa before talut) |
| qarun → story_musa | shared_character | 28:76 (qarun from musa's people) | No (musa before qarun) |

---

## 6. Source Requirements

All Batch 2 stories use:
- `ibn_kathir` (canonical)
- `tabari` (canonical)
- `qurtubi` (canonical)

These are the same canonical sources as Batch 1. All match TRUSTED_SOURCE_IDS.

---

## 7. Human Review Status

All Batch 2 stories carry:
- `sunniReview.status = 'needs_review'`
- `sunniReview.humanReviewRequired = true`
- `sunniReview.matchedEvidence = []`

No Batch 2 story is marked `approved`. The `needs_review` warning will be shown in the UI for all segments.

---

## 8. Expected Validation Results After Batch 2

| Check | Before | After |
|-------|--------|-------|
| Stories | 8 | 16 |
| Segments | 33 | ~57 |
| Warnings | 7 | 5 |
| Errors | 0 | 0 |

Remaining 5 warnings are all resolvable only in Batch 3+:
1. yusuf→musa (ordering cycle within batch 1)
2. musa→ibrahim (ordering cycle within batch 1)
3. kahf→ibrahim (ordering cycle within batch 1)
4. bilqis→dhulqarnayn (not yet added)
5. maryam→zakariyya_yahya (not yet added)
