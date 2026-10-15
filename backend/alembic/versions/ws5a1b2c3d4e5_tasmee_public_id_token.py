"""Tasmee sessions: unguessable public id and per-session client token

Sessions were addressed by a sequential integer with no credential, so anyone
could list, read, drive or complete another person's session. Routes now use
a UUID public_id and require the token returned once at creation; only its
SHA-256 is stored.

Revision ID: ws5a1b2c3d4e5
Revises: u0v1w2x3y4z5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ws5a1b2c3d4e5"
down_revision: Union[str, None] = "u0v1w2x3y4z5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tasmee_sessions ADD COLUMN IF NOT EXISTS public_id VARCHAR(36) "
        "DEFAULT gen_random_uuid()::text"
    )
    op.execute("ALTER TABLE tasmee_sessions ADD COLUMN IF NOT EXISTS client_token_hash VARCHAR(64)")
    # Existing rows get an id but no token, so they stay unreachable (by design).
    op.execute(
        "UPDATE tasmee_sessions SET public_id = gen_random_uuid()::text WHERE public_id IS NULL"
    )
    op.execute("ALTER TABLE tasmee_sessions ALTER COLUMN public_id SET NOT NULL")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tasmee_sessions_public_id "
        "ON tasmee_sessions (public_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tasmee_sessions_public_id")
    op.execute("ALTER TABLE tasmee_sessions DROP COLUMN IF EXISTS client_token_hash")
    op.execute("ALTER TABLE tasmee_sessions DROP COLUMN IF EXISTS public_id")
