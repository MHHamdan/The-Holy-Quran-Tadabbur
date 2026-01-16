"""Add theme_suggestions table for admin review workflow

Revision ID: h7i8j9k0l1m2
Revises: g6h7i8j9k0l1
Create Date: 2024-01-14

Adds theme_suggestions table for admin review workflow:
- Stores discovery candidates for review
- Supports approve/reject workflow
- Tracks reviewer and rejection reasons
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'h7i8j9k0l1m2'
down_revision = 'g6h7i8j9k0l1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'theme_suggestions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('theme_id', sa.String(100), nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('ayah_start', sa.Integer(), nullable=False),
        sa.Column('ayah_end', sa.Integer(), nullable=False),
        sa.Column('match_type', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasons_ar', sa.Text(), nullable=False),
        sa.Column('reasons_en', sa.Text(), nullable=True),
        sa.Column('evidence_sources', postgresql.JSONB(), nullable=False),
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('source', sa.String(50), nullable=True, server_default='discovery'),
        sa.Column('batch_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['theme_id'], ['quranic_themes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('theme_id', 'sura_no', 'ayah_start', 'ayah_end', name='uq_theme_suggestion_location')
    )

    # Create indexes
    op.create_index('ix_suggestion_theme', 'theme_suggestions', ['theme_id'])
    op.create_index('ix_suggestion_status', 'theme_suggestions', ['status'])
    op.create_index('ix_suggestion_location', 'theme_suggestions', ['sura_no', 'ayah_start'])
    op.create_index('ix_suggestion_confidence', 'theme_suggestions', ['confidence'])
    op.create_index('ix_suggestion_batch', 'theme_suggestions', ['batch_id'])


def downgrade() -> None:
    op.drop_index('ix_suggestion_batch', table_name='theme_suggestions')
    op.drop_index('ix_suggestion_confidence', table_name='theme_suggestions')
    op.drop_index('ix_suggestion_location', table_name='theme_suggestions')
    op.drop_index('ix_suggestion_status', table_name='theme_suggestions')
    op.drop_index('ix_suggestion_theme', table_name='theme_suggestions')
    op.drop_table('theme_suggestions')
