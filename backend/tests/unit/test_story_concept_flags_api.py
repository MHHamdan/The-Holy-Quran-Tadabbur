"""
API checks for concept evidence flags (shared dev DB; skip when not seeded).

- /concepts/{id}/associations hides story co-occurrence (story_themes)
  associations by default and never reports has_sufficient_evidence without
  an ayah reference.
- /concepts/{id}/occurrences never reports is_verified for an occurrence
  without a verse location.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_associations_exclude_co_occurrence_by_default(client: AsyncClient):
    r = await client.get("/api/v1/concepts/person_sulayman/associations")
    if r.status_code == 404:
        pytest.skip("concepts not seeded")
    assert r.status_code == 200
    for a in r.json():
        assert a["derivation"] != "co_occurrence"
    r2 = await client.get("/api/v1/concepts/person_sulayman/associations?include_derived=true")
    assert r2.status_code == 200
    for a in r2.json():
        if a["derivation"] == "co_occurrence":
            assert a["has_sufficient_evidence"] is False


async def test_occurrences_without_location_are_not_verified(client: AsyncClient):
    r = await client.get("/api/v1/concepts/person_musa/occurrences")
    if r.status_code == 404:
        pytest.skip("concepts not seeded")
    assert r.status_code == 200
    for o in r.json()["occurrences"]:
        if o["sura_no"] is None:
            assert o["is_verified"] is False
