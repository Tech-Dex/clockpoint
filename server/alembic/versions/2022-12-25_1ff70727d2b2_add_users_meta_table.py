"""add users_meta table

Revision ID: 1ff70727d2b2
Revises: 8e51b3ce0d1c
Create Date: 2022-12-25 12:12:56.166704

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "1ff70727d2b2"
down_revision = "8e51b3ce0d1c"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "users_meta",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("has_push_notifications", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_foreign_key(
        "fk_users_meta_user_ids_users",
        "users_meta",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index("ix_users_meta", "users_meta", ["user_id"], unique=True)


def downgrade():
    op.drop_table("users_meta")
