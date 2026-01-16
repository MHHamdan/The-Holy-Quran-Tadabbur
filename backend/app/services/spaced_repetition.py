"""
SM2 Spaced Repetition Algorithm for Quran Memorization.

Implements the SuperMemo 2 (SM2) algorithm adapted for Quranic memorization.

Features:
1. Adaptive review scheduling based on recall quality
2. Verse-level and passage-level tracking
3. Personalized difficulty assessment
4. Integration with study goals and achievements

Arabic: خوارزمية التكرار المتباعد SM2 لحفظ القرآن
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# SM2 CONFIGURATION
# =============================================================================

SM2_CONFIG = {
    # Default easiness factor (2.5 is optimal starting point)
    "default_easiness": 2.5,
    # Minimum easiness factor to prevent items becoming too hard
    "min_easiness": 1.3,
    # Quality response scale (0-5 in SM2)
    "quality_min": 0,
    "quality_max": 5,
    # Quality threshold for successful recall (>= 3)
    "success_threshold": 3,
    # Maximum interval in days
    "max_interval": 365,
    # Minimum interval in days
    "min_interval": 1,
}

# Quran-specific learning stages
class MemorizationStage(str, Enum):
    NEW = "new"                    # Not yet started
    LEARNING = "learning"          # Initial learning (first few exposures)
    YOUNG = "young"               # Recently memorized (< 21 days)
    MATURE = "mature"             # Well-established (>= 21 days)
    SUSPENDED = "suspended"        # Paused by user

# Quality ratings with Arabic descriptions
QUALITY_RATINGS = {
    0: {
        "en": "Complete blackout - no recall",
        "ar": "نسيان تام - لا تذكر شيئًا",
        "action": "Reset and relearn",
    },
    1: {
        "en": "Incorrect, but recognized when shown",
        "ar": "إجابة خاطئة، لكن تعرفت عليها عند العرض",
        "action": "Reset interval",
    },
    2: {
        "en": "Incorrect, but easy to recall after hint",
        "ar": "إجابة خاطئة، لكن تذكرتها بسهولة بعد التلميح",
        "action": "Reset interval",
    },
    3: {
        "en": "Correct with significant difficulty",
        "ar": "إجابة صحيحة مع صعوبة كبيرة",
        "action": "Continue with shorter interval",
    },
    4: {
        "en": "Correct with some hesitation",
        "ar": "إجابة صحيحة مع بعض التردد",
        "action": "Continue normally",
    },
    5: {
        "en": "Perfect recall - no hesitation",
        "ar": "تذكر تام - بدون تردد",
        "action": "Continue with longer interval",
    },
}

# Recommended daily review limits
DAILY_LIMITS = {
    "new_verses": 7,           # Maximum new verses per day
    "reviews": 50,             # Maximum reviews per day
    "learning_verses": 20,     # Maximum verses in learning stage
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class VerseMemoryCard:
    """Represents a verse in the memorization system."""
    verse_id: int
    sura_no: int
    aya_no: int
    verse_reference: str
    text_uthmani: str
    # SM2 parameters
    easiness_factor: float = SM2_CONFIG["default_easiness"]
    interval: int = 0  # Days until next review
    repetitions: int = 0
    # Dates
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    first_learned: Optional[datetime] = None
    # State
    stage: MemorizationStage = MemorizationStage.NEW
    # Statistics
    total_reviews: int = 0
    successful_reviews: int = 0
    average_quality: float = 0.0
    # Context
    juz_no: Optional[int] = None
    hizb_no: Optional[int] = None


@dataclass
class ReviewSession:
    """A memorization review session."""
    session_id: str
    user_id: str
    started_at: datetime
    cards: List[VerseMemoryCard]
    current_index: int = 0
    completed_reviews: int = 0
    correct_reviews: int = 0
    total_time_seconds: int = 0


@dataclass
class MemorizationStats:
    """User memorization statistics."""
    total_verses: int
    new_verses: int
    learning_verses: int
    young_verses: int
    mature_verses: int
    suspended_verses: int
    due_today: int
    streak_days: int
    average_retention: float
    estimated_completion_days: int


# =============================================================================
# SM2 ALGORITHM IMPLEMENTATION
# =============================================================================

class SM2Algorithm:
    """
    SuperMemo 2 algorithm implementation.

    The SM2 algorithm calculates optimal review intervals based on:
    - Quality of recall (0-5)
    - Easiness Factor (EF) - how easy the item is to remember
    - Number of successful repetitions

    Formula:
    EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    Where:
    - EF' is the new easiness factor
    - EF is the current easiness factor
    - q is the quality of response (0-5)
    """

    @staticmethod
    def calculate_next_interval(
        quality: int,
        repetitions: int,
        easiness_factor: float,
        current_interval: int,
    ) -> Tuple[int, float, int]:
        """
        Calculate the next review interval using SM2.

        Args:
            quality: Quality of recall (0-5)
            repetitions: Number of successful repetitions
            easiness_factor: Current easiness factor
            current_interval: Current interval in days

        Returns:
            Tuple of (new_interval, new_easiness_factor, new_repetitions)
        """
        # Clamp quality to valid range
        quality = max(SM2_CONFIG["quality_min"], min(SM2_CONFIG["quality_max"], quality))

        # Calculate new easiness factor
        new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(SM2_CONFIG["min_easiness"], new_ef)

        # Determine if recall was successful
        if quality >= SM2_CONFIG["success_threshold"]:
            # Successful recall
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                new_interval = round(current_interval * new_ef)

            new_repetitions = repetitions + 1
        else:
            # Failed recall - reset
            new_interval = 1
            new_repetitions = 0
            # Keep easiness factor reduction from above

        # Clamp interval
        new_interval = max(SM2_CONFIG["min_interval"], min(SM2_CONFIG["max_interval"], new_interval))

        return new_interval, new_ef, new_repetitions

    @staticmethod
    def determine_stage(repetitions: int, interval: int, first_learned: Optional[datetime]) -> MemorizationStage:
        """Determine memorization stage based on learning progress."""
        if repetitions == 0:
            if first_learned is None:
                return MemorizationStage.NEW
            return MemorizationStage.LEARNING

        if first_learned:
            days_since_learned = (datetime.utcnow() - first_learned).days
            if days_since_learned >= 21 and interval >= 21:
                return MemorizationStage.MATURE

        if interval < 21:
            return MemorizationStage.YOUNG

        return MemorizationStage.MATURE

    @staticmethod
    def estimate_retention(
        easiness_factor: float,
        days_since_review: int,
        interval: int,
    ) -> float:
        """
        Estimate current retention probability.

        Uses the forgetting curve formula:
        R = e^(-t/S)

        Where:
        - R is retention
        - t is time since last review
        - S is stability (related to interval and EF)
        """
        if interval == 0:
            return 0.0

        # Stability is proportional to interval and easiness
        stability = interval * (easiness_factor / 2.5)

        # Calculate retention
        retention = math.exp(-days_since_review / max(stability, 1))

        return min(1.0, max(0.0, retention))


# =============================================================================
# SPACED REPETITION SERVICE
# =============================================================================

class SpacedRepetitionService:
    """
    Quran memorization service using SM2 spaced repetition.

    Features:
    - Verse-level tracking
    - Juz/Hizb-based learning paths
    - Daily review scheduling
    - Progress analytics
    """

    def __init__(self):
        self._algorithm = SM2Algorithm()
        # In-memory storage (would be database in production)
        self._user_cards: Dict[str, Dict[int, VerseMemoryCard]] = {}
        self._user_stats: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, ReviewSession] = {}

    def _get_user_cards(self, user_id: str) -> Dict[int, VerseMemoryCard]:
        """Get or create user's card dictionary."""
        if user_id not in self._user_cards:
            self._user_cards[user_id] = {}
        return self._user_cards[user_id]

    async def add_verses_to_learn(
        self,
        user_id: str,
        verses: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Add verses to user's memorization queue.

        Arabic: إضافة آيات لقائمة الحفظ
        """
        cards = self._get_user_cards(user_id)
        added = 0

        for verse_data in verses:
            verse_id = verse_data.get("verse_id")
            if verse_id and verse_id not in cards:
                cards[verse_id] = VerseMemoryCard(
                    verse_id=verse_id,
                    sura_no=verse_data.get("sura_no", 0),
                    aya_no=verse_data.get("aya_no", 0),
                    verse_reference=verse_data.get("reference", ""),
                    text_uthmani=verse_data.get("text_uthmani", ""),
                    juz_no=verse_data.get("juz_no"),
                    hizb_no=verse_data.get("hizb_no"),
                    stage=MemorizationStage.NEW,
                )
                added += 1

        return {
            "user_id": user_id,
            "verses_added": added,
            "total_verses": len(cards),
            "message_ar": f"تمت إضافة {added} آية لقائمة الحفظ",
            "message_en": f"Added {added} verses to memorization queue",
        }

    async def get_due_reviews(
        self,
        user_id: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get verses due for review today.

        Arabic: الآيات المستحقة للمراجعة اليوم
        """
        cards = self._get_user_cards(user_id)
        now = datetime.utcnow()

        due_cards = []
        new_cards = []
        learning_cards = []

        for card in cards.values():
            if card.stage == MemorizationStage.SUSPENDED:
                continue

            if card.stage == MemorizationStage.NEW:
                new_cards.append(card)
            elif card.next_review and card.next_review <= now:
                due_cards.append(card)
            elif card.stage == MemorizationStage.LEARNING:
                learning_cards.append(card)

        # Sort due cards by overdue amount (most overdue first)
        due_cards.sort(
            key=lambda c: (now - c.next_review).total_seconds() if c.next_review else 0,
            reverse=True
        )

        # Collect cards for review
        review_cards = []

        # Add due cards first
        review_cards.extend(due_cards[:limit])

        # Add learning cards if room
        remaining = limit - len(review_cards)
        if remaining > 0:
            review_cards.extend(learning_cards[:remaining])

        # Add new cards if room (respect daily limit)
        remaining = min(limit - len(review_cards), DAILY_LIMITS["new_verses"])
        if remaining > 0:
            review_cards.extend(new_cards[:remaining])

        return {
            "user_id": user_id,
            "due_count": len(due_cards),
            "new_count": len(new_cards),
            "learning_count": len(learning_cards),
            "reviews": [
                {
                    "verse_id": c.verse_id,
                    "sura_no": c.sura_no,
                    "aya_no": c.aya_no,
                    "verse_reference": c.verse_reference,
                    "text_uthmani": c.text_uthmani,
                    "stage": c.stage.value,
                    "repetitions": c.repetitions,
                    "easiness_factor": round(c.easiness_factor, 2),
                    "interval": c.interval,
                    "days_overdue": (now - c.next_review).days if c.next_review and c.next_review < now else 0,
                }
                for c in review_cards[:limit]
            ],
            "total_to_review": len(review_cards),
        }

    async def record_review(
        self,
        user_id: str,
        verse_id: int,
        quality: int,
    ) -> Dict[str, Any]:
        """
        Record a review and calculate next interval using SM2.

        Args:
            quality: Quality of recall (0-5)
                0 = Complete blackout
                1 = Incorrect, recognized when shown
                2 = Incorrect, easy to recall after hint
                3 = Correct with significant difficulty
                4 = Correct with some hesitation
                5 = Perfect recall

        Arabic: تسجيل مراجعة وحساب الفاصل الزمني التالي
        """
        cards = self._get_user_cards(user_id)

        if verse_id not in cards:
            return {
                "error": "Verse not in memorization queue",
                "ar": "الآية ليست في قائمة الحفظ",
            }

        card = cards[verse_id]
        now = datetime.utcnow()

        # Get quality rating info
        quality_info = QUALITY_RATINGS.get(quality, QUALITY_RATINGS[3])

        # Calculate next interval using SM2
        new_interval, new_ef, new_reps = self._algorithm.calculate_next_interval(
            quality=quality,
            repetitions=card.repetitions,
            easiness_factor=card.easiness_factor,
            current_interval=card.interval,
        )

        # Update card
        old_interval = card.interval
        card.interval = new_interval
        card.easiness_factor = new_ef
        card.repetitions = new_reps
        card.next_review = now + timedelta(days=new_interval)
        card.last_review = now

        if card.first_learned is None:
            card.first_learned = now

        # Update statistics
        card.total_reviews += 1
        if quality >= SM2_CONFIG["success_threshold"]:
            card.successful_reviews += 1
        card.average_quality = (
            (card.average_quality * (card.total_reviews - 1) + quality) / card.total_reviews
        )

        # Update stage
        card.stage = self._algorithm.determine_stage(
            card.repetitions, card.interval, card.first_learned
        )

        return {
            "verse_id": verse_id,
            "verse_reference": card.verse_reference,
            "quality": quality,
            "quality_description": quality_info,
            "previous_interval": old_interval,
            "new_interval": new_interval,
            "next_review": card.next_review.isoformat(),
            "easiness_factor": round(new_ef, 2),
            "repetitions": new_reps,
            "stage": card.stage.value,
            "success": quality >= SM2_CONFIG["success_threshold"],
            "message_ar": f"المراجعة القادمة بعد {new_interval} يوم",
            "message_en": f"Next review in {new_interval} days",
        }

    async def get_memorization_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get comprehensive memorization statistics.

        Arabic: إحصائيات الحفظ الشاملة
        """
        cards = self._get_user_cards(user_id)
        now = datetime.utcnow()

        if not cards:
            return {
                "user_id": user_id,
                "total_verses": 0,
                "message_ar": "لم تبدأ الحفظ بعد",
                "message_en": "You haven't started memorizing yet",
            }

        # Count by stage
        stage_counts = {stage: 0 for stage in MemorizationStage}
        due_today = 0
        total_retention = 0
        retention_count = 0

        for card in cards.values():
            stage_counts[card.stage] += 1

            if card.next_review and card.next_review <= now:
                due_today += 1

            # Calculate estimated retention
            if card.last_review and card.interval > 0:
                days_since = (now - card.last_review).days
                retention = self._algorithm.estimate_retention(
                    card.easiness_factor, days_since, card.interval
                )
                total_retention += retention
                retention_count += 1

        avg_retention = total_retention / retention_count if retention_count > 0 else 0

        # Calculate streak (simplified)
        streak = self._user_stats.get(user_id, {}).get("streak", 0)

        # Estimate completion (verses not yet mature)
        not_mature = len(cards) - stage_counts[MemorizationStage.MATURE]
        est_days = int(not_mature * 3)  # Rough estimate

        return {
            "user_id": user_id,
            "total_verses": len(cards),
            "by_stage": {
                "new": stage_counts[MemorizationStage.NEW],
                "learning": stage_counts[MemorizationStage.LEARNING],
                "young": stage_counts[MemorizationStage.YOUNG],
                "mature": stage_counts[MemorizationStage.MATURE],
                "suspended": stage_counts[MemorizationStage.SUSPENDED],
            },
            "due_today": due_today,
            "streak_days": streak,
            "average_retention": round(avg_retention * 100, 1),
            "estimated_completion_days": est_days,
            "recommendations": self._get_recommendations(cards, stage_counts, due_today),
        }

    def _get_recommendations(
        self,
        cards: Dict[int, VerseMemoryCard],
        stage_counts: Dict[MemorizationStage, int],
        due_today: int,
    ) -> Dict[str, str]:
        """Generate personalized recommendations."""
        if due_today > 50:
            return {
                "ar": "لديك مراجعات كثيرة متراكمة، ركز على المراجعة اليوم",
                "en": "You have many overdue reviews, focus on reviewing today",
            }
        elif stage_counts[MemorizationStage.NEW] > 20:
            return {
                "ar": "لديك آيات جديدة كثيرة، تعلم بضع آيات كل يوم",
                "en": "You have many new verses, learn a few each day",
            }
        elif stage_counts[MemorizationStage.LEARNING] > 15:
            return {
                "ar": "ركز على إتقان الآيات في مرحلة التعلم قبل إضافة المزيد",
                "en": "Focus on mastering verses in learning stage before adding more",
            }
        elif stage_counts[MemorizationStage.MATURE] > len(cards) * 0.8:
            return {
                "ar": "أحسنت! أغلب آياتك محفوظة بشكل جيد",
                "en": "Great job! Most of your verses are well memorized",
            }
        else:
            return {
                "ar": "استمر في المراجعة اليومية للحفاظ على مستواك",
                "en": "Keep up daily reviews to maintain your progress",
            }

    async def get_learning_path(
        self,
        user_id: str,
        target: str = "juz",
        target_number: int = 30,
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """
        Get a structured learning path for a Juz or Hizb.

        Arabic: مسار تعلم منظم لجزء أو حزب
        """
        from app.models.quran import QuranVerse

        if session is None:
            return {
                "error": "Database session required",
            }

        # Get verses for target
        if target == "juz":
            result = await session.execute(
                select(QuranVerse).where(
                    QuranVerse.juz_no == target_number
                ).order_by(QuranVerse.sura_no, QuranVerse.aya_no)
            )
        else:  # hizb
            result = await session.execute(
                select(QuranVerse).where(
                    QuranVerse.hizb_no == target_number
                ).order_by(QuranVerse.sura_no, QuranVerse.aya_no)
            )

        verses = result.scalars().all()

        if not verses:
            return {
                "error": f"{target} {target_number} not found",
            }

        cards = self._get_user_cards(user_id)

        # Analyze progress
        memorized = 0
        learning = 0
        not_started = 0

        verse_list = []
        for verse in verses:
            card = cards.get(verse.id)
            if card:
                if card.stage in [MemorizationStage.MATURE, MemorizationStage.YOUNG]:
                    memorized += 1
                    status = "memorized"
                elif card.stage == MemorizationStage.LEARNING:
                    learning += 1
                    status = "learning"
                else:
                    not_started += 1
                    status = "not_started"
            else:
                not_started += 1
                status = "not_started"

            verse_list.append({
                "verse_id": verse.id,
                "sura_no": verse.sura_no,
                "aya_no": verse.aya_no,
                "reference": f"{verse.sura_no}:{verse.aya_no}",
                "status": status,
            })

        total = len(verses)
        progress = (memorized / total * 100) if total > 0 else 0

        # Calculate estimated days to completion
        if not_started + learning == 0:
            est_days = 0
        else:
            daily_rate = DAILY_LIMITS["new_verses"]
            est_days = math.ceil((not_started + learning) / daily_rate)

        return {
            "target_type": target,
            "target_number": target_number,
            "total_verses": total,
            "progress": {
                "memorized": memorized,
                "learning": learning,
                "not_started": not_started,
                "percentage": round(progress, 1),
            },
            "estimated_days": est_days,
            "daily_goal": min(DAILY_LIMITS["new_verses"], not_started),
            "verses": verse_list[:50],  # First 50 for preview
            "message_ar": f"تقدمك في الجزء {target_number}: {progress:.1f}%",
            "message_en": f"Your progress in {target} {target_number}: {progress:.1f}%",
        }

    async def suspend_verse(
        self,
        user_id: str,
        verse_id: int,
    ) -> Dict[str, Any]:
        """Suspend a verse from reviews."""
        cards = self._get_user_cards(user_id)

        if verse_id not in cards:
            return {"error": "Verse not found"}

        cards[verse_id].stage = MemorizationStage.SUSPENDED

        return {
            "verse_id": verse_id,
            "status": "suspended",
            "message_ar": "تم إيقاف مراجعة الآية مؤقتًا",
            "message_en": "Verse suspended from reviews",
        }

    async def unsuspend_verse(
        self,
        user_id: str,
        verse_id: int,
    ) -> Dict[str, Any]:
        """Unsuspend a verse to resume reviews."""
        cards = self._get_user_cards(user_id)

        if verse_id not in cards:
            return {"error": "Verse not found"}

        card = cards[verse_id]
        card.stage = self._algorithm.determine_stage(
            card.repetitions, card.interval, card.first_learned
        )
        card.next_review = datetime.utcnow()  # Due immediately

        return {
            "verse_id": verse_id,
            "status": card.stage.value,
            "message_ar": "تم استئناف مراجعة الآية",
            "message_en": "Verse resumed for reviews",
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

spaced_repetition_service = SpacedRepetitionService()
