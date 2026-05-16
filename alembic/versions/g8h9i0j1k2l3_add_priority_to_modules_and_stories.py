"""add priority to modules and stories

Revision ID: g8h9i0j1k2l3
Revises: f7g8h9i0j1k2
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g8h9i0j1k2l3'
down_revision: Union[str, None] = 'f7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('modules', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('stories', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('stories', 'priority')
    op.drop_column('modules', 'priority')
