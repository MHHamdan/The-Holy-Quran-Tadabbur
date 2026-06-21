"""Add dhikr_sessions table (Phase D — Dhikr Enhancement)

Revision ID: p5q6r7s8t9u0
Revises: o4p5q6r7s8t9
Create Date: 2026-06-20

Records anonymous community dhikr session completions for aggregate stats.
No PII stored — sessions are anonymous counts only.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'p5q6r7s8t9u0'
down_revision: Union[str, None] = 'o4p5q6r7s8t9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS dhikr_sessions (
            id                      SERIAL PRIMARY KEY,
            session_date            VARCHAR(10)  NOT NULL,
            category                VARCHAR(50),
            total_dhikr_completed   INTEGER      NOT NULL DEFAULT 0,
            total_count             INTEGER      NOT NULL DEFAULT 0,
            duration_seconds        INTEGER,
            created_at              TIMESTAMP    NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_dhikr_sessions_date
            ON dhikr_sessions (session_date)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dhikr_sessions CASCADE")
