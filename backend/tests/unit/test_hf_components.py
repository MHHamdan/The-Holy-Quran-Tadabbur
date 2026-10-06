"""
Mocked tests for the Hugging Face-backed ML components (no network).

Embeddings, reranker and speech-to-text must work against HF and degrade to
their deterministic fallbacks when HF is unavailable.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from pydantic import SecretStr

from app.ai import embeddings as emb
from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.core.config import settings


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setattr(settings, "hf_token", SecretStr("hf_unit_test_token_0000000000000000"))


# ------------------------------------------------------------------ embeddings

class _FakeFeatureClient:
    def __init__(self, dim=1024, fail=None):
        self.dim, self.fail, self.calls = dim, fail, []

    def feature_extraction(self, batch, model=None, truncate=None):
        self.calls.append((list(batch), model, truncate))
        if self.fail:
            raise self.fail
        rng = np.random.default_rng(len(self.calls))
        return rng.normal(size=(len(batch), self.dim)).astype(np.float32)


def test_encode_single_and_batch_are_normalised(token, monkeypatch):
    client = _FakeFeatureClient()
    monkeypatch.setattr(emb, "task_client", lambda task, **kw: client)
    model = emb.HFEmbeddingModel()

    one = model.encode("query: الصبر")
    many = model.encode([f"passage: {i}" for i in range(70)], batch_size=32)

    assert one.shape == (1024,)
    assert many.shape == (70, 1024)
    assert np.allclose(np.linalg.norm(many, axis=1), 1.0, atol=1e-5)
    assert [len(c[0]) for c in client.calls] == [1, 32, 32, 6]  # explicit batch_size=32
    assert all(c[1] == settings.hf_embedding_model and c[2] is True for c in client.calls)


def test_encode_rejects_wrong_dimension(token, monkeypatch):
    monkeypatch.setattr(emb, "task_client", lambda task, **kw: _FakeFeatureClient(dim=384))
    with pytest.raises(HFInferenceError) as info:
        emb.HFEmbeddingModel().encode("x")
    assert info.value.kind == HFErrorKind.MALFORMED  # never mix dimensions in Qdrant


def test_encode_maps_upstream_errors(token, monkeypatch):
    monkeypatch.setattr(emb, "RETRY_BACKOFF_SECONDS", 0)
    client = _FakeFeatureClient(fail=TimeoutError())
    monkeypatch.setattr(emb, "task_client", lambda task, **kw: client)
    with pytest.raises(HFInferenceError) as info:
        emb.HFEmbeddingModel().encode("x")
    assert info.value.kind == HFErrorKind.TIMEOUT
    assert len(client.calls) == emb.MAX_ATTEMPTS  # transient errors retried


def test_encode_does_not_retry_quota(token, monkeypatch):
    import httpx
    from huggingface_hub.errors import HfHubHTTPError

    resp = httpx.Response(402, request=httpx.Request("POST", "https://router.huggingface.co"))
    client = _FakeFeatureClient(fail=HfHubHTTPError("402", response=resp))
    monkeypatch.setattr(emb, "task_client", lambda task, **kw: client)
    with pytest.raises(HFInferenceError) as info:
        emb.HFEmbeddingModel().encode("x")
    assert info.value.kind == HFErrorKind.QUOTA and len(client.calls) == 1


def test_encode_without_token_is_not_configured():
    with pytest.raises(HFInferenceError) as info:
        emb.HFEmbeddingModel().encode("x")
    assert info.value.kind == HFErrorKind.NOT_CONFIGURED


async def test_similarity_service_falls_back_and_clears_cache(token):
    from app.services.semantic_embeddings import SemanticEmbeddingService

    svc = SemanticEmbeddingService()
    await svc.initialize()
    failing = MagicMock()

    async def boom(*a, **k):
        raise HFInferenceError(HFErrorKind.QUOTA, "embeddings")

    failing.aencode = boom
    svc._model = failing
    svc._embedding_cache["stale"] = np.ones(3)

    vec = await svc.compute_embedding("الحمد لله رب العالمين")

    assert svc._model is None                # switched to fallback for the process
    assert "stale" not in svc._embedding_cache
    assert vec.shape == (1024,)              # fallback shares the HF dimension


# -------------------------------------------------------------------- reranker

def _chunk(text, score=0.5):
    return SimpleNamespace(content=text, content_en=None, content_ar=text, relevance_score=score)


def test_parse_rerank_output_shapes():
    from app.rag.reranker import _parse_rerank_output

    wrapped = [[{"label": "LABEL_0", "score": 0.9}, {"label": "LABEL_0", "score": 0.1}]]
    assert _parse_rerank_output(wrapped, 2) == [0.9, 0.1]
    assert _parse_rerank_output([[{"label": "LABEL_0", "score": 0.3}]], 1) == [0.3]
    assert _parse_rerank_output([{"score": 0.4}, {"score": 0.6}], 2) == [0.4, 0.6]
    assert _parse_rerank_output([{"oops": 1}], 1) is None
    assert _parse_rerank_output([], 2) is None


def test_rerank_uses_hf_scores(token):
    from app.rag import reranker

    chunks = [_chunk("الزكاة"), _chunk("الصبر حبس النفس"), _chunk("")]
    with patch.object(reranker, "_post_pairs", return_value=[[{"score": 0.01}, {"score": 0.97}]]):
        ranked, result = reranker.rerank_chunks("ما معنى الصبر", chunks, top_k=2)

    assert result.method == "cross_encoder" and result.reranked
    assert ranked[0].content == "الصبر حبس النفس"
    assert ranked[0].rerank_score == pytest.approx(0.97)
    # Retrieval relevance (the confidence gate's scale) is left untouched.
    assert ranked[0].relevance_score == pytest.approx(0.5)


@pytest.mark.parametrize("failure", [
    HFInferenceError(HFErrorKind.QUOTA, "rerank"),
    TimeoutError(),
    ValueError("garbage"),
])
def test_rerank_falls_back_to_keyword_bm25(token, failure):
    from app.rag import reranker

    chunks = [_chunk("الزكاة ركن", 0.4), _chunk("الصبر حبس النفس على الطاعة", 0.5)]
    with patch.object(reranker, "_post_pairs", side_effect=failure):
        ranked, result = reranker.rerank_chunks("الصبر", chunks, top_k=2)
    assert result.method == "keyword_overlap"
    assert len(ranked) == 2


def test_rerank_without_token_never_calls_hf():
    from app.rag import reranker

    with patch.object(reranker, "_post_pairs") as post:
        _, result = reranker.rerank_chunks("q", [_chunk("a"), _chunk("b")], top_k=1)
    post.assert_not_called()
    assert result.method == "keyword_overlap"
    assert reranker.is_reranker_available()["method"] == "keyword_overlap"


# -------------------------------------------------------------- speech-to-text

class _FakeASR:
    def __init__(self, output=None, fail=None):
        self.output, self.fail, self.calls = output, fail, []

    def automatic_speech_recognition(self, payload, model=None, extra_body=None):
        self.calls.append((payload, model, extra_body))
        if self.fail:
            raise self.fail
        return self.output


def _asr_output(words):
    return SimpleNamespace(
        text=" ".join(w for w, *_ in words),
        chunks=[SimpleNamespace(text=f" {w}", timestamp=[s, e]) for w, s, e in words],
    )


def test_stt_transcribe_builds_words_and_wav(token, monkeypatch):
    from app.stt.providers import huggingface as hfstt

    fake = _FakeASR(_asr_output([("قل", 0.0, 0.36), ("هو", 0.36, 0.64), ("الله", 0.64, 1.32), ("أحد", 1.32, None)]))
    monkeypatch.setattr(hfstt, "task_client", lambda task, **kw: fake)
    audio = np.zeros(16000 * 2, dtype=np.float32)

    result = hfstt.HuggingFaceSTTProvider().transcribe(audio)

    payload, model, extra = fake.calls[0]
    assert payload[:4] == b"RIFF" and payload[8:12] == b"WAVE"
    assert model == settings.hf_stt_model
    assert extra["return_timestamps"] == "word"
    assert extra["generate_kwargs"]["language"] == "arabic"
    words = result.get_all_words()
    assert [w.word for w in words] == ["قل", "هو", "الله", "أحد"]
    assert words[-1].end_time == pytest.approx(2.0)  # open timestamp closed at audio end
    assert result.provider == "huggingface" and result.duration == pytest.approx(2.0)


def test_stt_without_timestamps_spreads_words(token, monkeypatch):
    from app.stt.providers import huggingface as hfstt

    fake = _FakeASR(SimpleNamespace(text="الحمد لله", chunks=None))
    monkeypatch.setattr(hfstt, "task_client", lambda task, **kw: fake)
    result = hfstt.HuggingFaceSTTProvider().transcribe(np.zeros(16000, dtype=np.float32))
    assert [w.word for w in result.get_all_words()] == ["الحمد", "لله"]


def test_stt_silence_gives_no_segments(token, monkeypatch):
    from app.stt.providers import huggingface as hfstt

    monkeypatch.setattr(hfstt, "task_client", lambda task, **kw: _FakeASR(SimpleNamespace(text="", chunks=[])))
    result = hfstt.HuggingFaceSTTProvider().transcribe(np.zeros(8000, dtype=np.float32))
    assert result.segments == [] and result.full_text == ""


def test_stt_errors_are_classified(token, monkeypatch):
    from app.stt.providers import huggingface as hfstt

    monkeypatch.setattr(hfstt, "task_client", lambda task, **kw: _FakeASR(fail=ConnectionError()))
    with pytest.raises(HFInferenceError) as info:
        hfstt.HuggingFaceSTTProvider().transcribe(np.zeros(1600, dtype=np.float32))
    assert info.value.kind == HFErrorKind.NETWORK


def test_stt_load_requires_token():
    from app.stt.providers.huggingface import HuggingFaceSTTProvider

    with pytest.raises(HFInferenceError) as info:
        HuggingFaceSTTProvider().load_model()
    assert info.value.kind == HFErrorKind.NOT_CONFIGURED


def test_stt_factory_defaults_to_huggingface():
    from app.stt import get_stt_provider

    assert get_stt_provider().name == "huggingface"
    with pytest.raises(ValueError):
        get_stt_provider("vosk")
