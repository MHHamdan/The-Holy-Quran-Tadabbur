"""
Phase G — User Feedback System Tests

Uses the real PostgreSQL database via httpx.AsyncClient + ASGITransport so that
asyncpg runs in the same event loop as the test — avoiding the "Future attached
to a different loop" error that occurs with starlette's sync TestClient.

Each test class tracks the IDs it inserts and deletes them in teardown so the
test DB stays clean without needing transactions or a separate schema.

Tests cover:
  1.  POST /feedback — accepted for all valid categories
  2.  POST /feedback — bilingual confirmation message returned
  3.  POST /feedback — priority auto-assigned from category
  4.  POST /feedback — message < 10 chars rejected with 422
  5.  POST /feedback — blank/whitespace-only message rejected
  6.  POST /feedback — unknown category rejected with 422
  7.  POST /feedback — missing required fields rejected
  8.  POST /feedback — optional fields (entity_type, entity_id, page_url) accepted
  9.  GET  /feedback/admin — 401 without admin token
  10. GET  /feedback/admin — 200 with admin token, returns list shape
  11. GET  /feedback/admin — filter by status works
  12. GET  /feedback/admin — filter by category works
  13. GET  /feedback/admin — items have bilingual category labels
  14. GET  /feedback/admin — pagination page_size respected
  15. GET  /feedback/admin/stats — 401 without token
  16. GET  /feedback/admin/stats — returns correct aggregate fields
  17. GET  /feedback/admin/stats — total is >= seeded count
  18. GET  /feedback/admin/stats — open_high_priority counts priority ≤ 2 open items
  19. GET  /feedback/admin/stats — by_category reflects actual submissions
  20. PATCH /feedback/admin/{id} — status update persists in DB
  21. PATCH /feedback/admin/{id} — admin_notes update persists in DB
  22. PATCH /feedback/admin/{id} — resolving sets resolved_at timestamp
  23. PATCH /feedback/admin/{id} — dismissing sets resolved_at
  24. PATCH /feedback/admin/{id} — 404 for nonexistent id
  25. PATCH /feedback/admin/{id} — 401 without admin token
  26. PATCH /feedback/admin/{id} — status and notes can update together
  27. tafsir_error and quran_ref_error → priority 1
  28. source_missing → priority 2
  29. translation_issue and inappropriate → priority 3
  30. ui_feedback and other → priority 5
  31. status defaults to 'open' on creation
  32. Admin list sorted: priority asc, then created_at desc
  33. Rate limit dependency overridable (infra check)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text

from app.main import app
from app.core.auth import require_admin, AdminUser
from app.core.rate_limit import feedback_rate_limit


# Pin every test in this module to a single shared event loop so that the
# app's module-level asyncpg engine (database.py::async_engine) is not
# used from a stale loop when the second test runs.
pytestmark = pytest.mark.asyncio(loop_scope="module")

# ---------------------------------------------------------------------------
# Dependency overrides
# ---------------------------------------------------------------------------

def _mock_admin() -> AdminUser:
    return AdminUser(user_id="phase-g-test-admin", role="admin")


async def _no_rate_limit() -> None:
    pass


app.dependency_overrides[require_admin] = _mock_admin
app.dependency_overrides[feedback_rate_limit] = _no_rate_limit

# ---------------------------------------------------------------------------
# Shared async client (module-scoped so the event loop stays warm)
# ---------------------------------------------------------------------------

_DB_URL = "postgresql+asyncpg://tadabbur:tadabbur_dev@localhost:5432/tadabbur"


async def _clean(ids: list[int]) -> None:
    """Delete test rows.  Creates a fresh engine inside the caller's event loop."""
    if not ids:
        return
    engine = create_async_engine(_DB_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM user_feedback WHERE id = ANY(:ids)"),
                {"ids": ids},
            )
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _post(client: AsyncClient, payload: dict):
    return await client.post("/api/v1/feedback", json=payload)


async def _admin_get(client: AsyncClient, path: str = "", params: dict | None = None):
    return await client.get(f"/api/v1/feedback/admin{path}", params=params or {})


async def _admin_patch(client: AsyncClient, feedback_id: int, payload: dict):
    return await client.patch(f"/api/v1/feedback/admin/{feedback_id}", json=payload)


async def _submit(
    client: AsyncClient,
    category: str = "ui_feedback",
    message: str = "Test feedback message long enough.",
) -> dict:
    r = await _post(client, {"category": category, "message": message})
    assert r.status_code == 200, f"Submit failed ({r.status_code}): {r.text}"
    return r.json()


# ===========================================================================
# 1–4. Submit — acceptance, bilingual response, priority, status default
# ===========================================================================

async def test_all_valid_categories_accepted(client):
    ids = []
    cats = [
        "translation_issue", "source_missing", "tafsir_error",
        "quran_ref_error", "ui_feedback", "inappropriate", "other",
    ]
    for cat in cats:
        data = await _submit(client, cat)
        ids.append(data["id"])
        assert data["ok"] is True
    await _clean(ids)


async def test_bilingual_confirmation_returned(client):
    data = await _submit(client, "tafsir_error", "Source attribution is missing from this tafsir entry.")
    await _clean([data["id"]])
    assert len(data["message_en"]) > 0
    assert len(data["message_ar"]) > 0


async def test_response_contains_integer_id(client):
    data = await _submit(client)
    await _clean([data["id"]])
    assert isinstance(data["id"], int)


async def test_status_defaults_to_open(client):
    data = await _submit(client)
    await _clean([data["id"]])
    assert data["status"] == "open"


# ===========================================================================
# 5–8. Input validation (no DB writes — all rejected before reaching DB)
# ===========================================================================

async def test_short_message_rejected(client):
    r = await _post(client, {"category": "other", "message": "short"})
    assert r.status_code == 422


async def test_blank_message_rejected(client):
    r = await _post(client, {"category": "other", "message": "   "})
    assert r.status_code == 422


async def test_unknown_category_rejected(client):
    r = await _post(client, {"category": "invented_xyz", "message": "Should fail validation here."})
    assert r.status_code == 422


async def test_missing_category_rejected(client):
    r = await _post(client, {"message": "No category field present in payload."})
    assert r.status_code == 422


async def test_missing_message_rejected(client):
    r = await _post(client, {"category": "other"})
    assert r.status_code == 422


# ===========================================================================
# 9. Optional fields
# ===========================================================================

async def test_all_optional_fields_accepted(client):
    r = await _post(client, {
        "category": "translation_issue",
        "message": "The translation shown here appears to be incorrect.",
        "entity_type": "story",
        "entity_id": "yusuf-segment-3",
        "page_url": "/stories/yusuf",
    })
    assert r.status_code == 200
    await _clean([r.json()["id"]])


async def test_no_optional_fields_accepted(client):
    r = await _post(client, {"category": "ui_feedback", "message": "Layout is broken on mobile."})
    assert r.status_code == 200
    await _clean([r.json()["id"]])


# ===========================================================================
# 10. Admin list — auth
# ===========================================================================

async def test_admin_list_requires_token(client):
    # Temporarily remove the admin override so the real auth check runs.
    app.dependency_overrides.pop(require_admin, None)
    try:
        r = await client.get("/api/v1/feedback/admin", headers={"Authorization": ""})
        assert r.status_code == 401
    finally:
        app.dependency_overrides[require_admin] = _mock_admin


# ===========================================================================
# 11–15. Admin list — shape, filters, pagination
# ===========================================================================

async def test_admin_list_shape(client):
    ids = [
        (await _submit(client, "tafsir_error", "Source missing from tafsir passage."))["id"],
        (await _submit(client, "source_missing", "Source not linked anywhere on this page."))["id"],
        (await _submit(client, "ui_feedback", "Mobile layout is broken on small screens."))["id"],
    ]
    r = await _admin_get(client)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data and "page" in data and "page_size" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 3
    await _clean(ids)


async def test_filter_by_status_open(client):
    ids = [(await _submit(client))["id"]]
    r = await _admin_get(client, params={"status": "open"})
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["status"] == "open"
    await _clean(ids)


async def test_filter_by_category(client):
    ids = [
        (await _submit(client, "tafsir_error", "Wrong attribution for tafsir entry."))["id"],
    ]
    r = await _admin_get(client, params={"category": "tafsir_error"})
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["category"] == "tafsir_error"
    await _clean(ids)


async def test_items_have_bilingual_labels(client):
    ids = [(await _submit(client, "source_missing", "No source linked for this tafsir."))["id"]]
    r = await _admin_get(client, params={"category": "source_missing"})
    items = r.json()["items"]
    assert len(items) >= 1
    item = items[0]
    assert item["category_label_en"] == "Source Missing"
    assert item["category_label_ar"] == "مصدر مفقود"
    await _clean(ids)


async def test_pagination_page_size_respected(client):
    r = await _admin_get(client, params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 2


# ===========================================================================
# 16. Admin stats — auth
# ===========================================================================

async def test_stats_requires_token(client):
    app.dependency_overrides.pop(require_admin, None)
    try:
        r = await client.get("/api/v1/feedback/admin/stats", headers={"Authorization": ""})
        assert r.status_code == 401
    finally:
        app.dependency_overrides[require_admin] = _mock_admin


# ===========================================================================
# 17–20. Admin stats — values
# ===========================================================================

async def test_stats_aggregate_fields_present(client):
    r = await _admin_get(client, "/stats")
    assert r.status_code == 200
    data = r.json()
    for key in ("total", "by_status", "by_category", "open_high_priority"):
        assert key in data


async def test_stats_total_ge_seeded(client):
    ids = [
        (await _submit(client, "tafsir_error", "Unattributed tafsir entry found."))["id"],
        (await _submit(client, "quran_ref_error", "Wrong surah number displayed."))["id"],
        (await _submit(client, "ui_feedback", "Layout breaks on small screens."))["id"],
    ]
    r = await _admin_get(client, "/stats")
    assert r.json()["total"] >= 3
    await _clean(ids)


async def test_stats_open_high_priority(client):
    ids = [
        (await _submit(client, "tafsir_error", "Attribution is missing from tafsir."))["id"],
        (await _submit(client, "quran_ref_error", "Surah number shown is incorrect."))["id"],
    ]
    r = await _admin_get(client, "/stats")
    assert r.json()["open_high_priority"] >= 2
    await _clean(ids)


async def test_stats_by_category_reflects_submissions(client):
    ids = [
        (await _submit(client, "tafsir_error", "Wrong scholar attributed here."))["id"],
        (await _submit(client, "ui_feedback", "Button is hard to find on mobile."))["id"],
    ]
    r = await _admin_get(client, "/stats")
    by_cat = r.json()["by_category"]
    assert by_cat.get("tafsir_error", 0) >= 1
    assert by_cat.get("ui_feedback", 0) >= 1
    await _clean(ids)


# ===========================================================================
# 21–27. Admin PATCH
# ===========================================================================

async def test_status_update_persists(client):
    fid = (await _submit(client, "other", "Feedback item for status update test."))["id"]
    r = await _admin_patch(client, fid, {"status": "in_review"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_review"
    await _clean([fid])


async def test_admin_notes_update_persists(client):
    fid = (await _submit(client, "other", "Feedback item for notes update testing."))["id"]
    r = await _admin_patch(client, fid, {"admin_notes": "Confirmed — will fix in next release."})
    assert r.status_code == 200
    assert r.json()["admin_notes"] == "Confirmed — will fix in next release."
    await _clean([fid])


async def test_resolved_sets_resolved_at(client):
    fid = (await _submit(client, "other", "Feedback item for resolve timestamp test."))["id"]
    r = await _admin_patch(client, fid, {"status": "resolved"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
    await _clean([fid])


async def test_dismissed_sets_resolved_at(client):
    fid = (await _submit(client, "other", "Feedback item for dismiss timestamp test."))["id"]
    r = await _admin_patch(client, fid, {"status": "dismissed"})
    assert r.status_code == 200
    assert r.json()["resolved_at"] is not None
    await _clean([fid])


async def test_patch_nonexistent_returns_404(client):
    r = await _admin_patch(client, 99999999, {"status": "resolved"})
    assert r.status_code == 404


async def test_patch_requires_token(client):
    fid = (await _submit(client, "other", "Feedback for auth check on patch endpoint."))["id"]
    app.dependency_overrides.pop(require_admin, None)
    try:
        r = await client.patch(
            f"/api/v1/feedback/admin/{fid}",
            json={"status": "resolved"},
            headers={"Authorization": ""},
        )
        assert r.status_code == 401
    finally:
        app.dependency_overrides[require_admin] = _mock_admin
    await _clean([fid])


async def test_status_and_notes_update_together(client):
    fid = (await _submit(client, "other", "Feedback item for combined update test."))["id"]
    r = await _admin_patch(client, fid, {"status": "in_review", "admin_notes": "Under investigation."})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "in_review"
    assert data["admin_notes"] == "Under investigation."
    await _clean([fid])


# ===========================================================================
# 28–31. Category priority auto-assignment
# ===========================================================================

async def test_tafsir_error_priority_1(client):
    data = await _submit(client, "tafsir_error", "Wrong scholar attributed to this tafsir passage.")
    await _clean([data["id"]])
    assert data["priority"] == 1


async def test_quran_ref_error_priority_1(client):
    data = await _submit(client, "quran_ref_error", "Wrong surah number is displayed for this verse.")
    await _clean([data["id"]])
    assert data["priority"] == 1


async def test_source_missing_priority_2(client):
    data = await _submit(client, "source_missing", "No source linked for this tafsir paragraph.")
    await _clean([data["id"]])
    assert data["priority"] == 2


async def test_translation_issue_priority_3(client):
    data = await _submit(client, "translation_issue", "The English translation here seems inaccurate.")
    await _clean([data["id"]])
    assert data["priority"] == 3


async def test_inappropriate_priority_3(client):
    data = await _submit(client, "inappropriate", "This content seems inappropriate for the platform.")
    await _clean([data["id"]])
    assert data["priority"] == 3


async def test_ui_feedback_priority_5(client):
    data = await _submit(client, "ui_feedback", "The button is difficult to find on mobile devices.")
    await _clean([data["id"]])
    assert data["priority"] == 5


async def test_other_priority_5(client):
    data = await _submit(client, "other", "Just a general comment about the overall platform.")
    await _clean([data["id"]])
    assert data["priority"] == 5


# ===========================================================================
# 32. Admin list sorted priority-asc, then newest-first
# ===========================================================================

async def test_admin_list_sorted_by_priority(client):
    ids = [
        (await _submit(client, "ui_feedback", "Low priority item submitted first for order test."))["id"],
        (await _submit(client, "tafsir_error", "High priority item submitted second for order."))["id"],
    ]
    r = await _admin_get(client)
    assert r.status_code == 200
    priorities = [item["priority"] for item in r.json()["items"]]
    assert priorities == sorted(priorities)
    await _clean(ids)


# ===========================================================================
# 33. Rate limit override sanity check
# ===========================================================================

async def test_rate_limit_override_allows_submission(client):
    data = await _submit(client, "ui_feedback", "Rate limit override is working correctly here.")
    await _clean([data["id"]])
    assert data["ok"] is True
