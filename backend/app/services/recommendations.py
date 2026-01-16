"""
Content Recommendations Service.

Provides personalized content recommendations based on:
- User interaction history
- Content similarity (semantic)
- Popular/trending content
- Thematic relationships

Arabic: خدمة التوصيات والمحتوى المقترح
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content for recommendations."""
    VERSE = "verse"
    SURAH = "surah"
    TAFSEER = "tafseer"
    THEME = "theme"
    PROPHET = "prophet"
    STORY = "story"
    CONCEPT = "concept"


@dataclass
class Recommendation:
    """A single recommendation."""
    content_type: ContentType
    content_id: str
    title: str
    title_ar: str
    description: str = ""
    description_ar: str = ""
    relevance_score: float = 1.0
    reason: str = ""  # Why this was recommended
    reason_ar: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserInteraction:
    """Record of user interaction with content."""
    user_id: str
    content_type: ContentType
    content_id: str
    interaction_type: str  # view, search, bookmark, share
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# RECOMMENDATION DATA
# =============================================================================

# Related content mappings (thematic connections)
RELATED_VERSES = {
    # Ayat al-Kursi connections
    "2:255": ["2:256", "2:257", "3:2", "20:14", "59:22", "59:23"],
    # Al-Fatiha connections
    "1:1": ["1:2", "1:3", "1:4", "1:5", "1:6", "1:7", "17:110"],
    # Last verses of Al-Baqarah
    "2:285": ["2:286", "3:193", "4:136"],
    "2:286": ["2:285", "7:42", "23:62"],
}

# Prophet story connections
PROPHET_RELATED_CONTENT = {
    "musa": {
        "surahs": [7, 10, 20, 26, 28],
        "themes": ["صبر", "توكل", "رسالة"],
        "related_prophets": ["harun", "ibrahim", "isa"],
    },
    "ibrahim": {
        "surahs": [2, 6, 14, 21, 37],
        "themes": ["توحيد", "إيمان", "تضحية"],
        "related_prophets": ["ismail", "ishaq", "lut"],
    },
    "yusuf": {
        "surahs": [12],
        "themes": ["صبر", "عفة", "مغفرة"],
        "related_prophets": ["yaqub", "ibrahim"],
    },
    "isa": {
        "surahs": [3, 5, 19, 61],
        "themes": ["معجزات", "رسالة", "توحيد"],
        "related_prophets": ["maryam", "yahya", "zakariya"],
    },
    "muhammad": {
        "surahs": [33, 47, 48, 61],
        "themes": ["رحمة", "قرآن", "سنة"],
        "related_prophets": ["ibrahim", "musa", "isa"],
    },
}

# Theme connections
THEME_RELATIONSHIPS = {
    "صبر": ["توكل", "شكر", "تقوى", "يقين"],
    "توبة": ["مغفرة", "رحمة", "استغفار"],
    "إيمان": ["توحيد", "تقوى", "يقين", "إسلام"],
    "رحمة": ["مغفرة", "عفو", "كرم"],
    "عدل": ["قسط", "إنصاف", "حق"],
    "هداية": ["نور", "صراط", "رشد"],
}

# Popular verses (commonly accessed)
POPULAR_VERSES = [
    ("2:255", "آية الكرسي", "Ayat al-Kursi"),
    ("1:1", "بسم الله الرحمن الرحيم", "Bismillah"),
    ("112:1", "قل هو الله أحد", "Al-Ikhlas"),
    ("2:286", "لا يكلف الله نفساً إلا وسعها", "Allah does not burden a soul"),
    ("3:185", "كل نفس ذائقة الموت", "Every soul shall taste death"),
    ("94:5", "إن مع العسر يسراً", "With hardship comes ease"),
    ("2:152", "فاذكروني أذكركم", "Remember Me, I will remember you"),
    ("33:56", "صلوا عليه وسلموا تسليماً", "Send blessings upon him"),
]


class RecommendationsService:
    """
    Service for generating personalized content recommendations.

    Uses multiple signals:
    - User viewing history
    - Content similarity
    - Thematic relationships
    - Popularity
    """

    def __init__(self):
        # In-memory storage for user interactions (use DB in production)
        self._interactions: Dict[str, List[UserInteraction]] = defaultdict(list)
        self._view_counts: Dict[str, int] = defaultdict(int)

    def record_interaction(
        self,
        user_id: str,
        content_type: ContentType,
        content_id: str,
        interaction_type: str = "view",
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Record a user interaction with content."""
        interaction = UserInteraction(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            interaction_type=interaction_type,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._interactions[user_id].append(interaction)

        # Update view counts
        key = f"{content_type.value}:{content_id}"
        self._view_counts[key] += 1

        # Keep only last 100 interactions per user
        if len(self._interactions[user_id]) > 100:
            self._interactions[user_id] = self._interactions[user_id][-100:]

    def get_recommendations_for_verse(
        self,
        verse_ref: str,
        limit: int = 5,
    ) -> List[Recommendation]:
        """
        Get recommendations based on a verse reference.

        Args:
            verse_ref: Verse reference (e.g., "2:255")
            limit: Max recommendations

        Returns:
            List of related content recommendations
        """
        recommendations = []

        # Get directly related verses
        if verse_ref in RELATED_VERSES:
            for related_ref in RELATED_VERSES[verse_ref][:limit]:
                surah, ayah = related_ref.split(":")
                recommendations.append(Recommendation(
                    content_type=ContentType.VERSE,
                    content_id=related_ref,
                    title=f"Verse {related_ref}",
                    title_ar=f"آية {related_ref}",
                    relevance_score=0.9,
                    reason="Thematically related verse",
                    reason_ar="آية مرتبطة موضوعياً",
                    metadata={"surah": int(surah), "ayah": int(ayah)},
                ))

        return recommendations[:limit]

    def get_recommendations_for_prophet(
        self,
        prophet_key: str,
        limit: int = 10,
    ) -> List[Recommendation]:
        """
        Get recommendations for content related to a Prophet.

        Args:
            prophet_key: Prophet key (e.g., "musa", "ibrahim")
            limit: Max recommendations

        Returns:
            List of related content recommendations
        """
        recommendations = []
        prophet_key = prophet_key.lower()

        if prophet_key not in PROPHET_RELATED_CONTENT:
            return recommendations

        data = PROPHET_RELATED_CONTENT[prophet_key]

        # Related surahs
        for surah_num in data.get("surahs", [])[:3]:
            recommendations.append(Recommendation(
                content_type=ContentType.SURAH,
                content_id=str(surah_num),
                title=f"Surah {surah_num}",
                title_ar=f"سورة {surah_num}",
                relevance_score=0.85,
                reason=f"Contains stories of {prophet_key.title()}",
                reason_ar=f"تحتوي على قصص {prophet_key}",
                metadata={"surah_number": surah_num},
            ))

        # Related themes
        for theme in data.get("themes", [])[:3]:
            recommendations.append(Recommendation(
                content_type=ContentType.THEME,
                content_id=theme,
                title=theme,
                title_ar=theme,
                relevance_score=0.75,
                reason=f"Theme from {prophet_key.title()}'s story",
                reason_ar=f"موضوع من قصة {prophet_key}",
            ))

        # Related prophets
        for related_prophet in data.get("related_prophets", [])[:2]:
            recommendations.append(Recommendation(
                content_type=ContentType.PROPHET,
                content_id=related_prophet,
                title=related_prophet.title(),
                title_ar=related_prophet,
                relevance_score=0.7,
                reason="Related prophet",
                reason_ar="نبي ذو صلة",
            ))

        return recommendations[:limit]

    def get_recommendations_for_theme(
        self,
        theme: str,
        limit: int = 5,
    ) -> List[Recommendation]:
        """
        Get recommendations for content related to a theme.

        Args:
            theme: Theme key (e.g., "صبر", "توبة")
            limit: Max recommendations

        Returns:
            List of related theme recommendations
        """
        recommendations = []

        if theme in THEME_RELATIONSHIPS:
            for related_theme in THEME_RELATIONSHIPS[theme][:limit]:
                recommendations.append(Recommendation(
                    content_type=ContentType.THEME,
                    content_id=related_theme,
                    title=related_theme,
                    title_ar=related_theme,
                    relevance_score=0.8,
                    reason=f"Related to {theme}",
                    reason_ar=f"مرتبط بـ {theme}",
                ))

        return recommendations

    def get_personalized_recommendations(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Recommendation]:
        """
        Get personalized recommendations based on user history.

        Args:
            user_id: User identifier
            limit: Max recommendations

        Returns:
            List of personalized recommendations
        """
        recommendations = []
        user_interactions = self._interactions.get(user_id, [])

        if not user_interactions:
            # Return popular content for new users
            return self.get_popular_recommendations(limit)

        # Analyze user interests
        viewed_content: Set[str] = set()
        interest_types: Dict[ContentType, int] = defaultdict(int)

        for interaction in user_interactions[-20:]:  # Last 20 interactions
            viewed_content.add(f"{interaction.content_type.value}:{interaction.content_id}")
            interest_types[interaction.content_type] += 1

        # Get related content for recent views
        for interaction in user_interactions[-5:]:  # Last 5 views
            if interaction.content_type == ContentType.VERSE:
                related = self.get_recommendations_for_verse(
                    interaction.content_id, limit=2
                )
                for rec in related:
                    key = f"{rec.content_type.value}:{rec.content_id}"
                    if key not in viewed_content:
                        rec.reason = "Based on your recent views"
                        rec.reason_ar = "بناءً على مشاهداتك الأخيرة"
                        recommendations.append(rec)

        # Fill with popular if needed
        if len(recommendations) < limit:
            popular = self.get_popular_recommendations(limit - len(recommendations))
            for rec in popular:
                key = f"{rec.content_type.value}:{rec.content_id}"
                if key not in viewed_content:
                    recommendations.append(rec)

        return recommendations[:limit]

    def get_popular_recommendations(
        self,
        limit: int = 10,
    ) -> List[Recommendation]:
        """
        Get popular content recommendations.

        Returns most viewed/accessed content.
        """
        recommendations = []

        for verse_ref, title_ar, title_en in POPULAR_VERSES[:limit]:
            surah, ayah = verse_ref.split(":")
            recommendations.append(Recommendation(
                content_type=ContentType.VERSE,
                content_id=verse_ref,
                title=title_en,
                title_ar=title_ar,
                relevance_score=0.9,
                reason="Popular verse",
                reason_ar="آية شائعة",
                metadata={"surah": int(surah), "ayah": int(ayah)},
            ))

        return recommendations

    def get_similar_content(
        self,
        content_type: ContentType,
        content_id: str,
        limit: int = 5,
    ) -> List[Recommendation]:
        """
        Get similar content based on type and ID.

        Routes to appropriate recommendation method.
        """
        if content_type == ContentType.VERSE:
            return self.get_recommendations_for_verse(content_id, limit)
        elif content_type == ContentType.PROPHET:
            return self.get_recommendations_for_prophet(content_id, limit)
        elif content_type == ContentType.THEME:
            return self.get_recommendations_for_theme(content_id, limit)
        else:
            return self.get_popular_recommendations(limit)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_recommendations_service: Optional[RecommendationsService] = None


def get_recommendations_service() -> RecommendationsService:
    """Get the recommendations service singleton."""
    global _recommendations_service
    if _recommendations_service is None:
        _recommendations_service = RecommendationsService()
    return _recommendations_service
