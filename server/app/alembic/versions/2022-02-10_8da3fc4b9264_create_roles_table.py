"""create roles table

Revision ID: 8da3fc4b9264
Revises: c23fd93d65bb
Create Date: 2022-02-10 20:48:18.171647

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8da3fc4b9264"
down_revision = "c23fd93d65bb"
branch_labels = None
depends_on = None


# "ix": "ix_%(column_0_label)s"
# "uq": "uq_%(table_name)s_%(column_0_name)s"
# "ck": "ck_%(table_name)s_%(constraint_name)s"
# "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
# "pk": "pk_%(table_name)s"


def upgrade():
    roles_table = op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("groups_id", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )

    op.create_index("ix_role", "roles", ["role"], unique=True)

    # op.bulk_insert(
    #     roles_table,
    #     [
    #         {"role": "owner"},
    #         {"role": "admin"},
    #         {"role": "user"},
    #     ],
    # )


def downgrade():
    op.drop_table("roles")
