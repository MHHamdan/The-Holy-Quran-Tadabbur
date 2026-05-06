# Closed Quranic AI Corpus Policy

**Platform:** Tadabbur Al-Quran  
**Version:** 1.1  
**Effective Date:** 2026-05-05  
**Updated:** 2026-05-05 (Phase C — added classifier reference)  
**Applies to:** All engineers, AI tools, and pipeline components

---

## 1. Why General AI Memory Is Unsafe for Quranic Tafsir

General-purpose large language models are trained on the entire internet. This means:

1. **No chain of evidence (isnad):** The model cannot tell you which scholar said what or through which chain of transmission.
2. **Hallucination of ayah references:** Models regularly produce surah:ayah combinations that do not exist in the Quran.
3. **Wrong attribution:** Quotes are assigned to the wrong scholar or the wrong book.
4. **Invented sources:** Model generates a book title, author, or hadith reference that does not exist.
5. **No theological vetting:** The model has no awareness of scholarly consensus (ijma'), methodological constraints, or sectarian sensitivities.
6. **Public users cannot detect errors:** Fluent, confident-sounding AI output passes unchallenged by non-specialists — who are the primary users of this platform.

**Conclusion:** General AI memory must never be used as a source of Quranic interpretation, tafsir, i'rab, morphology, vocabulary explanation, or fatwa. Every piece of religious content served by this platform must trace to a registered, verified source.

---

## 2. The Closed Corpus Principle

The platform operates as a **closed Quranic AI corpus**. This means:

- The AI (RAG pipeline, KG similarity, story system) can only search, summarize, classify, compare, and organize **content that is already in the trusted corpus**.
- The AI cannot add, invent, or supplement content from its own training knowledge.
- If a question requires knowledge not present in the corpus, the system must respond with a safe refusal — not an AI-generated answer.

### What Is In the Trusted Corpus

| Category | Sources | Status |
|---|---|---|
| Quran text (Arabic, Uthmani rasm) | `quran_uthmani_cloud`, `quran_hafs_local` | Active |
| English translation | `sahih_international` | Active |
| Tafsir (classical, Arabic) | `ibn_kathir_ar`, `tabari`, `qurtubi`, `jalalayn`, others | Active |
| Tafsir (classical, English) | `ibn_kathir_en` | Active |
| Tafsir (modern, Arabic) | `al_muyassar_ar` | Active |
| Tafsir (modern, English) | `tafheem_mawdudi_en` | Experimental |
| Quran stories | `stories_manifest` | Active (needs_review) |
| Concepts/themes | `concepts_dictionary`, `themes_taxonomy` | Active |
| Audio | `quran_audio_cdn` | Active |
| Vocabulary / غريب القرآن | — | **Planned — not yet active** |
| I'rab / الإعراب | — | **Planned — not yet active** |
| Morphology / التصريف | — | **Planned — not yet active** |
| Asbab al-nuzul / أسباب النزول | — | **Planned — not yet active** |
| Munasabah / المناسبة | — | **Planned — not yet active** |
| Qira'at / القراءات | — | **Planned — not yet active** |

**Rule:** No feature may serve content from a "Planned" category until a verified source is registered and activated. Queries requiring a missing category must return the safe refusal message.

---

## 3. How sourceId Validation Prevents Hallucination

The `SourceValidator` in `backend/app/rag/source_validator.py` enforces:

1. Every citation must have a non-empty `source_id`.
2. `source_id` must exist in `TRUSTED_SOURCE_IDS` (built from `TAFSIR_CATALOG` keys).
3. A missing or unrecognized `source_id` triggers a **hard block**: the pipeline returns `status=no_verified_source` with the bilingual safe refusal.
4. Experimental-only citations combined with ruling-intent queries → hard block.
5. Supporting-only citations (no verified/canonical source) → warning appended to response.

The `QuranAnswerGuard` in `backend/app/safety/quran_answer_guard.py` adds an additional layer:

1. Every ayah reference in a response must resolve to a real surah:ayah in the 6236-ayah corpus.
2. No invented surah numbers (only 1–114 are valid).
3. No invented ayah numbers (validated against the canonical per-surah ayah count table).
4. Scientific miracle claim responses must carry a mandatory caution label.
5. Fatwa-like responses must be blocked and redirected.
6. Translation text must always carry a translation label.

---

## 4. How Quran Text Is Protected

- The canonical Arabic text lives in `data/raw/quran_uthmani.json` — never modified.
- No code path may write Arabic Quran text as a string literal.
- The integrity validator (`scripts/validate-quran-integrity.ts`) must pass before any content deployment.
- Translations are stored separately and always labeled with `translator` field.
- AI-generated translations must not be served (`model_name` column must be NULL for served content).

---

## 5. How Tafsir Sources Are Verified

A source may only be added to `TAFSIR_CATALOG` and the source registry when:

1. The scholar's credentials and school are documented.
2. The text's license or public-domain status is confirmed.
3. The `reliabilityLevel` is set conservatively (`supporting` or `experimental` until verified by a human reviewer).
4. The entry passes the `validateRegistry()` function in `sourceRegistry.ts`.

**No source may be set to `canonical` or `verified` without explicit human sign-off**, documented in the source's `notes` field and `lastVerifiedAt` date.

---

## 6. How Public Answers Are Restricted

The following rules govern what reaches public users:

| Situation | Platform Action |
|---|---|
| No verified source exists for query | Return bilingual safe refusal |
| Source exists but is `experimental` + ruling intent | Hard block → safe refusal |
| All sources are `supporting` only | Return with warning label |
| Ayah reference in answer does not exist | Block answer entirely |
| Source ID not in trusted registry | Block answer entirely |
| Fatwa-like query detected | Redirect with refusal + recommend scholar consultation |
| Scientific miracle claim detected | Return answer with mandatory caution label |
| Content is `needs_review` | Display with `humanReviewRequired: true` badge |
| Content is `rejected` | Do not display |

---

## 7. How Uncertain Outputs Become needs_review

Any content generated or processed by AI that has not been reviewed by a qualified scholar is assigned `status: needs_review`. This includes:

- All story segments from `stories_manifest`
- All KG relations from `quranKnowledgeGraph.json`
- All tafsir comparison outputs
- All thematic groupings not in the canonical theme taxonomy
- All vocabulary/morphology/i'rab results (when those modules are built)
- Any AI-generated summary of tafsir that has not been reviewed

`needs_review` content may be displayed to users only with a visible `humanReviewRequired: true` badge. It must never be presented as authoritative or reviewed.

---

## 8. How Scholarly Review Is Required Before Approval

The review workflow (Phase 6) enforces:

- Approval requires a non-empty `reviewerId` (documented reviewer identity).
- Approval requires `notes` of at least 10 characters explaining the review decision.
- Decisions never modify the content itself — only the `reviewStatus` metadata.
- `humanReviewRequired: true` is preserved in all API responses.
- Rejected tasks never display as approved.
- All decisions are written to an append-only `review_decisions.json` audit log.

**No content may transition from `needs_review` to `approved` without this workflow.**

---

## 9. Source Category Gap — Required Before Feature Build

Before implementing vocabulary, i'rab, morphology, asbab, munasabah, or qira'at features, the following steps are required:

1. Identify a verified, openly licensed data source for the category.
2. Add a placeholder entry to `SOURCE_REGISTRY` with `reliabilityLevel: 'experimental'` and `notes` containing "PLANNED — DO NOT DISPLAY".
3. Add the source to `TAFSIR_CATALOG` only after license verification.
4. Build the ingest pipeline.
5. Run integrity validation.
6. Create review tasks for any ingested content.
7. Do not activate public display until at least one item has been reviewed and approved.

---

## 10. Safe Refusal Messages

When no verified source is available, the platform must return:

**English:**
> "No verified scholarly source is available for this answer. Please consult a qualified Islamic scholar."

**Arabic:**
> "لا يتوفر مصدر علمي موثوق للإجابة على هذا السؤال. يُرجى الرجوع إلى عالم إسلامي مؤهل."

These messages must not be removed, softened, or replaced with AI-generated content.

---

## 11. Pre-Generation Classifier (Phase C)

The `QuranQuestionClassifier` in `backend/app/safety/quran_question_classifier.py` acts as defense layer 1, running **before** any LLM call:

- Fatwa-like queries → hard block → safe refusal (no LLM call)
- Scientific miracle claims → allowed with mandatory caution labels
- Vague queries → clarification request (no LLM call)
- Non-Quranic topics → safe refusal (no LLM call)
- Vocabulary / i'rab / morphology / qiraat → allowed with module-unavailable warning

The post-generation `QuranAnswerGuard` (defense layer 2) remains mandatory. Neither layer may be removed.

See: `docs/phase-c-quran-question-classifier.md`

---

*This policy complements `docs/quran-content-policy.md`. In case of conflict, the more restrictive rule applies.*
