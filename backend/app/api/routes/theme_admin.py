"""
Theme Admin Routes - Admin Review Workflow for Theme Suggestions

ENDPOINTS:
==========
GET  /themes/admin/suggestions        - List pending suggestions
GET  /themes/admin/suggestions/{id}   - Get suggestion detail
POST /themes/admin/suggestions/import - Import candidates from discovery
POST /themes/admin/suggestions/{id}/approve - Approve suggestion
POST /themes/admin/suggestions/{id}/reject  - Reject suggestion
GET  /themes/admin/stats              - Admin statistics

AUTHORIZATION:
==============
All endpoints require admin authentication via Bearer token in Authorization header.
Set ADMIN_TOKEN environment variable to enable authentication.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.auth import require_admin, AdminUser
from app.models.theme import ThemeSuggestion, ThemeSegment, QuranicTheme


router = APIRouter(prefix="/admin", tags=["theme-admin"])


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class SuggestionResponse(BaseModel):
    """Theme suggestion for admin review."""
    id: int
    theme_id: str
    theme_title_ar: Optional[str] = None
    theme_title_en: Optional[str] = None
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    match_type: str
    confidence: float
    reasons_ar: str
    reasons_en: Optional[str] = None
    evidence_sources: List[Dict[str, Any]]
    evidence_count: int
    status: str
    status_label_ar: str
    status_label_en: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    source: str
    batch_id: Optional[str] = None
    created_at: str
    # New fields for approval workflow
    origin: str = "auto_discovery"
    origin_label_ar: str = "اكتشاف آلي"
    origin_label_en: str = "Auto Discovery"
    is_auto_discovery: bool = True
    meets_approval_requirements: bool = False
    approval_blockers: List[str] = []
    has_proper_attribution: bool = False


class SuggestionListResponse(BaseModel):
    """Response for suggestion listing."""
    suggestions: List[SuggestionResponse]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int
    offset: int
    limit: int


class ApproveRequest(BaseModel):
    """Request to approve a suggestion."""
    reviewer: str = Field(..., description="Admin username")
    summary_ar: Optional[str] = Field(None, description="Override summary in Arabic")
    summary_en: Optional[str] = Field(None, description="Override summary in English")
    is_core: bool = Field(True, description="Mark as core segment")


class RejectRequest(BaseModel):
    """Request to reject a suggestion."""
    reviewer: str = Field(..., description="Admin username")
    reason: str = Field(..., description="Reason for rejection")


class ImportRequest(BaseModel):
    """Request to import discovery candidates."""
    candidates: List[Dict[str, Any]] = Field(..., description="List of candidates to import")
    batch_id: Optional[str] = Field(None, description="Batch ID for tracking")


class AdminStatsResponse(BaseModel):
    """Admin statistics response."""
    total_suggestions: int
    pending_suggestions: int
    approved_suggestions: int
    rejected_suggestions: int
    total_segments: int
    discovered_segments: int
    manual_segments: int
    by_theme: List[Dict[str, Any]]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/suggestions", response_model=SuggestionListResponse)
async def list_suggestions(
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    theme_id: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|confidence_desc|confidence_asc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """
    List theme suggestions for admin review.

    Filters:
    - status: pending, approved, rejected
    - theme_id: Filter by specific theme
    - min_confidence: Minimum confidence threshold

    Sorting:
    - created_desc: Newest first (default)
    - created_asc: Oldest first
    - confidence_desc: Highest confidence first
    - confidence_asc: Lowest confidence first
    """
    # Build query
    query = select(ThemeSuggestion, QuranicTheme).join(
        QuranicTheme, ThemeSuggestion.theme_id == QuranicTheme.id
    )

    if status:
        query = query.where(ThemeSuggestion.status == status)
    if theme_id:
        query = query.where(ThemeSuggestion.theme_id == theme_id)
    if min_confidence is not None:
        query = query.where(ThemeSuggestion.confidence >= min_confidence)

    # Get counts
    count_query = select(
        func.count(ThemeSuggestion.id).filter(ThemeSuggestion.status == 'pending'),
        func.count(ThemeSuggestion.id).filter(ThemeSuggestion.status == 'approved'),
        func.count(ThemeSuggestion.id).filter(ThemeSuggestion.status == 'rejected'),
        func.count(ThemeSuggestion.id),
    )
    counts = (await session.execute(count_query)).fetchone()
    pending_count, approved_count, rejected_count, total = counts

    # Sort
    sort_map = {
        "created_desc": [ThemeSuggestion.created_at.desc()],
        "created_asc": [ThemeSuggestion.created_at.asc()],
        "confidence_desc": [ThemeSuggestion.confidence.desc()],
        "confidence_asc": [ThemeSuggestion.confidence.asc()],
    }
    query = query.order_by(*sort_map.get(sort, sort_map["created_desc"]))

    # Paginate
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    rows = result.all()

    suggestions = [
        SuggestionResponse(
            id=s.id,
            theme_id=s.theme_id,
            theme_title_ar=t.title_ar,
            theme_title_en=t.title_en,
            sura_no=s.sura_no,
            ayah_start=s.ayah_start,
            ayah_end=s.ayah_end,
            verse_reference=s.verse_reference,
            match_type=s.match_type,
            confidence=s.confidence,
            reasons_ar=s.reasons_ar,
            reasons_en=s.reasons_en,
            evidence_sources=s.evidence_sources or [],
            evidence_count=s.evidence_count,
            status=s.status,
            status_label_ar=s.status_label_ar,
            status_label_en=s.status_label_en,
            reviewed_by=s.reviewed_by,
            reviewed_at=str(s.reviewed_at) if s.reviewed_at else None,
            rejection_reason=s.rejection_reason,
            source=s.source or 'discovery',
            batch_id=s.batch_id,
            created_at=str(s.created_at) if s.created_at else "",
            # Approval workflow fields
            origin=s.origin or 'auto_discovery',
            origin_label_ar=s.origin_label_ar,
            origin_label_en=s.origin_label_en,
            is_auto_discovery=s.is_auto_discovery,
            meets_approval_requirements=s.meets_approval_requirements,
            approval_blockers=s.approval_blockers,
            has_proper_attribution=s.has_proper_attribution,
        )
        for s, t in rows
    ]

    return SuggestionListResponse(
        suggestions=suggestions,
        total=total,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        offset=offset,
        limit=limit,
    )


@router.get("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
async def get_suggestion(
    suggestion_id: int = Path(...),
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """Get a specific suggestion by ID."""
    query = select(ThemeSuggestion, QuranicTheme).join(
        QuranicTheme, ThemeSuggestion.theme_id == QuranicTheme.id
    ).where(ThemeSuggestion.id == suggestion_id)

    result = await session.execute(query)
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Suggestion not found: {suggestion_id}")

    s, t = row
    return SuggestionResponse(
        id=s.id,
        theme_id=s.theme_id,
        theme_title_ar=t.title_ar,
        theme_title_en=t.title_en,
        sura_no=s.sura_no,
        ayah_start=s.ayah_start,
        ayah_end=s.ayah_end,
        verse_reference=s.verse_reference,
        match_type=s.match_type,
        confidence=s.confidence,
        reasons_ar=s.reasons_ar,
        reasons_en=s.reasons_en,
        evidence_sources=s.evidence_sources or [],
        evidence_count=s.evidence_count,
        status=s.status,
        status_label_ar=s.status_label_ar,
        status_label_en=s.status_label_en,
        reviewed_by=s.reviewed_by,
        reviewed_at=str(s.reviewed_at) if s.reviewed_at else None,
        rejection_reason=s.rejection_reason,
        source=s.source or 'discovery',
        batch_id=s.batch_id,
        created_at=str(s.created_at) if s.created_at else "",
        # Approval workflow fields
        origin=s.origin or 'auto_discovery',
        origin_label_ar=s.origin_label_ar,
        origin_label_en=s.origin_label_en,
        is_auto_discovery=s.is_auto_discovery,
        meets_approval_requirements=s.meets_approval_requirements,
        approval_blockers=s.approval_blockers,
        has_proper_attribution=s.has_proper_attribution,
    )


@router.post("/suggestions/import")
async def import_suggestions(
    request: ImportRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """
    Import discovery candidates as suggestions.

    Each candidate should have:
    - theme_id: str
    - sura_no: int
    - ayah_start: int
    - ayah_end: int
    - match_type: str
    - confidence: float
    - reasons_ar: str
    - evidence_sources: List[Dict]
    - evidence_chunk_ids: List[str]
    """
    imported = 0
    skipped = 0
    errors = []

    batch_id = request.batch_id or f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    for candidate in request.candidates:
        try:
            # Check if suggestion already exists
            existing = await session.execute(
                select(ThemeSuggestion).where(
                    ThemeSuggestion.theme_id == candidate['theme_id'],
                    ThemeSuggestion.sura_no == candidate['sura_no'],
                    ThemeSuggestion.ayah_start == candidate['ayah_start'],
                    ThemeSuggestion.ayah_end == candidate['ayah_end'],
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Also check if segment already exists
            segment_id = f"{candidate['theme_id']}:{candidate['sura_no']}:{candidate['ayah_start']}"
            existing_segment = await session.execute(
                select(ThemeSegment).where(ThemeSegment.id == segment_id)
            )
            if existing_segment.scalar_one_or_none():
                skipped += 1
                continue

            suggestion = ThemeSuggestion(
                theme_id=candidate['theme_id'],
                sura_no=candidate['sura_no'],
                ayah_start=candidate['ayah_start'],
                ayah_end=candidate.get('ayah_end', candidate['ayah_start']),
                match_type=candidate['match_type'],
                confidence=candidate['confidence'],
                reasons_ar=candidate['reasons_ar'],
                reasons_en=candidate.get('reasons_en'),
                evidence_sources=candidate['evidence_sources'],
                evidence_chunk_ids=candidate['evidence_chunk_ids'],
                status='pending',
                origin=candidate.get('origin', 'auto_discovery'),  # Track origin
                source='import',
                batch_id=batch_id,
                created_at=datetime.utcnow(),
            )
            session.add(suggestion)
            imported += 1

        except Exception as e:
            errors.append({
                "candidate": candidate.get('theme_id', 'unknown'),
                "error": str(e),
            })

    await session.commit()

    return {
        "batch_id": batch_id,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int = Path(...),
    request: ApproveRequest = Body(...),
    force: bool = Query(False, description="Force approval even if requirements not met"),
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """
    Approve a suggestion and create a ThemeSegment.

    APPROVAL RULES (Sunni-safe):
    - Manual suggestions: Always approvable
    - Auto-discovered suggestions require:
      - At least 2 tafsir sources OR
      - (confidence >= 0.85 AND match_type in {direct, exact, lexical, root})

    Use force=true to override requirements (admin override).
    The suggestion is kept for audit trail after the segment is created.
    """
    # Get suggestion
    result = await session.execute(
        select(ThemeSuggestion).where(ThemeSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(status_code=404, detail=f"Suggestion not found: {suggestion_id}")

    if suggestion.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Suggestion already {suggestion.status}")

    # Validate approval requirements (unless force override)
    if not force and suggestion.is_auto_discovery and not suggestion.meets_approval_requirements:
        blockers = suggestion.approval_blockers
        raise HTTPException(
            status_code=400,
            detail={
                "error": "لا يمكن الموافقة - لم تستوفِ المتطلبات",
                "error_en": "Cannot approve - requirements not met",
                "blockers": blockers,
                "hint": "Use force=true to override (admin only)",
            }
        )

    # Get next segment order
    max_order_result = await session.execute(
        select(func.max(ThemeSegment.segment_order))
        .where(ThemeSegment.theme_id == suggestion.theme_id)
    )
    max_order = max_order_result.scalar() or 0

    # Create segment
    segment_id = f"{suggestion.theme_id}:{suggestion.sura_no}:{suggestion.ayah_start}"

    # Check if segment already exists
    existing = await session.execute(
        select(ThemeSegment).where(ThemeSegment.id == segment_id)
    )
    if existing.scalar_one_or_none():
        # Delete suggestion since segment exists
        await session.delete(suggestion)
        await session.commit()
        raise HTTPException(status_code=400, detail="Segment already exists")

    segment = ThemeSegment(
        id=segment_id,
        theme_id=suggestion.theme_id,
        segment_order=max_order + 1,
        sura_no=suggestion.sura_no,
        ayah_start=suggestion.ayah_start,
        ayah_end=suggestion.ayah_end,
        title_ar=f"آية {suggestion.verse_reference}",
        title_en=f"Verse {suggestion.verse_reference}",
        summary_ar=request.summary_ar or suggestion.reasons_ar,
        summary_en=request.summary_en or suggestion.reasons_en or f"Approved from suggestion for {suggestion.theme_id}",
        evidence_sources=suggestion.evidence_sources,
        evidence_chunk_ids=suggestion.evidence_chunk_ids,
        match_type=suggestion.match_type,
        confidence=suggestion.confidence,
        reasons_ar=suggestion.reasons_ar,
        reasons_en=suggestion.reasons_en,
        is_core=request.is_core,
        is_verified=True,  # Admin-approved = verified
        discovered_at=suggestion.created_at,
        created_at=datetime.utcnow(),
    )

    session.add(segment)

    # Update suggestion status (keep for audit trail)
    suggestion.status = 'approved'
    suggestion.reviewed_by = request.reviewer
    suggestion.reviewed_at = datetime.utcnow()

    await session.commit()

    return {
        "success": True,
        "segment_id": segment_id,
        "suggestion_id": suggestion_id,
        "reviewed_by": request.reviewer,
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int = Path(...),
    request: RejectRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """
    Reject a suggestion.

    The suggestion is kept for audit trail with rejection reason.
    """
    result = await session.execute(
        select(ThemeSuggestion).where(ThemeSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(status_code=404, detail=f"Suggestion not found: {suggestion_id}")

    if suggestion.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Suggestion already {suggestion.status}")

    suggestion.status = 'rejected'
    suggestion.reviewed_by = request.reviewer
    suggestion.reviewed_at = datetime.utcnow()
    suggestion.rejection_reason = request.reason

    await session.commit()

    return {
        "success": True,
        "suggestion_id": suggestion_id,
        "reviewed_by": request.reviewer,
        "reason": request.reason,
    }


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    session: AsyncSession = Depends(get_async_session),
    admin: AdminUser = Depends(require_admin),
):
    """Get admin statistics for theme suggestions and segments."""
    from sqlalchemy import text as sql_text

    # Suggestion counts
    suggestion_counts = await session.execute(sql_text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
        FROM theme_suggestions
    """))
    row = suggestion_counts.fetchone()
    total_suggestions = row[0] or 0
    pending = row[1] or 0
    approved = row[2] or 0
    rejected = row[3] or 0

    # Segment counts
    segment_counts = await session.execute(sql_text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN match_type != 'manual' AND match_type IS NOT NULL THEN 1 END) as discovered,
            COUNT(CASE WHEN match_type = 'manual' OR match_type IS NULL THEN 1 END) as manual
        FROM theme_segments
    """))
    seg_row = segment_counts.fetchone()
    total_segments = seg_row[0] or 0
    discovered_segments = seg_row[1] or 0
    manual_segments = seg_row[2] or 0

    # By theme (top 10)
    by_theme_result = await session.execute(sql_text("""
        SELECT
            ts.theme_id,
            qt.title_ar,
            COUNT(CASE WHEN ts.status = 'pending' THEN 1 END) as pending,
            COUNT(*) as total
        FROM theme_suggestions ts
        JOIN quranic_themes qt ON ts.theme_id = qt.id
        GROUP BY ts.theme_id, qt.title_ar
        ORDER BY pending DESC
        LIMIT 10
    """))
    by_theme = [
        {
            "theme_id": r[0],
            "title_ar": r[1],
            "pending": r[2],
            "total": r[3],
        }
        for r in by_theme_result
    ]

    return AdminStatsResponse(
        total_suggestions=total_suggestions,
        pending_suggestions=pending,
        approved_suggestions=approved,
        rejected_suggestions=rejected,
        total_segments=total_segments,
        discovered_segments=discovered_segments,
        manual_segments=manual_segments,
        by_theme=by_theme,
    )
