"""add_processing_started_at_and_model_fixes

Revision ID: a1b2c3d4e5f6
Revises: 8a92f814b3d2
Create Date: 2026-08-07 16:10:00.000000

Fixes:
  ISSUE-001: Add processing_started_at column to videos table.
  ISSUE-004: Convert all naive DateTime columns to timezone-aware (TIMESTAMPTZ).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8a92f814b3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ISSUE-001: Add the missing processing_started_at column
    op.add_column('videos', sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True))

    # ISSUE-004: Convert naive DateTime columns to timezone-aware on all tables
    # videos
    op.alter_column('videos', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)
    op.alter_column('videos', 'expires_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)

    # transcripts
    op.alter_column('transcripts', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)

    # video_frames
    op.alter_column('video_frames', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('video_frames', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('transcripts', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('videos', 'expires_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('videos', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.drop_column('videos', 'processing_started_at')
