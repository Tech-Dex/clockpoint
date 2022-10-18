"""add session in clock_groups_users_sessions_entries table

Revision ID: 8c5ef883acee
Revises: bbb6cbdfb965
Create Date: 2022-10-18 19:31:59.127224

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8c5ef883acee"
down_revision = "9cc0a08f5c15"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.add_column(
        "clock_groups_users_sessions_entries",
        sa.Column("clock_sessions_id", sa.Integer, nullable=False),
    )

    op.create_foreign_key(
        "fk_clock_g_u_s_entries_clock_sessions_id_clock_sessions",
        "clock_groups_users_sessions_entries",
        "clock_sessions",
        ["clock_sessions_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "fk_clock_g_u_s_entries_clock_sessions_id_clock_sessions",
        "clock_groups_users_entries",
        type_="foreignkey",
    )
    op.drop_column("clock_groups_users_sessions_entries", "clock_sessions_id")
