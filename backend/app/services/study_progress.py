"""
Study Progress Tracking Service.

Tracks user progress towards study goals:
1. Memorization progress
2. Comprehension milestones
3. Research coverage
4. Reflection journaling

Arabic: خدمة تتبع التقدم في الدراسة
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from collections import Counter, defaultdict
import asyncio
import json

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class StudySession:
    """A single study session record."""
    session_id: str
    user_session_id: str
    goal_type: str  # memorization, comprehension, research, reflection
    start_time: datetime
    end_time: Optional[datetime] = None
    verses_studied: List[str] = field(default_factory=list)  # verse references
    themes_explored: List[str] = field(default_factory=list)
    prophets_studied: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    completion_percentage: float = 0.0


@dataclass
class MemorizationProgress:
    """Progress tracking for verse memorization."""
    verse_reference: str
    sura_no: int
    aya_no: int
    status: str  # "not_started", "learning", "reviewing", "memorized"
    first_attempt: Optional[datetime] = None
    last_review: Optional[datetime] = None
    review_count: int = 0
    confidence_level: int = 0  # 0-5 scale
    next_review_due: Optional[datetime] = None


@dataclass
class ComprehensionMilestone:
    """Milestone for verse/theme comprehension."""
    milestone_id: str
    milestone_type: str  # "theme_mastery", "prophet_study", "sura_completion"
    target: str  # theme_id, prophet_name, or sura_no
    progress: float  # 0.0 to 1.0
    achieved_at: Optional[datetime] = None
    related_verses: List[str] = field(default_factory=list)


@dataclass
class ReflectionEntry:
    """A personal reflection on verses."""
    entry_id: str
    user_session_id: str
    verse_reference: str
    theme: Optional[str] = None
    reflection_text: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


# =============================================================================
# STUDY PROGRESS SERVICE
# =============================================================================

class StudyProgressService:
    """
    Service for tracking and managing user study progress.

    Supports multiple study modes:
    - Memorization: Spaced repetition tracking
    - Comprehension: Theme and concept mastery
    - Research: Cross-reference exploration
    - Reflection: Personal journaling
    """

    def __init__(self):
        # Session-based storage
        self._study_sessions: Dict[str, List[StudySession]] = defaultdict(list)
        self._memorization_progress: Dict[str, Dict[str, MemorizationProgress]] = defaultdict(dict)
        self._comprehension_milestones: Dict[str, List[ComprehensionMilestone]] = defaultdict(list)
        self._reflections: Dict[str, List[ReflectionEntry]] = defaultdict(list)
        self._daily_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    # =========================================================================
    # STUDY SESSIONS
    # =========================================================================

    async def start_study_session(
        self,
        user_session_id: str,
        goal_type: str,
    ) -> StudySession:
        """Start a new study session."""
        session = StudySession(
            session_id=f"study_{datetime.utcnow().timestamp()}_{user_session_id[:8]}",
            user_session_id=user_session_id,
            goal_type=goal_type,
            start_time=datetime.utcnow(),
        )

        async with self._lock:
            self._study_sessions[user_session_id].append(session)

        return session

    async def end_study_session(
        self,
        user_session_id: str,
        verses_studied: List[str] = None,
        themes_explored: List[str] = None,
        prophets_studied: List[str] = None,
        notes: str = None,
    ) -> Optional[StudySession]:
        """End the current study session."""
        async with self._lock:
            sessions = self._study_sessions.get(user_session_id, [])
            if not sessions:
                return None

            current_session = sessions[-1]
            if current_session.end_time is not None:
                return None  # Already ended

            current_session.end_time = datetime.utcnow()
            current_session.verses_studied = verses_studied or []
            current_session.themes_explored = themes_explored or []
            current_session.prophets_studied = prophets_studied or []
            current_session.notes = notes

            # Calculate completion
            if verses_studied:
                current_session.completion_percentage = min(100.0, len(verses_studied) * 10)

            # Update daily stats
            await self._update_daily_stats(user_session_id, current_session)

            return current_session

    async def _update_daily_stats(
        self,
        user_session_id: str,
        session: StudySession,
    ):
        """Update daily statistics."""
        today = datetime.utcnow().date().isoformat()

        if today not in self._daily_stats[user_session_id]:
            self._daily_stats[user_session_id][today] = {
                "total_time_minutes": 0,
                "verses_studied": 0,
                "themes_explored": set(),
                "sessions_count": 0,
            }

        stats = self._daily_stats[user_session_id][today]

        if session.end_time and session.start_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
            stats["total_time_minutes"] += duration

        stats["verses_studied"] += len(session.verses_studied)
        stats["themes_explored"].update(session.themes_explored)
        stats["sessions_count"] += 1

    # =========================================================================
    # MEMORIZATION TRACKING
    # =========================================================================

    async def record_memorization_attempt(
        self,
        user_session_id: str,
        sura_no: int,
        aya_no: int,
        confidence_level: int,  # 0-5 scale
    ) -> MemorizationProgress:
        """Record a memorization attempt for a verse."""
        verse_ref = f"{sura_no}:{aya_no}"

        async with self._lock:
            progress = self._memorization_progress[user_session_id].get(verse_ref)

            if progress is None:
                progress = MemorizationProgress(
                    verse_reference=verse_ref,
                    sura_no=sura_no,
                    aya_no=aya_no,
                    status="learning",
                    first_attempt=datetime.utcnow(),
                )
                self._memorization_progress[user_session_id][verse_ref] = progress

            # Update progress
            progress.last_review = datetime.utcnow()
            progress.review_count += 1
            progress.confidence_level = confidence_level

            # Update status based on confidence
            if confidence_level >= 5:
                progress.status = "memorized"
            elif confidence_level >= 3:
                progress.status = "reviewing"
            else:
                progress.status = "learning"

            # Calculate next review (spaced repetition)
            progress.next_review_due = self._calculate_next_review(progress)

            return progress

    def _calculate_next_review(self, progress: MemorizationProgress) -> datetime:
        """Calculate next review date using spaced repetition."""
        base_intervals = [1, 3, 7, 14, 30, 60, 90]  # Days

        # Get interval based on review count
        interval_idx = min(progress.review_count - 1, len(base_intervals) - 1)
        interval_days = base_intervals[max(0, interval_idx)]

        # Adjust based on confidence
        confidence_multiplier = 0.5 + (progress.confidence_level / 10)
        adjusted_days = int(interval_days * confidence_multiplier)

        return datetime.utcnow() + timedelta(days=max(1, adjusted_days))

    async def get_memorization_progress(
        self,
        user_session_id: str,
        sura_no: Optional[int] = None,
    ) -> List[MemorizationProgress]:
        """Get memorization progress for user, optionally filtered by sura."""
        progress_list = list(self._memorization_progress.get(user_session_id, {}).values())

        if sura_no is not None:
            progress_list = [p for p in progress_list if p.sura_no == sura_no]

        return sorted(progress_list, key=lambda x: (x.sura_no, x.aya_no))

    async def get_verses_due_for_review(
        self,
        user_session_id: str,
        limit: int = 20,
    ) -> List[MemorizationProgress]:
        """Get verses that are due for review."""
        now = datetime.utcnow()
        progress_list = list(self._memorization_progress.get(user_session_id, {}).values())

        due_verses = [
            p for p in progress_list
            if p.next_review_due is not None and p.next_review_due <= now
        ]

        # Sort by most overdue first
        due_verses.sort(key=lambda x: x.next_review_due or datetime.max)
        return due_verses[:limit]

    async def get_memorization_stats(
        self,
        user_session_id: str,
    ) -> Dict[str, Any]:
        """Get memorization statistics."""
        progress_list = list(self._memorization_progress.get(user_session_id, {}).values())

        if not progress_list:
            return {
                "total_verses": 0,
                "memorized": 0,
                "reviewing": 0,
                "learning": 0,
                "average_confidence": 0.0,
                "total_reviews": 0,
            }

        status_counts = Counter(p.status for p in progress_list)
        total_confidence = sum(p.confidence_level for p in progress_list)
        total_reviews = sum(p.review_count for p in progress_list)

        return {
            "total_verses": len(progress_list),
            "memorized": status_counts.get("memorized", 0),
            "reviewing": status_counts.get("reviewing", 0),
            "learning": status_counts.get("learning", 0),
            "average_confidence": round(total_confidence / len(progress_list), 2),
            "total_reviews": total_reviews,
            "completion_percentage": round(
                status_counts.get("memorized", 0) / len(progress_list) * 100, 1
            ),
        }

    # =========================================================================
    # COMPREHENSION MILESTONES
    # =========================================================================

    async def record_comprehension_progress(
        self,
        user_session_id: str,
        milestone_type: str,
        target: str,
        verses_covered: List[str],
    ) -> ComprehensionMilestone:
        """Record progress towards a comprehension milestone."""
        milestone_id = f"{milestone_type}_{target}"

        async with self._lock:
            # Find or create milestone
            existing = None
            for m in self._comprehension_milestones[user_session_id]:
                if m.milestone_id == milestone_id:
                    existing = m
                    break

            if existing is None:
                existing = ComprehensionMilestone(
                    milestone_id=milestone_id,
                    milestone_type=milestone_type,
                    target=target,
                    progress=0.0,
                )
                self._comprehension_milestones[user_session_id].append(existing)

            # Update progress
            existing.related_verses.extend(verses_covered)
            existing.related_verses = list(set(existing.related_verses))

            # Calculate progress (simplified - could be more sophisticated)
            if milestone_type == "theme_mastery":
                existing.progress = min(1.0, len(existing.related_verses) / 20)
            elif milestone_type == "prophet_study":
                existing.progress = min(1.0, len(existing.related_verses) / 30)
            elif milestone_type == "sura_completion":
                # Would need actual verse count for sura
                existing.progress = min(1.0, len(existing.related_verses) / 50)

            if existing.progress >= 1.0 and existing.achieved_at is None:
                existing.achieved_at = datetime.utcnow()

            return existing

    async def get_comprehension_milestones(
        self,
        user_session_id: str,
        milestone_type: Optional[str] = None,
    ) -> List[ComprehensionMilestone]:
        """Get comprehension milestones for user."""
        milestones = self._comprehension_milestones.get(user_session_id, [])

        if milestone_type:
            milestones = [m for m in milestones if m.milestone_type == milestone_type]

        return sorted(milestones, key=lambda x: x.progress, reverse=True)

    # =========================================================================
    # REFLECTION JOURNAL
    # =========================================================================

    async def add_reflection(
        self,
        user_session_id: str,
        verse_reference: str,
        reflection_text: str,
        theme: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ReflectionEntry:
        """Add a personal reflection on a verse."""
        entry = ReflectionEntry(
            entry_id=f"refl_{datetime.utcnow().timestamp()}",
            user_session_id=user_session_id,
            verse_reference=verse_reference,
            theme=theme,
            reflection_text=reflection_text,
            tags=tags or [],
        )

        async with self._lock:
            self._reflections[user_session_id].append(entry)

        return entry

    async def update_reflection(
        self,
        user_session_id: str,
        entry_id: str,
        reflection_text: str,
        tags: Optional[List[str]] = None,
    ) -> Optional[ReflectionEntry]:
        """Update an existing reflection."""
        async with self._lock:
            for entry in self._reflections.get(user_session_id, []):
                if entry.entry_id == entry_id:
                    entry.reflection_text = reflection_text
                    entry.updated_at = datetime.utcnow()
                    if tags is not None:
                        entry.tags = tags
                    return entry
        return None

    async def get_reflections(
        self,
        user_session_id: str,
        verse_reference: Optional[str] = None,
        theme: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[ReflectionEntry]:
        """Get reflections with optional filters."""
        reflections = self._reflections.get(user_session_id, [])

        if verse_reference:
            reflections = [r for r in reflections if r.verse_reference == verse_reference]

        if theme:
            reflections = [r for r in reflections if r.theme == theme]

        if tags:
            reflections = [
                r for r in reflections
                if any(t in r.tags for t in tags)
            ]

        # Sort by creation time (newest first)
        reflections.sort(key=lambda x: x.created_at, reverse=True)
        return reflections[:limit]

    # =========================================================================
    # OVERALL PROGRESS & STATISTICS
    # =========================================================================

    async def get_overall_progress(
        self,
        user_session_id: str,
    ) -> Dict[str, Any]:
        """Get comprehensive progress overview."""
        # Memorization stats
        mem_stats = await self.get_memorization_stats(user_session_id)

        # Comprehension milestones
        milestones = await self.get_comprehension_milestones(user_session_id)
        achieved_milestones = [m for m in milestones if m.achieved_at is not None]

        # Reflection count
        reflection_count = len(self._reflections.get(user_session_id, []))

        # Session history
        sessions = self._study_sessions.get(user_session_id, [])
        total_study_time = sum(
            (s.end_time - s.start_time).total_seconds() / 60
            for s in sessions
            if s.end_time is not None
        )

        # Calculate streak
        streak = await self._calculate_streak(user_session_id)

        return {
            "memorization": mem_stats,
            "comprehension": {
                "total_milestones": len(milestones),
                "achieved_milestones": len(achieved_milestones),
                "in_progress": len(milestones) - len(achieved_milestones),
            },
            "reflection": {
                "total_entries": reflection_count,
            },
            "sessions": {
                "total_sessions": len(sessions),
                "total_study_time_minutes": round(total_study_time, 1),
            },
            "streak": streak,
        }

    async def _calculate_streak(self, user_session_id: str) -> Dict[str, Any]:
        """Calculate study streak."""
        sessions = self._study_sessions.get(user_session_id, [])

        if not sessions:
            return {"current_streak": 0, "longest_streak": 0}

        # Get dates with study sessions
        study_dates = set()
        for session in sessions:
            if session.start_time:
                study_dates.add(session.start_time.date())

        if not study_dates:
            return {"current_streak": 0, "longest_streak": 0}

        # Calculate current streak
        today = datetime.utcnow().date()
        current_streak = 0
        check_date = today

        while check_date in study_dates:
            current_streak += 1
            check_date = check_date - timedelta(days=1)

        # Calculate longest streak
        sorted_dates = sorted(study_dates)
        longest_streak = 1
        current = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current += 1
                longest_streak = max(longest_streak, current)
            else:
                current = 1

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_study_date": max(study_dates).isoformat() if study_dates else None,
        }

    async def get_daily_stats(
        self,
        user_session_id: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get daily statistics for the past N days."""
        today = datetime.utcnow().date()
        stats = []

        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.isoformat()

            day_stats = self._daily_stats.get(user_session_id, {}).get(date_str, {})

            stats.append({
                "date": date_str,
                "total_time_minutes": day_stats.get("total_time_minutes", 0),
                "verses_studied": day_stats.get("verses_studied", 0),
                "themes_explored": len(day_stats.get("themes_explored", set())),
                "sessions_count": day_stats.get("sessions_count", 0),
            })

        return stats

    async def get_recommendations(
        self,
        user_session_id: str,
    ) -> Dict[str, Any]:
        """Get personalized study recommendations based on progress."""
        recommendations = {
            "memorization": [],
            "comprehension": [],
            "general": [],
        }

        # Memorization recommendations
        due_verses = await self.get_verses_due_for_review(user_session_id, limit=5)
        if due_verses:
            recommendations["memorization"].append({
                "type": "review_due",
                "message_en": f"You have {len(due_verses)} verses due for review",
                "message_ar": f"لديك {len(due_verses)} آيات للمراجعة",
                "verses": [v.verse_reference for v in due_verses[:3]],
            })

        mem_stats = await self.get_memorization_stats(user_session_id)
        if mem_stats["learning"] > 0:
            recommendations["memorization"].append({
                "type": "continue_learning",
                "message_en": f"Continue learning {mem_stats['learning']} verses in progress",
                "message_ar": f"أكمل حفظ {mem_stats['learning']} آية قيد التعلم",
            })

        # Comprehension recommendations
        milestones = await self.get_comprehension_milestones(user_session_id)
        in_progress = [m for m in milestones if m.progress > 0 and m.progress < 1]
        if in_progress:
            closest = max(in_progress, key=lambda x: x.progress)
            recommendations["comprehension"].append({
                "type": "complete_milestone",
                "message_en": f"You're {int(closest.progress * 100)}% through {closest.target}",
                "message_ar": f"أنت {int(closest.progress * 100)}% في {closest.target}",
                "milestone": closest.milestone_id,
            })

        # General recommendations
        streak = await self._calculate_streak(user_session_id)
        if streak["current_streak"] > 0:
            recommendations["general"].append({
                "type": "maintain_streak",
                "message_en": f"Keep your {streak['current_streak']}-day streak going!",
                "message_ar": f"حافظ على سلسلتك المكونة من {streak['current_streak']} أيام!",
            })

        return recommendations


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

study_progress_service = StudyProgressService()
