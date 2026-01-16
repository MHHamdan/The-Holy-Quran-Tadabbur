"""add_verification_queue

Revision ID: c2d3e4f5g6h7
Revises: b7c8d9e0f1a2
Create Date: 2026-01-10 18:00:00.000000

Enhanced verification queue for admin workflow:
- verification_queue: Full-featured queue with AI analysis support
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5g6h7'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verification_queue table
    op.create_table('verification_queue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=200), nullable=False),
        sa.Column('flagged_by', sa.String(length=100), nullable=False),
        sa.Column('flagged_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('flag_type', sa.String(length=50), nullable=False),
        sa.Column('flag_reason', sa.Text(), nullable=True),
        sa.Column('flag_reason_ar', sa.Text(), nullable=True),
        sa.Column('context_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_suggestion', sa.Text(), nullable=True),
        sa.Column('ai_suggestion_ar', sa.Text(), nullable=True),
        sa.Column('ai_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=True),
        sa.Column('assigned_to', sa.String(length=100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_decision', sa.String(length=20), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('review_notes_ar', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.String(length=100), nullable=True),
        sa.Column('action_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_verification_entity', 'verification_queue',
                    ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_verification_status_priority', 'verification_queue',
                    ['status', 'priority'], unique=False)
    op.create_index('ix_verification_assigned', 'verification_queue',
                    ['assigned_to', 'status'], unique=False)
    op.create_index('ix_verification_flagged_at', 'verification_queue',
                    ['flagged_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_verification_flagged_at', table_name='verification_queue')
    op.drop_index('ix_verification_assigned', table_name='verification_queue')
    op.drop_index('ix_verification_status_priority', table_name='verification_queue')
    op.drop_index('ix_verification_entity', table_name='verification_queue')
    op.drop_table('verification_queue')
