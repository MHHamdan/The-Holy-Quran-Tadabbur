"""
External tafsir: text cleaning and the edition list.

_clean_tafsir_text used to map every </span> to ⟩ (tabari 2:255 had 635 ⟩ for
270 ⟨) and stripped </p>/<hN> without a newline ('Ayat-al KursiThis'). The
copyrighted English works and five editions that always returned 404 are no
longer listed or proxied.
"""
import re

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.tafsir_api import (
    ALLOWED_QURAN_COM_IDS,
    TAFSIR_EDITIONS,
    external_tafsir_service,
)

clean = external_tafsir_service._clean_tafsir_text

FIXTURE = (
    '<h2 class="title">Ayat al-Kursi</h2>'
    '<p>This is the <span class="blue">greatest verse</span> of the Book.'
    '<span class="ref">(Muslim)</span></p>'
    '<p>Second <span class="green">quoted <span class="x">inner</span> text</span> here.<br>'
    'New line</p><div>Block</div><span class="blue">unclosed'
)


def _balanced(text: str) -> bool:
    depth = []
    pairs = {"⟩": "⟨", "』": "『"}
    for ch in text:
        if ch in "⟨『":
            depth.append(ch)
        elif ch in pairs:
            if not depth or depth.pop() != pairs[ch]:
                return False
    return not depth


def test_block_tags_become_newlines():
    out = clean(FIXTURE)
    assert out.startswith("Ayat al-Kursi\nThis is")
    assert "Book.(Muslim)\nSecond" in out
    assert "here.\nNew line\nBlock\n" in out
    assert not re.search(r"[a-z][A-Z]", out.replace("al-Kursi", ""))


def test_markers_balance_and_only_for_coloured_spans():
    out = clean(FIXTURE)
    assert _balanced(out)
    assert out.count("⟨") == out.count("⟩") == 2
    assert out.count("『") == out.count("』") == 1
    assert "⟨greatest verse⟩" in out
    assert "『quoted inner text』" in out
    assert "(Muslim)" in out and "⟩(Muslim)" not in out


def test_no_html_left():
    assert "<" not in clean(FIXTURE) and ">" not in clean(FIXTURE)


def test_empty_input():
    assert clean("") == ""


REMOVED = ["en_maarif", "en_tazkirul", "en_ibn_kathir", "ibn_kathir_en", "wasit",
           "mukhtasar", "ibn_juzayy", "alsidi", "alsiraaj", "ibn_ashoor"]


def test_unlicensed_and_broken_editions_removed():
    for eid in REMOVED:
        assert eid not in TAFSIR_EDITIONS
    assert all(e.language == "ar" for e in TAFSIR_EDITIONS.values())
    assert not ({168, 169, 817, 93} & ALLOWED_QURAN_COM_IDS)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", ["en_maarif", "wasit", "mukhtasar"])
async def test_removed_edition_404(client, edition):
    r = await client.get("/api/v1/tafseer/external/verse/2/255", params={"edition": edition})
    assert r.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("tafsir_id", [168, 169, 817, 1])
async def test_quran_com_proxy_refuses_unlisted_ids(client, tafsir_id):
    r = await client.get("/api/v1/tafseer/quran-com/verse/2/255", params={"tafsir_id": tafsir_id})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "EDITION_NOT_LICENSED"


@pytest.mark.asyncio
async def test_external_editions_list_matches(client):
    r = await client.get("/api/v1/tafseer/external/editions")
    ids = {e["id"] for e in r.json()["editions"]}
    assert ids == set(TAFSIR_EDITIONS)
