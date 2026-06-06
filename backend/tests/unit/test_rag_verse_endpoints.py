"""
Tests for Phase Y — grounded per-verse Ask AI endpoints.

These tests stub `RAGPipeline.query` so they don't hit the LLM. They
verify the shape of the response (citations, status, safe-refusal,
suggested questions), the surah/ayah validation, and the suggested-
questions endpoint contract.
"""
from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.types import GroundedResponse, Citation


# ---------------------------------------------------------------------------
# Stub responses (kept tiny — we only care about shape)
# ---------------------------------------------------------------------------


def _grounded_with_citations() -> GroundedResponse:
    return GroundedResponse(
        answer="This is a grounded answer about the verse.",
        citations=[
            Citation(
                chunk_id="chunk_1",
                source_id="ar.muyassar",
                source_name="Al-Muyassar",
                source_name_ar="الميسر",
                verse_reference="1:2",
                excerpt="Excerpt 1",
                relevance_score=0.9,
                author="Saudi Scholars",
            )
        ],
        confidence=0.85,
        confidence_level="high",
        scholarly_consensus="agreed",
        warnings=[],
        related_queries=[],
        intent="verse_meaning",
        processing_time_ms=123,
        status="answered",
        answer_language="en",
        session_id=None,
        related_verses=[],
        tafsir_by_source={},
        follow_up_suggestions=[],
        api_version="v1",
    )


def _grounded_refusal() -> GroundedResponse:
    return GroundedResponse(
        answer="No verified source available.",
        citations=[],
        confidence=0.0,
        scholarly_consensus=None,
        warnings=["No relevant sources found"],
        related_queries=[],
        intent="verse_meaning",
        processing_time_ms=12,
        status="no_verified_source",
        answer_language="ar",
        session_id=None,
        related_verses=[],
        tafsir_by_source={},
        follow_up_suggestions=[],
        api_version="v1",
    )


# ---------------------------------------------------------------------------
# Pipeline stub
# ---------------------------------------------------------------------------


class _StubPipeline:
    def __init__(self, _session, response: GroundedResponse):
        self._response = response

    async def query(self, **_kwargs) -> GroundedResponse:
        return self._response


@pytest.fixture
def patched_pipeline(monkeypatch):
    holder: Dict[str, Any] = {"response": _grounded_with_citations()}

    def _factory(session):
        return _StubPipeline(session, holder["response"])

    monkeypatch.setattr("app.api.routes.rag_verse.RAGPipeline", _factory)
    return holder


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# /verse/ask
# ---------------------------------------------------------------------------


def test_verse_ask_returns_grounded_response(patched_pipeline, client):
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={
            "surah": 1,
            "ayah_start": 2,
            "question": "What does this verse mean?",
            "language": "en",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"]
    assert len(body["citations"]) == 1
    assert body["status"] == "answered"
    assert body["verse"]["surah"] == 1
    assert body["verse"]["ayah_start"] == 2
    assert body["verse"]["reference"] == "1:2"


def test_verse_ask_safe_refusal_attaches_suggestions(patched_pipeline, client):
    patched_pipeline["response"] = _grounded_refusal()
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={
            "surah": 1,
            "ayah_start": 2,
            "question": "Unanswerable question?",
            "language": "ar",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "no_verified_source"
    assert body["citations"] == []
    assert isinstance(body["suggested_questions"], list)
    assert len(body["suggested_questions"]) == 3


def test_verse_ask_validates_surah_lower_bound(client):
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={"surah": 0, "ayah_start": 1, "question": "Why?", "language": "en"},
    )
    assert r.status_code == 422  # Pydantic ge=1 kicks in first


def test_verse_ask_validates_surah_upper_bound(client):
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={"surah": 999, "ayah_start": 1, "question": "Why?", "language": "en"},
    )
    assert r.status_code == 422


def test_verse_ask_rejects_short_question(client):
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={"surah": 1, "ayah_start": 1, "question": "a", "language": "en"},
    )
    assert r.status_code == 422


def test_verse_ask_rejects_invalid_language(client):
    r = client.post(
        "/api/v1/rag/verse/ask",
        json={"surah": 1, "ayah_start": 1, "question": "Test query", "language": "de"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# /verse/summarize
# ---------------------------------------------------------------------------


def test_verse_summarize_returns_citations(patched_pipeline, client):
    r = client.post(
        "/api/v1/rag/verse/summarize",
        json={"surah": 1, "ayah_start": 2, "language": "ar"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["answer"]
    assert len(body["citations"]) == 1
    assert body["verse"]["reference"] == "1:2"


def test_verse_summarize_safe_refusal(patched_pipeline, client):
    patched_pipeline["response"] = _grounded_refusal()
    r = client.post(
        "/api/v1/rag/verse/summarize",
        json={"surah": 1, "ayah_start": 2, "language": "ar"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "no_verified_source"
    assert body["suggested_questions"]


# ---------------------------------------------------------------------------
# /verse/explain-word
# ---------------------------------------------------------------------------


def test_verse_explain_word_includes_word_field(patched_pipeline, client):
    r = client.post(
        "/api/v1/rag/verse/explain-word",
        json={
            "surah": 2,
            "ayah_start": 30,
            "word": "خليفة",
            "language": "ar",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["word"] == "خليفة"
    assert body["verse"]["surah"] == 2
    assert body["verse"]["ayah_start"] == 30


def test_verse_explain_word_rejects_empty_word(client):
    r = client.post(
        "/api/v1/rag/verse/explain-word",
        json={"surah": 1, "ayah_start": 1, "word": "", "language": "ar"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# /verse/suggested-questions
# ---------------------------------------------------------------------------


def test_suggested_questions_ar_returns_three(client):
    r = client.get(
        "/api/v1/rag/verse/suggested-questions",
        params={"surah": 1, "ayah_start": 2, "language": "ar"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "ar"
    assert len(body["questions"]) == 3
    texts: List[str] = [q["text"] for q in body["questions"]]
    # Must contain the three canonical templates
    assert "ما سبب نزول هذه الآية؟" in texts
    assert "ما الدروس والعبر المستفادة من هذه الآية؟" in texts
    assert "ما علاقة هذه الآية بما قبلها وما بعدها؟" in texts


def test_suggested_questions_en_returns_three(client):
    r = client.get(
        "/api/v1/rag/verse/suggested-questions",
        params={"surah": 2, "ayah_start": 30, "language": "en"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "en"
    assert len(body["questions"]) == 3
    for q in body["questions"]:
        assert q["language"] == "en"
        assert q["text"]


def test_suggested_questions_invalid_surah(client):
    r = client.get(
        "/api/v1/rag/verse/suggested-questions",
        params={"surah": 200, "ayah_start": 1, "language": "ar"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Anchored-query composition (smoke)
# ---------------------------------------------------------------------------


def test_anchored_query_uses_verse_reference():
    from app.api.routes.rag_verse import _compose_anchored_query

    ar = _compose_anchored_query(
        surah=2, ayah_start=30, ayah_end=None, question="ما المعنى؟", language="ar"
    )
    assert "2:30" in ar
    assert "ما المعنى؟" in ar

    en = _compose_anchored_query(
        surah=2, ayah_start=30, ayah_end=33, question="What is the meaning?", language="en"
    )
    assert "2:30-33" in en
    assert "What is the meaning?" in en
