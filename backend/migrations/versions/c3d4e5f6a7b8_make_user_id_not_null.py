"""make_user_id_not_null

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-07 16:10:20.000000

Fixes:
  ISSUE-006: user_id on videos was nullable=True — orphaned rows could accumulate.
             Any existing NULL user_id rows are deleted before the constraint is applied.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ISSUE-006: Remove any orphaned videos that have no owner before adding the constraint
    op.execute("DELETE FROM videos WHERE user_id IS NULL")

    # Now make the column NOT NULL
    op.alter_column('videos', 'user_id',
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    nullable=False)


def downgrade() -> None:
    op.alter_column('videos', 'user_id',
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    nullable=True)
