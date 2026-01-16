"""
Knowledge Graph module using SurrealDB.

Provides:
- Graph storage for Quranic entities and relationships
- Vector-to-graph bridge for hybrid retrieval
- Ingestion tracking for idempotent pipelines
"""

from app.kg.client import get_kg_client, KGClient
from app.kg.models import (
    Ayah,
    TafsirChunk,
    StoryCluster,
    StoryEvent,
    Person,
    Place,
    ConceptTag,
    IngestRun,
    IngestStep,
    EmbeddingRecord,
)

__all__ = [
    "get_kg_client",
    "KGClient",
    "Ayah",
    "TafsirChunk",
    "StoryCluster",
    "StoryEvent",
    "Person",
    "Place",
    "ConceptTag",
    "IngestRun",
    "IngestStep",
    "EmbeddingRecord",
]
