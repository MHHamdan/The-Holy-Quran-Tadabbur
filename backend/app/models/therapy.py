"""
TherapySession model — Phase T: Spiritual Guidance & Emotional Support.

Tracks emotional support sessions, emotion classifications, and
the Quranic verses shown for healing and reflection.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from app.db.database import Base


class EmotionCategory(str, Enum):
    ANXIETY = "anxiety"
    SADNESS = "sadness"
    GRIEF = "grief"
    FEAR = "fear"
    LONELINESS = "loneliness"
    HOPELESSNESS = "hopelessness"
    ANGER = "anger"
    STRESS = "stress"
    GUILT = "guilt"
    DOUBT = "doubt"
    GRATITUDE = "gratitude"
    GENERAL = "general"


EMOTION_LABELS: dict[str, dict[str, str]] = {
    EmotionCategory.ANXIETY:     {"en": "Anxiety",     "ar": "قلق"},
    EmotionCategory.SADNESS:     {"en": "Sadness",     "ar": "حزن"},
    EmotionCategory.GRIEF:       {"en": "Grief",       "ar": "حُزن شديد"},
    EmotionCategory.FEAR:        {"en": "Fear",        "ar": "خوف"},
    EmotionCategory.LONELINESS:  {"en": "Loneliness",  "ar": "وحدة"},
    EmotionCategory.HOPELESSNESS:{"en": "Hopelessness","ar": "يأس"},
    EmotionCategory.ANGER:       {"en": "Anger",       "ar": "غضب"},
    EmotionCategory.STRESS:      {"en": "Stress",      "ar": "ضغط"},
    EmotionCategory.GUILT:       {"en": "Guilt",       "ar": "ذنب"},
    EmotionCategory.DOUBT:       {"en": "Doubt",       "ar": "شك"},
    EmotionCategory.GRATITUDE:   {"en": "Gratitude",   "ar": "شكر"},
    EmotionCategory.GENERAL:     {"en": "General",     "ar": "عام"},
}


class TherapySession(Base):
    __tablename__ = "therapy_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, unique=True, index=True)
    emotion = Column(String(30), nullable=False, index=True)
    theme = Column(String(30), nullable=True)
    user_message = Column(Text, nullable=False)
    verses_shown = Column(Text, nullable=True)  # JSON-serialised list of "surah:ayah" refs
    reflection_logged = Column(Text, nullable=True)
    language = Column(String(5), nullable=False, default="en")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_therapy_emotion", "emotion"),
        Index("ix_therapy_created", "created_at"),
    )
