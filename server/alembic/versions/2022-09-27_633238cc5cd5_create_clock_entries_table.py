"""create clock_entries table

Revision ID: 633238cc5cd5
Revises: 3933c5e87101
Create Date: 2022-09-27 22:12:07.246924

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "633238cc5cd5"
down_revision = "3933c5e87101"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "clock_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("datetime", sa.DateTime, nullable=False),
        sa.Column(
            "type",
            sa.Enum("start", "stop", "in", "out", name="clock_entry_type"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table("clock_entries")
