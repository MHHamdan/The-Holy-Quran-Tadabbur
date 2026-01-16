"""Initial schema for Tadabbur-AI

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quran_verses table
    op.create_table(
        'quran_verses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('sura_name_ar', sa.String(length=100), nullable=False),
        sa.Column('sura_name_en', sa.String(length=100), nullable=False),
        sa.Column('aya_no', sa.Integer(), nullable=False),
        sa.Column('text_uthmani', sa.Text(), nullable=False),
        sa.Column('text_imlaei', sa.Text(), nullable=False),
        sa.Column('page_no', sa.Integer(), nullable=False),
        sa.Column('juz_no', sa.Integer(), nullable=False),
        sa.Column('hizb_no', sa.Integer(), nullable=True),
        sa.Column('line_start', sa.Integer(), nullable=True),
        sa.Column('line_end', sa.Integer(), nullable=True),
        sa.Column('sajda_type', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sura_no', 'aya_no', name='uq_sura_aya')
    )
    op.create_index('ix_verse_sura_aya', 'quran_verses', ['sura_no', 'aya_no'])
    op.create_index('ix_verse_page', 'quran_verses', ['page_no'])
    op.create_index('ix_verse_juz', 'quran_verses', ['juz_no'])
    op.create_index(op.f('ix_quran_verses_sura_no'), 'quran_verses', ['sura_no'])

    # Create translations table
    op.create_table(
        'translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('verse_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('translator', sa.String(length=100), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('needs_review', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['verse_id'], ['quran_verses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('verse_id', 'language', 'translator', name='uq_verse_lang_translator')
    )
    op.create_index('ix_translation_lang', 'translations', ['language'])
    op.create_index(op.f('ix_translations_verse_id'), 'translations', ['verse_id'])

    # Create tafseer_sources table
    op.create_table(
        'tafseer_sources',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name_ar', sa.String(length=200), nullable=False),
        sa.Column('name_en', sa.String(length=200), nullable=False),
        sa.Column('author_ar', sa.String(length=200), nullable=True),
        sa.Column('author_en', sa.String(length=200), nullable=True),
        sa.Column('era', sa.String(length=50), nullable=True),
        sa.Column('death_year_hijri', sa.Integer(), nullable=True),
        sa.Column('methodology', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('license', sa.String(length=200), nullable=True),
        sa.Column('license_url', sa.Text(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True, default=1.0),
        sa.Column('is_primary_source', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tafseer_chunks table
    op.create_table(
        'tafseer_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chunk_id', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=50), nullable=False),
        sa.Column('verse_start_id', sa.Integer(), nullable=False),
        sa.Column('verse_end_id', sa.Integer(), nullable=False),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('aya_start', sa.Integer(), nullable=False),
        sa.Column('aya_end', sa.Integer(), nullable=False),
        sa.Column('content_ar', sa.Text(), nullable=True),
        sa.Column('content_en', sa.Text(), nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('scholarly_consensus', sa.String(length=50), nullable=True),
        sa.Column('chunk_order', sa.Integer(), nullable=True, default=0),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('char_count', sa.Integer(), nullable=True),
        sa.Column('is_embedded', sa.Integer(), nullable=True, default=0),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['tafseer_sources.id']),
        sa.ForeignKeyConstraint(['verse_start_id'], ['quran_verses.id']),
        sa.ForeignKeyConstraint(['verse_end_id'], ['quran_verses.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tafseer_chunks_chunk_id'), 'tafseer_chunks', ['chunk_id'], unique=True)
    op.create_index('ix_chunk_source', 'tafseer_chunks', ['source_id'])
    op.create_index('ix_chunk_verse_range', 'tafseer_chunks', ['verse_start_id', 'verse_end_id'])
    op.create_index('ix_chunk_sura', 'tafseer_chunks', ['sura_no'])

    # Create themes table
    op.create_table(
        'themes',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name_ar', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('parent_theme_id', sa.String(length=50), nullable=True),
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('related_themes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_theme_id'], ['themes.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create stories table
    op.create_table(
        'stories',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name_ar', sa.String(length=200), nullable=False),
        sa.Column('name_en', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('main_figures', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('themes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('summary_ar', sa.Text(), nullable=True),
        sa.Column('summary_en', sa.Text(), nullable=True),
        sa.Column('timeline_era', sa.String(length=50), nullable=True),
        sa.Column('lessons_ar', sa.Text(), nullable=True),
        sa.Column('lessons_en', sa.Text(), nullable=True),
        sa.Column('total_verses', sa.Integer(), nullable=True, default=0),
        sa.Column('suras_mentioned', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create story_segments table
    op.create_table(
        'story_segments',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('story_id', sa.String(length=50), nullable=False),
        sa.Column('narrative_order', sa.Integer(), nullable=False),
        sa.Column('segment_type', sa.String(length=50), nullable=True),
        sa.Column('aspect', sa.String(length=100), nullable=True),
        sa.Column('sura_no', sa.Integer(), nullable=False),
        sa.Column('aya_start', sa.Integer(), nullable=False),
        sa.Column('aya_end', sa.Integer(), nullable=False),
        sa.Column('verse_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('summary_ar', sa.Text(), nullable=True),
        sa.Column('summary_en', sa.Text(), nullable=True),
        sa.Column('key_points_ar', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('key_points_en', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_segment_story', 'story_segments', ['story_id'])
    op.create_index('ix_segment_location', 'story_segments', ['sura_no', 'aya_start', 'aya_end'])

    # Create story_connections table
    op.create_table(
        'story_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_segment_id', sa.String(length=100), nullable=False),
        sa.Column('target_segment_id', sa.String(length=100), nullable=False),
        sa.Column('connection_type', sa.String(length=50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=True, default=1.0),
        sa.Column('explanation_ar', sa.Text(), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),
        sa.Column('evidence_chunk_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('shared_themes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_segment_id'], ['story_segments.id']),
        sa.ForeignKeyConstraint(['target_segment_id'], ['story_segments.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name='ck_connection_has_evidence'
        )
    )
    op.create_index('ix_connection_source', 'story_connections', ['source_segment_id'])
    op.create_index('ix_connection_target', 'story_connections', ['target_segment_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_action_time', 'audit_logs', ['action', 'created_at'])
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_status', 'audit_logs', ['status'])
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('story_connections')
    op.drop_table('story_segments')
    op.drop_table('stories')
    op.drop_table('themes')
    op.drop_table('tafseer_chunks')
    op.drop_table('tafseer_sources')
    op.drop_table('translations')
    op.drop_table('quran_verses')
