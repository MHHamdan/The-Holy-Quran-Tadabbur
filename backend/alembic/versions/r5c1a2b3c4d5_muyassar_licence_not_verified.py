"""Al-Muyassar: licence not verified until the owner confirms the KFGQPC terms

tafseer_sources.muyassar_ar carried license_verified=1 while its own licence
text read "KFGQPC terms pending owner confirmation, not cleared" (manifest
status pending_owner_confirmation). license_verified=1 is what every
licensed-only path checks (reader /tafseer/external/verse, /tafseer/compare,
the AI tafsir assistant, story and theme evidence), so an uncleared work was
served everywhere and was the reader's default.

Interim state, pending the owner's final decision (confirm the King Fahd
Complex terms, or switch to the QuranEnc arabic_moyassar edition):
- license_verified = 0 (license_type keeps the claimed terms,
  publisher_terms_non_commercial);
- the licence statement says it is not served while the terms are pending;
- is_enabled, the stored text (tafseer_chunks) and every evidence pointer are
  kept: nothing is deleted, and the read-time licence filters hide it until
  license_verified is set back to 1.

Idempotent: only a row that still needs it is touched. downgrade() restores
the r3d1a2b3c4d5 statement.

Revision ID: r5c1a2b3c4d5
Revises: r4a1b2c3d4e5
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r5c1a2b3c4d5"
down_revision: Union[str, None] = "r4a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# tafseer_sources.license is varchar(200).
MUYASSAR_LICENSE = (
    "King Fahd Complex (KFGQPC) publication; terms pending owner confirmation, "
    "not cleared. Not licence-verified, so not served (interim hold, alembic r5c1a2b3c4d5)"
)
assert len(MUYASSAR_LICENSE) <= 200

# Statement written by r3d1a2b3c4d5, restored on downgrade.
PREVIOUS_LICENSE = (
    "King Fahd Complex: attributed, non-commercial display under "
    "docs/distribution-policy.md; KFGQPC terms pending owner confirmation, not cleared"
)

UPGRADE_SQL = [
    f"""
    UPDATE tafseer_sources
       SET license_verified = 0,
           license = '{MUYASSAR_LICENSE}'
     WHERE id = 'muyassar_ar'
       AND (license_verified IS DISTINCT FROM 0
            OR license IS DISTINCT FROM '{MUYASSAR_LICENSE}')
    """,
]

DOWNGRADE_SQL = [
    f"""
    UPDATE tafseer_sources
       SET license_verified = 1,
           license = '{PREVIOUS_LICENSE}'
     WHERE id = 'muyassar_ar' AND license = '{MUYASSAR_LICENSE}'
    """,
]


def upgrade() -> None:
    for sql in UPGRADE_SQL:
        op.execute(sql)


def downgrade() -> None:
    for sql in DOWNGRADE_SQL:
        op.execute(sql)
