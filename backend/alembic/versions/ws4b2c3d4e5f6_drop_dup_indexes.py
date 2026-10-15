"""Drop six duplicate B-tree indexes

Each of these duplicates another index on the same column(s):

  ix_verse_page        = ix_quran_verses_page_no      (quran_verses.page_no)
  ix_verse_juz         = ix_quran_verses_juz_no       (quran_verses.juz_no)
  ix_verse_sura_aya    = uq_sura_aya (unique)         (quran_verses.sura_no, aya_no)
  ix_translation_lang  = ix_translations_language     (translations.language)
  ix_chunk_source      = ix_tafseer_chunks_source_id  (tafseer_chunks.source_id)
  ix_chunk_sura        = ix_tafseer_chunks_sura_no    (tafseer_chunks.sura_no;
                         ix_chunk_sura_aya also covers the prefix)

They slow writes and reseeds without helping any plan. Idempotent.

Revision ID: ws4b2c3d4e5f6
Revises: ws4a1b2c3d4e5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ws4b2c3d4e5f6"
down_revision: Union[str, None] = "ws4a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DUPLICATES = {
    "ix_verse_page": "quran_verses (page_no)",
    "ix_verse_juz": "quran_verses (juz_no)",
    "ix_verse_sura_aya": "quran_verses (sura_no, aya_no)",
    "ix_translation_lang": "translations (language)",
    "ix_chunk_source": "tafseer_chunks (source_id)",
    "ix_chunk_sura": "tafseer_chunks (sura_no)",
}


def upgrade() -> None:
    for name in _DUPLICATES:
        op.execute(f"DROP INDEX IF EXISTS {name}")


def downgrade() -> None:
    for name, target in _DUPLICATES.items():
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {target}")
