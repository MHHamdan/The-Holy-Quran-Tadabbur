"""Therapy sessions: per-session client token (ownership proof)

Guidance sessions were readable, overwritable and deletable by anyone who
knew the session id, and /therapy/chat let the client choose that id. Each
session now gets a server-generated id plus a secret client token returned
once; only its SHA-256 is stored here and every later call must present it.
Rows created before this migration have no hash: they cannot be read or
written through the API any more and expire under THERAPY_RETENTION_DAYS;
their owners can still delete them by id.

Revision ID: r3b1c2d3e4f5
Revises: r2a1b2c3d4e5
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r3b1c2d3e4f5"
down_revision: Union[str, None] = "r2a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE therapy_sessions ADD COLUMN IF NOT EXISTS client_token_hash VARCHAR(64)")


def downgrade() -> None:
    op.execute("ALTER TABLE therapy_sessions DROP COLUMN IF EXISTS client_token_hash")
