# Query embeddings: server CPU vs HF hosted

Question: given the slow hosted embedding call (~15 s observed during the
Phase 6 RAG runs), should the e5 query embedding run on the server CPU instead
of HF Inference Providers?

## Setup

| | |
|---|---|
| Model | `intfloat/multilingual-e5-large` (1024-d, the model behind the stored Qdrant vectors) |
| CPU path | `onnxruntime` 1.30 + `tokenizers`, **no torch**; the official ONNX exports from the model repo (`onnx/model.onnx` fp32, `onnx/model_qint8_avx512_vnni.onnx` int8); mean pooling + L2 norm (same as sentence-transformers) |
| Hardware | 4 vCPU Intel Xeon @ 2.10 GHz (AVX-512 VNNI), 15 GB RAM, 4 intra-op threads |
| Queries | 10 Arabic/English queries with the `query: ` prefix, 30 timed runs after one warm-up |
| Parity | (1) re-embed 64 stored tafsir passages (`passage: ` prefix) and compare with the vectors in Qdrant; (2) compare query vectors with HF hosted output; (3) top-10 Qdrant retrieval overlap |

## Measurements

| | ONNX int8 (CPU) | ONNX fp32 (CPU) | HF hosted |
|---|---|---|---|
| Weights on disk | 562 MB | 2.24 GB | none |
| Session load | 1.6 s | 3.4 s | n/a |
| Resident memory added | ~930 MB | ~1.84 GB | ~0 |
| Single query p50 | **23 ms** | **62 ms** | **234 ms** (warm) |
| Single query p95 / max | 32 ms | 131 ms | 1,422 ms (first call) |
| 16 passages, one batch | 1.7 s | 5.1 s | n/a |
| Passage cosine vs stored Qdrant vectors (mean / min) | 0.9945 / 0.9632 | 0.9993 / 0.9682 | (source of stored vectors) |
| Query cosine vs HF hosted (min, n=8) | 0.9936 | **1.0000** | — |
| Top-10 retrieval overlap vs HF hosted | 0.90 | **1.00** | — |
| Top-1 agreement vs HF hosted | 7/8 | 8/8 | — |
| Per-call billing / quota failures | none | none | billed; **2 of 10 calls failed with HTTP 402** (credits depleted) |

The 0.96 minimum passage cosine for both CPU variants is one long chunk where
truncation at 512 tokens differs; the means show the vectors are the same
model.

The 15 s figure did **not** reproduce in isolation: warm hosted calls took
145–264 ms and the first call 1.4 s. The 15 s came from the RAG enhancer making
several sequential embedding calls under rate limiting while the account was
running out of credits. Hosted latency is therefore variable and coupled to
account state, not intrinsically 15 s.

## Recommendation

**Keep HF hosted as the default; offer ONNX fp32 on CPU as an opt-in backend
for deployments that have the RAM.**

- **fp32 ONNX, not int8.** fp32 reproduces the hosted vectors exactly (cosine 1.0, identical top-10), so the existing Qdrant collections stay valid and the two backends can be switched freely. int8 is 2.7× faster and half the memory, but only 90 % top-10 overlap against the stored vectors; adopting it would need a full re-index with int8 to stay self-consistent.
- **Why not make CPU the default.** It needs about 1.8 GB RAM per process that loads it (the production command runs 4 Uvicorn workers, which would be about 7.4 GB) and a 2.2 GB weight download. Making that the default would put model weights back into the default deployment, which the mission forbids and point (b) audits against. The latency gain (62 ms vs ~230 ms warm) is real but small next to LLM generation time (several seconds).
- **When to turn it on.** Turn it on when hosted embedding latency or 402/429 failures show up in production metrics, or to stop paying per query. It also keeps retrieval working when HF credits run out, though synthesis still needs the hosted LLM.
- **How to deploy it, if enabled.**
  - Install `onnxruntime` and `tokenizers` as an optional extra, not a default dependency.
  - Fetch the weights at deploy time into a mounted volume, never into the image.
  - Load the model once per process. Either run fewer workers or put embedding in a single sidecar process.
  - Keep HF hosted as the fallback.

This change is not implemented on this branch: the default stays HF-only, as the mission requires. The opt-in backend fits behind the existing `HFEmbeddingModel` interface (`encode` / `aencode` / `get_sentence_embedding_dimension`), so no call site would change.

Reproduce with the scripts described above: an ONNX venv with `onnxruntime`,
`tokenizers`, `numpy`, `httpx`; `huggingface-cli download
intfloat/multilingual-e5-large --include "onnx/*"`.
