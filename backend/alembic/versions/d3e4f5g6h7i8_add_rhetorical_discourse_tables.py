"""add_rhetorical_discourse_tables

Revision ID: d3e4f5g6h7i8
Revises: c2d3e4f5g6h7
Create Date: 2026-01-13 12:00:00.000000

Tables for Arabic rhetoric (علم البلاغة) analysis:
- rhetorical_device_types: Canonical registry of rhetorical devices
- rhetorical_occurrences: Device-to-verse links with evidence grounding
- discourse_segments: Verse cluster classification by discourse type
- verse_tones: Emotional tone tagging per verse range
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd3e4f5g6h7i8'
down_revision: Union[str, None] = 'c2d3e4f5g6h7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================
    # Table: rhetorical_device_types
    # Canonical registry of Arabic rhetorical devices (علم البلاغة)
    # =========================================
    op.create_table('rhetorical_device_types',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name_ar', sa.String(length=200), nullable=False),
        sa.Column('name_en', sa.String(length=200), nullable=False),
        # Category: bayaan (علم البيان), maani (علم المعاني), badeea (علم البديع)
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('definition_ar', sa.Text(), nullable=True),
        sa.Column('definition_en', sa.Text(), nullable=True),
        # JSON with Quranic examples and evidence sources
        sa.Column('examples_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Sub-types (e.g., استعارة تصريحية، استعارة مكنية)
        sa.Column('sub_types_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Parent device for hierarchical organization
        sa.Column('parent_device_id', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_device_id'], ['rhetorical_device_types.id'], name='fk_device_parent'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rhetorical_device_slug', 'rhetorical_device_types', ['slug'], unique=True)
    op.create_index('ix_rhetorical_device_category', 'rhetorical_device_types', ['category'], unique=False)
    op.create_index('ix_rhetorical_device_name_ar', 'rhetorical_device_types', ['name_ar'], unique=False)

    # =========================================
    # Table: rhetorical_occurrences
    # Links rhetorical devices to specific ayah ranges with evidence grounding
    # =========================================
    op.create_table('rhetorical_occurrences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_type_id', sa.String(length=50), nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('ayah_start', sa.Integer(), nullable=False),
        sa.Column('ayah_end', sa.Integer(), nullable=False),
        # The specific Arabic text exhibiting the device
        sa.Column('text_snippet_ar', sa.Text(), nullable=True),
        # Why this is classified as this device
        sa.Column('explanation_ar', sa.Text(), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),
        # MANDATORY: Tafsir evidence chunk IDs (balagha-focused sources)
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),
        # Confidence score (0.0-1.0)
        sa.Column('confidence', sa.Float(), nullable=True, default=1.0),
        # Source: "balagha_tafsir", "curated", "llm_extraction"
        sa.Column('source', sa.String(length=100), nullable=True),
        # Scholar verification
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['device_type_id'], ['rhetorical_device_types.id'], name='fk_occurrence_device'),
        sa.PrimaryKeyConstraint('id'),
        # Ensure at least one evidence chunk ID is provided
        sa.CheckConstraint("array_length(evidence_chunk_ids, 1) >= 1", name='ck_occurrence_has_evidence')
    )
    op.create_index('ix_rhetorical_occ_device', 'rhetorical_occurrences', ['device_type_id'], unique=False)
    op.create_index('ix_rhetorical_occ_ayah', 'rhetorical_occurrences', ['sura_no', 'ayah_start'], unique=False)
    op.create_index('ix_rhetorical_occ_verified', 'rhetorical_occurrences', ['is_verified'], unique=False)
    op.create_index('ix_rhetorical_occ_source', 'rhetorical_occurrences', ['source'], unique=False)

    # =========================================
    # Table: discourse_segments
    # Classifies contiguous verse ranges by discourse type
    # =========================================
    op.create_table('discourse_segments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('ayah_start', sa.Integer(), nullable=False),
        sa.Column('ayah_end', sa.Integer(), nullable=False),
        # Discourse type: narrative, exhortation, legal_ruling, supplication, promise, warning, parable, argumentation
        sa.Column('discourse_type', sa.String(length=50), nullable=False),
        # Optional sub-classification
        sa.Column('sub_type', sa.String(length=50), nullable=True),
        # Titles and summaries
        sa.Column('title_ar', sa.String(length=300), nullable=True),
        sa.Column('title_en', sa.String(length=300), nullable=True),
        sa.Column('summary_ar', sa.Text(), nullable=True),
        sa.Column('summary_en', sa.Text(), nullable=True),
        # Link to story for NARRATIVE type
        sa.Column('linked_story_id', sa.String(length=100), nullable=True),
        # Story segment IDs for narrative linking
        sa.Column('linked_segment_ids', postgresql.ARRAY(sa.String()), nullable=True),
        # Evidence grounding from tafsir
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, default=1.0),
        # Source and verification
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['linked_story_id'], ['stories.id'], name='fk_discourse_story'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("array_length(evidence_chunk_ids, 1) >= 1", name='ck_discourse_has_evidence')
    )
    op.create_index('ix_discourse_type', 'discourse_segments', ['discourse_type'], unique=False)
    op.create_index('ix_discourse_ayah', 'discourse_segments', ['sura_no', 'ayah_start'], unique=False)
    op.create_index('ix_discourse_sura', 'discourse_segments', ['sura_no'], unique=False)
    op.create_index('ix_discourse_story', 'discourse_segments', ['linked_story_id'], unique=False)

    # =========================================
    # Table: verse_tones
    # Emotional tone tagging per verse or verse range
    # =========================================
    op.create_table('verse_tones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('ayah_start', sa.Integer(), nullable=False),
        sa.Column('ayah_end', sa.Integer(), nullable=False),
        # Tone type: hope, fear, awe, glad_tidings, warning, consolation, gratitude, certainty, urgency
        sa.Column('tone_type', sa.String(length=50), nullable=False),
        # Intensity (0.0-1.0 scale)
        sa.Column('intensity', sa.Float(), nullable=True, default=0.5),
        # Explanations
        sa.Column('explanation_ar', sa.Text(), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),
        # Evidence grounding
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, default=1.0),
        # Source and verification
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("array_length(evidence_chunk_ids, 1) >= 1", name='ck_tone_has_evidence')
    )
    op.create_index('ix_tone_type', 'verse_tones', ['tone_type'], unique=False)
    op.create_index('ix_tone_ayah', 'verse_tones', ['sura_no', 'ayah_start'], unique=False)
    op.create_index('ix_tone_sura', 'verse_tones', ['sura_no'], unique=False)
    op.create_index('ix_tone_intensity', 'verse_tones', ['intensity'], unique=False)


def downgrade() -> None:
    # Drop verse_tones table
    op.drop_index('ix_tone_intensity', table_name='verse_tones')
    op.drop_index('ix_tone_sura', table_name='verse_tones')
    op.drop_index('ix_tone_ayah', table_name='verse_tones')
    op.drop_index('ix_tone_type', table_name='verse_tones')
    op.drop_table('verse_tones')

    # Drop discourse_segments table
    op.drop_index('ix_discourse_story', table_name='discourse_segments')
    op.drop_index('ix_discourse_sura', table_name='discourse_segments')
    op.drop_index('ix_discourse_ayah', table_name='discourse_segments')
    op.drop_index('ix_discourse_type', table_name='discourse_segments')
    op.drop_table('discourse_segments')

    # Drop rhetorical_occurrences table
    op.drop_index('ix_rhetorical_occ_source', table_name='rhetorical_occurrences')
    op.drop_index('ix_rhetorical_occ_verified', table_name='rhetorical_occurrences')
    op.drop_index('ix_rhetorical_occ_ayah', table_name='rhetorical_occurrences')
    op.drop_index('ix_rhetorical_occ_device', table_name='rhetorical_occurrences')
    op.drop_table('rhetorical_occurrences')

    # Drop rhetorical_device_types table
    op.drop_index('ix_rhetorical_device_name_ar', table_name='rhetorical_device_types')
    op.drop_index('ix_rhetorical_device_category', table_name='rhetorical_device_types')
    op.drop_index('ix_rhetorical_device_slug', table_name='rhetorical_device_types')
    op.drop_table('rhetorical_device_types')
