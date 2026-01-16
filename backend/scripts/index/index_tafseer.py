#!/usr/bin/env python3
"""
Index tafseer chunks into Qdrant vector database.

GPU SAFETY:
===========
This script includes safety checks for GPU indexing:
1. Dimension assertions - vectors MUST match expected dimension (1024 for e5-large)
2. GPU detection with safe CPU fallback
3. Device logging on startup for debugging
4. Memory checks before GPU allocation

Environment variables:
  EMBEDDING_MODEL: Model to use (default: intfloat/multilingual-e5-large)
    - intfloat/multilingual-e5-small (384 dim, ~500MB, fast)
    - intfloat/multilingual-e5-base (768 dim, ~1.1GB, balanced)
    - intfloat/multilingual-e5-large (1024 dim, ~2.2GB, best quality) [DEFAULT]
  EMBEDDING_DEVICE: Device to use (auto, cpu, cuda, cuda:0, etc.)
    - auto: Use GPU if available, else CPU (default)
    - cpu: Force CPU mode (for low-memory systems)
  EMBEDDING_DIMENSION: Override vector dimension (NOT RECOMMENDED - use model's dimension)

SAFETY RULES:
- NEVER mix embedding dimensions in same collection
- ALWAYS verify dimension consistency before indexing
- If GPU fails, fallback to CPU rather than crash
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("WARNING: sentence-transformers not installed. Using placeholder vectors.")

# Model dimension mapping
MODEL_DIMENSIONS = {
    "intfloat/multilingual-e5-small": 384,
    "intfloat/multilingual-e5-base": 768,
    "intfloat/multilingual-e5-large": 1024,
}

# Expected dimension for production (e5-large)
EXPECTED_DIMENSION = 1024
DEFAULT_MODEL = "intfloat/multilingual-e5-large"

# Minimum GPU memory required for each model (in bytes)
MIN_GPU_MEMORY = {
    "intfloat/multilingual-e5-small": 1 * 1024**3,   # 1GB
    "intfloat/multilingual-e5-base": 2 * 1024**3,    # 2GB
    "intfloat/multilingual-e5-large": 4 * 1024**3,   # 4GB
}

from app.models.tafseer import TafseerChunk, TafseerSource
from app.core.config import settings


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def get_qdrant_client() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    # Suppress version mismatch warning (client 1.16 works with server 1.7)
    return QdrantClient(host=host, port=port, check_compatibility=False)


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


def detect_gpu_info() -> dict:
    """
    Detect GPU availability and return detailed info.

    Returns:
        dict with keys: available, device_name, memory_total, memory_free, cuda_version
    """
    info = {
        "available": False,
        "device_name": None,
        "memory_total": 0,
        "memory_free": 0,
        "cuda_version": None,
        "device_count": 0,
    }

    try:
        import torch
        if torch.cuda.is_available():
            info["available"] = True
            info["device_count"] = torch.cuda.device_count()
            info["device_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info["memory_total"] = props.total_memory
            info["cuda_version"] = torch.version.cuda

            # Get free memory
            memory_stats = torch.cuda.memory_stats(0) if torch.cuda.is_initialized() else {}
            info["memory_free"] = info["memory_total"] - memory_stats.get("allocated_bytes.all.current", 0)
    except ImportError:
        pass
    except Exception as e:
        print(f"  Warning: GPU detection error: {e}")

    return info


def log_device_info():
    """Log device information on startup."""
    print("\n  === DEVICE INFO ===")
    gpu_info = detect_gpu_info()

    if gpu_info["available"]:
        print(f"  GPU: {gpu_info['device_name']}")
        print(f"  GPU Count: {gpu_info['device_count']}")
        print(f"  GPU Memory: {gpu_info['memory_total'] / 1024**3:.1f} GB")
        print(f"  CUDA Version: {gpu_info['cuda_version']}")
    else:
        print("  GPU: Not available (CPU mode)")

    return gpu_info


def get_device(model_name: str = None):
    """
    Determine device to use for embeddings with safe GPU fallback.

    Args:
        model_name: Model to check memory requirements for

    Returns:
        str: Device string ('cuda', 'cuda:0', 'cpu', etc.)
    """
    device = os.getenv("EMBEDDING_DEVICE", "auto")
    model_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)

    if device == "auto":
        gpu_info = detect_gpu_info()

        if gpu_info["available"]:
            # Check if GPU has enough memory for the model
            min_required = MIN_GPU_MEMORY.get(model_name, 2 * 1024**3)

            if gpu_info["memory_total"] >= min_required:
                print(f"  Using GPU: {gpu_info['device_name']}")
                return "cuda"
            else:
                print(f"  GPU memory insufficient for {model_name}")
                print(f"    Required: {min_required / 1024**3:.1f}GB, Available: {gpu_info['memory_total'] / 1024**3:.1f}GB")
                print(f"  Falling back to CPU")
                return "cpu"
        else:
            print("  No GPU detected, using CPU")
            return "cpu"

    # Validate explicitly specified CUDA device
    if device.startswith("cuda"):
        gpu_info = detect_gpu_info()
        if not gpu_info["available"]:
            print(f"  WARNING: CUDA device '{device}' requested but no GPU available!")
            print(f"  Falling back to CPU for safety")
            return "cpu"

    return device


def get_embedder():
    """
    Get sentence transformer model with dimension safety checks.

    Returns:
        tuple: (model, dimension) where dimension is validated

    Raises:
        ValueError: If dimension mismatch detected
    """
    if not HAS_EMBEDDINGS:
        print("  WARNING: sentence-transformers not installed, using placeholders")
        return None, EXPECTED_DIMENSION  # Use expected dimension for consistency

    # Default to large model for best quality (1024 dim)
    model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
    device = get_device(model_name)

    print(f"  Loading embedding model: {model_name}")
    print(f"  Device: {device}")

    try:
        model = SentenceTransformer(model_name, device=device)
    except Exception as e:
        if device.startswith("cuda"):
            print(f"  GPU loading failed: {e}")
            print(f"  Retrying with CPU...")
            model = SentenceTransformer(model_name, device="cpu")
        else:
            raise

    # Get actual dimension from model
    actual_dimension = model.get_sentence_embedding_dimension()
    expected_dimension = MODEL_DIMENSIONS.get(model_name, actual_dimension)

    # Dimension safety check
    if actual_dimension != expected_dimension:
        raise ValueError(
            f"DIMENSION MISMATCH! Model {model_name} returned {actual_dimension}D vectors, "
            f"expected {expected_dimension}D. This would corrupt the vector index!"
        )

    print(f"  Embedding dimension: {actual_dimension} (verified)")

    # Warn if not using production dimension
    if actual_dimension != EXPECTED_DIMENSION:
        print(f"  WARNING: Using non-standard dimension {actual_dimension}.")
        print(f"           Production expects {EXPECTED_DIMENSION}D (e5-large).")
        print(f"           Mixing dimensions will corrupt the index!")

    return model, actual_dimension


def generate_embedding(embedder, text: str, dimension: int = 1024) -> list:
    """Generate embedding for text."""
    if embedder:
        return embedder.encode(text).tolist()
    # Placeholder: return zero vector
    return [0.0] * dimension


def validate_collection_dimension(qdrant: QdrantClient, collection_name: str, expected_dim: int) -> bool:
    """
    Validate that existing collection has matching dimension.

    Returns:
        True if dimension matches or collection doesn't exist
        False if dimension mismatch (CRITICAL ERROR)
    """
    try:
        collections = {c.name: c for c in qdrant.get_collections().collections}

        if collection_name not in collections:
            return True  # Collection doesn't exist yet, OK to create

        # Get collection info
        collection_info = qdrant.get_collection(collection_name)
        existing_dim = collection_info.config.params.vectors.size

        if existing_dim != expected_dim:
            print(f"  CRITICAL ERROR: Dimension mismatch!")
            print(f"    Existing collection dimension: {existing_dim}")
            print(f"    New embedding dimension: {expected_dim}")
            print(f"    This would corrupt the vector index!")
            print(f"    Either use matching model or recreate collection.")
            return False

        return True
    except Exception as e:
        print(f"  Warning: Could not validate collection dimension: {e}")
        return True  # Allow to proceed with caution


def main():
    print("=" * 60)
    print("TAFSEER INDEXING (GPU-SAFE)")
    print("=" * 60)

    start_time = datetime.now()
    collection_name = os.getenv("QDRANT_COLLECTION", "tafseer_chunks")
    batch_size = 50

    # Log device info on startup
    log_device_info()

    try:
        print("\n[1/5] Connecting to services...")
        engine = create_engine(get_db_url())
        qdrant = get_qdrant_client()

        # Test Qdrant connection
        qdrant.get_collections()
        print("  Qdrant: Connected")

        print("\n[2/5] Loading embedding model...")
        embedder, dimension = get_embedder()

        # Override dimension if explicitly set (NOT RECOMMENDED)
        if os.getenv("EMBEDDING_DIMENSION"):
            override_dim = int(os.getenv("EMBEDDING_DIMENSION"))
            print(f"  WARNING: Dimension override requested: {override_dim}")
            print(f"           Model dimension: {dimension}")
            if override_dim != dimension:
                print(f"  ERROR: Cannot override dimension - would corrupt embeddings!")
                print(f"         Use matching model instead.")
                sys.exit(1)
            dimension = override_dim

        print("\n[3/5] Validating collection dimension...")
        if not validate_collection_dimension(qdrant, collection_name, dimension):
            print("\n  ABORTING: Dimension mismatch would corrupt index!")
            sys.exit(1)
        print(f"  Dimension validated: {dimension}D")

        print("\n[4/5] Setting up collection...")
        ensure_collection(qdrant, collection_name, dimension)

        print("\n[5/5] Indexing chunks (this may take a while on CPU)...")

        with Session(engine) as session:
            # Get chunks with source info
            result = session.execute(
                select(TafseerChunk, TafseerSource)
                .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
                .where(TafseerChunk.is_embedded == 0)
            )
            chunks = result.all()

            if not chunks:
                print("  No unindexed chunks found")
                print("\n  Checking total chunk count...")
                total = session.execute(select(TafseerChunk.id)).all()
                print(f"  Total chunks in database: {len(total)}")

                if len(total) == 0:
                    print("\n  No tafseer data loaded. Run seed_tafseer.py first.")
                else:
                    print("  All chunks already indexed.")
                sys.exit(0)

            print(f"  Found {len(chunks)} chunks to index")

            points = []
            indexed_ids = []

            for i, (chunk, source) in enumerate(chunks):
                # Get content for embedding
                content = chunk.content_en or chunk.content_ar or ""
                if not content:
                    continue

                # Generate embedding
                vector = generate_embedding(embedder, content, dimension)

                # Create point
                point = PointStruct(
                    id=chunk.id,
                    vector=vector,
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
                    }
                )
                points.append(point)
                indexed_ids.append(chunk.id)

                # Batch upsert
                if len(points) >= batch_size:
                    qdrant.upsert(collection_name=collection_name, points=points)
                    print(f"  Indexed {i + 1}/{len(chunks)} chunks")
                    points = []

            # Final batch
            if points:
                qdrant.upsert(collection_name=collection_name, points=points)

            # Update is_embedded flag
            if indexed_ids:
                from sqlalchemy import update
                session.execute(
                    update(TafseerChunk)
                    .where(TafseerChunk.id.in_(indexed_ids))
                    .values(is_embedded=1, embedding_model=os.getenv("EMBEDDING_MODEL", "placeholder"))
                )
                session.commit()

        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print(f"SUCCESS: Indexed {len(indexed_ids)} chunks in {duration:.2f}s")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
