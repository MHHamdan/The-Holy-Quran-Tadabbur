"""
Asbab al-Nuzul proxy (WS1: backend-asbab-no-server-cache).

Upstream (alquran.cloud) is mocked with httpx.MockTransport: no network.
The fixture payload is synthetic placeholder text, not Qur'an or tafsir text.
"""
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import asbab
from app.main import app

AYAHS = [
    {"numberInSurah": 1, "text": "placeholder occasion one"},
    {"numberInSurah": 2, "text": ""},
    {"numberInSurah": 3, "text": "placeholder occasion three"},
]


class Upstream:
    def __init__(self):
        self.calls = []
        self.fail = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request.url.path)
        if self.fail:
            return httpx.Response(502)
        return httpx.Response(200, json={"code": 200, "data": {"ayahs": AYAHS}})


@pytest.fixture
def upstream(monkeypatch):
    up = Upstream()
    asbab._cache.clear()
    asbab._locks.clear()
    monkeypatch.setattr(asbab, "_get_client",
                        lambda: httpx.AsyncClient(transport=httpx.MockTransport(up.handler)))
    yield up
    asbab._cache.clear()
    asbab._locks.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_surah_and_ayah_requests_share_one_upstream_call(client, upstream):
    r1 = client.get("/api/v1/quran/asbab/2")
    r2 = client.get("/api/v1/quran/asbab/2")
    r3 = client.get("/api/v1/quran/asbab/2/3")
    assert [r.status_code for r in (r1, r2, r3)] == [200, 200, 200]
    assert upstream.calls == ["/v1/surah/2/ar.wahidi"]

    body = r1.json()
    assert body["total_with_content"] == 2
    assert [v["ayah"] for v in body["verses"]] == [1, 3]
    assert body["source_name"] and body["source_name_en"]  # attribution kept
    assert r3.json() == {"surah": 2, "ayah": 3, "text": "placeholder occasion three"}
    assert r1.headers["Cache-Control"] == "public, max-age=86400"


def test_second_request_is_fast(client, upstream):
    client.get("/api/v1/quran/asbab/2")
    t0 = time.perf_counter()
    assert client.get("/api/v1/quran/asbab/2").status_code == 200
    assert (time.perf_counter() - t0) < 0.2  # served from the in-process cache


def test_ayah_without_occasion_returns_empty_text(client, upstream):
    r = client.get("/api/v1/quran/asbab/2/2")
    assert r.status_code == 200 and r.json()["text"] == ""


def test_ayah_beyond_surah_is_404(client, upstream):
    r = client.get("/api/v1/quran/asbab/2/99")
    assert r.status_code == 404
    assert r.json()["detail"]["message_ar"]


def test_upstream_failure_is_bilingual_503(client, upstream):
    upstream.fail = True
    r = client.get("/api/v1/quran/asbab/5")
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert detail["message_ar"] and detail["message_en"]


def test_stale_copy_served_when_refresh_fails(client, upstream, monkeypatch):
    assert client.get("/api/v1/quran/asbab/7").status_code == 200
    # Age the entry past the TTL, then break upstream.
    fetched, data = asbab._cache[7]
    asbab._cache[7] = (fetched - asbab._CACHE_SECONDS - 1, data)
    upstream.fail = True
    r = client.get("/api/v1/quran/asbab/7")
    assert r.status_code == 200 and r.json()["total_with_content"] == 2
    assert upstream.calls == ["/v1/surah/7/ar.wahidi"] * 2


@pytest.mark.parametrize("path", ["/api/v1/quran/asbab/0", "/api/v1/quran/asbab/115", "/api/v1/quran/asbab/2/0"])
def test_invalid_refs_are_400_without_upstream_call(client, upstream, path):
    assert client.get(path).status_code == 400
    assert upstream.calls == []
