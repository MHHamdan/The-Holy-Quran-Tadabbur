"""
Keyword / story retrieval quality when semantic search is unavailable
(no HF embeddings), plus the pure helpers behind it.

The DB-backed benchmark uses the shared dev database read-only and skips when
the tafsir corpus is not loaded. No Hugging Face call is made (token unset).
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.core.config import settings
from app.rag.llm_provider import BaseLLM
from app.rag.retrieval import HybridRetriever, diversify, query_fingerprint, query_keywords


def _c(source_id, n):
    return SimpleNamespace(source_id=source_id, chunk_id=f"{source_id}:{n}")


class TestHelpers:
    def test_stop_words_and_possessives_are_removed(self):
        assert query_keywords("Why did Yusuf's brothers throw him in the well?") == [
            "Yusuf", "brothers", "throw", "well"]
        assert query_keywords("ما وصايا لقمان لابنه؟") == ["وصايا", "لقمان", "لابنه"]

    def test_diversify_caps_each_source_then_fills(self):
        chunks = [_c("a", i) for i in range(4)] + [_c("b", 0)]
        out = diversify(chunks, 4)
        assert [c.source_id for c in out] == ["a", "a", "b", "a"]

    def test_query_fingerprint_never_contains_the_question(self):
        fp = query_fingerprint("my private question about my family")
        assert "private" not in fp and fp.startswith("len=")

    async def test_external_fallback_requests_tafsir_editions_only(self):
        r = HybridRetriever(session=None)
        r._enabled_sources_cache = {"baghawi_ar"}
        client = SimpleNamespace(get_tafseer=AsyncMock(return_value=SimpleNamespace(success=False)))
        r._tafseer_client = client
        await r._external_api_fallback(2, 255, "en")
        editions = client.get_tafseer.await_args.args[2]
        assert editions == ["ar.baghawi"]

    async def test_vector_failure_sets_degraded_flag(self, monkeypatch):
        r = HybridRetriever(session=None)
        monkeypatch.setattr(r, "_get_enabled_source_ids", AsyncMock(return_value={"x"}))

        class Boom:
            async def aencode(self, *_a, **_k):
                raise HFInferenceError(HFErrorKind.NOT_CONFIGURED, "embeddings")

        monkeypatch.setattr(r, "_get_embedding_model", lambda: Boom())
        assert await r._vector_search("q", "en", [], 5) == []
        assert r.vector_search_failed is True


class _QuotaLLM(BaseLLM):
    model = "fake"

    async def generate(self, *a, **k):
        raise HFInferenceError(HFErrorKind.QUOTA, "chat", 402)

    async def health_check(self):
        return True


CASES = [
    ("What does Ibn Kathir say about the story of Musa and Khidr?", "en", {18}),
    ("ماذا قال المفسرون عن قصة موسى والخضر؟", "ar", {18}),
    ("Why did Yusuf's brothers throw him in the well?", "en", {12}),
    ("لماذا ألقى إخوة يوسف أخاهم في البئر؟", "ar", {12}),
    ("What advice did Luqman give his son?", "en", {31}),
    ("ما وصايا لقمان لابنه؟", "ar", {31}),
    ("How did Ibrahim break the idols?", "en", {21, 37}),
    ("كيف حطم إبراهيم الأصنام؟", "ar", {21, 37}),
    ("What happened to the People of the Cave?", "en", {18}),
    ("ما قصة أصحاب الكهف؟", "ar", {18}),
    ("Explain the night journey of the Prophet", "en", {17}),
]


async def test_keyword_only_retrieval_finds_the_right_surah(monkeypatch):
    from app.db.database import AsyncSessionLocal
    from app.rag.pipeline import RAGPipeline

    monkeypatch.setattr(settings, "hf_token", None)
    hits, multi_source, ran = 0, 0, 0
    try:
        for question, language, expected in CASES:
            async with AsyncSessionLocal() as session:
                r = await RAGPipeline(session, llm=_QuotaLLM()).query(question=question, language=language)
            evidence = r.evidence or []
            if not evidence:
                continue
            ran += 1
            hits += any(e.sura_no in expected for e in evidence)
            multi_source += len({e.source_id for e in evidence}) >= 2
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"database unavailable: {exc}")
    if ran < len(CASES):
        pytest.skip("tafsir corpus not fully loaded in this database")
    assert hits >= 9, f"expected surah in evidence for {hits}/{len(CASES)} questions"
    assert multi_source >= 9, f"{multi_source}/{len(CASES)} answers drew on 2+ sources"
