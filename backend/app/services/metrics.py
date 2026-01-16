"""
Prometheus Metrics Service for Monitoring.

Provides metrics for:
- RAG query performance (latency, cache hits/misses)
- Search operations (vector, keyword, hybrid)
- Cache utilization (hit rate, size, TTL)
- Model inference (reranker, embeddings)

Integration with Grafana dashboards for visualization.

Arabic: خدمة المقاييس لـ Prometheus
"""
import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import prometheus_client
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        multiprocess,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics will be disabled.")


# Custom registry for metrics
if PROMETHEUS_AVAILABLE:
    REGISTRY = CollectorRegistry()

    # =============================================================================
    # RAG Query Metrics
    # =============================================================================

    RAG_QUERY_TOTAL = Counter(
        "rag_query_total",
        "Total number of RAG queries",
        ["language", "intent", "cached"],
        registry=REGISTRY,
    )

    RAG_QUERY_LATENCY = Histogram(
        "rag_query_latency_seconds",
        "RAG query latency in seconds",
        ["language", "cached"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        registry=REGISTRY,
    )

    RAG_QUERY_CONFIDENCE = Histogram(
        "rag_query_confidence",
        "RAG response confidence scores",
        ["intent"],
        buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        registry=REGISTRY,
    )

    # =============================================================================
    # Cache Metrics
    # =============================================================================

    CACHE_HITS = Counter(
        "cache_hits_total",
        "Total cache hits",
        ["cache_type"],  # rag, tafseer, embeddings
        registry=REGISTRY,
    )

    CACHE_MISSES = Counter(
        "cache_misses_total",
        "Total cache misses",
        ["cache_type"],
        registry=REGISTRY,
    )

    CACHE_HIT_RATE = Gauge(
        "cache_hit_rate",
        "Current cache hit rate",
        ["cache_type"],
        registry=REGISTRY,
    )

    CACHE_SIZE = Gauge(
        "cache_size_items",
        "Number of items in cache",
        ["cache_type"],
        registry=REGISTRY,
    )

    # =============================================================================
    # Search Metrics
    # =============================================================================

    SEARCH_TOTAL = Counter(
        "search_total",
        "Total search operations",
        ["search_type"],  # vector, keyword, hybrid, semantic
        registry=REGISTRY,
    )

    SEARCH_LATENCY = Histogram(
        "search_latency_seconds",
        "Search operation latency",
        ["search_type"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
        registry=REGISTRY,
    )

    SEARCH_RESULTS_COUNT = Histogram(
        "search_results_count",
        "Number of results returned by search",
        ["search_type"],
        buckets=[0, 1, 5, 10, 20, 50, 100],
        registry=REGISTRY,
    )

    # =============================================================================
    # Reranker Metrics
    # =============================================================================

    RERANK_TOTAL = Counter(
        "rerank_total",
        "Total reranking operations",
        ["method"],  # cross_encoder, keyword_overlap
        registry=REGISTRY,
    )

    RERANK_LATENCY = Histogram(
        "rerank_latency_seconds",
        "Reranking latency",
        ["method"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
        registry=REGISTRY,
    )

    # =============================================================================
    # Embedding Metrics
    # =============================================================================

    EMBEDDING_TOTAL = Counter(
        "embedding_total",
        "Total embedding computations",
        ["model"],
        registry=REGISTRY,
    )

    EMBEDDING_LATENCY = Histogram(
        "embedding_latency_seconds",
        "Embedding computation latency",
        ["model"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
        registry=REGISTRY,
    )

    # =============================================================================
    # System Info
    # =============================================================================

    SYSTEM_INFO = Info(
        "tadabbur_system",
        "System information",
        registry=REGISTRY,
    )


class MetricsCollector:
    """
    Centralized metrics collection for the application.

    Usage:
        metrics = MetricsCollector()

        # Record RAG query
        metrics.record_rag_query(
            language="en",
            intent="verse_meaning",
            latency=1.5,
            cached=False,
            confidence=0.85
        )

        # Record cache operation
        metrics.record_cache_hit("rag")
        metrics.record_cache_miss("rag")
    """

    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE

    def record_rag_query(
        self,
        language: str,
        intent: str,
        latency: float,
        cached: bool,
        confidence: float,
    ):
        """Record metrics for a RAG query."""
        if not self.enabled:
            return

        cached_str = "true" if cached else "false"

        RAG_QUERY_TOTAL.labels(
            language=language,
            intent=intent,
            cached=cached_str,
        ).inc()

        RAG_QUERY_LATENCY.labels(
            language=language,
            cached=cached_str,
        ).observe(latency)

        RAG_QUERY_CONFIDENCE.labels(intent=intent).observe(confidence)

    def record_cache_hit(self, cache_type: str):
        """Record a cache hit."""
        if not self.enabled:
            return
        CACHE_HITS.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record a cache miss."""
        if not self.enabled:
            return
        CACHE_MISSES.labels(cache_type=cache_type).inc()

    def update_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Update the current cache hit rate."""
        if not self.enabled:
            return
        CACHE_HIT_RATE.labels(cache_type=cache_type).set(hit_rate)

    def update_cache_size(self, cache_type: str, size: int):
        """Update the cache size."""
        if not self.enabled:
            return
        CACHE_SIZE.labels(cache_type=cache_type).set(size)

    def record_search(
        self,
        search_type: str,
        latency: float,
        results_count: int,
    ):
        """Record metrics for a search operation."""
        if not self.enabled:
            return

        SEARCH_TOTAL.labels(search_type=search_type).inc()
        SEARCH_LATENCY.labels(search_type=search_type).observe(latency)
        SEARCH_RESULTS_COUNT.labels(search_type=search_type).observe(results_count)

    def record_rerank(self, method: str, latency: float):
        """Record metrics for a reranking operation."""
        if not self.enabled:
            return

        RERANK_TOTAL.labels(method=method).inc()
        RERANK_LATENCY.labels(method=method).observe(latency)

    def record_embedding(self, model: str, latency: float):
        """Record metrics for an embedding computation."""
        if not self.enabled:
            return

        EMBEDDING_TOTAL.labels(model=model).inc()
        EMBEDDING_LATENCY.labels(model=model).observe(latency)

    def set_system_info(self, info: Dict[str, str]):
        """Set system information labels."""
        if not self.enabled:
            return
        SYSTEM_INFO.info(info)

    @contextmanager
    def time_operation(self, operation_type: str, labels: Dict[str, str] = None):
        """
        Context manager to time an operation.

        Usage:
            with metrics.time_operation("rag_query", {"language": "en"}):
                # do work
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            latency = time.perf_counter() - start
            if operation_type == "rag_query" and labels:
                self.record_rag_query(
                    language=labels.get("language", "unknown"),
                    intent=labels.get("intent", "unknown"),
                    latency=latency,
                    cached=labels.get("cached", False),
                    confidence=labels.get("confidence", 0.0),
                )
            elif operation_type == "search" and labels:
                self.record_search(
                    search_type=labels.get("search_type", "unknown"),
                    latency=latency,
                    results_count=labels.get("results_count", 0),
                )

    def get_metrics_output(self) -> bytes:
        """Generate Prometheus metrics output."""
        if not self.enabled:
            return b"# Prometheus metrics not available\n"
        return generate_latest(REGISTRY)

    def get_content_type(self) -> str:
        """Get the content type for metrics endpoint."""
        if not self.enabled:
            return "text/plain"
        return CONTENT_TYPE_LATEST


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the metrics collector singleton."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def metrics_endpoint_handler():
    """Handler for /metrics endpoint."""
    metrics = get_metrics()
    return metrics.get_metrics_output(), metrics.get_content_type()


# Decorator for timing functions
def timed_operation(operation_type: str, **extra_labels):
    """
    Decorator to automatically time and record metrics for a function.

    Usage:
        @timed_operation("search", search_type="vector")
        async def vector_search(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics()
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency = time.perf_counter() - start
                if operation_type == "search":
                    # Try to get results count from return value
                    results_count = len(result) if isinstance(result, (list, tuple)) else 0
                    metrics.record_search(
                        search_type=extra_labels.get("search_type", "unknown"),
                        latency=latency,
                        results_count=results_count,
                    )
                elif operation_type == "rerank":
                    metrics.record_rerank(
                        method=extra_labels.get("method", "unknown"),
                        latency=latency,
                    )
                elif operation_type == "embedding":
                    metrics.record_embedding(
                        model=extra_labels.get("model", "unknown"),
                        latency=latency,
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics()
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency = time.perf_counter() - start
                if operation_type == "rerank":
                    metrics.record_rerank(
                        method=extra_labels.get("method", "unknown"),
                        latency=latency,
                    )

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
