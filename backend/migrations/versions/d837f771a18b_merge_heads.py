"""Merge heads

Revision ID: d837f771a18b
Revises: 63c689249d08, c3d4e5f6a7b8
Create Date: 2026-08-10 17:12:07.544642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd837f771a18b'
down_revision: Union[str, None] = ('63c689249d08', 'c3d4e5f6a7b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
