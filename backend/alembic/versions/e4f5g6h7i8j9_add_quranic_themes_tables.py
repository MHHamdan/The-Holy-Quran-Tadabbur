"""add_quranic_themes_tables

Revision ID: e4f5g6h7i8j9
Revises: d3e4f5g6h7i8
Create Date: 2026-01-13 23:00:00.000000

Quranic Thematic Classification System (المحاور القرآنية)

Tables:
- quranic_themes: Root theme entities (التوحيد، الإيمان، العبادات، الأخلاق)
- theme_segments: Theme occurrences in verses
- theme_connections: Relationships between segments
- theme_consequences: Divine rewards/punishments (السنن الإلهية)

ISLAMIC CONSTRAINTS:
- All segments require tafsir evidence (4 madhab sources only)
- Evidence grounding enforced via CHECK constraints
- Layer separation: Quran text → Tafsir → Classification
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4f5g6h7i8j9'
down_revision: Union[str, None] = 'd3e4f5g6h7i8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # TABLE: quranic_themes - Root theme entities
    # ==========================================================================
    op.create_table('quranic_themes',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title_ar', sa.String(length=300), nullable=False),
        sa.Column('title_en', sa.String(length=300), nullable=False),
        sa.Column('short_title_ar', sa.String(length=100), nullable=True),
        sa.Column('short_title_en', sa.String(length=100), nullable=True),

        # Classification
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('order_of_importance', sa.Integer(), nullable=True, default=0),

        # Arabic key concepts for search
        sa.Column('key_concepts', postgresql.ARRAY(sa.String()), nullable=False),

        # Hierarchy
        sa.Column('parent_theme_id', sa.String(length=100), nullable=True),
        sa.Column('related_theme_ids', postgresql.ARRAY(sa.String()), nullable=True),

        # Content
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),

        # Approved tafsir sources used
        sa.Column('tafsir_sources', postgresql.ARRAY(sa.String()), nullable=True),

        # Metadata
        sa.Column('is_complete', sa.Boolean(), nullable=True, default=False),
        sa.Column('segment_count', sa.Integer(), nullable=True, default=0),
        sa.Column('total_verses', sa.Integer(), nullable=True, default=0),
        sa.Column('suras_mentioned', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('makki_percentage', sa.Float(), nullable=True, default=0),
        sa.Column('madani_percentage', sa.Float(), nullable=True, default=0),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_theme_slug'),
        sa.ForeignKeyConstraint(['parent_theme_id'], ['quranic_themes.id'], name='fk_theme_parent'),
    )

    # Indexes for quranic_themes
    op.create_index('ix_theme_category', 'quranic_themes', ['category'], unique=False)
    op.create_index('ix_theme_importance', 'quranic_themes', ['order_of_importance'], unique=False)
    op.create_index('ix_theme_parent', 'quranic_themes', ['parent_theme_id'], unique=False)
    op.create_index('ix_theme_key_concepts', 'quranic_themes', ['key_concepts'],
                    unique=False, postgresql_using='gin')

    # ==========================================================================
    # TABLE: theme_segments - Theme occurrences in verses
    # ==========================================================================
    op.create_table('theme_segments',
        sa.Column('id', sa.String(length=200), nullable=False),
        sa.Column('theme_id', sa.String(length=100), nullable=False),

        # Ordering
        sa.Column('segment_order', sa.Integer(), nullable=False),
        sa.Column('chronological_index', sa.Integer(), nullable=True),

        # Quran location
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('ayah_start', sa.Integer(), nullable=False),
        sa.Column('ayah_end', sa.Integer(), nullable=False),

        # Content
        sa.Column('title_ar', sa.String(length=200), nullable=True),
        sa.Column('title_en', sa.String(length=200), nullable=True),
        sa.Column('summary_ar', sa.Text(), nullable=False),
        sa.Column('summary_en', sa.Text(), nullable=False),

        # Tags and context
        sa.Column('semantic_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('revelation_context', sa.String(length=20), nullable=True),
        sa.Column('is_entry_point', sa.Boolean(), nullable=True, default=False),
        sa.Column('importance_weight', sa.Float(), nullable=True, default=0.5),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),

        # CRITICAL: Evidence grounding (required)
        sa.Column('evidence_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['theme_id'], ['quranic_themes.id'], name='fk_segment_theme'),

        # CONSTRAINT: Must have at least one evidence source
        sa.CheckConstraint(
            'array_length(evidence_chunk_ids, 1) >= 1',
            name='ck_theme_segment_has_evidence'
        ),
    )

    # Indexes for theme_segments
    op.create_index('ix_theme_segment_theme', 'theme_segments', ['theme_id'], unique=False)
    op.create_index('ix_theme_segment_location', 'theme_segments', ['sura_no', 'ayah_start'], unique=False)
    op.create_index('ix_theme_segment_revelation', 'theme_segments', ['revelation_context'], unique=False)
    op.create_index('ix_theme_segment_chronological', 'theme_segments',
                    ['theme_id', 'chronological_index'], unique=False)
    op.create_index('ix_theme_segment_evidence', 'theme_segments', ['evidence_chunk_ids'],
                    unique=False, postgresql_using='gin')
    op.create_index('ix_theme_segment_verified', 'theme_segments', ['is_verified'], unique=False)

    # ==========================================================================
    # TABLE: theme_connections - Relationships between segments
    # ==========================================================================
    op.create_table('theme_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        sa.Column('source_segment_id', sa.String(length=200), nullable=False),
        sa.Column('target_segment_id', sa.String(length=200), nullable=False),

        # Edge type
        sa.Column('edge_type', sa.String(length=50), nullable=False),

        # Is this part of sequential reading?
        sa.Column('is_sequential', sa.Boolean(), nullable=True, default=False),

        # Connection strength (0.0-1.0)
        sa.Column('strength', sa.Float(), nullable=True, default=0.5),

        # Explanation
        sa.Column('explanation_ar', sa.Text(), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),

        # Evidence (optional for weak links)
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_segment_id'], ['theme_segments.id'],
                               name='fk_conn_source'),
        sa.ForeignKeyConstraint(['target_segment_id'], ['theme_segments.id'],
                               name='fk_conn_target'),
        sa.UniqueConstraint('source_segment_id', 'target_segment_id', 'edge_type',
                           name='uq_theme_connection'),
    )

    # Indexes for theme_connections
    op.create_index('ix_theme_conn_source', 'theme_connections',
                    ['source_segment_id'], unique=False)
    op.create_index('ix_theme_conn_target', 'theme_connections',
                    ['target_segment_id'], unique=False)
    op.create_index('ix_theme_conn_type', 'theme_connections',
                    ['edge_type'], unique=False)
    op.create_index('ix_theme_conn_sequential', 'theme_connections',
                    ['is_sequential'], unique=False)

    # ==========================================================================
    # TABLE: theme_consequences - Divine rewards/punishments (السنن الإلهية)
    # ==========================================================================
    op.create_table('theme_consequences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        sa.Column('theme_id', sa.String(length=100), nullable=False),

        # Type of consequence
        sa.Column('consequence_type', sa.String(length=50), nullable=False),

        # Content
        sa.Column('description_ar', sa.Text(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=False),

        # Supporting verses
        sa.Column('supporting_verses', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Evidence grounding (required)
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),

        # Order for display
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),

        sa.Column('created_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['theme_id'], ['quranic_themes.id'],
                               name='fk_consequence_theme'),

        # CONSTRAINT: Must have evidence
        sa.CheckConstraint(
            'array_length(evidence_chunk_ids, 1) >= 1',
            name='ck_consequence_has_evidence'
        ),
    )

    # Indexes for theme_consequences
    op.create_index('ix_consequence_theme', 'theme_consequences',
                    ['theme_id'], unique=False)
    op.create_index('ix_consequence_type', 'theme_consequences',
                    ['consequence_type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('theme_consequences')
    op.drop_table('theme_connections')
    op.drop_table('theme_segments')
    op.drop_table('quranic_themes')
