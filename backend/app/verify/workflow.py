"""
Admin Verification Workflow Service.

Handles the complete lifecycle of content verification:
1. Flag content for review
2. Assign to reviewers
3. AI-assisted analysis
4. Review and decision
5. Action execution

Arabic: سير عمل التحقق الإداري
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select, func, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import (
    VerificationQueue,
    FlagType,
    VerificationStatus,
    ReviewDecision,
    EntityType,
)

logger = logging.getLogger(__name__)


@dataclass
class VerificationStats:
    """Statistics for the verification queue."""
    total: int = 0
    pending: int = 0
    in_review: int = 0
    approved: int = 0
    rejected: int = 0
    deferred: int = 0
    needs_info: int = 0
    avg_review_time_hours: float = 0.0
    by_flag_type: Dict[str, int] = None
    by_entity_type: Dict[str, int] = None

    def __post_init__(self):
        if self.by_flag_type is None:
            self.by_flag_type = {}
        if self.by_entity_type is None:
            self.by_entity_type = {}


class VerificationWorkflow:
    """
    Manages the verification workflow for flagged content.

    Provides methods for:
    - Creating flags
    - Assigning reviewers
    - Processing reviews
    - Tracking statistics
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def flag_content(
        self,
        entity_type: str,
        entity_id: str,
        flag_type: str,
        flagged_by: str,
        flag_reason: str = None,
        flag_reason_ar: str = None,
        context_snapshot: Dict[str, Any] = None,
        priority: int = 5,
    ) -> VerificationQueue:
        """
        Flag content for verification.

        Args:
            entity_type: Type of entity (concept, story, etc.)
            entity_id: ID of the entity
            flag_type: Type of flag (accuracy, source, etc.)
            flagged_by: User ID or "ai_system"
            flag_reason: Reason for flagging (English)
            flag_reason_ar: Reason for flagging (Arabic)
            context_snapshot: Current state of the entity
            priority: Priority level (1=highest, 10=lowest)

        Returns:
            Created VerificationQueue item
        """
        # Check for existing pending flag on same entity
        existing = await self.db.execute(
            select(VerificationQueue).where(
                and_(
                    VerificationQueue.entity_type == entity_type,
                    VerificationQueue.entity_id == entity_id,
                    VerificationQueue.status.in_(["pending", "in_review"]),
                )
            )
        )
        existing_flag = existing.scalar_one_or_none()

        if existing_flag:
            logger.info(f"Existing flag found for {entity_type}:{entity_id}, updating priority")
            # Update existing flag with potentially higher priority
            if priority < existing_flag.priority:
                existing_flag.priority = priority
            # Add to context if additional info
            if flag_reason and existing_flag.flag_reason:
                existing_flag.flag_reason = f"{existing_flag.flag_reason}\n---\n{flag_reason}"
            await self.db.commit()
            return existing_flag

        # Create new flag
        item = VerificationQueue(
            entity_type=entity_type,
            entity_id=entity_id,
            flag_type=flag_type,
            flagged_by=flagged_by,
            flag_reason=flag_reason,
            flag_reason_ar=flag_reason_ar,
            context_snapshot=context_snapshot,
            priority=priority,
            status=VerificationStatus.PENDING.value,
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        logger.info(f"Created flag {item.id} for {entity_type}:{entity_id}")
        return item

    async def assign_reviewer(
        self,
        item_id: int,
        reviewer_id: str,
    ) -> Optional[VerificationQueue]:
        """
        Assign a reviewer to a queue item.

        Args:
            item_id: ID of the queue item
            reviewer_id: ID of the reviewer

        Returns:
            Updated VerificationQueue item or None if not found
        """
        result = await self.db.execute(
            select(VerificationQueue).where(VerificationQueue.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        item.assigned_to = reviewer_id
        item.assigned_at = datetime.utcnow()
        item.status = VerificationStatus.IN_REVIEW.value

        await self.db.commit()
        await self.db.refresh(item)

        logger.info(f"Assigned item {item_id} to {reviewer_id}")
        return item

    async def submit_review(
        self,
        item_id: int,
        reviewer_id: str,
        decision: str,
        notes: str = None,
        notes_ar: str = None,
        action_taken: str = None,
        action_details: Dict[str, Any] = None,
    ) -> Optional[VerificationQueue]:
        """
        Submit a review decision for a queue item.

        Args:
            item_id: ID of the queue item
            reviewer_id: ID of the reviewer
            decision: Review decision (approve, reject, revise, defer, escalate)
            notes: Review notes (English)
            notes_ar: Review notes (Arabic)
            action_taken: Description of action taken
            action_details: Details of the action

        Returns:
            Updated VerificationQueue item or None if not found
        """
        result = await self.db.execute(
            select(VerificationQueue).where(VerificationQueue.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Map decision to status
        status_map = {
            ReviewDecision.APPROVE.value: VerificationStatus.APPROVED.value,
            ReviewDecision.REJECT.value: VerificationStatus.REJECTED.value,
            ReviewDecision.REVISE.value: VerificationStatus.IN_REVIEW.value,
            ReviewDecision.DEFER.value: VerificationStatus.DEFERRED.value,
            ReviewDecision.ESCALATE.value: VerificationStatus.IN_REVIEW.value,
        }

        item.reviewed_by = reviewer_id
        item.reviewed_at = datetime.utcnow()
        item.review_decision = decision
        item.review_notes = notes
        item.review_notes_ar = notes_ar
        item.status = status_map.get(decision, VerificationStatus.IN_REVIEW.value)
        item.action_taken = action_taken
        item.action_details = action_details

        await self.db.commit()
        await self.db.refresh(item)

        logger.info(f"Review submitted for item {item_id}: {decision}")
        return item

    async def get_queue(
        self,
        status: Optional[str] = None,
        entity_type: Optional[str] = None,
        flag_type: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[VerificationQueue], int]:
        """
        Get items from the verification queue.

        Args:
            status: Filter by status
            entity_type: Filter by entity type
            flag_type: Filter by flag type
            assigned_to: Filter by assigned reviewer
            limit: Max items to return
            offset: Offset for pagination

        Returns:
            Tuple of (items, total_count)
        """
        # Build query
        query = select(VerificationQueue)
        count_query = select(func.count(VerificationQueue.id))

        conditions = []
        if status:
            conditions.append(VerificationQueue.status == status)
        if entity_type:
            conditions.append(VerificationQueue.entity_type == entity_type)
        if flag_type:
            conditions.append(VerificationQueue.flag_type == flag_type)
        if assigned_to:
            conditions.append(VerificationQueue.assigned_to == assigned_to)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Order by priority (ascending) and created_at (ascending for FIFO)
        query = query.order_by(
            VerificationQueue.priority,
            VerificationQueue.created_at
        )
        query = query.limit(limit).offset(offset)

        # Execute
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return items, total

    async def get_item(self, item_id: int) -> Optional[VerificationQueue]:
        """Get a single queue item by ID."""
        result = await self.db.execute(
            select(VerificationQueue).where(VerificationQueue.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self) -> VerificationStats:
        """Get verification queue statistics."""
        stats = VerificationStats()

        # Total count
        result = await self.db.execute(select(func.count(VerificationQueue.id)))
        stats.total = result.scalar() or 0

        # Counts by status
        status_counts = await self.db.execute(
            select(
                VerificationQueue.status,
                func.count(VerificationQueue.id)
            ).group_by(VerificationQueue.status)
        )
        for status, count in status_counts:
            if status == VerificationStatus.PENDING.value:
                stats.pending = count
            elif status == VerificationStatus.IN_REVIEW.value:
                stats.in_review = count
            elif status == VerificationStatus.APPROVED.value:
                stats.approved = count
            elif status == VerificationStatus.REJECTED.value:
                stats.rejected = count
            elif status == VerificationStatus.DEFERRED.value:
                stats.deferred = count
            elif status == VerificationStatus.NEEDS_INFO.value:
                stats.needs_info = count

        # Counts by flag type
        flag_counts = await self.db.execute(
            select(
                VerificationQueue.flag_type,
                func.count(VerificationQueue.id)
            ).group_by(VerificationQueue.flag_type)
        )
        stats.by_flag_type = {flag: count for flag, count in flag_counts}

        # Counts by entity type
        entity_counts = await self.db.execute(
            select(
                VerificationQueue.entity_type,
                func.count(VerificationQueue.id)
            ).group_by(VerificationQueue.entity_type)
        )
        stats.by_entity_type = {entity: count for entity, count in entity_counts}

        # Average review time (for completed reviews)
        # Calculate time between flagged_at and reviewed_at
        reviewed_items = await self.db.execute(
            select(
                VerificationQueue.flagged_at,
                VerificationQueue.reviewed_at
            ).where(
                and_(
                    VerificationQueue.reviewed_at.isnot(None),
                    VerificationQueue.flagged_at.isnot(None),
                )
            )
        )
        review_times = []
        for flagged_at, reviewed_at in reviewed_items:
            if flagged_at and reviewed_at:
                delta = (reviewed_at - flagged_at).total_seconds() / 3600  # hours
                review_times.append(delta)

        if review_times:
            stats.avg_review_time_hours = round(sum(review_times) / len(review_times), 2)

        return stats

    async def bulk_update_priority(
        self,
        item_ids: List[int],
        priority: int,
    ) -> int:
        """
        Update priority for multiple items.

        Args:
            item_ids: List of item IDs to update
            priority: New priority value

        Returns:
            Number of items updated
        """
        result = await self.db.execute(
            update(VerificationQueue)
            .where(VerificationQueue.id.in_(item_ids))
            .values(priority=priority, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    async def get_my_assignments(
        self,
        reviewer_id: str,
        include_completed: bool = False,
    ) -> List[VerificationQueue]:
        """
        Get items assigned to a specific reviewer.

        Args:
            reviewer_id: ID of the reviewer
            include_completed: Include completed reviews

        Returns:
            List of assigned items
        """
        query = select(VerificationQueue).where(
            VerificationQueue.assigned_to == reviewer_id
        )

        if not include_completed:
            query = query.where(
                VerificationQueue.status.in_([
                    VerificationStatus.PENDING.value,
                    VerificationStatus.IN_REVIEW.value,
                ])
            )

        query = query.order_by(
            VerificationQueue.priority,
            VerificationQueue.assigned_at
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pending_by_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> List[VerificationQueue]:
        """
        Get pending verification items for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity

        Returns:
            List of pending items
        """
        result = await self.db.execute(
            select(VerificationQueue).where(
                and_(
                    VerificationQueue.entity_type == entity_type,
                    VerificationQueue.entity_id == entity_id,
                    VerificationQueue.status.in_([
                        VerificationStatus.PENDING.value,
                        VerificationStatus.IN_REVIEW.value,
                    ]),
                )
            )
        )
        return list(result.scalars().all())


# Helper function to get workflow instance
async def get_verification_workflow(db: AsyncSession) -> VerificationWorkflow:
    """Get a verification workflow instance."""
    return VerificationWorkflow(db)
