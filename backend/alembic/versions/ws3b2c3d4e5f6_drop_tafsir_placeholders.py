"""Tafsir: delete the 'no tafsir for this verse' placeholder rows

99 upstream rows (qurtubi_ar 60, ibn_kathir_ar 39) hold only the placeholder
'لا يوجد تفسير لهذه الأية'. They were stored, embedded and shown as the
scholar's own commentary, and RAG could cite them. The upstream groups
commentary across verses, so those verses have no separate passage in that
source; nothing replaces them. ayah_count is recomputed for the sources
touched. seed_tafseer.py now skips these rows (PLACEHOLDER_TEXTS).

The matching vectors must be dropped from the vector store (or the embed step
re-run for these chunk_ids); see notes for WS2.

Idempotent: safe to re-run. Not reversible (the rows carried no content).

Revision ID: ws3b2c3d4e5f6
Revises: ws3a1b2c3d4e5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ws3b2c3d4e5f6"
down_revision: Union[str, None] = "ws3a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLACEHOLDERS = ("لا يوجد تفسير لهذه الأية", "لا يوجد تفسير لهذه الآية")

UPGRADE_SQL = [
    """
    DELETE FROM tafseer_chunks
     WHERE btrim(content_ar) IN ('لا يوجد تفسير لهذه الأية', 'لا يوجد تفسير لهذه الآية')
    """,
    """
    UPDATE tafseer_sources s
       SET ayah_count = c.n, updated_at = NOW()
      FROM (
            SELECT source_id, COUNT(DISTINCT (sura_no, aya_start)) AS n
              FROM tafseer_chunks
             WHERE source_id IN ('qurtubi_ar', 'ibn_kathir_ar')
             GROUP BY source_id
           ) c
     WHERE s.id = c.source_id
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    # The deleted rows held no commentary; there is nothing to restore.
    pass
