"""add parent_id to stories

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "j1k2l3m4n5o6"
down_revision: Union[str, None] = "i0j1k2l3m4n5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stories", sa.Column("parent_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_stories_parent_id_stories",
        "stories", "stories",
        ["parent_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_stories_parent_id", "stories", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stories_parent_id", table_name="stories")
    op.drop_constraint("fk_stories_parent_id_stories", "stories", type_="foreignkey")
    op.drop_column("stories", "parent_id")
