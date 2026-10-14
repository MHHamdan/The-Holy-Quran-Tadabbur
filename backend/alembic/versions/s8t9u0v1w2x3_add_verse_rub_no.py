"""Add quran_verses.rub_no (hizb quarter 1-240)

hizb_no and sajda_type existed but were never populated. seed_quran.py now
fills all three from data/manifests/quran_structure_markers.json; run
`python scripts/ingest/seed_quran.py --markers-only` on an existing database.

Revision ID: s8t9u0v1w2x3
Revises: r7s8t9u0v1w2
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "s8t9u0v1w2x3"
down_revision: Union[str, None] = "r7s8t9u0v1w2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE quran_verses ADD COLUMN IF NOT EXISTS rub_no INTEGER")


def downgrade() -> None:
    op.execute("ALTER TABLE quran_verses DROP COLUMN IF EXISTS rub_no")
