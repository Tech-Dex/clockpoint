"""create groups_users table

Revision ID: d43649786045
Revises: 8da3fc4b9264
Create Date: 2022-02-10 20:36:37.328653

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d43649786045"
down_revision = "8da3fc4b9264"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    op.create_table(
        "groups_users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("groups_id", sa.Integer, nullable=False),
        sa.Column("users_id", sa.Integer, nullable=False),
        sa.Column("roles_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_foreign_key(
        "fk_groups_users_groups_id_groups",
        "groups_users",
        "groups",
        ["groups_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_groups_users_users_id_users",
        "groups_users",
        "users",
        ["users_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_groups_users_roles_id_roles",
        "groups_users",
        "roles",
        ["roles_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_groups_id_users_id",
        "groups_users",
        ["groups_id", "users_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("groups_users")
