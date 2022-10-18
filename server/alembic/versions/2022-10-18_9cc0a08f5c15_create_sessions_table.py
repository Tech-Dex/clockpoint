"""create sessions table

Revision ID: 9cc0a08f5c15
Revises: a4093dce64dc
Create Date: 2022-10-18 18:56:51.206859

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9cc0a08f5c15"
down_revision = "a4093dce64dc"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "clock_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("start_at", sa.DateTime, nullable=False),
        sa.Column("stop_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table("clock_sessions")
