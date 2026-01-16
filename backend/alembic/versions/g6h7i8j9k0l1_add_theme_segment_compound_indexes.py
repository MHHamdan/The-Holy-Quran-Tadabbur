"""Add compound indexes for theme segments performance

Revision ID: g6h7i8j9k0l1
Revises: f5g6h7i8j9k0
Create Date: 2024-01-14

Adds compound indexes for efficient filtering and sorting:
- (theme_id, confidence) - theme + confidence queries
- (theme_id, match_type) - theme + match_type queries
- (theme_id, sura_no, ayah_start) - theme + location queries
- (theme_id, is_core) - theme + core/supporting queries
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'g6h7i8j9k0l1'
down_revision = 'f5g6h7i8j9k0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Compound index for theme + confidence (sorting by confidence)
    op.create_index(
        'ix_theme_segments_theme_confidence',
        'theme_segments',
        ['theme_id', 'confidence'],
        unique=False
    )

    # Compound index for theme + match_type filtering
    op.create_index(
        'ix_theme_segments_theme_match_type',
        'theme_segments',
        ['theme_id', 'match_type'],
        unique=False
    )

    # Compound index for theme + sura location (Mushaf order)
    op.create_index(
        'ix_theme_segments_theme_sura_ayah',
        'theme_segments',
        ['theme_id', 'sura_no', 'ayah_start'],
        unique=False
    )

    # Compound index for theme + core/supporting
    op.create_index(
        'ix_theme_segments_theme_is_core',
        'theme_segments',
        ['theme_id', 'is_core'],
        unique=False
    )

    # Compound index for theme + segment_order (default sort)
    op.create_index(
        'ix_theme_segments_theme_order',
        'theme_segments',
        ['theme_id', 'segment_order'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_theme_segments_theme_order', table_name='theme_segments')
    op.drop_index('ix_theme_segments_theme_is_core', table_name='theme_segments')
    op.drop_index('ix_theme_segments_theme_sura_ayah', table_name='theme_segments')
    op.drop_index('ix_theme_segments_theme_match_type', table_name='theme_segments')
    op.drop_index('ix_theme_segments_theme_confidence', table_name='theme_segments')
