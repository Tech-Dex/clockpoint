"""add phone_number in user

Revision ID: 3933c5e87101
Revises: e5d593676c14
Create Date: 2022-09-27 21:23:31.313827

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3933c5e87101"
down_revision = "e5d593676c14"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.add_column("users", sa.Column("phone_number", sa.String(15), nullable=True))


def downgrade():
    op.drop_column("users", "phone_number")
