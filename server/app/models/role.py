from datetime import datetime
from typing import Mapping, Optional

from databases import Database
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.database.mysql_driver import create_batch_insert_query
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.enums.roles import Roles


class BaseRole(ConfigModel):
    role: str


class DBRole(DBCoreModel, BaseRole):
    @staticmethod
    async def save_batch(mysql_driver: Database, group_id: int, group_roles: list):
        async with mysql_driver.transaction():
            group_roles: list[dict] = DBRole.create_roles(group_roles)
            roles: str = "roles"
            columns: list = ["role", "groups_id", "created_at", "updated_at"]
            now = datetime.now()
            values: list = [
                f"{role['role']!r}, {group_id}, "
                f"{now.strftime('%Y-%m-%d %H:%M:%S')!r}, {now.strftime('%Y-%m-%d %H:%M:%S')!r}"
                for role in group_roles
            ]
            query: str = create_batch_insert_query(roles, columns, values)

            try:
                await mysql_driver.execute(query)

            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="Role already exists",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return True

    @classmethod
    async def get_all(cls, mysql_driver: Database) -> list["DBRole"]:
        """
        usage: [BaseRole(**db_role.dict()) for db_role in await DBRole.get_all(mysql_driver)]
        """
        roles: Table = Table("roles")
        query = MySQLQuery.from_(roles).select(roles.id, roles.role)

        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())

        if roles:
            return [cls(**role) for role in roles]

    @classmethod
    async def get_role_by_name(
        cls, mysql_driver: Database, role_name: str
    ) -> Optional["DBRole"]:
        """
        usage: BaseRole(**(await DBRole.get_role_owner(mysql_driver)).dict())
        """
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.role == Parameter(":role_name"))
        )
        values = {"role_name": role_name}

        role: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)

        if role:
            return cls(**role)

    @classmethod
    async def get_role_owner(cls, mysql_driver: Database) -> Optional["DBRole"]:
        return await cls.get_role_by_name(mysql_driver, Roles.OWNER)

    @classmethod
    async def get_role_admin(cls, mysql_driver: Database) -> Optional["DBRole"]:
        return await cls.get_role_by_name(mysql_driver, Roles.ADMIN)

    @classmethod
    async def get_role_user(cls, mysql_driver: Database) -> Optional["DBRole"]:
        return await cls.get_role_by_name(mysql_driver, Roles.USER)

    @staticmethod
    def get_default_roles() -> list:
        return [
            {"role": Roles.OWNER.value},
            {"role": Roles.ADMIN.value},
            {"role": Roles.USER.value},
        ]

    @staticmethod
    def create_roles(custom_roles: list):
        default_roles: list = DBRole.get_default_roles()
        for custom_role in custom_roles:
            default_roles.append({"role": custom_role})

        return default_roles

    @staticmethod
    async def get_default_full_permissions(mysql_driver: Database) -> list:
        permissions: Table = Table("permissions")
        query = MySQLQuery.from_(permissions).select(
            permissions.id, permissions.permission
        )

        permissions: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())
        if permissions:
            return [
                (permission["id"], permission["permission"])
                for permission in permissions
            ]

    @staticmethod
    async def create_role_permission_pairs(
        mysql_driver: Database, group_id: int, custom_roles_permissions: list[dict]
    ):
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.groups_id == Parameter(":group_id"))
        )
        values = {"group_id": group_id}

        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)
        if roles and set(
            [
                custom_role_permission["role"]
                for custom_role_permission in custom_roles_permissions
            ]
        ).issubset(set([role["role"] for role in roles])):
            full_permissions: list[tuple] = await DBRole.get_default_full_permissions(
                mysql_driver
            )
            if set(
                [
                    custom_role_permission["permission"]
                    for custom_role_permission in custom_roles_permissions
                ]
            ).issubset(
                set(
                    [
                        permission_name
                        for permission_id, permission_name in full_permissions
                    ]
                )
            ):
                final_custom_permissions: list = []

                for role in roles:
                    if role["role"] == Roles.OWNER.value:
                        for (
                            owner_permission_id,
                            owner_permission_name,
                        ) in full_permissions:
                            final_custom_permissions.append(
                                {
                                    "role_id": role["id"],
                                    "permission_id": owner_permission_id,
                                }
                            )
                    break

                for custom_role_permission in custom_roles_permissions:
                    for role in roles:
                        if role["role"] == custom_role_permission["role"]:
                            for permission_id, permission_name in full_permissions:
                                if (
                                    permission_name
                                    == custom_role_permission["permission"]
                                ):
                                    final_custom_permissions.append(
                                        {
                                            "role_id": role["id"],
                                            "permission_id": permission_id,
                                        }
                                    )
                                    break
                            break

                if final_custom_permissions:
                    return final_custom_permissions

            raise StarletteHTTPException(
                status_code=422,
                detail="Permissions not found",
            )

        raise StarletteHTTPException(
            status_code=422,
            detail="Roles not found",
        )


class BaseRoleWrapper(BaseRole):
    pass


class BaseRoleResponse(ConfigModel):
    role: BaseRoleWrapper


class BaseRoleRequest(ConfigModel):
    role: str
