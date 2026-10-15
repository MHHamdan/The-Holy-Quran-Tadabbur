"""
/translation/verse serves stored, published translations only.

mode=literal used to reach TranslationMode.LITERAL, which did not exist, and
answered 500; behind it sat an unused path that asked an LLM to translate the
Qur'an. Both are gone: the route has no mode, and the service cannot generate.
"""
import inspect

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import translation as svc


def test_no_generation_path_left():
    assert [m.value for m in svc.TranslationMode] == ["scholarly"]
    for name in ("_generate_llm_translation", "_save_translation", "_log_translation"):
        assert not hasattr(svc.TranslationService, name), name
    assert not hasattr(svc, "LITERAL_TRANSLATION_PROMPT")
    assert list(inspect.signature(svc.TranslationService.__init__).parameters) == ["self", "session"]


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("params", [{"language": "en", "mode": "literal"}, {"language": "en"}])
async def test_verse_translation_is_never_500(client, params):
    r = await client.get("/api/v1/translation/verse/1/1", params=params)
    assert r.status_code in (200, 404), r.text
    if r.status_code == 200:
        body = r.json()
        assert body["mode"] == "scholarly" and body["translator"] != "llm"
        assert body["translated_text"]
