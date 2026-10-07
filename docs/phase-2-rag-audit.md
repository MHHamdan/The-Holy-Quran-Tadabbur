> **HISTORICAL.** Audit snapshot from before the Hugging Face migration; LLM
> synthesis is now performed only via Hugging Face Inference Providers.

# Phase 2 RAG Audit — Tadabbur Al-Quran

**Audit date:** 2026-04-24  
**Scope:** Ask/RAG flow — data flow, schema gaps, citation weaknesses, content risks

---

## 1. Current Data Flow

```
User → AskPage.tsx
      ↓ ragApi.ask() / ragApi.askFollowup()
      POST /api/v1/rag/ask  (rag.py)
      ↓ RAGPipeline.query()  (pipeline.py)
        1. Language validation (ar/en only)
        2. Fast-path: direct verse lookup if famous verse detected
        3. Intent classification (rule-based + LLM fallback)
        4. Query expansion (ISLAMIC_TERM_MAPPINGS)
        5. HybridRetriever.retrieve() → tafseer_chunks (vector + keyword)
        6. Reranker: relevance + source reliability + query term overlap
        7. No-chunks guard → SAFE_REFUSAL_NO_SOURCES (English only)
        8. LLM synthesis (at the time Ollama or Claude; now Hugging Face) with GROUNDED_SYSTEM_PROMPT
        9. Citation extraction (regex on [Source, Ref] patterns)
       10. ConfidenceScorer → float score + level string
       11. GroundedResponse.to_dict()
      ↓ AskPage.tsx receives RAGResponse
      ↓ ChatMessage.tsx renders:
          - related_verses (VersesSection)
          - tafsir_by_source (TafsirAccordion)
          - answer text (AnswerCard)
          - CitationsSummary (source name badges only)
          - MissingSourceWarning (if no citations)
          - FollowUpChips
```

---

## 2. Current Weaknesses

### 2.1 No `status` Field in Response Schema
The `GroundedResponse` type has `confidence: float` and `confidence_level: str` but no explicit
`status` field. The frontend has no way to distinguish:
- A valid answered response
- A "no verified source" safe refusal
- A "needs clarification" (vague question)
- An error

The no-chunks guard returns a plain string answer with no structural signal. The frontend
checks `citations.length === 0` as a proxy — fragile and unreliable.

### 2.2 Missing `answerLanguage` Field
No `answer_language` field is returned. The frontend cannot validate whether the answer language
matches the requested language. Arabic answers with empty citations would display with no language
indication to the user, violating the bilingual refusal requirement.

### 2.3 Citations Lack Reliability Metadata
The `Citation` type exposes only `source_id`, `source_name`, `source_name_ar`, `verse_reference`,
`excerpt`, and `relevance_score`. Missing:
- `reliability_level` (canonical / verified / supporting / experimental)
- `author` (the human scholar name, not just the book)
- `quoted_evidence` (the actual tafsir text used)
- `explanation` (why this citation supports the answer)

Without reliability level the frontend `SourceBadge` component cannot be applied to citations,
defeating the Phase 1 source-integrity goal at the RAG layer.

### 2.4 No Enforcement of `no_verified_source` State
When there are no citations the pipeline returns `SAFE_REFUSAL_NO_SOURCES` — an English-only
string. If the user requested Arabic (`language="ar"`), the refusal text is still in English.
There is no structural rule forcing `status="no_verified_source"` when `citations` is empty.

### 2.5 No `needs_clarification` Handling
Vague questions ("اشرح الآية", "What does this mean?") are processed through the full LLM
pipeline. There is no early detection to return `status="needs_clarification"` before spending
LLM tokens on an unanswerable question.

### 2.6 Source Registry Not Consulted at RAG Layer
The backend `pipeline.py` and `rag.py` do not validate `source_id` against the frontend
`sourceRegistry.ts` or its backend equivalent (`TafseerSource` table). A chunk with an unknown
or disabled `source_id` can be cited without warning.

### 2.7 Experimental Sources May Be Sole Citation for Rulings
No check prevents an experimental-reliability source from being the sole citation for a fiqh
ruling question. The `confidence_scorer` uses `source_reliability` float but does not enforce the
rule "experimental sources alone cannot support a religious ruling."

### 2.8 Frontend CitationsSummary Shows Minimal Data
`CitationsSummary` in `ChatMessage.tsx` renders source-name badges with citation counts.
It does not show:
- Author name
- Reliability level badge (existing `SourceBadge` component unused here)
- Surah and ayah
- Quoted evidence excerpt
- Confidence level per-citation

### 2.9 Low-Confidence Answer Not Visually Distinguished from High-Confidence
The `ConfidenceBadge` in `AnswerCard` shows a percent + label, but when confidence is "low"
or "insufficient" the answer text is displayed identically to a high-confidence answer. Users
may not notice the yellow/red badge.

---

## 3. Missing Citation Fields (Gap Table)

| Field | Current `Citation` | Required |
|---|---|---|
| `source_id` | ✅ | ✅ |
| `source_name` | ✅ | ✅ |
| `source_name_ar` | ✅ | ✅ |
| `verse_reference` | ✅ | ✅ |
| `excerpt` | ✅ | ✅ |
| `relevance_score` | ✅ | ✅ |
| `reliability_level` | ❌ | ✅ canonical/verified/supporting/experimental |
| `author` | ❌ | ✅ human scholar name |
| `surah_number` | ❌ (derivable from `verse_reference`) | ✅ explicit |
| `ayah_number` | ❌ (derivable from `verse_reference`) | ✅ explicit |
| `quoted_evidence` | ❌ | ✅ verbatim tafsir excerpt |
| `explanation` | ❌ | ✅ why this source supports the answer |

---

## 4. Source Registry Usage

### Backend
- `TafseerSource` DB table: used by `/rag/sources` endpoint. Contains `reliability_score`
  (float 0–1) and `is_enabled` flag.
- Pipeline (`pipeline.py`): `source_reliability` is read from `RetrievedChunk.source_reliability`
  (comes from DB retrieval) and used in `ConfidenceScorer`. The source registry is NOT consulted
  to validate `source_id` before building a citation.

### Frontend
- `sourceRegistry.ts`: Used by `SourceBadge` and `SourceAttribution` components in the
  Quran reader and Sources page. **Not used at all by `ChatMessage.tsx` or `CitationsSummary`.**

### Gap
No bridge between `TafseerSource.reliability_score` (float) and the `ReliabilityLevel` enum
(`canonical | verified | supporting | experimental`) used by `SourceBadge`. The mapping must
be computed: ≥0.9 → canonical, ≥0.7 → verified, ≥0.5 → supporting, <0.5 → experimental.

---

## 5. Risks for Quran-Sensitive Answers

| Risk | Severity | Current Mitigation | Gap |
|---|---|---|---|
| LLM invents tafsir without source | Critical | `GROUNDED_SYSTEM_PROMPT` forbids it; `ConfidenceScorer` lowers score if no citations | No structural rejection of answers with zero validated citations |
| Wrong verse reference in citation | High | `verse_overlaps()` checks during extraction | Print-debugging still in production (`print()` calls in pipeline) |
| Refusal text in wrong language | High | None | `SAFE_REFUSAL_NO_SOURCES` is English-only string |
| Experimental source alone used for ruling | Medium | `ConfidenceScorer` lowers score | No hard block on single experimental source for fiqh |
| Translation presented as Quran text | Medium | `VersesSection` labels text correctly | No structural label in `citation.quoted_evidence` |
| Ayah reference invented | Medium | Regex extraction only matches what LLM outputs | No DB validation that cited ayah exists |
| Cache serves stale safe-refusal | Low | 1-hour TTL; only cached if `confidence ≥ 0.3` | Cache key does not include `status` |

---

## 6. Summary of Required Changes (Phase 2 Plan)

1. Add `status: "answered" | "no_verified_source" | "needs_clarification" | "error"` to schema.
2. Add `answer_language: "ar" | "en"` to schema.
3. Enforce `status="no_verified_source"` when `citations` is empty; use language-specific text.
4. Add `needs_clarification` detection for vague/decontextualised questions.
5. Enrich `Citation` with `reliability_level`, `author`, `quoted_evidence`, `explanation`.
6. Map `source_reliability` float → `ReliabilityLevel` string in pipeline.
7. Add hard check: experimental-only citations for ruling questions → `no_verified_source`.
8. Update frontend `CitationsSummary` to full citation cards with author, reliability badge, ayah.
9. Route frontend rendering on `status` not on `citations.length`.
10. Add unit tests for all schema rules.
