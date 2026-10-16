"""
Vector hits are pointers, not text: HybridRetriever resolves every Qdrant hit
against tafseer_chunks / tafseer_sources and serves the DB passage only.

Covers the stale-index failure modes from the release audit (orphan points
whose chunk_id is gone, 'لا يوجد تفسير' placeholder points, points from
disabled or unlicensed sources) plus the DB fallback that keeps enabled,
licensed sources with no vectors (baghawi) retrievable, and that keeps
retrieval working when muyassar_ar is not licence-verified.

The Qdrant client and the embedding model are faked; no HF call is made.
"""
from types import SimpleNamespace
from typing import List

import numpy as np
import pytest
from sqlalchemy import and_, select

from app.models.tafseer import TafseerChunk, TafseerSource
from app.rag.retrieval import HybridRetriever, is_placeholder_text, usable_evidence_text

PLACEHOLDER = "لا يوجد تفسير لهذه الأية"


class _FakeEmbedder:
    async def aencode(self, text):
        return np.zeros(4)


def _hit(chunk_id: str, source_id: str, score: float, payload_text: str = "PAYLOAD TEXT MUST NOT BE SERVED"):
    return {
        "id": abs(hash(chunk_id)) % 10_000_000,
        "score": score,
        "payload": {
            "chunk_id": chunk_id,
            "source_id": source_id,
            "source_name": "payload name",
            "source_name_ar": "payload name",
            "verse_reference": "9:9",
            "sura_no": 9,
            "aya_start": 9,
            "aya_end": 9,
            "content_ar": payload_text,
            "content_en": payload_text,
        },
    }


def _fake_qdrant(retriever: HybridRetriever, hits: List[dict], seen_bodies: list = None):
    async def _search(body):
        if seen_bodies is not None:
            seen_bodies.append(body)
        return hits

    retriever._qdrant_search = _search
    retriever._get_embedding_model = lambda: _FakeEmbedder()


# ---------------------------------------------------------------------------
# Pure unit tests (fake session, no DB)
# ---------------------------------------------------------------------------


def _row(chunk_id, source_id, text, sura=2, aya=255):
    chunk = SimpleNamespace(
        chunk_id=chunk_id, source_id=source_id, sura_no=sura, aya_start=aya, aya_end=aya,
        content_ar=text, content_en=None, scholarly_consensus=None,
    )
    source = SimpleNamespace(id=source_id, name_en=f"{source_id} (db)", name_ar=f"{source_id} db")
    return chunk, source


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def fetchall(self):
        return self._rows


class _FakeSession:
    """Returns the configured DB rows for any SELECT (the resolution query)."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        return _FakeResult(self.rows)


DB_TEXT = "هذا نص التفسير المخزن في قاعدة البيانات وهو أطول من عشرين حرفا"


class TestPlaceholderHelpers:
    def test_placeholder_detected(self):
        assert is_placeholder_text(PLACEHOLDER)
        assert not is_placeholder_text(DB_TEXT)
        assert not is_placeholder_text(None)

    def test_usable_evidence(self):
        assert usable_evidence_text(_row("a", "tabari_ar", DB_TEXT)[0])
        assert not usable_evidence_text(_row("a", "tabari_ar", PLACEHOLDER)[0])
        assert not usable_evidence_text(_row("a", "tabari_ar", "قصير")[0])
        assert not usable_evidence_text(_row("a", "tabari_ar", None)[0])


class TestVectorHitResolutionUnit:
    async def test_text_comes_from_db_not_payload(self):
        session = _FakeSession([_row("c1", "tabari_ar", DB_TEXT)])
        r = HybridRetriever(session)
        r._enabled_sources_cache = {"tabari_ar"}
        _fake_qdrant(r, [_hit("c1", "tabari_ar", 0.81)])

        out = await r._vector_search("q", "ar", None, top_k=5)

        assert len(out) == 1
        c = out[0]
        assert c.content == DB_TEXT and c.content_ar == DB_TEXT
        assert "PAYLOAD" not in (c.content or "")
        assert c.source_name == "tabari_ar (db)"
        assert c.verse_reference == "2:255"  # from the DB row, not the payload's 9:9
        assert c.relevance_score == pytest.approx(0.81)
        # one batched resolution query, no per-hit lookups
        assert session.calls == 1

    async def test_orphans_and_placeholders_dropped_order_kept(self):
        session = _FakeSession([
            _row("good1", "tabari_ar", DB_TEXT),
            _row("ph", "qurtubi_ar", PLACEHOLDER),
            _row("good2", "baghawi_ar", DB_TEXT + " ٢"),
        ])
        r = HybridRetriever(session)
        r._enabled_sources_cache = {"tabari_ar", "qurtubi_ar", "baghawi_ar"}
        _fake_qdrant(r, [
            _hit("orphan", "qurtubi_ar", 0.95, PLACEHOLDER),
            _hit("good2", "baghawi_ar", 0.9),
            _hit("ph", "qurtubi_ar", 0.85, PLACEHOLDER),
            _hit("good1", "tabari_ar", 0.8),
        ])

        out = await r._vector_search("q", "ar", None, top_k=5)

        assert [c.chunk_id for c in out] == ["good2", "good1"]
        assert all(not is_placeholder_text(c.content) for c in out)

    async def test_qdrant_filtered_to_retrievable_sources(self):
        session = _FakeSession([])
        r = HybridRetriever(session)
        r._enabled_sources_cache = {"tabari_ar", "baghawi_ar"}
        bodies: list = []
        _fake_qdrant(r, [_hit("x", "ibn_kathir_en", 0.99)], bodies)

        out = await r._vector_search("q", "en", None, top_k=5)

        assert out == []
        allowed = bodies[0]["filter"]["must"][0]["match"]["any"]
        assert set(allowed) == {"tabari_ar", "baghawi_ar"}
        assert session.calls == 0  # nothing to resolve

    async def test_preferred_sources_intersected(self):
        r = HybridRetriever(_FakeSession([]))
        r._enabled_sources_cache = {"tabari_ar"}
        bodies: list = []
        _fake_qdrant(r, [], bodies)
        assert await r._vector_search("q", "ar", ["ibn_kathir_en"], top_k=5) == []
        assert bodies == []  # never queried with a non-retrievable source

    async def test_external_fallback_skips_unlicensed_mirror(self):
        r = HybridRetriever(_FakeSession([]))
        r._enabled_sources_cache = {"tabari_ar"}  # muyassar_ar not retrievable
        requested = []

        class _Client:
            async def get_tafseer(self, s, a, editions):
                requested.append(list(editions))
                return SimpleNamespace(success=False, tafasir=[])

        r._tafseer_client = _Client()
        assert await r._external_api_fallback(2, 255, "ar") == []
        assert requested == []  # only edition was ar.muyassar -> skipped
        await r._external_api_fallback(2, 255, "en")
        assert requested == [["en.sahih"]]


# ---------------------------------------------------------------------------
# DB-backed tests (shared dev DB, read-only)
# ---------------------------------------------------------------------------


@pytest.fixture
async def session():
    from app.db import database

    async with database.AsyncSessionLocal() as s:
        yield s


def _exclude_muyassar(retriever: HybridRetriever):
    """Simulate muyassar_ar license_verified=0 without writing to the DB."""
    original = HybridRetriever._retrievable_source_clause

    def clause():
        return and_(original(), TafseerSource.id != "muyassar_ar")

    retriever._retrievable_source_clause = clause


async def _chunk_ids_for(session, sura, aya):
    rows = (await session.execute(
        select(TafseerChunk.chunk_id, TafseerChunk.source_id)
        .where(TafseerChunk.sura_no == sura, TafseerChunk.aya_start <= aya, TafseerChunk.aya_end >= aya)
    )).all()
    return {source_id: chunk_id for chunk_id, source_id in rows}


@pytest.mark.requires_data("tafsir:2:255")
class TestVectorHitResolutionDB:
    async def test_disabled_source_and_orphan_hits_dropped(self, session):
        ids = await _chunk_ids_for(session, 2, 255)
        if "tabari_ar" not in ids or "ibn_kathir_en" not in ids:
            pytest.skip("2:255 rows for tabari_ar / ibn_kathir_en not loaded")
        r = HybridRetriever(session)
        # payload lies about the source: the DB join must still reject it
        _fake_qdrant(r, [
            _hit(ids["ibn_kathir_en"], "tabari_ar", 0.99),
            _hit("deadbeefdeadbeef", "tabari_ar", 0.98, PLACEHOLDER),
            _hit(ids["tabari_ar"], "tabari_ar", 0.7),
        ])
        out = await r._vector_search("q", "ar", None, top_k=5)
        assert [c.chunk_id for c in out] == [ids["tabari_ar"]]
        db_text = (await session.execute(
            select(TafseerChunk.content_ar).where(TafseerChunk.chunk_id == ids["tabari_ar"])
        )).scalar_one()
        assert out[0].content_ar == db_text
        assert out[0].source_id == "tabari_ar"


@pytest.mark.requires_data("tafsir:2:255", "tafsir:39:53")
class TestDbFallbackWithoutMuyassar:
    """No vectors at all (HF unavailable): DB paths still return licensed sources."""

    @pytest.fixture
    def retriever(self, session):
        r = HybridRetriever(session)
        _exclude_muyassar(r)
        _fake_qdrant(r, [])  # empty index
        return r

    @staticmethod
    def _assert_licensed(out):
        assert out, "retrieval returned nothing"
        sources = {c.source_id for c in out}
        assert "muyassar_ar" not in sources
        assert sources <= {"tabari_ar", "qurtubi_ar", "ibn_kathir_ar", "baghawi_ar"}
        for c in out:
            assert c.content and not is_placeholder_text(c.content)
        return sources

    async def test_ayat_al_kursi(self, retriever):
        out = await retriever.retrieve("ما تفسير 2:255", language="ar", top_k=8)
        sources = self._assert_licensed(out)
        assert len(sources) >= 3
        assert any(c.sura_no == 2 and c.aya_start <= 255 <= c.aya_end for c in out)

    async def test_baghawi_reachable_without_vectors(self, retriever):
        out = await retriever._direct_verse_lookup(2, 255, None, "ar", ["baghawi_ar"])
        assert out and {c.source_id for c in out} == {"baghawi_ar"}

    async def test_zumar_53_english(self, retriever):
        out = await retriever.retrieve("What does 39:53 say about despair?", language="en", top_k=8)
        self._assert_licensed(out)
        assert any(c.sura_no == 39 and c.aya_start <= 53 <= c.aya_end for c in out)

    async def test_thematic_patience(self, retriever):
        out = await retriever.retrieve("patience in hardship", language="en", top_k=8)
        self._assert_licensed(out)

    async def test_lexical_fallback_spreads_sources(self, retriever):
        out = await retriever._keyword_search("الصبر", [], "ar", None, top_k=8)
        sources = self._assert_licensed(out)
        assert len(sources) >= 3, sources
