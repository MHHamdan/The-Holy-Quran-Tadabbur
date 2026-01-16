"""
AI-Driven Personalization Service.

Provides personalized content recommendations and adaptive learning
based on user behavior, preferences, and study patterns.

Features:
1. User preference learning
2. Content-based recommendations
3. Adaptive difficulty adjustment
4. Study goal tracking
5. Personalized learning paths
6. Engagement optimization

Arabic: خدمة التخصيص المدفوعة بالذكاء الاصطناعي
"""

import logging
import math
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class UserLevel(str, Enum):
    """User proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SCHOLAR = "scholar"


class ContentType(str, Enum):
    """Types of content for recommendations."""
    VERSE = "verse"
    STORY = "story"
    TAFSIR = "tafsir"
    HADITH = "hadith"
    LEARNING_PATH = "learning_path"
    THEMATIC_STUDY = "thematic_study"
    PROPHET_STUDY = "prophet_study"


class InteractionType(str, Enum):
    """Types of user interactions to track."""
    SEARCH = "search"
    VIEW = "view"
    SAVE = "save"
    COMPLETE_LESSON = "complete_lesson"
    QUIZ_ATTEMPT = "quiz_attempt"
    ANNOTATION = "annotation"
    SHARE = "share"


@dataclass
class UserProfile:
    """Comprehensive user profile for personalization."""
    user_id: str
    level: UserLevel
    preferred_language: str
    theme_interests: Dict[str, float]  # theme -> interest score
    prophet_interests: Dict[str, float]
    content_preferences: Dict[str, float]  # content_type -> preference
    study_goals: List[str]
    daily_goal_minutes: int
    streak_days: int
    total_study_time_minutes: int
    created_at: datetime
    last_active: datetime


@dataclass
class UserInteraction:
    """Record of a user interaction."""
    interaction_id: str
    user_id: str
    interaction_type: InteractionType
    content_type: ContentType
    content_id: str
    metadata: Dict[str, Any]
    timestamp: datetime
    duration_seconds: int


@dataclass
class Recommendation:
    """A content recommendation."""
    recommendation_id: str
    content_type: ContentType
    content_id: str
    title_ar: str
    title_en: str
    relevance_score: float
    reason_ar: str
    reason_en: str
    matched_interests: List[str]


# =============================================================================
# SAMPLE CONTENT FOR RECOMMENDATIONS
# =============================================================================

SAMPLE_CONTENT = {
    "verses": [
        {
            "content_id": "2:45",
            "title_ar": "الصبر والصلاة",
            "title_en": "Patience and Prayer",
            "themes": ["patience", "worship", "guidance"],
            "difficulty": "beginner",
        },
        {
            "content_id": "3:139",
            "title_ar": "لا تحزنوا",
            "title_en": "Do Not Grieve",
            "themes": ["hope", "faith", "victory"],
            "difficulty": "beginner",
        },
        {
            "content_id": "12:87",
            "title_ar": "لا تيأسوا من روح الله",
            "title_en": "Do Not Despair of Allah's Mercy",
            "themes": ["hope", "mercy", "trust_in_allah"],
            "difficulty": "intermediate",
        },
        {
            "content_id": "94:5-6",
            "title_ar": "مع العسر يسرا",
            "title_en": "With Hardship Comes Ease",
            "themes": ["patience", "hope", "trust_in_allah"],
            "difficulty": "beginner",
        },
    ],
    "stories": [
        {
            "content_id": "yusuf_story",
            "title_ar": "قصة يوسف عليه السلام",
            "title_en": "Story of Yusuf (Joseph)",
            "themes": ["patience", "forgiveness", "trust_in_allah"],
            "prophets": ["yusuf"],
            "difficulty": "intermediate",
        },
        {
            "content_id": "musa_story",
            "title_ar": "قصة موسى عليه السلام",
            "title_en": "Story of Musa (Moses)",
            "themes": ["liberation", "faith", "patience", "justice"],
            "prophets": ["musa"],
            "difficulty": "intermediate",
        },
        {
            "content_id": "ibrahim_story",
            "title_ar": "قصة إبراهيم عليه السلام",
            "title_en": "Story of Ibrahim (Abraham)",
            "themes": ["sacrifice", "faith", "submission", "truth"],
            "prophets": ["ibrahim"],
            "difficulty": "intermediate",
        },
    ],
    "learning_paths": [
        {
            "content_id": "patience_comprehensive",
            "title_ar": "الصبر في القرآن الكريم",
            "title_en": "Patience in the Quran",
            "themes": ["patience", "trust_in_allah", "gratitude"],
            "difficulty": "beginner",
        },
        {
            "content_id": "prophetic_leadership",
            "title_ar": "القيادة النبوية",
            "title_en": "Prophetic Leadership",
            "themes": ["leadership", "patience", "justice"],
            "prophets": ["musa", "muhammad"],
            "difficulty": "advanced",
        },
    ],
    "thematic_studies": [
        {
            "content_id": "theme_mercy",
            "title_ar": "رحمة الله في القرآن",
            "title_en": "Allah's Mercy in the Quran",
            "themes": ["mercy", "forgiveness", "hope"],
            "difficulty": "beginner",
        },
        {
            "content_id": "theme_justice",
            "title_ar": "العدل في الإسلام",
            "title_en": "Justice in Islam",
            "themes": ["justice", "truth", "accountability"],
            "difficulty": "intermediate",
        },
    ],
}


# =============================================================================
# PERSONALIZATION SERVICE
# =============================================================================

class PersonalizationService:
    """
    AI-Driven Personalization for content recommendations.

    Features:
    - User preference learning from interactions
    - Content-based recommendation engine
    - Adaptive difficulty adjustment
    - Personalized study paths
    - Engagement optimization
    """

    def __init__(self):
        self._user_profiles: Dict[str, UserProfile] = {}
        self._user_interactions: Dict[str, List[UserInteraction]] = defaultdict(list)
        self._content_library = SAMPLE_CONTENT
        self._recommendation_cache: Dict[str, List[Recommendation]] = {}

    # ==========================================================================
    # USER PROFILE MANAGEMENT
    # ==========================================================================

    def create_user_profile(
        self,
        user_id: str,
        preferred_language: str = "en",
        initial_level: str = "beginner",
        daily_goal_minutes: int = 15,
        study_goals: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new user profile."""
        if user_id in self._user_profiles:
            return {"error": "User profile already exists"}

        profile = UserProfile(
            user_id=user_id,
            level=UserLevel(initial_level),
            preferred_language=preferred_language,
            theme_interests={},
            prophet_interests={},
            content_preferences={},
            study_goals=study_goals or [],
            daily_goal_minutes=daily_goal_minutes,
            streak_days=0,
            total_study_time_minutes=0,
            created_at=datetime.now(),
            last_active=datetime.now(),
        )

        self._user_profiles[user_id] = profile

        return {
            "user_id": user_id,
            "profile_created": True,
            "level": profile.level.value,
            "message_ar": "تم إنشاء ملفك الشخصي بنجاح",
            "message_en": "Your profile has been created successfully",
        }

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        if user_id not in self._user_profiles:
            return None

        profile = self._user_profiles[user_id]

        return {
            "user_id": profile.user_id,
            "level": profile.level.value,
            "preferred_language": profile.preferred_language,
            "theme_interests": dict(sorted(profile.theme_interests.items(), key=lambda x: x[1], reverse=True)[:5]),
            "prophet_interests": dict(sorted(profile.prophet_interests.items(), key=lambda x: x[1], reverse=True)[:3]),
            "content_preferences": profile.content_preferences,
            "study_goals": profile.study_goals,
            "daily_goal_minutes": profile.daily_goal_minutes,
            "streak_days": profile.streak_days,
            "total_study_time_minutes": profile.total_study_time_minutes,
            "member_since": profile.created_at.isoformat(),
            "last_active": profile.last_active.isoformat(),
        }

    def update_user_preferences(
        self,
        user_id: str,
        theme_interests: Optional[Dict[str, float]] = None,
        prophet_interests: Optional[Dict[str, float]] = None,
        study_goals: Optional[List[str]] = None,
        daily_goal_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update user preferences."""
        if user_id not in self._user_profiles:
            return {"error": "User not found"}

        profile = self._user_profiles[user_id]

        if theme_interests:
            profile.theme_interests.update(theme_interests)
        if prophet_interests:
            profile.prophet_interests.update(prophet_interests)
        if study_goals is not None:
            profile.study_goals = study_goals
        if daily_goal_minutes is not None:
            profile.daily_goal_minutes = daily_goal_minutes

        # Clear recommendation cache
        if user_id in self._recommendation_cache:
            del self._recommendation_cache[user_id]

        return {
            "user_id": user_id,
            "preferences_updated": True,
        }

    # ==========================================================================
    # INTERACTION TRACKING
    # ==========================================================================

    def record_interaction(
        self,
        user_id: str,
        interaction_type: str,
        content_type: str,
        content_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration_seconds: int = 0,
    ) -> Dict[str, Any]:
        """Record a user interaction for learning preferences."""
        # Auto-create profile if needed
        if user_id not in self._user_profiles:
            self.create_user_profile(user_id)

        interaction_id = hashlib.md5(
            f"{user_id}:{content_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        try:
            i_type = InteractionType(interaction_type)
            c_type = ContentType(content_type)
        except ValueError:
            return {"error": "Invalid interaction or content type"}

        interaction = UserInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            interaction_type=i_type,
            content_type=c_type,
            content_id=content_id,
            metadata=metadata or {},
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
        )

        self._user_interactions[user_id].append(interaction)

        # Update profile based on interaction
        self._update_profile_from_interaction(user_id, interaction)

        # Clear recommendation cache
        if user_id in self._recommendation_cache:
            del self._recommendation_cache[user_id]

        return {
            "interaction_id": interaction_id,
            "recorded": True,
        }

    def _update_profile_from_interaction(
        self,
        user_id: str,
        interaction: UserInteraction,
    ) -> None:
        """Update user profile based on interaction."""
        profile = self._user_profiles[user_id]
        profile.last_active = datetime.now()

        # Update study time
        profile.total_study_time_minutes += interaction.duration_seconds // 60

        # Update content preferences
        content_key = interaction.content_type.value
        profile.content_preferences[content_key] = profile.content_preferences.get(content_key, 0) + 1

        # Extract themes from content and update interests
        themes = interaction.metadata.get("themes", [])
        for theme in themes:
            # Weight by interaction type
            weight = {
                InteractionType.SEARCH: 0.5,
                InteractionType.VIEW: 1.0,
                InteractionType.SAVE: 2.0,
                InteractionType.COMPLETE_LESSON: 3.0,
                InteractionType.ANNOTATION: 2.5,
            }.get(interaction.interaction_type, 1.0)

            profile.theme_interests[theme] = profile.theme_interests.get(theme, 0) + weight

        # Extract prophets
        prophets = interaction.metadata.get("prophets", [])
        for prophet in prophets:
            weight = 1.5 if interaction.interaction_type == InteractionType.COMPLETE_LESSON else 1.0
            profile.prophet_interests[prophet] = profile.prophet_interests.get(prophet, 0) + weight

        # Update streak
        self._update_streak(profile)

        # Update level based on activity
        self._update_level(profile)

    def _update_streak(self, profile: UserProfile) -> None:
        """Update user's study streak."""
        today = datetime.now().date()
        last_active_date = profile.last_active.date()

        if last_active_date == today:
            pass  # Same day, no change
        elif last_active_date == today - timedelta(days=1):
            profile.streak_days += 1
        else:
            profile.streak_days = 1

    def _update_level(self, profile: UserProfile) -> None:
        """Update user level based on activity."""
        total_interactions = sum(len(ints) for ints in self._user_interactions.get(profile.user_id, []))

        if total_interactions >= 500 and profile.total_study_time_minutes >= 3000:
            profile.level = UserLevel.SCHOLAR
        elif total_interactions >= 200 and profile.total_study_time_minutes >= 1000:
            profile.level = UserLevel.ADVANCED
        elif total_interactions >= 50 and profile.total_study_time_minutes >= 200:
            profile.level = UserLevel.INTERMEDIATE

    # ==========================================================================
    # RECOMMENDATIONS
    # ==========================================================================

    def get_recommendations(
        self,
        user_id: str,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get personalized content recommendations."""
        if user_id not in self._user_profiles:
            # Return default recommendations for new users
            return self._get_default_recommendations(limit)

        # Check cache
        cache_key = f"{user_id}:{','.join(content_types or [])}:{limit}"
        if cache_key in self._recommendation_cache:
            return {
                "user_id": user_id,
                "recommendations": self._recommendation_cache[cache_key],
                "source": "cache",
            }

        profile = self._user_profiles[user_id]
        recommendations = []

        # Gather all content
        all_content = []
        for c_type, items in self._content_library.items():
            if content_types and c_type not in content_types:
                continue
            for item in items:
                all_content.append({**item, "category": c_type})

        # Score each content item
        for item in all_content:
            score, reasons = self._compute_relevance_score(profile, item)

            if score > 0.1:  # Minimum relevance threshold
                rec_id = hashlib.md5(f"{user_id}:{item['content_id']}".encode()).hexdigest()[:12]

                recommendations.append({
                    "recommendation_id": rec_id,
                    "content_type": item["category"],
                    "content_id": item["content_id"],
                    "title_ar": item["title_ar"],
                    "title_en": item["title_en"],
                    "relevance_score": round(score, 3),
                    "matched_interests": reasons[:3],
                    "difficulty": item.get("difficulty", "intermediate"),
                })

        # Sort by relevance
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_recs = recommendations[:limit]

        # Cache results
        self._recommendation_cache[cache_key] = top_recs

        return {
            "user_id": user_id,
            "recommendations": top_recs,
            "user_level": profile.level.value,
            "based_on": {
                "top_themes": list(profile.theme_interests.keys())[:3],
                "top_prophets": list(profile.prophet_interests.keys())[:2],
            },
        }

    def _compute_relevance_score(
        self,
        profile: UserProfile,
        item: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """Compute relevance score for a content item."""
        score = 0.0
        reasons = []

        # Theme matching
        item_themes = set(item.get("themes", []))
        for theme, interest in profile.theme_interests.items():
            if theme in item_themes:
                score += interest * 0.3
                reasons.append(f"Matches your interest in {theme}")

        # Prophet matching
        item_prophets = set(item.get("prophets", []))
        for prophet, interest in profile.prophet_interests.items():
            if prophet in item_prophets:
                score += interest * 0.4
                reasons.append(f"Features Prophet {prophet}")

        # Difficulty matching
        item_difficulty = item.get("difficulty", "intermediate")
        level_order = ["beginner", "intermediate", "advanced", "scholar"]

        try:
            user_level_idx = level_order.index(profile.level.value)
            item_level_idx = level_order.index(item_difficulty)

            # Prefer content at or slightly above user level
            level_diff = item_level_idx - user_level_idx
            if level_diff == 0:
                score += 0.2
                reasons.append("Matches your level")
            elif level_diff == 1:
                score += 0.15
                reasons.append("Slightly challenging")
            elif level_diff == -1:
                score += 0.1
                reasons.append("Good for reinforcement")
        except ValueError:
            pass

        # Content type preference
        content_type = item.get("category", "")
        if content_type in profile.content_preferences:
            score += profile.content_preferences[content_type] * 0.05
            reasons.append(f"You enjoy {content_type.replace('_', ' ')}")

        # Normalize score
        score = min(1.0, score / 2.0)

        return score, reasons

    def _get_default_recommendations(self, limit: int = 10) -> Dict[str, Any]:
        """Get default recommendations for new users."""
        recommendations = []

        # Add beginner-friendly content
        for category, items in self._content_library.items():
            for item in items:
                if item.get("difficulty") == "beginner":
                    rec_id = hashlib.md5(item["content_id"].encode()).hexdigest()[:12]
                    recommendations.append({
                        "recommendation_id": rec_id,
                        "content_type": category,
                        "content_id": item["content_id"],
                        "title_ar": item["title_ar"],
                        "title_en": item["title_en"],
                        "relevance_score": 0.8,
                        "matched_interests": ["Great for beginners"],
                        "difficulty": "beginner",
                    })

        return {
            "user_id": None,
            "recommendations": recommendations[:limit],
            "message": "Recommended content for new users",
        }

    def get_daily_recommendations(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get daily personalized recommendations."""
        recs = self.get_recommendations(user_id, limit=5)

        if user_id in self._user_profiles:
            profile = self._user_profiles[user_id]

            return {
                **recs,
                "daily_goal_minutes": profile.daily_goal_minutes,
                "streak_days": profile.streak_days,
                "greeting_ar": f"مرحباً! استمر في رحلتك - سلسلتك: {profile.streak_days} أيام",
                "greeting_en": f"Welcome back! Continue your journey - Streak: {profile.streak_days} days",
            }

        return recs

    def get_study_insights(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get study insights and analytics for user."""
        if user_id not in self._user_profiles:
            return {"error": "User not found"}

        profile = self._user_profiles[user_id]
        interactions = self._user_interactions.get(user_id, [])

        # Calculate insights
        last_7_days = [i for i in interactions if i.timestamp > datetime.now() - timedelta(days=7)]
        last_30_days = [i for i in interactions if i.timestamp > datetime.now() - timedelta(days=30)]

        # Activity by type
        activity_by_type = defaultdict(int)
        for i in last_30_days:
            activity_by_type[i.interaction_type.value] += 1

        # Theme exploration
        theme_exploration = {}
        for i in last_30_days:
            for theme in i.metadata.get("themes", []):
                theme_exploration[theme] = theme_exploration.get(theme, 0) + 1

        return {
            "user_id": user_id,
            "level": profile.level.value,
            "streak_days": profile.streak_days,
            "total_study_time_hours": round(profile.total_study_time_minutes / 60, 1),
            "weekly_activity": {
                "interactions": len(last_7_days),
                "study_days": len(set(i.timestamp.date() for i in last_7_days)),
            },
            "monthly_activity": {
                "interactions": len(last_30_days),
                "study_days": len(set(i.timestamp.date() for i in last_30_days)),
            },
            "activity_by_type": dict(activity_by_type),
            "theme_exploration": dict(sorted(theme_exploration.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_interests": {
                "themes": list(profile.theme_interests.keys())[:5],
                "prophets": list(profile.prophet_interests.keys())[:3],
            },
        }

    def suggest_next_study(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Suggest what to study next based on user's journey."""
        if user_id not in self._user_profiles:
            return {
                "suggestion_type": "new_user",
                "suggestion_ar": "ابدأ بتعلم أساسيات الصبر في القرآن",
                "suggestion_en": "Start by learning about patience in the Quran",
                "content_id": "patience_comprehensive",
                "content_type": "learning_path",
            }

        profile = self._user_profiles[user_id]
        interactions = self._user_interactions.get(user_id, [])

        # Get recent completions
        recent = [i for i in interactions[-20:] if i.interaction_type == InteractionType.COMPLETE_LESSON]

        # Suggest based on pattern
        if not recent:
            # User hasn't completed much - suggest their top interest
            if profile.theme_interests:
                top_theme = max(profile.theme_interests, key=profile.theme_interests.get)
                return {
                    "suggestion_type": "continue_interest",
                    "suggestion_ar": f"تعمق أكثر في موضوع {top_theme}",
                    "suggestion_en": f"Dive deeper into {top_theme}",
                    "recommended_content": self.get_recommendations(user_id, limit=3),
                }
            else:
                return {
                    "suggestion_type": "explore",
                    "suggestion_ar": "اكتشف قصص الأنبياء",
                    "suggestion_en": "Explore prophet stories",
                    "content_id": "yusuf_story",
                    "content_type": "story",
                }
        else:
            # Continue from where they left off
            last_content = recent[-1]
            return {
                "suggestion_type": "continue",
                "suggestion_ar": "أكمل ما بدأته",
                "suggestion_en": "Continue where you left off",
                "last_content_id": last_content.content_id,
                "last_content_type": last_content.content_type.value,
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "total_users": len(self._user_profiles),
            "total_interactions": sum(len(i) for i in self._user_interactions.values()),
            "cached_recommendations": len(self._recommendation_cache),
            "content_items": sum(len(items) for items in self._content_library.values()),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

personalization_service = PersonalizationService()
