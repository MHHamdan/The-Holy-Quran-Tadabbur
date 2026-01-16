"""add_verification_workflow_tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-01-10 12:00:00.000000

Admin-gated verification workflow for content changes:
- verification_tasks: Stores proposed changes pending review
- verification_decisions: Audit trail of admin decisions

Entity types: concept, miracle, tafsir, occurrence, grammar
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verification_tasks table
    op.create_table('verification_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=200), nullable=False),
        sa.Column('proposed_change', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='ck_verification_status')
    )
    op.create_index('ix_verification_tasks_entity', 'verification_tasks', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_verification_tasks_status', 'verification_tasks', ['status'], unique=False)
    op.create_index('ix_verification_tasks_priority', 'verification_tasks', ['priority', 'created_at'], unique=False)

    # Create verification_decisions table
    op.create_table('verification_decisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['verification_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("decision IN ('approved', 'rejected')", name='ck_decision_value')
    )
    op.create_index('ix_verification_decisions_task', 'verification_decisions', ['task_id'], unique=False)
    op.create_index('ix_verification_decisions_admin', 'verification_decisions', ['admin_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_verification_decisions_admin', table_name='verification_decisions')
    op.drop_index('ix_verification_decisions_task', table_name='verification_decisions')
    op.drop_table('verification_decisions')

    op.drop_index('ix_verification_tasks_priority', table_name='verification_tasks')
    op.drop_index('ix_verification_tasks_status', table_name='verification_tasks')
    op.drop_index('ix_verification_tasks_entity', table_name='verification_tasks')
    op.drop_table('verification_tasks')
