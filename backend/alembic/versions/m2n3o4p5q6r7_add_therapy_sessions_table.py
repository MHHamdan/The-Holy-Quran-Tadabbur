"""Add therapy_sessions table (Phase T — Spiritual Guidance & Emotional Support)

Revision ID: m2n3o4p5q6r7
Revises: l1m2n3o4p5q6
Create Date: 2026-05-09

Stores user emotional support sessions, emotion classifications, and
the Quranic verses shown during healing interactions.

Pure-SQL so CREATE TABLE/INDEX IF NOT EXISTS is idempotent on re-run.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'm2n3o4p5q6r7'
down_revision: Union[str, None] = 'l1m2n3o4p5q6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS therapy_sessions (
            id              SERIAL PRIMARY KEY,

            -- Session identification
            session_id      VARCHAR(36)  NOT NULL UNIQUE,

            -- Emotional classification
            emotion         VARCHAR(30)  NOT NULL,
            theme           VARCHAR(30),

            -- User input
            user_message    TEXT         NOT NULL,

            -- Guidance delivered
            verses_shown    TEXT,               -- JSON list: ["94:5", "2:286", ...]
            reflection_logged TEXT,

            -- Locale
            language        VARCHAR(5)   NOT NULL DEFAULT 'en',

            created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_therapy_session_id
            ON therapy_sessions (session_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_therapy_emotion
            ON therapy_sessions (emotion)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_therapy_created
            ON therapy_sessions (created_at)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS therapy_sessions CASCADE")
