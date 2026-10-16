"""Degraded grammar responses carry an English note next to the Arabic one.

POST /grammar/analyze used to return only notes_ar when the model was down
and no static analysis existed, so the English UI had nothing to show.
"""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class _Down:
    health_check = AsyncMock(return_value=False)


class _Timeout:
    health_check = AsyncMock(return_value=True)

    async def analyze(self, **_kw):
        import httpx

        raise httpx.TimeoutException("slow")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service, source, en_fragment",
    [
        (_Down(), "unavailable", "unavailable right now"),
        (_Timeout(), "timeout", "timed out"),
    ],
)
async def test_degraded_analyze_is_bilingual(service, source, en_fragment):
    with patch("app.api.routes.grammar.get_grammar_service", return_value=service), patch(
        "app.api.routes.grammar.get_static_analysis", return_value=None
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            r = await client.post("/api/v1/grammar/analyze", json={"text": "ذهب الولد إلى المدرسة"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == source
    assert body["notes_ar"]
    assert en_fragment in body["notes_en"]
