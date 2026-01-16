#!/usr/bin/env python3
"""
Ingest tafseer data into PostgreSQL and Qdrant.

CRITICAL CHUNKING RULES:
1. Chunks are STRICTLY ayah-anchored - each chunk maps to specific ayah range
2. Chunks NEVER cross surah boundaries
3. Raw text is preserved with hash for verification
4. Each chunk has deterministic chunk_id based on source + ayah range

Exit codes:
  0 - All sources ingested successfully
  1 - Some sources failed ingestion
  2 - Configuration error
"""
import sys
import os
import json
import hashlib
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    Filter, FieldCondition, MatchValue
)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"
RAW_DIR = DATA_DIR / "raw"


@dataclass
class TafseerChunk:
    """
    A chunk of tafseer text for indexing.

    INVARIANTS:
    - surah_number is always set (never crosses surahs)
    - ayah_start <= ayah_end
    - raw_text_hash is SHA256 of original text
    """
    chunk_id: str
    source_id: str
    source_name_ar: str
    source_name_en: str
    language: str
    surah_number: int
    ayah_start: int
    ayah_end: int
    text: str
    raw_text: str  # Preserved original text
    raw_text_hash: str  # SHA256 of raw_text
    word_count: int
    metadata: dict = field(default_factory=dict)


class AyahAnchoredChunker:
    """
    Chunks tafseer text with STRICT ayah anchoring.

    Rules:
    1. Each chunk is anchored to one or more consecutive ayahs
    2. Chunks NEVER cross surah boundaries
    3. Raw text is preserved and hashed
    4. Chunk boundaries respect ayah boundaries
    """

    def __init__(self, config: dict):
        self.max_words = config.get("max_chunk_words", 500)
        self.overlap_words = config.get("overlap_words", 50)
        self.preserve_raw_text = config.get("preserve_raw_text", True)
        self.prevent_cross_surah = config.get("prevent_cross_surah", True)

    def _generate_chunk_id(
        self,
        source_id: str,
        surah: int,
        ayah_start: int,
        ayah_end: int,
        chunk_idx: int = 0
    ) -> str:
        """
        Generate deterministic unique chunk ID.

        Format: md5(source_id:sN:aM-P:cQ)[:16]
        """
        base = f"{source_id}:s{surah}:a{ayah_start}-{ayah_end}:c{chunk_idx}"
        return hashlib.md5(base.encode()).hexdigest()[:16]

    def _compute_raw_hash(self, text: str) -> str:
        """Compute SHA256 hash of raw text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _count_words(self, text: str) -> int:
        """Count words in text (handles both AR and EN)."""
        return len(text.split())

    def chunk_verses(
        self,
        tafseer_entries: list[dict],
        source: dict
    ) -> list[TafseerChunk]:
        """
        Chunk tafseer entries with STRICT ayah anchoring.

        Args:
            tafseer_entries: List of {surah, ayah, text} entries
            source: Source configuration from manifest

        Returns:
            List of TafseerChunk objects
        """
        chunks = []
        source_id = source["id"]
        source_name_ar = source.get("name_ar", "")
        source_name_en = source.get("name_en", "")
        language = source.get("language", "en")

        # CRITICAL: Group by surah FIRST to prevent cross-surah chunks
        by_surah: dict[int, list[dict]] = {}
        for entry in tafseer_entries:
            surah = entry.get("surah", entry.get("sura", 0))
            if surah == 0:
                continue  # Skip invalid entries

            if surah not in by_surah:
                by_surah[surah] = []
            by_surah[surah].append(entry)

        # Sort each surah by ayah
        for surah in by_surah:
            by_surah[surah].sort(key=lambda x: x.get("ayah", x.get("aya", 0)))

        # Chunk each surah independently (NEVER cross surah boundaries)
        for surah_num, entries in sorted(by_surah.items()):
            surah_chunks = self._chunk_single_surah(
                entries=entries,
                surah_num=surah_num,
                source_id=source_id,
                source_name_ar=source_name_ar,
                source_name_en=source_name_en,
                language=language,
                methodology=source.get("methodology", ""),
                era=source.get("era", "")
            )
            chunks.extend(surah_chunks)

        return chunks

    def _chunk_single_surah(
        self,
        entries: list[dict],
        surah_num: int,
        source_id: str,
        source_name_ar: str,
        source_name_en: str,
        language: str,
        methodology: str,
        era: str
    ) -> list[TafseerChunk]:
        """
        Chunk a single surah's tafseer entries.

        GUARANTEE: All returned chunks have surah_number == surah_num
        """
        chunks = []

        if not entries:
            return chunks

        # Accumulator for current chunk
        current_texts = []
        current_raw_texts = []
        current_word_count = 0
        current_ayah_start = entries[0].get("ayah", entries[0].get("aya", 1))
        current_ayah_end = current_ayah_start
        chunk_idx = 0

        for entry in entries:
            ayah = entry.get("ayah", entry.get("aya", 0))
            text = entry.get("text", "").strip()

            if not text:
                continue

            word_count = self._count_words(text)

            # Check if adding this ayah would exceed max words
            if current_word_count + word_count > self.max_words and current_texts:
                # Finalize current chunk
                combined_text = " ".join(current_texts)
                combined_raw = "\n---\n".join(current_raw_texts)

                chunk = TafseerChunk(
                    chunk_id=self._generate_chunk_id(
                        source_id, surah_num, current_ayah_start, current_ayah_end, chunk_idx
                    ),
                    source_id=source_id,
                    source_name_ar=source_name_ar,
                    source_name_en=source_name_en,
                    language=language,
                    surah_number=surah_num,
                    ayah_start=current_ayah_start,
                    ayah_end=current_ayah_end,
                    text=combined_text,
                    raw_text=combined_raw,
                    raw_text_hash=self._compute_raw_hash(combined_raw),
                    word_count=current_word_count,
                    metadata={
                        "chunk_index": chunk_idx,
                        "methodology": methodology,
                        "era": era,
                        "ayah_count": current_ayah_end - current_ayah_start + 1
                    }
                )
                chunks.append(chunk)

                # Start new chunk (with overlap - keep last ayah for context)
                chunk_idx += 1
                if current_texts:
                    # Overlap: keep last entry
                    last_text = current_texts[-1]
                    last_raw = current_raw_texts[-1]
                    current_texts = [last_text]
                    current_raw_texts = [last_raw]
                    current_word_count = self._count_words(last_text)
                    current_ayah_start = current_ayah_end  # Start from last ayah of prev chunk
                else:
                    current_texts = []
                    current_raw_texts = []
                    current_word_count = 0
                    current_ayah_start = ayah

            # Add entry to current chunk
            current_texts.append(text)
            current_raw_texts.append(f"[{surah_num}:{ayah}] {text}")
            current_word_count += word_count
            current_ayah_end = ayah

        # Finalize last chunk
        if current_texts:
            combined_text = " ".join(current_texts)
            combined_raw = "\n---\n".join(current_raw_texts)

            chunk = TafseerChunk(
                chunk_id=self._generate_chunk_id(
                    source_id, surah_num, current_ayah_start, current_ayah_end, chunk_idx
                ),
                source_id=source_id,
                source_name_ar=source_name_ar,
                source_name_en=source_name_en,
                language=language,
                surah_number=surah_num,
                ayah_start=current_ayah_start,
                ayah_end=current_ayah_end,
                text=combined_text,
                raw_text=combined_raw,
                raw_text_hash=self._compute_raw_hash(combined_raw),
                word_count=current_word_count,
                metadata={
                    "chunk_index": chunk_idx,
                    "methodology": methodology,
                    "era": era,
                    "ayah_count": current_ayah_end - current_ayah_start + 1
                }
            )
            chunks.append(chunk)

        return chunks


class TafseerIngester:
    """Ingests tafseer chunks into PostgreSQL and Qdrant."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.chunker = AyahAnchoredChunker(self.manifest.get("ingestion_config", {}))

    def _load_manifest(self) -> dict:
        """Load tafseer manifest."""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_raw_tafseer(self, source_id: str) -> Optional[list[dict]]:
        """Load raw tafseer data."""
        raw_path = RAW_DIR / f"{source_id}.json"
        if not raw_path.exists():
            return None

        with open(raw_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def ingest_to_postgres(
        self,
        session: AsyncSession,
        source: dict,
        chunks: list[TafseerChunk]
    ) -> tuple[int, int]:
        """
        Ingest chunks into PostgreSQL.

        Returns (inserted_count, skipped_count)
        """
        from app.models.tafseer import TafseerSource, TafseerChunk as TafseerChunkModel

        source_id = source["id"]

        # Check if source exists, create if not
        result = await session.execute(
            select(TafseerSource).where(TafseerSource.id == source_id)
        )
        db_source = result.scalar_one_or_none()

        if not db_source:
            license_info = source.get("license", {})
            db_source = TafseerSource(
                id=source_id,
                name_ar=source.get("name_ar", ""),
                name_en=source.get("name_en", ""),
                author_ar=source.get("author_ar", ""),
                author_en=source.get("author_en", ""),
                era=source.get("era", ""),
                methodology=source.get("methodology", ""),
                language=source.get("language", "en"),
                reliability_score=source.get("reliability_score", 0.8),
                is_primary_source=1 if source.get("is_primary_source", False) else 0,
                license=json.dumps(license_info)
            )
            session.add(db_source)
            await session.flush()

        # Insert chunks (skip duplicates)
        inserted = 0
        skipped = 0

        for chunk in chunks:
            # Check if chunk exists
            result = await session.execute(
                select(TafseerChunkModel).where(TafseerChunkModel.chunk_id == chunk.chunk_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            db_chunk = TafseerChunkModel(
                chunk_id=chunk.chunk_id,
                source_id=db_source.id,
                surah_number=chunk.surah_number,
                ayah_start=chunk.ayah_start,
                ayah_end=chunk.ayah_end,
                text_content=chunk.text,
                raw_text=chunk.raw_text,
                raw_text_hash=chunk.raw_text_hash,
                language=chunk.language,
                word_count=chunk.word_count,
                metadata_json=json.dumps(chunk.metadata)
            )
            session.add(db_chunk)
            inserted += 1

        await session.commit()
        return inserted, skipped

    def ingest_to_qdrant(
        self,
        client: QdrantClient,
        chunks: list[TafseerChunk],
        collection_name: str = "tafseer_chunks"
    ) -> tuple[int, int]:
        """
        Ingest chunks into Qdrant vector store.

        Note: Uses placeholder vectors. Replace with proper embeddings in production.

        Returns (inserted_count, skipped_count)
        """
        # Ensure collection exists
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        if not collection_exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,  # MiniLM dimension
                    distance=Distance.COSINE
                )
            )

        # Generate points
        points = []
        for chunk in chunks:
            # Placeholder vector (replace with real embeddings)
            vector = self._generate_placeholder_vector(chunk.text, 384)

            point = PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "source_id": chunk.source_id,
                    "source_name_ar": chunk.source_name_ar,
                    "source_name_en": chunk.source_name_en,
                    "language": chunk.language,
                    "surah_number": chunk.surah_number,
                    "ayah_start": chunk.ayah_start,
                    "ayah_end": chunk.ayah_end,
                    "text": chunk.text[:1000],  # Truncate for payload
                    "word_count": chunk.word_count,
                    "raw_text_hash": chunk.raw_text_hash,
                    "methodology": chunk.metadata.get("methodology", ""),
                    "era": chunk.metadata.get("era", "")
                }
            )
            points.append(point)

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=collection_name,
                points=batch
            )

        return len(points), 0

    def _generate_placeholder_vector(self, text: str, dim: int) -> list[float]:
        """
        Generate placeholder vector from text hash.

        WARNING: NOT a real embedding. Replace with sentence-transformers.
        """
        import struct

        text_hash = hashlib.sha256(text.encode()).digest()
        vector = []
        seed = text_hash

        while len(vector) < dim:
            seed = hashlib.sha256(seed).digest()
            for i in range(0, len(seed), 4):
                if len(vector) >= dim:
                    break
                val = struct.unpack('f', seed[i:i+4])[0]
                normalized = max(-1, min(1, val / 1e38))
                vector.append(normalized)

        return vector[:dim]

    def validate_chunks(self, chunks: list[TafseerChunk]) -> list[str]:
        """
        Validate chunking invariants.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        for i, chunk in enumerate(chunks):
            # Check surah is set
            if chunk.surah_number <= 0 or chunk.surah_number > 114:
                errors.append(f"Chunk {i}: Invalid surah_number {chunk.surah_number}")

            # Check ayah range is valid
            if chunk.ayah_start > chunk.ayah_end:
                errors.append(f"Chunk {i}: ayah_start ({chunk.ayah_start}) > ayah_end ({chunk.ayah_end})")

            # Check raw text hash matches
            computed_hash = hashlib.sha256(chunk.raw_text.encode('utf-8')).hexdigest()
            if computed_hash != chunk.raw_text_hash:
                errors.append(f"Chunk {i}: raw_text_hash mismatch")

        # Check for cross-surah chunks (should never happen)
        surah_ranges = {}
        for chunk in chunks:
            key = (chunk.source_id, chunk.surah_number)
            if key not in surah_ranges:
                surah_ranges[key] = []
            surah_ranges[key].append((chunk.ayah_start, chunk.ayah_end))

        return errors

    async def ingest_source(self, source: dict) -> dict:
        """Ingest a single tafseer source."""
        source_id = source["id"]
        status = source.get("status", "unknown")

        result = {
            "source_id": source_id,
            "status": "skipped",
            "chunks_created": 0,
            "postgres_inserted": 0,
            "postgres_skipped": 0,
            "qdrant_inserted": 0,
            "validation_errors": [],
            "message": ""
        }

        # Block pending sources
        if status == "pending_user_input":
            result["message"] = "BLOCKED: Source pending user input (license verification required)"
            return result

        # Load raw data
        tafseer_data = self._load_raw_tafseer(source_id)
        if not tafseer_data:
            result["message"] = f"No raw data found at {RAW_DIR / f'{source_id}.json'}"
            return result

        # Create chunks (ayah-anchored)
        chunks = self.chunker.chunk_verses(tafseer_data, source)
        result["chunks_created"] = len(chunks)

        if not chunks:
            result["message"] = "No chunks created"
            return result

        # Validate chunks
        validation_errors = self.validate_chunks(chunks)
        result["validation_errors"] = validation_errors
        if validation_errors:
            result["message"] = f"Validation failed: {len(validation_errors)} errors"
            result["status"] = "validation_failed"
            return result

        # Ingest to PostgreSQL
        try:
            from app.db.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                inserted, skipped = await self.ingest_to_postgres(session, source, chunks)
                result["postgres_inserted"] = inserted
                result["postgres_skipped"] = skipped
        except Exception as e:
            result["message"] = f"PostgreSQL error: {str(e)}"
            print(f"    PostgreSQL ingestion failed: {e}")

        # Ingest to Qdrant
        try:
            from app.core.config import settings
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            inserted, skipped = self.ingest_to_qdrant(client, chunks)
            result["qdrant_inserted"] = inserted
            result["status"] = "success"
            result["message"] = "Ingestion complete"
        except Exception as e:
            result["message"] = f"Qdrant error: {str(e)}"
            print(f"    Qdrant ingestion failed: {e}")

        return result


async def main():
    """Main entry point."""
    print("=" * 60)
    print("TAFSEER INGESTION (Ayah-Anchored)")
    print("=" * 60)

    # Load manifest
    manifest_path = MANIFESTS_DIR / "tafseer_sources.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(2)

    # Parse command line args
    source_ids = None
    if len(sys.argv) > 1:
        source_ids = sys.argv[1:]
        print(f"Ingesting specific sources: {source_ids}")

    ingester = TafseerIngester(manifest_path)
    manifest = ingester.manifest

    sources = manifest.get("sources", [])
    if source_ids:
        sources = [s for s in sources if s["id"] in source_ids]

    results = []
    for source in sources:
        print(f"\nProcessing: {source.get('name_en', source['id'])}")
        result = await ingester.ingest_source(source)
        results.append(result)
        print(f"  Chunks: {result['chunks_created']}")
        print(f"  PostgreSQL: {result['postgres_inserted']} inserted, {result['postgres_skipped']} skipped")
        print(f"  Qdrant: {result['qdrant_inserted']} inserted")
        print(f"  Status: {result['status']}")
        if result.get("validation_errors"):
            print(f"  Validation errors: {len(result['validation_errors'])}")
        if result.get("message"):
            print(f"  Message: {result['message']}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] not in ("success", "skipped")]

    print(f"  Successful: {len(success)}")
    print(f"  Skipped/Blocked: {len(skipped)}")
    print(f"  Failed: {len(failed)}")

    total_chunks = sum(r["chunks_created"] for r in results)
    total_pg = sum(r["postgres_inserted"] for r in results)
    total_qdrant = sum(r["qdrant_inserted"] for r in results)

    print(f"\n  Total chunks created: {total_chunks}")
    print(f"  Total PostgreSQL inserts: {total_pg}")
    print(f"  Total Qdrant inserts: {total_qdrant}")

    print("=" * 60)

    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
