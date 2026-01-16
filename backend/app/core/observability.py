"""
Observability module for Tadabbur.

Provides:
1. Structured logging
2. Request tracing
3. Metrics collection
4. Audit logging helpers
"""
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
from dataclasses import dataclass, field, asdict
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

# Context variable for request tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
request_start_var: ContextVar[float] = ContextVar("request_start", default=0.0)


@dataclass
class RequestContext:
    """Context for a single request."""
    request_id: str
    start_time: float
    path: str = ""
    method: str = ""
    user_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class StructuredLogger:
    """
    Structured JSON logger for consistent log format.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def _format_log(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> str:
        """Format log entry as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "request_id": request_id_var.get(""),
        }
        log_entry.update(kwargs)
        return json.dumps(log_entry, default=str)

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))


class MetricsCollector:
    """
    Simple in-memory metrics collector.

    In production, integrate with Prometheus, StatsD, or similar.
    """

    def __init__(self):
        self._metrics: Dict[str, list] = {}
        self._counters: Dict[str, int] = {}

    def increment(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter."""
        key = self._make_key(name, labels or {})
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge value."""
        key = self._make_key(name, labels or {})
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(MetricPoint(name=name, value=value, labels=labels or {}))

        # Keep only last 1000 points per metric
        if len(self._metrics[key]) > 1000:
            self._metrics[key] = self._metrics[key][-1000:]

    def histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value (for latencies, sizes, etc.)."""
        # Simple implementation - just store as gauge
        self.gauge(name, value, labels)

    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create unique key from name and labels."""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_str}"

    def get_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        return dict(self._counters)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {
            "counters": dict(self._counters),
            "gauges": {}
        }

        for key, points in self._metrics.items():
            if points:
                values = [p.value for p in points]
                summary["gauges"][key] = {
                    "count": len(values),
                    "last": values[-1],
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }

        return summary


# Global metrics collector
metrics = MetricsCollector()


class AuditLogger:
    """
    Async audit logger for database audit trail.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_rag_query(
        self,
        query: str,
        intent: str,
        chunks_retrieved: int,
        confidence: float,
        duration_ms: int,
        user_id: Optional[str] = None,
    ):
        """Log a RAG query for audit."""
        from app.models.audit import AuditLog

        log = AuditLog(
            action="rag_query",
            actor=f"user:{user_id}" if user_id else "anonymous",
            entity_type="rag_query",
            message=f"Query: {query[:100]}...",
            details={
                "query": query[:500],
                "intent": intent,
                "chunks_retrieved": chunks_retrieved,
                "confidence": confidence,
            },
            status="success",
            duration_ms=duration_ms,
            request_id=request_id_var.get(""),
        )
        self.session.add(log)
        await self.session.commit()

        # Record metrics
        metrics.increment("rag_queries_total", labels={"intent": intent})
        metrics.histogram("rag_query_duration_ms", duration_ms, labels={"intent": intent})
        metrics.histogram("rag_query_confidence", confidence, labels={"intent": intent})
        metrics.gauge("rag_chunks_retrieved", chunks_retrieved, labels={"intent": intent})

    async def log_citation_validation(
        self,
        query_id: str,
        valid_count: int,
        invalid_count: int,
        coverage_score: float,
        is_valid: bool,
    ):
        """Log citation validation result."""
        from app.models.audit import AuditLog

        log = AuditLog(
            action="citation_validation",
            actor="system",
            entity_type="rag_response",
            entity_id=query_id,
            message=f"Valid: {valid_count}, Invalid: {invalid_count}",
            details={
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "coverage_score": coverage_score,
                "is_valid": is_valid,
            },
            status="success" if is_valid else "warning",
            request_id=request_id_var.get(""),
        )
        self.session.add(log)
        await self.session.commit()

        # Record metrics
        metrics.increment("citation_validations_total", labels={"valid": str(is_valid).lower()})
        metrics.histogram("citation_coverage_score", coverage_score)

    async def log_translation(
        self,
        verse_reference: str,
        translator: str,
        confidence: int,
        needs_review: bool,
    ):
        """Log a translation operation."""
        from app.models.audit import AuditLog

        log = AuditLog(
            action="translation_create",
            actor="system:translation_service",
            entity_type="translation",
            entity_id=verse_reference,
            message=f"Translated {verse_reference} via {translator}",
            details={
                "verse_reference": verse_reference,
                "translator": translator,
                "confidence": confidence,
                "needs_review": needs_review,
            },
            status="warning" if needs_review else "success",
            request_id=request_id_var.get(""),
        )
        self.session.add(log)
        await self.session.commit()

        metrics.increment("translations_total", labels={"translator": translator})
        metrics.histogram("translation_confidence", confidence, labels={"translator": translator})

    async def log_data_ingestion(
        self,
        source_id: str,
        entity_type: str,
        count: int,
        duration_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """Log a data ingestion operation."""
        from app.models.audit import AuditLog

        log = AuditLog(
            action="data_import",
            actor="system:ingestion",
            entity_type=entity_type,
            message=f"Ingested {count} {entity_type} from {source_id}",
            details={
                "source_id": source_id,
                "count": count,
            },
            status=status,
            error_message=error_message,
            duration_ms=duration_ms,
            request_id=request_id_var.get(""),
        )
        self.session.add(log)
        await self.session.commit()

        metrics.increment("data_ingestion_total", labels={"source": source_id, "type": entity_type})
        metrics.gauge("data_ingestion_count", count, labels={"source": source_id, "type": entity_type})


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]


def trace_request(func: Callable):
    """Decorator to trace async request handlers."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request_id = generate_request_id()
        start_time = time.time()

        # Set context
        request_id_var.set(request_id)
        request_start_var.set(start_time)

        try:
            result = await func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log success
            metrics.increment("requests_total", labels={"status": "success"})
            metrics.histogram("request_duration_ms", duration_ms)

            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Log failure
            metrics.increment("requests_total", labels={"status": "error"})
            metrics.histogram("request_duration_ms", duration_ms)

            raise

    return wrapper


# Create logger instances
rag_logger = StructuredLogger("tadabbur.rag")
api_logger = StructuredLogger("tadabbur.api")
ingestion_logger = StructuredLogger("tadabbur.ingestion")
