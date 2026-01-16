# RAG Pipeline package
#
# Use lazy imports to avoid requiring all dependencies for individual modules.
# Import specific modules directly when needed:
#   from app.rag.confidence import ConfidenceScorer
#   from app.rag.query_expander import QueryExpander
#   from app.rag.pipeline import RAGPipeline  # requires qdrant_client

__all__ = [
    "RAGPipeline",
    "QueryIntent",
    "RetrievedChunk",
    "Citation",
    "GroundedResponse",
    "ValidationResult",
    "expand_query",
    "QueryExpander",
    "confidence_scorer",
    "ConfidenceScorer",
]


def __getattr__(name):
    """Lazy import to avoid loading heavy dependencies unnecessarily."""
    if name == "RAGPipeline":
        from app.rag.pipeline import RAGPipeline
        return RAGPipeline
    elif name in ("QueryIntent", "RetrievedChunk", "Citation", "GroundedResponse", "ValidationResult"):
        from app.rag import types
        return getattr(types, name)
    elif name in ("expand_query", "QueryExpander"):
        from app.rag import query_expander
        return getattr(query_expander, name)
    elif name in ("confidence_scorer", "ConfidenceScorer"):
        from app.rag import confidence
        return getattr(confidence, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
