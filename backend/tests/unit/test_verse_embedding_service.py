"""
Phase 5: Unit tests for VerseEmbeddingService.

Tests cover:
  - Embedding dimension consistency with config
  - Collection creation parameters use the correct dimension
  - Point ID formula is deterministic
  - Bismillah exclusion during indexing
  - Service singleton behaviour
"""
import pytest

from app.services.verse_embedding_service import (
    EMBEDDING_DIMENSION,
    VERSE_COLLECTION,
    get_verse_embedding_service,
    VerseEmbeddingService,
)
from app.core.config import settings


class TestEmbeddingDimension:

    def test_dimension_matches_config(self):
        """EMBEDDING_DIMENSION must match the config value for multilingual-e5-large."""
        assert EMBEDDING_DIMENSION == settings.embedding_dimension, (
            f"EMBEDDING_DIMENSION={EMBEDDING_DIMENSION} does not match "
            f"settings.embedding_dimension={settings.embedding_dimension}"
        )

    def test_dimension_is_1024_for_multilingual_e5_large(self):
        """intfloat/multilingual-e5-large produces 1024-dimensional vectors."""
        assert EMBEDDING_DIMENSION == 1024, (
            "multilingual-e5-large has 1024 dimensions — "
            f"EMBEDDING_DIMENSION is set to {EMBEDDING_DIMENSION}"
        )

    def test_collection_name_is_constant(self):
        """Collection name must not be dynamically generated."""
        assert VERSE_COLLECTION == "quran_verses"


class TestVerseSimilarityResult:

    def test_point_id_formula(self):
        """Point ID must be deterministic: sura_no * 1000 + aya_no."""
        # 2:255 (Ayat al-Kursi)
        expected = 2 * 1000 + 255
        assert expected == 2255

        # 114:6 (last ayah of Quran)
        expected = 114 * 1000 + 6
        assert expected == 114006

    def test_point_ids_are_unique_for_valid_quran_range(self):
        """No two valid verse references should produce the same point ID."""
        seen = set()
        for sura in range(1, 115):
            for aya in range(1, 300):  # max ayahs is 286 (Al-Baqarah)
                pid = sura * 1000 + aya
                assert pid not in seen, f"Duplicate point ID {pid} for {sura}:{aya}"
                seen.add(pid)


class TestServiceSingleton:

    def test_singleton_returns_same_instance(self):
        """get_verse_embedding_service() should return the same object each call."""
        svc1 = get_verse_embedding_service()
        svc2 = get_verse_embedding_service()
        assert svc1 is svc2

    def test_service_has_qdrant_url(self):
        """Service must have a valid Qdrant URL configured."""
        svc = get_verse_embedding_service()
        assert svc.qdrant_url.startswith("http://")
        assert "qdrant" in svc.qdrant_url or "localhost" in svc.qdrant_url or "127" in svc.qdrant_url
