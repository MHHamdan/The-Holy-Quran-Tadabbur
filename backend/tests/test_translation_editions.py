"""
Translation editions (QuranEnc) on the reader endpoints.

QuranEnc's republication terms require the text verbatim, with its version and
footnotes, so these tests pin: the catalogue carries attribution and version,
the reader only gets the editions it asks for, and the stored text matches the
cached upstream file byte for byte.
"""
import json
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "data" / "manifests" / "translation_sources.json"
CACHE_DIR = REPO_ROOT / "data" / "raw" / "translations" / "quranenc"
BASE = "/api/v1/quran"


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestManifest:
    """Static checks: run everywhere, no data needed."""

    def test_every_edition_carries_licence_terms(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["license_status"] == "verified"
        assert manifest["editions"], "manifest lists no editions"
        for edition in manifest["editions"]:
            assert "verbatim" in edition["license"]
            assert edition["language"] and edition["title"]

    def test_one_default_per_language_and_it_is_listed(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        keys = {e["key"]: e["language"] for e in manifest["editions"]}
        for language, key in manifest["defaults"].items():
            assert keys[key] == language
        assert manifest["defaults"]["en"] == "english_saheeh"


@pytest.mark.asyncio
class TestRequestValidation:
    async def test_too_many_editions_rejected(self, client):
        r = await client.get(f"{BASE}/suras/1", params={"translations": "a,b,c,d"})
        assert r.status_code == 400

    @pytest.mark.parametrize("bad", ["english saheeh", "x;drop", "EN", "a,,b"])
    async def test_malformed_keys_rejected(self, client, bad):
        r = await client.get(f"{BASE}/suras/1", params={"translations": bad})
        assert r.status_code == 422


@pytest.mark.asyncio
@pytest.mark.requires_data("translations")
class TestEditions:
    async def test_catalogue_lists_attribution_and_version(self, client):
        r = await client.get(f"{BASE}/translations/editions", params={"language": "en"})
        assert r.status_code == 200
        editions = r.json()
        assert editions[0]["key"] == "english_saheeh" and editions[0]["is_default"]
        for e in editions:
            assert e["version"]
            assert "QuranEnc.com" in e["attribution"]
            assert e["version"] in e["attribution"]
            assert e["source_url"].startswith("https://quranenc.com/")

    async def test_arabic_only_by_default(self, client):
        r = await client.get(f"{BASE}/suras/112")
        assert r.status_code == 200
        assert all(v["translations"] == [] for v in r.json())

    async def test_requested_editions_in_requested_order(self, client):
        r = await client.get(f"{BASE}/suras/1", params={"translations": "urdu_junagarhi,english_saheeh"})
        assert r.status_code == 200
        verses = r.json()
        assert len(verses) == 7
        for v in verses:
            assert [t["translator"] for t in v["translations"]] == ["urdu_junagarhi", "english_saheeh"]
            for t in v["translations"]:
                assert t["source_id"] == "quranenc" and t["edition_version"]

    @pytest.mark.parametrize(
        "path",
        ["page/2", "verses/2/255", "verses/2/1/5", "juz/30?limit=3"],
    )
    async def test_every_reader_endpoint_attaches_editions(self, client, path):
        sep = "&" if "?" in path else "?"
        r = await client.get(f"{BASE}/{path}{sep}translations=english_saheeh")
        assert r.status_code == 200, r.text
        body = r.json()
        verses = body if isinstance(body, list) else [body]
        assert verses
        assert all(v["translations"][0]["translator"] == "english_saheeh" for v in verses)

    async def test_footnotes_travel_with_the_text(self, client):
        # Saheeh International footnotes 1:2 ("Lord[4]") — QuranEnc term 4
        r = await client.get(f"{BASE}/verses/1/2", params={"translations": "english_saheeh"})
        t = r.json()["translations"][0]
        assert "[" in t["text"] and t["footnotes"]

    async def test_stored_text_is_verbatim(self, client):
        cache = CACHE_DIR / "english_saheeh.json"
        if not cache.exists():
            pytest.skip("QuranEnc cache not present (data bundle)")
        upstream = {
            (v["sura"], v["aya"]): v for v in json.loads(cache.read_text(encoding="utf-8"))["verses"]
        }
        r = await client.get(f"{BASE}/suras/2", params={"translations": "english_saheeh"})
        for v in r.json():
            t = v["translations"][0]
            source = upstream[(v["sura_no"], v["aya_no"])]
            assert t["text"] == source["translation"]
            assert t["footnotes"] == source["footnotes"]


@pytest.mark.asyncio
@pytest.mark.requires_data("translations")
class TestTranslationRoutes:
    async def test_available_translators_recommends_default(self, client):
        r = await client.get("/api/v1/translation/available-translators", params={"language": "en"})
        body = r.json()
        assert body["recommended"] == "english_saheeh"
        assert set(body["translators"]) >= {"english_saheeh", "english_rwwad"}

    async def test_verse_translation_with_several_editions_per_language(self, client):
        # Several English editions exist; the lookup must pick the default, not crash.
        r = await client.get("/api/v1/translation/verse/2/255", params={"language": "en"})
        assert r.status_code == 200
        assert r.json()["translator"] == "english_saheeh"


@pytest.mark.asyncio
@pytest.mark.requires_data("translations")
class TestTranslationSearch:
    URL = "/api/v1/quran/search/translation"

    async def test_all_words_must_match_in_mushaf_order(self, client):
        r = await client.get(self.URL, params={"q": "Moses Pharaoh", "limit": 50})
        body = r.json()
        assert r.status_code == 200 and body["total"] >= 20
        refs = [(h["sura_no"], h["aya_no"]) for h in body["hits"]]
        assert refs == sorted(refs)
        for h in body["hits"]:
            text = h["translation"]["text"].lower()
            assert "moses" in text and "pharaoh" in text
            assert h["translation"]["translator"] == "english_saheeh"

    async def test_transliteration_marks_are_folded(self, client):
        # Saheeh International spells it "Allāh"
        r = await client.get(self.URL, params={"q": "Allah", "limit": 1})
        assert r.json()["total"] > 1000

    async def test_word_start_not_substring(self, client):
        r = await client.get(self.URL, params={"q": "ad", "limit": 50})
        for h in r.json()["hits"]:
            assert any(w.startswith("ad") for w in h["translation"]["text"].lower().replace("ʿā", "a").split())

    @pytest.mark.parametrize("q", ["a.*b", "100%", "x|y", "[a-z]+"])
    async def test_regex_and_like_metacharacters_are_inert(self, client, q):
        r = await client.get(self.URL, params={"q": q})
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            assert r.json()["total"] == 0

    async def test_other_language_edition(self, client):
        r = await client.get(self.URL, params={"q": "صبر", "translations": "urdu_junagarhi"})
        assert r.json()["total"] > 0
        assert r.json()["editions"] == ["urdu_junagarhi"]

    async def test_unknown_language_404(self, client):
        r = await client.get(self.URL, params={"q": "mercy", "lang": "xx"})
        assert r.status_code == 404
