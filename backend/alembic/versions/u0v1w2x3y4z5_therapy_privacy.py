"""Therapy sessions: stop keeping users' messages

user_message was written on every guidance request and never read. It is no
longer stored; this makes the column nullable and erases what was kept.

Revision ID: u0v1w2x3y4z5
Revises: t9u0v1w2x3y4
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "u0v1w2x3y4z5"
down_revision: Union[str, None] = "t9u0v1w2x3y4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE therapy_sessions ALTER COLUMN user_message DROP NOT NULL")
    op.execute("UPDATE therapy_sessions SET user_message = NULL")


def downgrade() -> None:
    # The erased messages cannot be restored; keep the column nullable.
    pass
