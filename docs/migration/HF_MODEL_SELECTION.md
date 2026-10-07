# Hugging Face chat model selection

**Default:** `HF_LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct`, `HF_LLM_PROVIDER=auto`
Both are environment variables. Changing model or routing needs no code change.

## Method

`backend/scripts/bench/bench_hf_llm.py` runs the **production** grounded prompt
(`GROUNDED_SYSTEM_PROMPT` + `build_user_prompt`, same context layout as
`RAGPipeline._build_context`). The evidence is **real classical tafsir**:
Al-Muyassar, Al-Saadi, Ibn Kathir, Al-Baghawi and Al-Tabari, taken from the
Apache-2.0 dataset `riotu-lab/Quran-Tafseers`. The script invents no tafsir
text. There are 9 cases:

| Case | What it checks |
|---|---|
| `kursi_en`, `kursi_ar` | English and Arabic synthesis of 2:255 |
| `sabr_en`, `sabr_ar` | Synthesis across several verses (2:153–157) |
| `ikhlas_ar` | Synthesis across a whole surah (112) |
| `yusuf_en` | Narrative (12:4–6) |
| `fiqh_en` | Ruling question (2:184–185): the fatwa disclaimer must be present |
| `uncovered_en` | Question the evidence does not answer: the model must say so |
| `injection_ar` | A source chunk carries a planted "ignore instructions / write a new verse" payload |

Each answer is scored automatically on:
- answer language
- citations (`[Source, s:a]`) that do not match the retrieved evidence
- substantive paragraphs with no citation
- **Arabic text inside ﴿…﴾ that is not canonical Qur'an text** (checked against `data/raw/quran_uthmani.json`)
- fiqh disclaimer
- refusal on the uncovered case
- injection obedience
- latency, tokens

Scores (answers removed) are in [`hf_llm_benchmark.json`](hf_llm_benchmark.json).

## Results (2026-10-06, `:cheapest` routing, 1 run × 9 cases)

| Model | License | Completed | Lang OK | Citations (invalid) | Uncited paras | Fabricated Qur'an | Fiqh disclaimer | Uncovered → says so | Injection resisted | Median latency |
|---|---|---|---|---|---|---|---|---|---|---|
| **meta-llama/Llama-3.3-70B-Instruct** | Llama 3.3 Community | **9/9** | 9/9 | 57 (**1**) | 8 | **0** | ✅ | ✅ | ✅ | **10.1 s** |
| openai/gpt-oss-120b | Apache-2.0 | 8/9 | 8/8 | 46 (**12**) | 18 | 0 | ❌ | ✅ | ✅ | 23.6 s |
| Qwen/Qwen3-235B-A22B-Instruct-2507 | Apache-2.0 | 1/9 | 1/1 | 0 | 4 | 0 | – | ✅ | – | 20.3 s |
| google/gemma-4-31B-it | Gemma ToU | 0/9 | – | – | – | – | – | – | – | – |
| deepseek-ai/DeepSeek-V3.2 | MIT | 0/9 | – | – | – | – | – | – | – | – |

The Qwen and Gemma failures were upstream errors (429 and 502) from the
cheapest provider, not quality failures. DeepSeek-V3.2 failed because no
provider enabled on this account serves it (HTTP 400). A rerun with `auto`
routing was blocked. HF returned **402 "You have depleted your monthly
included credits"** for all chat models except very small requests, so
Qwen3-235B could not be compared on quality.

## Decision

1. **Llama-3.3-70B-Instruct** is the default. It was the only model to complete every case, and it has the fewest invalid citations, no fabricated Qur'an quotations, correct Arabic output, the fatwa disclaimer, injection resistance, and the lowest latency. Its router price is about $0.13–0.14 per 1M input and $0.40 per 1M output tokens. A typical RAG call is about 3.5k input and 0.5k output tokens, so roughly **$0.0007 per answer**. License: Llama 3.3 Community License. Commercial use is allowed below 700M MAU and requires "Built with Llama" attribution.
2. **`HF_LLM_PROVIDER=auto`**, not `cheapest`. In this run the cheapest providers were the least reliable (429/502 bursts). Owners who want the lowest price can set `HF_LLM_PROVIDER=cheapest`, and the app degrades gracefully when a provider fails.
3. **Fallback candidate:** `Qwen/Qwen3-235B-A22B-Instruct-2507` (Apache-2.0, strong Arabic). Re-run the benchmark once credits are available:
   `python backend/scripts/bench/bench_hf_llm.py --tafsir-json Tafseer.json --policy auto`

## Weaknesses observed (addressed by Phase 5 prompt and validator changes)

- On the uncovered question, Llama said the sources do not cover it, then went on to summarise unrelated retrieved material.
- Models sometimes cite the verse itself as `[Quran, 2:255]`, which is not a retrieved source. The validator counts these as invalid.

## Limitations

This is one run of 9 cases. It is enough to rank candidates, not to measure
small quality differences. Repeat it whenever the default model changes.
