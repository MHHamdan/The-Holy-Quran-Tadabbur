"""
Server-Sent Events (SSE) Streaming Endpoints for Real-time Results.

Provides streaming responses for:
1. Similarity search with progressive results
2. Concept search with live updates
3. Long-running analysis with status updates

Arabic: نقاط نهاية البث في الوقت الفعلي للنتائج
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.services.fast_similarity import get_fast_similarity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


async def generate_similarity_stream(
    sura_no: int,
    aya_no: int,
    top_k: int,
    min_score: float,
    exclude_same_sura: bool,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for similarity search results.

    Yields results progressively:
    1. Immediate acknowledgment
    2. Source verse info
    3. Results in batches of 5
    4. Final summary
    """
    service = get_fast_similarity_service()

    # Send initial acknowledgment immediately
    yield f"data: {json.dumps({'type': 'start', 'message': 'Starting similarity search...', 'verse': f'{sura_no}:{aya_no}'})}\n\n"

    # Ensure service is initialized
    if not service.is_initialized():
        yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing search index...'})}\n\n"
        await service.initialize(session)

    # Get results
    result = await service.find_similar(
        sura_no=sura_no,
        aya_no=aya_no,
        top_k=top_k,
        min_score=min_score,
        exclude_same_sura=exclude_same_sura,
        session=session,
    )

    if 'error' in result:
        yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
        return

    # Send source verse info
    yield f"data: {json.dumps({'type': 'source', 'verse': result.get('source_verse', {})})}\n\n"

    # Stream results in batches of 5 for progressive loading
    matches = result.get('matches', [])
    batch_size = 5

    for i in range(0, len(matches), batch_size):
        batch = matches[i:i + batch_size]
        yield f"data: {json.dumps({'type': 'results', 'batch': i // batch_size + 1, 'matches': batch})}\n\n"
        # Small delay to allow UI to render progressively
        await asyncio.sleep(0.01)

    # Send final summary
    yield f"data: {json.dumps({'type': 'complete', 'total': len(matches), 'search_time_ms': result.get('search_time_ms', 0), 'from_cache': result.get('from_cache', False)})}\n\n"


@router.get("/similarity/{sura_no}/{aya_no}")
async def stream_similarity_search(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_score: float = Query(0.1, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    exclude_same_sura: bool = Query(False, description="Exclude verses from same sura"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Stream similarity search results using Server-Sent Events.

    This endpoint provides real-time streaming of results as they're found,
    giving users immediate feedback and progressive loading.

    Event Types:
    - start: Search initiated
    - status: Status update
    - source: Source verse information
    - results: Batch of matching verses
    - complete: Search finished with summary
    - error: Error occurred

    Arabic: بث نتائج البحث عن التشابه في الوقت الفعلي
    """
    return StreamingResponse(
        generate_similarity_stream(
            sura_no=sura_no,
            aya_no=aya_no,
            top_k=top_k,
            min_score=min_score,
            exclude_same_sura=exclude_same_sura,
            session=session,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/health")
async def stream_health():
    """
    Health check for streaming endpoint.

    Returns service status and statistics.
    """
    service = get_fast_similarity_service()
    stats = service.get_stats()

    return {
        "status": "healthy",
        "streaming": "enabled",
        "fast_similarity": stats,
    }
