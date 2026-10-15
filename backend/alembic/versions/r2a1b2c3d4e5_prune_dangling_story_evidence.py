"""Stories: drop evidence links to tafsir chunks that no longer exist

scripts/ingest/resolve_story_evidence.py linked story_segments and
cross_story_connections to tafseer_chunks ids. Migration ws3b2c3d4e5f6 later
deleted the 99 'no tafsir for this verse' placeholder chunks (qurtubi_ar,
ibn_kathir_ar), so a few evidence ids now point at nothing (11 segments and
2 cross-story connections on the dev database). Those placeholder rows held
no commentary, so the links carried no evidence; they are removed, never
redirected. A segment left with no evidence gets NULL; a cross-story
connection keeps its array unless it would become empty (its CHECK requires
at least one id), in which case it is left for the resolver to rebuild.

Idempotent: safe to re-run. Not reversible (the targets no longer exist).

Revision ID: r2a1b2c3d4e5
Revises: ws5a1b2c3d4e5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r2a1b2c3d4e5"
down_revision: Union[str, None] = "ws5a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_KEPT = """
ARRAY(SELECT x FROM unnest({t}.evidence_chunk_ids) WITH ORDINALITY AS u(x, n)
       WHERE EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = u.x)
       ORDER BY u.n)
"""

_DANGLING = """
EXISTS (SELECT 1 FROM unnest({t}.evidence_chunk_ids) AS u(x)
         WHERE NOT EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = u.x))
"""

UPGRADE_SQL = [
    f"""
    UPDATE story_segments
       SET evidence_chunk_ids = NULLIF({_KEPT.format(t='story_segments')}, ARRAY[]::varchar[])
     WHERE evidence_chunk_ids IS NOT NULL
       AND {_DANGLING.format(t='story_segments')}
    """,
    f"""
    UPDATE cross_story_connections
       SET evidence_chunk_ids = {_KEPT.format(t='cross_story_connections')}
     WHERE {_DANGLING.format(t='cross_story_connections')}
       AND cardinality({_KEPT.format(t='cross_story_connections')}) > 0
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    # The removed ids pointed at deleted placeholder rows; nothing to restore.
    pass
