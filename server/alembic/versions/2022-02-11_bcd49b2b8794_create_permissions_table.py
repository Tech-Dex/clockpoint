"""create permissions table

Revision ID: bcd49b2b8794
Revises: d43649786045
Create Date: 2022-02-11 22:08:26.111644

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "bcd49b2b8794"
down_revision = "d43649786045"
branch_labels = None
depends_on = None

# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    roles_table = op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("permission", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_index("ix_permission", "permissions", ["permission"], unique=True)

    op.bulk_insert(
        roles_table,
        [
            {"permission": "view_own_report"},
            {"permission": "invite_user"},
            {"permission": "kick_user"},
            {"permission": "generate_report"},
            {"permission": "view_report"},
            {"permission": "assign_role"},
            {"permission": "edit"},
            {"permission": "delete"},
        ],
    )


def downgrade():
    op.drop_table("permissions")
