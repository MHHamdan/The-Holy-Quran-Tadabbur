"""Tafsir provenance and story evidence from enabled sources only

1. tafseer_sources.source_url was NULL for every row. It is set to the row's
   cdn_url: the URL the stored chunks were actually fetched from (the seeder
   writes cdn_url and data_hash together and never re-inserts an existing
   chunk, so cdn_url always describes the text in tafseer_chunks).
2. muyassar_ar: the DB said 'educational_use', the manifest
   'publisher_terms_non_commercial' and the registry 'waqf, no restrictive
   terms'. The DB now carries the manifest's statement: displayed with
   attribution for non-commercial use under docs/distribution-policy.md, the
   King Fahd Complex terms pending owner confirmation. is_enabled and
   license_verified are not touched (owner decision 2026-10-14).
3. Story evidence: chunk ids of disabled sources (the unlicensed English
   tafsir) are removed from story_segments and cross_story_connections. A
   segment left with none gets NULL; a cross-story connection is only
   rewritten when at least one id remains (its CHECK needs one).
4. story_connections held legacy pseudo ids ('ibn_kathir_en:18:83-84') that
   resolve to nothing. Each is re-derived by its verse reference to the real
   chunks of the enabled edition of the same work (ibn_kathir_en ->
   ibn_kathir_ar, tabari_ar -> tabari_ar). Another scholar is never
   substituted; a row with nothing to re-derive keeps its ids, which the API
   no longer exposes.
5. story_segments.evidence_sources references to ibn_kathir_en point at the
   Arabic original of the same work (verse reference only, no text), and any
   'snippet' key is removed: those were unsourced paraphrases presented as
   quotations.
6. theme_segments cited legacy pseudo ids ('ibn_kathir:112:1') that resolve
   to nothing. They are re-derived the same way (same work, enabled edition,
   by verse reference).
7. theme_segments.evidence_sources loses its hand-typed 'snippet' (several
   were Qur'an text typed from memory, presented as tafsir quotations); a
   pseudo chunk_id becomes a plain verse 'reference'.
theme_consequences cite 'consequence:...' ids with no source to re-derive
from; the API no longer serves a consequence without real evidence.

Idempotent: every statement only touches rows that still need it.

Revision ID: r3d1a2b3c4d5
Revises: r3b1c2d3e4f5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r3d1a2b3c4d5"
down_revision: Union[str, None] = "r3b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# tafseer_sources.license is varchar(200).
MUYASSAR_LICENSE = (
    "King Fahd Complex: attributed, non-commercial display under "
    "docs/distribution-policy.md; KFGQPC terms pending owner confirmation, not cleared"
)
assert len(MUYASSAR_LICENSE) <= 200

_ENABLED_CHUNK = """
EXISTS (SELECT 1 FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id
         WHERE c.chunk_id = {x} AND s.is_enabled = 1 AND s.license_verified = 1)
"""

_DISABLED_CHUNK = """
EXISTS (SELECT 1 FROM tafseer_chunks c JOIN tafseer_sources s ON s.id = c.source_id
         WHERE c.chunk_id = {x} AND NOT (s.is_enabled = 1 AND s.license_verified = 1))
"""

_KEPT = """
ARRAY(SELECT u.x FROM unnest({t}.evidence_chunk_ids) WITH ORDINALITY AS u(x, n)
       WHERE NOT """ + _DISABLED_CHUNK.format(x="u.x") + """
       ORDER BY u.n)
"""

_HAS_DISABLED = """
EXISTS (SELECT 1 FROM unnest({t}.evidence_chunk_ids) AS u(x)
         WHERE """ + _DISABLED_CHUNK.format(x="u.x") + """)
"""

# Verse-reference re-derivation of a legacy pseudo id 'work_lang:S:A[-B]'.
_REDERIVED = """
ARRAY(
  SELECT c.chunk_id
    FROM unnest(sc.evidence_chunk_ids) AS u(x)
    CROSS JOIN LATERAL regexp_match(u.x, '^([a-z_]+?)_(ar|en):(\\d{1,3}):(\\d{1,3})(?:-(\\d{1,3}))?$') AS m
    JOIN tafseer_sources s
      ON s.id IN (m[1] || '_ar', m[1] || '_en') AND s.is_enabled = 1 AND s.license_verified = 1
    JOIN tafseer_chunks c
      ON c.source_id = s.id
     AND c.sura_no = m[3]::int
     AND c.aya_start <= COALESCE(m[5], m[4])::int
     AND c.aya_end >= m[4]::int
   GROUP BY c.chunk_id
   ORDER BY min(c.aya_start), c.chunk_id
)
"""

_THEME_REDERIVED = """
ARRAY(
  SELECT c.chunk_id
    FROM unnest(ts.evidence_chunk_ids) AS u(x)
    CROSS JOIN LATERAL regexp_match(u.x, '^([a-z_]+):(\\d{1,3}):(\\d{1,3})(?:-(\\d{1,3}))?$') AS m
    JOIN tafseer_sources s
      ON s.id IN (m[1], m[1] || '_ar', m[1] || '_en') AND s.is_enabled = 1 AND s.license_verified = 1
    JOIN tafseer_chunks c
      ON c.source_id = s.id
     AND c.sura_no = m[2]::int
     AND c.aya_start <= COALESCE(m[4], m[3])::int
     AND c.aya_end >= m[3]::int
   GROUP BY c.chunk_id
   ORDER BY min(c.aya_start), c.chunk_id
)
"""

UPGRADE_SQL = [
    # 1. source_url
    """
    UPDATE tafseer_sources SET source_url = cdn_url
     WHERE source_url IS NULL AND cdn_url LIKE 'http%'
    """,
    # 2. muyassar_ar licence statement
    f"""
    UPDATE tafseer_sources
       SET license_type = 'publisher_terms_non_commercial',
           license = '{MUYASSAR_LICENSE}'
     WHERE id = 'muyassar_ar'
       AND (license_type IS DISTINCT FROM 'publisher_terms_non_commercial'
            OR license IS DISTINCT FROM '{MUYASSAR_LICENSE}')
    """,
    # 3. prune disabled-source chunk ids
    f"""
    UPDATE story_segments
       SET evidence_chunk_ids = NULLIF({_KEPT.format(t='story_segments')}, ARRAY[]::varchar[])
     WHERE evidence_chunk_ids IS NOT NULL
       AND {_HAS_DISABLED.format(t='story_segments')}
    """,
    f"""
    UPDATE cross_story_connections
       SET evidence_chunk_ids = {_KEPT.format(t='cross_story_connections')}
     WHERE {_HAS_DISABLED.format(t='cross_story_connections')}
       AND cardinality({_KEPT.format(t='cross_story_connections')}) > 0
    """,
    # 4. re-derive story_connections pseudo ids by verse reference
    f"""
    UPDATE story_connections sc
       SET evidence_chunk_ids = {_REDERIVED}
     WHERE EXISTS (SELECT 1 FROM unnest(sc.evidence_chunk_ids) AS u(x)
                    WHERE NOT {_ENABLED_CHUNK.format(x='u.x')})
       AND cardinality({_REDERIVED}) > 0
    """,
    # 5. evidence_sources: ibn_kathir_en -> ibn_kathir_ar, drop snippets
    """
    UPDATE story_segments
       SET evidence_sources = (
             SELECT jsonb_agg(
                      CASE WHEN e->>'source_id' = 'ibn_kathir_en'
                           THEN jsonb_set(e - 'snippet', '{source_id}', '"ibn_kathir_ar"')
                           ELSE e - 'snippet' END
                      ORDER BY n)
               FROM jsonb_array_elements(evidence_sources) WITH ORDINALITY AS t(e, n))
     WHERE jsonb_typeof(evidence_sources) = 'array'
       AND jsonb_array_length(evidence_sources) > 0
       AND (evidence_sources @> '[{"source_id": "ibn_kathir_en"}]'
            OR EXISTS (SELECT 1 FROM jsonb_array_elements(evidence_sources) e WHERE e ? 'snippet'))
    """,
    # 6. theme_segments: legacy pseudo ids 'work:S:A' -> real chunks of the
    #    enabled edition of the same work, by verse reference
    f"""
    UPDATE theme_segments ts
       SET evidence_chunk_ids = {_THEME_REDERIVED}
     WHERE ts.evidence_chunk_ids IS NOT NULL
       AND EXISTS (SELECT 1 FROM unnest(ts.evidence_chunk_ids) AS u(x)
                    WHERE NOT {_ENABLED_CHUNK.format(x='u.x')})
       AND cardinality({_THEME_REDERIVED}) > 0
    """,
    # 7. theme_segments.evidence_sources: drop hand-typed snippets; a pseudo
    #    chunk_id becomes a plain verse reference
    """
    UPDATE theme_segments
       SET evidence_sources = (
             SELECT jsonb_agg(
                      CASE WHEN e ? 'chunk_id'
                                AND NOT EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = e->>'chunk_id')
                           THEN (e - 'snippet' - 'chunk_id')
                                || jsonb_build_object('reference',
                                     substring(e->>'chunk_id' from '(\\d{1,3}:\\d{1,3}(?:-\\d{1,3})?)$'))
                           ELSE e - 'snippet' END
                      ORDER BY n)
               FROM jsonb_array_elements(evidence_sources) WITH ORDINALITY AS t(e, n))
     WHERE jsonb_typeof(evidence_sources) = 'array'
       AND jsonb_array_length(evidence_sources) > 0
       AND EXISTS (SELECT 1 FROM jsonb_array_elements(evidence_sources) e
                    WHERE e ? 'snippet'
                       OR (e ? 'chunk_id'
                           AND NOT EXISTS (SELECT 1 FROM tafseer_chunks c WHERE c.chunk_id = e->>'chunk_id')))
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    # Pruned ids pointed at unlicensed text and the pseudo ids resolved to
    # nothing; neither is restored.
    pass
