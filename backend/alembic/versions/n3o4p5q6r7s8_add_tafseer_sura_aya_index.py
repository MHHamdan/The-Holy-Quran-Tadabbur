"""Add composite index on tafseer_chunks(sura_no, aya_start, aya_end)

Revision ID: n3o4p5q6r7s8
Revises: m2n3o4p5q6r7
Create Date: 2026-05-14

Speeds up the direct-verse-lookup fast path in the RAG pipeline, which
filters tafseer_chunks by (sura_no, aya_start, aya_end) on every verse
reference query.  PostgreSQL can now satisfy the range predicate via a
single composite index scan instead of a full sura_no index scan + filter.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'n3o4p5q6r7s8'
down_revision: Union[str, None] = 'm2n3o4p5q6r7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_chunk_sura_aya
        ON tafseer_chunks (sura_no, aya_start, aya_end);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunk_sura_aya;")
