"""
Quran Verse Embedding Service for Semantic Search.

Provides:
1. Verse embedding generation using multilingual sentence transformers
2. Qdrant vector storage and retrieval
3. Semantic verse search with cross-language support

Arabic: خدمة تضمين آيات القرآن للبحث الدلالي
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.quran_text_utils import (
    preprocess_for_similarity,
    is_bismillah_verse,
)

logger = logging.getLogger(__name__)

# Qdrant collection name for verses
VERSE_COLLECTION = "quran_verses"

# Embedding dimension for the multilingual model (intfloat/multilingual-e5-large = 1024)
EMBEDDING_DIMENSION = 1024


@dataclass
class _VectorHit:
    """A Qdrant hit reduced to what we trust from it: the reference and score."""
    sura_no: int
    aya_no: int
    score: float


async def hydrate_vector_hits(
    hits: List["_VectorHit"],
    session=None,
) -> Dict[Tuple[int, int], Dict[str, Any]]:
    """Fetch canonical verse rows for Qdrant hits in one query.

    The Qdrant payload keeps a copy of the verse text from whenever the index
    was built; it drifted from the canonical Tanzil text in the database
    (4,885 of 6,236 verses differed). Every text field shown to a reader must
    come from ``quran_verses``, so the payload is used only for the reference.
    """
    refs = sorted({(h.sura_no, h.aya_no) for h in hits if h.sura_no and h.aya_no})
    if not refs:
        return {}

    from sqlalchemy import select, tuple_
    from app.db import database
    from app.models.quran import QuranVerse

    stmt = select(
        QuranVerse.id,
        QuranVerse.sura_no,
        QuranVerse.aya_no,
        QuranVerse.text_uthmani,
        QuranVerse.text_imlaei,
    ).where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(refs))

    if session is not None:
        rows = (await session.execute(stmt)).all()
    else:
        async with database.AsyncSessionLocal() as own_session:
            rows = (await own_session.execute(stmt)).all()

    return {
        (r.sura_no, r.aya_no): {
            "id": r.id,
            "text_uthmani": r.text_uthmani,
            "text_imlaei": r.text_imlaei,
        }
        for r in rows
    }


def _build_results(
    hits: List[_VectorHit],
    rows: Dict[Tuple[int, int], Dict[str, Any]],
    limit: int,
) -> List["VerseSimilarityResult"]:
    results: List[VerseSimilarityResult] = []
    for h in hits:
        row = rows.get((h.sura_no, h.aya_no))
        if row is None:
            # A vector whose reference is not in the canonical table is
            # never shown.
            continue
        # Skip verses that are only the Bismillah (1:1) so they do not
        # dominate similarity results.
        if (h.sura_no, h.aya_no) == (1, 1) or is_bismillah_verse(row["text_imlaei"]):
            continue
        results.append(VerseSimilarityResult(
            verse_id=row["id"],
            sura_no=h.sura_no,
            aya_no=h.aya_no,
            reference=f"{h.sura_no}:{h.aya_no}",
            text_uthmani=row["text_uthmani"],
            text_imlaei=row["text_imlaei"],
            similarity_score=h.score,
            matched_themes=[],
        ))
        if len(results) >= limit:
            break
    return results


@dataclass
class VerseSimilarityResult:
    """Result of semantic verse search."""
    verse_id: int
    sura_no: int
    aya_no: int
    reference: str
    text_uthmani: str
    text_imlaei: str
    similarity_score: float
    matched_themes: List[str]


class VerseEmbeddingService:
    """
    Service for generating and searching verse embeddings in Qdrant.

    Uses multilingual sentence transformers for cross-language semantic search.
    Supports Arabic and English queries against Arabic verse text.
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.hf_embedding_model
        self.qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        self._collection_ready = False

    def _get_model(self):
        """Embedding client (Hugging Face feature-extraction)."""
        if self._model is None:
            from app.ai.embeddings import HFEmbeddingModel

            logger.info(f"Using HF verse embedding model: {self._model_name}")
            self._model = HFEmbeddingModel(model=self._model_name)
        return self._model

    async def ensure_collection_exists(self) -> bool:
        """Ensure the Qdrant collection exists."""
        if self._collection_ready:
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if collection exists
                response = await client.get(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}"
                )

                if response.status_code == 200:
                    self._collection_ready = True
                    return True

                # Create collection if it doesn't exist
                create_body = {
                    "vectors": {
                        "size": EMBEDDING_DIMENSION,
                        "distance": "Cosine"
                    },
                    "optimizers_config": {
                        "memmap_threshold": 10000
                    }
                }

                response = await client.put(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}",
                    json=create_body
                )
                response.raise_for_status()

                # Create payload indices for filtering
                await client.put(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/index",
                    json={"field_name": "sura_no", "field_schema": "integer"}
                )
                await client.put(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/index",
                    json={"field_name": "aya_no", "field_schema": "integer"}
                )
                await client.put(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/index",
                    json={"field_name": "juz_no", "field_schema": "integer"}
                )

                logger.info(f"Created Qdrant collection: {VERSE_COLLECTION}")
                self._collection_ready = True
                return True

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False

    def compute_embedding(self, text: str, kind: str = "query") -> List[float]:
        """Compute embedding for text.

        multilingual-e5 models REQUIRE the asymmetric "query: " / "passage: "
        prefixes — without them retrieval quality collapses (verified by the
        concept-retrieval benchmark: direct-tier MRR was 0.0 unprefixed).
        """
        model = self._get_model()
        embedding = model.encode(f"{kind}: {text}", convert_to_numpy=True)
        return embedding.tolist()

    async def index_verses(
        self,
        verses: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Index verses into Qdrant.

        Args:
            verses: List of verse dicts with id, sura_no, aya_no, text_uthmani, etc.
            batch_size: Number of verses to index per batch

        Returns:
            Number of verses indexed
        """
        await self.ensure_collection_exists()

        model = self._get_model()
        total_indexed = 0

        for i in range(0, len(verses), batch_size):
            batch = verses[i:i + batch_size]

            # Prepare texts for embedding (with Bismillah exclusion)
            texts = []
            for v in batch:
                # Preprocess to exclude Bismillah from embedding
                # This prevents false similarity matches based on repeated phrase
                sura_no = v.get('sura_no')
                aya_no = v.get('aya_no')
                text_uthmani = preprocess_for_similarity(
                    v.get('text_uthmani', ''),
                    sura_no=sura_no,
                    aya_no=aya_no,
                    exclude_bismillah=True
                )
                text_imlaei = preprocess_for_similarity(
                    v.get('text_imlaei', ''),
                    sura_no=sura_no,
                    aya_no=aya_no,
                    exclude_bismillah=True
                )
                # Combine both scripts; "passage: " prefix is required by
                # multilingual-e5 for asymmetric retrieval.
                combined_text = f"passage: {text_uthmani} {text_imlaei}"
                texts.append(combined_text)

            # Generate embeddings for batch
            embeddings = await model.aencode(texts)

            # Prepare points for Qdrant
            points = []
            for j, v in enumerate(batch):
                point_id = v.get('id') or (v.get('sura_no', 0) * 1000 + v.get('aya_no', 0))
                points.append({
                    "id": point_id,
                    "vector": embeddings[j].tolist(),
                    "payload": {
                        "verse_id": v.get('id'),
                        "sura_no": v.get('sura_no'),
                        "aya_no": v.get('aya_no'),
                        "juz_no": v.get('juz_no', 0),
                        "page_no": v.get('page_no', 0),
                        # No verse text in the payload: readers always get
                        # the canonical text from quran_verses.
                    }
                })

            # Upsert to Qdrant
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.put(
                        f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/points",
                        json={"points": points}
                    )
                    response.raise_for_status()
                    total_indexed += len(batch)
            except Exception as e:
                logger.error(f"Failed to index batch {i}: {e}")

        logger.info(f"Indexed {total_indexed} verses into Qdrant")
        return total_indexed

    async def semantic_search(
        self,
        query: str,
        limit: int = 20,
        min_score: float = 0.3,
        sura_filter: Optional[int] = None,
        juz_filter: Optional[int] = None,
        exclude_verse: Optional[Tuple[int, int]] = None,
        session=None,
    ) -> List[VerseSimilarityResult]:
        """
        Search verses by semantic similarity.

        Args:
            query: Search query (Arabic or English)
            limit: Maximum results to return
            min_score: Minimum similarity score threshold
            sura_filter: Optional Surah filter
            juz_filter: Optional Juz filter
            exclude_verse: Optional (sura_no, aya_no) tuple to exclude

        Returns:
            List of similar verses with scores
        """
        await self.ensure_collection_exists()

        # Compute query embedding off the event loop (CPU-bound)
        import asyncio
        query_embedding = await asyncio.to_thread(self.compute_embedding, query)

        # Build filter conditions
        filter_conditions = []
        if sura_filter:
            filter_conditions.append({
                "key": "sura_no",
                "match": {"value": sura_filter}
            })
        if juz_filter:
            filter_conditions.append({
                "key": "juz_no",
                "match": {"value": juz_filter}
            })

        # Build search request
        search_body = {
            "vector": query_embedding,
            "limit": limit * 2 if exclude_verse else limit,  # Extra for filtering
            # Only the reference is read from the payload; text comes from Postgres.
            "with_payload": ["sura_no", "aya_no"],
            "score_threshold": min_score,
        }

        if filter_conditions:
            search_body["filter"] = {"must": filter_conditions}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/points/search",
                    json=search_body
                )
                response.raise_for_status()
                data = response.json()

            if data.get("status") != "ok":
                logger.warning(f"Qdrant search failed: {data}")
                return []

            hits = []
            for hit in data.get("result", []):
                payload = hit.get("payload", {})
                ref = (payload.get("sura_no", 0), payload.get("aya_no", 0))
                if exclude_verse and ref == exclude_verse:
                    continue
                hits.append(_VectorHit(ref[0], ref[1], hit.get("score", 0.0)))

            rows = await hydrate_vector_hits(hits, session=session)
            return _build_results(hits, rows, limit)

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def find_similar_to_verse(
        self,
        sura_no: int,
        aya_no: int,
        limit: int = 10,
        min_score: float = 0.5,
        exclude_same_sura: bool = False,
        session=None,
    ) -> List[VerseSimilarityResult]:
        """
        Find verses similar to a specific verse.

        Args:
            sura_no: Source verse Surah number
            aya_no: Source verse Ayah number
            limit: Maximum results
            min_score: Minimum similarity threshold
            exclude_same_sura: Whether to exclude verses from same Surah

        Returns:
            List of similar verses
        """
        # Look the source verse up by payload rather than by a derived point
        # id. index_verses() keys points on the database verse id, so the
        # previous `sura_no * 1000 + aya_no` guess never resolved and this
        # function always returned [] — silently, because the caller treats an
        # empty list as "no similar verses" rather than as a failure.
        try:
            scroll_body = {
                "limit": 1,
                "with_vector": True,
                "with_payload": False,
                "filter": {
                    "must": [
                        {"key": "sura_no", "match": {"value": sura_no}},
                        {"key": "aya_no", "match": {"value": aya_no}},
                    ]
                },
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/points/scroll",
                    json=scroll_body,
                )

                if response.status_code != 200:
                    logger.warning(
                        "Verse %s:%s lookup failed (%s)", sura_no, aya_no, response.status_code
                    )
                    return []

                points = response.json().get("result", {}).get("points", [])
                if not points:
                    logger.warning("Verse %s:%s not found in index", sura_no, aya_no)
                    return []

                verse_vector = points[0].get("vector") or []
                if not verse_vector:
                    return []

            # Search for similar verses
            search_body = {
                "vector": verse_vector,
                "limit": limit + 1,  # +1 to exclude self
                "with_payload": ["sura_no", "aya_no"],
                "score_threshold": min_score,
            }

            if exclude_same_sura:
                search_body["filter"] = {
                    "must_not": [{
                        "key": "sura_no",
                        "match": {"value": sura_no}
                    }]
                }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/points/search",
                    json=search_body
                )
                response.raise_for_status()
                data = response.json()

            hits = []
            for hit in data.get("result", []):
                payload = hit.get("payload", {})
                ref = (payload.get("sura_no", 0), payload.get("aya_no", 0))
                if ref == (sura_no, aya_no):
                    continue  # the source verse itself
                hits.append(_VectorHit(ref[0], ref[1], hit.get("score", 0.0)))

            rows = await hydrate_vector_hits(hits, session=session)
            return _build_results(hits, rows, limit)

        except Exception as e:
            logger.error(f"Find similar verses failed: {e}")
            return []

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get Qdrant collection statistics."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}"
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    points = result.get("points_count") or 0
                    # Newer Qdrant reports vectors_count as null (lazily
                    # computed) — fall back to points_count so callers
                    # gating on vectors_count don't treat a populated
                    # index as empty.
                    vectors = result.get("vectors_count")
                    return {
                        "exists": True,
                        "vectors_count": vectors if vectors is not None else points,
                        "points_count": points,
                        "segments_count": len(result.get("segments", [])),
                        "status": result.get("status", "unknown"),
                    }
                else:
                    return {"exists": False}

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"exists": False, "error": str(e)}


# Singleton instance
_verse_embedding_service: Optional[VerseEmbeddingService] = None


def get_verse_embedding_service() -> VerseEmbeddingService:
    """Get verse embedding service singleton."""
    global _verse_embedding_service
    if _verse_embedding_service is None:
        _verse_embedding_service = VerseEmbeddingService()
    return _verse_embedding_service
