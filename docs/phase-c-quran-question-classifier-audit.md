# Phase C — Quran Question Classifier: Pre-Implementation Audit

**Platform:** Tadabbur Al-Quran  
**Audit date:** 2026-05-05  
**Auditor:** Claude Code (Phase C)

---

## 1. Current Intent Classification Behavior

### 1.1 Where Classification Runs

Two separate classifiers exist and are called in sequence:

| Location | Method | Type | Called from |
|---|---|---|---|
| `backend/app/rag/query_expander.py` | `QueryExpander.classify_intent()` | Rule-based | `expand_query()` |
| `backend/app/rag/pipeline.py` | `RAGPipeline._classify_intent()` | Rule-based async | `RAGPipeline.query()` step 1 |

Both return `QueryIntent` (enum: `VERSE_MEANING`, `STORY_EXPLORATION`, `THEME_SEARCH`, `COMPARATIVE`, `LINGUISTIC`, `RULING`, `UNKNOWN`).

`pipeline._classify_intent()` is the authoritative one; `query_expander.classify_intent()` only affects query term expansion.

### 1.2 Current Intent Taxonomy (7 values)

```
VERSE_MEANING     — tafsir, meaning, explain
STORY_EXPLORATION — story, prophet, narrative
THEME_SEARCH      — theme, topic, about
COMPARATIVE       — compare, difference, between
LINGUISTIC        — root, grammar, i'rab
RULING            — ruling, halal, haram (fiqh — informational only)
UNKNOWN           — anything else
```

### 1.3 Current Routing Behavior per Intent

- All intents → RAG retrieval → LLM generation → citation validation → source validation
- `RULING` → same pipeline + `SAFE_REFUSAL_FIQH` warning *appended after generation*
- No intent causes an early exit before retrieval/generation

---

## 2. Weaknesses Found

### 2.1 Fatwa Queries Reach the LLM
`RULING` intent is classified correctly but does **not block generation**. A fatwa-like query ("Is it haram to invest in X?") is sent to the LLM with only a post-generation disclaimer appended. The LLM can still produce a detailed jurisprudential analysis that a user might treat as a fatwa.

### 2.2 Scientific Miracle Claims Are Undetected Before Generation
There is no intent for `scientific_miracle_claim`. A query like "Does 51:47 prove the Big Bang?" is classified as `VERSE_MEANING` and sent to the LLM without any pre-generation caution. The `QuranAnswerGuard` (Phase D) catches it post-generation, but the LLM has already processed it.

### 2.3 Missing Fine-Grained Intents
The 7-value taxonomy cannot route to planned modules:
- No `vocabulary_meaning` → cannot route to `/vocabulary` (Phase F)
- No `irab` → cannot route to `/tools/irab` (Phase G)
- No `morphology` → cannot route to `/morphology` (Phase H)
- No `munasabah` → cannot route to `/munasabah` (Phase J)
- No `qiraat` → cannot handle qira'at questions safely
- No `similarity` → cannot route to `/similarity` page
- No `thematic_tafsir` → thematic questions go to generic VERSE_MEANING

### 2.4 No Unsupported / Needs-Clarification Pre-Routing
Vague or off-topic queries are classified as `VERSE_MEANING` by default and sent to RAG retrieval. This wastes retrieval resources and can produce a "best effort" hallucinated answer for questions that should be refused.

### 2.5 Classifier Duplication
`pipeline._classify_intent()` and `query_expander.classify_intent()` implement overlapping logic with slight differences (e.g., `query_expander` checks for "fatwa", "فقه", "شرعي"; `pipeline` does not). The two classifiers can disagree.

---

## 3. Where Fatwa/Scientific-Miracle Detection Currently Happens

| Concern | Detection point | Action |
|---|---|---|
| Fatwa (fiqh) | `pipeline._classify_intent()` — checks "ruling", "halal", "haram" | Sets `RULING` intent; appends `SAFE_REFUSAL_FIQH` warning **post-generation** |
| Fatwa keyword in answer | `quran_answer_guard.py` (Phase D) — `_FATWA_KEYWORDS` | **Hard block** post-generation |
| Scientific miracle | `quran_answer_guard.py` (Phase D) — `_SCIENTIFIC_MIRACLE_KEYWORDS` | Adds caution labels **post-generation** |
| Missing ayah ref | `quran_answer_guard.py` (Phase D) | **Hard block** post-generation |

**Key gap:** All safety checks except source_validator run *after* LLM call. The LLM is still invoked even for clearly unsafe queries (fatwa, scientific miracle), wasting compute and introducing risk.

---

## 4. How the Classifier Should Integrate with QuranAnswerGuard

```
User Question
     │
     ▼
QuranQuestionClassifier.classify(question)
     │
     ├─ allowed_to_generate = False → Return safe_refusal immediately (no LLM call)
     │
     ├─ route_to = "clarification" → Return needs_clarification immediately
     │
     └─ allowed_to_generate = True → Continue to RAG pipeline
            │
            ▼
       FAST-PATH check (direct verse lookup)
            │
            ▼
       _classify_intent() → QueryIntent (for retrieval/generation)
            │
            ▼
       RAG retrieval → LLM generation
            │
            ▼
       QuranAnswerGuard.validate() ← Still required (post-generation safety)
            │
            └─ Guard blocks → Replace answer with safe refusal
```

**Principle:** The classifier is pre-generation defense. The guard is post-generation defense. Both must remain active — defense in depth.

---

## 5. Recommended Implementation Plan

### Step 1: Define `QuestionClassification` dataclass
File: `backend/app/safety/quran_question_classifier.py`

### Step 2: Implement rule-based classifier
- 14 intent types with Arabic + English keyword patterns
- Language detection (Arabic script presence)
- Risk level assignment
- Routing decision
- Bilingual warning messages

### Step 3: Add safe refusal constants to `types.py`
- `SAFE_REFUSAL_FATWA_EN` / `_AR`
- `SAFE_REFUSAL_UNSUPPORTED_EN` / `_AR`

### Step 4: Integrate into `pipeline.py`
- Import classifier
- Add `_pre_classify()` method
- Call it at the start of `query()`, after language validation
- Map classifier intent to `QueryIntent` for backward-compatible retrieval

### Step 5: Write tests
- 18+ unit tests for classifier
- Verify pipeline integration via existing RAG tests

### Step 6: Update docs

---

*This audit informs Phase C implementation. No Quranic text was generated or modified.*
