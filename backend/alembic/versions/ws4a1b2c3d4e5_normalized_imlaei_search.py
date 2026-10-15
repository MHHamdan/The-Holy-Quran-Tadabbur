"""Search keys: text_imlaei_normalized + shared normalizer backfill + trigram indexes

Adds quran_verses.text_imlaei_normalized and (re)fills both derived search
columns — text_normalized (from text_uthmani) and text_imlaei_normalized
(from text_imlaei) — with app.services.arabic_normalize.normalize_for_search,
the one normalizer the seeder, the search services and query terms share.
The canonical text columns (text_uthmani, text_imlaei) are only read.

Also adds:
  * a GIN trigram index on text_imlaei_normalized, so ILIKE over both
    normalized columns is a BitmapOr of two index scans instead of a
    sequential scan with regexp_replace on every row;
  * a GIN trigram index on the transliteration-folded translation text used
    by /quran/search/translation (pg_trgm serves its ~ word-start regex).

Idempotent: IF NOT EXISTS everywhere; re-running the backfill is harmless.

Revision ID: ws4a1b2c3d4e5
Revises: u0v1w2x3y4z5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ws4a1b2c3d4e5"
down_revision: Union[str, None] = "u0v1w2x3y4z5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fold_sql_literals() -> tuple[str, str]:
    from app.services.arabic_normalize import TRANSLIT_FOLD_FROM, TRANSLIT_FOLD_TO

    def lit(s: str) -> str:
        return "'" + s.replace("'", "''") + "'"

    return lit(TRANSLIT_FOLD_FROM), lit(TRANSLIT_FOLD_TO)


def upgrade() -> None:
    from app.services.arabic_normalize import normalize_for_search

    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("ALTER TABLE quran_verses ADD COLUMN IF NOT EXISTS text_imlaei_normalized TEXT")

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, text_uthmani, text_imlaei FROM quran_verses")).all()
    if rows:
        bind.execute(
            sa.text(
                "UPDATE quran_verses SET text_normalized = :n, text_imlaei_normalized = :m "
                "WHERE id = :i"
            ),
            [
                {
                    "i": r.id,
                    "n": normalize_for_search(r.text_uthmani or ""),
                    "m": normalize_for_search(r.text_imlaei or r.text_uthmani or ""),
                }
                for r in rows
            ],
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_quran_imlaei_norm_trgm "
        "ON quran_verses USING GIN (text_imlaei_normalized gin_trgm_ops)"
    )
    fold_from, fold_to = _fold_sql_literals()
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_translations_folded_trgm ON translations "
        f"USING GIN (lower(translate(text, {fold_from}, {fold_to})) gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_translations_folded_trgm")
    op.execute("DROP INDEX IF EXISTS idx_quran_imlaei_norm_trgm")
    op.execute("ALTER TABLE quran_verses DROP COLUMN IF EXISTS text_imlaei_normalized")
