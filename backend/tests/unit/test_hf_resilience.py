"""
Hugging Face resilience (no network, no HF credit):

- quota / auth failures open a cooldown: the next call fails fast with no
  HTTP request;
- the blocking cross-encoder call never freezes the event loop;
- request-path timeouts fit inside the 60 s route budget;
- an unclosed <think> block is never shown.
"""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from huggingface_hub.errors import HfHubHTTPError
from pydantic import SecretStr

from app.ai import hf_client
from app.ai.hf_client import HFErrorKind, HFInferenceError, classify_exception
from app.core.config import settings
from app.rag import llm_provider
from app.rag.llm_provider import HuggingFaceLLM

FAKE_TOKEN = "hf_unit_test_token_never_real_0000000000"


@pytest.fixture(autouse=True)
def _clean_cooldown(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", SecretStr(FAKE_TOKEN))
    hf_client.reset_cooldown()
    yield
    hf_client.reset_cooldown()


def _http_error(status, headers=None):
    request = httpx.Request("POST", "https://router.huggingface.co/v1/chat/completions")
    return HfHubHTTPError(f"{status}", response=httpx.Response(status, request=request, headers=headers or {}))


class _Client:
    def __init__(self, outcome, calls):
        self.outcome, self.calls = outcome, calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _router(monkeypatch, outcome):
    calls = []

    def factory(async_=True):
        hf_client.require_hf_token("chat")  # the real client resolves the token first
        return _Client(outcome, calls)

    monkeypatch.setattr(llm_provider, "router_chat_client", factory)
    return calls


class TestCooldown:
    @pytest.mark.parametrize("status,kind", [(429, HFErrorKind.QUOTA), (402, HFErrorKind.QUOTA),
                                             (401, HFErrorKind.AUTH), (403, HFErrorKind.FORBIDDEN)])
    def test_failure_short_circuits_the_next_call(self, monkeypatch, status, kind):
        calls = _router(monkeypatch, _http_error(status))
        llm = HuggingFaceLLM()
        for _ in range(3):
            with pytest.raises(HFInferenceError) as exc:
                asyncio.run(llm.generate("SYS", "USER"))
            assert exc.value.kind == kind
        assert len(calls) == 1  # only the first request reached HF
        state = hf_client.hf_cooldown_state()
        assert state["active"] and state["kind"] == kind.value and state["seconds_remaining"] > 0

    def test_retry_after_header_sets_the_quota_window(self):
        classify_exception(_http_error(429, {"Retry-After": "7"}), "chat")
        assert 0 < hf_client.hf_cooldown_state()["seconds_remaining"] <= 7

    def test_auth_cooldown_is_longer_than_quota(self):
        classify_exception(_http_error(401), "embeddings")
        assert hf_client.hf_cooldown_state()["seconds_remaining"] > 60

    def test_transient_errors_do_not_open_a_cooldown(self):
        for status in (500, 503, 404, 400):
            classify_exception(_http_error(status), "chat")
        assert hf_client.hf_cooldown_state() == {"active": False, "kind": None, "seconds_remaining": 0}

    def test_cooldown_expires(self, monkeypatch):
        classify_exception(_http_error(429, {"Retry-After": "1"}), "chat")
        now = time.monotonic()
        monkeypatch.setattr(hf_client.time, "monotonic", lambda: now + 2)
        assert hf_client.require_hf_token("chat") == FAKE_TOKEN

    def test_missing_token_still_reports_not_configured(self, monkeypatch):
        classify_exception(_http_error(429), "chat")
        monkeypatch.setattr(settings, "hf_token", None)
        with pytest.raises(HFInferenceError) as exc:
            hf_client.require_hf_token("chat")
        assert exc.value.kind == HFErrorKind.NOT_CONFIGURED


class TestThinkBlock:
    def test_unclosed_think_block_is_malformed(self, monkeypatch):
        out = SimpleNamespace(
            model="m", usage=None,
            choices=[SimpleNamespace(message=SimpleNamespace(content="<think>private reasoning"),
                                     finish_reason="length")],
        )
        _router(monkeypatch, out)
        with pytest.raises(HFInferenceError) as exc:
            asyncio.run(HuggingFaceLLM().generate("SYS", "USER"))
        assert exc.value.kind == HFErrorKind.MALFORMED

    def test_closed_think_block_is_stripped(self, monkeypatch):
        out = SimpleNamespace(
            model="m", usage=None,
            choices=[SimpleNamespace(message=SimpleNamespace(content="<think>x</think>Answer"),
                                     finish_reason="stop")],
        )
        _router(monkeypatch, out)
        assert asyncio.run(HuggingFaceLLM().generate("SYS", "USER")).content == "Answer"


class TestTimeoutBudget:
    def test_request_path_budgets_fit_the_route_timeout(self):
        total = (settings.hf_embedding_timeout_seconds + settings.hf_rerank_timeout_seconds
                 + settings.hf_chat_timeout_seconds)
        assert total <= 60.0

    def test_chat_uses_chat_budget(self):
        assert HuggingFaceLLM().timeout <= settings.hf_chat_timeout_seconds

    def test_request_path_embeddings_single_attempt_short_timeout(self, monkeypatch):
        from app.ai import embeddings as emb

        monkeypatch.setattr(emb, "_default_model", None)
        model = emb.get_embedding_model()
        assert model.max_attempts == 1 and model.timeout == settings.hf_embedding_timeout_seconds
        assert emb.HFEmbeddingModel().max_attempts == emb.MAX_ATTEMPTS  # batch default unchanged

    def test_rerank_request_uses_rerank_budget(self, monkeypatch):
        from app.rag import reranker

        seen = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            seen["timeout"] = timeout
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: [])

        monkeypatch.setattr(httpx, "post", fake_post)
        reranker._post_pairs("m", [])
        assert seen["timeout"] == settings.hf_rerank_timeout_seconds


async def test_slow_rerank_does_not_block_the_event_loop(monkeypatch):
    """A 2 s cross-encoder call must leave other requests on the worker responsive."""
    from app.rag import reranker
    from app.rag.retrieval import HybridRetriever
    from app.rag.types import RetrievedChunk

    def slow_post(model, payload):
        time.sleep(2)
        return [[{"label": "LABEL_0", "score": 0.5}] for _ in payload]

    monkeypatch.setattr(reranker, "_post_pairs", slow_post)
    chunk = RetrievedChunk(chunk_id="c1", source_id="ibn_kathir_en", source_name="Ibn Kathir",
                           source_name_ar="ابن كثير", verse_reference="2:255", sura_no=2, aya_start=255,
                           aya_end=255, content="TEST-EVIDENCE", relevance_score=0.5)
    r = HybridRetriever(session=None)
    r._thematic_verse_lookup = AsyncMock(return_value=[])
    r._story_lookup = AsyncMock(return_value=[])
    r._vector_search = AsyncMock(return_value=[chunk])
    r._keyword_search = AsyncMock(return_value=[])

    task = asyncio.create_task(r.retrieve("patience in hardship", "en", top_k=5))
    await asyncio.sleep(0.05)  # let retrieval reach the rerank call
    start = time.perf_counter()
    await asyncio.sleep(0.01)
    assert time.perf_counter() - start < 0.2, "event loop was blocked by the rerank call"
    assert await task


def test_emotion_keyword_only_path_never_calls_hf(monkeypatch):
    from app.services import emotion_classifier as ec

    def boom(self, text):
        raise AssertionError("zero-shot must not be called")

    monkeypatch.setattr(ec.NLIEmotionClassifier, "_zero_shot", boom)
    assert isinstance(ec.classify_keywords_only("I feel anxious and worried"), str)
