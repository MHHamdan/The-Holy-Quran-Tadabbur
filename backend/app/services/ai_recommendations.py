"""
Real-Time AI Recommendation Engine with Behavior Tracking.

Provides intelligent recommendations based on:
1. User behavior patterns and clickstream analysis
2. Collaborative filtering from similar users
3. Content-based filtering using embeddings
4. Real-time personalization
5. Feedback integration for continuous learning

Arabic: محرك التوصيات الذكية في الوقت الحقيقي
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math
import random

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class EventType(str, Enum):
    """User interaction event types."""
    SEARCH = "search"
    VIEW_VERSE = "view_verse"
    VIEW_TAFSIR = "view_tafsir"
    BOOKMARK = "bookmark"
    SHARE = "share"
    STUDY = "study"
    MEMORIZE = "memorize"
    COMPLETE_LESSON = "complete_lesson"
    RATING = "rating"
    DWELL_TIME = "dwell_time"


class RecommendationType(str, Enum):
    """Types of recommendations."""
    SIMILAR_VERSES = "similar_verses"
    RELATED_THEMES = "related_themes"
    NEXT_LESSON = "next_lesson"
    TAFSIR = "tafsir"
    PROPHET_STORY = "prophet_story"
    MEMORIZATION = "memorization"
    TRENDING = "trending"
    PERSONALIZED = "personalized"


# Event weights for preference scoring
EVENT_WEIGHTS = {
    EventType.SEARCH: 1.0,
    EventType.VIEW_VERSE: 1.5,
    EventType.VIEW_TAFSIR: 2.0,
    EventType.BOOKMARK: 3.0,
    EventType.SHARE: 3.5,
    EventType.STUDY: 2.5,
    EventType.MEMORIZE: 4.0,
    EventType.COMPLETE_LESSON: 3.0,
    EventType.RATING: 2.0,
    EventType.DWELL_TIME: 1.0,
}

# Decay factor for older events (per day)
TIME_DECAY_FACTOR = 0.95


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class UserEvent:
    """A user interaction event."""
    event_id: str
    user_id: str
    event_type: EventType
    timestamp: datetime
    # Content context
    content_type: str  # verse, sura, theme, tafsir, etc.
    content_id: str
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Computed
    weight: float = 1.0


@dataclass
class UserPreferences:
    """User's computed preferences."""
    user_id: str
    # Topic preferences (topic -> score)
    topic_scores: Dict[str, float] = field(default_factory=dict)
    # Sura preferences
    sura_scores: Dict[int, float] = field(default_factory=dict)
    # Theme preferences
    theme_scores: Dict[str, float] = field(default_factory=dict)
    # Scholar preferences (for Tafsir)
    scholar_scores: Dict[str, float] = field(default_factory=dict)
    # Prophet story preferences
    prophet_scores: Dict[str, float] = field(default_factory=dict)
    # Study patterns
    preferred_study_time: Optional[str] = None
    average_session_length: int = 0
    # Last updated
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Recommendation:
    """A single recommendation."""
    recommendation_id: str
    rec_type: RecommendationType
    content_type: str
    content_id: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    score: float
    reason_ar: str
    reason_en: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# AI RECOMMENDATION SERVICE
# =============================================================================

class AIRecommendationService:
    """
    Real-time AI-powered recommendation engine.

    Features:
    - Behavior tracking and analysis
    - Collaborative filtering
    - Content-based recommendations
    - Real-time personalization
    - Trending content detection
    """

    def __init__(self):
        # User events storage
        self._user_events: Dict[str, List[UserEvent]] = defaultdict(list)
        # Computed preferences
        self._user_preferences: Dict[str, UserPreferences] = {}
        # Global trending
        self._trending_cache: Dict[str, List[str]] = {}
        self._trending_updated: Optional[datetime] = None
        # Similar users cache
        self._similar_users: Dict[str, List[str]] = {}

    async def track_event(
        self,
        user_id: str,
        event_type: str,
        content_type: str,
        content_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Track a user interaction event.

        Arabic: تتبع حدث تفاعل المستخدم
        """
        try:
            evt_type = EventType(event_type)
        except ValueError:
            evt_type = EventType.VIEW_VERSE

        event = UserEvent(
            event_id=f"{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            event_type=evt_type,
            timestamp=datetime.utcnow(),
            content_type=content_type,
            content_id=content_id,
            metadata=metadata or {},
            weight=EVENT_WEIGHTS.get(evt_type, 1.0),
        )

        self._user_events[user_id].append(event)

        # Keep only last 1000 events per user
        if len(self._user_events[user_id]) > 1000:
            self._user_events[user_id] = self._user_events[user_id][-1000:]

        # Update preferences
        await self._update_preferences(user_id)

        return {
            "status": "tracked",
            "event_id": event.event_id,
            "event_type": evt_type.value,
            "content": f"{content_type}:{content_id}",
        }

    async def _update_preferences(self, user_id: str) -> None:
        """Update user preferences based on recent events."""
        events = self._user_events.get(user_id, [])

        if not events:
            return

        prefs = self._user_preferences.get(user_id, UserPreferences(user_id=user_id))

        now = datetime.utcnow()

        # Reset scores
        topic_scores = defaultdict(float)
        sura_scores = defaultdict(float)
        theme_scores = defaultdict(float)
        prophet_scores = defaultdict(float)
        scholar_scores = defaultdict(float)

        # Aggregate scores with time decay
        for event in events:
            days_ago = (now - event.timestamp).days
            time_weight = (TIME_DECAY_FACTOR ** days_ago)
            weighted_score = event.weight * time_weight

            # Update based on content type
            if event.content_type == "verse":
                try:
                    sura_no = int(event.content_id.split(":")[0])
                    sura_scores[sura_no] += weighted_score
                except:
                    pass

            elif event.content_type == "theme":
                theme_scores[event.content_id] += weighted_score

            elif event.content_type == "prophet":
                prophet_scores[event.content_id] += weighted_score

            elif event.content_type == "tafsir":
                scholar_scores[event.content_id] += weighted_score

            # Extract topics from metadata
            topics = event.metadata.get("topics", [])
            for topic in topics:
                topic_scores[topic] += weighted_score

        # Normalize and store
        prefs.topic_scores = dict(topic_scores)
        prefs.sura_scores = dict(sura_scores)
        prefs.theme_scores = dict(theme_scores)
        prefs.prophet_scores = dict(prophet_scores)
        prefs.scholar_scores = dict(scholar_scores)
        prefs.updated_at = now

        self._user_preferences[user_id] = prefs

    async def get_recommendations(
        self,
        user_id: str,
        rec_type: Optional[str] = None,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations for a user.

        Arabic: الحصول على توصيات مخصصة للمستخدم
        """
        prefs = self._user_preferences.get(user_id)

        if not prefs:
            # Return default recommendations for new users
            return await self._get_default_recommendations(limit)

        recommendations = []

        # Get recommendations based on type
        if rec_type:
            try:
                r_type = RecommendationType(rec_type)
                recs = await self._get_recommendations_by_type(prefs, r_type, limit, context)
                recommendations.extend(recs)
            except ValueError:
                pass
        else:
            # Get mixed recommendations
            for r_type in [
                RecommendationType.PERSONALIZED,
                RecommendationType.RELATED_THEMES,
                RecommendationType.TRENDING,
            ]:
                recs = await self._get_recommendations_by_type(prefs, r_type, limit // 3, context)
                recommendations.extend(recs)

        # Sort by score and limit
        recommendations.sort(key=lambda x: x.score, reverse=True)
        recommendations = recommendations[:limit]

        return {
            "user_id": user_id,
            "recommendations": [self._rec_to_dict(r) for r in recommendations],
            "count": len(recommendations),
            "personalized": prefs is not None,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _get_recommendations_by_type(
        self,
        prefs: UserPreferences,
        rec_type: RecommendationType,
        limit: int,
        context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Get recommendations of a specific type."""
        recommendations = []

        if rec_type == RecommendationType.PERSONALIZED:
            # Based on user's top themes
            top_themes = sorted(
                prefs.theme_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            for theme, score in top_themes:
                recommendations.append(Recommendation(
                    recommendation_id=f"theme_{theme}_{datetime.utcnow().timestamp()}",
                    rec_type=rec_type,
                    content_type="theme",
                    content_id=theme,
                    title_ar=f"موضوع: {theme}",
                    title_en=f"Theme: {theme}",
                    description_ar="موضوع يناسب اهتماماتك",
                    description_en="A theme matching your interests",
                    score=min(score / 10, 1.0),
                    reason_ar="بناءً على تصفحك السابق",
                    reason_en="Based on your browsing history",
                ))

        elif rec_type == RecommendationType.RELATED_THEMES:
            # Based on theme relationships
            themes_config = {
                "patience": ["trust", "trial", "reward"],
                "mercy": ["forgiveness", "love", "kindness"],
                "faith": ["prayer", "worship", "guidance"],
                "gratitude": ["blessing", "contentment", "worship"],
            }

            for theme in prefs.theme_scores.keys():
                related = themes_config.get(theme, [])
                for related_theme in related[:2]:
                    if related_theme not in prefs.theme_scores:
                        recommendations.append(Recommendation(
                            recommendation_id=f"related_{related_theme}_{datetime.utcnow().timestamp()}",
                            rec_type=rec_type,
                            content_type="theme",
                            content_id=related_theme,
                            title_ar=f"موضوع متصل: {related_theme}",
                            title_en=f"Related theme: {related_theme}",
                            description_ar=f"مرتبط بموضوع {theme}",
                            description_en=f"Related to {theme}",
                            score=0.7,
                            reason_ar=f"لأنك مهتم بـ {theme}",
                            reason_en=f"Because you're interested in {theme}",
                        ))

        elif rec_type == RecommendationType.TRENDING:
            # Get trending content
            trending = await self._get_trending_content()
            for item in trending[:limit]:
                recommendations.append(Recommendation(
                    recommendation_id=f"trending_{item}_{datetime.utcnow().timestamp()}",
                    rec_type=rec_type,
                    content_type="mixed",
                    content_id=item,
                    title_ar=f"شائع: {item}",
                    title_en=f"Trending: {item}",
                    description_ar="محتوى رائج بين المستخدمين",
                    description_en="Popular content among users",
                    score=0.6,
                    reason_ar="شائع هذا الأسبوع",
                    reason_en="Trending this week",
                ))

        elif rec_type == RecommendationType.SIMILAR_VERSES:
            # Context-based verse recommendations
            if context and "current_verse" in context:
                # Would query similar verses from embeddings
                pass

        elif rec_type == RecommendationType.TAFSIR:
            # Based on scholar preferences
            top_scholars = sorted(
                prefs.scholar_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            for scholar, score in top_scholars:
                recommendations.append(Recommendation(
                    recommendation_id=f"tafsir_{scholar}_{datetime.utcnow().timestamp()}",
                    rec_type=rec_type,
                    content_type="tafsir",
                    content_id=scholar,
                    title_ar=f"تفسير {scholar}",
                    title_en=f"Tafsir by {scholar}",
                    description_ar="من تفاسيرك المفضلة",
                    description_en="From your preferred Tafsirs",
                    score=min(score / 10, 1.0),
                    reason_ar="من مصادرك المفضلة",
                    reason_en="From your favorite sources",
                ))

        elif rec_type == RecommendationType.PROPHET_STORY:
            # Based on prophet story preferences
            top_prophets = sorted(
                prefs.prophet_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            for prophet, score in top_prophets:
                recommendations.append(Recommendation(
                    recommendation_id=f"prophet_{prophet}_{datetime.utcnow().timestamp()}",
                    rec_type=rec_type,
                    content_type="prophet",
                    content_id=prophet,
                    title_ar=f"قصة {prophet}",
                    title_en=f"Story of {prophet}",
                    description_ar="استكمل دراسة القصة",
                    description_en="Continue studying the story",
                    score=min(score / 10, 1.0),
                    reason_ar="من قصصك المفضلة",
                    reason_en="From your favorite stories",
                ))

        return recommendations[:limit]

    async def _get_default_recommendations(self, limit: int) -> Dict[str, Any]:
        """Get default recommendations for new users."""
        defaults = [
            Recommendation(
                recommendation_id="default_fatiha",
                rec_type=RecommendationType.PERSONALIZED,
                content_type="sura",
                content_id="1",
                title_ar="سورة الفاتحة",
                title_en="Surah Al-Fatiha",
                description_ar="أم الكتاب وأعظم سورة",
                description_en="The Mother of the Book",
                score=1.0,
                reason_ar="أفضل بداية للقرآن",
                reason_en="The best start to the Quran",
            ),
            Recommendation(
                recommendation_id="default_patience",
                rec_type=RecommendationType.RELATED_THEMES,
                content_type="theme",
                content_id="patience",
                title_ar="موضوع الصبر",
                title_en="Theme: Patience",
                description_ar="من أهم الموضوعات في القرآن",
                description_en="One of the most important themes",
                score=0.9,
                reason_ar="موضوع أساسي",
                reason_en="Fundamental theme",
            ),
            Recommendation(
                recommendation_id="default_yusuf",
                rec_type=RecommendationType.PROPHET_STORY,
                content_type="sura",
                content_id="12",
                title_ar="قصة يوسف",
                title_en="Story of Yusuf",
                description_ar="أحسن القصص",
                description_en="The best of stories",
                score=0.85,
                reason_ar="قصة ملهمة",
                reason_en="An inspiring story",
            ),
        ]

        return {
            "user_id": None,
            "recommendations": [self._rec_to_dict(r) for r in defaults[:limit]],
            "count": min(len(defaults), limit),
            "personalized": False,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _get_trending_content(self) -> List[str]:
        """Get trending content based on all users' activity."""
        # Check cache
        if self._trending_updated and (datetime.utcnow() - self._trending_updated).hours < 1:
            return self._trending_cache.get("all", [])

        # Aggregate recent events from all users
        content_counts = defaultdict(int)
        week_ago = datetime.utcnow() - timedelta(days=7)

        for user_events in self._user_events.values():
            for event in user_events:
                if event.timestamp >= week_ago:
                    content_counts[event.content_id] += event.weight

        # Sort by count
        trending = sorted(content_counts.items(), key=lambda x: x[1], reverse=True)
        trending_ids = [item[0] for item in trending[:20]]

        self._trending_cache["all"] = trending_ids
        self._trending_updated = datetime.utcnow()

        return trending_ids

    async def get_similar_users(
        self,
        user_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find users with similar preferences for collaborative filtering.

        Arabic: إيجاد المستخدمين ذوي الاهتمامات المشابهة
        """
        user_prefs = self._user_preferences.get(user_id)

        if not user_prefs:
            return []

        similarities = []

        for other_id, other_prefs in self._user_preferences.items():
            if other_id == user_id:
                continue

            # Calculate similarity based on theme preferences
            similarity = self._compute_preference_similarity(user_prefs, other_prefs)

            if similarity > 0.3:
                similarities.append({
                    "user_id": other_id,
                    "similarity": round(similarity, 3),
                })

        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:limit]

    def _compute_preference_similarity(
        self,
        prefs1: UserPreferences,
        prefs2: UserPreferences,
    ) -> float:
        """Compute similarity between two user preference profiles."""
        # Combine all themes from both users
        all_themes = set(prefs1.theme_scores.keys()) | set(prefs2.theme_scores.keys())

        if not all_themes:
            return 0.0

        # Compute cosine similarity on theme vectors
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0

        for theme in all_themes:
            score1 = prefs1.theme_scores.get(theme, 0)
            score2 = prefs2.theme_scores.get(theme, 0)

            dot_product += score1 * score2
            norm1 += score1 ** 2
            norm2 += score2 ** 2

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))

    async def get_collaborative_recommendations(
        self,
        user_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get recommendations based on similar users' preferences.

        Arabic: توصيات بناءً على تفضيلات المستخدمين المشابهين
        """
        similar_users = await self.get_similar_users(user_id, limit=10)

        if not similar_users:
            return await self._get_default_recommendations(limit)

        # Aggregate preferences from similar users
        aggregated_themes = defaultdict(float)
        aggregated_suras = defaultdict(float)

        user_prefs = self._user_preferences.get(user_id, UserPreferences(user_id=user_id))
        user_themes = set(user_prefs.theme_scores.keys())

        for similar in similar_users:
            other_id = similar["user_id"]
            similarity = similar["similarity"]
            other_prefs = self._user_preferences.get(other_id)

            if other_prefs:
                for theme, score in other_prefs.theme_scores.items():
                    if theme not in user_themes:
                        aggregated_themes[theme] += score * similarity

                for sura, score in other_prefs.sura_scores.items():
                    aggregated_suras[sura] += score * similarity

        # Create recommendations
        recommendations = []

        top_themes = sorted(aggregated_themes.items(), key=lambda x: x[1], reverse=True)[:5]
        for theme, score in top_themes:
            recommendations.append(Recommendation(
                recommendation_id=f"collab_theme_{theme}_{datetime.utcnow().timestamp()}",
                rec_type=RecommendationType.PERSONALIZED,
                content_type="theme",
                content_id=theme,
                title_ar=f"موضوع مقترح: {theme}",
                title_en=f"Suggested theme: {theme}",
                description_ar="أعجب المستخدمين المشابهين لك",
                description_en="Liked by users similar to you",
                score=min(score / 10, 1.0),
                reason_ar="من اهتمامات مستخدمين مشابهين",
                reason_en="From similar users' interests",
            ))

        return {
            "user_id": user_id,
            "recommendations": [self._rec_to_dict(r) for r in recommendations[:limit]],
            "count": len(recommendations),
            "similar_users_count": len(similar_users),
            "collaborative": True,
        }

    def _rec_to_dict(self, rec: Recommendation) -> Dict[str, Any]:
        """Convert Recommendation to dict."""
        return {
            "recommendation_id": rec.recommendation_id,
            "type": rec.rec_type.value,
            "content_type": rec.content_type,
            "content_id": rec.content_id,
            "title_ar": rec.title_ar,
            "title_en": rec.title_en,
            "description_ar": rec.description_ar,
            "description_en": rec.description_en,
            "score": round(rec.score, 3),
            "reason_ar": rec.reason_ar,
            "reason_en": rec.reason_en,
            "metadata": rec.metadata,
        }

    async def get_user_behavior_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get summary of user's behavior patterns.

        Arabic: ملخص أنماط سلوك المستخدم
        """
        events = self._user_events.get(user_id, [])
        prefs = self._user_preferences.get(user_id)

        if not events:
            return {
                "user_id": user_id,
                "has_activity": False,
                "message_ar": "لا يوجد نشاط مسجل بعد",
                "message_en": "No activity recorded yet",
            }

        # Analyze events
        event_counts = defaultdict(int)
        content_types = defaultdict(int)
        hourly_activity = defaultdict(int)

        for event in events:
            event_counts[event.event_type.value] += 1
            content_types[event.content_type] += 1
            hourly_activity[event.timestamp.hour] += 1

        # Find peak hours
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 12

        return {
            "user_id": user_id,
            "has_activity": True,
            "total_events": len(events),
            "event_breakdown": dict(event_counts),
            "content_breakdown": dict(content_types),
            "peak_activity_hour": peak_hour,
            "preferences": {
                "top_themes": sorted(
                    prefs.theme_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5] if prefs else [],
                "top_suras": sorted(
                    prefs.sura_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5] if prefs else [],
            },
            "insights": self._generate_behavior_insights(events, prefs),
        }

    def _generate_behavior_insights(
        self,
        events: List[UserEvent],
        prefs: Optional[UserPreferences],
    ) -> Dict[str, str]:
        """Generate insights from behavior patterns."""
        if len(events) < 5:
            return {
                "ar": "استمر في التصفح لنقدم لك توصيات أفضل",
                "en": "Continue browsing for better recommendations",
            }

        if prefs and prefs.theme_scores:
            top_theme = max(prefs.theme_scores.items(), key=lambda x: x[1])[0]
            return {
                "ar": f"أنت مهتم بشكل خاص بموضوع {top_theme}",
                "en": f"You're particularly interested in {top_theme}",
            }

        return {
            "ar": "أنت متعلم نشط، استمر!",
            "en": "You're an active learner, keep going!",
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

ai_recommendation_service = AIRecommendationService()
