"""
Admin API Routes - Verification Workflow Management.

All endpoints require admin authentication via Bearer token.

Endpoints:
- GET /verification/queue: List pending verification items
- GET /verification/queue/{id}: Get single item details
- POST /verification/flag: Flag content for review
- POST /verification/queue/{id}/assign: Assign reviewer
- POST /verification/queue/{id}/review: Submit review decision
- GET /verification/stats: Get queue statistics
- POST /verification/queue/{id}/ai-analyze: Trigger AI analysis
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.auth import require_admin, AdminUser
from app.core.responses import APIError, ErrorCode, get_request_id
from app.verify.workflow import VerificationWorkflow
from app.verify.ai_assistant import get_ai_assistant, AIAnalysisResult
from app.models.verification import (
    FlagType,
    VerificationStatus,
    ReviewDecision,
    EntityType,
    FLAG_TYPE_TRANSLATIONS,
    STATUS_TRANSLATIONS,
    DECISION_TRANSLATIONS,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class FlagContentRequest(BaseModel):
    """Request to flag content for verification."""
    entity_type: str = Field(..., description="Type of entity (concept, story, etc.)")
    entity_id: str = Field(..., description="ID of the entity")
    flag_type: str = Field(..., description="Type of flag (accuracy, source, etc.)")
    flag_reason: Optional[str] = Field(None, description="Reason for flagging (English)")
    flag_reason_ar: Optional[str] = Field(None, description="Reason for flagging (Arabic)")
    context_snapshot: Optional[Dict[str, Any]] = Field(None, description="Current state")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1=highest)")


class AssignReviewerRequest(BaseModel):
    """Request to assign a reviewer."""
    reviewer_id: str = Field(..., description="ID of the reviewer to assign")


class SubmitReviewRequest(BaseModel):
    """Request to submit a review decision."""
    decision: str = Field(..., description="Review decision (approve, reject, revise, defer, escalate)")
    notes: Optional[str] = Field(None, description="Review notes (English)")
    notes_ar: Optional[str] = Field(None, description="Review notes (Arabic)")
    action_taken: Optional[str] = Field(None, description="Description of action taken")
    action_details: Optional[Dict[str, Any]] = Field(None, description="Action details")


class BulkPriorityRequest(BaseModel):
    """Request to update priority for multiple items."""
    item_ids: List[int] = Field(..., description="List of item IDs")
    priority: int = Field(..., ge=1, le=10, description="New priority")


class QueueItemResponse(BaseModel):
    """Response for a queue item."""
    id: int
    entity_type: str
    entity_id: str
    flagged_by: str
    flagged_at: Optional[str] = None
    flag_type: str
    flag_type_label: Dict[str, str] = {}
    flag_reason: Optional[str] = None
    status: str
    status_label: Dict[str, str] = {}
    priority: int
    assigned_to: Optional[str] = None
    assigned_at: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_suggestion: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[str] = None


class QueueItemDetailResponse(QueueItemResponse):
    """Detailed response including snapshots and AI analysis."""
    context_snapshot: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None


class QueueListResponse(BaseModel):
    """Response for queue listing."""
    items: List[QueueItemResponse]
    total: int
    offset: int
    limit: int


class StatsResponse(BaseModel):
    """Response for queue statistics."""
    total: int
    pending: int
    in_review: int
    approved: int
    rejected: int
    deferred: int
    needs_info: int
    avg_review_time_hours: float
    by_flag_type: Dict[str, int]
    by_entity_type: Dict[str, int]


class AIAnalysisResponse(BaseModel):
    """Response for AI analysis."""
    confidence: float
    issues_found: List[str]
    issue_category: str
    suggestion: str
    suggestion_ar: str
    evidence_assessment: str
    evidence_assessment_ar: str
    recommended_action: str
    latency_ms: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_queue_item(item, include_details: bool = False) -> dict:
    """Format a queue item for response."""
    result = {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "flagged_by": item.flagged_by,
        "flagged_at": item.flagged_at.isoformat() if item.flagged_at else None,
        "flag_type": item.flag_type,
        "flag_type_label": FLAG_TYPE_TRANSLATIONS.get(item.flag_type, {}),
        "flag_reason": item.flag_reason,
        "status": item.status,
        "status_label": STATUS_TRANSLATIONS.get(item.status, {}),
        "priority": item.priority,
        "assigned_to": item.assigned_to,
        "assigned_at": item.assigned_at.isoformat() if item.assigned_at else None,
        "ai_confidence": item.ai_confidence,
        "ai_suggestion": item.ai_suggestion,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "review_decision": item.review_decision,
        "review_notes": item.review_notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

    if include_details:
        result.update({
            "context_snapshot": item.context_snapshot,
            "ai_analysis": item.ai_analysis,
            "action_taken": item.action_taken,
            "action_details": item.action_details,
        })

    return result


# =============================================================================
# PUBLIC ENDPOINTS (No auth required for flagging)
# =============================================================================

@router.post("/flag", response_model=QueueItemResponse)
async def flag_content(
    request: Request,
    body: FlagContentRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Flag content for verification review.

    This endpoint is public to allow users to report issues.
    The flagged item will be added to the admin verification queue.
    """
    request_id = get_request_id(request)

    # Validate entity type
    valid_entity_types = [e.value for e in EntityType]
    if body.entity_type not in valid_entity_types:
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en=f"Invalid entity_type. Must be one of: {', '.join(valid_entity_types)}",
            message_ar=f"نوع الكيان غير صالح",
            request_id=request_id,
            status_code=400,
        )

    # Validate flag type
    valid_flag_types = [f.value for f in FlagType]
    if body.flag_type not in valid_flag_types:
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en=f"Invalid flag_type. Must be one of: {', '.join(valid_flag_types)}",
            message_ar=f"نوع العلم غير صالح",
            request_id=request_id,
            status_code=400,
        )

    workflow = VerificationWorkflow(session)

    item = await workflow.flag_content(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        flag_type=body.flag_type,
        flagged_by="user",  # In production, extract from auth token
        flag_reason=body.flag_reason,
        flag_reason_ar=body.flag_reason_ar,
        context_snapshot=body.context_snapshot,
        priority=body.priority,
    )

    return _format_queue_item(item)


# =============================================================================
# ADMIN ENDPOINTS (Auth required)
# =============================================================================

@router.get("/verification/queue", response_model=QueueListResponse)
async def get_verification_queue(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    flag_type: Optional[str] = Query(None, description="Filter by flag type"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get items from the verification queue.

    Requires admin authentication.
    Returns paginated list of queue items sorted by priority and creation date.
    """
    workflow = VerificationWorkflow(session)

    items, total = await workflow.get_queue(
        status=status,
        entity_type=entity_type,
        flag_type=flag_type,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )

    return QueueListResponse(
        items=[_format_queue_item(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/verification/queue/{item_id}", response_model=QueueItemDetailResponse)
async def get_queue_item(
    request: Request,
    item_id: int,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get detailed information for a single queue item.

    Includes context snapshot and AI analysis details.
    """
    request_id = get_request_id(request)
    workflow = VerificationWorkflow(session)

    item = await workflow.get_item(item_id)
    if not item:
        raise APIError(
            code=ErrorCode.NOT_FOUND,
            message_en=f"Queue item {item_id} not found",
            message_ar=f"لم يتم العثور على العنصر {item_id}",
            request_id=request_id,
            status_code=404,
        )

    return _format_queue_item(item, include_details=True)


@router.post("/verification/queue/{item_id}/assign", response_model=QueueItemResponse)
async def assign_reviewer(
    request: Request,
    item_id: int,
    body: AssignReviewerRequest,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Assign a reviewer to a queue item.

    Changes item status to 'in_review'.
    """
    request_id = get_request_id(request)
    workflow = VerificationWorkflow(session)

    item = await workflow.assign_reviewer(item_id, body.reviewer_id)
    if not item:
        raise APIError(
            code=ErrorCode.NOT_FOUND,
            message_en=f"Queue item {item_id} not found",
            message_ar=f"لم يتم العثور على العنصر {item_id}",
            request_id=request_id,
            status_code=404,
        )

    return _format_queue_item(item)


@router.post("/verification/queue/{item_id}/review", response_model=QueueItemResponse)
async def submit_review(
    request: Request,
    item_id: int,
    body: SubmitReviewRequest,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Submit a review decision for a queue item.

    Valid decisions: approve, reject, revise, defer, escalate
    """
    request_id = get_request_id(request)

    # Validate decision
    valid_decisions = [d.value for d in ReviewDecision]
    if body.decision not in valid_decisions:
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}",
            message_ar=f"القرار غير صالح",
            request_id=request_id,
            status_code=400,
        )

    workflow = VerificationWorkflow(session)

    item = await workflow.submit_review(
        item_id=item_id,
        reviewer_id=admin.user_id,
        decision=body.decision,
        notes=body.notes,
        notes_ar=body.notes_ar,
        action_taken=body.action_taken,
        action_details=body.action_details,
    )

    if not item:
        raise APIError(
            code=ErrorCode.NOT_FOUND,
            message_en=f"Queue item {item_id} not found",
            message_ar=f"لم يتم العثور على العنصر {item_id}",
            request_id=request_id,
            status_code=404,
        )

    return _format_queue_item(item)


@router.get("/verification/stats", response_model=StatsResponse)
async def get_verification_stats(
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verification queue statistics.

    Returns counts by status, flag type, and entity type.
    Also includes average review time.
    """
    workflow = VerificationWorkflow(session)
    stats = await workflow.get_stats()

    return StatsResponse(
        total=stats.total,
        pending=stats.pending,
        in_review=stats.in_review,
        approved=stats.approved,
        rejected=stats.rejected,
        deferred=stats.deferred,
        needs_info=stats.needs_info,
        avg_review_time_hours=stats.avg_review_time_hours,
        by_flag_type=stats.by_flag_type,
        by_entity_type=stats.by_entity_type,
    )


@router.post("/verification/queue/{item_id}/ai-analyze", response_model=AIAnalysisResponse)
async def trigger_ai_analysis(
    request: Request,
    item_id: int,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Trigger AI analysis for a queue item.

    The AI assistant will analyze the flagged content and provide:
    - Confidence score
    - List of issues found
    - Suggested corrections
    - Recommended action
    """
    request_id = get_request_id(request)
    workflow = VerificationWorkflow(session)

    # Get the item
    item = await workflow.get_item(item_id)
    if not item:
        raise APIError(
            code=ErrorCode.NOT_FOUND,
            message_en=f"Queue item {item_id} not found",
            message_ar=f"لم يتم العثور على العنصر {item_id}",
            request_id=request_id,
            status_code=404,
        )

    # Run AI analysis
    ai_assistant = get_ai_assistant()
    result = await ai_assistant.analyze_content(
        entity_type=item.entity_type,
        entity_id=item.entity_id,
        flag_type=item.flag_type,
        flag_reason=item.flag_reason or "",
        content=item.context_snapshot or {},
    )

    # Update the item with AI results
    item.ai_confidence = result.confidence
    item.ai_suggestion = result.suggestion
    item.ai_suggestion_ar = result.suggestion_ar
    item.ai_analysis = result.to_dict()
    await session.commit()

    return AIAnalysisResponse(
        confidence=result.confidence,
        issues_found=result.issues_found,
        issue_category=result.issue_category.value,
        suggestion=result.suggestion,
        suggestion_ar=result.suggestion_ar,
        evidence_assessment=result.evidence_assessment,
        evidence_assessment_ar=result.evidence_assessment_ar,
        recommended_action=result.recommended_action,
        latency_ms=result.latency_ms,
    )


@router.get("/verification/my-assignments")
async def get_my_assignments(
    request: Request,
    include_completed: bool = Query(False, description="Include completed reviews"),
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verification items assigned to the current admin.
    """
    workflow = VerificationWorkflow(session)
    items = await workflow.get_my_assignments(
        reviewer_id=admin.user_id,
        include_completed=include_completed,
    )

    return {
        "items": [_format_queue_item(item) for item in items],
        "total": len(items),
    }


@router.post("/verification/bulk-priority")
async def update_bulk_priority(
    request: Request,
    body: BulkPriorityRequest,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update priority for multiple queue items.
    """
    workflow = VerificationWorkflow(session)
    updated_count = await workflow.bulk_update_priority(
        item_ids=body.item_ids,
        priority=body.priority,
    )

    return {
        "ok": True,
        "updated_count": updated_count,
    }


@router.get("/verification/ai-health")
async def check_ai_health(
    admin: AdminUser = Depends(require_admin),
):
    """
    Check AI verification assistant health status.
    """
    ai_assistant = get_ai_assistant()
    return await ai_assistant.health_check()


# =============================================================================
# REFERENCE DATA ENDPOINTS
# =============================================================================

@router.get("/verification/flag-types")
async def get_flag_types():
    """Get available flag types with translations."""
    return {
        "flag_types": [
            {
                "value": f.value,
                "label_ar": FLAG_TYPE_TRANSLATIONS.get(f.value, {}).get("ar", f.value),
                "label_en": FLAG_TYPE_TRANSLATIONS.get(f.value, {}).get("en", f.value),
            }
            for f in FlagType
        ]
    }


@router.get("/verification/entity-types")
async def get_entity_types():
    """Get available entity types."""
    return {
        "entity_types": [
            {"value": e.value, "label_en": e.value.replace("_", " ").title()}
            for e in EntityType
        ]
    }


@router.get("/verification/statuses")
async def get_statuses():
    """Get available statuses with translations."""
    return {
        "statuses": [
            {
                "value": s.value,
                "label_ar": STATUS_TRANSLATIONS.get(s.value, {}).get("ar", s.value),
                "label_en": STATUS_TRANSLATIONS.get(s.value, {}).get("en", s.value),
            }
            for s in VerificationStatus
        ]
    }


@router.get("/verification/decisions")
async def get_decisions():
    """Get available review decisions with translations."""
    return {
        "decisions": [
            {
                "value": d.value,
                "label_ar": DECISION_TRANSLATIONS.get(d.value, {}).get("ar", d.value),
                "label_en": DECISION_TRANSLATIONS.get(d.value, {}).get("en", d.value),
            }
            for d in ReviewDecision
        ]
    }
