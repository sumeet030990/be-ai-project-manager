"""add epics table and restructure features to Epic->Feature->Story hierarchy

Revision ID: o6p7q8r9s0t1
Revises: n5o6p7q8r9s0
Create Date: 2026-06-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "o6p7q8r9s0t1"
down_revision: Union[str, None] = "n5o6p7q8r9s0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create epics table (mirrors old features structure with jira_epic_key)
    op.create_table(
        "epics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jira_epic_key", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_epics_project_id", "epics", ["project_id"])
    op.create_index("ix_epics_status", "epics", ["status"])

    # 2. Migrate existing features to epics (preserve IDs so foreign-key references stay intact)
    #    Each old "feature" (which held jira_epic_key) becomes an Epic with the same UUID.
    op.execute("""
        INSERT INTO epics (id, project_id, created_by, name, description, "order", status, priority, jira_epic_key, created_at, updated_at)
        SELECT id, project_id, created_by, name, description, "order", status, priority, jira_epic_key, created_at, updated_at
        FROM features
    """)

    # 3. Add epic_id column to features (nullable first so we can fill it)
    op.add_column("features", sa.Column("epic_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "features_epic_id_fkey",
        "features",
        "epics",
        ["epic_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Each existing feature points to the epic with the same UUID
    #    (1-to-1: the old "feature" record is now both an epic AND a feature under that epic)
    op.execute("UPDATE features SET epic_id = id")

    # 5. Make epic_id NOT NULL
    op.alter_column("features", "epic_id", nullable=False)

    # 6. Drop the old project_id FK and column from features
    #    Note: the FK constraint was originally named modules_project_id_fkey (table was renamed from modules)
    op.execute("""
        DO $$
        DECLARE
            cname text;
        BEGIN
            SELECT con.conname INTO cname
            FROM pg_constraint con
            JOIN pg_class cls ON con.conrelid = cls.oid
            WHERE cls.relname = 'features'
              AND con.contype = 'f'
              AND con.conname LIKE '%project_id%';
            IF cname IS NOT NULL THEN
                EXECUTE format('ALTER TABLE features DROP CONSTRAINT %I', cname);
            END IF;
        END $$;
    """)
    op.drop_index("ix_features_project_id", table_name="features")
    op.drop_column("features", "project_id")

    # 7. Drop jira_epic_key from features (it now lives on epics)
    op.drop_column("features", "jira_epic_key")

    # 8. Rename the features index to reflect new FK
    op.create_index("ix_features_epic_id", "features", ["epic_id"])


def downgrade() -> None:
    # Reverse: restore project_id and jira_epic_key on features, drop epics
    op.drop_index("ix_features_epic_id", table_name="features")

    op.add_column("features", sa.Column("jira_epic_key", sa.String(length=50), nullable=True))
    op.add_column("features", sa.Column("project_id", sa.UUID(), nullable=True))

    # Restore project_id from epics
    op.execute("""
        UPDATE features f
        SET project_id = e.project_id,
            jira_epic_key = e.jira_epic_key
        FROM epics e
        WHERE f.epic_id = e.id
    """)

    op.alter_column("features", "project_id", nullable=False)
    op.create_foreign_key(
        "features_project_id_fkey",
        "features",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_features_project_id", "features", ["project_id"])

    op.drop_constraint("features_epic_id_fkey", "features", type_="foreignkey")
    op.drop_column("features", "epic_id")

    op.drop_index("ix_epics_status", table_name="epics")
    op.drop_index("ix_epics_project_id", table_name="epics")
    op.drop_table("epics")
