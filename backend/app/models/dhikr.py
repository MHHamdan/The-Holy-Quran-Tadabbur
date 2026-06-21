"""Dhikr session model — tracks anonymous community session completions."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from app.db.database import Base


class DhikrSession(Base):
    __tablename__ = 'dhikr_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_date = Column(String(10), nullable=False)          # YYYY-MM-DD
    category = Column(String(50), nullable=True)               # 'morning', 'evening', 'all', …
    total_dhikr_completed = Column(Integer, nullable=False, default=0)
    total_count = Column(Integer, nullable=False, default=0)   # sum of all individual counts
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_dhikr_sessions_date', 'session_date'),
    )
