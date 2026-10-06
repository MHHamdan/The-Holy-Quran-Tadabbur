# Phase Y — Grounded Per-Verse Ask AI

## Motivation

The in-verse AI Assistant on `/mushaf` previously called three endpoints
that fed the raw selected-verse + tafsir text directly to an LLM:

- `POST /api/v1/tafseer/llm/summarize`
- `POST /api/v1/tafseer/llm/explain-word`
- `POST /api/v1/tafseer/llm/answer`

These calls returned a plain string with **no citations, no source
tracking, no confidence, and no safe-refusal**. That violates the
project content policy (`docs/quran-content-policy.md` / `CLAUDE.md`)
which requires every tafsir-style answer to be retrieval-based and
attributed.

## What changed

A new router `backend/app/api/routes/rag_verse.py` (registered at
`/api/v1/rag`) exposes four endpoints that route every per-verse
question through the existing `RAGPipeline.query` so the answer is
backed by retrieved tafseer chunks with mandatory citations.

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/rag/verse/ask` | Free-form Q&A about a specific verse |
| `POST /api/v1/rag/verse/summarize` | Summarize tafsir for a verse |
| `POST /api/v1/rag/verse/explain-word` | Explain a word in a verse |
| `GET  /api/v1/rag/verse/suggested-questions` | Bilingual templated prompts |

The frontend `MushafPage.tsx` AI sidebar now calls these endpoints and
renders a new `GroundedAnswerCard` component which displays:

- Status banner (`answered` vs `no_verified_source`)
- Confidence percentage + source count
- AI-assisted disclaimer (`rag_ai_disclaimer`)
- The answer body (with copy button)
- Citation cards — source name (AR/EN), author, verse reference, excerpt
- Bilingual suggested-question chips when refused
- Warnings array

## Verse-anchoring without new retriever code

`HybridRetriever._direct_verse_lookup` already scopes chunks to a
surah/ayah window when the query contains a `surah:ayah` pattern. The
new endpoints simply prefix `الآية {ref}: …` / `Verse {ref}: …` to the
question text so the existing fast-path kicks in:

```python
# rag_verse.py
def _compose_anchored_query(*, surah, ayah_start, ayah_end, question, language):
    ref = f"{surah}:{ayah_start}-{ayah_end}" if ayah_end else f"{surah}:{ayah_start}"
    return (f"الآية {ref}: " if language == "ar" else f"Verse {ref}: ") + question.strip()
```

This means we did NOT modify `backend/app/rag/prompts.py` or any other
RAG internals — the policy boundary on `prompts.py` remains intact.

## Safe-refusal contract

When `RAGPipeline.query` returns `status == "no_verified_source"` (or
when `citations == []`) the endpoint:

1. Echoes the bilingual refusal text from `prompts.py`
   (`SAFE_REFUSAL_NO_SOURCES_AR` / `SAFE_REFUSAL_NO_SOURCES_EN`).
2. Attaches `suggested_questions` with the three canonical templates
   for the requested language.

The frontend renders an amber banner ("لا توجد مصادر موثوقة كافية…")
plus the suggestions as one-click chips. **No raw LLM fallback** is
used — falling back to ungrounded `/tafseer/llm/*` was explicitly
rejected in the design review.

## Request / response examples

### Suggested questions

```
GET /api/v1/rag/verse/suggested-questions?surah=1&ayah_start=2&language=ar
```
```json
{
  "surah": 1,
  "ayah_start": 2,
  "ayah_end": null,
  "language": "ar",
  "questions": [
    { "id": "revelation", "text": "ما سبب نزول هذه الآية؟", "language": "ar" },
    { "id": "lessons",   "text": "ما الدروس والعبر المستفادة من هذه الآية؟", "language": "ar" },
    { "id": "context",   "text": "ما علاقة هذه الآية بما قبلها وما بعدها؟", "language": "ar" }
  ]
}
```

### Ask about a verse

```
POST /api/v1/rag/verse/ask
{
  "surah": 2,
  "ayah_start": 30,
  "question": "ما المعنى الأساسي للخلافة في هذه الآية؟",
  "language": "ar"
}
```

Returns a `GroundedResponse` (see `backend/app/rag/types.py:GroundedResponse`)
with `citations[]`, `confidence`, `status`, `verse: {surah, ayah_start, ayah_end, reference}`,
and `suggested_questions[]` whenever the answer is refused.

## Validation rules

- `surah`: 1..114 (enforced by Pydantic `ge=1, le=114`)
- `ayah_start`: ≥ 1
- `ayah_end`: optional, ≥ `ayah_start` if present
- `question`: 3..1000 chars after trim
- `word`: 1..80 chars, non-empty after trim
- `language`: `"ar"` or `"en"` only

Invalid input returns HTTP 422 (Pydantic) or 400 (route-level
range check).

## Tests

`backend/tests/unit/test_rag_verse_endpoints.py` — 14 tests covering:

- grounded path returns citations + verse metadata
- safe-refusal attaches the three suggested questions
- surah / ayah / language validation
- Arabic + English suggested-questions endpoint returns 3 entries each
- `_compose_anchored_query` builds the expected reference token

All tests stub `RAGPipeline.query` so the suite runs in <10 seconds
without calling the LLM.

## Migration / deprecation note

The legacy `/api/v1/tafseer/llm/{summarize,explain-word,answer}`
endpoints remain in place for backwards compatibility with any external
integrations but are **no longer called by the frontend**. They should
be retired in a future phase once we confirm no external consumers
depend on them.
