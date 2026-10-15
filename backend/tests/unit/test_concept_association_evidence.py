"""
A concept association's explanation is an app-authored claim: it is only
served when the association cites an ayah reference
(has_sufficient_evidence). The relation itself stays, marked unverified.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("concept_id", ["person_musa", "person_ibrahim", "person_adam", "person_isa"])
async def test_unsupported_association_has_no_explanation(client, concept_id):
    r = await client.get(f"/api/v1/concepts/{concept_id}/associations", params={"include_derived": "true"})
    if r.status_code == 404:
        pytest.skip(f"{concept_id} not seeded")
    assert r.status_code == 200
    rows = r.json()
    if not rows:
        pytest.skip("no associations in this DB")
    for a in rows:
        if not a["has_sufficient_evidence"]:
            assert a["explanation_en"] is None and a["explanation_ar"] is None, a["id"]
