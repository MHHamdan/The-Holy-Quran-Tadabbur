"""
Maintenance, metrics and schema endpoints are not anonymous attack surface
(WS1: backend-public-dos-maintenance-endpoints, security-info-disclosure-
openapi-perf, backend-metrics-route-shadowed). Nothing here writes to the DB.
"""
import hashlib
from unittest.mock import patch

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import _feedback_limiter, feedback_rate_limit
from app.main import app

KEY = "ws1-maintenance-test-key"
KEY_HASH = hashlib.sha256(KEY.encode()).hexdigest()


@pytest.fixture
def client():
    return TestClient(app)


def _with_key():
    return patch("app.core.admin_auth._get_configured_key_hash", return_value=KEY_HASH)


# --- performance router ------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/v1/performance/metrics", "/api/v1/performance/db-pool",
                                  "/api/v1/performance/services"])
def test_performance_reads_need_admin_key(client, path):
    with _with_key():
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"X-Admin-API-Key": "wrong"}).status_code == 403


@pytest.mark.parametrize("iterations", [-1, 0, 101, 100000000])
def test_benchmark_iterations_are_bounded(client, iterations):
    url = f"/api/v1/performance/benchmark/similarity/2/255?iterations={iterations}"
    with _with_key():
        anon = client.post(url)
        assert anon.status_code in (401, 422)
        authed = client.post(url, headers={"X-Admin-API-Key": KEY})
        assert authed.status_code == 422


def test_performance_router_not_mounted_in_production():
    import app.main as main_mod

    src = open(main_mod.__file__, encoding="utf-8").read()
    assert 'if settings.environment.lower() not in ("production", "prod"):\n    app.include_router(performance.router' in src


# --- OpenAPI schema ----------------------------------------------------------

def test_openapi_json_is_hidden_without_debug(client):
    if settings.debug:
        pytest.skip("DEBUG=true in this environment")
    assert app.openapi_url is None
    assert client.get("/openapi.json").status_code == 404
    # The schema itself still builds for tests and tooling.
    assert "/api/v1/rag/ask" in app.openapi()["paths"]


# --- metrics -----------------------------------------------------------------

def test_metrics_is_registered_once():
    paths = [r.path for r in app.routes if isinstance(r, APIRoute) and r.path == "/metrics"]
    assert paths == ["/metrics"]


@pytest.mark.parametrize("path", ["/metrics", "/metrics/summary", "/metrics/app"])
def test_metrics_gated_in_production(client, monkeypatch, path):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("METRICS_SECRET", raising=False)
    assert client.get(path).status_code == 503

    monkeypatch.setenv("METRICS_SECRET", "s3cret-metrics")
    assert client.get(path).status_code == 403
    assert client.get(path, headers={"X-Metrics-Secret": "s3cret-metrics"}).status_code == 200


@pytest.mark.parametrize("path", ["/metrics", "/metrics/summary", "/metrics/app"])
def test_metrics_open_in_development(client, monkeypatch, path):
    monkeypatch.setenv("ENVIRONMENT", "development")
    assert client.get(path).status_code == 200


# --- public flag endpoint ----------------------------------------------------

def _flag(client, **overrides):
    # entity_type is deliberately invalid: the handler rejects it before any
    # write, so the shared dev database is never touched.
    body = {"entity_type": "not-a-type", "entity_id": "x", "flag_type": "accuracy"}
    body.update(overrides)
    return client.post("/api/v1/admin/flag", json=body)


def test_flag_reason_and_snapshot_are_capped(client):
    _feedback_limiter.reset()
    assert _flag(client, flag_reason="x" * 1001).status_code == 422
    assert _flag(client, context_snapshot={"blob": "y" * 9000}).status_code == 422
    assert _flag(client, context_snapshot={"blob": "y" * 100}).status_code == 400
    _feedback_limiter.reset()


@pytest.fixture
def real_feedback_limit():
    # test_feedback_phase_g installs a module-level no-op override of
    # feedback_rate_limit that outlives that module; use the real limiter here.
    saved = app.dependency_overrides.pop(feedback_rate_limit, None)
    yield
    if saved is not None:
        app.dependency_overrides[feedback_rate_limit] = saved


def test_flag_is_rate_limited(client, real_feedback_limit):
    _feedback_limiter.reset()
    codes = [_flag(client).status_code for _ in range(11)]
    assert codes[:10] == [400] * 10
    assert codes[10] == 429
    _feedback_limiter.reset()
