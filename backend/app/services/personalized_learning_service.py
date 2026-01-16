"""
Personalized Learning Paths Service with SM2 Spaced Repetition

Provides comprehensive learning path management with:
- SM2 spaced repetition algorithm for optimal memorization
- Adaptive study goals and recommendations
- Personalized study paths based on Quranic themes
- Progress milestones with motivational insights
- Quizzes and reflection prompts
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math
import random


class StudyGoalType(Enum):
    """Types of study goals"""
    MEMORIZATION = "memorization"
    COMPREHENSION = "comprehension"
    REFLECTION = "reflection"
    TAFSIR_STUDY = "tafsir_study"
    THEME_EXPLORATION = "theme_exploration"


class DifficultyLevel(Enum):
    """Difficulty levels for learning content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SCHOLAR = "scholar"


class ContentType(Enum):
    """Types of learning content"""
    VERSE = "verse"
    SURAH = "surah"
    THEME = "theme"
    TAFSIR = "tafsir"
    PROPHET_STORY = "prophet_story"
    QUIZ = "quiz"
    REFLECTION = "reflection"


@dataclass
class SM2ReviewItem:
    """Represents an item being reviewed using SM2 algorithm"""
    item_id: str
    item_type: ContentType
    content: Dict[str, Any]
    easiness_factor: float = 2.5  # EF starts at 2.5
    interval: int = 0  # Days until next review
    repetition: int = 0  # Number of successful reviews
    next_review: datetime = field(default_factory=datetime.now)
    last_review: Optional[datetime] = None
    quality_history: List[int] = field(default_factory=list)


@dataclass
class StudyGoal:
    """A user's study goal"""
    goal_id: str
    user_id: str
    goal_type: StudyGoalType
    target_description: str
    target_items: List[str]  # Item IDs to study
    daily_target_minutes: int
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    completed: bool = False
    progress_percentage: float = 0.0


@dataclass
class LearningPath:
    """A structured learning path"""
    path_id: str
    title: str
    title_arabic: str
    description: str
    difficulty: DifficultyLevel
    estimated_hours: float
    modules: List[Dict[str, Any]]
    prerequisites: List[str]
    themes: List[str]
    outcomes: List[str]


@dataclass
class StudySession:
    """A user's study session"""
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    items_studied: List[str]
    quiz_scores: List[Dict[str, Any]]
    reflections: List[str]
    duration_minutes: int = 0


@dataclass
class UserProgress:
    """User's overall learning progress"""
    user_id: str
    total_verses_memorized: int = 0
    total_surahs_completed: int = 0
    total_study_hours: float = 0.0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    themes_explored: List[str] = field(default_factory=list)
    achievements: List[Dict[str, Any]] = field(default_factory=list)
    last_study_date: Optional[datetime] = None


@dataclass
class Milestone:
    """A learning milestone"""
    milestone_id: str
    title: str
    description: str
    requirement: Dict[str, Any]
    reward_message: str
    icon: str


class PersonalizedLearningService:
    """
    Service for personalized learning paths with SM2 spaced repetition.
    """

    def __init__(self):
        self.review_items: Dict[str, Dict[str, SM2ReviewItem]] = {}  # user_id -> {item_id: item}
        self.study_goals: Dict[str, List[StudyGoal]] = {}  # user_id -> goals
        self.learning_paths: Dict[str, LearningPath] = {}
        self.user_progress: Dict[str, UserProgress] = {}
        self.study_sessions: Dict[str, List[StudySession]] = {}  # user_id -> sessions
        self.milestones: Dict[str, Milestone] = {}
        self._initialize_learning_paths()
        self._initialize_milestones()
        self._initialize_sample_content()

    def _initialize_learning_paths(self):
        """Initialize predefined learning paths"""
        paths = [
            LearningPath(
                path_id="beginners_journey",
                title="Beginner's Journey to the Quran",
                title_arabic="رحلة المبتدئين إلى القرآن",
                description="A comprehensive introduction to understanding and memorizing the Quran",
                difficulty=DifficultyLevel.BEGINNER,
                estimated_hours=20,
                modules=[
                    {
                        "module_id": "m1_fatiha",
                        "title": "Understanding Al-Fatiha",
                        "lessons": [
                            {"id": "l1", "title": "Memorize Al-Fatiha", "type": "memorization", "verses": ["1:1-7"]},
                            {"id": "l2", "title": "Tafsir of Al-Fatiha", "type": "tafsir", "content_id": "tafsir_fatiha"},
                            {"id": "l3", "title": "Reflection Quiz", "type": "quiz", "quiz_id": "q_fatiha"}
                        ]
                    },
                    {
                        "module_id": "m2_short_surahs",
                        "title": "Short Surahs for Daily Prayer",
                        "lessons": [
                            {"id": "l4", "title": "Surah Al-Ikhlas", "type": "memorization", "verses": ["112:1-4"]},
                            {"id": "l5", "title": "Surah Al-Falaq", "type": "memorization", "verses": ["113:1-5"]},
                            {"id": "l6", "title": "Surah An-Nas", "type": "memorization", "verses": ["114:1-6"]}
                        ]
                    }
                ],
                prerequisites=[],
                themes=["tawhid", "prayer", "protection"],
                outcomes=[
                    "Memorize Al-Fatiha and understand its meaning",
                    "Memorize the three Quls",
                    "Understand basic tafsir methodology"
                ]
            ),
            LearningPath(
                path_id="patience_path",
                title="The Path of Patience (Sabr)",
                title_arabic="طريق الصبر",
                description="Explore the theme of patience across the Quran with memorization and reflection",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_hours=15,
                modules=[
                    {
                        "module_id": "patience_intro",
                        "title": "Understanding Sabr",
                        "lessons": [
                            {"id": "p1", "title": "What is Sabr?", "type": "comprehension", "content_id": "sabr_intro"},
                            {"id": "p2", "title": "Ayah 2:153", "type": "memorization", "verses": ["2:153"]},
                            {"id": "p3", "title": "Tafsir Comparison", "type": "tafsir", "verses": ["2:153"]}
                        ]
                    },
                    {
                        "module_id": "patience_trials",
                        "title": "Patience in Trials",
                        "lessons": [
                            {"id": "p4", "title": "Ayah 2:155-157", "type": "memorization", "verses": ["2:155-157"]},
                            {"id": "p5", "title": "Prophets of Patience", "type": "prophet_story", "prophets": ["ayyub", "yaqub"]},
                            {"id": "p6", "title": "Reflection Prompts", "type": "reflection", "prompts": ["sabr_personal"]}
                        ]
                    }
                ],
                prerequisites=["beginners_journey"],
                themes=["patience", "trials", "trust"],
                outcomes=[
                    "Memorize key verses on patience",
                    "Understand patience from multiple tafsir perspectives",
                    "Apply patience concepts to daily life"
                ]
            ),
            LearningPath(
                path_id="mercy_exploration",
                title="Divine Mercy (Al-Rahma)",
                title_arabic="الرحمة الإلهية",
                description="Deep dive into Allah's mercy as revealed in the Quran",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_hours=18,
                modules=[
                    {
                        "module_id": "mercy_names",
                        "title": "The Names of Mercy",
                        "lessons": [
                            {"id": "r1", "title": "Al-Rahman and Al-Raheem", "type": "comprehension", "content_id": "mercy_names"},
                            {"id": "r2", "title": "Ayah 6:54", "type": "memorization", "verses": ["6:54"]},
                            {"id": "r3", "title": "Mercy in Creation", "type": "reflection", "prompts": ["mercy_creation"]}
                        ]
                    },
                    {
                        "module_id": "mercy_forgiveness",
                        "title": "Mercy and Forgiveness",
                        "lessons": [
                            {"id": "r4", "title": "Ayah 39:53", "type": "memorization", "verses": ["39:53"]},
                            {"id": "r5", "title": "Tafsir on Forgiveness", "type": "tafsir", "verses": ["39:53"]},
                            {"id": "r6", "title": "Quiz: Understanding Mercy", "type": "quiz", "quiz_id": "q_mercy"}
                        ]
                    }
                ],
                prerequisites=[],
                themes=["mercy", "forgiveness", "divine_names"],
                outcomes=[
                    "Understand the dimensions of Allah's mercy",
                    "Memorize key verses on mercy",
                    "Connect mercy to daily spiritual practice"
                ]
            ),
            LearningPath(
                path_id="prophet_stories",
                title="Stories of the Prophets",
                title_arabic="قصص الأنبياء",
                description="Learn from the lives of the Prophets mentioned in the Quran",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_hours=30,
                modules=[
                    {
                        "module_id": "ibrahim_story",
                        "title": "Prophet Ibrahim (AS)",
                        "lessons": [
                            {"id": "ps1", "title": "Ibrahim's Search for Truth", "type": "prophet_story", "prophets": ["ibrahim"]},
                            {"id": "ps2", "title": "Key Verses", "type": "memorization", "verses": ["6:76-79"]},
                            {"id": "ps3", "title": "Lessons from Ibrahim", "type": "reflection", "prompts": ["ibrahim_lessons"]}
                        ]
                    },
                    {
                        "module_id": "musa_story",
                        "title": "Prophet Musa (AS)",
                        "lessons": [
                            {"id": "ps4", "title": "Musa and Firaun", "type": "prophet_story", "prophets": ["musa"]},
                            {"id": "ps5", "title": "Trust in Allah", "type": "comprehension", "content_id": "musa_trust"},
                            {"id": "ps6", "title": "Quiz: Prophet Stories", "type": "quiz", "quiz_id": "q_prophets"}
                        ]
                    }
                ],
                prerequisites=[],
                themes=["prophets", "patience", "trust", "guidance"],
                outcomes=[
                    "Know the stories of major prophets",
                    "Extract practical lessons from their lives",
                    "Memorize key verses from their stories"
                ]
            ),
            LearningPath(
                path_id="tawhid_foundation",
                title="Foundations of Tawhid",
                title_arabic="أسس التوحيد",
                description="Understanding the core concept of Islamic monotheism through the Quran",
                difficulty=DifficultyLevel.ADVANCED,
                estimated_hours=25,
                modules=[
                    {
                        "module_id": "tawhid_basics",
                        "title": "What is Tawhid?",
                        "lessons": [
                            {"id": "t1", "title": "Surah Al-Ikhlas Deep Dive", "type": "tafsir", "verses": ["112:1-4"]},
                            {"id": "t2", "title": "Ayat al-Kursi", "type": "memorization", "verses": ["2:255"]},
                            {"id": "t3", "title": "Comparative Tafsir", "type": "tafsir", "verses": ["2:255"]}
                        ]
                    },
                    {
                        "module_id": "tawhid_names",
                        "title": "Knowing Allah Through His Names",
                        "lessons": [
                            {"id": "t4", "title": "Beautiful Names of Allah", "type": "comprehension", "content_id": "asma_husna"},
                            {"id": "t5", "title": "Names in the Quran", "type": "theme_exploration", "theme": "divine_names"},
                            {"id": "t6", "title": "Reflection: Connecting to Allah", "type": "reflection", "prompts": ["tawhid_connection"]}
                        ]
                    }
                ],
                prerequisites=["beginners_journey"],
                themes=["tawhid", "divine_names", "faith"],
                outcomes=[
                    "Deep understanding of Tawhid",
                    "Memorize Ayat al-Kursi with understanding",
                    "Know key names of Allah and their meanings"
                ]
            )
        ]

        for path in paths:
            self.learning_paths[path.path_id] = path

    def _initialize_milestones(self):
        """Initialize achievement milestones"""
        milestones_data = [
            Milestone(
                milestone_id="first_verse",
                title="First Step",
                description="Memorize your first verse",
                requirement={"verses_memorized": 1},
                reward_message="Congratulations! You've taken your first step in memorizing the Quran.",
                icon="🌟"
            ),
            Milestone(
                milestone_id="first_surah",
                title="Surah Complete",
                description="Complete memorizing your first surah",
                requirement={"surahs_completed": 1},
                reward_message="MashaAllah! You've memorized your first complete surah!",
                icon="📖"
            ),
            Milestone(
                milestone_id="seven_day_streak",
                title="Week of Dedication",
                description="Study for 7 consecutive days",
                requirement={"streak_days": 7},
                reward_message="Amazing consistency! A week of dedicated study.",
                icon="🔥"
            ),
            Milestone(
                milestone_id="thirty_day_streak",
                title="Month of Commitment",
                description="Study for 30 consecutive days",
                requirement={"streak_days": 30},
                reward_message="Exceptional! A full month of consistent Quran study.",
                icon="🏆"
            ),
            Milestone(
                milestone_id="ten_verses",
                title="Growing Foundation",
                description="Memorize 10 verses",
                requirement={"verses_memorized": 10},
                reward_message="Your foundation is growing stronger!",
                icon="🌱"
            ),
            Milestone(
                milestone_id="five_themes",
                title="Theme Explorer",
                description="Explore 5 different Quranic themes",
                requirement={"themes_explored": 5},
                reward_message="You're discovering the richness of the Quran's themes!",
                icon="🔍"
            ),
            Milestone(
                milestone_id="first_path",
                title="Path Complete",
                description="Complete your first learning path",
                requirement={"paths_completed": 1},
                reward_message="Alhamdulillah! You've completed your first learning journey!",
                icon="🎯"
            )
        ]

        for milestone in milestones_data:
            self.milestones[milestone.milestone_id] = milestone

    def _initialize_sample_content(self):
        """Initialize sample memorization content"""
        self.sample_verses = {
            "1:1": {"arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "english": "In the name of Allah, the Most Gracious, the Most Merciful"},
            "2:153": {"arabic": "يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ", "english": "O you who believe, seek help through patience and prayer"},
            "2:255": {"arabic": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", "english": "Allah - there is no deity except Him, the Ever-Living, the Sustainer"},
            "112:1": {"arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ", "english": "Say: He is Allah, the One"},
            "39:53": {"arabic": "قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنفُسِهِمْ لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ", "english": "Say, O My servants who have transgressed against themselves, do not despair of the mercy of Allah"}
        }

        self.reflection_prompts = {
            "sabr_personal": [
                "Reflect on a time when patience helped you through difficulty.",
                "How can you apply the concept of sabr in your current challenges?",
                "What lessons from the patient prophets resonate with you most?"
            ],
            "mercy_creation": [
                "List three manifestations of Allah's mercy in your life today.",
                "How does understanding Al-Rahman change your view of hardship?",
                "In what ways can you embody mercy towards others?"
            ],
            "ibrahim_lessons": [
                "What does Ibrahim's questioning teach us about faith?",
                "How did Ibrahim balance trust in Allah with taking action?",
                "What sacrifice are you being called to make for your faith?"
            ],
            "tawhid_connection": [
                "How does knowing Allah's names deepen your worship?",
                "Reflect on a time when you felt closest to Allah.",
                "What aspects of Tawhid do you want to understand better?"
            ]
        }

        self.quiz_bank = {
            "q_fatiha": [
                {
                    "question": "What does 'Al-Hamdulillah' mean?",
                    "options": ["Glory to Allah", "All praise is due to Allah", "Allah is the Greatest", "In the name of Allah"],
                    "correct": 1,
                    "explanation": "Al-Hamdulillah means 'All praise is due to Allah' and encompasses both praise and gratitude."
                },
                {
                    "question": "How many verses are in Surah Al-Fatiha?",
                    "options": ["5", "6", "7", "8"],
                    "correct": 2,
                    "explanation": "Surah Al-Fatiha has 7 verses, which is why it's also called 'As-Sab' al-Mathani' (The Seven Oft-Repeated)."
                }
            ],
            "q_mercy": [
                {
                    "question": "What is the difference between Al-Rahman and Al-Raheem?",
                    "options": [
                        "Al-Rahman is for believers only, Al-Raheem is for all",
                        "Al-Rahman encompasses all creation, Al-Raheem is specific mercy for believers",
                        "They mean exactly the same thing",
                        "Al-Rahman is for the Hereafter, Al-Raheem is for this world"
                    ],
                    "correct": 1,
                    "explanation": "Al-Rahman indicates the vastness of mercy encompassing all creation, while Al-Raheem indicates the special mercy Allah has for the believers."
                }
            ],
            "q_prophets": [
                {
                    "question": "Which prophet is known for his exceptional patience?",
                    "options": ["Musa (AS)", "Ayyub (AS)", "Isa (AS)", "Nuh (AS)"],
                    "correct": 1,
                    "explanation": "Prophet Ayyub (AS) is particularly known for his patience during severe trials of health and loss."
                }
            ]
        }

    # SM2 Algorithm Implementation
    def _calculate_sm2(self, quality: int, ef: float, interval: int, repetition: int) -> Tuple[float, int, int]:
        """
        Calculate new SM2 values based on quality of response.

        Quality ratings:
        5 - perfect response
        4 - correct response after hesitation
        3 - correct response with difficulty
        2 - incorrect response but remembered when shown
        1 - incorrect response with hint
        0 - complete blackout

        Returns: (new_ef, new_interval, new_repetition)
        """
        # Calculate new easiness factor
        new_ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)  # EF minimum is 1.3

        if quality < 3:
            # Failed - reset repetitions
            new_repetition = 0
            new_interval = 1
        else:
            # Passed
            if repetition == 0:
                new_interval = 1
            elif repetition == 1:
                new_interval = 6
            else:
                new_interval = int(interval * new_ef)

            new_repetition = repetition + 1

        return new_ef, new_interval, new_repetition

    def add_item_for_review(
            self,
            user_id: str,
            item_id: str,
            item_type: ContentType,
            content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a new item to user's spaced repetition queue"""
        if user_id not in self.review_items:
            self.review_items[user_id] = {}

        item = SM2ReviewItem(
            item_id=item_id,
            item_type=item_type,
            content=content,
            next_review=datetime.now()
        )

        self.review_items[user_id][item_id] = item

        return {
            "item_id": item_id,
            "message": "Item added to review queue",
            "next_review": item.next_review.isoformat()
        }

    def review_item(self, user_id: str, item_id: str, quality: int) -> Dict[str, Any]:
        """
        Record a review and calculate next review date using SM2.

        Args:
            user_id: User ID
            item_id: Item being reviewed
            quality: Quality of recall (0-5)

        Returns:
            Updated review information
        """
        if user_id not in self.review_items or item_id not in self.review_items[user_id]:
            return {"error": "Item not found in review queue"}

        if quality < 0 or quality > 5:
            return {"error": "Quality must be between 0 and 5"}

        item = self.review_items[user_id][item_id]

        # Calculate new SM2 values
        new_ef, new_interval, new_repetition = self._calculate_sm2(
            quality, item.easiness_factor, item.interval, item.repetition
        )

        # Update item
        item.easiness_factor = new_ef
        item.interval = new_interval
        item.repetition = new_repetition
        item.last_review = datetime.now()
        item.next_review = datetime.now() + timedelta(days=new_interval)
        item.quality_history.append(quality)

        # Update user progress
        self._update_user_progress(user_id, item, quality)

        return {
            "item_id": item_id,
            "quality_recorded": quality,
            "new_easiness_factor": round(new_ef, 2),
            "new_interval_days": new_interval,
            "repetition_count": new_repetition,
            "next_review": item.next_review.isoformat(),
            "review_result": "passed" if quality >= 3 else "needs_review"
        }

    def get_due_reviews(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get items due for review"""
        if user_id not in self.review_items:
            return {"items": [], "total_due": 0}

        now = datetime.now()
        due_items = [
            {
                "item_id": item.item_id,
                "item_type": item.item_type.value,
                "content": item.content,
                "days_overdue": (now - item.next_review).days if now > item.next_review else 0,
                "repetition_count": item.repetition,
                "easiness_factor": round(item.easiness_factor, 2)
            }
            for item in self.review_items[user_id].values()
            if item.next_review <= now
        ]

        # Sort by days overdue (most overdue first)
        due_items.sort(key=lambda x: x["days_overdue"], reverse=True)

        return {
            "items": due_items[:limit],
            "total_due": len(due_items)
        }

    def get_review_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user's review statistics"""
        if user_id not in self.review_items:
            return {"total_items": 0, "message": "No items in review queue"}

        items = self.review_items[user_id].values()
        now = datetime.now()

        return {
            "total_items": len(items),
            "items_due_today": len([i for i in items if i.next_review.date() == now.date()]),
            "items_overdue": len([i for i in items if i.next_review < now]),
            "items_mastered": len([i for i in items if i.repetition >= 5]),
            "average_easiness_factor": round(sum(i.easiness_factor for i in items) / len(items), 2) if items else 0,
            "total_reviews": sum(len(i.quality_history) for i in items)
        }

    # Study Goals Management
    def create_study_goal(
            self,
            user_id: str,
            goal_type: str,
            target_description: str,
            target_items: List[str],
            daily_target_minutes: int = 15,
            deadline_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new study goal for user"""
        goal_id = f"goal_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            goal_type_enum = StudyGoalType(goal_type)
        except ValueError:
            return {"error": f"Invalid goal type. Valid types: {[t.value for t in StudyGoalType]}"}

        deadline = datetime.now() + timedelta(days=deadline_days) if deadline_days else None

        goal = StudyGoal(
            goal_id=goal_id,
            user_id=user_id,
            goal_type=goal_type_enum,
            target_description=target_description,
            target_items=target_items,
            daily_target_minutes=daily_target_minutes,
            deadline=deadline
        )

        if user_id not in self.study_goals:
            self.study_goals[user_id] = []

        self.study_goals[user_id].append(goal)

        # Add items to review queue
        for item_id in target_items:
            if item_id in self.sample_verses:
                self.add_item_for_review(
                    user_id,
                    item_id,
                    ContentType.VERSE,
                    self.sample_verses[item_id]
                )

        return {
            "goal_id": goal_id,
            "goal_type": goal_type,
            "target_description": target_description,
            "items_count": len(target_items),
            "daily_target_minutes": daily_target_minutes,
            "deadline": deadline.isoformat() if deadline else None,
            "message": "Goal created successfully"
        }

    def get_user_goals(self, user_id: str) -> Dict[str, Any]:
        """Get all goals for a user"""
        if user_id not in self.study_goals:
            return {"goals": [], "total": 0}

        goals = [
            {
                "goal_id": g.goal_id,
                "goal_type": g.goal_type.value,
                "target_description": g.target_description,
                "progress_percentage": g.progress_percentage,
                "completed": g.completed,
                "daily_target_minutes": g.daily_target_minutes,
                "deadline": g.deadline.isoformat() if g.deadline else None
            }
            for g in self.study_goals[user_id]
        ]

        return {"goals": goals, "total": len(goals)}

    # Learning Paths
    def get_all_learning_paths(self) -> List[Dict[str, Any]]:
        """Get all available learning paths"""
        return [
            {
                "path_id": p.path_id,
                "title": p.title,
                "title_arabic": p.title_arabic,
                "description": p.description,
                "difficulty": p.difficulty.value,
                "estimated_hours": p.estimated_hours,
                "modules_count": len(p.modules),
                "themes": p.themes,
                "prerequisites": p.prerequisites
            }
            for p in self.learning_paths.values()
        ]

    def get_learning_path(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a learning path"""
        if path_id not in self.learning_paths:
            return None

        path = self.learning_paths[path_id]
        return {
            "path_id": path.path_id,
            "title": path.title,
            "title_arabic": path.title_arabic,
            "description": path.description,
            "difficulty": path.difficulty.value,
            "estimated_hours": path.estimated_hours,
            "modules": path.modules,
            "prerequisites": path.prerequisites,
            "themes": path.themes,
            "outcomes": path.outcomes
        }

    def get_recommended_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recommended learning paths based on user progress"""
        progress = self._get_or_create_progress(user_id)

        recommendations = []
        for path in self.learning_paths.values():
            # Check prerequisites
            # For simplicity, recommend paths without prerequisites first
            priority = 0
            if not path.prerequisites:
                priority = 10
            elif any(theme in progress.themes_explored for theme in path.themes):
                priority = 5

            recommendations.append({
                "path_id": path.path_id,
                "title": path.title,
                "difficulty": path.difficulty.value,
                "estimated_hours": path.estimated_hours,
                "relevance_score": priority,
                "reason": "Matches your interests" if priority > 5 else "Good starting point"
            })

        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:5]

    # Progress Tracking
    def _get_or_create_progress(self, user_id: str) -> UserProgress:
        """Get or create user progress"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(user_id=user_id)
        return self.user_progress[user_id]

    def _update_user_progress(self, user_id: str, item: SM2ReviewItem, quality: int):
        """Update user progress after a review"""
        progress = self._get_or_create_progress(user_id)

        # Update study streak
        today = datetime.now().date()
        if progress.last_study_date:
            if progress.last_study_date == today - timedelta(days=1):
                progress.current_streak_days += 1
            elif progress.last_study_date != today:
                progress.current_streak_days = 1

            if progress.current_streak_days > progress.longest_streak_days:
                progress.longest_streak_days = progress.current_streak_days
        else:
            progress.current_streak_days = 1

        progress.last_study_date = today

        # Update verses memorized if quality >= 4
        if quality >= 4 and item.item_type == ContentType.VERSE:
            progress.total_verses_memorized += 1

        # Check milestones
        self._check_milestones(user_id, progress)

    def _check_milestones(self, user_id: str, progress: UserProgress):
        """Check and award milestones"""
        for milestone_id, milestone in self.milestones.items():
            # Check if already awarded
            if any(a.get("milestone_id") == milestone_id for a in progress.achievements):
                continue

            # Check requirement
            awarded = False
            req = milestone.requirement

            if "verses_memorized" in req and progress.total_verses_memorized >= req["verses_memorized"]:
                awarded = True
            elif "surahs_completed" in req and progress.total_surahs_completed >= req["surahs_completed"]:
                awarded = True
            elif "streak_days" in req and progress.current_streak_days >= req["streak_days"]:
                awarded = True
            elif "themes_explored" in req and len(progress.themes_explored) >= req["themes_explored"]:
                awarded = True

            if awarded:
                progress.achievements.append({
                    "milestone_id": milestone_id,
                    "title": milestone.title,
                    "icon": milestone.icon,
                    "awarded_at": datetime.now().isoformat()
                })

    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's overall progress"""
        progress = self._get_or_create_progress(user_id)

        return {
            "user_id": user_id,
            "total_verses_memorized": progress.total_verses_memorized,
            "total_surahs_completed": progress.total_surahs_completed,
            "total_study_hours": progress.total_study_hours,
            "current_streak_days": progress.current_streak_days,
            "longest_streak_days": progress.longest_streak_days,
            "themes_explored": progress.themes_explored,
            "achievements": progress.achievements,
            "last_study_date": progress.last_study_date.isoformat() if progress.last_study_date else None
        }

    # Quizzes and Reflection
    def get_quiz(self, quiz_id: str) -> Dict[str, Any]:
        """Get a quiz by ID"""
        if quiz_id not in self.quiz_bank:
            return {"error": f"Quiz '{quiz_id}' not found"}

        questions = self.quiz_bank[quiz_id]
        # Don't include correct answers in response
        return {
            "quiz_id": quiz_id,
            "questions": [
                {
                    "question_index": i,
                    "question": q["question"],
                    "options": q["options"]
                }
                for i, q in enumerate(questions)
            ],
            "total_questions": len(questions)
        }

    def submit_quiz_answer(self, quiz_id: str, question_index: int, answer_index: int) -> Dict[str, Any]:
        """Submit and check a quiz answer"""
        if quiz_id not in self.quiz_bank:
            return {"error": f"Quiz '{quiz_id}' not found"}

        questions = self.quiz_bank[quiz_id]
        if question_index >= len(questions):
            return {"error": "Invalid question index"}

        question = questions[question_index]
        is_correct = answer_index == question["correct"]

        return {
            "is_correct": is_correct,
            "correct_answer": question["options"][question["correct"]],
            "explanation": question["explanation"],
            "your_answer": question["options"][answer_index] if 0 <= answer_index < len(question["options"]) else "Invalid"
        }

    def get_reflection_prompts(self, prompt_id: str) -> Dict[str, Any]:
        """Get reflection prompts by ID"""
        if prompt_id not in self.reflection_prompts:
            return {"error": f"Prompts '{prompt_id}' not found", "available": list(self.reflection_prompts.keys())}

        return {
            "prompt_id": prompt_id,
            "prompts": self.reflection_prompts[prompt_id]
        }

    def get_daily_recommendation(self, user_id: str) -> Dict[str, Any]:
        """Get personalized daily study recommendation"""
        progress = self._get_or_create_progress(user_id)
        due_reviews = self.get_due_reviews(user_id, limit=5)

        recommendation = {
            "greeting": self._get_motivational_greeting(progress),
            "due_reviews": due_reviews,
            "suggested_activity": None,
            "motivational_message": None
        }

        # Suggest activity based on progress
        if due_reviews["total_due"] > 0:
            recommendation["suggested_activity"] = {
                "type": "review",
                "message": f"You have {due_reviews['total_due']} items due for review"
            }
        elif progress.total_verses_memorized < 5:
            recommendation["suggested_activity"] = {
                "type": "memorization",
                "message": "Start memorizing a new verse to build your foundation"
            }
        else:
            recommendation["suggested_activity"] = {
                "type": "new_path",
                "message": "Explore a new learning path to expand your knowledge"
            }

        # Add motivational message based on streak
        if progress.current_streak_days >= 7:
            recommendation["motivational_message"] = f"Amazing! You're on a {progress.current_streak_days}-day streak! Keep it up!"
        elif progress.current_streak_days > 0:
            recommendation["motivational_message"] = f"Great start! You're on day {progress.current_streak_days} of your streak."
        else:
            recommendation["motivational_message"] = "Today is a perfect day to reconnect with the Quran!"

        return recommendation

    def _get_motivational_greeting(self, progress: UserProgress) -> str:
        """Generate personalized greeting"""
        greetings = [
            "Assalamu Alaikum! Ready for your Quran journey today?",
            "Welcome back! The Quran awaits your reflection.",
            "Bismillah! Let's continue your learning journey.",
            "May Allah bless your study today!"
        ]
        return random.choice(greetings)

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "total_learning_paths": len(self.learning_paths),
            "total_milestones": len(self.milestones),
            "total_quizzes": len(self.quiz_bank),
            "total_reflection_prompts": len(self.reflection_prompts),
            "total_users_with_progress": len(self.user_progress),
            "total_users_with_reviews": len(self.review_items),
            "available_paths": list(self.learning_paths.keys()),
            "available_quizzes": list(self.quiz_bank.keys())
        }


# Create singleton instance
personalized_learning_service = PersonalizedLearningService()
