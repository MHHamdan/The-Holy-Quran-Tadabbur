"""
Crowdsourced Annotation System with NLP Feedback Analysis.

Features:
1. User-contributed annotations for verses
2. Community voting and moderation
3. NLP-based quality scoring
4. Sentiment analysis of annotations
5. Theme extraction from user insights
6. Expert review workflow

Arabic: نظام التعليقات التوضيحية الجماعية مع تحليل الملاحظات باستخدام NLP
"""

import logging
import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import math

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class AnnotationType(str, Enum):
    """Types of annotations."""
    REFLECTION = "reflection"           # Personal reflection
    EXPLANATION = "explanation"         # Explanation/tafsir
    LINGUISTIC = "linguistic"           # Language analysis
    THEMATIC = "thematic"              # Theme identification
    LIFE_LESSON = "life_lesson"        # Practical application
    HISTORICAL = "historical"          # Historical context
    CONNECTION = "connection"          # Cross-reference
    QUESTION = "question"              # Question about verse


class AnnotationStatus(str, Enum):
    """Status of an annotation."""
    PENDING = "pending"                # Awaiting review
    APPROVED = "approved"              # Approved for display
    FEATURED = "featured"              # Featured annotation
    UNDER_REVIEW = "under_review"      # Being reviewed
    REJECTED = "rejected"              # Rejected


class VoteType(str, Enum):
    """Types of votes."""
    HELPFUL = "helpful"
    INSIGHTFUL = "insightful"
    ACCURATE = "accurate"
    WELL_WRITTEN = "well_written"


class SentimentCategory(str, Enum):
    """Sentiment categories."""
    HOPEFUL = "hopeful"
    GRATEFUL = "grateful"
    REFLECTIVE = "reflective"
    CONCERNED = "concerned"
    QUESTIONING = "questioning"
    INSPIRATIONAL = "inspirational"


@dataclass
class Annotation:
    """A user-contributed annotation."""
    annotation_id: str
    verse_reference: str
    user_id: str
    annotation_type: AnnotationType
    content_ar: str
    content_en: str
    status: AnnotationStatus
    created_at: datetime
    updated_at: datetime
    votes: Dict[str, int]
    tags: List[str]
    nlp_analysis: Dict[str, Any]
    expert_review: Optional[Dict[str, Any]] = None


@dataclass
class NLPAnalysis:
    """NLP analysis results for an annotation."""
    quality_score: float
    sentiment: SentimentCategory
    themes_detected: List[str]
    key_terms: List[str]
    readability_score: float
    relevance_score: float
    language: str
    word_count: int


@dataclass
class UserContributorProfile:
    """Profile for a contributor."""
    user_id: str
    annotations_count: int
    approved_count: int
    featured_count: int
    total_votes_received: int
    expertise_areas: List[str]
    reputation_score: float
    joined_date: datetime


# =============================================================================
# NLP ANALYSIS UTILITIES
# =============================================================================

# Islamic theme keywords for detection
THEME_KEYWORDS = {
    "patience": ["صبر", "patience", "sabr", "perseverance", "endurance"],
    "gratitude": ["شكر", "gratitude", "shukr", "thankful", "grateful"],
    "trust": ["توكل", "trust", "tawakkul", "reliance", "faith"],
    "mercy": ["رحمة", "mercy", "rahma", "compassion", "kindness"],
    "forgiveness": ["مغفرة", "forgiveness", "ghufran", "pardon", "repentance"],
    "justice": ["عدل", "justice", "adl", "fairness", "equity"],
    "love": ["محبة", "حب", "love", "hubb", "affection"],
    "fear_of_allah": ["تقوى", "خوف", "taqwa", "fear", "consciousness"],
    "hope": ["رجاء", "أمل", "hope", "raja", "optimism"],
    "knowledge": ["علم", "knowledge", "ilm", "learning", "understanding"],
    "worship": ["عبادة", "worship", "ibadah", "prayer", "devotion"],
    "family": ["أسرة", "family", "usra", "parents", "children"],
}

# Positive sentiment indicators
POSITIVE_INDICATORS = [
    "beautiful", "profound", "inspiring", "meaningful", "powerful",
    "جميل", "عميق", "ملهم", "مؤثر", "قوي", "رائع",
    "blessing", "grateful", "thankful", "hopeful", "uplifting",
]

# Reflective sentiment indicators
REFLECTIVE_INDICATORS = [
    "reflect", "contemplate", "ponder", "consider", "think",
    "تأمل", "تفكر", "تدبر", "نظر", "اعتبار",
    "reminds", "teaches", "shows", "demonstrates",
]

# Quality indicators
QUALITY_INDICATORS = {
    "evidence": ["verse", "ayah", "hadith", "scholar", "reference"],
    "structure": ["first", "second", "therefore", "because", "thus"],
    "depth": ["means", "signifies", "represents", "symbolizes", "indicates"],
}


class NLPAnalyzer:
    """NLP analysis for annotations."""

    def __init__(self):
        self._theme_keywords = THEME_KEYWORDS
        self._positive_indicators = POSITIVE_INDICATORS
        self._reflective_indicators = REFLECTIVE_INDICATORS
        self._quality_indicators = QUALITY_INDICATORS

    def analyze(self, text: str, language: str = "auto") -> NLPAnalysis:
        """Perform NLP analysis on annotation text."""
        # Detect language
        if language == "auto":
            language = self._detect_language(text)

        # Word count
        word_count = len(text.split())

        # Detect themes
        themes = self._detect_themes(text)

        # Extract key terms
        key_terms = self._extract_key_terms(text)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)

        # Calculate quality score
        quality = self._calculate_quality_score(text, themes, key_terms)

        # Calculate readability
        readability = self._calculate_readability(text)

        # Calculate relevance (how related to Quranic content)
        relevance = self._calculate_relevance(text, themes)

        return NLPAnalysis(
            quality_score=quality,
            sentiment=sentiment,
            themes_detected=themes,
            key_terms=key_terms,
            readability_score=readability,
            relevance_score=relevance,
            language=language,
            word_count=word_count,
        )

    def _detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return "en"
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.5 else "en"

    def _detect_themes(self, text: str) -> List[str]:
        """Detect Islamic themes in text."""
        text_lower = text.lower()
        detected = []

        for theme, keywords in self._theme_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if theme not in detected:
                        detected.append(theme)
                    break

        return detected[:5]  # Top 5 themes

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Simple word frequency approach
        words = re.findall(r'\b\w{4,}\b', text.lower())

        # Remove common stopwords
        stopwords = {
            "this", "that", "with", "from", "have", "been", "were",
            "which", "their", "about", "there", "when", "what",
            "هذا", "هذه", "الذي", "التي", "من", "إلى", "على",
        }
        words = [w for w in words if w not in stopwords]

        # Count frequencies
        freq = defaultdict(int)
        for word in words:
            freq[word] += 1

        # Get top terms
        sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:10]]

    def _analyze_sentiment(self, text: str) -> SentimentCategory:
        """Analyze sentiment of the text."""
        text_lower = text.lower()

        # Count indicators
        positive_count = sum(1 for ind in self._positive_indicators if ind in text_lower)
        reflective_count = sum(1 for ind in self._reflective_indicators if ind in text_lower)

        # Determine sentiment
        if "?" in text:
            return SentimentCategory.QUESTIONING
        elif positive_count >= 2:
            if "grateful" in text_lower or "شكر" in text or "thankful" in text_lower:
                return SentimentCategory.GRATEFUL
            elif "hope" in text_lower or "رجاء" in text or "أمل" in text:
                return SentimentCategory.HOPEFUL
            else:
                return SentimentCategory.INSPIRATIONAL
        elif reflective_count >= 1:
            return SentimentCategory.REFLECTIVE
        else:
            return SentimentCategory.REFLECTIVE  # Default

    def _calculate_quality_score(
        self,
        text: str,
        themes: List[str],
        key_terms: List[str],
    ) -> float:
        """Calculate quality score (0-1)."""
        score = 0.5  # Base score

        text_lower = text.lower()

        # Evidence (+0.15)
        evidence_count = sum(
            1 for kw in self._quality_indicators["evidence"]
            if kw in text_lower
        )
        score += min(0.15, evidence_count * 0.05)

        # Structure (+0.15)
        structure_count = sum(
            1 for kw in self._quality_indicators["structure"]
            if kw in text_lower
        )
        score += min(0.15, structure_count * 0.05)

        # Depth (+0.1)
        depth_count = sum(
            1 for kw in self._quality_indicators["depth"]
            if kw in text_lower
        )
        score += min(0.1, depth_count * 0.05)

        # Theme detection (+0.1)
        score += min(0.1, len(themes) * 0.02)

        # Length bonus (50-500 words optimal)
        word_count = len(text.split())
        if 50 <= word_count <= 500:
            score += 0.1
        elif 30 <= word_count < 50 or 500 < word_count <= 800:
            score += 0.05

        return min(1.0, max(0.0, score))

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (0-1)."""
        words = text.split()
        if not words:
            return 0.5

        # Average word length (optimal: 4-6 chars)
        avg_word_len = sum(len(w) for w in words) / len(words)
        word_len_score = 1.0 if 4 <= avg_word_len <= 6 else max(0.5, 1 - abs(avg_word_len - 5) / 10)

        # Sentence length (optimal: 15-25 words)
        sentences = re.split(r'[.!?؟]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
            sentence_score = 1.0 if 15 <= avg_sentence_len <= 25 else max(0.5, 1 - abs(avg_sentence_len - 20) / 30)
        else:
            sentence_score = 0.6

        return (word_len_score + sentence_score) / 2

    def _calculate_relevance(self, text: str, themes: List[str]) -> float:
        """Calculate relevance to Quranic content."""
        score = 0.4  # Base score

        # Theme detection boost
        score += min(0.3, len(themes) * 0.06)

        # Quranic reference keywords
        quran_keywords = [
            "quran", "verse", "ayah", "sura", "allah", "prophet",
            "قرآن", "آية", "سورة", "الله", "نبي", "رسول",
        ]
        text_lower = text.lower()
        quran_count = sum(1 for kw in quran_keywords if kw in text_lower)
        score += min(0.2, quran_count * 0.05)

        # Islamic terminology
        islamic_terms = [
            "iman", "islam", "ihsan", "tawbah", "dua", "salah",
            "إيمان", "إسلام", "إحسان", "توبة", "دعاء", "صلاة",
        ]
        islamic_count = sum(1 for term in islamic_terms if term in text_lower)
        score += min(0.1, islamic_count * 0.05)

        return min(1.0, max(0.0, score))


# =============================================================================
# ANNOTATION SERVICE
# =============================================================================

class AnnotationService:
    """
    Crowdsourced annotation service with NLP analysis.

    Features:
    - User-contributed annotations
    - Community voting
    - NLP quality analysis
    - Expert review workflow
    - Contributor reputation system
    """

    def __init__(self):
        self._annotations: Dict[str, Annotation] = {}
        self._verse_annotations: Dict[str, List[str]] = defaultdict(list)
        self._user_annotations: Dict[str, List[str]] = defaultdict(list)
        self._user_profiles: Dict[str, UserContributorProfile] = {}
        self._nlp_analyzer = NLPAnalyzer()
        self._pending_reviews: List[str] = []

    def submit_annotation(
        self,
        user_id: str,
        verse_reference: str,
        annotation_type: str,
        content_ar: str,
        content_en: str,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Submit a new annotation."""
        # Generate ID
        annotation_id = self._generate_id(user_id, verse_reference, content_en)

        # Analyze with NLP
        text_to_analyze = content_en if content_en else content_ar
        nlp_result = self._nlp_analyzer.analyze(text_to_analyze)

        # Determine initial status based on quality
        initial_status = AnnotationStatus.PENDING
        if nlp_result.quality_score >= 0.7 and nlp_result.relevance_score >= 0.6:
            initial_status = AnnotationStatus.APPROVED  # Auto-approve high quality

        # Create annotation
        annotation = Annotation(
            annotation_id=annotation_id,
            verse_reference=verse_reference,
            user_id=user_id,
            annotation_type=AnnotationType(annotation_type),
            content_ar=content_ar,
            content_en=content_en,
            status=initial_status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            votes={v.value: 0 for v in VoteType},
            tags=tags or [],
            nlp_analysis={
                "quality_score": nlp_result.quality_score,
                "sentiment": nlp_result.sentiment.value,
                "themes_detected": nlp_result.themes_detected,
                "key_terms": nlp_result.key_terms,
                "readability_score": nlp_result.readability_score,
                "relevance_score": nlp_result.relevance_score,
                "word_count": nlp_result.word_count,
            },
        )

        # Store
        self._annotations[annotation_id] = annotation
        self._verse_annotations[verse_reference].append(annotation_id)
        self._user_annotations[user_id].append(annotation_id)

        if initial_status == AnnotationStatus.PENDING:
            self._pending_reviews.append(annotation_id)

        # Update user profile
        self._update_user_profile(user_id, annotation)

        return {
            "annotation_id": annotation_id,
            "status": initial_status.value,
            "nlp_analysis": annotation.nlp_analysis,
            "message_ar": "تم تقديم التعليق بنجاح",
            "message_en": "Annotation submitted successfully",
            "auto_approved": initial_status == AnnotationStatus.APPROVED,
        }

    def get_verse_annotations(
        self,
        verse_reference: str,
        annotation_type: Optional[str] = None,
        status: str = "approved",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get annotations for a verse."""
        annotation_ids = self._verse_annotations.get(verse_reference, [])

        results = []
        for aid in annotation_ids:
            ann = self._annotations.get(aid)
            if not ann:
                continue

            # Filter by status
            if status and ann.status.value != status:
                continue

            # Filter by type
            if annotation_type and ann.annotation_type.value != annotation_type:
                continue

            results.append(self._annotation_to_dict(ann))

        # Sort by votes
        results.sort(key=lambda x: sum(x["votes"].values()), reverse=True)
        return results[:limit]

    def vote_on_annotation(
        self,
        annotation_id: str,
        user_id: str,
        vote_type: str,
    ) -> Dict[str, Any]:
        """Vote on an annotation."""
        if annotation_id not in self._annotations:
            return {"error": "Annotation not found"}

        annotation = self._annotations[annotation_id]

        # Can't vote on own annotation
        if annotation.user_id == user_id:
            return {"error": "Cannot vote on your own annotation"}

        # Add vote
        if vote_type in annotation.votes:
            annotation.votes[vote_type] += 1

        # Check for featured status
        total_votes = sum(annotation.votes.values())
        if total_votes >= 10 and annotation.status == AnnotationStatus.APPROVED:
            annotation.status = AnnotationStatus.FEATURED
            self._update_contributor_featured(annotation.user_id)

        return {
            "annotation_id": annotation_id,
            "vote_type": vote_type,
            "new_total": annotation.votes[vote_type],
            "all_votes": annotation.votes,
        }

    def get_user_annotations(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get annotations by a user."""
        annotation_ids = self._user_annotations.get(user_id, [])

        results = []
        for aid in annotation_ids[-limit:]:
            ann = self._annotations.get(aid)
            if ann:
                results.append(self._annotation_to_dict(ann))

        return results

    def get_user_contributor_profile(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get contributor profile."""
        if user_id not in self._user_profiles:
            # Create new profile
            self._user_profiles[user_id] = UserContributorProfile(
                user_id=user_id,
                annotations_count=0,
                approved_count=0,
                featured_count=0,
                total_votes_received=0,
                expertise_areas=[],
                reputation_score=0.0,
                joined_date=datetime.now(),
            )

        profile = self._user_profiles[user_id]
        return {
            "user_id": profile.user_id,
            "annotations_count": profile.annotations_count,
            "approved_count": profile.approved_count,
            "featured_count": profile.featured_count,
            "total_votes_received": profile.total_votes_received,
            "expertise_areas": profile.expertise_areas,
            "reputation_score": round(profile.reputation_score, 2),
            "contributor_level": self._get_contributor_level(profile.reputation_score),
            "joined_date": profile.joined_date.isoformat(),
        }

    def get_pending_reviews(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get annotations pending review (for moderators)."""
        results = []
        for aid in self._pending_reviews[:limit]:
            ann = self._annotations.get(aid)
            if ann and ann.status == AnnotationStatus.PENDING:
                results.append(self._annotation_to_dict(ann))
        return results

    def review_annotation(
        self,
        annotation_id: str,
        reviewer_id: str,
        decision: str,  # approve, reject, feature
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Review an annotation (moderator action)."""
        if annotation_id not in self._annotations:
            return {"error": "Annotation not found"}

        annotation = self._annotations[annotation_id]

        # Update status
        if decision == "approve":
            annotation.status = AnnotationStatus.APPROVED
            self._update_contributor_approved(annotation.user_id)
        elif decision == "reject":
            annotation.status = AnnotationStatus.REJECTED
        elif decision == "feature":
            annotation.status = AnnotationStatus.FEATURED
            self._update_contributor_featured(annotation.user_id)

        # Add expert review
        annotation.expert_review = {
            "reviewer_id": reviewer_id,
            "decision": decision,
            "feedback": feedback,
            "reviewed_at": datetime.now().isoformat(),
        }

        annotation.updated_at = datetime.now()

        # Remove from pending
        if annotation_id in self._pending_reviews:
            self._pending_reviews.remove(annotation_id)

        return {
            "annotation_id": annotation_id,
            "new_status": annotation.status.value,
            "reviewed": True,
        }

    def get_featured_annotations(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get featured annotations."""
        results = []
        for ann in self._annotations.values():
            if ann.status == AnnotationStatus.FEATURED:
                results.append(self._annotation_to_dict(ann))

        # Sort by total votes
        results.sort(key=lambda x: sum(x["votes"].values()), reverse=True)
        return results[:limit]

    def get_annotations_by_theme(
        self,
        theme: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get annotations that contain a specific theme."""
        results = []
        theme_lower = theme.lower()

        for ann in self._annotations.values():
            if ann.status not in [AnnotationStatus.APPROVED, AnnotationStatus.FEATURED]:
                continue

            themes_detected = ann.nlp_analysis.get("themes_detected", [])
            if any(theme_lower in t.lower() for t in themes_detected):
                results.append(self._annotation_to_dict(ann))

        # Sort by quality score
        results.sort(
            key=lambda x: x.get("nlp_analysis", {}).get("quality_score", 0),
            reverse=True,
        )
        return results[:limit]

    def get_annotation_statistics(self) -> Dict[str, Any]:
        """Get statistics about annotations."""
        total = len(self._annotations)
        approved = sum(1 for a in self._annotations.values() if a.status == AnnotationStatus.APPROVED)
        featured = sum(1 for a in self._annotations.values() if a.status == AnnotationStatus.FEATURED)
        pending = sum(1 for a in self._annotations.values() if a.status == AnnotationStatus.PENDING)

        # Type distribution
        type_dist = defaultdict(int)
        for ann in self._annotations.values():
            type_dist[ann.annotation_type.value] += 1

        # Theme distribution
        theme_dist = defaultdict(int)
        for ann in self._annotations.values():
            for theme in ann.nlp_analysis.get("themes_detected", []):
                theme_dist[theme] += 1

        # Average quality score
        quality_scores = [
            a.nlp_analysis.get("quality_score", 0)
            for a in self._annotations.values()
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_annotations": total,
            "approved": approved,
            "featured": featured,
            "pending": pending,
            "rejected": total - approved - featured - pending,
            "unique_contributors": len(self._user_profiles),
            "type_distribution": dict(type_dist),
            "theme_distribution": dict(sorted(theme_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
            "average_quality_score": round(avg_quality, 3),
            "verses_with_annotations": len(self._verse_annotations),
        }

    def get_annotation_types(self) -> List[Dict[str, str]]:
        """Get all annotation types with descriptions."""
        return [
            {
                "id": t.value,
                "name_ar": self._get_type_name_ar(t),
                "name_en": self._get_type_name_en(t),
            }
            for t in AnnotationType
        ]

    def get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top contributors by reputation."""
        sorted_profiles = sorted(
            self._user_profiles.values(),
            key=lambda p: p.reputation_score,
            reverse=True,
        )

        return [
            {
                "user_id": p.user_id,
                "annotations_count": p.annotations_count,
                "reputation_score": round(p.reputation_score, 2),
                "contributor_level": self._get_contributor_level(p.reputation_score),
                "expertise_areas": p.expertise_areas[:3],
            }
            for p in sorted_profiles[:limit]
        ]

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _generate_id(self, user_id: str, verse_ref: str, content: str) -> str:
        """Generate unique annotation ID."""
        data = f"{user_id}:{verse_ref}:{content[:50]}:{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _annotation_to_dict(self, ann: Annotation) -> Dict[str, Any]:
        """Convert annotation to dictionary."""
        return {
            "annotation_id": ann.annotation_id,
            "verse_reference": ann.verse_reference,
            "user_id": ann.user_id,
            "annotation_type": ann.annotation_type.value,
            "content_ar": ann.content_ar,
            "content_en": ann.content_en,
            "status": ann.status.value,
            "created_at": ann.created_at.isoformat(),
            "votes": ann.votes,
            "total_votes": sum(ann.votes.values()),
            "tags": ann.tags,
            "nlp_analysis": ann.nlp_analysis,
            "expert_review": ann.expert_review,
        }

    def _update_user_profile(self, user_id: str, annotation: Annotation) -> None:
        """Update user contributor profile."""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserContributorProfile(
                user_id=user_id,
                annotations_count=0,
                approved_count=0,
                featured_count=0,
                total_votes_received=0,
                expertise_areas=[],
                reputation_score=0.0,
                joined_date=datetime.now(),
            )

        profile = self._user_profiles[user_id]
        profile.annotations_count += 1

        # Add detected themes to expertise
        themes = annotation.nlp_analysis.get("themes_detected", [])
        for theme in themes:
            if theme not in profile.expertise_areas:
                profile.expertise_areas.append(theme)

        # Limit expertise areas
        profile.expertise_areas = profile.expertise_areas[:10]

        # Update reputation
        quality = annotation.nlp_analysis.get("quality_score", 0.5)
        profile.reputation_score += quality * 10

    def _update_contributor_approved(self, user_id: str) -> None:
        """Update contributor when annotation is approved."""
        if user_id in self._user_profiles:
            self._user_profiles[user_id].approved_count += 1
            self._user_profiles[user_id].reputation_score += 5

    def _update_contributor_featured(self, user_id: str) -> None:
        """Update contributor when annotation is featured."""
        if user_id in self._user_profiles:
            self._user_profiles[user_id].featured_count += 1
            self._user_profiles[user_id].reputation_score += 20

    def _get_contributor_level(self, reputation: float) -> str:
        """Get contributor level based on reputation."""
        if reputation >= 500:
            return "expert"
        elif reputation >= 200:
            return "advanced"
        elif reputation >= 50:
            return "intermediate"
        else:
            return "beginner"

    def _get_type_name_ar(self, t: AnnotationType) -> str:
        """Get Arabic name for annotation type."""
        names = {
            AnnotationType.REFLECTION: "تأمل شخصي",
            AnnotationType.EXPLANATION: "شرح وتفسير",
            AnnotationType.LINGUISTIC: "تحليل لغوي",
            AnnotationType.THEMATIC: "تحديد الموضوع",
            AnnotationType.LIFE_LESSON: "درس حياتي",
            AnnotationType.HISTORICAL: "سياق تاريخي",
            AnnotationType.CONNECTION: "ربط بآيات أخرى",
            AnnotationType.QUESTION: "سؤال",
        }
        return names.get(t, "غير محدد")

    def _get_type_name_en(self, t: AnnotationType) -> str:
        """Get English name for annotation type."""
        names = {
            AnnotationType.REFLECTION: "Personal Reflection",
            AnnotationType.EXPLANATION: "Explanation/Tafsir",
            AnnotationType.LINGUISTIC: "Linguistic Analysis",
            AnnotationType.THEMATIC: "Theme Identification",
            AnnotationType.LIFE_LESSON: "Life Lesson",
            AnnotationType.HISTORICAL: "Historical Context",
            AnnotationType.CONNECTION: "Cross-Reference",
            AnnotationType.QUESTION: "Question",
        }
        return names.get(t, "Unknown")


# =============================================================================
# EXPERT ANNOTATION SYSTEM (PHASE 8 ENHANCEMENT)
# =============================================================================


class ScholarCredential(str, Enum):
    """Types of scholar credentials."""
    IJAZAH = "ijazah"                    # Traditional Islamic certification
    PHD_ISLAMIC_STUDIES = "phd_islamic"  # PhD in Islamic studies
    MASTERS_QURAN = "masters_quran"      # Masters in Quranic studies
    HAFIZ = "hafiz"                      # Quran memorizer
    ALIM = "alim"                        # Traditional scholar
    MUFTI = "mufti"                      # Qualified to give fatwa
    MUHADITH = "muhadith"                # Hadith specialist
    MUFASSIR = "mufassir"                # Tafsir specialist
    LINGUIST = "linguist"                # Arabic linguistics expert


class EndorsementType(str, Enum):
    """Types of endorsements."""
    SCHOLARLY_APPROVAL = "scholarly_approval"
    ACCURACY_VERIFIED = "accuracy_verified"
    RECOMMENDED = "recommended"
    HIGHLIGHTED = "highlighted"
    PEER_REVIEWED = "peer_reviewed"


@dataclass
class ScholarProfile:
    """Profile for a verified scholar."""
    scholar_id: str
    name_ar: str
    name_en: str
    credentials: List[ScholarCredential]
    institution: str
    specializations: List[str]
    verified: bool
    verification_date: Optional[datetime]
    endorsements_given: int
    peer_reviews_completed: int
    reputation_score: float
    bio_ar: str
    bio_en: str


@dataclass
class ScholarEndorsement:
    """Endorsement from a verified scholar."""
    endorsement_id: str
    annotation_id: str
    scholar_id: str
    endorsement_type: EndorsementType
    comment_ar: str
    comment_en: str
    created_at: datetime
    weight: float  # Based on scholar's reputation


@dataclass
class PeerReview:
    """Peer review of an annotation."""
    review_id: str
    annotation_id: str
    reviewer_id: str  # Scholar ID
    accuracy_score: float  # 0-1
    depth_score: float  # 0-1
    relevance_score: float  # 0-1
    suggestions_ar: str
    suggestions_en: str
    verdict: str  # approve, revise, reject
    created_at: datetime


class ExpertAnnotationService:
    """
    Expert Annotation System with peer review and scholar endorsements.

    Features:
    - Scholar verification and profiles
    - Peer review workflow
    - Scholar endorsements
    - Expert-verified annotations
    - Credential-based weighting

    Arabic: نظام التعليقات الخبيرة مع مراجعة الأقران وتأييد العلماء
    """

    def __init__(self, annotation_service: AnnotationService):
        self._annotation_service = annotation_service
        self._scholars: Dict[str, ScholarProfile] = {}
        self._endorsements: Dict[str, List[ScholarEndorsement]] = defaultdict(list)
        self._peer_reviews: Dict[str, List[PeerReview]] = defaultdict(list)
        self._pending_peer_reviews: List[str] = []

        # Initialize with sample verified scholars
        self._initialize_sample_scholars()

    def _initialize_sample_scholars(self):
        """Initialize with sample verified scholars for demo."""
        sample_scholars = [
            {
                "scholar_id": "scholar_001",
                "name_ar": "د. أحمد العالم",
                "name_en": "Dr. Ahmad Al-Alim",
                "credentials": [ScholarCredential.PHD_ISLAMIC_STUDIES, ScholarCredential.HAFIZ],
                "institution": "Al-Azhar University",
                "specializations": ["tafsir", "arabic_linguistics"],
                "bio_ar": "أستاذ التفسير وعلوم القرآن",
                "bio_en": "Professor of Tafsir and Quranic Sciences",
            },
            {
                "scholar_id": "scholar_002",
                "name_ar": "الشيخ محمد الفقيه",
                "name_en": "Sheikh Muhammad Al-Faqih",
                "credentials": [ScholarCredential.IJAZAH, ScholarCredential.ALIM, ScholarCredential.MUFTI],
                "institution": "Dar al-Ulum",
                "specializations": ["fiqh", "usul_al_fiqh"],
                "bio_ar": "عالم في الفقه وأصوله",
                "bio_en": "Scholar of Fiqh and its Principles",
            },
            {
                "scholar_id": "scholar_003",
                "name_ar": "د. فاطمة الحافظة",
                "name_en": "Dr. Fatima Al-Hafiza",
                "credentials": [ScholarCredential.PHD_ISLAMIC_STUDIES, ScholarCredential.HAFIZ, ScholarCredential.MUFASSIR],
                "institution": "Islamic University of Madinah",
                "specializations": ["tajweed", "tafsir", "women_studies"],
                "bio_ar": "متخصصة في علوم القرآن والتجويد",
                "bio_en": "Specialist in Quranic Sciences and Tajweed",
            },
        ]

        for data in sample_scholars:
            self._scholars[data["scholar_id"]] = ScholarProfile(
                scholar_id=data["scholar_id"],
                name_ar=data["name_ar"],
                name_en=data["name_en"],
                credentials=data["credentials"],
                institution=data["institution"],
                specializations=data["specializations"],
                verified=True,
                verification_date=datetime.now() - timedelta(days=365),
                endorsements_given=0,
                peer_reviews_completed=0,
                reputation_score=100.0,
                bio_ar=data["bio_ar"],
                bio_en=data["bio_en"],
            )

    def register_scholar(
        self,
        scholar_id: str,
        name_ar: str,
        name_en: str,
        credentials: List[str],
        institution: str,
        specializations: List[str],
        bio_ar: str = "",
        bio_en: str = "",
    ) -> Dict[str, Any]:
        """Register a new scholar (pending verification)."""
        if scholar_id in self._scholars:
            return {"error": "Scholar ID already exists"}

        cred_enums = []
        for c in credentials:
            try:
                cred_enums.append(ScholarCredential(c))
            except ValueError:
                pass

        profile = ScholarProfile(
            scholar_id=scholar_id,
            name_ar=name_ar,
            name_en=name_en,
            credentials=cred_enums,
            institution=institution,
            specializations=specializations,
            verified=False,  # Pending verification
            verification_date=None,
            endorsements_given=0,
            peer_reviews_completed=0,
            reputation_score=0.0,
            bio_ar=bio_ar,
            bio_en=bio_en,
        )

        self._scholars[scholar_id] = profile

        return {
            "scholar_id": scholar_id,
            "status": "pending_verification",
            "message_ar": "تم تسجيل الملف الشخصي، في انتظار التحقق",
            "message_en": "Profile registered, pending verification",
        }

    def verify_scholar(
        self,
        scholar_id: str,
        verifier_id: str,
    ) -> Dict[str, Any]:
        """Verify a scholar's credentials (admin action)."""
        if scholar_id not in self._scholars:
            return {"error": "Scholar not found"}

        scholar = self._scholars[scholar_id]
        scholar.verified = True
        scholar.verification_date = datetime.now()
        scholar.reputation_score = 50.0  # Starting reputation

        return {
            "scholar_id": scholar_id,
            "verified": True,
            "verification_date": scholar.verification_date.isoformat(),
        }

    def get_scholar_profile(
        self,
        scholar_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get scholar profile."""
        if scholar_id not in self._scholars:
            return None

        scholar = self._scholars[scholar_id]

        return {
            "scholar_id": scholar.scholar_id,
            "name_ar": scholar.name_ar,
            "name_en": scholar.name_en,
            "credentials": [c.value for c in scholar.credentials],
            "institution": scholar.institution,
            "specializations": scholar.specializations,
            "verified": scholar.verified,
            "verification_date": scholar.verification_date.isoformat() if scholar.verification_date else None,
            "endorsements_given": scholar.endorsements_given,
            "peer_reviews_completed": scholar.peer_reviews_completed,
            "reputation_score": round(scholar.reputation_score, 2),
            "bio_ar": scholar.bio_ar,
            "bio_en": scholar.bio_en,
        }

    def get_all_verified_scholars(self) -> List[Dict[str, Any]]:
        """Get all verified scholars."""
        return [
            {
                "scholar_id": s.scholar_id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "credentials": [c.value for c in s.credentials],
                "institution": s.institution,
                "specializations": s.specializations[:3],
                "reputation_score": round(s.reputation_score, 2),
            }
            for s in self._scholars.values()
            if s.verified
        ]

    def submit_expert_annotation(
        self,
        scholar_id: str,
        verse_reference: str,
        annotation_type: str,
        content_ar: str,
        content_en: str,
        tags: Optional[List[str]] = None,
        requires_peer_review: bool = True,
    ) -> Dict[str, Any]:
        """Submit an expert annotation from a verified scholar."""
        if scholar_id not in self._scholars:
            return {"error": "Scholar not found"}

        scholar = self._scholars[scholar_id]
        if not scholar.verified:
            return {"error": "Scholar not verified"}

        # Submit through regular service but with special handling
        result = self._annotation_service.submit_annotation(
            user_id=scholar_id,
            verse_reference=verse_reference,
            annotation_type=annotation_type,
            content_ar=content_ar,
            content_en=content_en,
            tags=tags,
        )

        if "error" in result:
            return result

        annotation_id = result["annotation_id"]

        # Mark as expert annotation
        if annotation_id in self._annotation_service._annotations:
            ann = self._annotation_service._annotations[annotation_id]
            ann.nlp_analysis["is_expert"] = True
            ann.nlp_analysis["scholar_id"] = scholar_id
            ann.nlp_analysis["scholar_credentials"] = [c.value for c in scholar.credentials]

            # Auto-approve expert annotations unless peer review required
            if not requires_peer_review:
                ann.status = AnnotationStatus.APPROVED
            else:
                self._pending_peer_reviews.append(annotation_id)
                ann.status = AnnotationStatus.UNDER_REVIEW

        return {
            **result,
            "is_expert": True,
            "scholar_id": scholar_id,
            "requires_peer_review": requires_peer_review,
        }

    def submit_peer_review(
        self,
        annotation_id: str,
        reviewer_id: str,
        accuracy_score: float,
        depth_score: float,
        relevance_score: float,
        suggestions_ar: str = "",
        suggestions_en: str = "",
        verdict: str = "approve",  # approve, revise, reject
    ) -> Dict[str, Any]:
        """Submit a peer review for an annotation."""
        if reviewer_id not in self._scholars:
            return {"error": "Reviewer must be a verified scholar"}

        reviewer = self._scholars[reviewer_id]
        if not reviewer.verified:
            return {"error": "Reviewer not verified"}

        if annotation_id not in self._annotation_service._annotations:
            return {"error": "Annotation not found"}

        # Check reviewer is not the author
        ann = self._annotation_service._annotations[annotation_id]
        if ann.user_id == reviewer_id:
            return {"error": "Cannot review your own annotation"}

        # Create review
        review_id = hashlib.md5(
            f"{annotation_id}:{reviewer_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        review = PeerReview(
            review_id=review_id,
            annotation_id=annotation_id,
            reviewer_id=reviewer_id,
            accuracy_score=accuracy_score,
            depth_score=depth_score,
            relevance_score=relevance_score,
            suggestions_ar=suggestions_ar,
            suggestions_en=suggestions_en,
            verdict=verdict,
            created_at=datetime.now(),
        )

        self._peer_reviews[annotation_id].append(review)

        # Update reviewer stats
        reviewer.peer_reviews_completed += 1
        reviewer.reputation_score += 5

        # Process verdict
        if len(self._peer_reviews[annotation_id]) >= 2:
            # Check consensus
            verdicts = [r.verdict for r in self._peer_reviews[annotation_id]]
            approve_count = verdicts.count("approve")

            if approve_count >= 2:
                ann.status = AnnotationStatus.APPROVED
            elif verdicts.count("reject") >= 2:
                ann.status = AnnotationStatus.REJECTED

            # Remove from pending
            if annotation_id in self._pending_peer_reviews:
                self._pending_peer_reviews.remove(annotation_id)

        return {
            "review_id": review_id,
            "annotation_id": annotation_id,
            "reviewer_id": reviewer_id,
            "verdict": verdict,
            "overall_score": round((accuracy_score + depth_score + relevance_score) / 3, 2),
            "status": ann.status.value,
        }

    def endorse_annotation(
        self,
        annotation_id: str,
        scholar_id: str,
        endorsement_type: str,
        comment_ar: str = "",
        comment_en: str = "",
    ) -> Dict[str, Any]:
        """Scholar endorses an annotation."""
        if scholar_id not in self._scholars:
            return {"error": "Scholar not found"}

        scholar = self._scholars[scholar_id]
        if not scholar.verified:
            return {"error": "Scholar not verified"}

        if annotation_id not in self._annotation_service._annotations:
            return {"error": "Annotation not found"}

        # Calculate weight based on scholar's reputation
        weight = min(1.0, scholar.reputation_score / 100)

        endorsement_id = hashlib.md5(
            f"{annotation_id}:{scholar_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        try:
            etype = EndorsementType(endorsement_type)
        except ValueError:
            etype = EndorsementType.SCHOLARLY_APPROVAL

        endorsement = ScholarEndorsement(
            endorsement_id=endorsement_id,
            annotation_id=annotation_id,
            scholar_id=scholar_id,
            endorsement_type=etype,
            comment_ar=comment_ar,
            comment_en=comment_en,
            created_at=datetime.now(),
            weight=weight,
        )

        self._endorsements[annotation_id].append(endorsement)

        # Update scholar stats
        scholar.endorsements_given += 1

        # Boost annotation author's reputation
        ann = self._annotation_service._annotations[annotation_id]
        if ann.user_id in self._annotation_service._user_profiles:
            self._annotation_service._user_profiles[ann.user_id].reputation_score += 10 * weight

        # Feature highly endorsed annotations
        if len(self._endorsements[annotation_id]) >= 3:
            ann.status = AnnotationStatus.FEATURED

        return {
            "endorsement_id": endorsement_id,
            "annotation_id": annotation_id,
            "scholar_id": scholar_id,
            "scholar_name_en": scholar.name_en,
            "endorsement_type": etype.value,
            "weight": round(weight, 2),
            "total_endorsements": len(self._endorsements[annotation_id]),
        }

    def get_annotation_endorsements(
        self,
        annotation_id: str,
    ) -> Dict[str, Any]:
        """Get all endorsements for an annotation."""
        if annotation_id not in self._annotation_service._annotations:
            return {"error": "Annotation not found"}

        endorsements = self._endorsements.get(annotation_id, [])

        return {
            "annotation_id": annotation_id,
            "endorsements": [
                {
                    "endorsement_id": e.endorsement_id,
                    "scholar_id": e.scholar_id,
                    "scholar_name_en": self._scholars[e.scholar_id].name_en if e.scholar_id in self._scholars else "Unknown",
                    "endorsement_type": e.endorsement_type.value,
                    "comment_en": e.comment_en,
                    "created_at": e.created_at.isoformat(),
                    "weight": round(e.weight, 2),
                }
                for e in endorsements
            ],
            "total_endorsements": len(endorsements),
            "total_weight": round(sum(e.weight for e in endorsements), 2),
        }

    def get_annotation_peer_reviews(
        self,
        annotation_id: str,
    ) -> Dict[str, Any]:
        """Get all peer reviews for an annotation."""
        reviews = self._peer_reviews.get(annotation_id, [])

        return {
            "annotation_id": annotation_id,
            "reviews": [
                {
                    "review_id": r.review_id,
                    "reviewer_id": r.reviewer_id,
                    "reviewer_name_en": self._scholars[r.reviewer_id].name_en if r.reviewer_id in self._scholars else "Unknown",
                    "accuracy_score": r.accuracy_score,
                    "depth_score": r.depth_score,
                    "relevance_score": r.relevance_score,
                    "overall_score": round((r.accuracy_score + r.depth_score + r.relevance_score) / 3, 2),
                    "verdict": r.verdict,
                    "suggestions_en": r.suggestions_en,
                    "created_at": r.created_at.isoformat(),
                }
                for r in reviews
            ],
            "total_reviews": len(reviews),
            "average_score": round(
                sum((r.accuracy_score + r.depth_score + r.relevance_score) / 3 for r in reviews) / len(reviews), 2
            ) if reviews else 0,
        }

    def get_expert_annotations(
        self,
        verse_reference: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get expert-contributed annotations."""
        results = []

        for ann in self._annotation_service._annotations.values():
            if not ann.nlp_analysis.get("is_expert"):
                continue

            if verse_reference and ann.verse_reference != verse_reference:
                continue

            if ann.status not in [AnnotationStatus.APPROVED, AnnotationStatus.FEATURED]:
                continue

            scholar_id = ann.nlp_analysis.get("scholar_id")
            scholar = self._scholars.get(scholar_id)

            results.append({
                "annotation_id": ann.annotation_id,
                "verse_reference": ann.verse_reference,
                "annotation_type": ann.annotation_type.value,
                "content_ar": ann.content_ar,
                "content_en": ann.content_en,
                "scholar": {
                    "scholar_id": scholar_id,
                    "name_en": scholar.name_en if scholar else "Unknown",
                    "credentials": ann.nlp_analysis.get("scholar_credentials", []),
                },
                "endorsements_count": len(self._endorsements.get(ann.annotation_id, [])),
                "peer_reviews_count": len(self._peer_reviews.get(ann.annotation_id, [])),
                "status": ann.status.value,
            })

        # Sort by endorsements
        results.sort(key=lambda x: x["endorsements_count"], reverse=True)
        return results[:limit]

    def get_pending_peer_reviews(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get annotations pending peer review."""
        results = []

        for ann_id in self._pending_peer_reviews[:limit]:
            if ann_id in self._annotation_service._annotations:
                ann = self._annotation_service._annotations[ann_id]
                results.append({
                    "annotation_id": ann_id,
                    "verse_reference": ann.verse_reference,
                    "content_en": ann.content_en[:200] + "..." if len(ann.content_en) > 200 else ann.content_en,
                    "scholar_id": ann.nlp_analysis.get("scholar_id"),
                    "reviews_received": len(self._peer_reviews.get(ann_id, [])),
                    "reviews_needed": max(0, 2 - len(self._peer_reviews.get(ann_id, []))),
                })

        return results

    def get_endorsement_types(self) -> List[Dict[str, str]]:
        """Get all endorsement types."""
        return [
            {"id": e.value, "name_en": e.value.replace("_", " ").title()}
            for e in EndorsementType
        ]

    def get_credential_types(self) -> List[Dict[str, str]]:
        """Get all scholar credential types."""
        descriptions = {
            ScholarCredential.IJAZAH: "Traditional Islamic certification chain",
            ScholarCredential.PHD_ISLAMIC_STUDIES: "Doctoral degree in Islamic Studies",
            ScholarCredential.MASTERS_QURAN: "Master's degree in Quranic Studies",
            ScholarCredential.HAFIZ: "Complete Quran memorization",
            ScholarCredential.ALIM: "Traditional Islamic scholarship",
            ScholarCredential.MUFTI: "Qualified to issue religious rulings",
            ScholarCredential.MUHADITH: "Specialist in Hadith sciences",
            ScholarCredential.MUFASSIR: "Specialist in Tafsir",
            ScholarCredential.LINGUIST: "Expert in Arabic linguistics",
        }

        return [
            {"id": c.value, "name_en": c.value.replace("_", " ").title(), "description": descriptions.get(c, "")}
            for c in ScholarCredential
        ]

    def get_expert_statistics(self) -> Dict[str, Any]:
        """Get statistics about the expert annotation system."""
        verified_scholars = sum(1 for s in self._scholars.values() if s.verified)
        total_endorsements = sum(len(e) for e in self._endorsements.values())
        total_reviews = sum(len(r) for r in self._peer_reviews.values())

        expert_annotations = sum(
            1 for a in self._annotation_service._annotations.values()
            if a.nlp_analysis.get("is_expert")
        )

        return {
            "verified_scholars": verified_scholars,
            "pending_scholars": len(self._scholars) - verified_scholars,
            "total_endorsements": total_endorsements,
            "total_peer_reviews": total_reviews,
            "expert_annotations": expert_annotations,
            "pending_peer_reviews": len(self._pending_peer_reviews),
            "annotations_with_endorsements": len(self._endorsements),
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

annotation_service = AnnotationService()
expert_annotation_service = ExpertAnnotationService(annotation_service)
