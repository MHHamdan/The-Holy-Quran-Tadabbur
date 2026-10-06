"""Reconcile Tasmee and theme_suggestions schema with the ORM models

The ORM models select columns that no earlier migration created, so every
query on these tables failed on a database built from migrations alone
(e.g. GET /api/v1/tasmee/progress returned 500):

- tasmee_events:      expected_word, verse_sura_no, verse_aya_no, similarity_score
- tasmee_mistakes:    audio_start_time, audio_end_time, corrected_at
                      (+ word columns widened to the model's 200 chars)
- tasmee_progress:    last_attempt_at (backfilled from last_practiced_at),
                      common_mistakes
- theme_suggestions:  origin

Additive and idempotent (IF NOT EXISTS): safe on databases restored from the
data bundle that may already have some of these columns.

Revision ID: q6r7s8t9u0v1
Revises: p5q6r7s8t9u0
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op

revision: str = "q6r7s8t9u0v1"
down_revision: Union[str, None] = "p5q6r7s8t9u0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_ADD = [
    ("tasmee_events", "expected_word", "VARCHAR(100)"),
    ("tasmee_events", "verse_sura_no", "INTEGER"),
    ("tasmee_events", "verse_aya_no", "INTEGER"),
    ("tasmee_events", "similarity_score", "FLOAT"),
    ("tasmee_mistakes", "audio_start_time", "FLOAT"),
    ("tasmee_mistakes", "audio_end_time", "FLOAT"),
    ("tasmee_mistakes", "corrected_at", "TIMESTAMP"),
    ("tasmee_progress", "last_attempt_at", "TIMESTAMP"),
    ("tasmee_progress", "common_mistakes", "JSON"),
    ("theme_suggestions", "origin", "VARCHAR(50) DEFAULT 'auto_discovery'"),
]

_WIDEN = [
    ("tasmee_mistakes", "expected_word"),
    ("tasmee_mistakes", "expected_normalized"),
    ("tasmee_mistakes", "actual_word"),
    ("tasmee_mistakes", "actual_normalized"),
]


def upgrade() -> None:
    for table, column, ddl in _ADD:
        op.execute(f"ALTER TABLE IF EXISTS {table} ADD COLUMN IF NOT EXISTS {column} {ddl}")
    for table, column in _WIDEN:
        op.execute(f"ALTER TABLE IF EXISTS {table} ALTER COLUMN {column} TYPE VARCHAR(200)")

    # Carry existing practice timestamps into the column the model reads.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'tasmee_progress' AND column_name = 'last_practiced_at') THEN
                UPDATE tasmee_progress SET last_attempt_at = last_practiced_at
                WHERE last_attempt_at IS NULL;
            END IF;
        END $$;
    """)
    op.execute("UPDATE theme_suggestions SET origin = 'auto_discovery' WHERE origin IS NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_theme_suggestions_origin ON theme_suggestions (origin)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_theme_suggestions_origin")
    for table, column, _ in reversed(_ADD):
        op.execute(f"ALTER TABLE IF EXISTS {table} DROP COLUMN IF EXISTS {column}")
