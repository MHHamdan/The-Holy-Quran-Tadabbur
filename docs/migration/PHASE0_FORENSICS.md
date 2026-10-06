# Phase 0 — Repository forensics (HF migration)

> **HISTORICAL record** of the repository state *before* the migration. Every
> Ollama / Anthropic / GPU item listed here has since been removed.

Date: 2026-10-06 · Branch: `feat/huggingface-mobile-production` · Base: `main@59cbcfe`

Code and executable tests were treated as authoritative; README claims were not.

## 1. Structure

| Area | Contents |
|---|---|
| `backend/` | FastAPI app (`app/`), 23 Alembic migrations, 62 scripts, 108 test files (~2,500 tests) |
| `frontend/` | React 18 + Vite + TS (221 source files), Playwright e2e, nginx Dockerfile |
| `data/` | Tracked: `raw/quran_uthmani.json`, `manifests/`, `concepts/`, `BUNDLE.lock`. Bulk tafsir corpora + QAC morphology are **not** tracked (data bundle, 262 MB, no GitHub release published) |
| root | `Makefile` (podman-based local stack), `docker-compose.prod.yml`, `docker-compose.portable.yml`, `streamlit_app.py` (separate Streamlit demo) |
| CI | one workflow: `.github/workflows/theme-audit.yml` (path-filtered; installs `backend/requirements.txt`, which does not exist) |

There is **no** root `docker-compose.yml` even though the README references one.

## 2. AI / model call sites (traced)

### LLM generation
| Call site | Backend | Notes |
|---|---|---|
| `app/rag/llm_provider.py` | `OllamaLLM` (HTTP `/api/chat`), `ClaudeLLM` (sync `anthropic` SDK inside async code) | `_detect_gpu()` shells out to `nvidia-smi` |
| `app/rag/pipeline.py` | `get_llm()` | GPU→`qwen2.5:14b`, no GPU→`llama3.2:3b`; LLM exceptions are returned to the user as `"Error generating response: {e}"` (leak) |
| `app/api/routes/rag.py` | Ollama `/api/tags` pre-flight, Anthropic key check | |
| `app/api/routes/therapy.py` | Ollama/Claude availability probe, then RAG pipeline | |
| `app/api/routes/quiz.py` | `get_llm(ollama_model=ollama_model_fast)` | |
| `app/services/grammar_ollama.py` | direct Ollama `/api/chat` | used by `/grammar/*` and NLP fallback chain |
| `app/services/grammatical_analyzer.py` | direct Ollama `/api/generate`, hard-coded `http://localhost:11434` | used by `quran.py` word analysis |
| `app/services/tafsir_api.py::TafsirLLMService` | direct Ollama `/api/generate`, default `host.docker.internal:11434` | summarize / explain word / answer |
| `app/services/translation.py` | Anthropic `messages.create` pattern (client never injected → dead path) | |
| `app/verify/ai_assistant.py` | `get_llm()` | verification workflow |
| `app/api/routes/health.py` | reports `anthropic` configured | |

### Other ML (all local, torch-based)
| Component | Model | Where |
|---|---|---|
| Tafsir/verse embeddings | `intfloat/multilingual-e5-large` (1024-d) via `sentence-transformers` | `rag/retrieval.py`, `services/semantic_search.py` (re-loads the model **on every request**), `verse_embedding_service.py`, `scripts/index/index_tafseer.py` |
| Similarity embeddings | MiniLM / e5 variants, TF-IDF fallback | `semantic_embeddings.py`, `arabic_semantic_search.py`, `contextual_search.py` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (English-only), keyword fallback | `rag/reranker.py` |
| Emotion | `facebook/bart-large-mnli` via `transformers`; **top-level `import torch`** | `services/emotion_classifier.py` |
| STT (Tasmee) | `faster-whisper` local, optional extra | `stt/providers/faster_whisper.py` |
| Arabic NLP | farasapy / camel-tools / stanza — imported lazily, **not declared as dependencies** (never installed) | `nlp/providers/*` |

### Hard GPU / local assumptions
- `nvidia-smi` routing in `llm_provider._detect_gpu` and `scripts/start_all.sh` (`nvidia-smi -i 3`)
- `torch.cuda.is_available()` device selection in 6 modules
- `localhost:11434` in config, services, scripts, monitoring, Docker compose
- `docker-compose.prod.yml` points the backend at `host.docker.internal:11434` (owner workstation)

## 3. Baseline test run (before any change)

Environment: Python 3.11 venv, no torch (download.pytorch.org is blocked here; and the target is torch-free), PostgreSQL 16, Redis 7, Qdrant 1.7.4 (Docker).

| Run | Result |
|---|---|
| Collection with pyproject deps as resolved today | **ImportError** — SQLAlchemy 2.1 async needs `greenlet` (not declared) |
| After installing greenlet | 44 collection errors — SQLAlchemy 2.1 defaults `postgresql://` to psycopg 3 |
| Empty DB | 2274 passed / 201 failed / 22 skipped |
| Seeded DB (quran, stories, atlas, concepts, themes, rhetoric) | 2348 passed / 124 failed / 25 skipped |

Failure causes on the seeded DB:
- 70 tests: `ModuleNotFoundError: torch` (therapy endpoints import the emotion classifier, which imports torch at module top level)
- 6 tests: FastAPI ≥0.137 nests routers (`_IncludedRouter`) so `app.routes` no longer lists API paths
- ~48 tests: need data that is only in the unpublished data bundle (tafsir corpora, QAC morphology, Qdrant vectors)
- `seed_story_graphs.py` fails under psycopg 3 (tuple `IN :ids` bind)

Dependency fixes applied in this phase: `sqlalchemy[asyncio]>=2.0.25,<2.1`, `fastapi>=0.109.0,<0.137`.
Migrations: `alembic upgrade head` runs cleanly on an empty PostgreSQL 16 database (23 revisions).

## 4. Security observations (handled in Phase 11)

- `app/api/routes/kg.py`: `KG_ADMIN_TOKEN` falls back to the public string `tadabbur-admin-dev-token` → KG admin endpoints are open if the env var is unset. **Fail-open; fix.**
- `frontend/src/lib/api.ts`: `VITE_ADMIN_API_KEY` bakes the backend admin key into the JS bundle.
- `.gitignore` covers `.env` but not `.env.*`.
- History scan (214 commits, full clone): no HF / Anthropic / OpenAI / AWS / GitHub tokens or private keys found; only dev placeholders (`tadabbur-admin-dev-token`, `test_admin_token_dev`).
- Docker prod compose ships SurrealDB with `root/root` and `ADMIN_TOKEN` default `change_this_in_production`.

## 5. External data reachability from this VM

`api.alquran.cloud`, `api.quran.com`, `api.qurancdn.com`, jsDelivr: **unreachable** (tafsir download scripts cannot run here).
`huggingface.co`, `router.huggingface.co`: reachable (proxy-authenticated).
The HF dataset `riotu-lab/Quran-Tafseers` (Apache-2.0; 8 classical tafsir works × 6,235 ayat) is used as a dev-only evidence source for benchmarks and local verification; it is not committed.
