"""RAG keyword retrieval: trigram indexes on tafsir chunk text

The keyword fallback (the only retrieval path while HF embeddings are
unavailable) ranks chunks by how many query keywords they contain, which
needs every matching row. GIN trigram indexes let PostgreSQL answer
``content ILIKE '%kw%'`` from the index instead of scanning all 37k chunks.

Additive and idempotent; built CONCURRENTLY so writes are not blocked.

Revision ID: ws2a1b2c3d4e5
Revises: u0v1w2x3y4z5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ws2a1b2c3d4e5"
down_revision: Union[str, None] = "u0v1w2x3y4z5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tafseer_chunks_content_ar_trgm "
            "ON tafseer_chunks USING gin (content_ar gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tafseer_chunks_content_en_trgm "
            "ON tafseer_chunks USING gin (content_en gin_trgm_ops)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_tafseer_chunks_content_en_trgm")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_tafseer_chunks_content_ar_trgm")
