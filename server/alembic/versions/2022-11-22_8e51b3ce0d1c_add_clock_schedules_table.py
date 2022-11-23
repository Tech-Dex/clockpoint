"""add clock_schedules table

Revision ID: 8e51b3ce0d1c
Revises: 8c5ef883acee
Create Date: 2022-11-22 20:03:49.845771

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8e51b3ce0d1c"
down_revision = "8c5ef883acee"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "clock_schedules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("groups_users_id", sa.Integer, nullable=False),
        sa.Column("start_at", sa.Time, nullable=False),
        sa.Column("stop_at", sa.Time, nullable=False),
        sa.Column("monday", sa.Boolean, nullable=False, default=False),
        sa.Column("tuesday", sa.Boolean, nullable=False, default=False),
        sa.Column("wednesday", sa.Boolean, nullable=False, default=False),
        sa.Column("thursday", sa.Boolean, nullable=False, default=False),
        sa.Column("friday", sa.Boolean, nullable=False, default=False),
        sa.Column("saturday", sa.Boolean, nullable=False, default=False),
        sa.Column("sunday", sa.Boolean, nullable=False, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_foreign_key(
        "fk_clock_schedules_groups_users_id_groups_users",
        "clock_schedules",
        "groups_users",
        ["groups_users_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_groups_users_id_start_at_stop_at",
        "clock_schedules",
        ["groups_users_id", "start_at", "stop_at"],
        unique=True,
    )


def downgrade():
    op.drop_table("clock_schedules")
