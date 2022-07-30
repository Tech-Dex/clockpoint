"""create groups table

Revision ID: c23fd93d65bb
Revises: 54a81b09753c
Create Date: 2022-02-10 20:29:51.374647

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c23fd93d65bb"
down_revision = "54a81b09753c"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

def downgrade():
    op.drop_table("groups")
