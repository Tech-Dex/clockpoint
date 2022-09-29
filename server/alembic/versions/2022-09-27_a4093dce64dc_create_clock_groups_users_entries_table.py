"""create clock_groups_users_entries table

Revision ID: a4093dce64dc
Revises: 633238cc5cd5
Create Date: 2022-09-27 22:17:50.014895

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a4093dce64dc"
down_revision = "633238cc5cd5"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "clock_groups_users_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("groups_users_id", sa.Integer, nullable=False),
        sa.Column("clock_entries_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_foreign_key(
        "fk_clock_groups_users_entries_groups_users_id_groups_users",
        "clock_groups_users_entries",
        "groups_users",
        ["groups_users_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_clock_groups_users_entries_clock_entries_id_clock_entries",
        "clock_groups_users_entries",
        "clock_entries",
        ["clock_entries_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_groups_users_id_clock_entries_id",
        "clock_groups_users_entries",
        ["groups_users_id", "clock_entries_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("clock_groups_users_entries")
