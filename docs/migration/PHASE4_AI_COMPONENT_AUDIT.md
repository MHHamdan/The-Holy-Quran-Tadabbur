# Phase 4: AI/ML component audit

The deployed backend needs **no GPU, no torch, no local model files**.
`torch`, `sentence-transformers` and `transformers` are no longer backend dependencies.

Options:
- **A**: Hugging Face hosted inference
- **B**: lightweight local CPU implementation
- **C**: deterministic, non-ML implementation

| Component | Before | Now | Option | Fallback when HF unavailable |
|---|---|---|---|---|
| RAG synthesis, verification assistant, quiz, grammar (LLM), tafsir summarise/explain | Ollama `qwen2.5` (GPU-routed) / Claude | HF chat, `HF_LLM_MODEL` (Llama-3.3-70B) | A | RAG returns `status=ai_unavailable` with sources shown verbatim; grammar uses QAC/static data; quiz returns 503/429 |
| Tafsir and verse embeddings (Qdrant queries, verse indexing, `index_tafseer.py`) | `sentence-transformers` e5-large on CUDA/CPU; `semantic_vector_search` loaded the model **on every request** | HF feature-extraction, `HF_EMBEDDING_MODEL` = `intfloat/multilingual-e5-large` (1024-d, same model as the stored vectors) | A | Retrieval falls back to keyword/DB search (existing hybrid path) |
| Similarity services (`semantic_embeddings`, `arabic_semantic_search`, `contextual_search`) | MiniLM / multilingual ST models loaded locally | Shared HF e5 model | A | Hashed TF-IDF vectors. On the first HF failure the service switches to the fallback for the rest of the process and clears its cache, so the two vector types are never compared |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (English-only), FP16 on GPU | HF `BAAI/bge-reranker-v2-m3` (multilingual, Arabic-capable) | A | Deterministic keyword overlap + BM25 (existing) |
| Emotion classification (therapy) | `facebook/bart-large-mnli` via `transformers`; **top-level `import torch` broke every therapy endpoint when torch was absent** | HF zero-shot (`HF_ZERO_SHOT_MODEL`, same model and hypothesis template), 10 s timeout, run off the event loop | A | Arabic and English keyword classifier (existing) |
| Speech-to-text (Tasmeeʿ) | `faster-whisper` local (optional extra, CTranslate2 + torch) | HF `openai/whisper-large-v3-turbo` with word timestamps (`HuggingFaceSTTProvider`) | A | REST returns 503/429; WebSocket sends `stt_unavailable`, then closes with 4003 after 3 failed windows |
| Query expansion | Islamic terminology glossary | unchanged | C | n/a |
| Crisis, discourse, tone, NER, thematic mapper, story/concept graph, consensus agent, fast/advanced similarity | rules, lexicons, graph algorithms, numpy | unchanged | C | n/a |
| Arabic NLP chain (farasa / camel-tools / stanza) | lazily imported, **never declared as dependencies**, so never installed | unchanged and not installed. The chain falls through to the scholar-verified Quranic Arabic Corpus data, then the HF LLM | C (+A) | QAC / static morphology |
| Recitation alignment, Arabic normalisation | deterministic | unchanged | C | n/a |

## Remaining local CPU models

**None in the default deployment.**

`faster-whisper` remains as an **opt-in** provider (`STT_PROVIDER=faster-whisper`,
`pip install -e ".[stt-local]"`) for self-hosters who want offline speech
recognition. It is not installed by default, and nothing depends on it. It
downloads its model from the Hugging Face Hub on first use; it uses no
owner-specific files.

## Cost and latency notes

- Every embedding, rerank, zero-shot and ASR call is billed against the HF account's Inference Providers credits. Embeddings for a RAG query are one short call; reranking batches all candidates into one call.
- Calls that sit in the request path have short timeouts: zero-shot 10 s, others `HF_TIMEOUT_SECONDS` (60 s). Blocking HTTP calls run in worker threads (`asyncio.to_thread`), not on the event loop.
- Re-indexing the whole tafsir corpus (~37k chunks) is about 1,200 batched embedding calls. Indexing is incremental (`is_embedded`) and refuses to write placeholder vectors.

## Verified live in this session (before credits ran out)

- chat (router)
- embeddings (1024-d, unit-normalised, batch input)
- reranker: Arabic and cross-lingual pairs scored as expected
- zero-shot: `grief` 0.9998 for a bereavement message
- ASR: "قل هو الله أحد" with word timestamps, from the 112:1 fixture
