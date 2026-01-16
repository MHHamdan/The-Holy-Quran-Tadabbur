"""
Adaptive Learning Paths Service.

Provides personalized learning experiences based on user patterns:
1. Learning style detection (visual, auditory, kinesthetic)
2. Pace adaptation based on performance
3. Content recommendations based on interests
4. Goal-oriented path generation
5. Progress analytics and insights

Arabic: خدمة مسارات التعلم التكيفية
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math

logger = logging.getLogger(__name__)


# =============================================================================
# LEARNING CONFIGURATION
# =============================================================================

class LearningStyle(str, Enum):
    """User learning styles."""
    VISUAL = "visual"           # Prefers reading, graphics
    AUDITORY = "auditory"       # Prefers listening, recitation
    KINESTHETIC = "kinesthetic" # Prefers practice, interaction
    MIXED = "mixed"             # Combination


class StudyGoal(str, Enum):
    """Study goals."""
    MEMORIZATION = "memorization"       # Hifz
    UNDERSTANDING = "understanding"     # Tadabbur
    RECITATION = "recitation"          # Tajweed
    TRANSLATION = "translation"        # Arabic to target language
    TAFSIR = "tafsir"                  # Deep interpretation
    DAILY_PRACTICE = "daily_practice"  # Regular reading


class DifficultyLevel(str, Enum):
    """Content difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningPace(str, Enum):
    """Learning pace preferences."""
    SLOW = "slow"           # 1-3 verses/day
    MODERATE = "moderate"   # 4-7 verses/day
    FAST = "fast"           # 8-15 verses/day
    INTENSIVE = "intensive" # 15+ verses/day


# Recommended content for each goal and level
LEARNING_PATHS = {
    StudyGoal.MEMORIZATION: {
        DifficultyLevel.BEGINNER: {
            "start_suras": [1, 112, 113, 114, 110, 108],  # Short suras
            "daily_target": 3,
            "techniques": [
                {"ar": "التكرار المتباعد", "en": "Spaced repetition"},
                {"ar": "الاستماع المتكرر", "en": "Repeated listening"},
            ],
            "resources": ["audio_recitation", "verse_by_verse"],
        },
        DifficultyLevel.INTERMEDIATE: {
            "start_suras": [67, 36, 55, 56],  # Medium suras
            "daily_target": 5,
            "techniques": [
                {"ar": "الربط بالمعاني", "en": "Meaning association"},
                {"ar": "المراجعة اليومية", "en": "Daily review"},
            ],
            "resources": ["translation", "tafsir_brief"],
        },
        DifficultyLevel.ADVANCED: {
            "start_suras": [2, 3, 4],  # Long suras
            "daily_target": 7,
            "techniques": [
                {"ar": "الحفظ بالصفحات", "en": "Page-based memorization"},
                {"ar": "الربط الموضوعي", "en": "Thematic connection"},
            ],
            "resources": ["tafsir_detailed", "word_analysis"],
        },
    },
    StudyGoal.UNDERSTANDING: {
        DifficultyLevel.BEGINNER: {
            "start_suras": [1, 112, 103, 99],
            "daily_target": 5,
            "techniques": [
                {"ar": "قراءة التفسير الميسر", "en": "Simple Tafsir reading"},
                {"ar": "التأمل في المعاني", "en": "Contemplating meanings"},
            ],
            "resources": ["tafsir_simple", "word_meanings"],
        },
        DifficultyLevel.INTERMEDIATE: {
            "start_suras": [12, 20, 28],  # Story suras
            "daily_target": 10,
            "techniques": [
                {"ar": "دراسة أسباب النزول", "en": "Studying revelation context"},
                {"ar": "المقارنة بين التفاسير", "en": "Comparing Tafsirs"},
            ],
            "resources": ["tafsir_comparative", "historical_context"],
        },
    },
    StudyGoal.RECITATION: {
        DifficultyLevel.BEGINNER: {
            "start_suras": [1, 112, 113, 114],
            "daily_target": 5,
            "techniques": [
                {"ar": "الاستماع والترديد", "en": "Listen and repeat"},
                {"ar": "تعلم مخارج الحروف", "en": "Learn letter articulation"},
            ],
            "resources": ["audio_teacher", "tajweed_basics"],
        },
        DifficultyLevel.INTERMEDIATE: {
            "start_suras": [36, 55, 67],
            "daily_target": 10,
            "techniques": [
                {"ar": "تطبيق أحكام التجويد", "en": "Apply Tajweed rules"},
                {"ar": "القراءة على شيخ", "en": "Recite to a teacher"},
            ],
            "resources": ["tajweed_advanced", "reciter_comparison"],
        },
    },
}

# Study session duration recommendations
SESSION_DURATIONS = {
    LearningPace.SLOW: {"min": 10, "max": 20, "optimal": 15},
    LearningPace.MODERATE: {"min": 20, "max": 40, "optimal": 30},
    LearningPace.FAST: {"min": 30, "max": 60, "optimal": 45},
    LearningPace.INTENSIVE: {"min": 45, "max": 90, "optimal": 60},
}


# =============================================================================
# USER LEARNING PROFILE
# =============================================================================

@dataclass
class StudySession:
    """A single study session record."""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    verses_studied: int = 0
    goal: Optional[StudyGoal] = None
    performance_score: float = 0.0  # 0-1
    topics_covered: List[str] = field(default_factory=list)


@dataclass
class LearningProfile:
    """User's learning profile with patterns and preferences."""
    user_id: str
    # Detected preferences
    learning_style: LearningStyle = LearningStyle.MIXED
    preferred_pace: LearningPace = LearningPace.MODERATE
    current_level: DifficultyLevel = DifficultyLevel.BEGINNER
    primary_goal: StudyGoal = StudyGoal.UNDERSTANDING
    # Study patterns
    preferred_times: List[str] = field(default_factory=list)  # e.g., ["morning", "evening"]
    average_session_duration: int = 20  # minutes
    sessions_per_week: int = 3
    # Progress tracking
    total_sessions: int = 0
    total_study_time: int = 0  # minutes
    verses_mastered: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    # Performance metrics
    average_retention: float = 0.0
    improvement_rate: float = 0.0
    # History
    sessions: List[StudySession] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    completed_suras: List[int] = field(default_factory=list)
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# ADAPTIVE LEARNING SERVICE
# =============================================================================

class AdaptiveLearningService:
    """
    Adaptive learning paths based on user patterns.

    Features:
    - Learning style detection
    - Pace adaptation
    - Content personalization
    - Goal-oriented paths
    - Progress insights
    """

    def __init__(self):
        self._profiles: Dict[str, LearningProfile] = {}
        self._learning_paths = LEARNING_PATHS

    def _get_profile(self, user_id: str) -> LearningProfile:
        """Get or create user's learning profile."""
        if user_id not in self._profiles:
            self._profiles[user_id] = LearningProfile(user_id=user_id)
        return self._profiles[user_id]

    async def initialize_profile(
        self,
        user_id: str,
        goal: str = "understanding",
        level: str = "beginner",
        pace: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Initialize a user's learning profile with preferences.

        Arabic: تهيئة ملف التعلم للمستخدم
        """
        profile = self._get_profile(user_id)

        try:
            profile.primary_goal = StudyGoal(goal)
        except ValueError:
            profile.primary_goal = StudyGoal.UNDERSTANDING

        try:
            profile.current_level = DifficultyLevel(level)
        except ValueError:
            profile.current_level = DifficultyLevel.BEGINNER

        try:
            profile.preferred_pace = LearningPace(pace)
        except ValueError:
            profile.preferred_pace = LearningPace.MODERATE

        # Generate initial path
        path = self._generate_learning_path(profile)

        return {
            "user_id": user_id,
            "profile": {
                "goal": profile.primary_goal.value,
                "level": profile.current_level.value,
                "pace": profile.preferred_pace.value,
                "learning_style": profile.learning_style.value,
            },
            "initial_path": path,
            "message_ar": "تم إعداد مسار التعلم الخاص بك",
            "message_en": "Your learning path has been set up",
        }

    def _generate_learning_path(self, profile: LearningProfile) -> Dict[str, Any]:
        """Generate personalized learning path based on profile."""
        goal = profile.primary_goal
        level = profile.current_level

        if goal in self._learning_paths and level in self._learning_paths[goal]:
            path_config = self._learning_paths[goal][level]
        else:
            # Default path
            path_config = {
                "start_suras": [1, 112, 113, 114],
                "daily_target": 3,
                "techniques": [
                    {"ar": "القراءة اليومية", "en": "Daily reading"},
                ],
                "resources": ["audio_recitation"],
            }

        # Adjust based on pace
        pace_multiplier = {
            LearningPace.SLOW: 0.5,
            LearningPace.MODERATE: 1.0,
            LearningPace.FAST: 1.5,
            LearningPace.INTENSIVE: 2.0,
        }

        adjusted_target = int(
            path_config["daily_target"] * pace_multiplier.get(profile.preferred_pace, 1.0)
        )

        session_duration = SESSION_DURATIONS.get(profile.preferred_pace, SESSION_DURATIONS[LearningPace.MODERATE])

        return {
            "goal": goal.value,
            "level": level.value,
            "recommended_suras": path_config["start_suras"][:5],
            "daily_target_verses": adjusted_target,
            "session_duration_minutes": session_duration["optimal"],
            "techniques": path_config["techniques"],
            "resources": path_config["resources"],
        }

    async def record_study_session(
        self,
        user_id: str,
        duration_minutes: int,
        verses_studied: int,
        goal: Optional[str] = None,
        performance: float = 0.7,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Record a study session and update user profile.

        Arabic: تسجيل جلسة دراسة وتحديث الملف الشخصي
        """
        profile = self._get_profile(user_id)

        session = StudySession(
            session_id=f"{user_id}_{datetime.utcnow().timestamp()}",
            started_at=datetime.utcnow() - timedelta(minutes=duration_minutes),
            ended_at=datetime.utcnow(),
            duration_minutes=duration_minutes,
            verses_studied=verses_studied,
            performance_score=performance,
            topics_covered=topics or [],
        )

        if goal:
            try:
                session.goal = StudyGoal(goal)
            except ValueError:
                pass

        # Update profile statistics
        profile.sessions.append(session)
        profile.total_sessions += 1
        profile.total_study_time += duration_minutes
        profile.last_active = datetime.utcnow()

        # Update average session duration
        profile.average_session_duration = profile.total_study_time // max(1, profile.total_sessions)

        # Update retention
        all_performances = [s.performance_score for s in profile.sessions if s.performance_score > 0]
        if all_performances:
            profile.average_retention = sum(all_performances) / len(all_performances)

        # Update streak
        self._update_streak(profile)

        # Adapt profile based on patterns
        self._adapt_profile(profile)

        return {
            "session_recorded": True,
            "session_id": session.session_id,
            "stats_updated": {
                "total_sessions": profile.total_sessions,
                "total_study_time_minutes": profile.total_study_time,
                "average_retention": round(profile.average_retention, 2),
                "current_streak": profile.current_streak,
            },
            "insights": self._generate_session_insights(session, profile),
        }

    def _update_streak(self, profile: LearningProfile) -> None:
        """Update study streak based on recent sessions."""
        if len(profile.sessions) < 2:
            profile.current_streak = 1
            return

        # Check if last session was within 24-48 hours of previous
        sorted_sessions = sorted(profile.sessions, key=lambda s: s.started_at, reverse=True)

        streak = 1
        for i in range(len(sorted_sessions) - 1):
            current = sorted_sessions[i].started_at
            previous = sorted_sessions[i + 1].started_at

            if (current - previous).days <= 1:
                streak += 1
            else:
                break

        profile.current_streak = streak
        profile.longest_streak = max(profile.longest_streak, streak)

    def _adapt_profile(self, profile: LearningProfile) -> None:
        """Adapt profile based on user patterns."""
        recent_sessions = profile.sessions[-10:]

        if len(recent_sessions) < 3:
            return

        # Detect pace from session durations
        avg_duration = sum(s.duration_minutes for s in recent_sessions) / len(recent_sessions)

        if avg_duration < 15:
            profile.preferred_pace = LearningPace.SLOW
        elif avg_duration < 35:
            profile.preferred_pace = LearningPace.MODERATE
        elif avg_duration < 55:
            profile.preferred_pace = LearningPace.FAST
        else:
            profile.preferred_pace = LearningPace.INTENSIVE

        # Detect level from performance
        avg_performance = profile.average_retention

        if avg_performance >= 0.9 and profile.total_sessions >= 20:
            if profile.current_level == DifficultyLevel.BEGINNER:
                profile.current_level = DifficultyLevel.INTERMEDIATE
            elif profile.current_level == DifficultyLevel.INTERMEDIATE:
                profile.current_level = DifficultyLevel.ADVANCED

    def _generate_session_insights(
        self,
        session: StudySession,
        profile: LearningProfile,
    ) -> Dict[str, str]:
        """Generate insights after a study session."""
        insights = {}

        if session.performance_score >= 0.9:
            insights["ar"] = "أداء ممتاز! استمر على هذا المستوى"
            insights["en"] = "Excellent performance! Keep up this level"
        elif session.performance_score >= 0.7:
            insights["ar"] = "أداء جيد، حاول المراجعة المنتظمة للتحسين"
            insights["en"] = "Good performance, try regular review to improve"
        else:
            insights["ar"] = "راجع المواد السابقة قبل المضي قدمًا"
            insights["en"] = "Review previous materials before moving forward"

        if profile.current_streak >= 7:
            insights["streak_ar"] = f"رائع! {profile.current_streak} أيام متتالية"
            insights["streak_en"] = f"Amazing! {profile.current_streak} consecutive days"

        return insights

    async def get_personalized_recommendations(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get personalized content recommendations based on user patterns.

        Arabic: توصيات محتوى مخصصة بناءً على أنماط المستخدم
        """
        profile = self._get_profile(user_id)

        # Generate learning path
        path = self._generate_learning_path(profile)

        # Next actions based on profile
        next_actions = []

        # Recommend based on gaps
        if profile.total_sessions == 0:
            next_actions.append({
                "action": "start_learning",
                "ar": "ابدأ أول جلسة دراسية",
                "en": "Start your first study session",
                "priority": "high",
            })
        elif profile.current_streak == 0:
            next_actions.append({
                "action": "resume_streak",
                "ar": "استأنف سلسلة المداومة",
                "en": "Resume your study streak",
                "priority": "high",
            })

        # Recommend reviews based on time
        if profile.total_sessions > 5:
            next_actions.append({
                "action": "review",
                "ar": "راجع ما تعلمته سابقًا",
                "en": "Review what you've learned",
                "priority": "medium",
            })

        # Recommend new content
        next_actions.append({
            "action": "new_content",
            "ar": f"تعلم {path['daily_target_verses']} آيات جديدة",
            "en": f"Learn {path['daily_target_verses']} new verses",
            "priority": "medium",
        })

        return {
            "user_id": user_id,
            "profile_summary": {
                "level": profile.current_level.value,
                "goal": profile.primary_goal.value,
                "pace": profile.preferred_pace.value,
                "streak": profile.current_streak,
            },
            "recommended_path": path,
            "next_actions": next_actions,
            "encouragement": self._get_encouragement(profile),
        }

    def _get_encouragement(self, profile: LearningProfile) -> Dict[str, str]:
        """Get personalized encouragement message."""
        if profile.current_streak >= 30:
            return {
                "ar": "ما شاء الله! شهر من المداومة، أنت قدوة",
                "en": "MashaAllah! A month of consistency, you're an example",
            }
        elif profile.current_streak >= 7:
            return {
                "ar": "أسبوع من المداومة! استمر",
                "en": "A week of consistency! Keep going",
            }
        elif profile.total_sessions > 20:
            return {
                "ar": "أنت تتقدم بشكل رائع",
                "en": "You're progressing wonderfully",
            }
        else:
            return {
                "ar": "كل رحلة تبدأ بخطوة، استمر!",
                "en": "Every journey begins with a step, keep going!",
            }

    async def get_daily_plan(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a personalized daily study plan.

        Arabic: إنشاء خطة دراسة يومية مخصصة
        """
        profile = self._get_profile(user_id)
        path = self._generate_learning_path(profile)

        session_duration = SESSION_DURATIONS.get(
            profile.preferred_pace,
            SESSION_DURATIONS[LearningPace.MODERATE]
        )

        # Build daily plan
        plan_items = []

        # Add warm-up
        plan_items.append({
            "order": 1,
            "type": "warmup",
            "activity_ar": "تلاوة الفاتحة وقصار السور",
            "activity_en": "Recite Al-Fatiha and short suras",
            "duration_minutes": 5,
        })

        # Add main study based on goal
        if profile.primary_goal == StudyGoal.MEMORIZATION:
            plan_items.append({
                "order": 2,
                "type": "new_content",
                "activity_ar": f"حفظ {path['daily_target_verses']} آيات جديدة",
                "activity_en": f"Memorize {path['daily_target_verses']} new verses",
                "duration_minutes": session_duration["optimal"] // 2,
            })
            plan_items.append({
                "order": 3,
                "type": "review",
                "activity_ar": "مراجعة المحفوظ السابق",
                "activity_en": "Review previous memorization",
                "duration_minutes": session_duration["optimal"] // 2,
            })
        elif profile.primary_goal == StudyGoal.UNDERSTANDING:
            plan_items.append({
                "order": 2,
                "type": "study",
                "activity_ar": f"قراءة وتدبر {path['daily_target_verses']} آيات",
                "activity_en": f"Read and contemplate {path['daily_target_verses']} verses",
                "duration_minutes": session_duration["optimal"] // 2,
            })
            plan_items.append({
                "order": 3,
                "type": "tafsir",
                "activity_ar": "قراءة التفسير",
                "activity_en": "Read Tafsir",
                "duration_minutes": session_duration["optimal"] // 2,
            })
        else:
            plan_items.append({
                "order": 2,
                "type": "study",
                "activity_ar": f"دراسة {path['daily_target_verses']} آيات",
                "activity_en": f"Study {path['daily_target_verses']} verses",
                "duration_minutes": session_duration["optimal"],
            })

        # Add closing
        plan_items.append({
            "order": len(plan_items) + 1,
            "type": "dua",
            "activity_ar": "الدعاء بالثبات والتوفيق",
            "activity_en": "Make dua for steadfastness and success",
            "duration_minutes": 2,
        })

        total_duration = sum(item["duration_minutes"] for item in plan_items)

        return {
            "user_id": user_id,
            "date": datetime.utcnow().date().isoformat(),
            "goal": profile.primary_goal.value,
            "total_duration_minutes": total_duration,
            "plan_items": plan_items,
            "techniques": path["techniques"],
            "motivation_ar": "اللهم علمنا ما ينفعنا وانفعنا بما علمتنا",
            "motivation_en": "O Allah, teach us what benefits us and benefit us from what You taught us",
        }

    async def get_progress_analytics(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed progress analytics and insights.

        Arabic: تحليلات التقدم والرؤى التفصيلية
        """
        profile = self._get_profile(user_id)

        # Calculate weekly stats
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_sessions = [s for s in profile.sessions if s.started_at >= week_ago]
        weekly_time = sum(s.duration_minutes for s in weekly_sessions)
        weekly_verses = sum(s.verses_studied for s in weekly_sessions)

        # Calculate improvement
        if len(profile.sessions) >= 10:
            recent_performance = sum(s.performance_score for s in profile.sessions[-5:]) / 5
            earlier_performance = sum(s.performance_score for s in profile.sessions[-10:-5]) / 5
            improvement = ((recent_performance - earlier_performance) / max(earlier_performance, 0.1)) * 100
        else:
            improvement = 0

        # Study pattern analysis
        study_times = {}
        for session in profile.sessions:
            hour = session.started_at.hour
            if 5 <= hour < 12:
                time_slot = "morning"
            elif 12 <= hour < 17:
                time_slot = "afternoon"
            elif 17 <= hour < 21:
                time_slot = "evening"
            else:
                time_slot = "night"

            study_times[time_slot] = study_times.get(time_slot, 0) + 1

        best_time = max(study_times.items(), key=lambda x: x[1])[0] if study_times else "morning"

        return {
            "user_id": user_id,
            "overall": {
                "total_sessions": profile.total_sessions,
                "total_study_time_hours": round(profile.total_study_time / 60, 1),
                "average_retention_percent": round(profile.average_retention * 100, 1),
                "current_streak": profile.current_streak,
                "longest_streak": profile.longest_streak,
                "current_level": profile.current_level.value,
            },
            "this_week": {
                "sessions": len(weekly_sessions),
                "study_time_minutes": weekly_time,
                "verses_studied": weekly_verses,
            },
            "trends": {
                "improvement_percent": round(improvement, 1),
                "best_study_time": best_time,
                "study_time_distribution": study_times,
            },
            "recommendations": self._generate_analytics_recommendations(profile, weekly_sessions),
        }

    def _generate_analytics_recommendations(
        self,
        profile: LearningProfile,
        weekly_sessions: List[StudySession],
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on analytics."""
        recommendations = []

        # Check consistency
        if len(weekly_sessions) < 3:
            recommendations.append({
                "type": "consistency",
                "ar": "حاول الدراسة على الأقل 3 مرات أسبوعيًا",
                "en": "Try to study at least 3 times per week",
            })

        # Check retention
        if profile.average_retention < 0.7:
            recommendations.append({
                "type": "retention",
                "ar": "ركز على المراجعة المتكررة لتحسين الحفظ",
                "en": "Focus on frequent review to improve retention",
            })

        # Check streak
        if profile.current_streak == 0 and profile.longest_streak > 0:
            recommendations.append({
                "type": "streak",
                "ar": f"رقمك القياسي {profile.longest_streak} أيام، حاول تجاوزه!",
                "en": f"Your record is {profile.longest_streak} days, try to beat it!",
            })

        if not recommendations:
            recommendations.append({
                "type": "encouragement",
                "ar": "أداؤك ممتاز، استمر!",
                "en": "Your performance is excellent, keep going!",
            })

        return recommendations

    async def get_adaptive_quiz(
        self,
        user_id: str,
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an adaptive quiz based on user's level and history.

        Arabic: اختبار تكيفي بناءً على مستوى المستخدم
        """
        profile = self._get_profile(user_id)

        # Adjust difficulty based on profile
        difficulty = profile.current_level

        # Sample questions (in real app, would come from database)
        questions = [
            {
                "id": 1,
                "type": "verse_completion",
                "difficulty": "beginner",
                "question_ar": "أكمل الآية: بِسْمِ اللَّهِ الرَّحْمَٰنِ ...",
                "question_en": "Complete the verse: Bismillah ar-Rahman...",
                "options": ["الرحيم", "الكريم", "العظيم", "الحليم"],
                "correct": 0,
                "verse_ref": "1:1",
            },
            {
                "id": 2,
                "type": "meaning",
                "difficulty": "beginner",
                "question_ar": "ما معنى 'الصمد' في سورة الإخلاص؟",
                "question_en": "What does 'As-Samad' mean in Surah Al-Ikhlas?",
                "options": [
                    "المستغني عن كل شيء والمحتاج إليه كل شيء",
                    "القادر على كل شيء",
                    "العالم بكل شيء",
                    "الرحيم بعباده",
                ],
                "correct": 0,
                "verse_ref": "112:2",
            },
            {
                "id": 3,
                "type": "sura_identification",
                "difficulty": "intermediate",
                "question_ar": "في أي سورة وردت آية الكرسي؟",
                "question_en": "In which Surah is Ayat al-Kursi mentioned?",
                "options": ["البقرة", "آل عمران", "النساء", "المائدة"],
                "correct": 0,
                "verse_ref": "2:255",
            },
        ]

        # Filter by difficulty
        difficulty_order = [d.value for d in DifficultyLevel]
        current_idx = difficulty_order.index(difficulty.value)
        allowed_difficulties = difficulty_order[:current_idx + 2]

        filtered_questions = [
            q for q in questions
            if q["difficulty"] in allowed_difficulties
        ]

        return {
            "user_id": user_id,
            "quiz_id": f"quiz_{datetime.utcnow().timestamp()}",
            "difficulty": difficulty.value,
            "questions": filtered_questions[:5],
            "time_limit_minutes": 10,
            "instructions_ar": "أجب على الأسئلة التالية لقياس تقدمك",
            "instructions_en": "Answer the following questions to measure your progress",
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

adaptive_learning_service = AdaptiveLearningService()
