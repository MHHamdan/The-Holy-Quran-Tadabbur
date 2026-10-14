"""Add the Bismillah of each surah's first verse (Tanzil keeps it apart from the verse)

The canonical text is now Tanzil's (CC BY 3.0). Unlike the previous KFGQPC
file, Tanzil does not inline the opening Bismillah into verse 1; it gives it
separately. Storing it separately lets the readers show it as the surah
heading without splitting verse text.

Revision ID: t9u0v1w2x3y4
Revises: s8t9u0v1w2x3
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "t9u0v1w2x3y4"
down_revision: Union[str, None] = "s8t9u0v1w2x3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE quran_verses ADD COLUMN IF NOT EXISTS bismillah_uthmani TEXT")
    op.execute("ALTER TABLE quran_verses ADD COLUMN IF NOT EXISTS bismillah_imlaei TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE quran_verses DROP COLUMN IF EXISTS bismillah_imlaei")
    op.execute("ALTER TABLE quran_verses DROP COLUMN IF EXISTS bismillah_uthmani")
