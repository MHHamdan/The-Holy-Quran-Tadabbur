"""
LLM-backed routes are rate limited and fail with a bilingual envelope
(WS1: security-unmetered-llm-stt-cost, hf-quiz-error-envelope,
hf-grammar-search-error-leak). No test here calls Hugging Face.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.api.routes import quiz
from app.core.rate_limit import _rag_limiter, rag_rate_limit
from app.main import app


class _FailingLLM:
    def __init__(self, kind):
        self.kind = kind

    async def generate(self, **kwargs):
        raise HFInferenceError(self.kind, "chat")


@pytest.fixture
def client(monkeypatch):
    async def _ctx(session, surah, lang, max_chars=quiz._MAX_CONTEXT_CHARS):
        return "سياق تفسير للاختبار", 1

    monkeypatch.setattr(quiz, "_fetch_surah_context", _ctx)
    _rag_limiter.reset()
    yield TestClient(app)
    _rag_limiter.reset()


def _route_dependencies(path: str, method: str):
    for r in app.routes:
        if getattr(r, "path", None) == path and method in getattr(r, "methods", set()):
            return [d.call for d in r.dependant.dependencies]
    raise AssertionError(f"route {method} {path} not found")


@pytest.mark.parametrize("path,method", [
    ("/api/v1/quiz/generate-questions", "POST"),
    ("/api/v1/grammar/analyze", "POST"),
    ("/api/v1/grammar/ayah/{sura_ayah}", "GET"),
])
def test_llm_routes_carry_the_rag_rate_limit(path, method):
    assert rag_rate_limit in _route_dependencies(path, method)


def test_quiz_generation_is_limited_to_20_per_minute(client, monkeypatch):
    monkeypatch.setattr(quiz, "get_llm", lambda: _FailingLLM(HFErrorKind.NOT_CONFIGURED))
    codes = [
        client.post("/api/v1/quiz/generate-questions", json={"surah": 1}).status_code
        for _ in range(21)
    ]
    assert codes[:20] == [503] * 20
    assert codes[20] == 429


def test_quiz_outage_is_bilingual_503(client, monkeypatch):
    monkeypatch.setattr(quiz, "get_llm", lambda: _FailingLLM(HFErrorKind.NOT_CONFIGURED))
    r = client.post("/api/v1/quiz/generate-questions", json={"surah": 1})
    assert r.status_code == 503
    body = r.json()
    assert body["error"]["code"] == "service_unavailable"
    assert body["message_ar"] and body["message_en"]
    assert "not_configured" not in r.text


def test_quiz_quota_is_429_ai_quota_exceeded(client, monkeypatch):
    monkeypatch.setattr(quiz, "get_llm", lambda: _FailingLLM(HFErrorKind.QUOTA))
    r = client.post("/api/v1/quiz/generate-questions", json={"surah": 1})
    assert r.status_code == 429
    body = r.json()
    assert body["error"]["code"] == "ai_quota_exceeded"
    assert body["message_ar"] and body["message_en"]


def test_quiz_missing_context_is_bilingual_503(client, monkeypatch):
    async def _empty(session, surah, lang, max_chars=quiz._MAX_CONTEXT_CHARS):
        return "", 0

    monkeypatch.setattr(quiz, "_fetch_surah_context", _empty)
    r = client.post("/api/v1/quiz/generate-questions", json={"surah": 2})
    assert r.status_code == 503
    assert r.json()["message_ar"] and r.json()["message_en"]


def test_grammar_analyze_text_is_length_capped(client):
    r = client.post("/api/v1/grammar/analyze", json={"text": "ب" * 501})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Grammatical analyzer notes never leak internal error kinds
# ---------------------------------------------------------------------------

def _analyzer_with(llm):
    from app.services.grammatical_analyzer import GrammaticalAnalyzer

    a = GrammaticalAnalyzer.__new__(GrammaticalAnalyzer)
    a.llm = llm
    return a


@pytest.mark.parametrize("kind", list(HFErrorKind))
def test_word_analysis_failure_is_localized(kind):
    analysis = asyncio.run(_analyzer_with(_FailingLLM(kind)).analyze_word("كلمة", "نص", "1:1"))
    assert analysis.source == "unavailable"
    assert kind.value not in analysis.notes_ar and kind.value not in analysis.notes_en
    assert "AI service" not in analysis.notes_ar
    assert analysis.notes_ar == "خدمة التحليل بالذكاء الاصطناعي غير متاحة مؤقتاً."
    assert analysis.notes_en == "AI analysis is temporarily unavailable."


def test_verse_analysis_failure_is_localized():
    v = asyncio.run(_analyzer_with(_FailingLLM(HFErrorKind.NOT_CONFIGURED)).analyze_verse("نص", "1:1", 1, 1))
    assert v.source == "unavailable"
    assert "not_configured" not in v.parsing_notes
    assert v.parsing_notes_en == "AI analysis is temporarily unavailable."


def test_unparseable_model_output_is_not_echoed():
    class _Garbage:
        async def generate(self, **kwargs):
            class R:
                content = "INTERNAL GARBAGE no json"
            return R()

    analysis = asyncio.run(_analyzer_with(_Garbage()).analyze_word("كلمة", "نص", "1:1"))
    assert analysis.source == "unavailable"
    assert "GARBAGE" not in analysis.notes_ar + analysis.notes_en + analysis.raw_response
