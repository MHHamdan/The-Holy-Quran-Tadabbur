"""
R2-A integration hardening: limiter wiring, log privacy, HF cooldown in
/health/rag, grammar provenance, therapy single HF call, withheld theme claims
and the dangling story-evidence cleanup migration.
"""
import ast
import importlib.util
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import rate_limit
from app.main import app

BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND.parent


@pytest.fixture
def client():
    rate_limit.reset_all_limiters()
    with TestClient(app) as c:
        yield c
    rate_limit.reset_all_limiters()


# ---------------------------------------------------------------------------
# Rate limiters use the shared helper (no X-Forwarded-For, no IP in logs)
# ---------------------------------------------------------------------------

def test_duas_limiter_is_named_and_logs_no_ip(client, caplog, monkeypatch):
    from app.api.routes import duas

    assert isinstance(duas._duas_limiter, rate_limit.InMemoryRateLimiter)
    assert duas._duas_limiter.name == "duas"
    monkeypatch.setattr(duas._duas_limiter, "is_allowed", lambda ip: (False, 0))
    with caplog.at_level(logging.WARNING):
        r = client.get("/api/v1/duas")
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    assert "testclient" not in caplog.text and "IP" not in caplog.text
    assert "Duas rate limit exceeded" in caplog.text


def test_resolve_limiter_ignores_forwarded_for(monkeypatch):
    from app.api.routes import quran

    lim = quran._resolve_rate_limiter
    assert isinstance(lim, rate_limit.InMemoryRateLimiter) and lim.name == "resolve"
    seen = []
    monkeypatch.setattr(lim, "is_allowed", lambda ip: (seen.append(ip), (False, 0))[1])
    with TestClient(app) as c:
        r = c.get(
            "/api/v1/quran/resolve",
            params={"text": "بسم"},
            headers={"X-Forwarded-For": "203.0.113.9"},
        )
    assert r.status_code == 429
    assert seen and "203.0.113.9" not in seen


def test_tasmee_uses_app_wide_stt_limiter():
    from fastapi.routing import APIRoute

    from app.api.routes import tasmee

    assert not hasattr(tasmee, "_tasmee_limiter")
    for path in ("/api/v1/tasmee/sessions", "/api/v1/tasmee/transcribe"):
        route = next(
            r for r in app.routes
            if isinstance(r, APIRoute) and r.path == path and "POST" in r.methods
        )
        names = {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}
        assert "stt_rate_limit" in names, path
    assert tasmee.MAX_UPLOAD_BYTES == 5 * 1024 * 1024


def test_tasmee_websocket_rate_limited_by_stt_budget(client, monkeypatch):
    from starlette.websockets import WebSocketDisconnect

    monkeypatch.setattr(rate_limit._stt_limiter, "is_allowed", lambda ip: (False, 0))
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/api/v1/tasmee/ws/00000000-0000-4000-8000-000000000000"
        ) as ws:
            ws.receive_json()
    assert exc.value.code == 4029


def test_dead_anonymous_atlas_writes_removed_and_miracle_feedback_limited():
    from fastapi.routing import APIRoute

    posts = {
        r.path: r for r in app.routes
        if isinstance(r, APIRoute) and "POST" in r.methods
    }
    for gone in (
        "/api/v1/quran/atlas/feedback/{story_id}",
        "/api/v1/quran/atlas/user/journey",
        "/api/v1/quran/atlas/stories/{story_id}/flag",
    ):
        assert gone not in posts, gone
    deps = {getattr(d.call, "__name__", "") for d in posts["/api/v1/quran/miracles/feedback"].dependant.dependencies}
    assert "feedback_rate_limit" in deps


@pytest.mark.asyncio
async def test_check_counts_without_raising():
    lim = rate_limit.InMemoryRateLimiter(max_requests=1, window_seconds=60, name="t_check")

    class Conn:
        client = type("C", (), {"host": "10.0.0.1"})()

    assert await rate_limit.check(lim, Conn(), "T") is True
    assert await rate_limit.check(lim, Conn(), "T") is False


# ---------------------------------------------------------------------------
# No raw user text in application logs
# ---------------------------------------------------------------------------

_USER_TEXT_NAMES = {
    "query", "question", "message", "user_message", "transcript", "user_query",
    "raw_query", "search_query", "original_query", "full_text",
}
_SAFE_WRAPPERS = {"len", "query_fingerprint", "type", "bool", "_get_cache_key", "hash"}
_LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical"}
# file -> why its interpolation is not user text
_ALLOWED = {
    "app/core/observability.py": "'message' is the log message itself",
    "app/services/cache_warmer.py": "warms a curated, operator-defined question list",
}


def _refs(node):
    if isinstance(node, ast.Call):
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
        if name in _SAFE_WRAPPERS:
            return
    if isinstance(node, ast.Name) and node.id in _USER_TEXT_NAMES:
        yield node.id
        return
    if isinstance(node, ast.Attribute) and node.attr in _USER_TEXT_NAMES:
        yield node.attr
        return
    for child in ast.iter_child_nodes(node):
        yield from _refs(child)


def test_no_logger_call_interpolates_user_text():
    offenders = []
    for path in sorted((BACKEND / "app").rglob("*.py")):
        rel = path.relative_to(BACKEND).as_posix()
        if rel in _ALLOWED:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr not in _LOG_METHODS or "log" not in ast.unparse(node.func.value).lower():
                continue
            args = list(node.args) + [k.value for k in node.keywords]
            if any(True for a in args for _ in _refs(a)):
                offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, "logger calls with raw user text: " + ", ".join(offenders)


# ---------------------------------------------------------------------------
# /health/rag exposes the HF cooldown
# ---------------------------------------------------------------------------

def test_health_rag_reports_hf_cooldown(client, monkeypatch):
    from app.ai import hf_client
    from app.api.routes import health

    monkeypatch.setattr(health, "llm_configured", lambda: True)
    hf_client.reset_cooldown()
    try:
        r = client.get("/health/rag")
        assert r.status_code == 200
        llm = r.json()["checks"]["llm_api"]
        assert llm["cooldown"] == {"active": False, "kind": None, "seconds_remaining": 0}

        hf_client.record_failure(hf_client.HFInferenceError(hf_client.HFErrorKind.QUOTA, "chat"))
        body = client.get("/health/rag").json()
        llm = body["checks"]["llm_api"]
        assert llm["cooldown"]["active"] is True
        assert llm["cooldown"]["kind"] == "quota"
        assert llm["status"] == "warn" and body["status"] == "degraded"
        assert "token" not in json.dumps(llm).lower()
    finally:
        hf_client.reset_cooldown()


# ---------------------------------------------------------------------------
# Therapy classification: one zero-shot call at most
# ---------------------------------------------------------------------------

def test_therapy_keyword_fallback_makes_no_second_hf_call(monkeypatch):
    from app.api.routes import therapy
    from app.services import emotion_classifier, spiritual_guidance_service

    calls = []

    class FakeClf:
        def classify(self, text):
            calls.append(text)
            return ("", 0.2)

    monkeypatch.setattr(emotion_classifier, "get_classifier", lambda **k: FakeClf())
    monkeypatch.setattr(
        spiritual_guidance_service, "classify_emotion",
        lambda *a, **k: pytest.fail("classify_emotion would repeat the zero-shot call"),
    )
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "emotion_classifier_enabled", True, raising=False)

    emotion, conf = therapy._classify_with_confidence("I feel so anxious and worried today")
    assert conf == 0.0 and emotion
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# Grammar analysis reports where the analysis came from
# ---------------------------------------------------------------------------

def test_grammar_analyze_exposes_source(client, monkeypatch):
    from app.api.routes import quran
    from app.services import grammatical_analyzer as ga

    class FakeAnalyzer:
        async def analyze_word(self, word, verse_text, verse_reference):
            return ga.GrammaticalAnalyzer._default_analysis(
                None, word, verse_text, verse_reference, ("تعذر التحليل", "Analysis unavailable")
            )

        async def close(self):
            pass

    monkeypatch.setattr(quran, "GrammaticalAnalyzer", FakeAnalyzer)
    r = client.post(
        "/api/v1/quran/search/grammar/analyze",
        params={"word": "الحمد", "sura_no": 1, "aya_no": 2},
    )
    if r.status_code == 404:
        pytest.skip("quran_verses not seeded")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "unavailable"
    assert body["is_ai_generated"] is False


def test_grammar_analyze_is_rate_limited():
    from fastapi.routing import APIRoute

    route = next(
        r for r in app.routes
        if isinstance(r, APIRoute) and r.path == "/api/v1/quran/search/grammar/analyze"
    )
    assert "rag_rate_limit" in {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}


# ---------------------------------------------------------------------------
# Withheld theme claims and the owner review queue
# ---------------------------------------------------------------------------

_CLAIMS = ("ثلث القرآن", "one-third", "أعظم آية", "greatest verse")
_WITHHELD = ("theme_tawheed:112:1-4", "theme_tawheed:2:255")


def test_theme_seed_carries_no_unsourced_hadith_claims():
    raw = (BACKEND / "app" / "data" / "themes" / "quranic_themes.json").read_text(encoding="utf-8")
    for phrase in _CLAIMS:
        assert phrase.lower() not in raw.lower(), phrase
    segs = {s["id"]: s for s in json.loads(raw)["segments"]}
    for sid in _WITHHELD:
        seg = segs[sid]
        assert seg["summary_ar"] == "" and seg["summary_en"] == ""
        assert seg["review_status"] == "withheld_owner_review"
        # verse reference and the tafsir chunk reference are kept
        assert seg["sura_no"] and seg["ayah_start"]
        assert seg["evidence_sources"] and all("snippet" not in e for e in seg["evidence_sources"])


def test_owner_review_queue_lists_withheld_claims_and_plan_items():
    queue = json.loads((ROOT / "data" / "review" / "owner_review_queue.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in queue["items"]]
    for sid in _WITHHELD:
        assert sid in ids
    assert len(ids) == len(set(ids))
    # 17 plan owner_review items; themes-mostly-empty is split into the two
    # withheld segment ids.
    assert len(ids) >= 18
    for item in queue["items"]:
        assert item["reason"] and item["current_handling"] and item["decision_needed"]


# ---------------------------------------------------------------------------
# Migration: prune story evidence ids whose tafsir chunk was deleted
# ---------------------------------------------------------------------------

def _r2a_migration():
    path = BACKEND / "alembic" / "versions" / "r2a1b2c3d4e5_prune_dangling_story_evidence.py"
    spec = importlib.util.spec_from_file_location("r2a_migration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.asyncio
async def test_prune_migration_is_idempotent_and_leaves_no_dangling_ids():
    from app.db import database

    mod = _r2a_migration()
    assert mod.revision == "r2a1b2c3d4e5"
    async with database.AsyncSessionLocal() as session:
        try:
            await session.execute(text("SELECT 1 FROM story_segments LIMIT 1"))
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        try:
            for sql in mod.UPGRADE_SQL:
                await session.execute(text(sql))
            for sql in mod.UPGRADE_SQL:
                again = await session.execute(text(sql))
                assert again.rowcount == 0
            dangling = (await session.execute(text(
                "SELECT count(*) FROM story_segments s, unnest(s.evidence_chunk_ids) x "
                "WHERE NOT EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = x)"
            ))).scalar()
            assert dangling == 0
        finally:
            await session.rollback()
