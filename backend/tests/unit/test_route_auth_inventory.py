"""
Route auth inventory (WS1: backend-public-dos-maintenance-endpoints,
security-unauth-maintenance-endpoints).

Every state-changing route (anything but GET/HEAD/OPTIONS) whose path looks
administrative — admin, update, verify, review, endorse, decide, cache — must
carry an admin dependency somewhere in its dependency tree:

  - app.core.admin_auth.require_admin_api_key   (X-Admin-API-Key)
  - app.core.auth.require_admin                 (Bearer admin token)
  - verify_admin_token in rag.py / kg.py        (X-Admin-Token)

Ordinary user actions that only match the pattern by name are listed in
USER_ACTIONS with the reason they are public.

PENDING lists routes owned by other workstreams (quran.py: WS4, rag.py: WS2)
that still lack an admin dependency. Each is a strict xfail: when the owner
adds the dependency the case XPASSes, the suite fails, and the entry must be
deleted here. The list may only shrink.
"""
import re

import pytest
from fastapi.routing import APIRoute

from app.main import app

SENSITIVE = re.compile(r"admin|update|verify|review|endorse|decide|cache")
ADMIN_DEPENDENCIES = {"require_admin_api_key", "require_admin", "verify_admin_token"}

# (method, path) -> why it is a public user action, not an admin one.
USER_ACTIONS = {
    ("POST", "/api/v1/admin/flag"):
        "readers report a content problem; rate limited (feedback_rate_limit), size-capped",
    ("POST", "/api/v1/quran/memorization/record-review"):
        "a reader's own memorisation review (spaced repetition)",
    ("POST", "/api/v1/quran/learning/review/add"):
        "a reader adds a verse to their own review list",
    ("POST", "/api/v1/quran/learning/review/submit"):
        "a reader submits their own review answer",
    ("POST", "/api/v1/quran/learning/sm2-review"):
        "a reader's own SM-2 review step",
}

# Owned by other workstreams; must gain an admin dependency (see module doc).
PENDING = {
    ("POST", "/api/v1/quran/cache/cleanup"): "WS4",
    ("DELETE", "/api/v1/quran/cache/user/{user_id}"): "WS4",
    ("POST", "/api/v1/quran/annotations/{annotation_id}/review"): "WS4",
    ("POST", "/api/v1/quran/expert/scholars/{scholar_id}/verify"): "WS4",
    ("POST", "/api/v1/quran/expert/peer-review/{annotation_id}"): "WS4",
    ("POST", "/api/v1/quran/expert/endorse/{annotation_id}"): "WS4",
    ("POST", "/api/v1/quran/atlas/stories/{story_id}/update"): "WS4",
    ("DELETE", "/api/v1/quran/atlas/cache"): "WS4",
    ("POST", "/api/v1/quran/miracles/admin/review-feedback"): "WS4",
    ("DELETE", "/api/v1/rag/cache/clear"): "WS2",
}


def _dependency_names(dependant):
    for dep in dependant.dependencies:
        yield getattr(dep.call, "__name__", "")
        yield from _dependency_names(dep)


def _sensitive_routes():
    out = {}
    for route in app.routes:
        if not isinstance(route, APIRoute) or not SENSITIVE.search(route.path):
            continue
        for method in sorted(set(route.methods) - {"GET", "HEAD", "OPTIONS"}):
            out[(method, route.path)] = set(_dependency_names(route.dependant))
    return out


ROUTES = _sensitive_routes()


def _has_admin(key):
    return bool(ROUTES[key] & ADMIN_DEPENDENCIES)


def test_inventory_finds_routes():
    # Guard against the walk silently matching nothing (e.g. nested routers).
    assert len(ROUTES) >= 20
    assert ("POST", "/cache/warm") in ROUTES and _has_admin(("POST", "/cache/warm"))


def test_sensitive_mutations_require_an_admin_dependency():
    missing = [
        f"{m} {p}" for (m, p) in ROUTES
        if (m, p) not in USER_ACTIONS and (m, p) not in PENDING and not _has_admin((m, p))
    ]
    assert not missing, "state-changing admin-looking routes without admin auth: " + ", ".join(missing)


@pytest.mark.parametrize("key", sorted(PENDING), ids=lambda k: f"{k[0]} {k[1]}")
def test_pending_routes_from_other_workstreams(key):
    if key not in ROUTES:
        pytest.fail(f"{key} no longer exists: delete it from PENDING")
    if _has_admin(key):
        pytest.fail(f"{key} now has admin auth ({PENDING[key]} landed): delete it from PENDING")
    pytest.xfail(f"awaiting {PENDING[key]}: add an admin dependency")


def test_user_action_allowlist_is_current():
    stale = [k for k in USER_ACTIONS if k not in ROUTES]
    assert not stale, f"delete removed routes from USER_ACTIONS: {stale}"


def test_public_flag_is_rate_limited():
    assert "feedback_rate_limit" in ROUTES[("POST", "/api/v1/admin/flag")]


def test_performance_router_requires_admin_key():
    perf = [r for r in app.routes if isinstance(r, APIRoute) and r.path.startswith("/api/v1/performance")]
    for route in perf:
        assert "require_admin_api_key" in set(_dependency_names(route.dependant)), route.path
