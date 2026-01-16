"""
Ingestion Pipeline for Knowledge Graph.

Provides:
- Run orchestration with step tracking
- Idempotent record processing
- Hash-based skip for unchanged data
- CLI for pipeline execution
"""

from app.ingest.orchestrator import (
    IngestOrchestrator,
    get_orchestrator,
    StepName,
    StepResult,
)

__all__ = [
    "IngestOrchestrator",
    "get_orchestrator",
    "StepName",
    "StepResult",
]
