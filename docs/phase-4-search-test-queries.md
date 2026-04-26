# Phase 4 — Search Test Queries

Use these queries to manually verify search quality across normalization types,
match types, and ranking. Run against the running backend (`/api/search`).

---

## 1. Standard Normalization — Alef/Ya/Diacritics

These should always work and return results with `match_type: "exact"` or `"normalized"`.

| Query | Expected Match | Notes |
|-------|----------------|-------|
| `الله` | 2600+ verses | Most frequent word |
| `آمن` | Verses with إيمان / آمن | Alef with madda → plain alef |
| `إيمان` | Verses about faith | Alef with hamza below |
| `موسى` | Verses about Moses | Alef maqsura ى |
| `الرَّحْمَٰنِ` | Al-Fatiha 1:3, many others | Diacritics stripped |
| `الرحمن` | Same verses as above | Without diacritics |
| `قال` | Narrative verses | Common verb |

---

## 2. Ta Marbuta Normalization (Python-level only)

These test the `normalize_for_matching()` path. Results depend on Python-level re-check
after DB retrieval.

| Query | Stored Form | Expected | Notes |
|-------|-------------|----------|-------|
| `رحمه` | `رحمة` | Should match | User typed ه, Quran has ة |
| `رحمة` | `رحمة` | Should match exactly | Standard form |
| `نعمه` | `نعمة` | Should match | Blessing/bounty |
| `جنه` | `جنة` | Should match | Paradise |

> **Note:** DB ILIKE uses standard normalization (no ta marbuta). These queries rely on
> Python-level `normalize_for_matching()` re-scoring after retrieval. If the DB doesn't
> return the verse at all, Python-level matching won't help. Full fix requires DB migration.

---

## 3. Hamza Carrier Normalization (Python-level only)

| Query | Stored Form | Expected | Notes |
|-------|-------------|----------|-------|
| `مومن` | `مؤمن` | Should match via normalization | ؤ → و |
| `مؤمن` | `مؤمن` | Exact match | Standard form |
| `يومن` | `يؤمن` | Should match | ؤ → و in verb |

---

## 4. Semantic/Root Expansion

These should return results with `match_type: "root"` when `include_semantic=true`.

| Query | Should Also Match | Notes |
|-------|-------------------|-------|
| `صبر` | صابر, صابرين, اصبر | Root expansion |
| `رحم` | رحمة, رحيم, رحمن | Root: mercy |
| `هدى` | هداية, اهدنا, مهتدي | Root: guidance |
| `توب` | توبة, تائب, تابوا | Root: repentance |
| `علم` | عليم, علماء, يعلم | Root: knowledge |

---

## 5. Exact Match Ranking

Exact matches must rank above normalized/root matches for the same query.

| Query | Top result should be | Reasoning |
|-------|---------------------|-----------|
| `الله` | Verse with most occurrences of الله | TF-IDF + exact match bonus |
| `بسم الله الرحمن الرحيم` | 1:1 Al-Fatiha | Phrase match |
| `آية الكرسي` | 2:255 | Known by name |
| `لا إله إلا الله` | Tawheed verses | Core phrase |

---

## 6. Sura Filter

| Query | Filter | Expected |
|-------|--------|----------|
| `الرحمن` | sura_no=55 | Only Ar-Rahman chapter results |
| `الله` | sura_no=112 | Al-Ikhlas (4 verses) |
| `نور` | sura_no=24 | An-Nur chapter results |

---

## 7. Edge Cases

| Query | Expected Behavior | Notes |
|-------|-------------------|-------|
| Empty string | No results / validation error | Graceful handling |
| `hello` | 0 results (no Arabic match) | English input |
| Single letter `ب` | 0 or few results (too short) | Stop word / short filter |
| `و` | 0 results | Filtered as stop word |
| Very long query (100+ chars) | Graceful truncation or error | Stress test |
| `ابن تيمية` | May return 0 (not in Quran text) | Scholar name, not in Quran |

---

## 8. UI Verification

After each search in the browser, verify:

| Check | Expected |
|-------|---------|
| Search input `dir` attribute | `rtl` in Arabic mode, `ltr` in English mode |
| Result cards show "Quran Text" badge (teal) | Every result |
| Exact match results show green "Exact Match" badge | When `match_type="exact"` |
| Root/related results show purple "Related" badge | When `match_type="root"` |
| Relevance percentage shown on each card | Always visible |
| Arabic verse text has `dir="rtl"` | Yes |
| Verse references (2:255) stay LTR in Arabic mode | Yes (uses `verse-ref` CSS class) |
