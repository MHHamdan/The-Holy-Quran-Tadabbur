"""Add user_feedback table (Phase G)

Revision ID: k0l1m2n3o4p5
Revises: j9k0l1m2n3o4
Create Date: 2026-05-09

Pure-SQL implementation so CREATE TABLE/INDEX IF NOT EXISTS makes every
statement safe to re-run after a partial failure.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'k0l1m2n3o4p5'
down_revision: Union[str, None] = 'j9k0l1m2n3o4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id          SERIAL PRIMARY KEY,
            category    VARCHAR(50)  NOT NULL,
            entity_type VARCHAR(50),
            entity_id   VARCHAR(200),
            page_url    VARCHAR(500),
            message     TEXT         NOT NULL,
            status      VARCHAR(20)  NOT NULL DEFAULT 'open',
            priority    INTEGER      NOT NULL DEFAULT 5,
            admin_notes TEXT,
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            resolved_at TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS ix_user_feedback_category
            ON user_feedback (category);
        CREATE INDEX IF NOT EXISTS ix_user_feedback_entity_type
            ON user_feedback (entity_type);
        CREATE INDEX IF NOT EXISTS ix_user_feedback_status
            ON user_feedback (status);
        CREATE INDEX IF NOT EXISTS ix_user_feedback_priority
            ON user_feedback (priority);
        CREATE INDEX IF NOT EXISTS ix_user_feedback_status_priority
            ON user_feedback (status, priority);
        CREATE INDEX IF NOT EXISTS ix_user_feedback_created_at
            ON user_feedback (created_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_feedback;")
