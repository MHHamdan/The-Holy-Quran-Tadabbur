# Phase 5: Qur'anic safety architecture (after the HF migration)

Regression suite: `backend/tests/unit/test_quranic_safety_phase5.py` (40 tests,
offline, using a fake LLM).

| # | Property | Enforcement | Tests |
|---|---|---|---|
| 1 | Never fabricate Qur'an text | Every quoted Arabic span (﴿﴾ « » “ ” "…") in an AI answer must appear verbatim in the canonical Qur'an (Uthmani or Imla'i, loaded from `quran_verses`) or in the retrieved evidence. If not, it is replaced with a visible "[quotation removed …]" marker and a warning is added. If the canonical text cannot be loaded, the check fails closed. | `TestNoFabricatedQuran` |
| 2 | Never invent tafsir | An answer with **no valid citation** is withheld and replaced by the safe fallback. This replaces the old behaviour of auto-attaching the top retrieved chunks as citations when the model omitted them. The explain-word prompt is limited to linguistic meaning with no attribution to scholars. | `test_uncited_answer_is_withheld`, `test_only_invalid_citations_is_withheld_in_arabic` |
| 3 | Qur'an text and facts from the canonical store | Fast-path surah names now come from `quran_verses`. **Bug fixed:** every famous verse used to be described as "Surah Al-Baqarah" (e.g. "Al-Fatiha is verse 1 of Surah Al-Baqarah"). | `test_famous_verse_fast_path_uses_canonical_surah_name` |
| 4 | Tafsir only from approved, retrieved sources | The existing trusted-source registry hard block is kept and tested | `TestApprovedSources` |
| 5 | AI synthesis structurally distinct | `answer_kind` (`ai_synthesis` / `source_digest` / `refusal` / `notice`) and `ai_generated` on every RAG response. Evidence and `tafsir_by_source` stay separate fields. `/tafseer/llm/*` responses carry `ai_generated=true` and a disclaimer. | `TestStructuralDistinction`, `TestTafsirLLMEndpoints` |
| 6 | Cite actual retrieved chunk IDs | Citations are built only by matching `[Source, s:a]` to a retrieved chunk, so `chunk_id` is always from the retrieved set | `test_valid_citations_map_to_retrieved_chunk_ids` |
| 7 | Reject citations not in the evidence | Unmatched citations are counted, **removed from the answer text** and reported in a warning. `[Quran, s:a]` references are accepted only for ayat that exist in the canonical corpus. | `TestCitations` |
| 8 | Insufficient evidence → existing safe fallback | No chunks → `SAFE_REFUSAL_NO_SOURCES_*` with no LLM call. A model reply that cites nothing gets the same fallback. HF outage or quota → `status=ai_unavailable` with the sources shown verbatim and no error internals. | `test_no_retrieved_evidence_returns_existing_fallback`, `test_hf_failure_returns_notice_with_sources_and_no_internals` |
| 9 | Fiqh is never a personalised fatwa | The pre-classifier refusal is kept. For ruling intents the disclaimer is now **appended to the answer itself** (EN/AR) if the model omitted it. | `TestFiqh` |
| 10 | Injected source text cannot override instructions | Each chunk is fenced in a single `<source>` block. Fence-closing tags, chat-template tokens, markdown/`[Source:` headers inside sources are neutralised, and attributes are escaped. The system prompt states that sources and history are data. Conversation history (user-controlled; `/therapy/chat` accepts it from the client) is **no longer concatenated into the sources block**: it gets its own labelled section. If a model does obey a payload, rules 1 and 7 still strip the invented verse and fake citation. | `TestPromptInjection` |

Also hardened: `/tafseer/llm/*` errors no longer echo exception text to clients.
