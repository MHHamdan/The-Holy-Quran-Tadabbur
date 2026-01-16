"""add_concept_graph_tables

Revision ID: a1b2c3d4e5f6
Revises: 8c162ed15d9b
Create Date: 2026-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8c162ed15d9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create concepts table
    op.create_table('concepts',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('label_ar', sa.String(length=200), nullable=False),
        sa.Column('label_en', sa.String(length=200), nullable=False),
        sa.Column('concept_type', sa.String(length=50), nullable=False),
        sa.Column('aliases_ar', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('aliases_en', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('parent_concept_id', sa.String(length=100), nullable=True),
        sa.Column('icon_hint', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('is_curated', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_concept_id'], ['concepts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_concept_label_ar', 'concepts', ['label_ar'], unique=False)
    op.create_index('ix_concept_type_slug', 'concepts', ['concept_type', 'slug'], unique=False)
    op.create_index(op.f('ix_concepts_concept_type'), 'concepts', ['concept_type'], unique=False)
    op.create_index(op.f('ix_concepts_slug'), 'concepts', ['slug'], unique=True)

    # Create occurrences table
    op.create_table('occurrences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('concept_id', sa.String(length=100), nullable=False),
        sa.Column('ref_type', sa.String(length=50), nullable=False),
        sa.Column('ref_id', sa.String(length=200), nullable=True),
        sa.Column('sura_no', sa.Integer(), nullable=True),
        sa.Column('ayah_start', sa.Integer(), nullable=True),
        sa.Column('ayah_end', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('context_ar', sa.Text(), nullable=True),
        sa.Column('context_en', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_occurrence_ayah', 'occurrences', ['sura_no', 'ayah_start'], unique=False)
    op.create_index('ix_occurrence_concept', 'occurrences', ['concept_id'], unique=False)
    op.create_index('ix_occurrence_ref', 'occurrences', ['ref_type', 'ref_id'], unique=False)
    op.create_index(op.f('ix_occurrences_concept_id'), 'occurrences', ['concept_id'], unique=False)
    op.create_index(op.f('ix_occurrences_sura_no'), 'occurrences', ['sura_no'], unique=False)

    # Create associations table
    op.create_table('associations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('concept_a_id', sa.String(length=100), nullable=False),
        sa.Column('concept_b_id', sa.String(length=100), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('is_directional', sa.Boolean(), nullable=True),
        sa.Column('strength', sa.Float(), nullable=True),
        sa.Column('explanation_ar', sa.Text(), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),
        sa.Column('evidence_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('has_sufficient_evidence', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("evidence_refs IS NOT NULL AND evidence_refs != '{}'::jsonb", name='ck_association_has_evidence'),
        sa.ForeignKeyConstraint(['concept_a_id'], ['concepts.id'], ),
        sa.ForeignKeyConstraint(['concept_b_id'], ['concepts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('concept_a_id', 'concept_b_id', 'relation_type', name='uq_association_pair')
    )
    op.create_index('ix_association_concepts', 'associations', ['concept_a_id', 'concept_b_id'], unique=False)
    op.create_index('ix_association_type', 'associations', ['relation_type'], unique=False)
    op.create_index(op.f('ix_associations_concept_a_id'), 'associations', ['concept_a_id'], unique=False)
    op.create_index(op.f('ix_associations_concept_b_id'), 'associations', ['concept_b_id'], unique=False)


def downgrade() -> None:
    # Drop associations table
    op.drop_index(op.f('ix_associations_concept_b_id'), table_name='associations')
    op.drop_index(op.f('ix_associations_concept_a_id'), table_name='associations')
    op.drop_index('ix_association_type', table_name='associations')
    op.drop_index('ix_association_concepts', table_name='associations')
    op.drop_table('associations')

    # Drop occurrences table
    op.drop_index(op.f('ix_occurrences_sura_no'), table_name='occurrences')
    op.drop_index(op.f('ix_occurrences_concept_id'), table_name='occurrences')
    op.drop_index('ix_occurrence_ref', table_name='occurrences')
    op.drop_index('ix_occurrence_concept', table_name='occurrences')
    op.drop_index('ix_occurrence_ayah', table_name='occurrences')
    op.drop_table('occurrences')

    # Drop concepts table
    op.drop_index(op.f('ix_concepts_slug'), table_name='concepts')
    op.drop_index(op.f('ix_concepts_concept_type'), table_name='concepts')
    op.drop_index('ix_concept_type_slug', table_name='concepts')
    op.drop_index('ix_concept_label_ar', table_name='concepts')
    op.drop_table('concepts')
