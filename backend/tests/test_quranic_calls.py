"""
Tests for Quranic Calls Atlas API — Phase Y

Uses ASGI transport (no real DB needed — the API reads pre-generated JSON files).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestQuranicCallsStatistics:
    async def test_statistics_200(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/statistics")
        assert r.status_code == 200

    async def test_statistics_has_required_fields(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/statistics")
        d = r.json()
        for field in ["totalCalls", "totalAyahsWithCalls", "directYaCalls",
                       "supplicationCalls", "byPattern", "byAddresseeType",
                       "byCallerType", "topSurahs", "latency_ms"]:
            assert field in d, f"Missing field: {field}"

    async def test_statistics_positive_counts(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/statistics")
        d = r.json()
        assert d["totalCalls"] > 0
        assert d["directYaCalls"] > 0
        assert d["supplicationCalls"] > 0

    async def test_statistics_top_surahs_non_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/statistics")
        d = r.json()
        assert len(d["topSurahs"]) > 0

    async def test_statistics_latency_ms(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/statistics")
        assert r.json()["latency_ms"] >= 0


class TestQuranicCallsList:
    async def test_list_200(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list")
        assert r.status_code == 200

    async def test_list_pagination_fields(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list")
        d = r.json()
        for f in ["items", "total", "page", "pageSize", "totalPages", "latency_ms"]:
            assert f in d

    async def test_list_items_have_required_fields(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list")
        items = r.json()["items"]
        assert len(items) > 0
        for item in items[:3]:
            for f in ["callId", "surahNumber", "ayahNumber", "ayahReference",
                       "ayahTextUthmani", "callPattern", "caller", "addressee",
                       "callFunction", "tone", "confidence", "reviewStatus",
                       "humanReviewRequired"]:
                assert f in item, f"Missing: {f}"

    async def test_list_all_items_need_review(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?page_size=50")
        items = r.json()["items"]
        for item in items:
            assert item["reviewStatus"] == "needs_review"
            assert item["humanReviewRequired"] is True

    async def test_list_filter_by_pattern(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?call_pattern=supplication")
        d = r.json()
        for item in d["items"]:
            assert item["callPattern"] == "supplication"

    async def test_list_filter_by_surah(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?surah=2")
        d = r.json()
        assert d["total"] > 0
        for item in d["items"]:
            assert item["surahNumber"] == 2

    async def test_list_filter_by_addressee(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?addressee_type=believers")
        d = r.json()
        for item in d["items"]:
            assert item["addressee"]["addresseeType"] == "believers"

    async def test_list_direct_only(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?direct_only=true")
        d = r.json()
        DIRECT = {
            "ya_direct", "ya_ayyuhal", "ya_ayatuha", "ya_bani", "ya_qawmi",
            "ya_ibadi", "ya_ahl", "ya_rabbi", "ya_abati", "ya_bunayya",
            "ya_prophet_name", "ya_lament", "ya_wish",
        }
        for item in d["items"]:
            assert item["callPattern"] in DIRECT

    async def test_list_page_size(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?page_size=5")
        assert len(r.json()["items"]) <= 5

    async def test_list_pages_non_overlapping(self, client: AsyncClient):
        r1 = await client.get("/api/v1/quranic-calls/list?page=1&page_size=10")
        r2 = await client.get("/api/v1/quranic-calls/list?page=2&page_size=10")
        ids1 = {i["callId"] for i in r1.json()["items"]}
        ids2 = {i["callId"] for i in r2.json()["items"]}
        assert len(ids1 & ids2) == 0

    async def test_list_ayah_text_not_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/list?page_size=30")
        for item in r.json()["items"]:
            assert item["ayahTextUthmani"].strip() != ""


class TestQuranicCallsDetail:
    async def test_detail_valid_call(self, client: AsyncClient):
        listing = await client.get("/api/v1/quranic-calls/list?page_size=1")
        call_id = listing.json()["items"][0]["callId"]
        r = await client.get(f"/api/v1/quranic-calls/detail/{call_id}")
        assert r.status_code == 200
        assert r.json()["callId"] == call_id

    async def test_detail_404_unknown(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/detail/call_999_999_999")
        assert r.status_code == 404

    async def test_detail_400_invalid_format(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/detail/not-a-valid-id")
        assert r.status_code == 400


class TestQuranicCallsBySurah:
    async def test_by_surah_2(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-surah/2")
        d = r.json()
        assert d["total"] > 0
        for item in d["items"]:
            assert item["surahNumber"] == 2

    async def test_by_surah_out_of_range(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-surah/115")
        assert r.status_code == 400

    async def test_by_surah_3_high_count(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-surah/3")
        assert r.json()["total"] >= 5


class TestQuranicCallsByAudience:
    async def test_by_audience_believers(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-audience/believers")
        d = r.json()
        assert d["total"] > 0
        for item in d["items"]:
            assert item["addressee"]["addresseeType"] == "believers"

    async def test_by_audience_invalid(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-audience/dragons")
        assert r.status_code == 400

    async def test_by_audience_prophet(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-audience/prophet")
        assert r.json()["total"] > 0


class TestQuranicCallsByCaller:
    async def test_by_caller_allah(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-caller/allah")
        d = r.json()
        assert d["total"] > 0
        for item in d["items"]:
            assert item["caller"]["callerType"] == "allah"

    async def test_by_caller_invalid(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-caller/robot")
        assert r.status_code == 400


class TestQuranicCallsByFunction:
    async def test_by_function_supplication(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/by-function/supplication")
        d = r.json()
        assert d["total"] > 0
        for item in d["items"]:
            assert item["callFunction"] == "supplication"


class TestQuranicCallsSearch:
    async def test_search_english_term(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/search?q=Imraan")
        assert r.status_code == 200

    async def test_search_empty_returns_error(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/search?q=")
        assert r.status_code in (400, 422)

    async def test_search_results_paged(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/search?q=surah&page_size=5")
        d = r.json()
        assert len(d["items"]) <= 5


class TestQuranicCallsGraph:
    async def test_graph_200(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/graph?max_nodes=50")
        assert r.status_code == 200

    async def test_graph_has_nodes_and_edges(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/graph?max_nodes=100")
        d = r.json()
        assert len(d["nodes"]) > 0
        assert len(d["edges"]) > 0

    async def test_graph_filter_by_node_type(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/graph?node_type=surah&max_nodes=200")
        d = r.json()
        for node in d["nodes"]:
            assert node["nodeType"] == "surah"

    async def test_graph_edges_review_required(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/graph?max_nodes=50")
        for edge in r.json()["edges"][:20]:
            assert edge["humanReviewRequired"] is True
            assert edge["reviewStatus"] == "needs_review"


class TestQuranicCallsExplain:
    async def test_explain_valid(self, client: AsyncClient):
        listing = await client.get("/api/v1/quranic-calls/list?page_size=1")
        call_id = listing.json()["items"][0]["callId"]
        r = await client.get(f"/api/v1/quranic-calls/explain/{call_id}")
        assert r.status_code == 200
        d = r.json()
        assert "disclaimer" in d

    async def test_explain_has_review_required(self, client: AsyncClient):
        listing = await client.get("/api/v1/quranic-calls/list?page_size=1")
        call_id = listing.json()["items"][0]["callId"]
        r = await client.get(f"/api/v1/quranic-calls/explain/{call_id}")
        d = r.json()
        assert d["reviewStatus"] == "needs_review"
        assert d["humanReviewRequired"] is True

    async def test_explain_404_unknown(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/explain/call_999_999_0")
        assert r.status_code == 404

    async def test_explain_400_invalid_format(self, client: AsyncClient):
        r = await client.get("/api/v1/quranic-calls/explain/bad-format")
        assert r.status_code == 400
