# Quran Stories Inventory
_Tadabbur Al-Quran — Verified Story Index_
_Date: 2026-04-25_

---

## Usage Note

This inventory catalogs all Quranic stories currently in the platform manifest
(`data/manifests/stories.json`). Each story entry reflects the data actually present.

**Important:**
- Stories marked `needs_review` have Quran references but their explanations have NOT been validated against DB tafsir chunks
- Source IDs use short form (`ibn_kathir`, `tabari`, `qurtubi`, `saadi`) matching TAFSIR_CATALOG keys
- Arabic text is never written here; all Arabic titles come from the manifest's `name_ar` field
- Kids and adult summaries do not yet exist for most stories — they are flagged as `missing`

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Present and complete |
| ⚠️ | Present but needs review |
| ❌ | Missing — requires addition |
| 🔍 | Needs human verification before production |

---

## Priority Batch (8 Stories — First Implementation)

These 8 stories are selected for the first seed data batch. They are:
- Fully traceable to Quran references
- Central to user understanding
- Broadly covered by the four approved tafsir sources

---

### 1. Story of Yusuf عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_yusuf` |
| Arabic title | قصة يوسف عليه السلام ✅ |
| English title | Story of Prophet Yusuf (Joseph) ✅ |
| Main characters | Yusuf, Yaqub, Brothers, Aziz, Zulaykha ✅ |
| Main surah | 12 (Surah Yusuf — complete story) ✅ |
| Quran references | 12:4-6, 12:7-18, 12:19-22, 12:23-35, 12:36-53, 12:54-57, 12:58-87, 12:88-98, 12:99-101 ✅ |
| Segments | 9 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing (only general summary_en exists) |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Complete story in one surah — ideal for first batch |

---

### 2. Story of Musa عليه السلام and Pharaoh

| Field | Status |
|-------|--------|
| Story ID | `story_musa` |
| Arabic title | قصة موسى عليه السلام ✅ |
| English title | Story of Prophet Musa (Moses) ✅ |
| Main characters | Musa, Harun, Firawn, Bani Israel, Asiya ✅ |
| Surahs | 2, 7, 10, 11, 17, 18, 20, 26, 27, 28, 40, 43, 44, 79 ✅ |
| Quran references | Multiple cross-surah references ✅ |
| Segments | 9 ✅ |
| Sources | ibn_kathir, tabari, qurtubi, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Most mentioned prophet in the Quran (28:7-13, 20:9-48, 7:103-137, 26:10-68, 20:56-76, 20:77-98, 7:142-156, 18:60-82) |

---

### 3. Story of People of the Cave

| Field | Status |
|-------|--------|
| Story ID | `story_kahf` |
| Arabic title | قصة أصحاب الكهف ✅ |
| English title | Story of the People of the Cave ✅ |
| Main characters | Seven sleepers, their dog ✅ |
| Main surah | 18 ✅ |
| Quran references | 18:9-26 ✅ |
| Segments | 5 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Number of sleepers is disputed — multiple scholarly opinions must be noted |

---

### 4. Story of Ibrahim عليه السلام (Idols and Fire)

| Field | Status |
|-------|--------|
| Story ID | `story_ibrahim` (main) + `story_ibrahim_fire` (fire episode) |
| Arabic title | قصة إبراهيم عليه السلام ✅ |
| English title | Story of Prophet Ibrahim ✅ |
| Main characters | Ibrahim, his father Azar, his people, angels ✅ |
| Surahs | 2, 6, 9, 11, 14, 15, 16, 19, 21, 22, 26, 29, 37, 43, 51, 53, 60, 87 ✅ |
| Quran references | 21:51-73 (idols and fire), 2:260 (birds), 37:83-113, 6:74-83, 11:69-76 ✅ |
| Segments | 8 (main story) + 2 (fire episode) ✅ |
| Sources | ibn_kathir, tabari, qurtubi, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Fire miracle is explicit in Quran (21:69); no extra-Quranic details should be added |

---

### 5. Story of Nuh عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_nuh` |
| Arabic title | قصة نوح عليه السلام ✅ |
| English title | Story of Prophet Nuh (Noah) ✅ |
| Main characters | Nuh, his wife, his son ✅ |
| Surahs | 7, 10, 11, 21, 23, 26, 37, 54, 71 ✅ |
| Quran references | 71:1-28 (Nuh's full call), 11:25-49 (the ark), 7:59-64, 10:71-73, 23:23-30 ✅ |
| Segments | 6 ✅ |
| Sources | ibn_kathir, tabari ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Story of Nuh's son (story_son_nuh) and wife (story_wife_nuh) are separate entries |

---

### 6. Story of Sulayman عليه السلام and Bilqis

| Field | Status |
|-------|--------|
| Story ID | `story_bilqis` + `story_sulayman` + `story_ant_hoopoe` |
| Arabic title | قصة سليمان وبلقيس ✅ |
| English title | Story of Sulayman and Bilqis ✅ |
| Main characters | Sulayman, Bilqis (Queen of Sheba), Hudhud, Jinn ✅ |
| Main surah | 27 (Surah Al-Naml) ✅ |
| Quran references | 27:15-44 (Bilqis), 27:17-19 (ants/hoopoe), 34:12-13 (Sulayman and Jinn) ✅ |
| Segments | 3 (Bilqis) + 2 (ant/hoopoe) + 6 (main Sulayman) ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Bilqis not named in Quran — title must be labeled appropriately |

---

### 7. Story of Maryam عليها السلام

| Field | Status |
|-------|--------|
| Story ID | `story_maryam` |
| Arabic title | قصة مريم عليها السلام ✅ |
| English title | Story of Maryam (Mary) ✅ |
| Main characters | Maryam, Zakariya, Angels ✅ |
| Surahs | 3, 19, 21, 66 ✅ |
| Quran references | 19:16-34 (Maryam in Surah Maryam), 3:35-47 (family of Imran) ✅ |
| Segments | 6 ✅ |
| Sources | ibn_kathir, tabari ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Birth and early life not fabricated — only what is in Quran |

---

### 8. Story of Luqman's Advice

| Field | Status |
|-------|--------|
| Story ID | `story_luqman` |
| Arabic title | قصة لقمان الحكيم ✅ |
| English title | Story of Luqman's Wisdom ✅ |
| Main characters | Luqman, his son ✅ |
| Main surah | 31 ✅ |
| Quran references | 31:12-19 ✅ |
| Segments | 5 ✅ |
| Sources | ibn_kathir, tabari, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Whether Luqman was a prophet is disputed — must reflect scholarly disagreement |

---

## Full Story Inventory (All 122 Stories)

Stories are listed with key data. All have Quran references in the manifest.
Coverage status reflects presence of kids/adult summaries and sunni review.

| Story ID | Arabic Title | Surahs | Segs | Kids | Adult | Sunni Review |
|----------|-------------|--------|------|------|-------|--------------|
| story_adam | قصة آدم عليه السلام | 2,7,15,17,18,20,38 | 8 | ❌ | ❌ | ❌ |
| story_nuh | قصة نوح عليه السلام | 7,10,11,21,23,26,37,54,71 | 6 | ❌ | ❌ | ❌ |
| story_ibrahim | قصة إبراهيم عليه السلام | 13 surahs | 8 | ❌ | ❌ | ❌ |
| story_musa | قصة موسى عليه السلام | 14 surahs | 9 | ❌ | ❌ | ❌ |
| story_yusuf | قصة يوسف عليه السلام | 12 | 9 | ❌ | ❌ | ❌ |
| story_isa | قصة عيسى عليه السلام | 6 surahs | 7 | ❌ | ❌ | ❌ |
| story_maryam | قصة مريم عليها السلام | 3,19,21,66 | 6 | ❌ | ❌ | ❌ |
| story_zakariyya_yahya | قصة زكريا ويحيى عليهما السلام | 3 surahs | 4 | ❌ | ❌ | ❌ |
| story_sulayman | قصة سليمان عليه السلام | 4 surahs | 6 | ❌ | ❌ | ❌ |
| story_dawud | قصة داود عليه السلام | 5 surahs | 5 | ❌ | ❌ | ❌ |
| story_ayyub | قصة أيوب عليه السلام | 2 surahs | 3 | ❌ | ❌ | ❌ |
| story_yunus | قصة يونس عليه السلام | 4 surahs | 5 | ❌ | ❌ | ❌ |
| story_lut | قصة لوط عليه السلام | 8 surahs | 4 | ❌ | ❌ | ❌ |
| story_shuayb | قصة شعيب عليه السلام | 4 surahs | 4 | ❌ | ❌ | ❌ |
| story_salih | قصة صالح عليه السلام | 6 surahs | 4 | ❌ | ❌ | ❌ |
| story_hud | قصة هود عليه السلام | 7 surahs | 4 | ❌ | ❌ | ❌ |
| story_kahf | قصة أصحاب الكهف | 18 | 5 | ❌ | ❌ | ❌ |
| story_dhulqarnayn | قصة ذي القرنين | 18 | 5 | ❌ | ❌ | ❌ |
| story_luqman | قصة لقمان الحكيم | 31 | 5 | ❌ | ❌ | ❌ |
| story_qarun | قصة قارون | 3 surahs | 5 | ❌ | ❌ | ❌ |
| story_habil_qabil | قصة هابيل وقابيل | 5 | 5 | ❌ | ❌ | ❌ |
| story_elephant | قصة أصحاب الفيل | 105 | 1 | ❌ | ❌ | ❌ |
| story_baqarah_cow | قصة البقرة | 2 | 4 | ❌ | ❌ | ❌ |
| story_talut_jalut | قصة طالوت وجالوت | 2 | 3 | ❌ | ❌ | ❌ |
| story_ismail | قصة إسماعيل عليه السلام | 7 surahs | 3 | ❌ | ❌ | ❌ |
| story_khidr | قصة موسى والخضر | 18 | 5 | ❌ | ❌ | ❌ |
| story_bilqis | قصة بلقيس ملكة سبأ | 27 | 3 | ❌ | ❌ | ❌ |
| story_two_gardens | قصة صاحبي الجنتين | 18 | 4 | ❌ | ❌ | ❌ |
| story_ditch | قصة أصحاب الأخدود | 85 | 1 | ❌ | ❌ | ❌ |
| story_ant_hoopoe | قصة النملة والهدهد | 27 | 2 | ❌ | ❌ | ❌ |
| story_sabbath_breakers | قصة أصحاب السبت | 2 surahs | 4 | ❌ | ❌ | ❌ |
| story_mother_musa | قصة أم موسى | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_asiya | قصة آسية زوجة فرعون | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_magicians | قصة سحرة فرعون | 3 surahs | 4 | ❌ | ❌ | ❌ |
| story_sea_crossing | قصة عبور البحر | 6 surahs | 2 | ❌ | ❌ | ❌ |
| story_ibrahim_fire | قصة إبراهيم والنار | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_yusuf_dream | قصة رؤيا يوسف | 12 | 2 | ❌ | ❌ | ❌ |
| story_yusuf_prison | قصة يوسف في السجن | 12 | 3 | ❌ | ❌ | ❌ |
| story_yusuf_brothers | قصة يوسف وإخوته | 12 | 3 | ❌ | ❌ | ❌ |
| story_isra_miraj | قصة الإسراء والمعراج | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_badr | غزوة بدر | 2 surahs | 3 | ❌ | ❌ | ❌ |
| story_uhud | غزوة أحد | 3 | 3 | ❌ | ❌ | ❌ |
| story_three_messengers | قصة أصحاب القرية (يس) | 36 | 3 | ❌ | ❌ | ❌ |
| *(remaining 80+ stories)* | … | … | … | ❌ | ❌ | ❌ |

---

## Stories from User Task — Coverage Check

| Requested Story | Manifest ID | Status |
|----------------|-------------|--------|
| Adam عليه السلام | `story_adam` | ⚠️ present, no levels |
| Habil and Qabil | `story_habil_qabil` | ⚠️ present, no levels |
| Nuh عليه السلام | `story_nuh` | ⚠️ present, no levels |
| Hud عليه السلام and Aad | `story_hud` + `story_ad` | ⚠️ present, no levels |
| Salih عليه السلام and Thamud | `story_salih` + `story_thamud` | ⚠️ present, no levels |
| Ibrahim عليه السلام | `story_ibrahim` | ⚠️ present, no levels |
| Ibrahim and the idols | `story_ibrahim` | ⚠️ present (aspect=idols) |
| Ibrahim and the fire | `story_ibrahim_fire` | ⚠️ present, no levels |
| Ibrahim and the guests | `story_ibrahim` (segment) | ⚠️ partial (in main) |
| Lut عليه السلام | `story_lut` | ⚠️ present, no levels |
| Ismail عليه السلام | `story_ismail` | ⚠️ present, no levels |
| Yusuf عليه السلام | `story_yusuf` | ⚠️ present, no levels |
| Yaqub عليه السلام | `story_yaqub` | ⚠️ present (2 segments) |
| Musa عليه السلام | `story_musa` | ⚠️ present, no levels |
| Musa and his mother | `story_mother_musa` | ⚠️ present, no levels |
| Musa and Pharaoh | `story_musa` (segment) | ⚠️ present |
| Musa and the sea | `story_sea_crossing` | ⚠️ present, no levels |
| Musa and Bani Israel | `story_bani_israel` | ⚠️ present, no levels |
| Musa and Al-Khidr | `story_khidr` | ⚠️ present, no levels |
| Harun عليه السلام | Part of `story_musa` | ⚠️ partial |
| Dawud عليه السلام | `story_dawud` | ⚠️ present, no levels |
| Sulayman عليه السلام | `story_sulayman` | ⚠️ present, no levels |
| Sulayman and the ants | `story_ant_hoopoe` | ⚠️ present, no levels |
| Sulayman and the hoopoe | `story_ant_hoopoe` | ⚠️ present |
| Sulayman and Bilqis | `story_bilqis` | ⚠️ present, no levels |
| Ayyub عليه السلام | `story_ayyub` | ⚠️ present, no levels |
| Yunus عليه السلام | `story_yunus` | ⚠️ present, no levels |
| Zakariya عليه السلام | `story_zakariyya_yahya` | ⚠️ present, no levels |
| Yahya عليه السلام | `story_zakariyya_yahya` | ⚠️ part of same |
| Maryam عليها السلام | `story_maryam` | ⚠️ present, no levels |
| Isa عليه السلام | `story_isa` | ⚠️ present, no levels |
| People of the Cave | `story_kahf` | ⚠️ present, no levels |
| Owner of the two gardens | `story_two_gardens` | ⚠️ present, no levels |
| People of the Garden (Qalam) | `story_garden_owners` | ⚠️ present, no levels |
| Dhu al-Qarnayn | `story_dhulqarnayn` | ⚠️ present, no levels |
| Qarun | `story_qarun` | ⚠️ present, no levels |
| Talut and Jalut | `story_talut_jalut` | ⚠️ present, no levels |
| Sabbath breakers | `story_sabbath_breakers` | ⚠️ present, no levels |
| People of the Elephant | `story_elephant` | ⚠️ present (1 segment) |
| Luqman and his advice | `story_luqman` | ⚠️ present, no levels |
| Believers in Surah Yasin | `story_three_messengers` | ⚠️ present, no levels |
| Cow in Surah Al-Baqarah | `story_baqarah_cow` | ⚠️ present, no levels |
| Table spread (Al-Ma'idah) | Not yet found in manifest | 🔍 needs_review |
| Companions of the trench | `story_ditch` | ⚠️ present (1 segment) |

---

## Source Coverage Assessment

All 122 stories use the following tafsir sources (all marked `needs_review`):

| Source ID | Source Name | Reliability |
|-----------|------------|-------------|
| `ibn_kathir` | Tafsir Ibn Kathir | canonical (base form maps to `ibn_kathir_ar`) |
| `tabari` | Tafsir Al-Tabari | canonical (base form maps to `tabari_ar`) |
| `qurtubi` | Tafsir Al-Qurtubi | canonical (base form maps to `qurtubi_ar`) |
| `saadi` | Tafsir Al-Saadi | verified (base form maps to `saadi_ar`) |

All evidence items currently carry `"needs_review": true` meaning:
1. The ayah references are correct (taken from Quran text)
2. The tafsir chunk IDs are placeholder keys — they have not been matched to actual tafsir chunks in the DB
3. No explanation text has been pulled from tafsir sources

This means all story segment summaries in `quranStories.ts` must be marked `needs_review` in sunniReview.

---

## Recommended First Batch Implementation Order

1. `story_yusuf` — Complete surah, clear references, all aspects covered
2. `story_musa` — Most referenced prophet, key segments clear
3. `story_kahf` — Clear surah 18 reference, popular story
4. `story_ibrahim` + `story_ibrahim_fire` — Key fire miracle verse (21:69) is explicit
5. `story_nuh` — Clear cross-surah references
6. `story_bilqis` + `story_ant_hoopoe` — Surah 27 coverage
7. `story_maryam` — Surah 19 and 3 clear
8. `story_luqman` — Surah 31 clear, short and accessible
