"""update_video_schema

Revision ID: 8a92f814b3d2
Revises: 4f17a290ae78
Create Date: 2026-08-01 20:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a92f814b3d2'
down_revision: Union[str, None] = '4f17a290ae78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update ENUM values
    new_statuses = [
        'EXTRACTING_AUDIO',
        'EXTRACTING_FRAMES',
        'RUNNING_OCR',
        'CHUNKING',
        'DETECTING_TOPICS',
        'GENERATING_NOTES',
        'EXPORTING'
    ]
    
    # We use a connection and autocommit isolation level because ALTER TYPE cannot be run inside a transaction block in Postgres.
    with op.get_context().autocommit_block():
        for status in new_statuses:
            op.execute(f"ALTER TYPE videostatus ADD VALUE IF NOT EXISTS '{status}'")

    # 2. Change user_id to UUID and add Foreign Key
    op.execute('ALTER TABLE videos ALTER COLUMN user_id TYPE UUID USING user_id::uuid')
    op.create_foreign_key('fk_videos_user_id', 'videos', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 1. Drop Foreign Key
    op.drop_constraint('fk_videos_user_id', 'videos', type_='foreignkey')
    
    # 2. Convert back to String
    op.execute('ALTER TABLE videos ALTER COLUMN user_id TYPE VARCHAR USING user_id::varchar')

    # Note: PostgreSQL does not support dropping ENUM values easily.
    # We will leave the enum values in place during downgrade as it's non-destructive.
