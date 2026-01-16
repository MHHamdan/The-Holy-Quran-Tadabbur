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

# Embedding dimension for the multilingual model
EMBEDDING_DIMENSION = 384  # MiniLM-L12 has 384 dimensions


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
        self._model_name = settings.embedding_model_multilingual
        self.qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        self._collection_ready = False

    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            import os
            import torch
            from sentence_transformers import SentenceTransformer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            device = os.environ.get("EMBEDDING_DEVICE", device)

            logger.info(f"Loading verse embedding model: {self._model_name} on {device}")
            self._model = SentenceTransformer(self._model_name, device=device)
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

    def compute_embedding(self, text: str) -> List[float]:
        """Compute embedding for text."""
        model = self._get_model()
        # For query, add prefix as recommended for E5/multilingual models
        embedding = model.encode(text, convert_to_numpy=True)
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
                # Combine Arabic text with transliteration for better matching
                combined_text = f"{text_uthmani} {text_imlaei}"
                texts.append(combined_text)

            # Generate embeddings for batch
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

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
                        "text_uthmani": v.get('text_uthmani', ''),
                        "text_imlaei": v.get('text_imlaei', ''),
                        "sura_name_ar": v.get('sura_name_ar', ''),
                        "sura_name_en": v.get('sura_name_en', ''),
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

        # Compute query embedding
        query_embedding = self.compute_embedding(query)

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
            "with_payload": True,
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

            results = []
            for hit in data.get("result", []):
                payload = hit.get("payload", {})
                sura_no = payload.get("sura_no", 0)
                aya_no = payload.get("aya_no", 0)
                text_uthmani = payload.get("text_uthmani", "")

                # Skip excluded verse
                if exclude_verse and (sura_no, aya_no) == exclude_verse:
                    continue

                # Skip verses that are primarily Bismillah (e.g., 1:1)
                # These shouldn't appear in semantic search results
                if is_bismillah_verse(text_uthmani):
                    continue

                results.append(VerseSimilarityResult(
                    verse_id=payload.get("verse_id", 0),
                    sura_no=sura_no,
                    aya_no=aya_no,
                    reference=f"{sura_no}:{aya_no}",
                    text_uthmani=text_uthmani,
                    text_imlaei=payload.get("text_imlaei", ""),
                    similarity_score=hit.get("score", 0.0),
                    matched_themes=[],  # Can be enriched later
                ))

                if len(results) >= limit:
                    break

            return results

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
        # Get the verse vector from Qdrant
        point_id = sura_no * 1000 + aya_no

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.qdrant_url}/collections/{VERSE_COLLECTION}/points/{point_id}"
                )

                if response.status_code != 200:
                    logger.warning(f"Verse {sura_no}:{aya_no} not found in index")
                    return []

                data = response.json()
                verse_vector = data.get("result", {}).get("vector", [])

                if not verse_vector:
                    return []

            # Search for similar verses
            search_body = {
                "vector": verse_vector,
                "limit": limit + 1,  # +1 to exclude self
                "with_payload": True,
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

            results = []
            for hit in data.get("result", []):
                payload = hit.get("payload", {})
                hit_sura = payload.get("sura_no", 0)
                hit_aya = payload.get("aya_no", 0)
                text_uthmani = payload.get("text_uthmani", "")

                # Skip the source verse itself
                if hit_sura == sura_no and hit_aya == aya_no:
                    continue

                # Skip verses that are primarily Bismillah
                if is_bismillah_verse(text_uthmani):
                    continue

                results.append(VerseSimilarityResult(
                    verse_id=payload.get("verse_id", 0),
                    sura_no=hit_sura,
                    aya_no=hit_aya,
                    reference=f"{hit_sura}:{hit_aya}",
                    text_uthmani=text_uthmani,
                    text_imlaei=payload.get("text_imlaei", ""),
                    similarity_score=hit.get("score", 0.0),
                    matched_themes=[],
                ))

                if len(results) >= limit:
                    break

            return results

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
                    return {
                        "exists": True,
                        "vectors_count": result.get("vectors_count", 0),
                        "points_count": result.get("points_count", 0),
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
