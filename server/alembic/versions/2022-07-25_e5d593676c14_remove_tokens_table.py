"""remove tokens table

Revision ID: e5d593676c14
Revises: deee135305c9
Create Date: 2022-07-25 20:17:29.669491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5d593676c14'
down_revision = 'deee135305c9'
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.drop_table("tokens")


def downgrade():
    op.drop_table("tokens")
