"""add jira_issue_key to stories

Revision ID: a2b3c4d5e6f7
Revises: 0503944248d7
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "0503944248d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stories", sa.Column("jira_issue_key", sa.String(length=50), nullable=True))
    op.create_index("ix_stories_jira_issue_key", "stories", ["jira_issue_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stories_jira_issue_key", table_name="stories")
    op.drop_column("stories", "jira_issue_key")
