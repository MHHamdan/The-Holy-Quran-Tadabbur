"""
Performance Monitoring and Metrics Endpoints.

Provides real-time performance metrics for:
1. Service initialization status
2. Cache statistics
3. Database connection pool status
4. Response time tracking

Arabic: نقاط نهاية مراقبة الأداء والمقاييس
"""

import time
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_async_session, async_engine
from app.services.fast_similarity import get_fast_similarity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])

# Track response times
_response_times: Dict[str, list] = {}
_max_samples = 100


def record_response_time(endpoint: str, time_ms: float):
    """Record response time for an endpoint."""
    if endpoint not in _response_times:
        _response_times[endpoint] = []
    _response_times[endpoint].append(time_ms)
    # Keep only last N samples
    if len(_response_times[endpoint]) > _max_samples:
        _response_times[endpoint] = _response_times[endpoint][-_max_samples:]


def get_memory_usage() -> Dict[str, Any]:
    """Get memory usage from /proc/self/status (Linux)."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    rss_kb = int(line.split()[1])
                    return {"rss_mb": round(rss_kb / 1024, 2)}
    except:
        pass
    return {"rss_mb": 0}


@router.get("/metrics")
async def get_performance_metrics(
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get comprehensive performance metrics.

    Returns:
    - Service status
    - Cache statistics
    - Database pool status
    - Memory usage
    - Response time statistics

    Arabic: الحصول على مقاييس الأداء الشاملة
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "database": {},
        "memory": {},
        "response_times": {},
    }

    # Fast Similarity Service status
    fast_sim = get_fast_similarity_service()
    metrics["services"]["fast_similarity"] = fast_sim.get_stats()

    # Database connection pool status
    pool = async_engine.pool
    metrics["database"] = {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }

    # Test database latency
    start = time.time()
    await session.execute(text("SELECT 1"))
    db_latency = (time.time() - start) * 1000
    metrics["database"]["latency_ms"] = round(db_latency, 2)

    # Memory usage (simple Linux method)
    metrics["memory"] = get_memory_usage()

    # Response time statistics
    for endpoint, times in _response_times.items():
        if times:
            metrics["response_times"][endpoint] = {
                "avg_ms": round(sum(times) / len(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "samples": len(times),
            }

    return metrics


@router.get("/db-pool")
async def get_db_pool_status() -> Dict[str, Any]:
    """
    Get database connection pool status.

    Arabic: حالة مجموعة اتصالات قاعدة البيانات
    """
    pool = async_engine.pool
    return {
        "status": "healthy",
        "pool_size": pool.size(),
        "max_overflow": async_engine.pool._max_overflow,
        "checked_out": pool.checkedout(),
        "checked_in": pool.checkedin(),
        "overflow": pool.overflow(),
        "invalid": pool._invalidated,
    }


@router.get("/services")
async def get_services_status() -> Dict[str, Any]:
    """
    Get status of all initialized services.

    Arabic: حالة جميع الخدمات المُهيأة
    """
    services = {}

    # Fast Similarity Service
    fast_sim = get_fast_similarity_service()
    services["fast_similarity"] = {
        "initialized": fast_sim.is_initialized(),
        "stats": fast_sim.get_stats() if fast_sim.is_initialized() else None,
    }

    return {
        "status": "healthy",
        "services": services,
    }


@router.post("/benchmark/similarity/{sura_no}/{aya_no}")
async def benchmark_similarity(
    sura_no: int,
    aya_no: int,
    iterations: int = 10,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Benchmark similarity search performance.

    Runs multiple iterations and reports statistics.

    Arabic: اختبار أداء البحث عن التشابه
    """
    service = get_fast_similarity_service()

    if not service.is_initialized():
        await service.initialize(session)

    times = []
    for _ in range(iterations):
        start = time.time()
        await service.find_similar(
            sura_no=sura_no,
            aya_no=aya_no,
            top_k=20,
            min_score=0.1,
            session=session,
        )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    return {
        "verse": f"{sura_no}:{aya_no}",
        "iterations": iterations,
        "avg_ms": round(sum(times) / len(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "p50_ms": round(sorted(times)[len(times) // 2], 2),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2),
        "times": [round(t, 2) for t in times],
    }
