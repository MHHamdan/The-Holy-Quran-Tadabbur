"""Tafsir: disable the English translations seeded as public domain; add translator

ibn_kathir_en, jalalayn_en and ibn_abbas_en were seeded with
license_type 'public_domain_classical' and license_verified=1 on the strength
of the Arabic authors' death dates. The texts are modern English translations
(the Darussalam abridgement of Ibn Kathir; Feras Hamza's Jalalayn for the
Royal Aal al-Bayt Institute) whose rights were never cleared. They are
disabled and marked unverified until permission is recorded in
data/manifests/tafseer_sources.json. No content is deleted.

Also adds a nullable tafseer_sources.translator column so translations can be
credited to their translator.

Idempotent: safe to re-run.

Revision ID: ws3a1b2c3d4e5
Revises: u0v1w2x3y4z5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ws3a1b2c3d4e5"
down_revision: Union[str, None] = "u0v1w2x3y4z5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UNLICENSED_ENGLISH = ("ibn_kathir_en", "jalalayn_en", "ibn_abbas_en")

UPGRADE_SQL = [
    "ALTER TABLE tafseer_sources ADD COLUMN IF NOT EXISTS translator VARCHAR(200)",
    """
    UPDATE tafseer_sources
       SET is_enabled = 0,
           license_verified = 0,
           license_type = 'pending_verification',
           license = 'Modern English translation - permission required',
           updated_at = NOW()
     WHERE id IN ('ibn_kathir_en', 'jalalayn_en', 'ibn_abbas_en')
    """,
    """
    UPDATE tafseer_sources SET translator = 'Darussalam abridgement'
     WHERE id = 'ibn_kathir_en' AND translator IS NULL
    """,
    """
    UPDATE tafseer_sources SET translator = 'Feras Hamza (Royal Aal al-Bayt Institute)'
     WHERE id = 'jalalayn_en' AND translator IS NULL
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    # Re-enabling unlicensed text is an owner decision, not a schema rollback;
    # only the column is removed.
    op.execute("ALTER TABLE tafseer_sources DROP COLUMN IF EXISTS translator")
