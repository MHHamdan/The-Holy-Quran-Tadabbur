"""Add trigram GIN index on text_normalized for fast ILIKE search

Revision ID: j9k0l1m2n3o4
Revises: i8j9k0l1m2n3
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'j9k0l1m2n3o4'
down_revision: Union[str, None] = 'i8j9k0l1m2n3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add text_normalized column if it doesn't already exist
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE quran_verses ADD COLUMN text_normalized TEXT;
        EXCEPTION WHEN duplicate_column THEN NULL; END $$;
    """)
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    op.execute(
        'CREATE INDEX IF NOT EXISTS idx_quran_text_trgm '
        'ON quran_verses USING GIN (text_normalized gin_trgm_ops);'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_quran_text_trgm;')
    op.execute('ALTER TABLE quran_verses DROP COLUMN IF EXISTS text_normalized;')
