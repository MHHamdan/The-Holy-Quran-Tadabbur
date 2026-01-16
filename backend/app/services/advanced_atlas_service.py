"""
Advanced Atlas Service - FANG-Level Enhancements v2.0

Provides:
1. Human-in-the-loop verification pipeline with ML feedback learning
2. Semantic search with AraBERT-like embeddings and intent detection
3. AI-driven personalization with SM2 spaced repetition and adaptive learning
4. Expanded knowledge graph with temporal and cause-effect relationships
5. Scalability features - auto-scaling, load balancing, cache warming
6. Interactive graph exploration with zoom and real-time node exploration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from datetime import datetime, timedelta
import re
import math
import hashlib
import random
from collections import defaultdict
import numpy as np


# ============================================
# ENUMS AND DATA CLASSES
# ============================================

class VerificationStatus(Enum):
    """Status of story verification"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    FLAGGED = "flagged"


class VerificationPriority(Enum):
    """Priority levels for verification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QueryIntent(Enum):
    """User query intent types"""
    STORY_SEARCH = "story_search"           # Looking for a specific story
    THEME_EXPLORATION = "theme_exploration"  # Exploring themes
    PROPHET_INFO = "prophet_info"           # Information about prophets
    RULING_QUERY = "ruling_query"           # Fiqh ruling question
    GUIDANCE_SEEKING = "guidance_seeking"   # Spiritual guidance
    TAFSIR_REQUEST = "tafsir_request"       # Requesting interpretation
    COMPARISON = "comparison"               # Comparing stories/themes
    LEARNING = "learning"                   # Educational content


class LearningGoal(Enum):
    """User learning goals"""
    MEMORIZATION = "memorization"           # Hifz - memorizing Quran
    COMPREHENSION = "comprehension"         # Understanding meanings
    TAFSIR_STUDY = "tafsir_study"          # Studying interpretations
    THEMATIC_STUDY = "thematic_study"       # Studying by themes
    STORY_EXPLORATION = "story_exploration" # Exploring Quranic stories
    FIQH_LEARNING = "fiqh_learning"        # Learning jurisprudence
    ARABIC_LEARNING = "arabic_learning"     # Learning Arabic through Quran


@dataclass
class VerificationTask:
    """A verification task for human review"""
    task_id: str
    story_id: str
    task_type: str  # "accuracy", "completeness", "categorization", "tafsir"
    status: VerificationStatus
    priority: VerificationPriority
    created_at: datetime
    assigned_to: Optional[str]
    issues_found: List[str]
    ai_confidence: float  # 0-1 confidence score
    madhab_verification: Dict[str, bool]  # Verified by each madhab
    reviewer_notes: Optional[str]
    resolution: Optional[str]


@dataclass
class UserLearningProfile:
    """User learning profile with SM2 data"""
    user_id: str
    learning_goal: LearningGoal
    preferred_language: str
    preferred_madhab: Optional[str]
    themes_of_interest: Set[str]
    stories_completed: Set[str]
    current_streak: int
    total_time_spent: int  # seconds
    sm2_data: Dict[str, Dict[str, Any]]  # story_id -> SM2 parameters
    interaction_history: List[Dict[str, Any]]
    milestones: List[str]
    created_at: datetime
    last_active: datetime


@dataclass
class SemanticSearchResult:
    """Result from semantic search"""
    story_id: str
    title_ar: str
    title_en: str
    relevance_score: float
    semantic_similarity: float
    intent_match: bool
    matched_concepts: List[str]
    context_snippet_ar: str
    context_snippet_en: str


@dataclass
class MLFeedbackModel:
    """ML model that learns from admin feedback"""
    feature_weights: Dict[str, float]
    decision_history: List[Dict[str, Any]]
    accuracy_score: float
    last_trained: datetime
    training_samples: int


@dataclass
class EntityRelationship:
    """Deep entity relationship with temporal and cause-effect data"""
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relationship_type: str  # "caused_by", "leads_to", "contemporary", "mentioned_with"
    temporal_order: Optional[int]  # Chronological ordering
    strength: float  # 0-1 relationship strength
    evidence: List[str]  # Verse references
    madhab_consensus: Dict[str, bool]  # Agreement across madhabs


class EdgeCaseType(Enum):
    """Types of edge cases requiring manual review"""
    CONFLICTING_NARRATIONS = "conflicting_narrations"
    MULTIPLE_INTERPRETATIONS = "multiple_interpretations"
    DISPUTED_ATTRIBUTION = "disputed_attribution"
    INCOMPLETE_SOURCES = "incomplete_sources"
    CROSS_MADHAB_DISAGREEMENT = "cross_madhab_disagreement"


class RelationshipType(Enum):
    """Types of knowledge graph relationships"""
    TEMPORAL = "temporal"           # Time-based sequence
    CAUSAL = "causal"               # Cause and effect
    THEMATIC = "thematic"           # Shared themes
    GEOGRAPHICAL = "geographical"   # Shared locations
    GENEALOGICAL = "genealogical"   # Family/lineage
    NARRATIVE = "narrative"         # Story continuation
    REFERENCE = "reference"         # Cross-reference


class AdvancedAtlasService:
    """
    Advanced Atlas Service with FANG-level features.
    Provides verification pipeline, semantic search, and personalization.
    """

    def __init__(self):
        # Verification system
        self._verification_tasks: Dict[str, VerificationTask] = {}
        self._verification_queue: List[str] = []  # Task IDs in priority order
        self._admin_users: Set[str] = {"admin", "scholar_1", "scholar_2"}

        # User learning profiles
        self._user_profiles: Dict[str, UserLearningProfile] = {}

        # Semantic search index with AraBERT-like embeddings
        self._semantic_index: Dict[str, List[float]] = {}  # story_id -> embedding
        self._concept_index: Dict[str, Set[str]] = {}  # concept -> story_ids
        self._embedding_dimension: int = 768  # AraBERT embedding size

        # Cache warming and auto-scaling
        self._warm_cache: Dict[str, Any] = {}
        self._cache_stats: Dict[str, int] = {"hits": 0, "misses": 0}
        self._request_history: List[Dict[str, Any]] = []  # For auto-scaling decisions
        self._auto_scale_config: Dict[str, Any] = {
            "min_instances": 1,
            "max_instances": 10,
            "current_instances": 1,
            "scale_up_threshold": 0.8,  # CPU usage threshold
            "scale_down_threshold": 0.3,
            "cooldown_seconds": 300
        }

        # Knowledge graph expansion with temporal/causal relationships
        self._entity_relationships: Dict[str, List[EntityRelationship]] = {}
        self._temporal_graph: Dict[str, Dict[str, Any]] = {}  # Chronological ordering
        self._causal_graph: Dict[str, List[str]] = {}  # Cause-effect chains

        # ML Feedback Learning Model
        self._ml_model: MLFeedbackModel = MLFeedbackModel(
            feature_weights={
                "completeness_score": 1.0,
                "theme_count": 0.5,
                "verse_count": 0.8,
                "tafsir_count": 0.7,
                "figure_count": 0.4,
                "event_count": 0.6,
                "summary_length": 0.3
            },
            decision_history=[],
            accuracy_score=0.0,
            last_trained=datetime.now(),
            training_samples=0
        )

        # Edge case detection patterns
        self._edge_case_patterns: Dict[EdgeCaseType, List[str]] = {
            EdgeCaseType.CONFLICTING_NARRATIONS: [
                "اختلاف", "خلاف", "روايات متعددة", "disagreement"
            ],
            EdgeCaseType.MULTIPLE_INTERPRETATIONS: [
                "تفسيرات مختلفة", "آراء", "interpretations"
            ],
            EdgeCaseType.DISPUTED_ATTRIBUTION: [
                "منسوب", "مشكوك", "attributed", "disputed"
            ],
            EdgeCaseType.CROSS_MADHAB_DISAGREEMENT: [
                "حنفي", "مالكي", "شافعي", "حنبلي", "madhab"
            ]
        }

        # Interactive graph state
        self._graph_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> state

        # Initialize components
        self._initialize_concept_index()
        self._initialize_semantic_embeddings()
        self._initialize_temporal_causal_graph()
        self._initialize_arabert_vocabulary()

    # ============================================
    # 1. VERIFICATION PIPELINE (HUMAN IN THE LOOP)
    # ============================================

    def create_verification_task(
        self,
        story_id: str,
        task_type: str,
        issues_found: List[str],
        ai_confidence: float,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a verification task for human review.
        AI flags potential issues, humans verify.
        """
        task_id = f"vt_{story_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Determine priority based on AI confidence and issue severity
        if priority:
            task_priority = VerificationPriority(priority)
        elif ai_confidence < 0.5:
            task_priority = VerificationPriority.CRITICAL
        elif ai_confidence < 0.7:
            task_priority = VerificationPriority.HIGH
        elif ai_confidence < 0.85:
            task_priority = VerificationPriority.MEDIUM
        else:
            task_priority = VerificationPriority.LOW

        task = VerificationTask(
            task_id=task_id,
            story_id=story_id,
            task_type=task_type,
            status=VerificationStatus.PENDING,
            priority=task_priority,
            created_at=datetime.now(),
            assigned_to=None,
            issues_found=issues_found,
            ai_confidence=ai_confidence,
            madhab_verification={
                "hanafi": False,
                "maliki": False,
                "shafii": False,
                "hanbali": False
            },
            reviewer_notes=None,
            resolution=None
        )

        self._verification_tasks[task_id] = task
        self._add_to_verification_queue(task_id, task_priority)

        return {
            "success": True,
            "task_id": task_id,
            "priority": task_priority.value,
            "status": "pending",
            "message": "تم إنشاء مهمة التحقق - Verification task created"
        }

    def _add_to_verification_queue(self, task_id: str, priority: VerificationPriority):
        """Add task to queue maintaining priority order"""
        priority_order = {
            VerificationPriority.CRITICAL: 0,
            VerificationPriority.HIGH: 1,
            VerificationPriority.MEDIUM: 2,
            VerificationPriority.LOW: 3
        }

        # Find insertion point
        insert_idx = len(self._verification_queue)
        for i, existing_id in enumerate(self._verification_queue):
            existing_task = self._verification_tasks.get(existing_id)
            if existing_task and priority_order[priority] < priority_order[existing_task.priority]:
                insert_idx = i
                break

        self._verification_queue.insert(insert_idx, task_id)

    def get_verification_queue(
        self,
        admin_id: str,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get verification queue for admins"""
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        tasks = []
        for task_id in self._verification_queue:
            task = self._verification_tasks.get(task_id)
            if not task:
                continue

            # Apply filters
            if status_filter and task.status.value != status_filter:
                continue
            if priority_filter and task.priority.value != priority_filter:
                continue

            tasks.append({
                "task_id": task.task_id,
                "story_id": task.story_id,
                "task_type": task.task_type,
                "status": task.status.value,
                "priority": task.priority.value,
                "ai_confidence": task.ai_confidence,
                "issues_count": len(task.issues_found),
                "issues": task.issues_found,
                "created_at": task.created_at.isoformat(),
                "assigned_to": task.assigned_to
            })

            if len(tasks) >= limit:
                break

        return {
            "queue": tasks,
            "total_pending": len([t for t in self._verification_tasks.values()
                                 if t.status == VerificationStatus.PENDING]),
            "total_in_review": len([t for t in self._verification_tasks.values()
                                   if t.status == VerificationStatus.IN_REVIEW])
        }

    def assign_verification_task(
        self,
        task_id: str,
        admin_id: str,
        reviewer_id: str
    ) -> Dict[str, Any]:
        """Assign verification task to a reviewer"""
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        task = self._verification_tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        task.assigned_to = reviewer_id
        task.status = VerificationStatus.IN_REVIEW

        return {
            "success": True,
            "task_id": task_id,
            "assigned_to": reviewer_id,
            "status": "in_review"
        }

    def submit_verification_result(
        self,
        task_id: str,
        reviewer_id: str,
        decision: str,  # "approve", "reject", "needs_revision"
        madhab_verified: Dict[str, bool],
        notes: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit verification result from reviewer"""
        task = self._verification_tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        if task.assigned_to != reviewer_id and reviewer_id not in self._admin_users:
            return {"error": "Unauthorized - Task not assigned to this reviewer"}

        # Update task
        status_map = {
            "approve": VerificationStatus.APPROVED,
            "reject": VerificationStatus.REJECTED,
            "needs_revision": VerificationStatus.NEEDS_REVISION
        }

        task.status = status_map.get(decision, VerificationStatus.PENDING)
        task.madhab_verification.update(madhab_verified)
        task.reviewer_notes = notes
        task.resolution = resolution

        # Remove from queue if resolved
        if task.status in [VerificationStatus.APPROVED, VerificationStatus.REJECTED]:
            if task_id in self._verification_queue:
                self._verification_queue.remove(task_id)

        return {
            "success": True,
            "task_id": task_id,
            "new_status": task.status.value,
            "madhab_verification": task.madhab_verification,
            "message": "تم تسجيل نتيجة التحقق - Verification result recorded"
        }

    def flag_story_for_review(
        self,
        story_id: str,
        user_id: str,
        reason: str,
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """Allow users to flag stories for admin review"""
        task_id = f"flag_{story_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        task = VerificationTask(
            task_id=task_id,
            story_id=story_id,
            task_type="user_flag",
            status=VerificationStatus.FLAGGED,
            priority=VerificationPriority.MEDIUM,
            created_at=datetime.now(),
            assigned_to=None,
            issues_found=[f"User flag: {reason}"],
            ai_confidence=0.0,  # User-submitted, no AI confidence
            madhab_verification={
                "hanafi": False, "maliki": False,
                "shafii": False, "hanbali": False
            },
            reviewer_notes=details,
            resolution=None
        )

        self._verification_tasks[task_id] = task
        self._verification_queue.append(task_id)

        return {
            "success": True,
            "flag_id": task_id,
            "message": "شكراً لإبلاغك - تم إرسال الملاحظة للمراجعة",
            "message_en": "Thank you for flagging - Your report has been submitted for review"
        }

    def auto_verify_story(self, story_id: str) -> Dict[str, Any]:
        """
        AI-assisted automatic verification of a story.
        Returns confidence scores and flags potential issues.
        """
        from app.services.alatlas_service import alatlas_service

        story = alatlas_service.get_story(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        issues = []
        confidence_factors = []

        # Check completeness
        completeness = story.get("completeness_score", 0)
        confidence_factors.append(completeness)
        if completeness < 0.7:
            issues.append(f"Low completeness score: {completeness}")

        # Check required fields
        if not story.get("title_ar"):
            issues.append("Missing Arabic title")
            confidence_factors.append(0.0)
        else:
            confidence_factors.append(1.0)

        if not story.get("summary_ar") or len(story.get("summary_ar", "")) < 100:
            issues.append("Summary too short or missing")
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(1.0)

        # Check themes consistency
        themes = story.get("themes", [])
        themes_ar = story.get("themes_ar", [])
        if len(themes) != len(themes_ar):
            issues.append("Theme count mismatch between Arabic and English")
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(1.0)

        # Check figures
        figures = story.get("figures", [])
        if not figures:
            issues.append("No figures/characters defined")
            confidence_factors.append(0.5)
        elif not any(f.get("is_prophet") for f in figures):
            issues.append("No prophet identified in prophet story")
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(1.0)

        # Check events
        events = story.get("events", [])
        if not events:
            issues.append("No events defined")
            confidence_factors.append(0.5)
        elif len(events) < 3:
            issues.append("Too few events (< 3)")
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(1.0)

        # Check verse references
        verses = story.get("verses", [])
        if not verses:
            issues.append("No Quranic verse references")
            confidence_factors.append(0.4)
        else:
            confidence_factors.append(1.0)

        # Check tafsir references
        tafsir = story.get("tafsir_references", [])
        if not tafsir:
            issues.append("No Tafsir references from four madhabs")
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0

        # Create verification task if issues found
        if issues:
            self.create_verification_task(
                story_id=story_id,
                task_type="auto_verification",
                issues_found=issues,
                ai_confidence=overall_confidence
            )

        return {
            "story_id": story_id,
            "ai_confidence": round(overall_confidence, 2),
            "issues_found": issues,
            "issues_count": len(issues),
            "verification_required": len(issues) > 0 or overall_confidence < 0.8,
            "recommendation": "approve" if overall_confidence >= 0.9 and not issues else
                            "review" if overall_confidence >= 0.7 else "needs_attention"
        }

    # ============================================
    # 1.5 ML FEEDBACK LEARNING SYSTEM
    # ============================================

    def train_ml_model_from_feedback(
        self,
        admin_id: str,
        training_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Train ML model from admin verification feedback.
        The model learns to predict verification outcomes based on story features.
        """
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        # Use existing decision history if no training data provided
        if not training_data:
            training_data = self._ml_model.decision_history

        if len(training_data) < 5:
            return {
                "success": False,
                "message": "Insufficient training data (minimum 5 samples required)",
                "current_samples": len(training_data)
            }

        # Extract features and labels
        feature_names = list(self._ml_model.feature_weights.keys())
        X = []  # Feature vectors
        y = []  # Labels (1 = approved, 0 = rejected)

        for sample in training_data:
            features = [sample.get("features", {}).get(f, 0) for f in feature_names]
            X.append(features)
            y.append(1 if sample.get("decision") == "approve" else 0)

        # Simple gradient descent to update weights
        X = np.array(X)
        y = np.array(y)
        learning_rate = 0.1
        epochs = 100

        weights = np.array([self._ml_model.feature_weights[f] for f in feature_names])

        for _ in range(epochs):
            # Forward pass
            predictions = 1 / (1 + np.exp(-X.dot(weights)))  # Sigmoid
            # Gradient
            gradient = X.T.dot(predictions - y) / len(y)
            # Update weights
            weights -= learning_rate * gradient

        # Update model weights
        for i, feature in enumerate(feature_names):
            self._ml_model.feature_weights[feature] = float(weights[i])

        # Calculate accuracy
        final_predictions = (1 / (1 + np.exp(-X.dot(weights)))) > 0.5
        accuracy = np.mean(final_predictions == y)

        self._ml_model.accuracy_score = float(accuracy)
        self._ml_model.last_trained = datetime.now()
        self._ml_model.training_samples = len(training_data)

        return {
            "success": True,
            "accuracy": round(accuracy, 4),
            "training_samples": len(training_data),
            "updated_weights": self._ml_model.feature_weights,
            "trained_at": self._ml_model.last_trained.isoformat()
        }

    def ml_predict_verification(self, story_id: str) -> Dict[str, Any]:
        """
        Use ML model to predict verification outcome for a story.
        Based on learned patterns from admin feedback.
        """
        from app.services.alatlas_service import alatlas_service

        story = alatlas_service.get_story(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        # Extract features
        features = {
            "completeness_score": story.get("completeness_score", 0),
            "theme_count": len(story.get("themes", [])),
            "verse_count": len(story.get("verses", [])),
            "tafsir_count": len(story.get("tafsir_references", [])),
            "figure_count": len(story.get("figures", [])),
            "event_count": len(story.get("events", [])),
            "summary_length": len(story.get("summary_ar", "")) / 1000  # Normalized
        }

        # Calculate prediction using learned weights
        feature_vector = np.array([
            features[f] * self._ml_model.feature_weights[f]
            for f in self._ml_model.feature_weights.keys()
        ])
        prediction_score = 1 / (1 + np.exp(-np.sum(feature_vector)))  # Sigmoid

        # Determine recommendation
        if prediction_score >= 0.8:
            recommendation = "auto_approve"
            confidence = "high"
        elif prediction_score >= 0.6:
            recommendation = "likely_approve"
            confidence = "medium"
        elif prediction_score >= 0.4:
            recommendation = "needs_review"
            confidence = "low"
        else:
            recommendation = "likely_reject"
            confidence = "medium"

        return {
            "story_id": story_id,
            "ml_prediction_score": round(float(prediction_score), 4),
            "recommendation": recommendation,
            "confidence": confidence,
            "model_accuracy": self._ml_model.accuracy_score,
            "feature_scores": features,
            "model_trained_at": self._ml_model.last_trained.isoformat(),
            "training_samples": self._ml_model.training_samples
        }

    def record_verification_feedback(
        self,
        task_id: str,
        decision: str,
        reviewer_id: str
    ) -> Dict[str, Any]:
        """
        Record verification feedback to train the ML model.
        """
        from app.services.alatlas_service import alatlas_service

        task = self._verification_tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        story = alatlas_service.get_story(task.story_id)
        if not story:
            return {"error": f"Story '{task.story_id}' not found"}

        # Extract features for training
        features = {
            "completeness_score": story.get("completeness_score", 0),
            "theme_count": len(story.get("themes", [])),
            "verse_count": len(story.get("verses", [])),
            "tafsir_count": len(story.get("tafsir_references", [])),
            "figure_count": len(story.get("figures", [])),
            "event_count": len(story.get("events", [])),
            "summary_length": len(story.get("summary_ar", "")) / 1000
        }

        # Record for ML training
        feedback_record = {
            "task_id": task_id,
            "story_id": task.story_id,
            "decision": decision,
            "reviewer_id": reviewer_id,
            "features": features,
            "timestamp": datetime.now().isoformat()
        }

        self._ml_model.decision_history.append(feedback_record)

        # Auto-retrain if enough new samples
        auto_retrain = False
        if len(self._ml_model.decision_history) >= 10 and \
           len(self._ml_model.decision_history) % 5 == 0:
            self.train_ml_model_from_feedback("admin")
            auto_retrain = True

        return {
            "success": True,
            "feedback_recorded": True,
            "total_training_samples": len(self._ml_model.decision_history),
            "auto_retrained": auto_retrain
        }

    def detect_edge_cases(self, story_id: str) -> Dict[str, Any]:
        """
        Detect edge cases that require manual human review.
        Identifies conflicting narrations, disputed attributions, etc.
        """
        from app.services.alatlas_service import alatlas_service

        story = alatlas_service.get_story(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        edge_cases = []
        risk_level = "low"

        # Check all text content for edge case patterns
        text_content = " ".join([
            story.get("summary_ar", ""),
            story.get("summary_en", ""),
            " ".join([e.get("description_ar", "") for e in story.get("events", [])]),
            " ".join([str(t) for t in story.get("tafsir_references", [])])
        ]).lower()

        for edge_type, patterns in self._edge_case_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_content:
                    edge_cases.append({
                        "type": edge_type.value,
                        "trigger_pattern": pattern,
                        "requires_review": True
                    })

        # Check madhab consistency
        madhab_refs = defaultdict(int)
        for tafsir in story.get("tafsir_references", []):
            madhab = tafsir.get("madhab", "unknown")
            madhab_refs[madhab] += 1

        madhabs_present = set(madhab_refs.keys())
        required_madhabs = {"hanafi", "maliki", "shafii", "hanbali"}
        missing_madhabs = required_madhabs - madhabs_present

        if missing_madhabs:
            edge_cases.append({
                "type": EdgeCaseType.INCOMPLETE_SOURCES.value,
                "trigger_pattern": f"Missing madhabs: {', '.join(missing_madhabs)}",
                "requires_review": True
            })

        # Determine risk level
        if len(edge_cases) >= 3:
            risk_level = "high"
        elif len(edge_cases) >= 1:
            risk_level = "medium"

        # Auto-create verification task for high-risk edge cases
        if risk_level == "high":
            self.create_verification_task(
                story_id=story_id,
                task_type="edge_case_review",
                issues_found=[ec["trigger_pattern"] for ec in edge_cases],
                ai_confidence=0.3,
                priority="high"
            )

        return {
            "story_id": story_id,
            "edge_cases_detected": edge_cases,
            "edge_case_count": len(edge_cases),
            "risk_level": risk_level,
            "requires_manual_review": risk_level in ["medium", "high"],
            "madhab_coverage": {
                "present": list(madhabs_present),
                "missing": list(missing_madhabs),
                "complete": len(missing_madhabs) == 0
            }
        }

    def auto_categorize_story(self, story_id: str) -> Dict[str, Any]:
        """
        Auto-categorize story using ML and flag edge cases.
        Combines ML prediction with edge case detection.
        """
        # Get ML prediction
        ml_result = self.ml_predict_verification(story_id)
        if "error" in ml_result:
            return ml_result

        # Detect edge cases
        edge_cases = self.detect_edge_cases(story_id)
        if "error" in edge_cases:
            return edge_cases

        # Combine results
        auto_approve = (
            ml_result["recommendation"] == "auto_approve" and
            edge_cases["risk_level"] == "low"
        )

        final_recommendation = "auto_approve" if auto_approve else "manual_review"

        return {
            "story_id": story_id,
            "ml_prediction": ml_result,
            "edge_cases": edge_cases,
            "final_recommendation": final_recommendation,
            "auto_approved": auto_approve,
            "review_reasons": edge_cases["edge_cases_detected"] if not auto_approve else [],
            "confidence_score": ml_result["ml_prediction_score"] * (
                1.0 if edge_cases["risk_level"] == "low" else
                0.7 if edge_cases["risk_level"] == "medium" else 0.4
            )
        }

    def get_admin_dashboard(self, admin_id: str) -> Dict[str, Any]:
        """
        Get comprehensive admin dashboard with real-time verification status.
        """
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        # Get queue stats
        queue = self.get_verification_queue(admin_id, limit=50)

        # Calculate stats
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for task in self._verification_tasks.values():
            status_counts[task.status.value] += 1
            priority_counts[task.priority.value] += 1
            type_counts[task.task_type] += 1

        # Get ML model status
        ml_status = {
            "accuracy": self._ml_model.accuracy_score,
            "training_samples": self._ml_model.training_samples,
            "last_trained": self._ml_model.last_trained.isoformat(),
            "feature_weights": self._ml_model.feature_weights
        }

        return {
            "admin_id": admin_id,
            "dashboard_generated_at": datetime.now().isoformat(),
            "verification_queue": queue,
            "statistics": {
                "total_tasks": len(self._verification_tasks),
                "by_status": dict(status_counts),
                "by_priority": dict(priority_counts),
                "by_type": dict(type_counts)
            },
            "ml_model_status": ml_status,
            "madhab_verification_stats": self._get_madhab_stats()
        }

    def _get_madhab_stats(self) -> Dict[str, Any]:
        """Get verification statistics per madhab"""
        madhab_stats = {
            "hanafi": {"verified": 0, "pending": 0},
            "maliki": {"verified": 0, "pending": 0},
            "shafii": {"verified": 0, "pending": 0},
            "hanbali": {"verified": 0, "pending": 0}
        }

        for task in self._verification_tasks.values():
            for madhab, verified in task.madhab_verification.items():
                if verified:
                    madhab_stats[madhab]["verified"] += 1
                else:
                    madhab_stats[madhab]["pending"] += 1

        return madhab_stats

    # ============================================
    # 2. SEMANTIC SEARCH WITH INTENT DETECTION
    # ============================================

    def _initialize_concept_index(self):
        """Initialize concept-based index for semantic search"""
        # Quranic concepts with Arabic/English mappings
        self._concepts = {
            "patience": {
                "ar": ["صبر", "الصبر", "صابرين", "اصبر"],
                "en": ["patience", "patient", "endure", "persevere"],
                "related_themes": ["perseverance", "trust", "faith"],
                "prophets": ["ayub", "yaqub", "musa"]
            },
            "trust_in_allah": {
                "ar": ["توكل", "التوكل", "متوكلين", "توكلت"],
                "en": ["trust", "reliance", "tawakkul"],
                "related_themes": ["faith", "patience"],
                "prophets": ["ibrahim", "musa", "muhammad"]
            },
            "repentance": {
                "ar": ["توبة", "التوبة", "تائبين", "تاب"],
                "en": ["repentance", "repent", "forgiveness", "tawbah"],
                "related_themes": ["mercy", "forgiveness"],
                "prophets": ["adam", "dawud", "yunus"]
            },
            "divine_mercy": {
                "ar": ["رحمة", "الرحمة", "رحيم", "الرحمن"],
                "en": ["mercy", "merciful", "compassion", "rahmah"],
                "related_themes": ["forgiveness", "guidance"],
                "prophets": ["muhammad", "isa", "yusuf"]
            },
            "guidance": {
                "ar": ["هداية", "الهداية", "هدى", "يهدي"],
                "en": ["guidance", "guide", "hidayah", "path"],
                "related_themes": ["faith", "wisdom"],
                "prophets": ["muhammad", "musa", "ibrahim"]
            },
            "justice": {
                "ar": ["عدل", "العدل", "قسط", "ميزان"],
                "en": ["justice", "fairness", "equity", "balance"],
                "related_themes": ["truth", "wisdom"],
                "prophets": ["dawud", "sulayman", "musa"]
            },
            "sacrifice": {
                "ar": ["تضحية", "فداء", "ذبح", "قربان"],
                "en": ["sacrifice", "offering", "devotion"],
                "related_themes": ["obedience", "faith"],
                "prophets": ["ibrahim", "ismail"]
            },
            "tawhid": {
                "ar": ["توحيد", "التوحيد", "وحدانية", "إله واحد"],
                "en": ["monotheism", "oneness", "unity", "tawhid"],
                "related_themes": ["faith", "guidance"],
                "prophets": ["ibrahim", "musa", "muhammad"]
            },
            "prophethood": {
                "ar": ["نبوة", "النبوة", "رسالة", "الرسالة"],
                "en": ["prophethood", "prophecy", "messenger", "revelation"],
                "related_themes": ["guidance", "wisdom"],
                "prophets": ["all"]
            },
            "afterlife": {
                "ar": ["آخرة", "الآخرة", "جنة", "نار", "حساب"],
                "en": ["afterlife", "hereafter", "paradise", "hell", "judgment"],
                "related_themes": ["reward", "punishment"],
                "prophets": ["all"]
            }
        }

        # Build concept index
        for concept, data in self._concepts.items():
            self._concept_index[concept] = set()

    def _initialize_semantic_embeddings(self):
        """Initialize AraBERT-like semantic embeddings for stories"""
        # AraBERT vocabulary simulation with contextual Arabic understanding
        self._arabert_vocab = {}
        self._story_embeddings = {}

    def _initialize_arabert_vocabulary(self):
        """Initialize AraBERT-like vocabulary for Arabic semantic understanding"""
        # Root-based Arabic vocabulary with semantic weights
        self._arabic_roots = {
            # Verb roots with semantic meanings
            "صبر": {"meaning": "patience", "weight": 1.0, "related": ["حلم", "تحمل", "صمود"]},
            "توكل": {"meaning": "trust", "weight": 1.0, "related": ["إيمان", "ثقة", "اعتماد"]},
            "توب": {"meaning": "repentance", "weight": 1.0, "related": ["ندم", "رجع", "أناب"]},
            "رحم": {"meaning": "mercy", "weight": 1.0, "related": ["عطف", "شفق", "حنان"]},
            "هدى": {"meaning": "guidance", "weight": 1.0, "related": ["إرشاد", "دلالة", "هداية"]},
            "عدل": {"meaning": "justice", "weight": 1.0, "related": ["قسط", "إنصاف", "حق"]},
            "أمن": {"meaning": "faith", "weight": 1.0, "related": ["إيمان", "يقين", "تصديق"]},
            "شكر": {"meaning": "gratitude", "weight": 1.0, "related": ["حمد", "ثناء", "امتنان"]},
            "ذكر": {"meaning": "remembrance", "weight": 1.0, "related": ["تذكر", "ذكرى", "حفظ"]},
            "دعا": {"meaning": "supplication", "weight": 1.0, "related": ["صلاة", "مناجاة", "طلب"]},
        }

        # Prophet name embeddings with variations
        self._prophet_embeddings = {
            "adam": {"ar": ["آدم", "ادم"], "themes": ["creation", "repentance", "first_human"]},
            "nuh": {"ar": ["نوح", "نوحا"], "themes": ["patience", "flood", "perseverance"]},
            "ibrahim": {"ar": ["إبراهيم", "ابراهيم"], "themes": ["sacrifice", "monotheism", "faith"]},
            "musa": {"ar": ["موسى", "موسي"], "themes": ["liberation", "law", "confrontation"]},
            "isa": {"ar": ["عيسى", "عيسي"], "themes": ["miracles", "mercy", "prophecy"]},
            "yusuf": {"ar": ["يوسف", "يوسفا"], "themes": ["patience", "dreams", "forgiveness"]},
            "dawud": {"ar": ["داود", "داوود"], "themes": ["kingship", "psalms", "repentance"]},
            "sulayman": {"ar": ["سليمان", "سلمان"], "themes": ["wisdom", "kingdom", "jinn"]},
            "ayub": {"ar": ["أيوب", "ايوب"], "themes": ["patience", "trial", "healing"]},
            "yunus": {"ar": ["يونس", "يونسا"], "themes": ["repentance", "whale", "mercy"]},
            "muhammad": {"ar": ["محمد", "محمدا", "النبي"], "themes": ["final_messenger", "mercy", "guidance"]},
        }

        # Contextual phrase patterns for intent detection
        self._phrase_patterns = {
            "story_request": ["قصة", "حكاية", "أخبرني عن", "ما قصة", "tell me about"],
            "lesson_seeking": ["ماذا نتعلم", "ما الدرس", "what lesson", "ما العبرة"],
            "comparison": ["الفرق بين", "مقارنة", "compare", "versus", "أو"],
            "explanation": ["اشرح", "وضح", "explain", "ما معنى", "what does"],
            "ruling_query": ["حكم", "هل يجوز", "is it permissible", "ruling on"],
        }

    def _initialize_temporal_causal_graph(self):
        """Initialize temporal and causal relationship graph"""
        # Temporal ordering of prophets and events
        self._temporal_order = {
            "adam": {"order": 1, "era": "beginning", "years_ago": "unknown"},
            "idris": {"order": 2, "era": "early", "years_ago": "unknown"},
            "nuh": {"order": 3, "era": "flood", "years_ago": "unknown"},
            "hud": {"order": 4, "era": "post_flood", "years_ago": "unknown"},
            "salih": {"order": 5, "era": "post_flood", "years_ago": "unknown"},
            "ibrahim": {"order": 6, "era": "patriarchs", "years_ago": "4000"},
            "lut": {"order": 7, "era": "patriarchs", "years_ago": "4000"},
            "ismail": {"order": 8, "era": "patriarchs", "years_ago": "3900"},
            "ishaq": {"order": 9, "era": "patriarchs", "years_ago": "3900"},
            "yaqub": {"order": 10, "era": "patriarchs", "years_ago": "3800"},
            "yusuf": {"order": 11, "era": "egypt", "years_ago": "3700"},
            "shuayb": {"order": 12, "era": "midian", "years_ago": "3500"},
            "musa": {"order": 13, "era": "exodus", "years_ago": "3400"},
            "harun": {"order": 14, "era": "exodus", "years_ago": "3400"},
            "dawud": {"order": 15, "era": "israel_kingdom", "years_ago": "3000"},
            "sulayman": {"order": 16, "era": "israel_kingdom", "years_ago": "2950"},
            "ilyas": {"order": 17, "era": "divided_kingdom", "years_ago": "2850"},
            "alyasa": {"order": 18, "era": "divided_kingdom", "years_ago": "2800"},
            "yunus": {"order": 19, "era": "assyrian", "years_ago": "2750"},
            "zakariya": {"order": 20, "era": "second_temple", "years_ago": "2050"},
            "yahya": {"order": 21, "era": "roman", "years_ago": "2030"},
            "isa": {"order": 22, "era": "roman", "years_ago": "2025"},
            "muhammad": {"order": 23, "era": "final", "years_ago": "1445"},
        }

        # Causal relationships between events
        self._causal_chains = {
            "adam_sin": {
                "event": "Adam's eating from the tree",
                "causes": ["disobedience", "shaytan_deception"],
                "effects": ["expulsion_paradise", "earthly_life", "repentance_model"],
                "lessons": ["obedience", "repentance", "mercy"]
            },
            "nuh_flood": {
                "event": "The Great Flood",
                "causes": ["people_disbelief", "rejection_prophet"],
                "effects": ["destruction_disbelievers", "salvation_believers", "new_beginning"],
                "lessons": ["patience", "perseverance", "divine_justice"]
            },
            "ibrahim_sacrifice": {
                "event": "Ibrahim's test with Ismail",
                "causes": ["divine_command", "test_faith"],
                "effects": ["ransom_ram", "eid_adha", "model_submission"],
                "lessons": ["submission", "sacrifice", "trust"]
            },
            "yusuf_well": {
                "event": "Yusuf thrown in the well",
                "causes": ["brothers_jealousy"],
                "effects": ["slavery_egypt", "prison", "eventual_power"],
                "lessons": ["patience", "trust", "forgiveness"]
            },
            "musa_pharaoh": {
                "event": "Musa confronting Pharaoh",
                "causes": ["oppression_israelites", "divine_mission"],
                "effects": ["plagues", "exodus", "drowning_pharaoh"],
                "lessons": ["courage", "trust", "liberation"]
            },
        }

        # Build temporal graph
        for prophet, data in self._temporal_order.items():
            self._temporal_graph[prophet] = data

    def generate_arabert_embedding(self, text: str) -> List[float]:
        """
        Generate AraBERT-like embedding for text.
        Uses semantic root analysis and contextual understanding.
        """
        # Initialize embedding vector
        embedding = np.zeros(self._embedding_dimension)

        text_lower = text.lower()

        # Analyze Arabic roots
        root_scores = {}
        for root, data in self._arabic_roots.items():
            if root in text:
                root_scores[root] = data["weight"]
                # Add related root scores
                for related in data.get("related", []):
                    if related in text:
                        root_scores[root] += 0.3

        # Analyze prophet mentions
        prophet_scores = {}
        for prophet, data in self._prophet_embeddings.items():
            for ar_name in data["ar"]:
                if ar_name in text:
                    prophet_scores[prophet] = 1.0
                    break

        # Build embedding from components
        # First 256 dimensions: root-based semantics
        for i, (root, score) in enumerate(list(root_scores.items())[:256]):
            if i < 256:
                embedding[i] = score

        # Next 256 dimensions: prophet/entity mentions
        for i, (prophet, score) in enumerate(list(prophet_scores.items())[:256]):
            if i < 256:
                embedding[256 + i] = score

        # Next 256 dimensions: phrase pattern matches
        pattern_idx = 512
        for pattern_type, patterns in self._phrase_patterns.items():
            for pattern in patterns:
                if pattern in text_lower or pattern in text:
                    embedding[pattern_idx] = 1.0
                    break
            pattern_idx += 1
            if pattern_idx >= 768:
                break

        # Normalize embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def compute_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Compute cosine similarity between two texts using embeddings"""
        emb1 = np.array(self.generate_arabert_embedding(text1))
        emb2 = np.array(self.generate_arabert_embedding(text2))

        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def semantic_search_with_embeddings(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.1
    ) -> Dict[str, Any]:
        """
        Advanced semantic search using AraBERT-like embeddings.
        """
        from app.services.alatlas_service import alatlas_service

        # Generate query embedding
        query_embedding = self.generate_arabert_embedding(query)

        # Get all stories
        all_stories = alatlas_service.get_all_stories(limit=100)
        stories = all_stories.get("stories", [])

        results = []
        for story in stories:
            # Generate story embedding from title and summary
            story_text = f"{story.get('title_ar', '')} {story.get('summary_ar', '')}"
            story_embedding = self.generate_arabert_embedding(story_text)

            # Calculate similarity
            similarity = self.compute_semantic_similarity(query, story_text)

            if similarity >= min_similarity:
                results.append({
                    "story_id": story.get("id"),
                    "title_ar": story.get("title_ar"),
                    "title_en": story.get("title_en"),
                    "similarity_score": round(similarity, 4),
                    "category": story.get("category"),
                    "themes": story.get("themes", [])
                })

        # Sort by similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "query": query,
            "embedding_dimension": self._embedding_dimension,
            "results": results[:limit],
            "total_matches": len(results),
            "min_similarity_threshold": min_similarity
        }

    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect user intent from query.
        Uses keyword analysis and pattern matching.
        """
        query_lower = query.lower()
        query_ar = query  # Keep original for Arabic

        intent_scores = defaultdict(float)
        detected_concepts = []
        detected_entities = []

        # Story search patterns
        story_patterns = [
            r"قصة\s+(\w+)", r"story\s+of\s+(\w+)", r"حكاية",
            r"tell\s+me\s+about", r"أخبرني\s+عن"
        ]
        for pattern in story_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.STORY_SEARCH] += 2.0

        # Theme exploration patterns
        theme_patterns = [
            r"موضوع", r"theme", r"مواضيع", r"topics",
            r"about\s+(patience|faith|mercy)", r"عن\s+(الصبر|الإيمان|الرحمة)"
        ]
        for pattern in theme_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.THEME_EXPLORATION] += 2.0

        # Prophet info patterns
        prophet_patterns = [
            r"(prophet|نبي|رسول)\s+(\w+)", r"من\s+هو", r"who\s+is",
            r"(موسى|إبراهيم|يوسف|نوح|آدم|عيسى|محمد)"
        ]
        for pattern in prophet_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.PROPHET_INFO] += 2.0

        # Ruling/Fiqh patterns
        ruling_patterns = [
            r"حكم", r"ruling", r"حلال", r"حرام", r"فقه",
            r"is\s+it\s+(halal|haram)", r"ما\s+حكم"
        ]
        for pattern in ruling_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.RULING_QUERY] += 2.0

        # Guidance patterns
        guidance_patterns = [
            r"كيف\s+(أ|ي)", r"how\s+(do|can|should)", r"نصيحة",
            r"advice", r"help\s+me", r"ساعدني"
        ]
        for pattern in guidance_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.GUIDANCE_SEEKING] += 2.0

        # Tafsir patterns
        tafsir_patterns = [
            r"تفسير", r"tafsir", r"interpretation", r"meaning\s+of",
            r"ما\s+معنى", r"explain"
        ]
        for pattern in tafsir_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.TAFSIR_REQUEST] += 2.0

        # Comparison patterns
        comparison_patterns = [
            r"مقارنة", r"compare", r"difference\s+between",
            r"الفرق\s+بين", r"vs", r"مقابل"
        ]
        for pattern in comparison_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                intent_scores[QueryIntent.COMPARISON] += 2.0

        # Detect concepts in query
        for concept, data in self._concepts.items():
            for ar_term in data["ar"]:
                if ar_term in query_ar:
                    detected_concepts.append({
                        "concept": concept,
                        "term": ar_term,
                        "language": "ar"
                    })
            for en_term in data["en"]:
                if en_term in query_lower:
                    detected_concepts.append({
                        "concept": concept,
                        "term": en_term,
                        "language": "en"
                    })

        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])
            confidence = min(primary_intent[1] / 4.0, 1.0)  # Normalize to 0-1
        else:
            primary_intent = (QueryIntent.STORY_SEARCH, 0.5)
            confidence = 0.3

        return {
            "query": query,
            "primary_intent": primary_intent[0].value,
            "intent_confidence": round(confidence, 2),
            "all_intents": {k.value: round(v/4, 2) for k, v in intent_scores.items()},
            "detected_concepts": detected_concepts,
            "detected_entities": detected_entities,
            "suggested_filters": self._suggest_filters_for_intent(primary_intent[0], detected_concepts)
        }

    def _suggest_filters_for_intent(
        self,
        intent: QueryIntent,
        concepts: List[Dict]
    ) -> Dict[str, Any]:
        """Suggest search filters based on detected intent"""
        suggestions = {
            "categories": [],
            "themes": [],
            "prophets": [],
            "search_scope": "all"
        }

        if intent == QueryIntent.STORY_SEARCH:
            suggestions["categories"] = ["prophets", "nations", "parables"]
            suggestions["search_scope"] = "stories"

        elif intent == QueryIntent.THEME_EXPLORATION:
            suggestions["search_scope"] = "themes"
            for concept in concepts:
                concept_data = self._concepts.get(concept["concept"], {})
                suggestions["themes"].extend(concept_data.get("related_themes", []))

        elif intent == QueryIntent.PROPHET_INFO:
            suggestions["categories"] = ["prophets"]
            suggestions["search_scope"] = "prophets"

        elif intent == QueryIntent.RULING_QUERY:
            suggestions["search_scope"] = "fiqh"
            suggestions["include_tafsir"] = True

        elif intent == QueryIntent.TAFSIR_REQUEST:
            suggestions["search_scope"] = "tafsir"
            suggestions["include_all_madhabs"] = True

        return suggestions

    def semantic_search(
        self,
        query: str,
        intent: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Perform semantic search with intent-aware ranking.
        """
        from app.services.alatlas_service import alatlas_service

        # Detect intent if not provided
        if not intent:
            intent_result = self.detect_query_intent(query)
            intent = intent_result["primary_intent"]
            detected_concepts = intent_result["detected_concepts"]
        else:
            detected_concepts = []

        # Get all stories
        all_stories = alatlas_service.get_all_stories(limit=100)
        stories = all_stories.get("stories", [])

        results = []
        query_lower = query.lower()

        for story in stories:
            score = 0.0
            matched_concepts = []
            semantic_score = 0.0

            # Title match
            if query_lower in story.get("title_ar", "").lower() or \
               query_lower in story.get("title_en", "").lower():
                score += 5.0

            # Theme match
            for theme in story.get("themes", []):
                if theme in query_lower:
                    score += 3.0
                    matched_concepts.append(f"theme:{theme}")

            # Concept match
            for concept in detected_concepts:
                concept_name = concept["concept"]
                concept_data = self._concepts.get(concept_name, {})

                # Check if story themes relate to concept
                for related_theme in concept_data.get("related_themes", []):
                    if related_theme in story.get("themes", []):
                        semantic_score += 2.0
                        matched_concepts.append(f"concept:{concept_name}")

            # Summary match (simplified semantic similarity)
            summary = story.get("summary_ar", "") + " " + story.get("summary_en", "")
            summary_lower = summary.lower()

            # Count keyword matches in summary
            query_words = set(query_lower.split())
            summary_words = set(summary_lower.split())
            overlap = len(query_words & summary_words)
            semantic_score += overlap * 0.5

            total_score = score + semantic_score
            if total_score > 0:
                results.append({
                    "story_id": story.get("id"),
                    "title_ar": story.get("title_ar"),
                    "title_en": story.get("title_en"),
                    "relevance_score": round(total_score, 2),
                    "semantic_similarity": round(semantic_score / max(1, score + semantic_score), 2),
                    "intent_match": intent == "story_search",
                    "matched_concepts": list(set(matched_concepts)),
                    "category": story.get("category"),
                    "themes": story.get("themes", [])
                })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "query": query,
            "intent": intent,
            "results": results[:limit],
            "total": len(results),
            "concepts_detected": [c["concept"] for c in detected_concepts]
        }

    def expand_query(self, query: str) -> Dict[str, Any]:
        """
        Expand query with synonyms, related terms, and prophetic sayings.
        """
        expansions = [query]
        related_concepts = []
        related_ahadith = []

        query_lower = query.lower()

        # Find matching concepts
        for concept, data in self._concepts.items():
            for ar_term in data["ar"]:
                if ar_term in query:
                    expansions.extend(data["ar"])
                    expansions.extend(data["en"])
                    related_concepts.append(concept)
                    break
            for en_term in data["en"]:
                if en_term in query_lower:
                    expansions.extend(data["ar"])
                    expansions.extend(data["en"])
                    related_concepts.append(concept)
                    break

        # Add prophetic sayings references (simplified)
        hadith_references = {
            "patience": "إنما الصبر عند الصدمة الأولى",
            "trust": "لو أنكم توكلتم على الله حق توكله",
            "repentance": "كل ابن آدم خطاء وخير الخطائين التوابون",
            "mercy": "الراحمون يرحمهم الرحمن",
            "guidance": "من يهده الله فلا مضل له"
        }

        for concept in related_concepts:
            if concept.split("_")[0] in hadith_references:
                related_ahadith.append({
                    "concept": concept,
                    "hadith": hadith_references[concept.split("_")[0]]
                })

        return {
            "original_query": query,
            "expanded_queries": list(set(expansions)),
            "related_concepts": list(set(related_concepts)),
            "related_ahadith": related_ahadith
        }

    # ============================================
    # 3. AI-DRIVEN PERSONALIZATION WITH SM2
    # ============================================

    def create_user_profile(
        self,
        user_id: str,
        learning_goal: str,
        preferred_language: str = "ar",
        preferred_madhab: Optional[str] = None,
        themes_of_interest: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create or update user learning profile"""

        try:
            goal = LearningGoal(learning_goal)
        except ValueError:
            goal = LearningGoal.COMPREHENSION

        profile = UserLearningProfile(
            user_id=user_id,
            learning_goal=goal,
            preferred_language=preferred_language,
            preferred_madhab=preferred_madhab,
            themes_of_interest=set(themes_of_interest or []),
            stories_completed=set(),
            current_streak=0,
            total_time_spent=0,
            sm2_data={},
            interaction_history=[],
            milestones=[],
            created_at=datetime.now(),
            last_active=datetime.now()
        )

        self._user_profiles[user_id] = profile

        return {
            "success": True,
            "user_id": user_id,
            "profile": {
                "learning_goal": goal.value,
                "preferred_language": preferred_language,
                "preferred_madhab": preferred_madhab,
                "themes_of_interest": list(themes_of_interest or [])
            }
        }

    def track_interaction(
        self,
        user_id: str,
        interaction_type: str,  # "view", "complete", "quiz", "bookmark"
        story_id: str,
        time_spent_seconds: int = 0,
        score: Optional[float] = None,  # Quiz score 0-1
        themes_explored: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Track user interaction for personalization"""

        if user_id not in self._user_profiles:
            self.create_user_profile(user_id, "comprehension")

        profile = self._user_profiles[user_id]

        # Record interaction
        interaction = {
            "type": interaction_type,
            "story_id": story_id,
            "time_spent": time_spent_seconds,
            "score": score,
            "themes": themes_explored or [],
            "timestamp": datetime.now().isoformat()
        }
        profile.interaction_history.append(interaction)

        # Update profile stats
        profile.total_time_spent += time_spent_seconds
        profile.last_active = datetime.now()

        if interaction_type == "complete":
            profile.stories_completed.add(story_id)

            # Update SM2 data
            if story_id not in profile.sm2_data:
                profile.sm2_data[story_id] = {
                    "easiness": 2.5,
                    "interval": 1,
                    "repetitions": 0,
                    "next_review": datetime.now().isoformat()
                }

            # Update streak
            if profile.interaction_history:
                last_date = datetime.fromisoformat(
                    profile.interaction_history[-2]["timestamp"]
                ).date() if len(profile.interaction_history) > 1 else None
                today = datetime.now().date()

                if last_date == today - timedelta(days=1):
                    profile.current_streak += 1
                elif last_date != today:
                    profile.current_streak = 1

        # Update themes of interest
        if themes_explored:
            profile.themes_of_interest.update(themes_explored)

        # Check milestones
        self._check_milestones(profile)

        return {
            "success": True,
            "user_id": user_id,
            "interaction_recorded": interaction_type,
            "current_streak": profile.current_streak,
            "stories_completed": len(profile.stories_completed),
            "new_milestones": profile.milestones[-3:] if profile.milestones else []
        }

    def _check_milestones(self, profile: UserLearningProfile):
        """Check and award milestones"""
        milestones_to_add = []

        stories_count = len(profile.stories_completed)
        if stories_count >= 1 and "first_story" not in profile.milestones:
            milestones_to_add.append("first_story")
        if stories_count >= 5 and "five_stories" not in profile.milestones:
            milestones_to_add.append("five_stories")
        if stories_count >= 10 and "ten_stories" not in profile.milestones:
            milestones_to_add.append("ten_stories")

        if profile.current_streak >= 7 and "week_streak" not in profile.milestones:
            milestones_to_add.append("week_streak")
        if profile.current_streak >= 30 and "month_streak" not in profile.milestones:
            milestones_to_add.append("month_streak")

        themes_count = len(profile.themes_of_interest)
        if themes_count >= 5 and "theme_explorer" not in profile.milestones:
            milestones_to_add.append("theme_explorer")

        profile.milestones.extend(milestones_to_add)

    def calculate_sm2_review(
        self,
        user_id: str,
        story_id: str,
        quality: int  # 0-5 response quality
    ) -> Dict[str, Any]:
        """
        Calculate SM2 spaced repetition for story review.
        Quality: 0=complete blackout, 5=perfect response
        """
        if user_id not in self._user_profiles:
            return {"error": "User profile not found"}

        profile = self._user_profiles[user_id]

        if story_id not in profile.sm2_data:
            profile.sm2_data[story_id] = {
                "easiness": 2.5,
                "interval": 1,
                "repetitions": 0,
                "next_review": datetime.now().isoformat()
            }

        sm2 = profile.sm2_data[story_id]

        # SM2 Algorithm
        if quality >= 3:
            # Correct response
            if sm2["repetitions"] == 0:
                sm2["interval"] = 1
            elif sm2["repetitions"] == 1:
                sm2["interval"] = 6
            else:
                sm2["interval"] = round(sm2["interval"] * sm2["easiness"])

            sm2["repetitions"] += 1
        else:
            # Incorrect response
            sm2["repetitions"] = 0
            sm2["interval"] = 1

        # Update easiness factor
        sm2["easiness"] = max(1.3, sm2["easiness"] + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=sm2["interval"])
        sm2["next_review"] = next_review.isoformat()

        return {
            "story_id": story_id,
            "quality_rating": quality,
            "new_interval_days": sm2["interval"],
            "next_review": sm2["next_review"],
            "easiness_factor": round(sm2["easiness"], 2),
            "repetitions": sm2["repetitions"]
        }

    def get_personalized_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get personalized story recommendations based on user profile"""
        from app.services.alatlas_service import alatlas_service

        if user_id not in self._user_profiles:
            # Return general recommendations
            return alatlas_service.get_recommendations(limit=limit)

        profile = self._user_profiles[user_id]
        recommendations = []

        # Get all stories
        all_stories = alatlas_service.get_all_stories(limit=100)
        stories = all_stories.get("stories", [])

        for story in stories:
            story_id = story.get("id")

            # Skip completed stories
            if story_id in profile.stories_completed:
                continue

            score = 0.0
            reasons = []

            # Theme match
            story_themes = set(story.get("themes", []))
            theme_overlap = story_themes & profile.themes_of_interest
            if theme_overlap:
                score += len(theme_overlap) * 2
                reasons.append(f"مواضيع تهمك: {', '.join(theme_overlap)}")

            # SM2 due for review
            if story_id in profile.sm2_data:
                next_review = datetime.fromisoformat(profile.sm2_data[story_id]["next_review"])
                if next_review <= datetime.now():
                    score += 5
                    reasons.append("موعد المراجعة")

            # Learning goal alignment
            if profile.learning_goal == LearningGoal.STORY_EXPLORATION:
                score += 1
            elif profile.learning_goal == LearningGoal.THEMATIC_STUDY:
                if theme_overlap:
                    score += 2

            if score > 0:
                recommendations.append({
                    "story_id": story_id,
                    "title_ar": story.get("title_ar"),
                    "title_en": story.get("title_en"),
                    "score": score,
                    "reasons": reasons,
                    "category": story.get("category"),
                    "themes": list(story_themes)
                })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        # Get due reviews
        due_reviews = []
        for story_id, sm2 in profile.sm2_data.items():
            next_review = datetime.fromisoformat(sm2["next_review"])
            if next_review <= datetime.now():
                story = alatlas_service.get_story(story_id)
                if story:
                    due_reviews.append({
                        "story_id": story_id,
                        "title_ar": story.get("title_ar"),
                        "days_overdue": (datetime.now() - next_review).days
                    })

        return {
            "user_id": user_id,
            "learning_goal": profile.learning_goal.value,
            "recommendations": recommendations[:limit],
            "due_reviews": due_reviews[:5],
            "current_streak": profile.current_streak,
            "total_completed": len(profile.stories_completed)
        }

    def get_learning_goal_content(
        self,
        user_id: str,
        goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get content tailored to user's learning goal"""
        from app.services.alatlas_service import alatlas_service

        if user_id in self._user_profiles:
            profile = self._user_profiles[user_id]
            learning_goal = LearningGoal(goal) if goal else profile.learning_goal
        else:
            learning_goal = LearningGoal(goal) if goal else LearningGoal.COMPREHENSION

        content = {
            "goal": learning_goal.value,
            "goal_description_ar": "",
            "goal_description_en": "",
            "recommended_approach": [],
            "suggested_content": []
        }

        if learning_goal == LearningGoal.MEMORIZATION:
            content["goal_description_ar"] = "حفظ القرآن الكريم"
            content["goal_description_en"] = "Memorizing the Holy Quran"
            content["recommended_approach"] = [
                "Start with short verses",
                "Use spaced repetition",
                "Review daily"
            ]
            content["suggested_content"] = ["Short surahs", "Key verses from stories"]

        elif learning_goal == LearningGoal.COMPREHENSION:
            content["goal_description_ar"] = "فهم معاني القرآن"
            content["goal_description_en"] = "Understanding Quranic meanings"
            content["recommended_approach"] = [
                "Study with Tafsir",
                "Explore themes deeply",
                "Connect verses to stories"
            ]

        elif learning_goal == LearningGoal.TAFSIR_STUDY:
            content["goal_description_ar"] = "دراسة التفسير"
            content["goal_description_en"] = "Studying Tafsir"
            content["recommended_approach"] = [
                "Compare four madhab interpretations",
                "Focus on classical scholars",
                "Study verse contexts"
            ]

        elif learning_goal == LearningGoal.STORY_EXPLORATION:
            content["goal_description_ar"] = "استكشاف قصص القرآن"
            content["goal_description_en"] = "Exploring Quranic Stories"
            content["recommended_approach"] = [
                "Follow chronological timeline",
                "Explore prophet connections",
                "Study themes across stories"
            ]
            # Get story recommendations
            stories = alatlas_service.get_all_stories(limit=5)
            content["suggested_content"] = stories.get("stories", [])

        return content

    # ============================================
    # 4. KNOWLEDGE GRAPH EXPANSION
    # ============================================

    def explore_deep_relationships(
        self,
        entity_id: str,
        entity_type: str,  # "prophet", "theme", "place", "event"
        depth: int = 2
    ) -> Dict[str, Any]:
        """Explore deep relationships in the knowledge graph"""
        from app.services.alatlas_service import alatlas_service

        relationships = {
            "entity": {"id": entity_id, "type": entity_type},
            "direct_connections": [],
            "indirect_connections": [],
            "thematic_connections": [],
            "fiqh_connections": []
        }

        if entity_type == "prophet":
            # Get prophet details
            prophet_info = alatlas_service.get_prophet_details(entity_id)
            if "error" not in prophet_info:
                # Direct connections - stories
                relationships["direct_connections"] = prophet_info.get("stories", [])

                # Get related prophets
                relationships["related_entities"] = prophet_info.get("related_prophets", [])

                # Get events
                relationships["events"] = prophet_info.get("events", [])

        elif entity_type == "theme":
            # Get stories with this theme
            stories = alatlas_service.get_all_stories(theme=entity_id, limit=20)
            relationships["direct_connections"] = stories.get("stories", [])

            # Get related themes
            dynamic_themes = alatlas_service.get_dynamic_themes()
            for theme in dynamic_themes.get("themes", []):
                if theme.get("id") == entity_id:
                    relationships["related_entities"] = theme.get("related_themes", [])
                    break

        # Add fiqh connections (simplified)
        fiqh_connections = self._get_fiqh_connections(entity_id, entity_type)
        relationships["fiqh_connections"] = fiqh_connections

        return relationships

    def _get_fiqh_connections(self, entity_id: str, entity_type: str) -> List[Dict]:
        """Get fiqh (jurisprudence) connections for an entity"""
        # Simplified fiqh connections
        fiqh_topics = {
            "patience": ["Ruling on complaining during hardship", "Patience in worship"],
            "sacrifice": ["Rules of Qurbani", "Sacrifice in Hajj"],
            "justice": ["Judicial rulings in Islam", "Fairness in transactions"],
            "musa": ["Laws given to Bani Israel", "Rulings on Sabbath"],
            "ibrahim": ["Hajj rituals", "Sacrifice of Ismail"]
        }

        connections = []
        topics = fiqh_topics.get(entity_id, [])
        for topic in topics:
            connections.append({
                "topic": topic,
                "madhabs": ["hanafi", "maliki", "shafii", "hanbali"],
                "related_to": entity_id
            })

        return connections

    def get_theme_progression(self, theme: str) -> Dict[str, Any]:
        """Track how a theme evolves across stories and verses"""
        from app.services.alatlas_service import alatlas_service

        progression = {
            "theme": theme,
            "theme_ar": self._concepts.get(theme, {}).get("ar", [theme])[0] if theme in self._concepts else theme,
            "stories_chronological": [],
            "key_verses": [],
            "evolution_summary": ""
        }

        # Get stories with this theme
        stories = alatlas_service.get_all_stories(theme=theme, limit=50)

        # Get timeline for chronological order
        timeline = alatlas_service.get_timeline()
        timeline_order = {t["story_id"]: t["order"] for t in timeline.get("timeline", [])}

        theme_stories = []
        for story in stories.get("stories", []):
            story_id = story.get("id")
            order = timeline_order.get(story_id, 999)
            theme_stories.append({
                "story_id": story_id,
                "title_ar": story.get("title_ar"),
                "order": order,
                "themes": story.get("themes", [])
            })

        # Sort by chronological order
        theme_stories.sort(key=lambda x: x["order"])
        progression["stories_chronological"] = theme_stories

        # Generate evolution summary
        if theme_stories:
            first = theme_stories[0]["title_ar"]
            last = theme_stories[-1]["title_ar"]
            progression["evolution_summary"] = f"يظهر موضوع {progression['theme_ar']} من قصة {first} إلى {last}"

        return progression

    # ============================================
    # 5. SCALABILITY & PERFORMANCE
    # ============================================

    def warm_up_cache(self, data_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Preload frequently accessed data into cache"""
        from app.services.alatlas_service import alatlas_service

        if not data_types:
            data_types = ["stories", "themes", "categories", "prophets"]

        warmed = []

        if "stories" in data_types:
            stories = alatlas_service.get_cached_stories(force_refresh=True)
            self._warm_cache["stories"] = stories
            warmed.append("stories")

        if "themes" in data_types:
            themes = alatlas_service.get_dynamic_themes()
            self._warm_cache["themes"] = themes
            warmed.append("themes")

        if "categories" in data_types:
            categories = alatlas_service.get_dynamic_categories()
            self._warm_cache["categories"] = categories
            warmed.append("categories")

        if "prophets" in data_types:
            prophets = alatlas_service.get_prophets()
            self._warm_cache["prophets"] = prophets
            warmed.append("prophets")

        self._warm_cache["warmed_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "warmed_data_types": warmed,
            "cache_size": len(self._warm_cache),
            "warmed_at": self._warm_cache["warmed_at"]
        }

    def get_cached_data(self, data_type: str) -> Dict[str, Any]:
        """Get data from warm cache"""
        if data_type in self._warm_cache:
            self._cache_stats["hits"] += 1
            return {
                "data": self._warm_cache[data_type],
                "from_cache": True,
                "cache_hit": True
            }

        self._cache_stats["misses"] += 1
        return {
            "data": None,
            "from_cache": False,
            "cache_hit": False,
            "message": "Data not in warm cache"
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance and cache statistics"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / max(total_requests, 1)

        return {
            "cache_stats": {
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests
            },
            "warm_cache_size": len(self._warm_cache),
            "warm_cache_keys": list(self._warm_cache.keys()),
            "last_warmed": self._warm_cache.get("warmed_at"),
            "active_users": len(self._user_profiles),
            "pending_verifications": len([t for t in self._verification_tasks.values()
                                         if t.status == VerificationStatus.PENDING])
        }

    # ============================================
    # 6. INTERACTIVE GRAPH EXPLORATION
    # ============================================

    def explore_graph_interactive(
        self,
        start_node: str,
        node_type: str,
        exploration_mode: str = "connected",  # "connected", "thematic", "chronological"
        depth: int = 2,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Interactive graph exploration with click-through navigation"""
        from app.services.alatlas_service import alatlas_service

        explored_nodes = set()
        graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "start_node": start_node,
                "node_type": node_type,
                "exploration_mode": exploration_mode,
                "depth": depth
            }
        }

        def explore_node(node_id: str, current_depth: int, parent_id: Optional[str] = None):
            if current_depth > depth or node_id in explored_nodes:
                return

            explored_nodes.add(node_id)

            if node_type == "story" or (parent_id and current_depth > 0):
                story = alatlas_service.get_story(node_id)
                if story:
                    graph_data["nodes"].append({
                        "id": node_id,
                        "label": story.get("title_ar"),
                        "type": "story",
                        "depth": current_depth,
                        "metadata": {
                            "themes": [t.get("id") for t in story.get("themes", [])],
                            "category": story.get("category")
                        }
                    })

                    if parent_id:
                        graph_data["edges"].append({
                            "source": parent_id,
                            "target": node_id,
                            "type": "related"
                        })

                    # Explore related stories
                    for related in story.get("related_stories", []):
                        related_id = related.get("id") if isinstance(related, dict) else related
                        if related_id not in explored_nodes:
                            explore_node(related_id, current_depth + 1, node_id)

            elif node_type == "theme":
                theme_data = alatlas_service.get_dynamic_themes()
                theme = next((t for t in theme_data.get("themes", []) if t.get("id") == node_id), None)

                if theme:
                    graph_data["nodes"].append({
                        "id": node_id,
                        "label": theme.get("name_ar"),
                        "type": "theme",
                        "depth": current_depth,
                        "metadata": {
                            "story_count": theme.get("story_count", 0)
                        }
                    })

                    # Add stories with this theme
                    for story in theme.get("stories", [])[:5]:
                        story_id = story.get("id")
                        if story_id not in explored_nodes:
                            explored_nodes.add(story_id)
                            graph_data["nodes"].append({
                                "id": story_id,
                                "label": story.get("title_ar"),
                                "type": "story",
                                "depth": current_depth + 1
                            })
                            graph_data["edges"].append({
                                "source": node_id,
                                "target": story_id,
                                "type": "theme_story"
                            })

        explore_node(start_node, 0)

        return graph_data

    def get_thematic_journey(
        self,
        theme: str,
        start_story: Optional[str] = None
    ) -> Dict[str, Any]:
        """Visualize the journey of a theme across prophets and stories"""
        from app.services.alatlas_service import alatlas_service

        journey = {
            "theme": theme,
            "theme_ar": "",
            "path": [],
            "connections": [],
            "insights": []
        }

        # Get theme Arabic name
        themes_data = alatlas_service.get_dynamic_themes()
        for t in themes_data.get("themes", []):
            if t.get("id") == theme:
                journey["theme_ar"] = t.get("name_ar")
                break

        # Get stories with this theme in chronological order
        timeline = alatlas_service.get_timeline()
        stories_with_theme = alatlas_service.get_all_stories(theme=theme, limit=50)

        # Map stories to timeline
        timeline_map = {t["story_id"]: t for t in timeline.get("timeline", [])}

        journey_steps = []
        for story in stories_with_theme.get("stories", []):
            story_id = story.get("id")
            if story_id in timeline_map:
                timeline_info = timeline_map[story_id]
                journey_steps.append({
                    "order": timeline_info.get("order"),
                    "story_id": story_id,
                    "title_ar": story.get("title_ar"),
                    "title_en": story.get("title_en"),
                    "era": timeline_info.get("era"),
                    "category": story.get("category")
                })

        # Sort by chronological order
        journey_steps.sort(key=lambda x: x.get("order", 999))
        journey["path"] = journey_steps

        # Generate connections between consecutive stories
        for i in range(len(journey_steps) - 1):
            current = journey_steps[i]
            next_step = journey_steps[i + 1]
            journey["connections"].append({
                "from": current["story_id"],
                "to": next_step["story_id"],
                "connection_type": "thematic_progression",
                "shared_theme": theme
            })

        # Generate insights
        if journey_steps:
            journey["insights"].append(
                f"موضوع {journey['theme_ar']} يظهر في {len(journey_steps)} قصة"
            )
            if len(journey_steps) >= 2:
                journey["insights"].append(
                    f"يبدأ من {journey_steps[0]['title_ar']} وينتهي في {journey_steps[-1]['title_ar']}"
                )

        return journey

    # ============================================
    # 7. ADAPTIVE LEARNING ALGORITHMS
    # ============================================

    def get_adaptive_recommendations(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get AI-adaptive recommendations that evolve based on user behavior.
        Uses collaborative filtering and content-based filtering.
        """
        from app.services.alatlas_service import alatlas_service

        if user_id not in self._user_profiles:
            self.create_user_profile(user_id, "comprehension")

        profile = self._user_profiles[user_id]
        recommendations = []

        # Get all stories
        all_stories = alatlas_service.get_all_stories(limit=100)
        stories = all_stories.get("stories", [])

        # Calculate personalized scores
        for story in stories:
            story_id = story.get("id")
            if story_id in profile.stories_completed:
                continue

            score = 0.0
            reasons = []

            # Content-based filtering: Theme preference
            story_themes = set(story.get("themes", []))
            theme_overlap = story_themes & profile.themes_of_interest
            if theme_overlap:
                theme_score = len(theme_overlap) * 3
                score += theme_score
                reasons.append(f"يتوافق مع اهتماماتك: {', '.join(theme_overlap)}")

            # Collaborative filtering: Similar user behavior (simplified)
            interaction_count = sum(1 for i in profile.interaction_history
                                   if any(t in story_themes for t in i.get("themes", [])))
            score += interaction_count * 0.5

            # Learning goal alignment
            goal_boost = self._get_goal_alignment_score(profile.learning_goal, story)
            score += goal_boost
            if goal_boost > 0:
                reasons.append("يدعم هدفك التعليمي")

            # Spaced repetition: Due for review
            if story_id in profile.sm2_data:
                next_review = datetime.fromisoformat(profile.sm2_data[story_id]["next_review"])
                if next_review <= datetime.now():
                    score += 5
                    reasons.append("حان موعد المراجعة")

            # Difficulty progression
            difficulty_score = self._calculate_difficulty_progression(profile, story)
            score += difficulty_score

            if score > 0:
                recommendations.append({
                    "story_id": story_id,
                    "title_ar": story.get("title_ar"),
                    "title_en": story.get("title_en"),
                    "adaptive_score": round(score, 2),
                    "reasons": reasons,
                    "themes": list(story_themes),
                    "predicted_engagement": self._predict_engagement(profile, story)
                })

        # Sort by adaptive score
        recommendations.sort(key=lambda x: x["adaptive_score"], reverse=True)

        return {
            "user_id": user_id,
            "learning_goal": profile.learning_goal.value,
            "recommendations": recommendations[:10],
            "adaptation_factors": {
                "theme_preferences": list(profile.themes_of_interest),
                "completed_stories": len(profile.stories_completed),
                "current_streak": profile.current_streak,
                "total_interactions": len(profile.interaction_history)
            }
        }

    def _get_goal_alignment_score(self, goal: LearningGoal, story: Dict) -> float:
        """Calculate how well a story aligns with user's learning goal"""
        alignment_map = {
            LearningGoal.MEMORIZATION: {
                "short_verses": 2.0,
                "repetitive_themes": 1.5
            },
            LearningGoal.COMPREHENSION: {
                "detailed_summary": 2.0,
                "many_themes": 1.5
            },
            LearningGoal.TAFSIR_STUDY: {
                "tafsir_available": 2.0,
                "madhab_coverage": 1.5
            },
            LearningGoal.STORY_EXPLORATION: {
                "many_events": 2.0,
                "connected_stories": 1.5
            }
        }

        score = 0.0
        goal_factors = alignment_map.get(goal, {})

        if "many_events" in goal_factors:
            events = story.get("events", [])
            if len(events) >= 5:
                score += goal_factors["many_events"]

        if "tafsir_available" in goal_factors:
            tafsir = story.get("tafsir_references", [])
            if len(tafsir) >= 2:
                score += goal_factors["tafsir_available"]

        return score

    def _calculate_difficulty_progression(
        self,
        profile: UserLearningProfile,
        story: Dict
    ) -> float:
        """Calculate score based on appropriate difficulty progression"""
        completed_count = len(profile.stories_completed)
        story_complexity = len(story.get("events", [])) + len(story.get("themes", []))

        # Early users get simpler stories
        if completed_count < 3:
            if story_complexity <= 5:
                return 2.0
            return 0.5

        # Intermediate users get medium complexity
        if completed_count < 10:
            if 4 <= story_complexity <= 8:
                return 2.0
            return 0.5

        # Advanced users get complex stories
        if story_complexity >= 7:
            return 2.0
        return 0.5

    def _predict_engagement(
        self,
        profile: UserLearningProfile,
        story: Dict
    ) -> str:
        """Predict user engagement level with a story"""
        story_themes = set(story.get("themes", []))
        theme_overlap = story_themes & profile.themes_of_interest

        # Calculate engagement factors
        theme_match = len(theme_overlap) / max(len(story_themes), 1)
        completion_rate = len(profile.stories_completed) / max(len(profile.interaction_history), 1)

        if theme_match >= 0.5 and completion_rate >= 0.7:
            return "high"
        elif theme_match >= 0.3 or completion_rate >= 0.5:
            return "medium"
        return "low"

    def update_learning_path(
        self,
        user_id: str,
        feedback_type: str,  # "liked", "disliked", "completed", "skipped"
        story_id: str,
        feedback_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update user's learning path based on feedback.
        Adapts future recommendations dynamically.
        """
        if user_id not in self._user_profiles:
            return {"error": "User profile not found"}

        profile = self._user_profiles[user_id]
        from app.services.alatlas_service import alatlas_service

        story = alatlas_service.get_story(story_id)
        if not story:
            return {"error": f"Story '{story_id}' not found"}

        # Extract theme IDs (handle both dict and string formats)
        raw_themes = story.get("themes", [])
        story_themes = set()
        for theme in raw_themes:
            if isinstance(theme, dict):
                story_themes.add(theme.get("id", theme.get("name", str(theme))))
            else:
                story_themes.add(str(theme))

        # Update based on feedback
        if feedback_type == "liked":
            # Increase interest in story's themes
            profile.themes_of_interest.update(story_themes)

        elif feedback_type == "disliked":
            # Decrease interest in story's themes (but don't remove completely)
            pass  # Keep themes but lower their priority in recommendations

        elif feedback_type == "completed":
            profile.stories_completed.add(story_id)
            profile.themes_of_interest.update(story_themes)

        elif feedback_type == "skipped":
            # Note the skip for future recommendations
            pass

        # Record the feedback interaction
        profile.interaction_history.append({
            "type": f"feedback_{feedback_type}",
            "story_id": story_id,
            "timestamp": datetime.now().isoformat(),
            "themes": list(story_themes)
        })

        return {
            "success": True,
            "user_id": user_id,
            "feedback_recorded": feedback_type,
            "updated_interests": list(profile.themes_of_interest),
            "completed_count": len(profile.stories_completed)
        }

    # ============================================
    # 8. AUTO-SCALING & LOAD MANAGEMENT
    # ============================================

    def record_request(self, endpoint: str, response_time_ms: float):
        """Record API request for auto-scaling analysis"""
        self._request_history.append({
            "endpoint": endpoint,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 1000 requests
        if len(self._request_history) > 1000:
            self._request_history = self._request_history[-1000:]

    def evaluate_scaling_need(self) -> Dict[str, Any]:
        """
        Evaluate if auto-scaling is needed based on load patterns.
        Returns scaling recommendation.
        """
        if len(self._request_history) < 10:
            return {
                "scaling_needed": False,
                "reason": "Insufficient data for evaluation",
                "current_instances": self._auto_scale_config["current_instances"]
            }

        # Calculate metrics from recent requests (last 5 minutes)
        recent_cutoff = datetime.now() - timedelta(minutes=5)
        recent_requests = [
            r for r in self._request_history
            if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
        ]

        if not recent_requests:
            return {
                "scaling_needed": False,
                "reason": "No recent requests",
                "current_instances": self._auto_scale_config["current_instances"]
            }

        # Calculate average response time
        avg_response_time = sum(r["response_time_ms"] for r in recent_requests) / len(recent_requests)
        request_rate = len(recent_requests) / 5  # requests per minute

        # Simulated CPU usage based on response time
        estimated_cpu = min(avg_response_time / 100, 1.0)  # Normalize to 0-1

        current_instances = self._auto_scale_config["current_instances"]
        scaling_action = None

        if estimated_cpu > self._auto_scale_config["scale_up_threshold"]:
            if current_instances < self._auto_scale_config["max_instances"]:
                scaling_action = "scale_up"
        elif estimated_cpu < self._auto_scale_config["scale_down_threshold"]:
            if current_instances > self._auto_scale_config["min_instances"]:
                scaling_action = "scale_down"

        return {
            "scaling_needed": scaling_action is not None,
            "scaling_action": scaling_action,
            "metrics": {
                "avg_response_time_ms": round(avg_response_time, 2),
                "request_rate_per_min": round(request_rate, 2),
                "estimated_cpu_usage": round(estimated_cpu, 2),
                "recent_request_count": len(recent_requests)
            },
            "current_instances": current_instances,
            "config": self._auto_scale_config
        }

    def apply_scaling(self, admin_id: str, action: str) -> Dict[str, Any]:
        """Apply scaling action (requires admin)"""
        if admin_id not in self._admin_users:
            return {"error": "Unauthorized - Admin access required"}

        if action == "scale_up":
            if self._auto_scale_config["current_instances"] < self._auto_scale_config["max_instances"]:
                self._auto_scale_config["current_instances"] += 1
                return {
                    "success": True,
                    "action": "scaled_up",
                    "new_instance_count": self._auto_scale_config["current_instances"]
                }
            return {"success": False, "reason": "Already at max instances"}

        elif action == "scale_down":
            if self._auto_scale_config["current_instances"] > self._auto_scale_config["min_instances"]:
                self._auto_scale_config["current_instances"] -= 1
                return {
                    "success": True,
                    "action": "scaled_down",
                    "new_instance_count": self._auto_scale_config["current_instances"]
                }
            return {"success": False, "reason": "Already at min instances"}

        return {"error": f"Unknown action: {action}"}

    def get_cache_optimization_report(self) -> Dict[str, Any]:
        """Get cache optimization recommendations"""
        hit_rate = self._cache_stats["hits"] / max(
            self._cache_stats["hits"] + self._cache_stats["misses"], 1
        )

        recommendations = []

        if hit_rate < 0.5:
            recommendations.append({
                "issue": "Low cache hit rate",
                "suggestion": "Consider warming up frequently accessed data",
                "priority": "high"
            })

        if len(self._warm_cache) < 3:
            recommendations.append({
                "issue": "Insufficient cache warming",
                "suggestion": "Warm up stories, themes, and categories",
                "priority": "medium"
            })

        return {
            "current_hit_rate": round(hit_rate, 2),
            "cache_size": len(self._warm_cache),
            "recommendations": recommendations,
            "optimal_hit_rate_target": 0.8
        }

    # ============================================
    # 9. INTERACTIVE ZOOM & REAL-TIME EXPLORATION
    # ============================================

    def create_graph_session(self, user_id: str) -> Dict[str, Any]:
        """Create an interactive graph exploration session"""
        session_id = f"gs_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self._graph_sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "current_view": {
                "center_node": None,
                "zoom_level": 1.0,
                "visible_nodes": [],
                "filters": {}
            },
            "history": [],
            "bookmarks": []
        }

        return {
            "session_id": session_id,
            "user_id": user_id,
            "created": True
        }

    def graph_zoom(
        self,
        session_id: str,
        zoom_level: float,  # 0.1 to 10.0
        center_node: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Zoom in/out on graph visualization.
        Higher zoom = more detail, fewer nodes visible.
        Lower zoom = overview, more nodes visible.
        """
        if session_id not in self._graph_sessions:
            return {"error": f"Session '{session_id}' not found"}

        session = self._graph_sessions[session_id]

        # Clamp zoom level
        zoom_level = max(0.1, min(10.0, zoom_level))
        session["current_view"]["zoom_level"] = zoom_level

        if center_node:
            session["current_view"]["center_node"] = center_node

        # Calculate visible node count based on zoom
        # Higher zoom = fewer nodes (more detail)
        # Lower zoom = more nodes (overview)
        max_nodes = int(50 / zoom_level)

        return {
            "session_id": session_id,
            "zoom_level": zoom_level,
            "center_node": center_node,
            "max_visible_nodes": max_nodes,
            "view_type": "detail" if zoom_level >= 2.0 else "overview" if zoom_level <= 0.5 else "normal"
        }

    def graph_explore_node(
        self,
        session_id: str,
        node_id: str,
        node_type: str,
        expand: bool = True
    ) -> Dict[str, Any]:
        """
        Real-time node exploration in interactive graph.
        Click on a node to expand or collapse its connections.
        """
        from app.services.alatlas_service import alatlas_service

        if session_id not in self._graph_sessions:
            return {"error": f"Session '{session_id}' not found"}

        session = self._graph_sessions[session_id]

        # Record in history
        session["history"].append({
            "action": "explore_node",
            "node_id": node_id,
            "timestamp": datetime.now().isoformat()
        })

        # Update center node
        session["current_view"]["center_node"] = node_id

        # Get node details and connections
        node_data = {
            "id": node_id,
            "type": node_type,
            "connections": [],
            "metadata": {}
        }

        if node_type == "story":
            story = alatlas_service.get_story(node_id)
            if story:
                node_data["label"] = story.get("title_ar")
                node_data["metadata"] = {
                    "title_en": story.get("title_en"),
                    "category": story.get("category"),
                    "themes": story.get("themes", []),
                    "completeness": story.get("completeness_score", 0)
                }

                if expand:
                    # Add connected stories
                    for related in story.get("related_stories", [])[:10]:
                        rel_id = related.get("id") if isinstance(related, dict) else related
                        node_data["connections"].append({
                            "id": rel_id,
                            "type": "related_story",
                            "relationship": "thematic"
                        })

                    # Add themes as connections
                    for theme in story.get("themes", [])[:5]:
                        node_data["connections"].append({
                            "id": theme if isinstance(theme, str) else theme.get("id"),
                            "type": "theme",
                            "relationship": "has_theme"
                        })

        elif node_type == "theme":
            # Get theme details
            themes_data = alatlas_service.get_dynamic_themes()
            theme = next((t for t in themes_data.get("themes", [])
                         if t.get("id") == node_id), None)

            if theme:
                node_data["label"] = theme.get("name_ar")
                node_data["metadata"] = {
                    "name_en": theme.get("name_en"),
                    "story_count": theme.get("story_count", 0)
                }

                if expand:
                    # Add stories with this theme
                    stories = alatlas_service.get_all_stories(theme=node_id, limit=10)
                    for story in stories.get("stories", []):
                        node_data["connections"].append({
                            "id": story.get("id"),
                            "type": "story",
                            "relationship": "theme_story"
                        })

        elif node_type == "prophet":
            # Get prophet details
            prophet_info = alatlas_service.get_prophet_details(node_id)
            if "error" not in prophet_info:
                node_data["label"] = prophet_info.get("prophet", {}).get("name_ar")
                node_data["metadata"] = prophet_info.get("prophet", {})

                if expand:
                    # Add prophet's stories
                    for story in prophet_info.get("stories", [])[:10]:
                        node_data["connections"].append({
                            "id": story.get("id"),
                            "type": "story",
                            "relationship": "prophet_story"
                        })

        return {
            "session_id": session_id,
            "node": node_data,
            "expanded": expand,
            "connection_count": len(node_data["connections"])
        }

    def graph_filter(
        self,
        session_id: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply filters to graph visualization.
        Filters: themes, categories, prophets, time_period, etc.
        """
        if session_id not in self._graph_sessions:
            return {"error": f"Session '{session_id}' not found"}

        session = self._graph_sessions[session_id]
        session["current_view"]["filters"] = filters

        return {
            "session_id": session_id,
            "filters_applied": filters,
            "message": "Filters applied to graph view"
        }

    def graph_bookmark_node(
        self,
        session_id: str,
        node_id: str,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bookmark a node for later reference"""
        if session_id not in self._graph_sessions:
            return {"error": f"Session '{session_id}' not found"}

        session = self._graph_sessions[session_id]

        bookmark = {
            "node_id": node_id,
            "note": note,
            "timestamp": datetime.now().isoformat()
        }

        session["bookmarks"].append(bookmark)

        return {
            "success": True,
            "bookmark_added": bookmark,
            "total_bookmarks": len(session["bookmarks"])
        }

    def get_visualization_data(
        self,
        center_node: str,
        node_type: str,
        depth: int = 2,
        max_nodes: int = 50,
        layout: str = "force"  # "force", "hierarchical", "circular"
    ) -> Dict[str, Any]:
        """
        Get visualization-ready graph data for frontend rendering.
        Includes node positions, colors, and edge weights.
        """
        from app.services.alatlas_service import alatlas_service

        # Get graph data
        graph = self.explore_graph_interactive(center_node, node_type, depth=depth)
        nodes = graph.get("nodes", [])[:max_nodes]
        edges = graph.get("edges", [])

        # Add visualization properties
        visualization_nodes = []
        for i, node in enumerate(nodes):
            # Calculate position based on layout
            if layout == "force":
                # Simplified force-directed position
                angle = (2 * 3.14159 * i) / len(nodes)
                radius = 100 + (node.get("depth", 0) * 50)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
            elif layout == "hierarchical":
                x = node.get("depth", 0) * 150
                y = (i % 5) * 100
            else:  # circular
                angle = (2 * 3.14159 * i) / len(nodes)
                x = 200 * math.cos(angle)
                y = 200 * math.sin(angle)

            # Assign colors based on type
            color_map = {
                "story": "#4CAF50",
                "theme": "#2196F3",
                "prophet": "#FFC107",
                "event": "#9C27B0"
            }

            visualization_nodes.append({
                **node,
                "x": round(x, 2),
                "y": round(y, 2),
                "color": color_map.get(node.get("type"), "#757575"),
                "size": 30 if node.get("id") == center_node else 20
            })

        return {
            "nodes": visualization_nodes,
            "edges": edges,
            "layout": layout,
            "center": {"x": 0, "y": 0},
            "bounds": {
                "min_x": min(n["x"] for n in visualization_nodes) if visualization_nodes else 0,
                "max_x": max(n["x"] for n in visualization_nodes) if visualization_nodes else 0,
                "min_y": min(n["y"] for n in visualization_nodes) if visualization_nodes else 0,
                "max_y": max(n["y"] for n in visualization_nodes) if visualization_nodes else 0
            },
            "legend": [
                {"type": "story", "color": "#4CAF50", "label_ar": "قصة"},
                {"type": "theme", "color": "#2196F3", "label_ar": "موضوع"},
                {"type": "prophet", "color": "#FFC107", "label_ar": "نبي"},
                {"type": "event", "color": "#9C27B0", "label_ar": "حدث"}
            ]
        }

    # ============================================
    # 10. TEMPORAL & CAUSAL GRAPH METHODS
    # ============================================

    def get_temporal_relationships(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get temporal relationships for an entity.
        Shows what came before and after in the Quranic narrative.
        """
        if entity_id not in self._temporal_order:
            return {"error": f"Entity '{entity_id}' not found in temporal graph"}

        entity_order = self._temporal_order[entity_id]["order"]
        entity_era = self._temporal_order[entity_id]["era"]

        # Find predecessors and successors
        predecessors = []
        successors = []
        contemporaries = []

        for other_id, data in self._temporal_order.items():
            if other_id == entity_id:
                continue

            if data["order"] < entity_order:
                predecessors.append({
                    "id": other_id,
                    "order": data["order"],
                    "era": data["era"],
                    "relationship": "before"
                })
            elif data["order"] > entity_order:
                successors.append({
                    "id": other_id,
                    "order": data["order"],
                    "era": data["era"],
                    "relationship": "after"
                })

            if data["era"] == entity_era and other_id != entity_id:
                contemporaries.append({
                    "id": other_id,
                    "order": data["order"],
                    "relationship": "contemporary"
                })

        # Sort by order
        predecessors.sort(key=lambda x: x["order"], reverse=True)
        successors.sort(key=lambda x: x["order"])

        return {
            "entity_id": entity_id,
            "order": entity_order,
            "era": entity_era,
            "predecessors": predecessors[:5],  # Last 5 before
            "successors": successors[:5],      # Next 5 after
            "contemporaries": contemporaries,
            "timeline_position": f"{entity_order}/{len(self._temporal_order)}"
        }

    def get_causal_chain(
        self,
        event_id: str,
        direction: str = "both"  # "causes", "effects", "both"
    ) -> Dict[str, Any]:
        """
        Get cause-effect chain for an event.
        Shows what caused this event and what effects it had.
        """
        if event_id not in self._causal_chains:
            return {"error": f"Event '{event_id}' not found in causal graph"}

        chain_data = self._causal_chains[event_id]

        result = {
            "event_id": event_id,
            "event_description": chain_data["event"],
            "lessons": chain_data.get("lessons", [])
        }

        if direction in ["causes", "both"]:
            result["causes"] = chain_data.get("causes", [])

        if direction in ["effects", "both"]:
            result["effects"] = chain_data.get("effects", [])

        return result

    def get_relationship_path(
        self,
        from_entity: str,
        to_entity: str,
        max_hops: int = 5
    ) -> Dict[str, Any]:
        """
        Find relationship path between two entities in the knowledge graph.
        Uses BFS to find shortest path.
        """
        if from_entity not in self._temporal_order and to_entity not in self._temporal_order:
            return {"error": "Entities not found in graph"}

        # BFS to find path
        queue = [(from_entity, [from_entity])]
        visited = {from_entity}

        while queue:
            current, path = queue.pop(0)

            if current == to_entity:
                return {
                    "found": True,
                    "from": from_entity,
                    "to": to_entity,
                    "path": path,
                    "hop_count": len(path) - 1,
                    "relationship_types": self._get_path_relationships(path)
                }

            if len(path) >= max_hops:
                continue

            # Get neighbors from temporal order
            current_order = self._temporal_order.get(current, {}).get("order", 0)
            for entity, data in self._temporal_order.items():
                if entity not in visited:
                    # Connect to adjacent entities in timeline
                    if abs(data["order"] - current_order) <= 2:
                        visited.add(entity)
                        queue.append((entity, path + [entity]))

        return {
            "found": False,
            "from": from_entity,
            "to": to_entity,
            "path": [],
            "message": f"No path found within {max_hops} hops"
        }

    def _get_path_relationships(self, path: List[str]) -> List[Dict[str, str]]:
        """Get relationship types between consecutive path nodes"""
        relationships = []
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]

            from_data = self._temporal_order.get(from_node, {})
            to_data = self._temporal_order.get(to_node, {})

            if from_data.get("era") == to_data.get("era"):
                rel_type = "contemporary"
            elif from_data.get("order", 0) < to_data.get("order", 0):
                rel_type = "preceded"
            else:
                rel_type = "followed"

            relationships.append({
                "from": from_node,
                "to": to_node,
                "relationship": rel_type
            })

        return relationships

    def explore_journey(
        self,
        start_entity: str,
        journey_type: str = "chronological"  # "chronological", "thematic", "causal"
    ) -> Dict[str, Any]:
        """
        Create an exploration journey through the knowledge graph.
        """
        from app.services.alatlas_service import alatlas_service

        journey = {
            "start": start_entity,
            "type": journey_type,
            "steps": [],
            "total_entities": 0
        }

        if journey_type == "chronological":
            # Follow temporal order
            if start_entity in self._temporal_order:
                start_order = self._temporal_order[start_entity]["order"]

                for entity, data in sorted(
                    self._temporal_order.items(),
                    key=lambda x: x[1]["order"]
                ):
                    if data["order"] >= start_order:
                        journey["steps"].append({
                            "entity": entity,
                            "order": data["order"],
                            "era": data["era"]
                        })
                        if len(journey["steps"]) >= 10:
                            break

        elif journey_type == "thematic":
            # Follow theme connections
            story = alatlas_service.get_story(start_entity)
            if story:
                themes = story.get("themes", [])
                journey["steps"].append({
                    "entity": start_entity,
                    "title": story.get("title_ar"),
                    "themes": themes
                })

                # Find stories with overlapping themes
                for theme in themes[:2]:
                    theme_id = theme if isinstance(theme, str) else theme.get("id")
                    related = alatlas_service.get_all_stories(theme=theme_id, limit=3)
                    for s in related.get("stories", []):
                        if s.get("id") != start_entity:
                            journey["steps"].append({
                                "entity": s.get("id"),
                                "title": s.get("title_ar"),
                                "connection": f"Shares theme: {theme_id}"
                            })

        elif journey_type == "causal":
            # Follow causal chains
            for event_id, data in self._causal_chains.items():
                if start_entity in event_id or start_entity in str(data):
                    journey["steps"].append({
                        "event": event_id,
                        "description": data["event"],
                        "effects": data.get("effects", [])[:3],
                        "lessons": data.get("lessons", [])
                    })

        journey["total_entities"] = len(journey["steps"])
        return journey


# Create singleton instance
advanced_atlas_service = AdvancedAtlasService()
