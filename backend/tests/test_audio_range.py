"""
Verse-range audio: open-ended ranges stop at the end of the surah.

The reader asks for "verse N to the end" as N..286 (the longest surah) and
plays the list verse by verse; any URL past the last verse is a dead file.
"""
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.audio_service import RECITERS, SURAH_VERSE_COUNTS, get_audio_service


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


# ---------------------------------------------------------------------------
# Fallbacks never switch reciter or style
# ---------------------------------------------------------------------------

_EVERYAYAH_FOLDERS = {info.everyayah_folder for info in RECITERS.values()}
_CDN_IDS = {info.alquran_cloud_id for info in RECITERS.values() if info.alquran_cloud_id}


def _foreign_markers(reciter_key):
    info = RECITERS[reciter_key]
    return ({f"/{f}/" for f in _EVERYAYAH_FOLDERS - {info.everyayah_folder}}
            | {f"/{c}/" for c in _CDN_IDS - {info.alquran_cloud_id}})


@pytest.mark.parametrize("reciter", list(RECITERS))
def test_no_fallback_uses_another_reciter(reciter):
    svc = get_audio_service()
    rid = RECITERS[reciter].id
    urls = list(svc.get_verse_audio_urls_with_fallback(2, 255, rid).values())
    urls += svc.get_all_fallback_urls(2, 255, rid)
    for v in svc.get_verse_range_audio_urls(1, 1, 7, rid):
        urls += [v["url"], *v["fallback_urls"]]
    assert urls
    for url in urls:
        assert not any(m in url for m in _foreign_markers(reciter)), (rid, url)
        assert "quranicaudio" not in url and "verses.quran.com" not in url


def test_cdn_fallbacks_use_working_bitrates_and_matching_style():
    svc = get_audio_service()
    by_id = {info.id: svc.get_verse_audio_urls_with_fallback(1, 3, info.id) for info in RECITERS.values()}
    assert by_id["mishary_afasy"]["fallback1"].endswith("/128/ar.alafasy/3.mp3")
    assert by_id["saud_shuraim"]["fallback1"].endswith("/64/ar.saoodshuraym/3.mp3")
    assert by_id["minshawi"]["fallback1"].endswith("/64/ar.minshawimujawwad/3.mp3")
    # Abdul Basit is mujawwad; the CDN only has his murattal: no fallback.
    assert "fallback1" not in by_id["abdul_basit"]
    assert all("fallback2" not in urls for urls in by_id.values())


def test_surah_level_quranicaudio_links_are_gone():
    assert get_audio_service().get_surah_audio_url(1, "mishary_afasy") is None


@pytest.mark.skipif(os.environ.get("RUN_NETWORK_TESTS") != "1",
                    reason="network: set RUN_NETWORK_TESTS=1 to HEAD-check every CDN fallback")
@pytest.mark.parametrize("reciter", list(RECITERS))
def test_every_fallback_answers_200(reciter):
    import httpx

    urls = get_audio_service().get_all_fallback_urls(1, 1, RECITERS[reciter].id)
    for url in urls:
        r = httpx.head(url, timeout=15, follow_redirects=True)
        assert r.status_code == 200, url
