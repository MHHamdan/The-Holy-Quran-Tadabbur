"""Add discovery fields to theme_segments

Revision ID: f5g6h7i8j9k0
Revises: e4f5g6h7i8j9
Create Date: 2024-01-14

Adds fields needed for Quran-wide theme discovery:
- match_type: how the segment was matched (lexical/root/semantic/mixed/manual)
- confidence: 0.0-1.0 confidence score
- reasons_ar: Arabic explanation of why verse belongs to theme
- reasons_en: English explanation (optional)
- is_core: whether this is a core verse or supporting verse
- discovered_at: timestamp when segment was discovered
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5g6h7i8j9k0'
down_revision = 'e4f5g6h7i8j9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add match_type column
    op.add_column('theme_segments', sa.Column(
        'match_type',
        sa.VARCHAR(50),
        nullable=True,
        server_default='manual',
        comment='How segment was matched: lexical, root, semantic, mixed, manual'
    ))

    # Add confidence column
    op.add_column('theme_segments', sa.Column(
        'confidence',
        sa.Float(),
        nullable=True,
        server_default='1.0',
        comment='Confidence score 0.0-1.0'
    ))

    # Add reasons_ar column
    op.add_column('theme_segments', sa.Column(
        'reasons_ar',
        sa.Text(),
        nullable=True,
        comment='Arabic explanation of why verse belongs to theme'
    ))

    # Add reasons_en column
    op.add_column('theme_segments', sa.Column(
        'reasons_en',
        sa.Text(),
        nullable=True,
        comment='English explanation of why verse belongs to theme'
    ))

    # Add is_core column
    op.add_column('theme_segments', sa.Column(
        'is_core',
        sa.Boolean(),
        nullable=True,
        server_default='true',
        comment='True if core verse, False if supporting'
    ))

    # Add discovered_at column
    op.add_column('theme_segments', sa.Column(
        'discovered_at',
        sa.TIMESTAMP(),
        nullable=True,
        comment='When segment was discovered by automated process'
    ))

    # Create index for confidence filtering
    op.create_index(
        'ix_theme_segments_confidence',
        'theme_segments',
        ['confidence'],
        unique=False
    )

    # Create index for match_type filtering
    op.create_index(
        'ix_theme_segments_match_type',
        'theme_segments',
        ['match_type'],
        unique=False
    )

    # Create index for is_core filtering
    op.create_index(
        'ix_theme_segments_is_core',
        'theme_segments',
        ['is_core'],
        unique=False
    )

    # Update existing segments to have default values
    op.execute("""
        UPDATE theme_segments
        SET match_type = 'manual',
            confidence = 1.0,
            is_core = true
        WHERE match_type IS NULL
    """)


def downgrade() -> None:
    op.drop_index('ix_theme_segments_is_core', table_name='theme_segments')
    op.drop_index('ix_theme_segments_match_type', table_name='theme_segments')
    op.drop_index('ix_theme_segments_confidence', table_name='theme_segments')
    op.drop_column('theme_segments', 'discovered_at')
    op.drop_column('theme_segments', 'is_core')
    op.drop_column('theme_segments', 'reasons_en')
    op.drop_column('theme_segments', 'reasons_ar')
    op.drop_column('theme_segments', 'confidence')
    op.drop_column('theme_segments', 'match_type')
