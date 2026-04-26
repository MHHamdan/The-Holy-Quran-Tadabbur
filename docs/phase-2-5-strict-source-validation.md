# Phase 2.5 – Strict sourceId Validation

**Status:** Complete  
**Date:** 2026-04-25  
**Files changed:** `backend/app/rag/source_validator.py` (new), `backend/app/rag/pipeline.py` (updated), `backend/tests/unit/test_source_validation.py` (new), this document

---

## Problem

Phase 2 added citation enrichment and response status tracking, but the pipeline had no guard
against fabricated source IDs.  An LLM-generated citation with `source_id="al_hallucinator"` or
a chunk from a corrupted retrieval with a missing `source_id` could slip through validation and
appear in an `"answered"` response.

---

## Trusted Source Registry

The authoritative list is `TAFSIR_CATALOG` in `backend/app/services/tafsir_sources.py`.  
It contains 15 sources:

| Base ID | Scholar / Institution |
|---|---|
| `ibn_kathir` | Ismail ibn Umar ibn Kathir |
| `tabari` | Muhammad ibn Jarir al-Tabari |
| `qurtubi` | Muhammad ibn Ahmad al-Qurtubi |
| `jalalayn` | Al-Mahalli and al-Suyuti |
| `fi_zilal` | Sayyid Qutb |
| `sha_rawi` | Muhammad Metwalli al-Sha'rawi |
| `muyassar` | King Fahd Complex |
| `ibn_ashur` | Muhammad al-Tahir ibn Ashur |
| `saadi` | Abd al-Rahman ibn Nasir al-Sa'di |
| `tantawi` | Muhammad Sayyid Tantawi |
| `bayyinah` | Nouman Ali Khan |
| `maariful_quran` | Mufti Muhammad Shafi |
| `tafsir_hamiduddin` | Amin Ahsan Islahi |
| `tafsir_french` | Muhammad Hamidullah |
| `tafsir_indonesian` | Indonesian Ministry of Religious Affairs |

The DB stores language variants with `_ar` / `_en` suffixes (e.g. `ibn_kathir_ar`).
`TRUSTED_SOURCE_IDS` contains all 45 accepted forms (15 base × 3).

---

## Validation Rules

All rules are enforced by `SourceValidator.validate_citations()` in
`backend/app/rag/source_validator.py`.

| # | Rule | Severity | Outcome |
|---|---|---|---|
| 0 | No citations at all | Hard block | `no_verified_source` |
| 1 | Citation has empty / None `source_id` | Hard block | `no_verified_source` |
| 2 | `source_id` not in `TRUSTED_SOURCE_IDS` | Hard block | `no_verified_source` |
| 3 | All citations are `experimental` **and** `intent=ruling` | Hard block | `no_verified_source` |
| 4 | No `canonical` or `verified` citation (supporting/experimental only) | Warning | `answered` + warning text |

A **hard block** means the pipeline discards all citations and returns:
- `status = "no_verified_source"`
- `citations = []`
- `answer = SAFE_REFUSAL_NO_SOURCES_{AR|EN}` (language-matched)
- `warnings = [hard_block_reason]`

---

## Integration Points

### `_validate_and_parse_response` (full pipeline path)

After the citation list is built from the LLM output, `source_validator.validate_citations()` is
called with `intent` and `language`.  If the result is a hard block, the method returns early
with a `no_verified_source` GroundedResponse — the confidence scoring step is skipped entirely.

If the result is valid, any non-fatal warnings from the validator are prepended to the
`warnings` list that the confidence scorer may also append to.

`language` was added as a parameter to `_validate_and_parse_response` and is threaded from the
`query()` call site.

### `_try_fast_path_verse_query` (fast-path)

After building `enriched_citations` from direct DB chunks, the same validator is called.  Fast-path
sources come from real DB rows and should always be trusted; this check is belt-and-suspenders.

---

## Return Shapes

### Hard block (any language)

```json
{
  "answer": "No verified source available for this answer.",
  "status": "no_verified_source",
  "answer_language": "en",
  "citations": [],
  "confidence": 0.0,
  "warnings": ["Unknown source_id 'al_hallucinator' — not in trusted registry."]
}
```

### Supporting-only warning (valid response)

```json
{
  "answer": "...",
  "status": "answered",
  "citations": [...],
  "warnings": [
    "All citations come from supporting or experimental sources. Consider verifying with canonical or verified scholarly sources."
  ]
}
```

---

## Tests

`backend/tests/unit/test_source_validation.py` — **45 tests, all passing**

| Class | Tests | Coverage |
|---|---|---|
| `TestSourceIdPresence` | 5 | empty/None/unknown/invented/partial source_id |
| `TestTrustedSourceIds` | 24 | all 15 catalog IDs + _ar/_en variants + exclusions |
| `TestExperimentalRulingBlock` | 5 | experimental+ruling block; mixed/canonical/verified allowed |
| `TestReliabilityWarnings` | 5 | supporting-only warning; verified/canonical no warning |
| `TestEmptyCitations` | 2 | empty list hard block |
| `TestIsTrustedSourceId` | 4 | helper method |
| `TestNoAnsweredWithEmptyCitations` | 3 | filtered_citations on success / empty on block |
| `TestModuleSingleton` | 2 | singleton import and behaviour |

---

## Open Risks

- The validator uses an in-memory static set.  If a new source is added to the DB without
  updating `TAFSIR_CATALOG`, its chunks will be blocked.  Mitigation: keep `TAFSIR_CATALOG`
  as the single source of truth and run `add_source` through it.
- The `reliability_level` field on citations is set by the pipeline from `source_reliability`
  float.  If a DB row has `source_reliability = None`, it defaults to `0.8` → `"verified"`.
  This is conservative (no false hard-blocks) but could suppress the supporting-only warning.
