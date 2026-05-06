# Phase C — Quran Question Classifier

**Platform:** Tadabbur Al-Quran  
**Version:** 1.0  
**Effective Date:** 2026-05-05

---

## 1. Purpose

The Quran Question Classifier is a pre-generation safety gate. It classifies every user question **before** retrieval or LLM generation so the system can:

- Block fatwa-like questions immediately (no LLM call)
- Route similarity/story/vocabulary/i'rab questions to the correct module
- Apply caution labels to scientific miracle claims before generation
- Request clarification for vague queries before wasting retrieval resources
- Refuse clearly non-Quranic topics with a safe message

**Defense in depth:** The classifier is defense layer 1 (pre-generation). `QuranAnswerGuard` remains defense layer 2 (post-generation). Both must remain active.

---

## 2. Supported Intents (14 values)

| Intent | Risk | Allowed to Generate | Route |
|---|---|---|---|
| `fatwa_like` | HIGH | **No** | `safe_refusal` |
| `scientific_miracle_claim` | HIGH | Yes (with caution) | `rag` |
| `qiraat` | MEDIUM | Yes (module unavailable → RAG) | `rag` |
| `morphology` | MEDIUM | Yes (module unavailable → RAG) | `rag` |
| `irab` | MEDIUM | Yes (module unavailable → RAG) | `rag` |
| `vocabulary_meaning` | LOW | Yes (module unavailable → RAG) | `rag` |
| `munasabah` | MEDIUM | Yes | `rag` |
| `similarity` | LOW | Yes | `similarity` |
| `story` | LOW | Yes | `stories` |
| `thematic_tafsir` | LOW | Yes | `rag` |
| `tafsir_summary` | LOW | Yes | `rag` |
| `general_question` | LOW | Yes | `rag` |
| `needs_clarification` | LOW | **No** | `clarification` |
| `unsupported` | LOW | **No** | `safe_refusal` |

---

## 3. Classification Priority

The classifier checks patterns in priority order:

1. **fatwa_like** — highest priority, immediately hard-blocks generation
2. **scientific_miracle_claim** — high risk, passes with mandatory caution labels
3. **qiraat** — specific recitation query
4. **morphology** — word form / root / pattern query
5. **irab** — grammatical parsing query
6. **vocabulary_meaning** — word meaning / gharib al-Quran
7. **munasabah** — contextual relationship between ayahs/surahs
8. **similarity** — related/similar verse search
9. **story** — Quranic narrative query
10. **thematic_tafsir** — theme-based verse grouping
11. **tafsir_summary** — general explanation/meaning query
12. **unsupported** — clearly non-Quranic topic
13. **needs_clarification** — query too short/vague (< 3 words)
14. **general_question** — default (send to RAG)

---

## 4. Routing Rules

| route_to | Meaning | Current implementation |
|---|---|---|
| `safe_refusal` | Return safe refusal immediately, no LLM call | ✓ Active |
| `clarification` | Return clarification request, no LLM call | ✓ Active |
| `rag` | Normal RAG retrieval + generation pipeline | ✓ Active |
| `stories` | Route to stories module | ✓ Classification only (pipeline stays RAG for now) |
| `similarity` | Route to verse similarity module | ✓ Classification only |
| `vocabulary` | Route to vocabulary module (planned) | Planned — Phase F |
| `irab` | Route to i'rab module (planned) | Planned — Phase G |
| `morphology` | Route to morphology module (planned) | Planned — Phase H |
| `search` | Route to search page | Future |

**Note:** For `stories`, `similarity`, `vocabulary`, `irab`, `morphology` — the classifier correctly identifies the intent and attaches the appropriate route label, but the pipeline currently still runs RAG for all `allowed_to_generate=True` classifications. Module-specific routing will be wired in when each module is built.

---

## 5. Safe Response Messages

### Fatwa-like (hard block)

**English:**
> "I cannot issue a fatwa. I can only show documented information from available sources. Please consult qualified scholars for religious rulings."

**Arabic:**
> "لا أستطيع إصدار فتوى. يمكنني فقط عرض معلومات موثقة من المصادر المتاحة، وينبغي الرجوع إلى أهل العلم في مسائل الفتوى."

### Scientific miracle claim (caution, not block)

**English:**
> "Connecting an ayah to scientific theories requires specialized scholarly and scientific review. This is presented as a contemporary reflection, not a definitive tafsir position."

**Arabic:**
> "الربط بين الآية والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة. هذا الطرح تأمل معاصر وليس موقفًا تفسيريًا قطعيًا."

### Unsupported topic

**English:**
> "No verified source available for this answer."

**Arabic:**
> "لا يوجد مصدر موثوق متاح لهذه الإجابة."

### Needs clarification

**English:**
> "Please specify the ayah or topic more clearly so I can search the verified sources."

**Arabic:**
> "يرجى تحديد الآية أو الموضوع بشكل أوضح حتى أستطيع البحث في المصادر الموثوقة."

### Module unavailable (qiraat / i'rab / morphology / vocabulary)

**English:**
> "This feature requires a verified source that is not yet available on this platform. The answer will be retrieved from general tafsir sources where possible."

**Arabic:**
> "هذه الميزة تحتاج إلى مصدر موثوق لم يتوفر بعد على هذه المنصة. سيتم البحث في مصادر التفسير العامة حيث أمكن."

---

## 6. Example Classifications

| Question | Intent | Allowed | Route |
|---|---|---|---|
| "هل يجوز الاستثمار في البنوك؟" | fatwa_like | No | safe_refusal |
| "Is it halal to eat this?" | fatwa_like | No | safe_refusal |
| "Does 51:47 prove the Big Bang?" | scientific_miracle_claim | Yes + caution | rag |
| "Explain the meaning of Al-Fatiha." | tafsir_summary | Yes | rag |
| "What is the tafsir of 2:255?" | tafsir_summary | Yes | rag |
| "Meaning of the word 'ghayb'?" | vocabulary_meaning | Yes + warning | rag |
| "What is the i'rab of this verse?" | irab | Yes + warning | rag |
| "What are the qiraat of this ayah?" | qiraat | Yes + warning | rag |
| "Story of Prophet Yusuf?" | story | Yes | stories |
| "Verses about patience?" | thematic_tafsir | Yes | rag |
| "Related ayahs to 2:255?" | similarity | Yes | similarity |
| "What is the relationship between these ayahs?" | munasabah | Yes | rag |
| "Stock market forecast?" | unsupported | No | safe_refusal |
| "explain" (1 word) | needs_clarification | No | clarification |

---

## 7. Limitations

1. **Keyword-based — not semantic.** A cleverly rephrased fatwa question might evade detection. The `QuranAnswerGuard` (Phase D) remains the last-line defense.
2. **No context window.** Each question is classified in isolation; follow-up questions in a conversation are re-classified independently.
3. **Arabic patterns without diacritics.** Harakat (vowel marks) are ignored; bare Arabic root matching may occasionally over- or under-match.
4. **Module routing is classification-only.** `route_to` labels are set correctly but full module routing wiring requires each module to be built first (Phases F–J).
5. **Language detection is heuristic.** Short mixed queries may be misidentified; classification still applies correctly because patterns are checked in both Arabic and English.

---

## 8. Why Post-Generation Guard Is Still Required

The classifier is a deterministic keyword filter. It cannot:

- Catch hallucinated ayah references generated by the LLM (only `QuranAnswerGuard` can)
- Block invented source IDs in LLM outputs (only `SourceValidator` can)
- Detect fatwa-like reasoning *inside* an otherwise normal answer
- Validate citation integrity post-generation

Therefore, both layers remain mandatory:
- **Classifier** → pre-generation (defense layer 1)
- **QuranAnswerGuard + SourceValidator** → post-generation (defense layer 2)

---

## 9. Implementation Files

| File | Purpose |
|---|---|
| `backend/app/safety/quran_question_classifier.py` | Classifier implementation + constants |
| `backend/app/rag/pipeline.py` | Integration: `_pre_classify()` method + import |
| `backend/app/rag/types.py` | New safe refusal constants (fatwa, unsupported, clarification) |
| `backend/tests/unit/test_quran_question_classifier.py` | 85 tests across 19 classes |
| `docs/phase-c-quran-question-classifier-audit.md` | Pre-implementation audit |
| `docs/phase-c-quran-question-classifier.md` | This document |

---

*This document contains no Quranic text, tafsir, or AI-generated religious content.*
