"""
Multi-Disciplinary Learning Paths Service.

Provides structured learning journeys that guide users through
cross-disciplinary exploration of Quranic topics, integrating
Fiqh, Hadith, Tafsir, Sira, and thematic studies.

Features:
1. Pre-designed learning paths for common study goals
2. Personalized path generation based on interests
3. Progress tracking and milestones
4. Cross-disciplinary integration
5. Adaptive difficulty adjustment

Arabic: خدمة مسارات التعلم متعددة التخصصات
"""

import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class PathDifficulty(str, Enum):
    """Learning path difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SCHOLAR = "scholar"


class PathCategory(str, Enum):
    """Categories of learning paths."""
    FOUNDATIONAL = "foundational"
    THEMATIC = "thematic"
    PROPHET_STUDY = "prophet_study"
    JURISPRUDENCE = "jurisprudence"
    SPIRITUALITY = "spirituality"
    RESEARCH = "research"


class LessonType(str, Enum):
    """Types of lessons in a learning path."""
    QURAN_VERSES = "quran_verses"
    TAFSIR_STUDY = "tafsir_study"
    HADITH_STUDY = "hadith_study"
    FIQH_RULING = "fiqh_ruling"
    SIRA_EVENT = "sira_event"
    REFLECTION = "reflection"
    QUIZ = "quiz"
    PRACTICAL = "practical"


class MilestoneType(str, Enum):
    """Types of milestones."""
    LESSON_COMPLETE = "lesson_complete"
    MODULE_COMPLETE = "module_complete"
    PATH_COMPLETE = "path_complete"
    QUIZ_PASSED = "quiz_passed"
    REFLECTION_SUBMITTED = "reflection_submitted"


@dataclass
class Lesson:
    """A lesson in a learning path."""
    lesson_id: str
    title_ar: str
    title_en: str
    lesson_type: LessonType
    content: Dict[str, Any]
    duration_minutes: int
    objectives: List[str]
    resources: List[Dict[str, str]]


@dataclass
class Module:
    """A module containing related lessons."""
    module_id: str
    title_ar: str
    title_en: str
    description_en: str
    lessons: List[Lesson]
    prerequisites: List[str]
    learning_outcomes: List[str]


@dataclass
class LearningPath:
    """Complete learning path."""
    path_id: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    category: PathCategory
    difficulty: PathDifficulty
    modules: List[Module]
    estimated_hours: int
    tags: List[str]
    disciplines_covered: List[str]


@dataclass
class UserPathProgress:
    """User's progress in a learning path."""
    user_id: str
    path_id: str
    started_at: datetime
    current_module: int
    current_lesson: int
    lessons_completed: List[str]
    milestones: List[Dict[str, Any]]
    quiz_scores: Dict[str, float]
    reflections: List[Dict[str, Any]]
    completion_percent: float


# =============================================================================
# LEARNING PATHS DATA
# =============================================================================

LEARNING_PATHS = {
    "patience_comprehensive": {
        "title_ar": "الصبر في القرآن والسنة",
        "title_en": "Patience in Quran and Sunnah",
        "description_ar": "دراسة شاملة لمفهوم الصبر من خلال القرآن والحديث وقصص الأنبياء",
        "description_en": "Comprehensive study of patience through Quran, Hadith, and Prophet stories",
        "category": PathCategory.THEMATIC,
        "difficulty": PathDifficulty.INTERMEDIATE,
        "disciplines": ["quran", "tafsir", "hadith", "sira"],
        "estimated_hours": 15,
        "tags": ["patience", "trials", "faith", "prophets"],
        "modules": [
            {
                "module_id": "patience_intro",
                "title_ar": "مفهوم الصبر",
                "title_en": "Understanding Patience",
                "description_en": "Introduction to the concept of patience in Islam",
                "prerequisites": [],
                "learning_outcomes": ["Define sabr", "Understand types of patience", "Know rewards of patience"],
                "lessons": [
                    {
                        "lesson_id": "patience_def",
                        "title_ar": "تعريف الصبر",
                        "title_en": "Definition of Patience",
                        "lesson_type": LessonType.QURAN_VERSES,
                        "duration_minutes": 20,
                        "content": {
                            "verses": ["2:45", "2:153", "2:155-157"],
                            "focus": "Understanding patience as seeking help",
                        },
                        "objectives": ["Define patience Islamically", "Identify verse keywords"],
                        "resources": [{"type": "verse", "reference": "2:45"}],
                    },
                    {
                        "lesson_id": "patience_tafsir",
                        "title_ar": "تفسير آيات الصبر",
                        "title_en": "Tafsir of Patience Verses",
                        "lesson_type": LessonType.TAFSIR_STUDY,
                        "duration_minutes": 30,
                        "content": {
                            "verses": ["2:155-157"],
                            "tafsir_sources": ["ibn_kathir", "qurtubi"],
                        },
                        "objectives": ["Understand scholarly interpretations"],
                        "resources": [{"type": "tafsir", "source": "ibn_kathir"}],
                    },
                    {
                        "lesson_id": "patience_hadith",
                        "title_ar": "أحاديث الصبر",
                        "title_en": "Hadith on Patience",
                        "lesson_type": LessonType.HADITH_STUDY,
                        "duration_minutes": 25,
                        "content": {
                            "hadith_topics": ["reward_of_patience", "patience_in_calamity"],
                            "key_hadith": ["الصبر عند الصدمة الأولى"],
                        },
                        "objectives": ["Learn key hadith on patience"],
                        "resources": [{"type": "hadith", "source": "bukhari"}],
                    },
                ],
            },
            {
                "module_id": "patience_prophets",
                "title_ar": "الصبر في قصص الأنبياء",
                "title_en": "Patience in Prophet Stories",
                "description_en": "Studying patience through the lives of prophets",
                "prerequisites": ["patience_intro"],
                "learning_outcomes": ["Learn from prophet examples", "Apply lessons to life"],
                "lessons": [
                    {
                        "lesson_id": "ayyub_patience",
                        "title_ar": "صبر أيوب",
                        "title_en": "Patience of Ayyub",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 30,
                        "content": {
                            "prophet": "أيوب",
                            "verses": ["21:83-84", "38:41-44"],
                            "lessons": ["patience_in_illness", "gratitude_after_trial"],
                        },
                        "objectives": ["Understand Ayyub's trials", "Extract lessons"],
                        "resources": [{"type": "narrative", "prophet": "ayyub"}],
                    },
                    {
                        "lesson_id": "yusuf_patience",
                        "title_ar": "صبر يوسف",
                        "title_en": "Patience of Yusuf",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 35,
                        "content": {
                            "prophet": "يوسف",
                            "verses": ["12:18", "12:83", "12:90"],
                            "lessons": ["patience_with_injustice", "trust_in_divine_plan"],
                        },
                        "objectives": ["Study Yusuf's patience"],
                        "resources": [{"type": "narrative", "prophet": "yusuf"}],
                    },
                    {
                        "lesson_id": "yaqub_patience",
                        "title_ar": "صبر يعقوب",
                        "title_en": "Patience of Yaqub",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 25,
                        "content": {
                            "prophet": "يعقوب",
                            "verses": ["12:18", "12:83", "12:86"],
                            "lessons": ["patience_of_parent", "beautiful_patience"],
                        },
                        "objectives": ["Understand beautiful patience (sabr jameel)"],
                        "resources": [{"type": "narrative", "prophet": "yaqub"}],
                    },
                ],
            },
            {
                "module_id": "patience_practical",
                "title_ar": "تطبيق الصبر في الحياة",
                "title_en": "Practical Application of Patience",
                "description_en": "Applying patience in daily life",
                "prerequisites": ["patience_intro", "patience_prophets"],
                "learning_outcomes": ["Apply patience practically", "Develop patience strategies"],
                "lessons": [
                    {
                        "lesson_id": "patience_reflection",
                        "title_ar": "تأملات في الصبر",
                        "title_en": "Reflections on Patience",
                        "lesson_type": LessonType.REFLECTION,
                        "duration_minutes": 20,
                        "content": {
                            "prompts": [
                                "When have you needed patience recently?",
                                "How can prophet stories help you?",
                            ],
                        },
                        "objectives": ["Personal reflection"],
                        "resources": [],
                    },
                    {
                        "lesson_id": "patience_quiz",
                        "title_ar": "اختبار الصبر",
                        "title_en": "Patience Quiz",
                        "lesson_type": LessonType.QUIZ,
                        "duration_minutes": 15,
                        "content": {
                            "questions": 10,
                            "passing_score": 70,
                        },
                        "objectives": ["Test understanding"],
                        "resources": [],
                    },
                ],
            },
        ],
    },
    "prayer_fiqh_guide": {
        "title_ar": "دليل الصلاة الشامل",
        "title_en": "Comprehensive Prayer Guide",
        "description_ar": "تعلم أحكام الصلاة من الفقه والسنة",
        "description_en": "Learn prayer rulings from Fiqh and Sunnah",
        "category": PathCategory.JURISPRUDENCE,
        "difficulty": PathDifficulty.BEGINNER,
        "disciplines": ["quran", "hadith", "fiqh"],
        "estimated_hours": 10,
        "tags": ["prayer", "salah", "worship", "fiqh"],
        "modules": [
            {
                "module_id": "prayer_obligation",
                "title_ar": "فرضية الصلاة",
                "title_en": "Obligation of Prayer",
                "description_en": "Understanding prayer as an obligation",
                "prerequisites": [],
                "learning_outcomes": ["Know prayer is obligatory", "Understand who must pray"],
                "lessons": [
                    {
                        "lesson_id": "prayer_verses",
                        "title_ar": "آيات الصلاة",
                        "title_en": "Quranic Verses on Prayer",
                        "lesson_type": LessonType.QURAN_VERSES,
                        "duration_minutes": 25,
                        "content": {
                            "verses": ["2:43", "2:110", "4:103", "20:14"],
                            "focus": "Prayer commandments in Quran",
                        },
                        "objectives": ["Identify prayer verses"],
                        "resources": [{"type": "verse", "reference": "2:43"}],
                    },
                    {
                        "lesson_id": "prayer_fiqh",
                        "title_ar": "فقه الصلاة",
                        "title_en": "Fiqh of Prayer",
                        "lesson_type": LessonType.FIQH_RULING,
                        "duration_minutes": 30,
                        "content": {
                            "ruling_id": "salah_obligation",
                            "topics": ["conditions", "pillars", "obligatory_acts"],
                        },
                        "objectives": ["Know prayer conditions"],
                        "resources": [{"type": "fiqh", "ruling": "salah_obligation"}],
                    },
                ],
            },
            {
                "module_id": "prayer_method",
                "title_ar": "كيفية الصلاة",
                "title_en": "How to Pray",
                "description_en": "Learning the correct method of prayer",
                "prerequisites": ["prayer_obligation"],
                "learning_outcomes": ["Perform prayer correctly", "Know pillars and Sunnahs"],
                "lessons": [
                    {
                        "lesson_id": "prayer_hadith",
                        "title_ar": "أحاديث كيفية الصلاة",
                        "title_en": "Hadith on Prayer Method",
                        "lesson_type": LessonType.HADITH_STUDY,
                        "duration_minutes": 35,
                        "content": {
                            "key_hadith": ["صلوا كما رأيتموني أصلي"],
                            "topics": ["prayer_description", "prophet_prayer"],
                        },
                        "objectives": ["Learn prayer method from Sunnah"],
                        "resources": [{"type": "hadith", "topic": "prayer"}],
                    },
                    {
                        "lesson_id": "prayer_practical",
                        "title_ar": "التطبيق العملي",
                        "title_en": "Practical Application",
                        "lesson_type": LessonType.PRACTICAL,
                        "duration_minutes": 30,
                        "content": {
                            "activities": ["practice_wudu", "practice_prayer"],
                        },
                        "objectives": ["Practice prayer physically"],
                        "resources": [],
                    },
                ],
            },
        ],
    },
    "prophetic_leadership": {
        "title_ar": "القيادة النبوية",
        "title_en": "Prophetic Leadership",
        "description_ar": "دراسة نماذج القيادة من قصص الأنبياء",
        "description_en": "Study leadership models from prophet stories",
        "category": PathCategory.PROPHET_STUDY,
        "difficulty": PathDifficulty.ADVANCED,
        "disciplines": ["quran", "tafsir", "sira"],
        "estimated_hours": 20,
        "tags": ["leadership", "prophets", "wisdom", "governance"],
        "modules": [
            {
                "module_id": "leadership_intro",
                "title_ar": "مقدمة في القيادة",
                "title_en": "Introduction to Leadership",
                "description_en": "Understanding Islamic leadership principles",
                "prerequisites": [],
                "learning_outcomes": ["Define Islamic leadership", "Know key qualities"],
                "lessons": [
                    {
                        "lesson_id": "leadership_qualities",
                        "title_ar": "صفات القائد",
                        "title_en": "Qualities of a Leader",
                        "lesson_type": LessonType.QURAN_VERSES,
                        "duration_minutes": 30,
                        "content": {
                            "themes": ["justice", "wisdom", "consultation"],
                            "verses": ["3:159", "38:26", "42:38"],
                        },
                        "objectives": ["Identify leadership qualities from Quran"],
                        "resources": [{"type": "theme", "id": "leadership"}],
                    },
                ],
            },
            {
                "module_id": "prophet_leaders",
                "title_ar": "الأنبياء القادة",
                "title_en": "Prophets as Leaders",
                "description_en": "Studying specific prophets as leadership models",
                "prerequisites": ["leadership_intro"],
                "learning_outcomes": ["Learn from prophets' leadership", "Extract practical lessons"],
                "lessons": [
                    {
                        "lesson_id": "dawud_sulayman",
                        "title_ar": "داود وسليمان",
                        "title_en": "Dawud and Sulayman",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 40,
                        "content": {
                            "prophets": ["داود", "سليمان"],
                            "verses": ["38:26", "27:15-44"],
                            "themes": ["justice", "wisdom", "gratitude"],
                        },
                        "objectives": ["Study prophet-kings"],
                        "resources": [{"type": "narrative", "prophet": "dawud"}],
                    },
                    {
                        "lesson_id": "yusuf_leadership",
                        "title_ar": "قيادة يوسف",
                        "title_en": "Leadership of Yusuf",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 35,
                        "content": {
                            "prophet": "يوسف",
                            "verses": ["12:54-57", "12:100"],
                            "themes": ["planning", "crisis_management", "forgiveness"],
                        },
                        "objectives": ["Study Yusuf's leadership"],
                        "resources": [{"type": "narrative", "prophet": "yusuf"}],
                    },
                    {
                        "lesson_id": "musa_leadership",
                        "title_ar": "قيادة موسى",
                        "title_en": "Leadership of Musa",
                        "lesson_type": LessonType.SIRA_EVENT,
                        "duration_minutes": 45,
                        "content": {
                            "prophet": "موسى",
                            "verses": ["20:25-36", "7:142"],
                            "themes": ["delegation", "courage", "perseverance"],
                        },
                        "objectives": ["Study Musa's leadership"],
                        "resources": [{"type": "narrative", "prophet": "musa"}],
                    },
                ],
            },
        ],
    },
    "spiritual_purification": {
        "title_ar": "تزكية النفس",
        "title_en": "Spiritual Purification",
        "description_ar": "رحلة تزكية النفس من خلال القرآن والسنة",
        "description_en": "Journey of soul purification through Quran and Sunnah",
        "category": PathCategory.SPIRITUALITY,
        "difficulty": PathDifficulty.INTERMEDIATE,
        "disciplines": ["quran", "tafsir", "hadith"],
        "estimated_hours": 18,
        "tags": ["tazkiyah", "heart", "soul", "ihsan"],
        "modules": [
            {
                "module_id": "tazkiyah_intro",
                "title_ar": "مفهوم التزكية",
                "title_en": "Understanding Tazkiyah",
                "description_en": "Introduction to spiritual purification",
                "prerequisites": [],
                "learning_outcomes": ["Define tazkiyah", "Know its importance"],
                "lessons": [
                    {
                        "lesson_id": "tazkiyah_quran",
                        "title_ar": "التزكية في القرآن",
                        "title_en": "Tazkiyah in Quran",
                        "lesson_type": LessonType.QURAN_VERSES,
                        "duration_minutes": 30,
                        "content": {
                            "verses": ["91:7-10", "87:14-15", "62:2"],
                            "focus": "Soul purification commands",
                        },
                        "objectives": ["Understand Quranic basis for tazkiyah"],
                        "resources": [{"type": "verse", "reference": "91:7-10"}],
                    },
                ],
            },
            {
                "module_id": "heart_diseases",
                "title_ar": "أمراض القلوب",
                "title_en": "Diseases of the Heart",
                "description_en": "Identifying and treating spiritual diseases",
                "prerequisites": ["tazkiyah_intro"],
                "learning_outcomes": ["Identify heart diseases", "Know treatments"],
                "lessons": [
                    {
                        "lesson_id": "kibr_hasad",
                        "title_ar": "الكبر والحسد",
                        "title_en": "Pride and Envy",
                        "lesson_type": LessonType.TAFSIR_STUDY,
                        "duration_minutes": 35,
                        "content": {
                            "topics": ["kibr", "hasad"],
                            "verses": ["4:54", "2:109", "31:18"],
                        },
                        "objectives": ["Understand pride and envy"],
                        "resources": [{"type": "tafsir", "topic": "heart_diseases"}],
                    },
                    {
                        "lesson_id": "heart_hadith",
                        "title_ar": "أحاديث القلوب",
                        "title_en": "Hadith on Hearts",
                        "lesson_type": LessonType.HADITH_STUDY,
                        "duration_minutes": 30,
                        "content": {
                            "key_hadith": ["ألا وإن في الجسد مضغة"],
                            "topics": ["heart_rectification"],
                        },
                        "objectives": ["Learn from hadith on hearts"],
                        "resources": [{"type": "hadith", "topic": "heart"}],
                    },
                ],
            },
        ],
    },
}


# =============================================================================
# LEARNING PATH SERVICE
# =============================================================================

class LearningPathService:
    """
    Multi-disciplinary learning paths service.

    Features:
    - Structured learning journeys
    - Progress tracking
    - Cross-disciplinary integration
    - Personalized recommendations
    """

    def __init__(self):
        self._paths = LEARNING_PATHS
        self._user_progress: Dict[str, Dict[str, UserPathProgress]] = {}

    def get_all_paths(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all available learning paths."""
        results = []

        for path_id, path_data in self._paths.items():
            # Filter by category
            if category and path_data["category"].value != category:
                continue
            # Filter by difficulty
            if difficulty and path_data["difficulty"].value != difficulty:
                continue

            total_lessons = sum(
                len(m["lessons"]) for m in path_data["modules"]
            )

            results.append({
                "path_id": path_id,
                "title_ar": path_data["title_ar"],
                "title_en": path_data["title_en"],
                "description_en": path_data["description_en"],
                "category": path_data["category"].value,
                "difficulty": path_data["difficulty"].value,
                "estimated_hours": path_data["estimated_hours"],
                "disciplines": path_data["disciplines"],
                "tags": path_data["tags"],
                "module_count": len(path_data["modules"]),
                "lesson_count": total_lessons,
            })

        return results

    def get_path_details(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a learning path."""
        if path_id not in self._paths:
            return None

        path_data = self._paths[path_id]

        modules = []
        for m in path_data["modules"]:
            lessons = []
            for l in m["lessons"]:
                lessons.append({
                    "lesson_id": l["lesson_id"],
                    "title_ar": l["title_ar"],
                    "title_en": l["title_en"],
                    "lesson_type": l["lesson_type"].value if isinstance(l["lesson_type"], LessonType) else l["lesson_type"],
                    "duration_minutes": l["duration_minutes"],
                    "objectives": l["objectives"],
                })

            modules.append({
                "module_id": m["module_id"],
                "title_ar": m["title_ar"],
                "title_en": m["title_en"],
                "description_en": m["description_en"],
                "prerequisites": m["prerequisites"],
                "learning_outcomes": m["learning_outcomes"],
                "lessons": lessons,
                "lesson_count": len(lessons),
            })

        return {
            "path_id": path_id,
            "title_ar": path_data["title_ar"],
            "title_en": path_data["title_en"],
            "description_ar": path_data["description_ar"],
            "description_en": path_data["description_en"],
            "category": path_data["category"].value,
            "difficulty": path_data["difficulty"].value,
            "estimated_hours": path_data["estimated_hours"],
            "disciplines": path_data["disciplines"],
            "tags": path_data["tags"],
            "modules": modules,
        }

    def get_lesson_content(
        self,
        path_id: str,
        module_id: str,
        lesson_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed lesson content."""
        if path_id not in self._paths:
            return None

        path_data = self._paths[path_id]

        for module in path_data["modules"]:
            if module["module_id"] == module_id:
                for lesson in module["lessons"]:
                    if lesson["lesson_id"] == lesson_id:
                        return {
                            "path_id": path_id,
                            "module_id": module_id,
                            "lesson_id": lesson_id,
                            "title_ar": lesson["title_ar"],
                            "title_en": lesson["title_en"],
                            "lesson_type": lesson["lesson_type"].value if isinstance(lesson["lesson_type"], LessonType) else lesson["lesson_type"],
                            "duration_minutes": lesson["duration_minutes"],
                            "content": lesson["content"],
                            "objectives": lesson["objectives"],
                            "resources": lesson["resources"],
                        }

        return None

    def enroll_in_path(
        self,
        user_id: str,
        path_id: str,
    ) -> Dict[str, Any]:
        """Enroll a user in a learning path."""
        if path_id not in self._paths:
            return {"error": f"Path '{path_id}' not found"}

        if user_id not in self._user_progress:
            self._user_progress[user_id] = {}

        if path_id in self._user_progress[user_id]:
            return {"error": "Already enrolled in this path"}

        path_data = self._paths[path_id]

        progress = UserPathProgress(
            user_id=user_id,
            path_id=path_id,
            started_at=datetime.now(),
            current_module=0,
            current_lesson=0,
            lessons_completed=[],
            milestones=[],
            quiz_scores={},
            reflections=[],
            completion_percent=0.0,
        )

        self._user_progress[user_id][path_id] = progress

        return {
            "enrolled": True,
            "path_id": path_id,
            "path_title_en": path_data["title_en"],
            "first_module": path_data["modules"][0]["title_en"],
            "first_lesson": path_data["modules"][0]["lessons"][0]["title_en"],
            "message_ar": "تم التسجيل في المسار بنجاح",
            "message_en": "Successfully enrolled in the learning path",
        }

    def complete_lesson(
        self,
        user_id: str,
        path_id: str,
        lesson_id: str,
    ) -> Dict[str, Any]:
        """Mark a lesson as complete."""
        if user_id not in self._user_progress:
            return {"error": "Not enrolled in any paths"}

        if path_id not in self._user_progress[user_id]:
            return {"error": "Not enrolled in this path"}

        progress = self._user_progress[user_id][path_id]
        path_data = self._paths[path_id]

        if lesson_id in progress.lessons_completed:
            return {"error": "Lesson already completed"}

        progress.lessons_completed.append(lesson_id)

        # Add milestone
        progress.milestones.append({
            "type": MilestoneType.LESSON_COMPLETE.value,
            "lesson_id": lesson_id,
            "timestamp": datetime.now().isoformat(),
        })

        # Calculate completion
        total_lessons = sum(len(m["lessons"]) for m in path_data["modules"])
        progress.completion_percent = (len(progress.lessons_completed) / total_lessons) * 100

        # Check if module complete
        current_module = path_data["modules"][progress.current_module]
        module_lessons = [l["lesson_id"] for l in current_module["lessons"]]
        module_completed = all(l in progress.lessons_completed for l in module_lessons)

        if module_completed:
            progress.milestones.append({
                "type": MilestoneType.MODULE_COMPLETE.value,
                "module_id": current_module["module_id"],
                "timestamp": datetime.now().isoformat(),
            })

            # Move to next module
            if progress.current_module < len(path_data["modules"]) - 1:
                progress.current_module += 1
                progress.current_lesson = 0

        # Check if path complete
        if progress.completion_percent >= 100:
            progress.milestones.append({
                "type": MilestoneType.PATH_COMPLETE.value,
                "timestamp": datetime.now().isoformat(),
            })

        return {
            "completed": True,
            "lesson_id": lesson_id,
            "completion_percent": round(progress.completion_percent, 1),
            "module_completed": module_completed,
            "path_completed": progress.completion_percent >= 100,
            "milestones_earned": len(progress.milestones),
        }

    def get_user_progress(
        self,
        user_id: str,
        path_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get user's progress in learning paths."""
        if user_id not in self._user_progress:
            return {
                "user_id": user_id,
                "enrolled_paths": 0,
                "paths": [],
            }

        user_data = self._user_progress[user_id]

        if path_id:
            if path_id not in user_data:
                return {"error": "Not enrolled in this path"}

            progress = user_data[path_id]
            path_data = self._paths[path_id]

            return {
                "path_id": path_id,
                "path_title_en": path_data["title_en"],
                "started_at": progress.started_at.isoformat(),
                "current_module": progress.current_module,
                "current_lesson": progress.current_lesson,
                "lessons_completed": len(progress.lessons_completed),
                "total_lessons": sum(len(m["lessons"]) for m in path_data["modules"]),
                "completion_percent": round(progress.completion_percent, 1),
                "milestones": progress.milestones,
                "quiz_scores": progress.quiz_scores,
            }

        # Return all paths progress
        paths_progress = []
        for pid, prog in user_data.items():
            path_data = self._paths.get(pid, {})
            paths_progress.append({
                "path_id": pid,
                "path_title_en": path_data.get("title_en", "Unknown"),
                "completion_percent": round(prog.completion_percent, 1),
                "lessons_completed": len(prog.lessons_completed),
            })

        return {
            "user_id": user_id,
            "enrolled_paths": len(user_data),
            "paths": paths_progress,
        }

    def get_recommended_paths(
        self,
        user_id: str,
        interests: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get personalized path recommendations."""
        recommendations = []

        # Get user's completed paths
        completed_paths = set()
        if user_id in self._user_progress:
            for pid, prog in self._user_progress[user_id].items():
                if prog.completion_percent >= 100:
                    completed_paths.add(pid)

        for path_id, path_data in self._paths.items():
            # Skip completed paths
            if path_id in completed_paths:
                continue

            # Filter by difficulty
            if difficulty and path_data["difficulty"].value != difficulty:
                continue

            score = 0.5  # Base score

            # Boost for matching interests
            if interests:
                matching_tags = set(interests).intersection(set(path_data["tags"]))
                score += len(matching_tags) * 0.1

            recommendations.append({
                "path_id": path_id,
                "title_en": path_data["title_en"],
                "title_ar": path_data["title_ar"],
                "category": path_data["category"].value,
                "difficulty": path_data["difficulty"].value,
                "relevance_score": round(score, 2),
                "estimated_hours": path_data["estimated_hours"],
                "tags": path_data["tags"],
            })

        # Sort by relevance
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:5]

    def get_path_categories(self) -> List[Dict[str, str]]:
        """Get all path categories."""
        return [
            {"id": c.value, "name_en": self._get_category_name(c)}
            for c in PathCategory
        ]

    def get_difficulty_levels(self) -> List[Dict[str, str]]:
        """Get all difficulty levels."""
        return [
            {"id": d.value, "name_en": d.value.capitalize(), "description": self._get_difficulty_desc(d)}
            for d in PathDifficulty
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning path statistics."""
        total_lessons = 0
        total_hours = 0
        category_counts = defaultdict(int)

        for path_data in self._paths.values():
            total_lessons += sum(len(m["lessons"]) for m in path_data["modules"])
            total_hours += path_data["estimated_hours"]
            category_counts[path_data["category"].value] += 1

        return {
            "total_paths": len(self._paths),
            "total_lessons": total_lessons,
            "total_hours": total_hours,
            "categories": dict(category_counts),
            "enrolled_users": len(self._user_progress),
        }

    def _get_category_name(self, category: PathCategory) -> str:
        """Get display name for category."""
        names = {
            PathCategory.FOUNDATIONAL: "Foundational Studies",
            PathCategory.THEMATIC: "Thematic Studies",
            PathCategory.PROPHET_STUDY: "Prophet Studies",
            PathCategory.JURISPRUDENCE: "Islamic Jurisprudence",
            PathCategory.SPIRITUALITY: "Spiritual Development",
            PathCategory.RESEARCH: "Research & Academic",
        }
        return names.get(category, category.value)

    def _get_difficulty_desc(self, difficulty: PathDifficulty) -> str:
        """Get description for difficulty level."""
        descs = {
            PathDifficulty.BEGINNER: "No prior knowledge required",
            PathDifficulty.INTERMEDIATE: "Basic Islamic knowledge helpful",
            PathDifficulty.ADVANCED: "Requires foundational understanding",
            PathDifficulty.SCHOLAR: "For advanced students and researchers",
        }
        return descs.get(difficulty, "")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

learning_path_service = LearningPathService()
