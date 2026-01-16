"""
Adaptive Quiz System with Difficulty Adjustment.

Provides personalized quizzes that adapt to user's knowledge level
across Fiqh, Hadith, Tafsir, and Quranic themes.

Features:
1. Multi-category question bank
2. Adaptive difficulty adjustment
3. Spaced repetition for weak areas
4. Performance analytics
5. Achievement tracking

Arabic: نظام الاختبارات التكيفية مع ضبط الصعوبة
"""

import logging
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class QuestionCategory(str, Enum):
    """Categories of questions."""
    QURAN_KNOWLEDGE = "quran_knowledge"
    PROPHET_STORIES = "prophet_stories"
    TAFSIR = "tafsir"
    FIQH = "fiqh"
    HADITH = "hadith"
    ARABIC_LINGUISTICS = "arabic_linguistics"
    ISLAMIC_HISTORY = "islamic_history"


class DifficultyLevel(str, Enum):
    """Difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestionType(str, Enum):
    """Types of questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"


@dataclass
class Question:
    """A quiz question."""
    question_id: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    question_type: QuestionType
    question_ar: str
    question_en: str
    options: List[Dict[str, str]]  # [{ar, en, is_correct}]
    correct_answer_index: int
    explanation_ar: str
    explanation_en: str
    related_verses: List[str]
    tags: List[str]


@dataclass
class QuizSession:
    """A quiz session."""
    session_id: str
    user_id: str
    category: Optional[QuestionCategory]
    difficulty: DifficultyLevel
    questions: List[Question]
    current_index: int
    answers: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    score: int
    total_questions: int


@dataclass
class UserQuizProfile:
    """User's quiz performance profile."""
    user_id: str
    category_scores: Dict[str, Dict[str, float]]  # category -> {correct, total, avg_time}
    difficulty_level: DifficultyLevel
    weak_areas: List[str]
    strong_areas: List[str]
    total_quizzes: int
    total_correct: int
    total_questions: int
    current_streak: int
    best_streak: int
    achievements: List[str]


# =============================================================================
# QUESTION BANK
# =============================================================================

QUESTION_BANK = [
    # Quran Knowledge - Easy
    {
        "question_id": "qk_001",
        "category": QuestionCategory.QURAN_KNOWLEDGE,
        "difficulty": DifficultyLevel.EASY,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "كم عدد سور القرآن الكريم؟",
        "question_en": "How many suras are in the Quran?",
        "options": [
            {"ar": "114 سورة", "en": "114 suras", "is_correct": True},
            {"ar": "100 سورة", "en": "100 suras", "is_correct": False},
            {"ar": "120 سورة", "en": "120 suras", "is_correct": False},
            {"ar": "99 سورة", "en": "99 suras", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "يتكون القرآن الكريم من 114 سورة",
        "explanation_en": "The Quran consists of 114 suras",
        "related_verses": [],
        "tags": ["basic", "quran_structure"],
    },
    {
        "question_id": "qk_002",
        "category": QuestionCategory.QURAN_KNOWLEDGE,
        "difficulty": DifficultyLevel.EASY,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "ما هي أطول سورة في القرآن الكريم؟",
        "question_en": "What is the longest sura in the Quran?",
        "options": [
            {"ar": "سورة البقرة", "en": "Sura Al-Baqarah", "is_correct": True},
            {"ar": "سورة آل عمران", "en": "Sura Aal-Imran", "is_correct": False},
            {"ar": "سورة النساء", "en": "Sura An-Nisa", "is_correct": False},
            {"ar": "سورة الكهف", "en": "Sura Al-Kahf", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "سورة البقرة هي أطول سورة وتحتوي على 286 آية",
        "explanation_en": "Sura Al-Baqarah is the longest with 286 verses",
        "related_verses": ["2:1"],
        "tags": ["basic", "quran_structure", "surah_baqarah"],
    },
    # Prophet Stories - Easy
    {
        "question_id": "ps_001",
        "category": QuestionCategory.PROPHET_STORIES,
        "difficulty": DifficultyLevel.EASY,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "أي نبي بنى الكعبة مع ابنه إسماعيل؟",
        "question_en": "Which prophet built the Kaaba with his son Ismail?",
        "options": [
            {"ar": "إبراهيم عليه السلام", "en": "Ibrahim (Abraham)", "is_correct": True},
            {"ar": "موسى عليه السلام", "en": "Musa (Moses)", "is_correct": False},
            {"ar": "نوح عليه السلام", "en": "Nuh (Noah)", "is_correct": False},
            {"ar": "آدم عليه السلام", "en": "Adam", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "بنى إبراهيم وإسماعيل عليهما السلام الكعبة كما ورد في القرآن",
        "explanation_en": "Ibrahim and Ismail built the Kaaba as mentioned in the Quran",
        "related_verses": ["2:125-127"],
        "tags": ["prophets", "ibrahim", "kaaba"],
    },
    {
        "question_id": "ps_002",
        "category": QuestionCategory.PROPHET_STORIES,
        "difficulty": DifficultyLevel.EASY,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "أي نبي ألقي في النار ونجاه الله منها؟",
        "question_en": "Which prophet was thrown into fire and saved by Allah?",
        "options": [
            {"ar": "إبراهيم عليه السلام", "en": "Ibrahim (Abraham)", "is_correct": True},
            {"ar": "يوسف عليه السلام", "en": "Yusuf (Joseph)", "is_correct": False},
            {"ar": "موسى عليه السلام", "en": "Musa (Moses)", "is_correct": False},
            {"ar": "عيسى عليه السلام", "en": "Isa (Jesus)", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "قال الله للنار كوني برداً وسلاماً على إبراهيم",
        "explanation_en": "Allah commanded the fire to be cool and peaceful for Ibrahim",
        "related_verses": ["21:68-69"],
        "tags": ["prophets", "ibrahim", "miracles"],
    },
    # Prophet Stories - Medium
    {
        "question_id": "ps_003",
        "category": QuestionCategory.PROPHET_STORIES,
        "difficulty": DifficultyLevel.MEDIUM,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "كم لبث يوسف عليه السلام في السجن؟",
        "question_en": "How long did Yusuf stay in prison?",
        "options": [
            {"ar": "بضع سنين (حوالي 7-9)", "en": "Several years (about 7-9)", "is_correct": True},
            {"ar": "سنة واحدة", "en": "One year", "is_correct": False},
            {"ar": "عشرون سنة", "en": "Twenty years", "is_correct": False},
            {"ar": "أربعون سنة", "en": "Forty years", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "قال تعالى: فلبث في السجن بضع سنين، والبضع من 3 إلى 9",
        "explanation_en": "The Quran says 'bid' sineen' meaning several years, typically 3-9",
        "related_verses": ["12:42"],
        "tags": ["prophets", "yusuf", "patience"],
    },
    # Tafsir - Medium
    {
        "question_id": "tf_001",
        "category": QuestionCategory.TAFSIR,
        "difficulty": DifficultyLevel.MEDIUM,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "ما المقصود بـ 'الصراط المستقيم' في سورة الفاتحة؟",
        "question_en": "What does 'Sirat al-Mustaqeem' mean in Sura Al-Fatiha?",
        "options": [
            {"ar": "الإسلام وطريق الهداية", "en": "Islam and the path of guidance", "is_correct": True},
            {"ar": "الطريق المادي", "en": "A physical road", "is_correct": False},
            {"ar": "طريق مكة", "en": "The road to Mecca", "is_correct": False},
            {"ar": "الجسر يوم القيامة", "en": "The bridge on Day of Judgment", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "الصراط المستقيم هو دين الإسلام والطريق الموصل إلى مرضاة الله",
        "explanation_en": "The Straight Path refers to Islam and the way leading to Allah's pleasure",
        "related_verses": ["1:6-7"],
        "tags": ["tafsir", "fatiha", "guidance"],
    },
    # Fiqh - Easy
    {
        "question_id": "fq_001",
        "category": QuestionCategory.FIQH,
        "difficulty": DifficultyLevel.EASY,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "كم عدد أركان الإسلام؟",
        "question_en": "How many pillars of Islam are there?",
        "options": [
            {"ar": "خمسة أركان", "en": "Five pillars", "is_correct": True},
            {"ar": "ستة أركان", "en": "Six pillars", "is_correct": False},
            {"ar": "سبعة أركان", "en": "Seven pillars", "is_correct": False},
            {"ar": "أربعة أركان", "en": "Four pillars", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "الشهادتان، الصلاة، الزكاة، الصوم، والحج",
        "explanation_en": "Shahada, Prayer, Zakat, Fasting, and Hajj",
        "related_verses": [],
        "tags": ["fiqh", "pillars", "basic"],
    },
    # Hadith - Medium
    {
        "question_id": "hd_001",
        "category": QuestionCategory.HADITH,
        "difficulty": DifficultyLevel.MEDIUM,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "ما هو أول حديث في صحيح البخاري؟",
        "question_en": "What is the first hadith in Sahih Bukhari?",
        "options": [
            {"ar": "إنما الأعمال بالنيات", "en": "Actions are by intentions", "is_correct": True},
            {"ar": "المسلم من سلم المسلمون", "en": "A Muslim is one from whose...", "is_correct": False},
            {"ar": "لا يؤمن أحدكم حتى يحب", "en": "None of you believes until...", "is_correct": False},
            {"ar": "الدين النصيحة", "en": "The religion is sincere advice", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "حديث النية هو أول حديث في صحيح البخاري لأهميته",
        "explanation_en": "The hadith of intention is first due to its foundational importance",
        "related_verses": [],
        "tags": ["hadith", "bukhari", "niyyah"],
    },
    # Hard Questions
    {
        "question_id": "tf_002",
        "category": QuestionCategory.TAFSIR,
        "difficulty": DifficultyLevel.HARD,
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "question_ar": "ما هي الحروف المقطعة وما أشهر الأقوال فيها؟",
        "question_en": "What are the disjointed letters and the most common views about them?",
        "options": [
            {"ar": "حروف في بداية بعض السور، والله أعلم بمعناها", "en": "Letters at the start of some suras, their meaning known only to Allah", "is_correct": True},
            {"ar": "اختصارات لأسماء الصحابة", "en": "Abbreviations for companions' names", "is_correct": False},
            {"ar": "رموز رياضية", "en": "Mathematical codes", "is_correct": False},
            {"ar": "أخطاء نسخية", "en": "Scribal errors", "is_correct": False},
        ],
        "correct_answer_index": 0,
        "explanation_ar": "الحروف المقطعة مثل ألم، حم، يس من المتشابه الذي استأثر الله بعلمه",
        "explanation_en": "Disjointed letters like Alif-Lam-Mim are among the unclear matters known only to Allah",
        "related_verses": ["2:1", "3:1"],
        "tags": ["tafsir", "huruf_muqattaaat", "advanced"],
    },
]


# =============================================================================
# QUIZ SERVICE
# =============================================================================

class QuizService:
    """
    Adaptive Quiz System with difficulty adjustment.

    Features:
    - Personalized quiz generation
    - Adaptive difficulty
    - Performance tracking
    - Spaced repetition for weak areas
    - Achievements and gamification
    """

    def __init__(self):
        self._questions = {q["question_id"]: self._dict_to_question(q) for q in QUESTION_BANK}
        self._sessions: Dict[str, QuizSession] = {}
        self._user_profiles: Dict[str, UserQuizProfile] = {}
        self._question_history: Dict[str, List[Dict]] = defaultdict(list)  # user_id -> [attempts]

    def _dict_to_question(self, data: Dict) -> Question:
        """Convert dict to Question object."""
        return Question(
            question_id=data["question_id"],
            category=data["category"],
            difficulty=data["difficulty"],
            question_type=data["question_type"],
            question_ar=data["question_ar"],
            question_en=data["question_en"],
            options=data["options"],
            correct_answer_index=data["correct_answer_index"],
            explanation_ar=data["explanation_ar"],
            explanation_en=data["explanation_en"],
            related_verses=data.get("related_verses", []),
            tags=data.get("tags", []),
        )

    def _get_or_create_profile(self, user_id: str) -> UserQuizProfile:
        """Get or create user quiz profile."""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserQuizProfile(
                user_id=user_id,
                category_scores={},
                difficulty_level=DifficultyLevel.EASY,
                weak_areas=[],
                strong_areas=[],
                total_quizzes=0,
                total_correct=0,
                total_questions=0,
                current_streak=0,
                best_streak=0,
                achievements=[],
            )
        return self._user_profiles[user_id]

    def start_quiz(
        self,
        user_id: str,
        category: Optional[str] = None,
        num_questions: int = 5,
        difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a new quiz session."""
        profile = self._get_or_create_profile(user_id)

        # Determine difficulty
        if difficulty:
            try:
                quiz_difficulty = DifficultyLevel(difficulty)
            except ValueError:
                quiz_difficulty = profile.difficulty_level
        else:
            quiz_difficulty = profile.difficulty_level

        # Filter questions
        available_questions = list(self._questions.values())

        if category:
            try:
                cat = QuestionCategory(category)
                available_questions = [q for q in available_questions if q.category == cat]
            except ValueError:
                pass

        # Filter by difficulty (allow one level above and below)
        difficulty_order = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD, DifficultyLevel.EXPERT]
        target_idx = difficulty_order.index(quiz_difficulty)
        allowed_difficulties = set()
        if target_idx > 0:
            allowed_difficulties.add(difficulty_order[target_idx - 1])
        allowed_difficulties.add(quiz_difficulty)
        if target_idx < len(difficulty_order) - 1:
            allowed_difficulties.add(difficulty_order[target_idx + 1])

        available_questions = [q for q in available_questions if q.difficulty in allowed_difficulties]

        if not available_questions:
            return {"error": "No questions available for this criteria"}

        # Select questions
        num_questions = min(num_questions, len(available_questions))
        selected = random.sample(available_questions, num_questions)

        # Create session
        session_id = hashlib.md5(f"{user_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        session = QuizSession(
            session_id=session_id,
            user_id=user_id,
            category=QuestionCategory(category) if category else None,
            difficulty=quiz_difficulty,
            questions=selected,
            current_index=0,
            answers=[],
            started_at=datetime.now(),
            completed_at=None,
            score=0,
            total_questions=len(selected),
        )

        self._sessions[session_id] = session

        # Return first question
        first_q = selected[0]
        return {
            "session_id": session_id,
            "quiz_started": True,
            "total_questions": len(selected),
            "current_question": 1,
            "difficulty": quiz_difficulty.value,
            "question": {
                "question_id": first_q.question_id,
                "category": first_q.category.value,
                "question_ar": first_q.question_ar,
                "question_en": first_q.question_en,
                "options": [{"ar": o["ar"], "en": o["en"]} for o in first_q.options],
                "question_type": first_q.question_type.value,
            },
        }

    def submit_answer(
        self,
        session_id: str,
        answer_index: int,
        time_taken_seconds: int = 0,
    ) -> Dict[str, Any]:
        """Submit answer for current question."""
        if session_id not in self._sessions:
            return {"error": "Session not found"}

        session = self._sessions[session_id]

        if session.completed_at:
            return {"error": "Quiz already completed"}

        current_q = session.questions[session.current_index]
        is_correct = answer_index == current_q.correct_answer_index

        # Record answer
        session.answers.append({
            "question_id": current_q.question_id,
            "answer_index": answer_index,
            "correct_answer_index": current_q.correct_answer_index,
            "is_correct": is_correct,
            "time_taken_seconds": time_taken_seconds,
        })

        if is_correct:
            session.score += 1

        # Record for user history
        self._question_history[session.user_id].append({
            "question_id": current_q.question_id,
            "category": current_q.category.value,
            "difficulty": current_q.difficulty.value,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat(),
        })

        # Check if quiz is complete
        if session.current_index >= len(session.questions) - 1:
            session.completed_at = datetime.now()
            self._update_user_profile(session)

            return {
                "session_id": session_id,
                "answer_result": {
                    "is_correct": is_correct,
                    "correct_answer_index": current_q.correct_answer_index,
                    "explanation_ar": current_q.explanation_ar,
                    "explanation_en": current_q.explanation_en,
                    "related_verses": current_q.related_verses,
                },
                "quiz_completed": True,
                "final_score": session.score,
                "total_questions": session.total_questions,
                "percentage": round(session.score / session.total_questions * 100, 1),
            }
        else:
            # Move to next question
            session.current_index += 1
            next_q = session.questions[session.current_index]

            return {
                "session_id": session_id,
                "answer_result": {
                    "is_correct": is_correct,
                    "correct_answer_index": current_q.correct_answer_index,
                    "explanation_ar": current_q.explanation_ar,
                    "explanation_en": current_q.explanation_en,
                    "related_verses": current_q.related_verses,
                },
                "quiz_completed": False,
                "current_score": session.score,
                "next_question": {
                    "question_number": session.current_index + 1,
                    "question_id": next_q.question_id,
                    "category": next_q.category.value,
                    "question_ar": next_q.question_ar,
                    "question_en": next_q.question_en,
                    "options": [{"ar": o["ar"], "en": o["en"]} for o in next_q.options],
                    "question_type": next_q.question_type.value,
                },
            }

    def _update_user_profile(self, session: QuizSession) -> None:
        """Update user profile after quiz completion."""
        profile = self._get_or_create_profile(session.user_id)

        # Update totals
        profile.total_quizzes += 1
        profile.total_correct += session.score
        profile.total_questions += session.total_questions

        # Update category scores
        for answer in session.answers:
            q = self._questions.get(answer["question_id"])
            if q:
                cat = q.category.value
                if cat not in profile.category_scores:
                    profile.category_scores[cat] = {"correct": 0, "total": 0}
                profile.category_scores[cat]["total"] += 1
                if answer["is_correct"]:
                    profile.category_scores[cat]["correct"] += 1

        # Determine weak and strong areas
        weak = []
        strong = []
        for cat, scores in profile.category_scores.items():
            if scores["total"] >= 3:
                ratio = scores["correct"] / scores["total"]
                if ratio < 0.5:
                    weak.append(cat)
                elif ratio >= 0.8:
                    strong.append(cat)

        profile.weak_areas = weak
        profile.strong_areas = strong

        # Adjust difficulty
        if profile.total_quizzes >= 3:
            recent_quizzes = list(self._sessions.values())[-5:]
            recent_scores = [
                s.score / s.total_questions
                for s in recent_quizzes
                if s.user_id == profile.user_id and s.completed_at
            ]

            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                difficulty_order = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD, DifficultyLevel.EXPERT]
                current_idx = difficulty_order.index(profile.difficulty_level)

                if avg_score >= 0.85 and current_idx < len(difficulty_order) - 1:
                    profile.difficulty_level = difficulty_order[current_idx + 1]
                elif avg_score < 0.4 and current_idx > 0:
                    profile.difficulty_level = difficulty_order[current_idx - 1]

        # Update streak
        percentage = session.score / session.total_questions
        if percentage >= 0.7:
            profile.current_streak += 1
            profile.best_streak = max(profile.best_streak, profile.current_streak)
        else:
            profile.current_streak = 0

        # Check achievements
        self._check_achievements(profile)

    def _check_achievements(self, profile: UserQuizProfile) -> None:
        """Check and award achievements."""
        achievements = []

        if profile.total_quizzes >= 1 and "first_quiz" not in profile.achievements:
            achievements.append("first_quiz")

        if profile.total_quizzes >= 10 and "quiz_veteran" not in profile.achievements:
            achievements.append("quiz_veteran")

        if profile.best_streak >= 5 and "streak_master" not in profile.achievements:
            achievements.append("streak_master")

        if profile.difficulty_level == DifficultyLevel.HARD and "advanced_learner" not in profile.achievements:
            achievements.append("advanced_learner")

        if len(profile.strong_areas) >= 3 and "well_rounded" not in profile.achievements:
            achievements.append("well_rounded")

        profile.achievements.extend(achievements)

    def get_user_quiz_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's quiz profile."""
        profile = self._get_or_create_profile(user_id)

        return {
            "user_id": profile.user_id,
            "difficulty_level": profile.difficulty_level.value,
            "category_scores": profile.category_scores,
            "weak_areas": profile.weak_areas,
            "strong_areas": profile.strong_areas,
            "statistics": {
                "total_quizzes": profile.total_quizzes,
                "total_correct": profile.total_correct,
                "total_questions": profile.total_questions,
                "accuracy": round(profile.total_correct / max(1, profile.total_questions) * 100, 1),
            },
            "streaks": {
                "current": profile.current_streak,
                "best": profile.best_streak,
            },
            "achievements": profile.achievements,
        }

    def get_practice_quiz(
        self,
        user_id: str,
        focus_weak_areas: bool = True,
        num_questions: int = 5,
    ) -> Dict[str, Any]:
        """Get a personalized practice quiz focusing on weak areas."""
        profile = self._get_or_create_profile(user_id)

        if focus_weak_areas and profile.weak_areas:
            # Focus on first weak area
            return self.start_quiz(
                user_id=user_id,
                category=profile.weak_areas[0],
                num_questions=num_questions,
                difficulty=profile.difficulty_level.value,
            )
        else:
            return self.start_quiz(
                user_id=user_id,
                num_questions=num_questions,
                difficulty=profile.difficulty_level.value,
            )

    def get_quiz_categories(self) -> List[Dict[str, str]]:
        """Get all available quiz categories."""
        return [
            {"id": c.value, "name_en": c.value.replace("_", " ").title()}
            for c in QuestionCategory
        ]

    def get_difficulty_levels(self) -> List[Dict[str, str]]:
        """Get all difficulty levels."""
        return [
            {"id": d.value, "name_en": d.value.title()}
            for d in DifficultyLevel
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "total_questions": len(self._questions),
            "active_sessions": sum(1 for s in self._sessions.values() if not s.completed_at),
            "completed_sessions": sum(1 for s in self._sessions.values() if s.completed_at),
            "registered_users": len(self._user_profiles),
            "questions_by_category": {
                c.value: sum(1 for q in self._questions.values() if q.category == c)
                for c in QuestionCategory
            },
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

quiz_service = QuizService()
