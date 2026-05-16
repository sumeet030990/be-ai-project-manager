"""add jira_account_id to users

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h9i0j1k2l3m4"
down_revision: Union[str, None] = "g8h9i0j1k2l3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("jira_account_id", sa.String(length=255), nullable=True))
    op.create_index("ix_users_jira_account_id", "users", ["jira_account_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_jira_account_id", table_name="users")
    op.drop_column("users", "jira_account_id")
