"""create roles_permissions table

Revision ID: deee135305c9
Revises: bcd49b2b8794
Create Date: 2022-02-11 22:13:28.476123

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "deee135305c9"
down_revision = "bcd49b2b8794"
branch_labels = None
depends_on = None


# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    roles_permissions_table = op.create_table(
        "roles_permissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("roles_id", sa.Integer, nullable=False),
        sa.Column("permissions_id", sa.Integer, nullable=False),
        sa.Column("groups_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_foreign_key(
        "fk_roles_permissions_roles_id_roles",
        "roles_permissions",
        "roles",
        ["roles_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_roles_permissions_permissions_id_roles",
        "roles_permissions",
        "permissions",
        ["permissions_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_roles_permissions_groups_id_groups",
        "roles_permissions",
        "groups",
        ["groups_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_groups_users_roles_id_permissions_id",
        "roles_permissions",
        ["roles_id", "permissions_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("roles_permissions")
