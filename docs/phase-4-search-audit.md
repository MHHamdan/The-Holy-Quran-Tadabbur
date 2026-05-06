# Phase 4 — Search Quality Audit

**Audit Date:** 2026-04-25  
**Scope:** `backend/app/services/quran_search.py`, `frontend/src/pages/SearchPage.tsx`, `frontend/src/lib/api.ts`

---

## Issues Found and Fixed

### 1. Arabic Normalization: Missing Ta Marbuta support

**Issue:** `normalize_arabic()` did not normalize Ta Marbuta (ة → ه). A user searching
`رحمه` (with ه) would not match verses containing `رحمة` (with ة), and vice versa.

**Fix:** Added `normalize_ta_marbuta: bool = False` parameter (off by default — backward compatible).
Added `TA_MARBUTA` dict: `{ 'ة': 'ه' }`.  
Added `normalize_for_matching()` convenience function that applies all normalizations including
Ta Marbuta and Hamza variants.

**Constraint:** The `text_normalized` PostgreSQL column was built without Ta Marbuta normalization.
Applying it to stored text would require a DB migration. Therefore:
- `normalize_for_matching()` is for Python-level query matching only
- DB ILIKE conditions use standard `normalize_arabic()` (no Ta Marbuta)

### 2. Arabic Normalization: Missing Hamza Carrier variants

**Issue:** Hamza-on-Waw (ؤ) and Hamza-on-Ya (ئ) were not normalized. Searching `مومن`
would not match `مؤمن`.

**Fix:** Added `normalize_hamza_variants: bool = False` parameter.
Added `HAMZA_VARIANTS` dict: `{ 'ؤ': 'و', 'ئ': 'ي' }`.
Both flags activate via `normalize_for_matching()`.

### 3. `SearchMatch` dataclass: No match type classification

**Issue:** `SearchMatch` only had `exact_match: bool`. There was no way to distinguish
between an exact normalized match, a match via semantic expansion, and a match via root
expansion — all appeared identical in the UI.

**Fix:** Added `match_type: str = "normalized"` field to `SearchMatch` dataclass.
Values: `"exact"` | `"normalized"` | `"root"` | `"semantic"`.

**Computation logic in `search()` method:**
```python
if exact_match:
    match_type = "exact"
elif include_semantic and len(search_terms) > 1 and query_normalized not in verse_norm:
    match_type = "root"  # Verse only returned via semantic expansion
else:
    match_type = "normalized"
```

**In `search_phrase()` method:** All results set `match_type="exact"` (phrase search by definition).

### 4. Frontend `SearchMatch` interface missing `match_type`

**Issue:** `api.ts` interface for `SearchMatch` did not include `match_type` or `result_type`.

**Fix:** Added:
```typescript
match_type: string;   // "exact" | "normalized" | "root" | "semantic" | "metadata"
result_type?: string; // "quran_text" for direct text search results
```

### 5. Search result card: Binary exact/semantic badge

**Issue:** The `SearchMatchCard` only showed two states: green "Exact" or yellow "Semantic",
regardless of actual match type. This was misleading — "Semantic" was shown for all
non-exact matches, including normalized matches.

**Fix:** Added `MatchTypeBadge` component that renders based on `match_type`:
- `"exact"` → green "Exact Match" / "تطابق تام" (with check icon)
- `"normalized"` → blue "Quran Text" / "نص قرآني"
- `"root"` → purple "Related" / "مرتبط"
- `"semantic"` → yellow "Semantic" / "دلالي"

Also added a persistent teal "Quran Text" badge to every result card, sourced from
`t('search_result_type_quran', language)`. This distinguishes text-search results
from future tafsir/concept result types.

### 6. Search input: Hardcoded `dir="rtl"`

**Issue:** The main search text input had `dir="rtl"` hardcoded, making it RTL even in
English mode. An English query typed in the box would appear reversed.

**Fix:** Changed to `dir={language === 'ar' ? 'rtl' : 'ltr'}`.

---

## New Translation Keys Added

| Key | Arabic | English |
|-----|--------|---------|
| `search_result_type_quran` | نص قرآني | Quran Text |
| `search_match_exact` | تطابق تام | Exact Match |
| `search_match_normalized` | نص قرآني | Quran Text |
| `search_match_root` | مرتبط | Related |
| `search_match_semantic` | دلالي | Semantic |

---

## New Backend Tests Added (`tests/unit/test_quran_search.py`)

| Class | Test Count | Coverage |
|-------|-----------|----------|
| `TestTaMarbuta` | 5 | `normalize_ta_marbuta` flag, TA_MARBUTA dict, preservation by default |
| `TestHamzaVariants` | 5 | `normalize_hamza_variants` flag, HAMZA_VARIANTS dict, both carriers |
| `TestNormalizeForMatching` | 8 | Full normalization pipeline, matching equivalence proofs |
| `TestMatchType` | 4 | Default value, "exact" type, "root" type, exact outranks normalized in relevance |

**Total new tests:** 22  
**All 63 tests pass** (41 pre-existing + 22 new).

---

## Normalization Design Principles

| Normalization | `normalize_arabic()` | `normalize_for_matching()` | DB `text_normalized` |
|--------------|---------------------|---------------------------|----------------------|
| Remove diacritics | ✓ (default) | ✓ | ✓ |
| Alef variants (آأإٱ→ا) | ✓ | ✓ | ✓ |
| Ya/Alef Maqsura (ى→ي) | ✓ | ✓ | ✓ |
| Ta Marbuta (ة→ه) | Optional flag | ✓ | ✗ (would need migration) |
| Hamza carriers (ؤ→و, ئ→ي) | Optional flag | ✓ | ✗ (would need migration) |

**Key rule:** `normalize_for_matching()` MUST NOT be applied to stored Quran text or
display output. It is for query-side matching only.

---

## Remaining Risks / Items for Human Review

| Risk | Severity | Notes |
|------|----------|-------|
| Ta Marbuta DB column gap | Medium | `text_normalized` doesn't have ة→ه. Users querying رحمه won't find رحمة via DB ILIKE. Fix requires adding `text_normalized_full` column and migration. |
| Hamza DB column gap | Medium | Same as above for ؤ/ئ variants. |
| `match_type` for intelligent/semantic search | Low | Intelligent search result converter sets `match_type='semantic'` — this is correct but coarse. A future improvement would derive the type from the grounding explanation. |
| English search not tested | Medium | All normalization is Arabic-only. English queries go through as-is. |

---

## Phase 4 Update — Alias Layer (2026-04-26)

### Problem
Queries for well-known verse/surah *names* (metadata labels) returned 0 results because
those names do not appear as literal text inside any Quran verse.
Examples: "آية الكرسي", "Ayat al-Kursi", "الفاتحة", "People of the Cave".

### Solution: Curated Alias Layer

**New file:** `backend/app/services/quran_aliases.py`

A hand-curated `ALIAS_MAP` maps well-known names to their canonical `AliasTarget`
(sura_no, aya_start, aya_end). Matching is case-insensitive and diacritic-insensitive.

#### Rules for the alias map

1. Every entry is explicitly verified against the mushaf.
2. No model-generated aliases — human curation only.
3. No speculative aliases (e.g., "do not add 'Night of Power' if unsure of exact range").
4. Alias targets store only `(sura_no, aya_start, aya_end)` — never Quran text strings.
5. Aliases rank above concept-expansion results but below a future direct `surah:ayah`
   reference endpoint.

#### Alias entries (2026-04-26)

| Alias (representative) | Target | Range |
|---|---|---|
| آية الكرسي / Ayat al-Kursi | Surah 2 | 2:255 (single verse) |
| الفاتحة / Al-Fatihah | Surah 1 | 1:1–1:7 (full surah) |
| سورة الكهف / Al-Kahf | Surah 18 | anchor 18:1 |
| أصحاب الكهف / People of the Cave | Surah 18 | 18:9–18:26 |
| ذو القرنين / Dhul-Qarnayn | Surah 18 | 18:83–18:98 |
| المعوذتان / Al-Mu'awwidhatayn | Surah 113 | 113:1 anchor |
| الإخلاص / Al-Ikhlas | Surah 112 | 112:1–112:4 |
| يس / Surah Yasin | Surah 36 | anchor 36:1 |
| الملك / Al-Mulk | Surah 67 | anchor 67:1 |
| الرحمن / Ar-Rahman | Surah 55 | anchor 55:1 |

#### Intentionally excluded

- Any name whose canonical reference is disputed among scholars.
- Names that are also common Arabic words searched for in Quran text (e.g. "العلق" could
  be searched as text or as "Surah Al-Alaq" — currently excluded to avoid ambiguity).
- Translated/paraphrased names that don't have a unique canonical reference.

#### How to add a new alias safely

1. Confirm the canonical surah:ayah in an authoritative mushaf.
2. Add all common spelling variants to `_RAW` in `quran_aliases.py`.
3. Add test cases to `tests/unit/test_quran_aliases.py`.
4. The import-time collision check will fail if two spellings resolve to different targets.

### Integration

`intelligent_search` in `quran.py` now:
1. Calls `resolve_alias(query)` before concept expansion.
2. If an alias is found, fetches the target verse(s) from the DB (exact surah:ayah query).
3. Prepends alias results (with `match_type="alias"`, `relevance_score=1.0`) to the output.
4. Fills remaining slots with full-text results, deduplicating by verse_id.
5. Summary prefixes the alias label when an alias hit occurred.

### New field on GroundedVerseResponse

`match_type: str = "normalized"` — values: `"alias"` | `"normalized"` | `"concept_expansion"`.

### Tests

`tests/unit/test_quran_aliases.py` — 36 assertions across:
- Specific alias resolutions (Ayat al-Kursi, Fatihah, Cave, Dhul-Qarnayn)
- Case/diacritic insensitivity
- Non-alias queries return None
- No Quran-text mutation
- `match_type` field correctness
- `ALIAS_MAP` integrity (sura range, label non-empty, no collisions)

### Remaining Risks / Items for Human Review

| Risk | Severity | Notes |
|------|----------|-------|
| Alias map completeness | Low | Only the most frequently searched verse names are covered in the first batch. Additional aliases should be added by a qualified reviewer. |
| Surah-level aliases return first verse as anchor | Low | When `aya_end` is None and `aya_start=1`, the full surah is fetched up to `limit`. Consumers should check `aya_end` to know whether more verses exist. |
| Alias collision at import | Low (guarded) | The `_RAW` loop raises `ValueError` at import if two spellings of the same form resolve to different targets — caught at startup, not at runtime. |
