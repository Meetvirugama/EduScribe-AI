"""Add artifact model and update video status

Revision ID: 2aea7972d19d
Revises: d837f771a18b
Create Date: 2026-08-10 21:38:16.932696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aea7972d19d'
down_revision: Union[str, None] = 'd837f771a18b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update VideoStatus ENUM
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'MERGING_ALIGNMENT';")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'UNDERSTANDING_CONTENT';")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'READY_FOR_SELECTION';")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'GENERATING_ARTIFACT';")

    # 2. Create ArtifactStatus ENUM
    op.execute("CREATE TYPE artifactstatus AS ENUM ('PENDING', 'GENERATING', 'COMPLETED', 'FAILED');")

    # 3. Create Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'GENERATING', 'COMPLETED', 'FAILED', name='artifactstatus'), nullable=False),
        sa.Column('content', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Note: Removing ENUM values is not supported by PostgreSQL directly without dropping the type.
    # We will just drop the artifacts table and the new artifactstatus ENUM.
    op.drop_table('artifacts')
    op.execute("DROP TYPE artifactstatus;")
