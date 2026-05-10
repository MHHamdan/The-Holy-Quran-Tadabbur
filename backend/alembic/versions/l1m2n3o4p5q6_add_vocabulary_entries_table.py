"""Add vocabulary_entries table (Phase H — QAC integration)

Revision ID: l1m2n3o4p5q6
Revises: k0l1m2n3o4p5
Create Date: 2026-05-09

Stores word-by-word morphological entries sourced from the Quranic Arabic
Corpus (QAC) and future classical lexicons.  Every entry carries a source_id
that must reference a trusted, verified lexicographic source.

Pure-SQL so CREATE TABLE/INDEX IF NOT EXISTS is idempotent on re-run.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'l1m2n3o4p5q6'
down_revision: Union[str, None] = 'k0l1m2n3o4p5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_entries (
            id              SERIAL PRIMARY KEY,

            -- Verse-word location (matches QAC chapter:verse:word indexing)
            sura_no         SMALLINT  NOT NULL,
            aya_no          SMALLINT  NOT NULL,
            word_position   SMALLINT  NOT NULL,   -- 1-indexed within the verse

            -- Arabic word forms
            word_ar         TEXT      NOT NULL,   -- Full diacritised form
            word_ar_bare    TEXT      NOT NULL,   -- Without diacritics (for search)

            -- Morphology
            root_ar         TEXT,                 -- Trilateral/quadrilateral root in Arabic script
            pattern_ar      TEXT,                 -- Morphological weight pattern (وزن)
            pos_tag         VARCHAR(50),           -- POS tag: اسم / فعل / حرف / ...

            -- Meanings
            meaning_en      TEXT,                 -- English gloss
            meaning_ar      TEXT,                 -- Arabic meaning (from classical lexicon)

            -- Provenance — REQUIRED
            source_id       TEXT      NOT NULL,   -- 'quranic_arabic_corpus' | 'mufradat_al_raghib' | ...

            created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
            reviewed_at     TIMESTAMP,
            reviewer_id     TEXT
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_vocab_location
            ON vocabulary_entries (sura_no, aya_no, word_position)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vocab_root
            ON vocabulary_entries (root_ar)
        WHERE root_ar IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vocab_word_bare
            ON vocabulary_entries (word_ar_bare)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vocab_source
            ON vocabulary_entries (source_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vocabulary_entries CASCADE")
