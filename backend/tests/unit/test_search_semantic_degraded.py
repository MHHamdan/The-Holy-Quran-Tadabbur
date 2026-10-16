"""GET /quran/semantic/search says when it is running on fallback vectors.

During an HF outage the route returned {results: [], model_used: 'fallback'}
with no degraded flag or message.
"""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _get(payload: dict) -> dict:
    with patch(
        "app.services.arabic_semantic_search.arabic_semantic_service.semantic_search",
        AsyncMock(return_value=payload),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            r = await client.get("/api/v1/quran/semantic/search", params={"q": "patience"})
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_fallback_model_is_flagged_bilingually():
    body = await _get({"results": [], "count": 0, "model_used": "fallback"})
    assert body["degraded"] == "ai_unavailable"
    assert body["message_en"] and body["message_ar"]
    assert body["results"] == []


@pytest.mark.asyncio
async def test_real_model_is_not_flagged():
    body = await _get({"results": [], "count": 0, "model_used": "intfloat/multilingual-e5-base"})
    assert "degraded" not in body
