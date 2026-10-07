#!/usr/bin/env python3
"""
Index tafseer chunks into Qdrant using Hugging Face hosted embeddings.

Embeddings come from HF Inference Providers (``HF_EMBEDDING_MODEL``, default
``intfloat/multilingual-e5-large``, 1024-d) — the same model that produced the
vectors in the published data bundle, so incremental indexing stays
compatible. No GPU, torch, or local model files are needed.

SAFETY RULES:
- NEVER mix embedding dimensions in one collection (checked before writing)
- NEVER write placeholder vectors: without HF_TOKEN the script aborts
- Chunks are marked ``is_embedded`` only after their batch is upserted

Usage:
  python scripts/index/index_tafseer.py [--source muyassar_ar] [--limit 500]

Environment: DATABASE_URL, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION,
HF_TOKEN (server secret), HF_EMBEDDING_MODEL.
"""
import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.models import Distance, PointStruct, VectorParams  # noqa: E402
from sqlalchemy import create_engine, select, update  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.ai.embeddings import HFEmbeddingModel  # noqa: E402
from app.ai.hf_client import hf_configured  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models.tafseer import TafseerChunk, TafseerSource  # noqa: E402

BATCH_SIZE = 32


def get_qdrant_client() -> QdrantClient:
    # Suppress version mismatch warning (newer client works with server 1.7)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, check_compatibility=False)


def ensure_collection(client: QdrantClient, collection_name: str, dimension: int):
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
        print(f"  Created collection: {collection_name}")
    else:
        print(f"  Collection exists: {collection_name}")


def validate_collection_dimension(qdrant: QdrantClient, collection_name: str, expected_dim: int) -> bool:
    """False when an existing collection has a different vector size."""
    collections = {c.name for c in qdrant.get_collections().collections}
    if collection_name not in collections:
        return True
    existing_dim = qdrant.get_collection(collection_name).config.params.vectors.size
    if existing_dim != expected_dim:
        print("  CRITICAL ERROR: Dimension mismatch!")
        print(f"    Existing collection dimension: {existing_dim}")
        print(f"    New embedding dimension: {expected_dim}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Index tafseer chunks into Qdrant (HF embeddings)")
    parser.add_argument("--source", action="append", help="only index these source ids (repeatable)")
    parser.add_argument("--limit", type=int, default=None, help="index at most N chunks")
    args = parser.parse_args()

    print("=" * 60)
    print("TAFSEER INDEXING (Hugging Face embeddings)")
    print("=" * 60)

    if not hf_configured():
        print("ERROR: HF_TOKEN is not configured — refusing to write placeholder vectors.")
        sys.exit(1)

    start_time = datetime.now()
    collection_name = os.getenv("QDRANT_COLLECTION", settings.qdrant_collection_tafseer)
    embedder = HFEmbeddingModel()
    dimension = embedder.get_sentence_embedding_dimension()
    print(f"  Model: {embedder.model_name} ({dimension}-d)")

    engine = create_engine(settings.database_url)
    qdrant = get_qdrant_client()
    qdrant.get_collections()
    print("  Qdrant: connected")

    if not validate_collection_dimension(qdrant, collection_name, dimension):
        print("\n  ABORTING: dimension mismatch would corrupt the index")
        sys.exit(1)
    ensure_collection(qdrant, collection_name, dimension)

    indexed = 0
    with Session(engine) as session:
        query = (
            select(TafseerChunk, TafseerSource)
            .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
            .where(TafseerChunk.is_embedded == 0)
            .order_by(TafseerChunk.id)
        )
        if args.source:
            query = query.where(TafseerChunk.source_id.in_(args.source))
        if args.limit:
            query = query.limit(args.limit)
        rows = [(c, s) for c, s in session.execute(query).all() if (c.content_en or c.content_ar)]

        if not rows:
            total = session.execute(select(TafseerChunk.id)).all()
            print(f"  No unindexed chunks found (total chunks: {len(total)})")
            sys.exit(0)

        print(f"  Found {len(rows)} chunks to index")
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start:start + BATCH_SIZE]
            # multilingual-e5 asymmetric retrieval: "passage: " here,
            # retrieval.py sends "query: "-prefixed queries.
            texts = [f"passage: {c.content_en or c.content_ar}" for c, _ in batch]
            vectors = embedder.encode(texts)

            points = [
                PointStruct(
                    id=chunk.id,
                    vector=vectors[i].tolist(),
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "source_id": chunk.source_id,
                        "source_name": source.name_en,
                        "source_name_ar": source.name_ar,
                        "verse_reference": chunk.verse_reference,
                        "sura_no": chunk.sura_no,
                        "aya_start": chunk.aya_start,
                        "aya_end": chunk.aya_end,
                        "content_en": chunk.content_en[:500] if chunk.content_en else None,
                        "content_ar": chunk.content_ar[:500] if chunk.content_ar else None,
                        "scholarly_consensus": chunk.scholarly_consensus,
                    },
                )
                for i, (chunk, source) in enumerate(batch)
            ]
            qdrant.upsert(collection_name=collection_name, points=points)
            session.execute(
                update(TafseerChunk)
                .where(TafseerChunk.id.in_([c.id for c, _ in batch]))
                .values(is_embedded=1, embedding_model=embedder.model_name)
            )
            session.commit()
            indexed += len(batch)
            print(f"  Indexed {indexed}/{len(rows)} chunks")

    duration = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print(f"SUCCESS: Indexed {indexed} chunks in {duration:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    from app.ai.hf_client import HFInferenceError

    try:
        main()
    except HFInferenceError as err:
        # Nothing is written for a failed batch; already-indexed chunks keep
        # is_embedded=true, so re-running resumes where this stopped.
        print(f"ERROR: {err}. Check HF_TOKEN, network access and HF credits, then re-run.", file=sys.stderr)
        sys.exit(2)
