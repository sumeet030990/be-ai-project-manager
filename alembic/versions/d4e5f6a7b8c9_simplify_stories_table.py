"""simplify stories table

Revision ID: d4e5f6a7b8c9
Revises: 4387e334c3ed
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = '4387e334c3ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('stories_parent_story_id_fkey', 'stories', type_='foreignkey')
    op.drop_index('ix_stories_parent_story_id', table_name='stories')
    op.drop_index('ix_stories_story_type', table_name='stories')
    op.drop_column('stories', 'parent_story_id')
    op.drop_column('stories', 'story_type')
    op.alter_column('stories', 'module_id', nullable=False)


def downgrade() -> None:
    op.alter_column('stories', 'module_id', nullable=True)
    op.add_column('stories', sa.Column('story_type', sa.String(length=20), nullable=False, server_default='story'))
    op.add_column('stories', sa.Column('parent_story_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'stories_parent_story_id_fkey', 'stories', 'stories',
        ['parent_story_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_stories_story_type', 'stories', ['story_type'])
    op.create_index('ix_stories_parent_story_id', 'stories', ['parent_story_id'])
