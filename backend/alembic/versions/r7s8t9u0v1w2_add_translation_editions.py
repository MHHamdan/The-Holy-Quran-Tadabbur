"""Add translation_editions catalogue and provenance columns on translations

The reader shipped with an empty translations table. Translations are now
ingested verbatim from QuranEnc.com, whose republication terms require the
edition version and footnotes to travel with the text, so:

- translation_editions: one row per ingested edition (key, language, title,
  version, licence and attribution)
- translations: source_id, edition_version, footnotes

Additive and idempotent (IF NOT EXISTS) so it is safe on databases restored
from the data bundle.

Revision ID: r7s8t9u0v1w2
Revises: q6r7s8t9u0v1
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r7s8t9u0v1w2"
down_revision: Union[str, None] = "q6r7s8t9u0v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS translation_editions (
            key VARCHAR(100) PRIMARY KEY,
            language VARCHAR(10) NOT NULL,
            title VARCHAR(255) NOT NULL,
            translator_name VARCHAR(255),
            version VARCHAR(32) NOT NULL,
            source_id VARCHAR(50) NOT NULL,
            source_url VARCHAR(500) NOT NULL,
            license VARCHAR(255) NOT NULL,
            attribution TEXT NOT NULL,
            verse_count INTEGER NOT NULL DEFAULT 0,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            fetched_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_translation_editions_language "
        "ON translation_editions (language)"
    )
    op.execute("ALTER TABLE translations ADD COLUMN IF NOT EXISTS source_id VARCHAR(50)")
    op.execute("ALTER TABLE translations ADD COLUMN IF NOT EXISTS edition_version VARCHAR(32)")
    op.execute("ALTER TABLE translations ADD COLUMN IF NOT EXISTS footnotes TEXT")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_translation_translator "
        "ON translations (translator)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_translation_translator")
    op.execute("ALTER TABLE translations DROP COLUMN IF EXISTS footnotes")
    op.execute("ALTER TABLE translations DROP COLUMN IF EXISTS edition_version")
    op.execute("ALTER TABLE translations DROP COLUMN IF EXISTS source_id")
    op.execute("DROP INDEX IF EXISTS ix_translation_editions_language")
    op.execute("DROP TABLE IF EXISTS translation_editions")
