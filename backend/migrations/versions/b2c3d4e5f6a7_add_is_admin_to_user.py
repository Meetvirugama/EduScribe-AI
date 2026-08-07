"""add_is_admin_to_user

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-07 16:10:10.000000

Fixes:
  ISSUE-003: Add is_admin Boolean column to users table with default False.
  ISSUE-004: Convert users.created_at to timezone-aware.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ISSUE-003: Add is_admin column — all existing users get False (not admin)
    op.add_column('users', sa.Column(
        'is_admin',
        sa.Boolean(),
        nullable=False,
        server_default='false',
    ))

    # ISSUE-004: Convert users.created_at to timezone-aware
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.drop_column('users', 'is_admin')
