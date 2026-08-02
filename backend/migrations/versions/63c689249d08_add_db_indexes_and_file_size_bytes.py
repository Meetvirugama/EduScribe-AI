"""add_db_indexes_and_file_size_bytes

Revision ID: 63c689249d08
Revises: 8a92f814b3d2
Create Date: 2026-08-02 21:46:05.632419

Adds:
  - videos.file_size_bytes (BigInteger): Enables O(1) SQL SUM for storage tracking.
  - INDEX idx_videos_user_id:       Critical for per-user video list & analytics queries.
  - INDEX idx_transcripts_video_id: Critical for workspace transcript lookup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63c689249d08'
down_revision: Union[str, None] = '8a92f814b3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add file_size_bytes column for fast SQL SUM storage tracking
    op.add_column('videos', sa.Column('file_size_bytes', sa.BigInteger(), nullable=True))

    # Add index on videos.user_id — all user-facing queries filter by this column
    op.create_index('idx_videos_user_id', 'videos', ['user_id'], unique=False)

    # Add index on transcripts.video_id — always queried when loading a workspace
    op.create_index('idx_transcripts_video_id', 'transcripts', ['video_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_transcripts_video_id', table_name='transcripts')
    op.drop_index('idx_videos_user_id', table_name='videos')
    op.drop_column('videos', 'file_size_bytes')

