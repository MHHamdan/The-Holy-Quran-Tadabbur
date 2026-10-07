# Phase 12: Testing strategy for the HF backend

| Command | What runs | HF credit |
|---|---|---|
| `pytest -m "not live_hf"` | Every normal test. `tests/conftest.py` clears the HF token for every non-live test, so a missing mock degrades to the "not configured" path instead of a paid call. | none |
| `pytest` (no marker) | Same; `live_hf` tests are collected but skipped with a reason | none |
| `pytest -m live_hf` (or `RUN_LIVE_HF=1`) | Live smoke tests in `tests/live/` plus the live emotion checks | minimal |

## Upstream-failure matrix (mocked, `tests/unit/test_hf_llm_provider.py`, `tests/unit/test_hf_components.py`)

Covered:
- valid response (system/user separation, temperature, max tokens, usage, model id)
- timeout
- 401 → `auth`
- 403 → `forbidden`
- 402/429 → `quota`
- 404/503 and "not supported by any enabled provider" → `model_unavailable`
- 400/422 → `bad_request`
- malformed bodies (no choices, empty or null content, missing fields)
- network outage, including huggingface_hub's vendored `httpx2` errors
- missing token
- retry on 5xx/network only
- JSON-mode fallback
- `<think>` stripping
- errors never contain the token or upstream body
- embeddings dimension guard and retries (quota is not retried)
- reranker fallback
- STT word timestamps, silence and errors

Citation validation and Arabic/English answer handling are covered by `tests/unit/test_quranic_safety_phase5.py` (offline) and `tests/live/test_live_hf_smoke.py` (live).

## Live smoke tests (`tests/live/test_live_hf_smoke.py`)

- chat: English and Arabic
- unknown model → `model_unavailable`
- embeddings: dimension and ranking
- reranker: ordering
- zero-shot emotion
- speech-to-text on a recitation fixture
- grounded RAG in English and Arabic: citations ⊆ retrieved chunk IDs, answer in the requested language

If the account's credits are exhausted (HTTP 402/429) a test **skips with that reason** instead of failing. Any other upstream error fails.
