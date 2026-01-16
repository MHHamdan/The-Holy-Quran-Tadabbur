"""add_is_enabled_to_tafseer_sources

Revision ID: 4fdb53c55f30
Revises: f796d0030737
Create Date: 2026-01-04 14:05:47.350577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fdb53c55f30'
down_revision: Union[str, None] = 'f796d0030737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tafseer_sources', sa.Column('is_enabled', sa.Integer(), nullable=True, server_default='1'))
    # Update existing rows to be enabled by default
    op.execute("UPDATE tafseer_sources SET is_enabled = 1 WHERE is_enabled IS NULL")


def downgrade() -> None:
    op.drop_column('tafseer_sources', 'is_enabled')
