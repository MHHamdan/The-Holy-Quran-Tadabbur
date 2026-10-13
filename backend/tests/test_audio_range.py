"""
Verse-range audio: open-ended ranges stop at the end of the surah.

The reader asks for "verse N to the end" as N..286 (the longest surah) and
plays the list verse by verse; any URL past the last verse is a dead file.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.audio_service import SURAH_VERSE_COUNTS, get_audio_service


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.parametrize("sura, count", [(1, 7), (2, 286), (108, 3), (114, 6)])
def test_service_clamps_to_surah_length(sura, count):
    urls = get_audio_service().get_verse_range_audio_urls(sura, 1, 286)
    assert [u["aya_no"] for u in urls] == list(range(1, count + 1))
    assert SURAH_VERSE_COUNTS[sura - 1] == count


@pytest.mark.asyncio
async def test_open_ended_range_reports_the_real_bounds(client):
    r = await client.get("/api/v1/quran/audio/range/1/3/286")
    assert r.status_code == 200
    body = r.json()
    assert body["total_verses"] == 5
    assert (body["aya_start"], body["aya_end"]) == (3, 7)
    assert body["verse_audios"][-1]["reference"] == "1:7"


@pytest.mark.asyncio
async def test_range_starting_past_the_end_is_empty(client):
    r = await client.get("/api/v1/quran/audio/range/1/8/286")
    assert r.status_code == 200
    assert r.json()["verse_audios"] == []
