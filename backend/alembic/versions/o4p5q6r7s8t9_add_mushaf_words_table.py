"""Add mushaf_words table — word-level page/line layout for King Fahd Mushaf

Revision ID: o4p5q6r7s8t9
Revises: n3o4p5q6r7s8
Create Date: 2026-06-19

Stores the canonical word-to-page-line assignments from the King Fahd
Madinah Mushaf (604-page edition).  Data source: qurancdn.com API which
exposes the same page/line layout used on quran.com.

Each row is one word (or verse-end marker) with its physical location
on the printed page.  Enables pixel-faithful line-by-line rendering.
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'o4p5q6r7s8t9'
down_revision: Union[str, None] = 'n3o4p5q6r7s8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS mushaf_words (
            id           SERIAL    PRIMARY KEY,
            page_no      SMALLINT  NOT NULL,
            line_no      SMALLINT  NOT NULL,
            word_order   SMALLINT  NOT NULL,   -- sequential within page (1-based)
            sura_no      SMALLINT  NOT NULL,
            aya_no       SMALLINT  NOT NULL,
            word_pos     SMALLINT  NOT NULL,   -- position within verse (1-based)
            text_uthmani TEXT      NOT NULL,
            char_type    VARCHAR(20) NOT NULL DEFAULT 'word'
                         CHECK (char_type IN ('word','end','hizb','sajda','rub','page'))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_mushaf_words_page_order
            ON mushaf_words (page_no, word_order)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mushaf_words_page_line
            ON mushaf_words (page_no, line_no)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mushaf_words_verse
            ON mushaf_words (sura_no, aya_no)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mushaf_words CASCADE")
