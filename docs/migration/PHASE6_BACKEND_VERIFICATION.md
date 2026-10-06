# Phase 6: Backend verification and repairs

Environment: Ubuntu 24.04 VM, Python 3.11, PostgreSQL 16, Redis 7, Qdrant 1.7.4 (Docker), no GPU.

## How the backend was exercised

| Check | Result |
|---|---|
| Clean install from `backend/pyproject.toml` only (fresh venv, no torch) | ✅ installs; no torch / sentence-transformers / anthropic |
| Boot with environment variables only (no `.env`) | ✅ `/health` 200, `/ready` 200 |
| `alembic upgrade head` on an empty database, then `downgrade -1` / `upgrade head` | ✅ single head `q6r7s8t9u0v1` |
| Seeding: Qur'an (6,236 ayat), stories, story atlas and graphs, concepts, themes, rhetoric | ✅ |
| Tafsir ingestion: 5 classical Arabic works (31,081 chunks) | ✅ via `seed_tafseer.py`. Dev-only input exported from the Apache-2.0 HF dataset `riotu-lab/Quran-Tafseers`, because the tafsir CDNs are unreachable from this VM. Not committed. |
| Vector indexing with HF embeddings | ✅ 586 tafsir chunks (Al-Fatiha and Al-Baqarah, two works) plus the Qur'an verse collection (partial; HF throttling) |
| GET smoke test of every OpenAPI route with sample parameters | 287 × 200 before fixes. All 5xx were fixed except the external Asbab API (blocked by the VM proxy; returns a clean 503). |
| Live HF end to end: `/rag/ask` (Arabic), Tasmee transcription, quiz, grammar, therapy | ✅ (see the G11 evidence in the session report) |
| Production mode (`ENVIRONMENT=production`) | ✅ `/docs` disabled, generic errors, wildcard CORS dropped, hostile origin rejected, admin 401/403, startup config report |
| Rate limiting | ✅ `/rag/ask` 429 after 20/min; `/quran/resolve` 429 after 30/min (was 500, see below) |

## Defects found and fixed

1. **`/openapi.json` and `/docs` returned 500.** An unresolved `"Request"` forward reference in `/quran/resolve` broke schema generation. Because the request object was never injected, that route's per-IP rate limit was also a no-op.
2. **`/quran/resolve` rate limit returned 500** once it could trigger: `ErrorCode.RATE_LIMITED` did not exist. Every rhetoric 404 also returned 500, because of a non-existent `ErrorCode.RESOURCE_NOT_FOUND`. A test now checks every `ErrorCode.X` reference in the codebase.
3. **Schema drift.** The ORM models selected 10 columns that no migration creates (`tasmee_events`, `tasmee_mistakes`, `tasmee_progress`, `theme_suggestions.origin`), so `/tasmee/progress` and similar queries returned 500. New additive migration `q6r7s8t9u0v1`. A model-vs-database column test was added.
4. **`/quran/semantic/similar` and `/semantic/connections` always returned 500**: the route and service disagreed on the result type. Also ~30 s per request, because root extraction re-normalised the whole root dictionary for each of ~6,200 verses. `extract_root` and `normalize_arabic` are now memoised: warm requests take 1.8 s with identical results.
5. **`/quran/similarity/semantic` hung for more than 90 s** without the verse index: it embedded 500 verses per request. It now has a 20 s budget, then a deterministic lexical ranking (`coverage: partial_lexical`). The enhancement step has its own budget.
6. **Unauthenticated cost endpoints.** `POST /quran/search/semantic/index` (re-embeds the whole Qur'an) and four cache-warm endpoints (one runs RAG queries that spend LLM credit) are now protected by `X-Admin-API-Key`.
7. **`settings.debug` defaulted to `True`**, which returns raw exception text and exposes `/docs` if `DEBUG` is unset. It now defaults to `False` and is forced off in production.
8. **SurrealDB outages returned 500.** They now return a 503 envelope. An uncaught `HFInferenceError` returns 429 (quota) or 503.
9. **`/performance/db-pool` returned 500** because it read private SQLAlchemy pool attributes.
10. **The thematic fast path hijacked unrelated questions.** Substring keyword matching made `هم` ("worry") fire inside فهم/منهم and `ذكر` inside ذكرها, so questions on other topics got canned consolation verses. Matching is now whole-word and proclitic-aware. The same bug made "الحكمة" ("wisdom") classify as a fiqh *ruling* (`حكم`).
11. **Reranker scale mismatch.** The HF cross-encoder's probabilities (correct passage ≈0.08, unrelated ≈0.001) were overwriting retrieval relevance, which the confidence gate is calibrated against. Every answer was refused. The reranker now orders results only, and its score is kept as `rerank_score`.
12. **Al-Baghawi was refused wholesale.** It is listed as a verified source in `docs/sunni-source-review-policy.md` and shipped by the ingestion manifest, but was missing from the trust registry. Untrusted chunks are now also dropped *before* generation.
13. **Zero-confidence answers were shown under `no_verified_source`.** The safe fallback is now returned instead. Sentences whose only citations were rejected are removed, not just their markers.
14. **Tasmee graded the Basmala prefix as 4 missing words** on ayah 1 of every surah except Al-Fatiha. The canonical store prefixes it editorially; Tasmee now uses the recitable text.
15. **Embedding calls had no retry.** One HF 502 aborted a 6,236-verse indexing job. Transient errors now get up to 3 attempts; quota and auth errors are not retried.

## Services

- **PostgreSQL, Redis, Qdrant**: required and in use.
- **SurrealDB**: still required. The knowledge-graph pages (`/kg/story/*`, `/kg/search`) are used by the frontend. The backend now degrades to a 503 when it is down.
