"""Story-atlas event evidence cites only enabled, licence-verified tafsir

story_events.evidence held 62 pointers to the disabled, blocked English Ibn
Kathir ({"source_id": "ibn_kathir_en", "reference": "18:71"}), served by
GET /api/v1/story-atlas/{cluster} and shown as "In tafsir: Tafsir Ibn Kathir
(English)". The English text is a translation of the Arabic tafsir, so each
pointer is moved to the Arabic original of the same work (ibn_kathir_ar) at
the same verse reference, but only when an enabled, licence-verified
ibn_kathir_ar chunk covers that verse. A pointer that does not resolve to an
enabled, licensed chunk of its source (or of the same work's Arabic edition)
is dropped. No snippet text is kept or created: evidence is a pointer, the
tafsir text is read from tafseer_chunks.

Idempotent: only rows whose evidence still changes are touched.

Revision ID: r4a1b2c3d4e5
Revises: r3d1a2b3c4d5
Create Date: 2026-10-15
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r4a1b2c3d4e5"
down_revision: Union[str, None] = "r3d1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# One pointer, remapped to the same work's enabled edition and reduced to its
# public keys; NULL when it does not resolve to an enabled, licensed chunk.
_RESOLVED = r"""
(SELECT jsonb_strip_nulls(jsonb_build_object(
          'source_id', x.src,
          'reference', x.ref,
          'chunk_id', CASE WHEN x.src = e->>'source_id' THEN e->>'chunk_id' END))
   FROM (SELECT CASE WHEN e->>'source_id' = 'ibn_kathir_en' THEN 'ibn_kathir_ar'
                     ELSE e->>'source_id' END AS src,
                e->>'reference' AS ref,
                regexp_match(e->>'reference', '^(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?$') AS m) x
  WHERE EXISTS (SELECT 1 FROM tafseer_sources s
                 WHERE s.id = x.src AND s.is_enabled = 1 AND s.license_verified = 1)
    AND CASE WHEN x.src = e->>'source_id' AND e ? 'chunk_id'
             THEN EXISTS (SELECT 1 FROM tafseer_chunks c
                           WHERE c.chunk_id = e->>'chunk_id' AND c.source_id = x.src)
             ELSE x.m IS NOT NULL
                  AND EXISTS (SELECT 1 FROM tafseer_chunks c
                               WHERE c.source_id = x.src
                                 AND c.sura_no = x.m[1]::int
                                 AND c.aya_start <= COALESCE(x.m[3], x.m[2])::int
                                 AND c.aya_end >= x.m[2]::int) END)
"""

_NEW_EVIDENCE = f"""
COALESCE((SELECT jsonb_agg(r.v ORDER BY r.n)
            FROM (SELECT {_RESOLVED} AS v, n
                    FROM jsonb_array_elements(se.evidence) WITH ORDINALITY AS t(e, n)) r
           WHERE r.v IS NOT NULL), '[]'::jsonb)
"""

UPGRADE_SQL = [
    f"""
    UPDATE story_events se
       SET evidence = {_NEW_EVIDENCE}
     WHERE jsonb_typeof(se.evidence) = 'array'
       AND se.evidence IS DISTINCT FROM {_NEW_EVIDENCE}
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    # The dropped pointers cited an unlicensed source; they are not restored.
    pass
