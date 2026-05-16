"""add jira_epic_key to modules, drop parent_id from stories

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "k2l3m4n5o6p7"
down_revision: Union[str, None] = "j1k2l3m4n5o6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("modules", sa.Column("jira_epic_key", sa.String(50), nullable=True))

    op.drop_index("ix_stories_parent_id", table_name="stories")
    op.drop_constraint("fk_stories_parent_id_stories", "stories", type_="foreignkey")
    op.drop_column("stories", "parent_id")


def downgrade() -> None:
    op.drop_column("modules", "jira_epic_key")

    op.add_column("stories", sa.Column("parent_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_stories_parent_id_stories",
        "stories", "stories",
        ["parent_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_stories_parent_id", "stories", ["parent_id"], unique=False)
