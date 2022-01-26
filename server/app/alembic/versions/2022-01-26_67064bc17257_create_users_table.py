"""create users table

Revision ID: 67064bc17257
Revises: 
Create Date: 2022-01-26 20:21:52.859352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67064bc17257'
down_revision = None
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("salt", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("second_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_index("ix_usernames", "users", ["username"], unique=True)

    op.create_index("ix_emails", "users", ["email"], unique=True)


def downgrade():
    op.drop_table("users")

