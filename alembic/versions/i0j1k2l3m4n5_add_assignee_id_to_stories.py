"""add assignee_id to stories

Revision ID: i0j1k2l3m4n5
Revises: h9i0j1k2l3m4
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "i0j1k2l3m4n5"
down_revision: Union[str, None] = "h9i0j1k2l3m4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stories", sa.Column("assignee_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_stories_assignee_id_users",
        "stories", "users",
        ["assignee_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_stories_assignee_id", "stories", ["assignee_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stories_assignee_id", table_name="stories")
    op.drop_constraint("fk_stories_assignee_id_users", "stories", type_="foreignkey")
    op.drop_column("stories", "assignee_id")
