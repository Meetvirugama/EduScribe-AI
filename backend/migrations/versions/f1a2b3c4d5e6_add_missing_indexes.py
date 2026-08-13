"""add_missing_indexes

Revision ID: f1a2b3c4d5e6
Revises: 63c689249d08
Create Date: 2026-08-11

Adds indexes identified in the performance audit that were missing:
  - idx_videos_user_created     : (user_id, created_at DESC) for list + analytics
  - idx_video_frames_video_id   : frames lookup by video
  - idx_frame_metadata_frame_id : JOIN from video_frames to frame_metadata
  - idx_ocr_results_frame_id    : JOIN from video_frames to ocr_results
  - idx_frame_scores_frame_id   : JOIN from video_frames to frame_scores
  - idx_artifacts_video_type    : artifact lookup by (video_id, artifact_type)
  - idx_videos_expires_at       : nightly cleanup query on expires_at (partial)

Note: idx_videos_user_id and idx_transcripts_video_id were already created in
      migration 63c689249d08 — those are NOT repeated here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '63c689249d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────────────
    # Videos table
    # ──────────────────────────────────────────────────────────────────────

    # Composite index for per-user video listing sorted by creation time.
    # Covers: GET /videos, GET /videos/analytics, GET /videos/storage
    op.create_index(
        'idx_videos_user_created',
        'videos',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
        postgresql_using='btree',
    )

    # Partial index on expires_at for the nightly retention cleanup query.
    # Only indexes rows that actually have an expiry set (skips NULL rows).
    op.create_index(
        'idx_videos_expires_at',
        'videos',
        ['expires_at'],
        unique=False,
        postgresql_where=sa.text('expires_at IS NOT NULL'),
    )

    # ──────────────────────────────────────────────────────────────────────
    # video_frames table
    # ──────────────────────────────────────────────────────────────────────

    # Index for frame listing by video (GET /videos/{id}/frames).
    # Also used by vision pipeline (bulk DELETE + SELECT).
    op.create_index(
        'idx_video_frames_video_id',
        'video_frames',
        ['video_id'],
        unique=False,
    )

    # ──────────────────────────────────────────────────────────────────────
    # frame_metadata / ocr_results / frame_scores tables
    # ──────────────────────────────────────────────────────────────────────

    # These three tables are always queried by frame_id via JOIN or IN-clause.
    op.create_index(
        'idx_frame_metadata_frame_id',
        'frame_metadata',
        ['frame_id'],
        unique=False,
    )

    op.create_index(
        'idx_ocr_results_frame_id',
        'ocr_results',
        ['frame_id'],
        unique=False,
    )

    # Composite: frame_id + is_selected is queried together for top-pick filtering.
    op.create_index(
        'idx_frame_scores_frame_id_selected',
        'frame_scores',
        ['frame_id', 'is_selected'],
        unique=False,
    )

    # ──────────────────────────────────────────────────────────────────────
    # artifacts table
    # ──────────────────────────────────────────────────────────────────────

    # Composite index for artifact lookup by video + type.
    # Covers: GET /generate/{id}/artifacts, POST /generate/{id}
    op.create_index(
        'idx_artifacts_video_type',
        'artifacts',
        ['video_id', 'artifact_type'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_artifacts_video_type', table_name='artifacts')
    op.drop_index('idx_frame_scores_frame_id_selected', table_name='frame_scores')
    op.drop_index('idx_ocr_results_frame_id', table_name='ocr_results')
    op.drop_index('idx_frame_metadata_frame_id', table_name='frame_metadata')
    op.drop_index('idx_video_frames_video_id', table_name='video_frames')
    op.drop_index('idx_videos_expires_at', table_name='videos')
    op.drop_index('idx_videos_user_created', table_name='videos')
