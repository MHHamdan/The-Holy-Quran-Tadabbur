"""
Search History & Personalization Service

Tracks user search history and provides personalized suggestions:
- Recent searches storage
- Search frequency analysis
- Related verse suggestions based on history
- Popular searches aggregation
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from collections import Counter, defaultdict
import json
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SearchEntry:
    """Represents a single search entry."""
    query: str
    query_type: str  # 'text', 'verse', 'semantic', 'similar'
    timestamp: datetime
    result_count: int = 0
    clicked_verses: List[str] = field(default_factory=list)
    session_id: Optional[str] = None


@dataclass
class SearchSuggestion:
    """A search suggestion based on history."""
    query: str
    query_type: str
    frequency: int
    last_used: datetime
    relevance_score: float


@dataclass
class VerseRecommendation:
    """A verse recommendation based on search history."""
    sura_no: int
    aya_no: int
    reference: str
    text_uthmani: str
    sura_name_ar: str
    sura_name_en: str
    reason: str  # Why this verse is recommended
    reason_ar: str
    confidence: float


@dataclass
class SimilarityFeedback:
    """User feedback on a similarity result."""
    source_reference: str      # e.g., "2:255"
    target_reference: str      # e.g., "3:18"
    is_relevant: bool          # True if user marked as relevant
    feedback_type: str         # "thumbs_up", "thumbs_down", "rating"
    rating: Optional[float] = None  # 1-5 scale rating if provided
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    notes: Optional[str] = None  # Optional user comment


class SearchHistoryService:
    """
    Service for managing search history and personalization.

    Uses in-memory storage with optional persistence.
    Designed to work both per-session and aggregated.
    """

    def __init__(self, max_history_per_session: int = 100):
        self.max_history_per_session = max_history_per_session
        # In-memory storage: session_id -> list of SearchEntry
        self._session_history: Dict[str, List[SearchEntry]] = defaultdict(list)
        # Global search counts for popularity
        self._global_search_counts: Counter = Counter()
        # Verse click counts
        self._verse_clicks: Counter = Counter()
        # Theme/concept interest tracking
        self._theme_interests: Dict[str, Counter] = defaultdict(Counter)
        # Similarity feedback storage: (source_ref, target_ref) -> list of feedback
        self._similarity_feedback: Dict[tuple, List[SimilarityFeedback]] = defaultdict(list)
        # Session-based feedback: session_id -> list of feedback
        self._session_feedback: Dict[str, List[SimilarityFeedback]] = defaultdict(list)
        # Aggregated relevance scores: (source_ref, target_ref) -> (positive_count, total_count)
        self._relevance_scores: Dict[tuple, tuple] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def record_search(
        self,
        session_id: str,
        query: str,
        query_type: str,
        result_count: int = 0,
        themes: Optional[List[str]] = None,
    ) -> None:
        """Record a search in the history."""
        async with self._lock:
            entry = SearchEntry(
                query=query,
                query_type=query_type,
                timestamp=datetime.utcnow(),
                result_count=result_count,
                session_id=session_id,
            )

            # Add to session history
            history = self._session_history[session_id]
            history.append(entry)

            # Trim if too long
            if len(history) > self.max_history_per_session:
                self._session_history[session_id] = history[-self.max_history_per_session:]

            # Update global counts
            self._global_search_counts[query.lower()] += 1

            # Track theme interests
            if themes:
                for theme in themes:
                    self._theme_interests[session_id][theme] += 1

    async def record_verse_click(
        self,
        session_id: str,
        sura_no: int,
        aya_no: int,
        context: str = "search",
    ) -> None:
        """Record a verse click/view."""
        async with self._lock:
            verse_ref = f"{sura_no}:{aya_no}"
            self._verse_clicks[verse_ref] += 1

            # Update last search entry with clicked verse if available
            history = self._session_history.get(session_id, [])
            if history:
                last_entry = history[-1]
                if verse_ref not in last_entry.clicked_verses:
                    last_entry.clicked_verses.append(verse_ref)

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 20,
        query_type: Optional[str] = None,
    ) -> List[SearchEntry]:
        """Get search history for a session."""
        history = self._session_history.get(session_id, [])

        if query_type:
            history = [e for e in history if e.query_type == query_type]

        # Return most recent first
        return list(reversed(history[-limit:]))

    async def get_search_suggestions(
        self,
        session_id: str,
        prefix: Optional[str] = None,
        limit: int = 10,
    ) -> List[SearchSuggestion]:
        """
        Get search suggestions based on:
        1. User's recent searches (highest priority)
        2. Popular global searches
        """
        suggestions: List[SearchSuggestion] = []
        seen_queries: Set[str] = set()

        # First, add from user's history
        history = self._session_history.get(session_id, [])
        query_counts: Counter = Counter()
        query_times: Dict[str, datetime] = {}
        query_types: Dict[str, str] = {}

        for entry in history:
            q = entry.query.lower()
            query_counts[q] += 1
            query_times[q] = entry.timestamp
            query_types[q] = entry.query_type

        # Filter by prefix if provided
        if prefix:
            prefix_lower = prefix.lower()
            query_counts = Counter({
                q: c for q, c in query_counts.items()
                if q.startswith(prefix_lower) or prefix_lower in q
            })

        # Add user's searches
        for query, count in query_counts.most_common(limit):
            if query not in seen_queries:
                suggestions.append(SearchSuggestion(
                    query=query,
                    query_type=query_types.get(query, "text"),
                    frequency=count,
                    last_used=query_times.get(query, datetime.utcnow()),
                    relevance_score=min(1.0, count / 10 + 0.5),  # Personal history bonus
                ))
                seen_queries.add(query)

        # Add popular global searches if we need more
        if len(suggestions) < limit:
            for query, count in self._global_search_counts.most_common(50):
                if query in seen_queries:
                    continue
                if prefix and prefix.lower() not in query:
                    continue

                suggestions.append(SearchSuggestion(
                    query=query,
                    query_type="text",
                    frequency=count,
                    last_used=datetime.utcnow() - timedelta(hours=1),  # Approximate
                    relevance_score=min(0.8, count / 20),  # Lower score for global
                ))
                seen_queries.add(query)

                if len(suggestions) >= limit:
                    break

        # Sort by relevance
        suggestions.sort(key=lambda s: s.relevance_score, reverse=True)
        return suggestions[:limit]

    async def get_theme_interests(
        self,
        session_id: str,
    ) -> Dict[str, int]:
        """Get user's theme interests based on search history."""
        return dict(self._theme_interests.get(session_id, Counter()))

    async def get_personalized_recommendations(
        self,
        session_id: str,
        session: AsyncSession,
        limit: int = 10,
    ) -> List[VerseRecommendation]:
        """
        Get personalized verse recommendations based on:
        1. User's search history patterns
        2. Previously clicked verses
        3. Popular/important verses

        Note: A more sophisticated version would analyze themes and
        use semantic similarity, but this simple version uses
        popular verses as a starting point.
        """
        recommendations: List[VerseRecommendation] = []

        # Get user's theme interests and search history
        theme_interests = await self.get_theme_interests(session_id)
        history = self._session_history.get(session_id, [])

        # If no history, return popular verses
        if not history and not theme_interests:
            return await self._get_popular_verses(session, limit)

        # Get previously clicked verses to avoid recommending same ones
        clicked_refs = set()
        for entry in history:
            clicked_refs.update(entry.clicked_verses)

        # Get some popular verses, excluding clicked ones
        popular = await self._get_popular_verses(session, limit + len(clicked_refs))

        # Filter out already clicked verses
        for rec in popular:
            if rec.reference not in clicked_refs:
                recommendations.append(rec)
            if len(recommendations) >= limit:
                break

        # If user has theme interests, add context to reasons
        if theme_interests:
            top_theme = max(theme_interests.items(), key=lambda x: x[1])[0]
            for rec in recommendations[:3]:  # Update first 3 recommendations
                rec.reason = f"Popular verse - you might enjoy exploring {top_theme}"
                rec.reason_ar = f"آية مشهورة - قد تستمتع باستكشاف {top_theme}"

        return recommendations[:limit]

    async def _get_popular_verses(
        self,
        session: AsyncSession,
        limit: int = 10,
    ) -> List[VerseRecommendation]:
        """Get popular/important verses for users without history."""
        # Well-known verses that are commonly studied
        important_verses = [
            (1, 1, "Opening of Al-Fatiha", "فاتحة الكتاب"),
            (2, 255, "Ayat al-Kursi (Throne Verse)", "آية الكرسي"),
            (2, 286, "Final verse of Al-Baqara", "خاتمة البقرة"),
            (36, 1, "Opening of Ya-Sin", "فاتحة يس"),
            (112, 1, "Al-Ikhlas (Purity)", "سورة الإخلاص"),
            (113, 1, "Al-Falaq (Daybreak)", "سورة الفلق"),
            (114, 1, "An-Nas (Mankind)", "سورة الناس"),
            (55, 13, "Ar-Rahman's repeated verse", "آية الرحمن"),
            (67, 1, "Opening of Al-Mulk", "فاتحة الملك"),
            (18, 1, "Opening of Al-Kahf", "فاتحة الكهف"),
        ]

        recommendations = []
        for sura_no, aya_no, reason_en, reason_ar in important_verses[:limit]:
            query = text("""
                SELECT text_uthmani, sura_name_ar, sura_name_en
                FROM quran_verses
                WHERE sura_no = :sura_no AND aya_no = :aya_no
            """)
            result = await session.execute(query, {"sura_no": sura_no, "aya_no": aya_no})
            row = result.fetchone()

            if row:
                recommendations.append(VerseRecommendation(
                    sura_no=sura_no,
                    aya_no=aya_no,
                    reference=f"{sura_no}:{aya_no}",
                    text_uthmani=row.text_uthmani,
                    sura_name_ar=row.sura_name_ar,
                    sura_name_en=row.sura_name_en,
                    reason=reason_en,
                    reason_ar=reason_ar,
                    confidence=0.9,
                ))

        return recommendations

    # =========================================================================
    # USER FEEDBACK SYSTEM
    # =========================================================================

    async def record_similarity_feedback(
        self,
        session_id: str,
        source_reference: str,
        target_reference: str,
        is_relevant: bool,
        feedback_type: str = "thumbs_up",
        rating: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """
        Record user feedback on a similarity result.

        This feedback is used to improve search relevance over time.

        Args:
            session_id: User's session identifier
            source_reference: Source verse reference (e.g., "2:255")
            target_reference: Target/similar verse reference (e.g., "3:18")
            is_relevant: True if user marked result as relevant
            feedback_type: Type of feedback ("thumbs_up", "thumbs_down", "rating")
            rating: Optional 1-5 star rating
            notes: Optional user comment

        Returns:
            Status and updated relevance score
        """
        async with self._lock:
            feedback = SimilarityFeedback(
                source_reference=source_reference,
                target_reference=target_reference,
                is_relevant=is_relevant,
                feedback_type=feedback_type,
                rating=rating,
                timestamp=datetime.utcnow(),
                session_id=session_id,
                notes=notes,
            )

            # Store feedback by verse pair
            pair_key = (source_reference, target_reference)
            self._similarity_feedback[pair_key].append(feedback)

            # Store feedback by session
            self._session_feedback[session_id].append(feedback)

            # Update aggregated relevance scores
            current = self._relevance_scores.get(pair_key, (0, 0))
            positive_count = current[0] + (1 if is_relevant else 0)
            total_count = current[1] + 1
            self._relevance_scores[pair_key] = (positive_count, total_count)

            # Calculate new relevance score
            relevance_score = positive_count / total_count if total_count > 0 else 0.5

            return {
                "status": "recorded",
                "pair": f"{source_reference} -> {target_reference}",
                "relevance_score": round(relevance_score, 3),
                "total_feedback_count": total_count,
            }

    async def get_relevance_score(
        self,
        source_reference: str,
        target_reference: str,
    ) -> Optional[float]:
        """
        Get the community relevance score for a verse pair.

        Returns:
            Float between 0-1 indicating how relevant users found this pair,
            or None if no feedback exists.
        """
        pair_key = (source_reference, target_reference)
        scores = self._relevance_scores.get(pair_key)

        if not scores or scores[1] == 0:
            return None

        return scores[0] / scores[1]

    async def get_pair_feedback(
        self,
        source_reference: str,
        target_reference: str,
        limit: int = 50,
    ) -> List[SimilarityFeedback]:
        """Get all feedback for a specific verse pair."""
        pair_key = (source_reference, target_reference)
        feedback_list = self._similarity_feedback.get(pair_key, [])
        return feedback_list[-limit:]

    async def get_session_feedback(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[SimilarityFeedback]:
        """Get all feedback from a specific session."""
        return self._session_feedback.get(session_id, [])[-limit:]

    async def get_feedback_stats(self) -> Dict:
        """Get aggregated feedback statistics."""
        total_feedback = sum(
            len(fb_list) for fb_list in self._similarity_feedback.values()
        )
        positive_feedback = sum(
            sum(1 for fb in fb_list if fb.is_relevant)
            for fb_list in self._similarity_feedback.values()
        )

        # Find most and least relevant pairs
        sorted_pairs = sorted(
            self._relevance_scores.items(),
            key=lambda x: x[1][0] / x[1][1] if x[1][1] > 0 else 0,
            reverse=True,
        )

        most_relevant = [
            {
                "pair": f"{pair[0]} -> {pair[1]}",
                "score": round(scores[0] / scores[1], 3) if scores[1] > 0 else 0,
                "count": scores[1],
            }
            for pair, scores in sorted_pairs[:10]
            if scores[1] >= 2  # At least 2 votes
        ]

        least_relevant = [
            {
                "pair": f"{pair[0]} -> {pair[1]}",
                "score": round(scores[0] / scores[1], 3) if scores[1] > 0 else 0,
                "count": scores[1],
            }
            for pair, scores in reversed(sorted_pairs[-10:])
            if scores[1] >= 2
        ]

        return {
            "total_feedback_entries": total_feedback,
            "positive_feedback": positive_feedback,
            "negative_feedback": total_feedback - positive_feedback,
            "unique_pairs_rated": len(self._relevance_scores),
            "sessions_with_feedback": len(self._session_feedback),
            "most_relevant_pairs": most_relevant[:5],
            "least_relevant_pairs": least_relevant[:5],
            "average_relevance": (
                positive_feedback / total_feedback if total_feedback > 0 else 0.5
            ),
        }

    async def apply_feedback_boost(
        self,
        source_reference: str,
        results: List[Dict],
        boost_weight: float = 0.1,
    ) -> List[Dict]:
        """
        Apply feedback-based score boosting to similarity results.

        Verses with positive feedback get a score boost,
        verses with negative feedback get a score reduction.

        Args:
            source_reference: The source verse being searched
            results: List of similarity match dictionaries with 'reference' and 'scores'
            boost_weight: How much to weight feedback (0-1)

        Returns:
            Results with adjusted scores based on community feedback
        """
        for result in results:
            target_ref = result.get("reference", "")
            relevance = await self.get_relevance_score(source_reference, target_ref)

            if relevance is not None:
                # Apply feedback boost/penalty
                # relevance > 0.5 = boost, < 0.5 = penalty
                adjustment = (relevance - 0.5) * 2 * boost_weight

                # Update combined score if present
                if "scores" in result and hasattr(result["scores"], "combined"):
                    original = result["scores"].combined
                    result["scores"].combined = min(1.0, max(0.0, original + adjustment))
                elif "combined_score" in result:
                    original = result["combined_score"]
                    result["combined_score"] = min(1.0, max(0.0, original + adjustment))

                # Add feedback info
                result["user_relevance_score"] = round(relevance, 3)
                result["feedback_applied"] = True

        return results

    async def clear_session_history(self, session_id: str) -> None:
        """Clear history for a session."""
        async with self._lock:
            if session_id in self._session_history:
                del self._session_history[session_id]
            if session_id in self._theme_interests:
                del self._theme_interests[session_id]

    def get_stats(self) -> Dict:
        """Get service statistics."""
        return {
            "active_sessions": len(self._session_history),
            "total_searches": sum(self._global_search_counts.values()),
            "unique_queries": len(self._global_search_counts),
            "total_verse_clicks": sum(self._verse_clicks.values()),
            "top_searches": self._global_search_counts.most_common(10),
            "top_clicked_verses": self._verse_clicks.most_common(10),
        }

    # =========================================================================
    # AI-BASED FEEDBACK LEARNING
    # =========================================================================

    async def learn_from_feedback(self) -> Dict[str, Any]:
        """
        Analyze feedback patterns to learn feature importance.

        This method examines which types of verse connections receive
        positive vs negative feedback and adjusts feature weights accordingly.

        Returns:
            Learning insights and suggested weight adjustments
        """
        if not self._similarity_feedback:
            return {"status": "insufficient_data", "message": "Need more feedback"}

        # Analyze feedback patterns
        positive_patterns = Counter()
        negative_patterns = Counter()

        for (source_ref, target_ref), feedbacks in self._similarity_feedback.items():
            for fb in feedbacks:
                if fb.is_relevant:
                    positive_patterns[f"{source_ref[:3]}"] += 1
                else:
                    negative_patterns[f"{source_ref[:3]}"] += 1

        # Calculate feature importance adjustments
        total_positive = sum(positive_patterns.values())
        total_negative = sum(negative_patterns.values())
        total = total_positive + total_negative

        if total < 10:
            return {"status": "insufficient_data", "total_feedback": total}

        # Calculate relevance rate and confidence
        relevance_rate = total_positive / total if total > 0 else 0.5
        confidence = min(1.0, total / 100)  # More data = higher confidence

        return {
            "status": "analyzed",
            "total_feedback": total,
            "positive_count": total_positive,
            "negative_count": total_negative,
            "relevance_rate": round(relevance_rate, 3),
            "confidence": round(confidence, 3),
            "top_positive_suras": positive_patterns.most_common(5),
            "top_negative_suras": negative_patterns.most_common(5),
            "recommendation": (
                "increase_contextual_weight" if relevance_rate > 0.7
                else "review_results" if relevance_rate < 0.3
                else "maintain_current"
            ),
        }

    async def get_personalized_weight_adjustments(
        self,
        session_id: str,
    ) -> Dict[str, float]:
        """
        Get personalized weight adjustments based on user's feedback history.

        Users who consistently prefer certain types of connections
        get adjusted weights for their searches.
        """
        session_feedback = self._session_feedback.get(session_id, [])

        if len(session_feedback) < 5:
            return {}  # Not enough data for personalization

        # Analyze this user's preferences
        positive_count = sum(1 for fb in session_feedback if fb.is_relevant)
        total = len(session_feedback)
        user_relevance_rate = positive_count / total

        # If user has high relevance rate, boost their preferences
        adjustments = {}

        if user_relevance_rate > 0.7:
            # User finds results relevant - maintain current approach
            adjustments["contextual_boost"] = 0.05
        elif user_relevance_rate < 0.3:
            # User finds results irrelevant - try different approach
            adjustments["contextual_boost"] = -0.05
            adjustments["semantic_boost"] = 0.1

        return adjustments

    # =========================================================================
    # BOOKMARK SYSTEM
    # =========================================================================

    _bookmarks: Dict[str, List[Dict]] = {}  # session_id -> list of bookmarks
    _bookmark_collections: Dict[str, Dict[str, List[str]]] = {}  # session_id -> collection_name -> verse_refs

    async def add_bookmark(
        self,
        session_id: str,
        sura_no: int,
        aya_no: int,
        note: Optional[str] = None,
        collection: str = "default",
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """
        Add a verse bookmark for the user.

        Args:
            session_id: User session
            sura_no: Surah number
            aya_no: Ayah number
            note: Optional personal note
            collection: Collection name (default, memorization, study, etc.)
            tags: Optional tags for organization
        """
        async with self._lock:
            if session_id not in self._bookmarks:
                self._bookmarks[session_id] = []
                self._bookmark_collections[session_id] = {"default": []}

            verse_ref = f"{sura_no}:{aya_no}"
            bookmark = {
                "reference": verse_ref,
                "sura_no": sura_no,
                "aya_no": aya_no,
                "note": note,
                "collection": collection,
                "tags": tags or [],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Check if already bookmarked
            existing = [b for b in self._bookmarks[session_id] if b["reference"] == verse_ref]
            if existing:
                # Update existing bookmark
                for b in self._bookmarks[session_id]:
                    if b["reference"] == verse_ref:
                        b.update(bookmark)
                        break
            else:
                self._bookmarks[session_id].append(bookmark)

            # Add to collection
            if collection not in self._bookmark_collections[session_id]:
                self._bookmark_collections[session_id][collection] = []
            if verse_ref not in self._bookmark_collections[session_id][collection]:
                self._bookmark_collections[session_id][collection].append(verse_ref)

            return {"status": "added", "bookmark": bookmark}

    async def remove_bookmark(
        self,
        session_id: str,
        sura_no: int,
        aya_no: int,
    ) -> Dict:
        """Remove a bookmark."""
        async with self._lock:
            verse_ref = f"{sura_no}:{aya_no}"
            if session_id in self._bookmarks:
                self._bookmarks[session_id] = [
                    b for b in self._bookmarks[session_id]
                    if b["reference"] != verse_ref
                ]
                # Remove from collections
                for collection in self._bookmark_collections.get(session_id, {}).values():
                    if verse_ref in collection:
                        collection.remove(verse_ref)

            return {"status": "removed", "reference": verse_ref}

    async def get_bookmarks(
        self,
        session_id: str,
        collection: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Get user's bookmarks, optionally filtered."""
        bookmarks = self._bookmarks.get(session_id, [])

        if collection:
            bookmarks = [b for b in bookmarks if b.get("collection") == collection]

        if tags:
            bookmarks = [
                b for b in bookmarks
                if any(tag in b.get("tags", []) for tag in tags)
            ]

        return sorted(bookmarks, key=lambda x: x.get("timestamp", ""), reverse=True)

    async def get_bookmark_collections(self, session_id: str) -> Dict[str, int]:
        """Get user's bookmark collections with counts."""
        collections = self._bookmark_collections.get(session_id, {})
        return {name: len(refs) for name, refs in collections.items()}

    # =========================================================================
    # STUDY GOALS & PERSONALIZATION
    # =========================================================================

    _study_goals: Dict[str, Dict] = {}  # session_id -> study goal config

    async def set_study_goal(
        self,
        session_id: str,
        goal_type: str,  # "memorization", "comprehension", "research", "reflection"
        themes: Optional[List[str]] = None,
        prophets: Optional[List[str]] = None,
        suras: Optional[List[int]] = None,
    ) -> Dict:
        """
        Set user's current study goal for personalized results.

        Args:
            goal_type: Type of study (memorization, comprehension, research, reflection)
            themes: Themes user is interested in
            prophets: Prophets user wants to study
            suras: Specific suras to focus on
        """
        self._study_goals[session_id] = {
            "goal_type": goal_type,
            "themes": themes or [],
            "prophets": prophets or [],
            "suras": suras or [],
            "created_at": datetime.utcnow().isoformat(),
        }

        return {"status": "set", "goal": self._study_goals[session_id]}

    async def get_study_goal(self, session_id: str) -> Optional[Dict]:
        """Get user's current study goal."""
        return self._study_goals.get(session_id)

    async def get_personalized_filters(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Get personalized search filters based on user's history and goals.

        Returns filter suggestions and weight adjustments.
        """
        filters = {
            "suggested_themes": [],
            "suggested_prophets": [],
            "weight_adjustments": {},
            "recommended_connection_types": [],
        }

        # Get theme interests from search history
        theme_interests = await self.get_theme_interests(session_id)
        if theme_interests:
            top_themes = sorted(
                theme_interests.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            filters["suggested_themes"] = [t[0] for t in top_themes]

        # Get study goal preferences
        goal = self._study_goals.get(session_id)
        if goal:
            if goal["themes"]:
                filters["suggested_themes"].extend(goal["themes"])
            if goal["prophets"]:
                filters["suggested_prophets"] = goal["prophets"]

            # Adjust weights based on goal type
            if goal["goal_type"] == "memorization":
                filters["weight_adjustments"]["lexical_boost"] = 0.1
                filters["recommended_connection_types"] = ["lexical", "root_based"]
            elif goal["goal_type"] == "comprehension":
                filters["weight_adjustments"]["semantic_boost"] = 0.15
                filters["recommended_connection_types"] = ["thematic", "conceptual"]
            elif goal["goal_type"] == "research":
                filters["weight_adjustments"]["contextual_boost"] = 0.1
                filters["recommended_connection_types"] = ["prophetic", "narrative"]
            elif goal["goal_type"] == "reflection":
                filters["weight_adjustments"]["thematic_boost"] = 0.15
                filters["recommended_connection_types"] = ["thematic", "semantic"]

        # Apply feedback-based personalization
        feedback_adjustments = await self.get_personalized_weight_adjustments(session_id)
        filters["weight_adjustments"].update(feedback_adjustments)

        return filters

    # =========================================================================
    # TOPIC CLUSTERING
    # =========================================================================

    async def cluster_search_results(
        self,
        results: List[Dict],
        cluster_by: str = "theme",  # "theme", "sura", "prophet", "connection_type"
    ) -> Dict[str, List[Dict]]:
        """
        Cluster search results by specified criteria.

        Args:
            results: List of search result dictionaries
            cluster_by: Clustering criterion

        Returns:
            Dictionary of cluster_name -> list of results
        """
        clusters = defaultdict(list)

        for result in results:
            if cluster_by == "theme":
                themes = result.get("shared_themes", [])
                if themes:
                    for theme in themes:
                        clusters[theme].append(result)
                else:
                    clusters["other"].append(result)

            elif cluster_by == "sura":
                sura = result.get("sura_name_ar", "other")
                clusters[sura].append(result)

            elif cluster_by == "prophet":
                prophets = result.get("shared_prophets", [])
                if prophets:
                    for prophet in prophets:
                        clusters[prophet].append(result)
                else:
                    clusters["general"].append(result)

            elif cluster_by == "connection_type":
                conn_type = result.get("connection_type", "other")
                clusters[conn_type].append(result)

        # Sort clusters by size
        return dict(sorted(
            clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ))

    async def get_topic_clusters_summary(
        self,
        session_id: str,
    ) -> List[Dict]:
        """
        Get topic clusters based on user's search history.

        Returns clusters user has explored and suggestions.
        """
        history = self._session_history.get(session_id, [])
        theme_counts = Counter()

        for entry in history:
            # Count queries by inferred themes
            query_lower = entry.query.lower()
            for theme in EXTENDED_THEME_KEYWORDS if 'EXTENDED_THEME_KEYWORDS' in dir() else {}:
                if theme in query_lower:
                    theme_counts[theme] += 1

        clusters = []
        for theme, count in theme_counts.most_common(10):
            clusters.append({
                "theme": theme,
                "search_count": count,
                "label_ar": THEME_LABELS_AR.get(theme, theme),
                "color": THEME_COLORS.get(theme, "#6B7280"),
            })

        return clusters


# Import theme constants for clustering (avoid circular import)
try:
    from app.services.advanced_similarity import (
        THEME_LABELS_AR,
        THEME_COLORS,
        EXTENDED_THEME_KEYWORDS,
    )
except ImportError:
    THEME_LABELS_AR = {}
    THEME_COLORS = {}
    EXTENDED_THEME_KEYWORDS = {}


# Global instance
search_history_service = SearchHistoryService()
