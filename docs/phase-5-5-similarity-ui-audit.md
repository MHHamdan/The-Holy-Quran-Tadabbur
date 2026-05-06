# Phase 5.5 – Similarity UI Audit

**Date:** 2026-04-27  
**Auditor:** Claude Code  
**Status:** Completed – Fixes Applied

---

## 1. Current UI Behavior (Before Phase 5.5)

### SimilarityPage (`/similarity`)
- Full dedicated page for exploring verse similarities.
- Input: text field accepting `sura:aya`, Arabic digits, surah names (AR/EN), or verse text.
- Text search resolves via `/quran/resolve` endpoint with candidate selection modal.
- Results fetched from `/similarity/advanced/{sura_no}/{aya_no}`.
- Results shown as MatchCards with: reference, connection type badge, connection strength, verse text (Uthmani), shared themes, shared words, shared roots, sentence structure, score breakdown, explanation.
- Popular verse shortcuts shown.
- Filters: theme, connection type, min score, exclude same sura, grouping.
- RTL/LTR: mostly correct; a few issues (see below).

### SimilarVersesPanel (`/quran/:suraNo`)
- Embeddable panel component for the Quran page.
- Same service, same types, manual "Find Similar Verses" trigger.

---

## 2. Current API Behavior

### `/similarity/advanced/{sura_no}/{aya_no}` (existing)
Returns `AdvancedSimilaritySearchResponse` with:
- `source_verse`, `source_themes`, `source_structure`
- `matches[]`: `AdvancedSimilarityMatch` (lexical/thematic/semantic scoring via TF-IDF + vectors)
- `theme_distribution`, `connection_type_distribution`, `connection_types`
- `search_time_ms`

**Missing Phase 5 KG fields:**
- No `humanReviewRequired`
- No `evidence[]` with `relationStatus`
- No `warnings[]`
- No `pathExplanation`
- No `allNeedsReview` flag

### `/similarity/kg/{sura_no}/{aya_no}` (Phase 5 – **new in Phase 5.5**)
Added in Phase 5.5. Returns `KGSimilaritySearchResponse` with:
- `sourceAyah`, `relatedAyahs[]`, `totalRelated`, `allNeedsReview`, `searchTimeMs`
- Each `relatedAyah`: `surahNumber`, `ayahNumber`, `score`, `relationTypes[]`, `explanationArabic`, `explanationEnglish`, `evidence[]`, `warnings[]`, `humanReviewRequired`
- Each `evidence`: `sourceId`, `sourceTitleArabic`, `sourceTitleEnglish`, `storyId`, `segmentId`, `conceptId`, `themeId`, `tafsirReference`, `relationStatus`

---

## 3. Missing Fields (Before Phase 5.5)

| Field | Status |
|---|---|
| `humanReviewRequired` | Missing from existing endpoint and UI |
| `evidence[].relationStatus` | Missing from existing endpoint and UI |
| `warnings[]` | Missing from existing endpoint and UI |
| `pathExplanation` | Missing from types and UI |
| Experimental toggle | Missing from UI |
| "Needs review" badge | Missing from UI |
| "Approved" badge | Missing from UI |
| KG-specific empty state | Missing |

---

## 4. Missing Warnings (Before Phase 5.5)

- No banner stating all current KG edges are `needs_review`
- No per-result warning for `humanReviewRequired`
- No per-evidence `needs_review` or `experimental` indicator
- No safeguard against showing "approved" when relation is not approved
- Experimental relations not hidden by default

---

## 5. Missing Translations (Before Phase 5.5)

Added in Phase 5.5:
- `similarity_kg_title`, `similarity_kg_subtitle`
- `similarity_needs_review`, `similarity_approved`, `similarity_experimental`
- `similarity_human_review_required`
- `similarity_show_experimental`, `similarity_experimental_warning`
- `similarity_no_verified_ayahs`
- `similarity_open_in_mushaf`
- `similarity_evidence`, `similarity_path_explanation`, `similarity_relation_type`
- `similarity_kg_pending_notice_title`, `similarity_kg_pending_notice_body`
- `similarity_kg_human_review_detail`, `similarity_kg_needs_review_detail`
- `similarity_kg_experimental_detail`
- `similarity_kg_searching`, `similarity_kg_load_error`, `similarity_kg_relation_count`
- `similarity_under_review`, `similarity_relation_label`
- `similarity_rt_*` for all KG relation types
- `similarity_evidence_story`, `similarity_evidence_concept`, `similarity_evidence_theme`, `similarity_evidence_tafsir_ref`
- `similarity_enter_reference`, `similarity_invalid_ayah`

---

## 6. RTL/LTR Issues (Before Phase 5.5)

| Issue | Location | Fix |
|---|---|---|
| `FuzzyMatchWarning` always shows Arabic text and uses `dir="rtl"` regardless of language | `SimilarityPage.tsx:767` | Fixed in Phase 5.5 |
| KG explanation text needs explicit `dir` per language | New KG components | Applied in Phase 5.5 |
| Evidence cards show untranslated labels in Arabic UI | New (Phase 5.5) | Added bilingual labels |

---

## 7. Review-Status Risks (Before Phase 5.5)

1. **No indication that all current KG edges are `needs_review`** — user could interpret results as authoritative.
2. **Experimental (semantic-only) relations not hidden** — semantic similarity could be presented as meaning.
3. **No distinction between source-backed and semantic-only** — both look identical to the user.
4. **"Approved" badge absent** — system has no way to show when a relation is verified (future-proofing).

---

## 8. Recommended Fixes (Applied in Phase 5.5)

### Backend
- [x] Add `/similarity/kg/{sura_no}/{aya_no}` endpoint using `VerseSimilarityService`
- [x] Return `humanReviewRequired`, `evidence[]` with `relationStatus`, `warnings[]`, `allNeedsReview`
- [x] Validate surah range (1–114) via `Path(..., ge=1, le=114)`

### Frontend Types
- [x] Add `KGRelationStatus`, `KGEvidenceItem`, `KGRelatedAyah`, `KGSimilarityApiResponse` to `api.ts`
- [x] Add `quranApi.getKGSimilarity()` method
- [x] Add `PathExplanation` and `pathExplanation?` field to `RelatedAyah` in `quranKnowledgeGraph.ts`

### UI
- [x] Create `KGSimilaritySection` component with all Phase 5.5 safety rules
- [x] `ReviewStatusBadge` showing Approved / Needs Review / Experimental
- [x] `HumanReviewWarning` banner per card
- [x] Global `allNeedsReview` notice at section level
- [x] Experimental toggle (default OFF) with warning when enabled
- [x] Bilingual evidence cards (`EvidenceCard`)
- [x] Bilingual relation type badges (`RelationTypeBadge`)
- [x] Safe empty state: "No verified related ayahs are available for this ayah yet."
- [x] Never shows "Approved" unless backend returns `approved` status
- [x] KG section mounted in `SimilarityPage` when a verse is selected

### Translations
- [x] All Phase 5.5 keys added to `translations.ts` (AR + EN)

### RTL/LTR
- [x] `FuzzyMatchWarning` fixed to be bilingual with correct `dir`
- [x] All new KG components use `dir={isArabic ? 'rtl' : 'ltr'}` on text containers

---

## 9. Remaining Risks

1. **KG endpoint needs backend running** — the `VerseSimilarityService` loads stories/concepts from disk. If data files are missing, the endpoint returns 0 results (graceful fallback, no crash).
2. **Semantic embedding (Qdrant)** — the service tries Qdrant for experimental relations; if Qdrant is unavailable, it falls back silently. This is safe.
3. **`pathExplanation` field** — type added but the current `VerseSimilarityService` does not yet populate it. Cards will omit the path section until the service is extended.
4. **All KG edges are `needs_review`** — no `approved` relations exist yet. The `ReviewStatusBadge` for `approved` is implemented but will only appear when editors approve edges in a future phase.
5. **Frontend test framework** — Vitest/React Testing Library not yet configured. A test plan document is provided in `phase-5-5-similarity-ui-test-plan.md`.
