"""The OpenAPI schema (/docs, /openapi.json) must always build.

Regression: an unresolved forward reference (`request: "Request"`) in the
/quran/resolve route made schema generation fail with HTTP 500, and the
request object was never injected, so per-IP rate limiting was a no-op.
"""
import inspect

from fastapi import Request

from app.main import app


def test_openapi_schema_builds():
    app.openapi_schema = None
    schema = app.openapi()
    assert "/api/v1/quran/resolve" in schema["paths"]
    assert "/api/v1/rag/ask" in schema["paths"]


def test_resolve_route_receives_request_object():
    from app.api.routes.quran import resolve_verse_text

    assert inspect.signature(resolve_verse_text).parameters["request"].annotation is Request


def test_resolve_rate_limit_returns_429_not_500():
    """Regression: ErrorCode.RATE_LIMITED did not exist, so the limiter raised 500."""
    from fastapi.testclient import TestClient
    from app.api.routes import quran

    quran._resolve_rate_limiter.reset() if hasattr(quran._resolve_rate_limiter, "reset") else None
    original = quran._resolve_rate_limiter.is_allowed
    quran._resolve_rate_limiter.is_allowed = lambda ip: (False, 0)
    try:
        r = TestClient(app).get("/api/v1/quran/resolve", params={"text": "بسم"})
    finally:
        quran._resolve_rate_limiter.is_allowed = original
    assert r.status_code == 429


def test_every_error_code_used_with_core_enums_exists():
    """Regression: routes referenced ErrorCode members that did not exist, turning 404/429 into 500."""
    import ast
    import pathlib

    from app.core import errors, responses

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    missing = []
    for path in root.rglob("*.py"):
        if path.name == "grounded_ask_service.py":  # defines its own ErrorCode enum
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "ErrorCode"):
                if not (hasattr(responses.ErrorCode, node.attr) or hasattr(errors.ErrorCode, node.attr)):
                    missing.append(f"{path.relative_to(root)}:{node.lineno} {node.attr}")
    assert not missing, missing
