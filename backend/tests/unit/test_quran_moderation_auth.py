"""
quran.py moderation / cache routes: either removed or gated by X-Admin-API-Key.

Before this change anyone could rewrite story text through
POST /quran/atlas/stories/{id}/update, self-verify as a scholar, approve
annotations, and open the miracles admin dashboard with ?admin_id=admin.
"""
import hashlib
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

TEST_KEY = "ws4-moderation-test-key"
TEST_KEY_HASH = hashlib.sha256(TEST_KEY.encode()).hexdigest()

client = TestClient(app, raise_server_exceptions=False)
Q = "/api/v1/quran"


def _patch_key():
    return patch("app.core.admin_auth._get_configured_key_hash", return_value=TEST_KEY_HASH)


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", f"{Q}/atlas/stories/adam/update"),
        ("post", f"{Q}/atlas/verification/create"),
        ("get", f"{Q}/atlas/verification/queue?admin_id=admin"),
        ("post", f"{Q}/atlas/verification/t1/submit"),
        ("post", f"{Q}/annotations/a1/review"),
        ("post", f"{Q}/annotations/submit"),
        ("post", f"{Q}/expert/scholars/register"),
        ("post", f"{Q}/expert/scholars/s1/verify"),
        ("post", f"{Q}/expert/endorse/a1"),
        ("post", f"{Q}/expert/peer-review/a1"),
    ],
)
def test_removed_moderation_routes_are_gone(method, path):
    r = client.request(method.upper(), path, json={} if method != "get" else None)
    assert r.status_code in (404, 405), (path, r.status_code)


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", f"{Q}/miracles/admin/dashboard?admin_id=admin"),
        ("post", f"{Q}/miracles/admin/review-feedback?admin_id=admin&feedback_id=x&decision=accepted"),
        ("delete", f"{Q}/atlas/cache"),
        ("post", f"{Q}/cache/cleanup"),
        ("post", f"{Q}/cache/warm"),
        ("delete", f"{Q}/cache/user/someone"),
        ("post", f"{Q}/cache/warm-up"),
        ("post", f"{Q}/search/semantic/index"),
    ],
)
def test_admin_routes_require_key(method, path):
    with _patch_key():
        r = getattr(client, method)(path)
    assert r.status_code == 401, (path, r.status_code)


def test_miracles_dashboard_with_key():
    with _patch_key():
        r = client.get(f"{Q}/miracles/admin/dashboard", headers={"X-Admin-API-Key": TEST_KEY})
    assert r.status_code == 200
    body = r.json()
    assert "statistics" in body
    assert "admin_id" not in body


def test_miracles_review_rejects_bad_decision():
    with _patch_key():
        r = client.post(
            f"{Q}/miracles/admin/review-feedback?feedback_id=x&decision=whatever",
            headers={"X-Admin-API-Key": TEST_KEY},
        )
    assert r.status_code == 422


def test_non_get_moderation_routes_in_quran_router_are_gated():
    """Every non-GET quran.py route whose path looks like moderation or cache
    management must depend on require_admin_api_key."""
    import re
    from app.api.routes.quran import router
    from app.core.admin_auth import require_admin_api_key

    pattern = re.compile(r"/(admin|update|verify|endorse|decide|cache)(/|$)|/review(/|$)|review-feedback|peer-review")
    offenders = []
    for route in router.routes:
        methods = getattr(route, "methods", set()) or set()
        if methods <= {"GET", "HEAD"}:
            continue
        if not pattern.search(route.path):
            continue
        deps = {d.call for d in route.dependant.dependencies}
        if require_admin_api_key not in deps:
            offenders.append(f"{sorted(methods)} {route.path}")
    assert offenders == []
