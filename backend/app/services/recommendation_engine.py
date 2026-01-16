"""
Theme-Based Recommendation Engine.

Provides personalized verse and theme recommendations based on:
1. User's search and study history
2. Theme relationships and patterns
3. Cross-story connections
4. Collaborative filtering (popular among similar users)

Arabic: محرك التوصيات المبني على المواضيع
"""

import logging
from typing import List, Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ThemeRecommendation:
    """A theme recommendation."""
    theme_id: str
    theme_name_ar: str
    theme_name_en: str
    relevance_score: float
    reason: str
    reason_ar: str
    related_verses_count: int
    color: str


@dataclass
class VerseRecommendation:
    """A verse recommendation."""
    sura_no: int
    aya_no: int
    reference: str
    text_preview: str
    relevance_score: float
    reason: str
    reason_ar: str
    themes: List[str]


@dataclass
class ProphetRecommendation:
    """A prophet study recommendation."""
    prophet_name: str
    relevance_score: float
    themes: List[str]
    moral_lessons: Dict[str, List[str]]
    suggested_suras: List[int]
    reason: str
    reason_ar: str


# =============================================================================
# THEME RELATIONSHIP GRAPH
# =============================================================================

# Theme relationships for recommendation traversal
THEME_RELATIONSHIPS = {
    # Emotional themes relationships
    "patience": ["trials", "trust", "contentment", "gratitude", "hope"],
    "gratitude": ["contentment", "worship", "divine_mercy", "reward"],
    "trust": ["patience", "divine_power", "guidance", "submission"],
    "grief": ["patience", "hope", "divine_mercy", "comfort"],
    "hope": ["trust", "divine_mercy", "guidance", "reward"],
    "fear": ["worship", "afterlife", "punishment", "repentance"],
    "love": ["divine_mercy", "worship", "brotherhood", "family"],
    "repentance": ["divine_forgiveness", "hope", "guidance", "mercy"],
    "contentment": ["gratitude", "trust", "patience", "submission"],

    # Divine attribute themes
    "divine_mercy": ["divine_forgiveness", "hope", "love", "salvation"],
    "divine_justice": ["punishment", "reward", "afterlife", "judgment"],
    "divine_power": ["creation", "resurrection", "miracles", "trust"],
    "divine_wisdom": ["guidance", "law", "creation", "prophets"],
    "divine_forgiveness": ["repentance", "divine_mercy", "hope", "salvation"],

    # Consequence themes
    "punishment": ["fear", "divine_justice", "hellfire", "afterlife"],
    "reward": ["hope", "paradise", "gratitude", "good_deeds"],
    "hellfire": ["punishment", "fear", "afterlife", "warning"],
    "paradise": ["reward", "hope", "afterlife", "righteousness"],

    # Narrative themes
    "prophets": ["guidance", "patience", "trials", "divine_power"],
    "creation": ["divine_power", "nature", "tawheed", "resurrection"],
    "resurrection": ["afterlife", "divine_power", "creation", "judgment"],
    "salvation": ["divine_mercy", "divine_rescue", "hope", "faith"],

    # Social themes
    "family": ["love", "patience", "brotherhood", "trials"],
    "brotherhood": ["love", "community", "charity", "ethics"],
    "charity": ["gratitude", "brotherhood", "reward", "ethics"],
    "justice": ["divine_justice", "ethics", "law", "community"],
}


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================

class RecommendationEngine:
    """
    Engine for generating personalized theme and verse recommendations.

    Uses multiple signals:
    1. User history (themes explored, verses studied)
    2. Theme relationships (suggest related themes)
    3. Prophet connections (suggest related prophets)
    4. Popular content (collaborative signals)
    """

    def __init__(self):
        self._global_theme_popularity: Counter = Counter()
        self._global_prophet_popularity: Counter = Counter()
        self._theme_verse_cache: Dict[str, List[Dict]] = {}

    async def get_theme_recommendations(
        self,
        user_themes_explored: List[str],
        user_prophets_studied: List[str],
        study_goal: Optional[str] = None,
        limit: int = 5,
    ) -> List[ThemeRecommendation]:
        """
        Get personalized theme recommendations.

        Args:
            user_themes_explored: Themes user has already explored
            user_prophets_studied: Prophets user has studied
            study_goal: User's study goal (memorization, comprehension, etc.)
            limit: Maximum recommendations to return
        """
        from app.services.advanced_similarity import (
            THEME_LABELS_AR,
            THEME_COLORS,
            EXTENDED_THEME_KEYWORDS,
            PROPHETIC_THEMES,
        )

        recommendations = []
        explored_set = set(user_themes_explored)

        # Strategy 1: Related themes (expand from explored)
        related_themes = self._find_related_themes(explored_set)

        for theme_id, score in related_themes[:limit * 2]:
            if theme_id in explored_set:
                continue

            if theme_id not in THEME_LABELS_AR:
                continue

            recommendations.append(ThemeRecommendation(
                theme_id=theme_id,
                theme_name_ar=THEME_LABELS_AR.get(theme_id, theme_id),
                theme_name_en=theme_id.replace("_", " ").title(),
                relevance_score=score,
                reason=f"Related to themes you've explored",
                reason_ar="مرتبط بالمواضيع التي استكشفتها",
                related_verses_count=len(EXTENDED_THEME_KEYWORDS.get(theme_id, [])) * 10,
                color=THEME_COLORS.get(theme_id, "#6B7280"),
            ))

        # Strategy 2: Prophet-related themes
        for prophet in user_prophets_studied[:3]:
            if prophet in PROPHETIC_THEMES:
                prophet_themes = PROPHETIC_THEMES[prophet].get("themes", [])
                for theme in prophet_themes:
                    if theme not in explored_set and theme in THEME_LABELS_AR:
                        existing = next((r for r in recommendations if r.theme_id == theme), None)
                        if existing:
                            existing.relevance_score += 0.2
                        else:
                            recommendations.append(ThemeRecommendation(
                                theme_id=theme,
                                theme_name_ar=THEME_LABELS_AR.get(theme, theme),
                                theme_name_en=theme.replace("_", " ").title(),
                                relevance_score=0.7,
                                reason=f"Appears in Prophet {prophet}'s story",
                                reason_ar=f"يظهر في قصة النبي {prophet}",
                                related_verses_count=20,
                                color=THEME_COLORS.get(theme, "#6B7280"),
                            ))

        # Strategy 3: Goal-based recommendations
        goal_themes = self._get_goal_based_themes(study_goal, explored_set)
        for theme_id, reason_en, reason_ar in goal_themes:
            if theme_id in explored_set:
                continue

            existing = next((r for r in recommendations if r.theme_id == theme_id), None)
            if existing:
                existing.relevance_score += 0.15
            elif theme_id in THEME_LABELS_AR:
                recommendations.append(ThemeRecommendation(
                    theme_id=theme_id,
                    theme_name_ar=THEME_LABELS_AR.get(theme_id, theme_id),
                    theme_name_en=theme_id.replace("_", " ").title(),
                    relevance_score=0.6,
                    reason=reason_en,
                    reason_ar=reason_ar,
                    related_verses_count=15,
                    color=THEME_COLORS.get(theme_id, "#6B7280"),
                ))

        # Sort by relevance and return top results
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        return recommendations[:limit]

    def _find_related_themes(
        self,
        explored_themes: Set[str],
    ) -> List[Tuple[str, float]]:
        """Find themes related to explored themes."""
        related_scores: Counter = Counter()

        for theme in explored_themes:
            if theme in THEME_RELATIONSHIPS:
                for related in THEME_RELATIONSHIPS[theme]:
                    if related not in explored_themes:
                        related_scores[related] += 1.0

        # Also check reverse relationships
        for theme, relations in THEME_RELATIONSHIPS.items():
            if theme not in explored_themes:
                overlap = len(set(relations) & explored_themes)
                if overlap > 0:
                    related_scores[theme] += overlap * 0.5

        # Normalize scores
        max_score = max(related_scores.values()) if related_scores else 1
        normalized = [(t, s / max_score) for t, s in related_scores.most_common()]

        return normalized

    def _get_goal_based_themes(
        self,
        goal: Optional[str],
        explored: Set[str],
    ) -> List[Tuple[str, str, str]]:
        """Get themes recommended based on study goal."""
        goal_themes = {
            "memorization": [
                ("patience", "Essential for memorization journey", "أساسي في رحلة الحفظ"),
                ("repetition", "Key concept for memory retention", "مفهوم أساسي للاحتفاظ بالذاكرة"),
            ],
            "comprehension": [
                ("divine_wisdom", "Deepen understanding of meanings", "تعميق فهم المعاني"),
                ("guidance", "Core Quranic theme", "موضوع قرآني أساسي"),
                ("prophets", "Learn through prophetic stories", "التعلم من قصص الأنبياء"),
            ],
            "research": [
                ("creation", "Scientific themes in Quran", "المواضيع العلمية في القرآن"),
                ("history", "Historical narratives", "السرد التاريخي"),
                ("law", "Islamic jurisprudence themes", "مواضيع الفقه الإسلامي"),
            ],
            "reflection": [
                ("divine_mercy", "Contemplate Allah's mercy", "تأمل رحمة الله"),
                ("afterlife", "Reflect on the hereafter", "التأمل في الآخرة"),
                ("repentance", "Personal spiritual growth", "النمو الروحي الشخصي"),
            ],
        }

        return goal_themes.get(goal, [])

    async def get_prophet_recommendations(
        self,
        user_themes_explored: List[str],
        prophets_already_studied: List[str],
        limit: int = 3,
    ) -> List[ProphetRecommendation]:
        """
        Get prophet study recommendations based on themes explored.
        """
        from app.services.advanced_similarity import PROPHETIC_THEMES

        recommendations = []
        studied_set = set(prophets_already_studied)
        explored_themes = set(user_themes_explored)

        for prophet, data in PROPHETIC_THEMES.items():
            if prophet in studied_set:
                continue

            # Calculate relevance based on theme overlap
            prophet_themes = set(data.get("themes", []))
            theme_overlap = len(prophet_themes & explored_themes)

            # Also check related prophets
            related_bonus = 0
            for studied in prophets_already_studied:
                if studied in PROPHETIC_THEMES:
                    if prophet in PROPHETIC_THEMES[studied].get("related_prophets", []):
                        related_bonus = 0.3
                        break

            relevance = (theme_overlap / max(len(prophet_themes), 1)) * 0.7 + related_bonus

            if relevance > 0 or not explored_themes:
                # Default relevance for users with no history
                if not explored_themes:
                    relevance = 0.5 + random.random() * 0.3

                reason_en = f"Shares themes: {', '.join(prophet_themes & explored_themes)}" if theme_overlap > 0 else "Recommended prophet to study"
                reason_ar = f"يشترك في المواضيع: {', '.join(prophet_themes & explored_themes)}" if theme_overlap > 0 else "نبي موصى بدراسته"

                recommendations.append(ProphetRecommendation(
                    prophet_name=prophet,
                    relevance_score=relevance,
                    themes=list(prophet_themes),
                    moral_lessons=data.get("moral_lessons", {"ar": [], "en": []}),
                    suggested_suras=data.get("suras", []),
                    reason=reason_en,
                    reason_ar=reason_ar,
                ))

        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        return recommendations[:limit]

    async def get_cross_theme_exploration_path(
        self,
        start_theme: str,
        depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate an exploration path starting from a theme.

        Creates a graph of connected themes for interactive exploration.
        """
        from app.services.advanced_similarity import THEME_LABELS_AR, THEME_COLORS

        visited = set()
        nodes = []
        edges = []

        def explore(theme: str, current_depth: int):
            if current_depth > depth or theme in visited:
                return

            visited.add(theme)
            nodes.append({
                "id": theme,
                "label_ar": THEME_LABELS_AR.get(theme, theme),
                "label_en": theme.replace("_", " ").title(),
                "color": THEME_COLORS.get(theme, "#6B7280"),
                "depth": current_depth,
            })

            if theme in THEME_RELATIONSHIPS:
                for related in THEME_RELATIONSHIPS[theme][:4]:  # Limit connections
                    edges.append({
                        "source": theme,
                        "target": related,
                        "weight": 1.0 - (current_depth * 0.2),
                    })
                    explore(related, current_depth + 1)

        explore(start_theme, 0)

        return {
            "start_theme": start_theme,
            "nodes": nodes,
            "edges": edges,
            "total_themes": len(nodes),
        }

    async def get_verse_recommendations_for_theme(
        self,
        theme: str,
        verses_already_seen: List[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get verse recommendations for a specific theme.

        This would ideally query the database, but returns a structure
        for the verses that match the theme.
        """
        from app.services.advanced_similarity import EXTENDED_THEME_KEYWORDS

        seen_set = set(verses_already_seen)
        keywords = EXTENDED_THEME_KEYWORDS.get(theme, [])

        # This would need database access to get actual verses
        # For now, return the structure
        return {
            "theme": theme,
            "keywords": keywords,
            "message": "Query database for verses containing these keywords",
            "exclude_verses": list(seen_set),
            "limit": limit,
        }

    async def get_thematic_journey(
        self,
        start_theme: str,
        user_session_id: str,
        user_history: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a personalized thematic journey through the Quran.

        Creates a structured path through related themes with verse suggestions.
        """
        from app.services.advanced_similarity import (
            THEME_LABELS_AR,
            CROSS_STORY_THEMES,
        )

        journey_steps = []
        current_theme = start_theme
        visited = {start_theme}

        for step in range(5):  # 5-step journey
            step_info = {
                "step": step + 1,
                "theme": current_theme,
                "theme_ar": THEME_LABELS_AR.get(current_theme, current_theme),
                "theme_en": current_theme.replace("_", " ").title(),
                "description": "",
                "suggested_focus": "",
            }

            # Add description from cross-story themes if available
            if current_theme in CROSS_STORY_THEMES:
                step_info["description"] = CROSS_STORY_THEMES[current_theme].get("description_en", "")
                step_info["description_ar"] = CROSS_STORY_THEMES[current_theme].get("description_ar", "")

            journey_steps.append(step_info)

            # Find next theme
            if current_theme in THEME_RELATIONSHIPS:
                candidates = [t for t in THEME_RELATIONSHIPS[current_theme] if t not in visited]
                if candidates:
                    current_theme = candidates[0]
                    visited.add(current_theme)
                else:
                    break
            else:
                break

        return {
            "journey_id": f"journey_{start_theme}_{user_session_id[:8]}",
            "start_theme": start_theme,
            "steps": journey_steps,
            "total_steps": len(journey_steps),
            "estimated_study_time_minutes": len(journey_steps) * 15,
        }


# =============================================================================
# COLLABORATIVE FILTERING (SIMPLIFIED)
# =============================================================================

class CollaborativeRecommender:
    """
    Simplified collaborative filtering for recommendations.

    Tracks what themes/verses are popular among users with similar interests.
    """

    def __init__(self):
        # User profiles: session_id -> {themes: Counter, prophets: Counter}
        self._user_profiles: Dict[str, Dict[str, Counter]] = defaultdict(
            lambda: {"themes": Counter(), "prophets": Counter()}
        )

    async def update_user_profile(
        self,
        session_id: str,
        themes: List[str],
        prophets: List[str],
    ):
        """Update user profile with their interests."""
        self._user_profiles[session_id]["themes"].update(themes)
        self._user_profiles[session_id]["prophets"].update(prophets)

    async def find_similar_users(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[str]:
        """Find users with similar interests."""
        if session_id not in self._user_profiles:
            return []

        user_themes = set(self._user_profiles[session_id]["themes"].keys())

        similar = []
        for other_id, profile in self._user_profiles.items():
            if other_id == session_id:
                continue

            other_themes = set(profile["themes"].keys())
            similarity = len(user_themes & other_themes) / max(len(user_themes | other_themes), 1)

            if similarity > 0.2:
                similar.append((other_id, similarity))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in similar[:limit]]

    async def get_collaborative_recommendations(
        self,
        session_id: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Get theme recommendations based on what similar users explored.
        """
        similar_users = await self.find_similar_users(session_id)

        if not similar_users:
            return []

        user_themes = set(self._user_profiles[session_id]["themes"].keys())
        recommendations: Counter = Counter()

        for other_id in similar_users:
            other_themes = self._user_profiles[other_id]["themes"]
            for theme, count in other_themes.items():
                if theme not in user_themes:
                    recommendations[theme] += count

        return [theme for theme, _ in recommendations.most_common(limit)]


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

recommendation_engine = RecommendationEngine()
collaborative_recommender = CollaborativeRecommender()
