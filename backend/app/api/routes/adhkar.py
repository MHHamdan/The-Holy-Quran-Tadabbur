"""
Dhikr Session Tracking API — Phase D.

Public endpoints:
  POST /api/v1/dhikr/sessions  — record a completed session (anonymous, no PII)
  GET  /api/v1/dhikr/stats     — aggregate community stats for the current day

The current app keeps dhikr counts on the device and no longer calls
POST /sessions; it remains only for older installed versions. Rows hold a
date, a category and counts (no id, no IP) and are deleted after
DHIKR_RETENTION_DAYS (see therapy.purge_expired_private_data).

Rate-limited to 20 requests/min per IP.
No authentication required — sessions are intentionally anonymous.
"""
import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.rate_limit import InMemoryRateLimiter, enforce
from app.models.dhikr import DhikrSession

logger = logging.getLogger(__name__)

router = APIRouter()

_dhikr_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60, name="dhikr")


async def dhikr_rate_limit(request: Request) -> None:
    await enforce(_dhikr_limiter, request, "Dhikr")


DHIKR_RETENTION_DAYS = int(os.getenv("DHIKR_RETENTION_DAYS", "30"))


async def purge_expired_dhikr_sessions(db: AsyncSession) -> None:
    cutoff = datetime.utcnow() - timedelta(days=DHIKR_RETENTION_DAYS)
    await db.execute(delete(DhikrSession).where(DhikrSession.created_at < cutoff))


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class DhikrSessionIn(BaseModel):
    session_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    category: Optional[str] = Field(None, max_length=50)
    total_dhikr_completed: int = Field(default=0, ge=0, le=500)
    # A realistic upper bound for one focus session; larger values are abuse of
    # the community counter, not dhikr.
    total_count: int = Field(default=0, ge=0, le=10_000)
    duration_seconds: Optional[int] = Field(default=None, ge=0, le=86_400)


class DhikrSessionOut(BaseModel):
    id: int
    session_date: str
    category: Optional[str]
    total_dhikr_completed: int
    total_count: int
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class DhikrStats(BaseModel):
    sessions_today: int
    counts_today: int
    sessions_alltime: int
    date: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post('/sessions', response_model=DhikrSessionOut, status_code=201,
             dependencies=[Depends(dhikr_rate_limit)])
async def record_session(
    body: DhikrSessionIn,
    db: AsyncSession = Depends(get_async_session),
) -> DhikrSessionOut:
    """Record one completed dhikr focus session."""
    session = DhikrSession(
        session_date=body.session_date,
        category=body.category,
        total_dhikr_completed=body.total_dhikr_completed,
        total_count=body.total_count,
        duration_seconds=body.duration_seconds,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return DhikrSessionOut.model_validate(session)


@router.get('/stats', response_model=DhikrStats)
async def get_stats(db: AsyncSession = Depends(get_async_session)) -> DhikrStats:
    """Return aggregate community dhikr stats for today."""
    today = date.today().isoformat()

    today_row = await db.execute(
        select(func.count(), func.coalesce(func.sum(DhikrSession.total_count), 0))
        .where(DhikrSession.session_date == today)
    )
    sessions_today, counts_today = today_row.one()

    all_row = await db.execute(
        select(func.count()).select_from(DhikrSession)
    )
    sessions_alltime = all_row.scalar_one()

    return DhikrStats(
        sessions_today=sessions_today or 0,
        counts_today=int(counts_today or 0),
        sessions_alltime=sessions_alltime or 0,
        date=today,
    )
