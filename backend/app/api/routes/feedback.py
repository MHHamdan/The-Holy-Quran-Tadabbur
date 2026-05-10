"""
User Feedback API — Phase G.

Public endpoint: POST /api/v1/feedback
Admin endpoints:  GET/PATCH /api/v1/admin/feedback[/{id}]
                  GET /api/v1/admin/feedback/stats

Rate-limited to 10 submissions per minute per IP (public).
Admin endpoints require X-Admin-Token header (same mechanism as review workflow).
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.auth import require_admin, AdminUser
from app.core.rate_limit import feedback_rate_limit
from app.models.feedback import (
    UserFeedback,
    FeedbackCategory,
    FeedbackStatus,
    CATEGORY_PRIORITY,
    CATEGORY_LABELS,
)

router = APIRouter()


# =============================================================================
# REQUEST / RESPONSE SCHEMAS
# =============================================================================

class SubmitFeedbackRequest(BaseModel):
    category: FeedbackCategory = Field(..., description="Feedback category")
    message: str = Field(..., min_length=10, max_length=2000, description="Feedback message")
    entity_type: Optional[str] = Field(None, max_length=50, description="Content type (story, tafsir, concept, …)")
    entity_id: Optional[str] = Field(None, max_length=200, description="ID of the specific piece of content")
    page_url: Optional[str] = Field(None, max_length=500, description="URL where the issue was found")

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must not be blank.")
        return v.strip()


class FeedbackResponse(BaseModel):
    ok: bool = True
    id: int
    category: str
    status: str
    priority: int
    message_en: str
    message_ar: str


class FeedbackItem(BaseModel):
    id: int
    category: str
    category_label_en: str
    category_label_ar: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    page_url: Optional[str]
    message: str
    status: str
    priority: int
    admin_notes: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    ok: bool = True
    items: List[FeedbackItem]
    total: int
    page: int
    page_size: int


class FeedbackStatsResponse(BaseModel):
    ok: bool = True
    total: int
    by_status: dict
    by_category: dict
    open_high_priority: int


class UpdateFeedbackRequest(BaseModel):
    status: Optional[FeedbackStatus] = None
    admin_notes: Optional[str] = Field(None, max_length=2000)


# =============================================================================
# HELPERS
# =============================================================================

def _to_item(fb: UserFeedback) -> FeedbackItem:
    labels = CATEGORY_LABELS.get(fb.category, {"en": fb.category, "ar": fb.category})
    return FeedbackItem(
        id=fb.id,
        category=fb.category,
        category_label_en=labels["en"],
        category_label_ar=labels["ar"],
        entity_type=fb.entity_type,
        entity_id=fb.entity_id,
        page_url=fb.page_url,
        message=fb.message,
        status=fb.status,
        priority=fb.priority,
        admin_notes=fb.admin_notes,
        created_at=fb.created_at.isoformat(),
        updated_at=fb.updated_at.isoformat(),
        resolved_at=fb.resolved_at.isoformat() if fb.resolved_at else None,
    )


# =============================================================================
# PUBLIC ENDPOINT
# =============================================================================

@router.post(
    "",
    response_model=FeedbackResponse,
    summary="Submit user feedback",
    dependencies=[Depends(feedback_rate_limit)],
)
async def submit_feedback(
    body: SubmitFeedbackRequest,
    db: AsyncSession = Depends(get_async_session),
) -> FeedbackResponse:
    """
    Submit feedback about content quality, accuracy, or UI issues.
    No authentication required. Rate-limited to 10/minute per IP.
    """
    priority = CATEGORY_PRIORITY.get(body.category, 5)
    fb = UserFeedback(
        category=body.category,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        page_url=body.page_url,
        message=body.message,
        status=FeedbackStatus.OPEN,
        priority=priority,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)

    labels = CATEGORY_LABELS.get(body.category, {"en": body.category, "ar": body.category})
    return FeedbackResponse(
        id=fb.id,
        category=fb.category,
        status=fb.status,
        priority=fb.priority,
        message_en=f"Thank you. Your {labels['en']} report has been received and will be reviewed.",
        message_ar=f"شكراً لك. تم استلام تقريرك بخصوص ({labels['ar']}) وسيتم مراجعته.",
    )


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.get(
    "/admin",
    response_model=FeedbackListResponse,
    summary="List feedback (admin)",
)
async def list_feedback(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> FeedbackListResponse:
    """List feedback submissions, sorted by priority then newest-first (admin)."""
    q = select(UserFeedback)
    if status:
        q = q.where(UserFeedback.status == status)
    if category:
        q = q.where(UserFeedback.category == category)
    q = q.order_by(UserFeedback.priority.asc(), UserFeedback.created_at.desc())

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    rows = result.scalars().all()

    return FeedbackListResponse(
        items=[_to_item(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/admin/stats",
    response_model=FeedbackStatsResponse,
    summary="Feedback statistics (admin)",
)
async def feedback_stats(
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> FeedbackStatsResponse:
    """Aggregate counts by status and category for the admin dashboard."""
    total_result = await db.execute(select(func.count()).select_from(UserFeedback))
    total = total_result.scalar_one()

    by_status_result = await db.execute(
        select(UserFeedback.status, func.count().label("n"))
        .group_by(UserFeedback.status)
    )
    by_status = {row.status: row.n for row in by_status_result}

    by_category_result = await db.execute(
        select(UserFeedback.category, func.count().label("n"))
        .group_by(UserFeedback.category)
    )
    by_category = {row.category: row.n for row in by_category_result}

    high_priority_result = await db.execute(
        select(func.count()).select_from(UserFeedback).where(
            UserFeedback.status == FeedbackStatus.OPEN,
            UserFeedback.priority <= 2,
        )
    )
    open_high_priority = high_priority_result.scalar_one()

    return FeedbackStatsResponse(
        total=total,
        by_status=by_status,
        by_category=by_category,
        open_high_priority=open_high_priority,
    )


@router.patch(
    "/admin/{feedback_id}",
    response_model=FeedbackItem,
    summary="Update feedback status or notes (admin)",
)
async def update_feedback(
    feedback_id: int,
    body: UpdateFeedbackRequest,
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
) -> FeedbackItem:
    """Update status and/or admin notes for a feedback item."""
    result = await db.execute(
        select(UserFeedback).where(UserFeedback.id == feedback_id)
    )
    fb = result.scalar_one_or_none()
    if fb is None:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found.")

    if body.status is not None:
        fb.status = body.status
        if body.status in (FeedbackStatus.RESOLVED, FeedbackStatus.DISMISSED):
            fb.resolved_at = datetime.utcnow()
    if body.admin_notes is not None:
        fb.admin_notes = body.admin_notes

    fb.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(fb)
    return _to_item(fb)
