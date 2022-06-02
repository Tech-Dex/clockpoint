import asyncio
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
from app.models.group import BaseGroupCustomRolePermissionCreate
from app.models.permission import DBPermission


class BaseRole(ConfigModel):
    role: str


class DBRole(DBCoreModel, BaseRole):
    class Meta:
        table_name: str = "roles"

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
    async def get_all_by_group_id(
        cls, mysql_driver: Database, group_id: int
    ) -> list["DBRole"]:
        """
        usage: [BaseRole(**db_role.dict()) for db_role in await DBRole.get_all(mysql_driver, 1)]
        """
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.deleted_at.isnull())
            .where(roles.groups_id == Parameter(f":group_id"))
        )

        values = {"group_id": group_id}
        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)

        return [cls(**role) for role in roles]

    @classmethod
    async def get_role_owner_by_group(
        cls, mysql_driver: Database, group_id: int
    ) -> Optional["DBRole"]:
        return await cls.get_role_type_by_group(
            mysql_driver, group_id, Roles.OWNER.value
        )

    @classmethod
    async def get_role_admin_by_group(
        cls, mysql_driver: Database, group_id: int
    ) -> Optional["DBRole"]:
        return await cls.get_role_type_by_group(
            mysql_driver, group_id, Roles.ADMIN.value
        )

    @classmethod
    async def get_role_user_by_group(
        cls, mysql_driver: Database, group_id: int
    ) -> Optional["DBRole"]:
        return await cls.get_role_type_by_group(
            mysql_driver, group_id, Roles.USER.value
        )

    @classmethod
    async def get_role_type_by_group(
        cls, mysql_driver: Database, group_id: int, role: str
    ) -> Optional["DBRole"]:
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(roles)
            .select("*")
            .where(roles.deleted_at.isnull())
            .where(roles.groups_id == Parameter(f":group_id"))
            .where(roles.role == Parameter(f":role"))
        )

        values = {"group_id": group_id, "role": role}
        role: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)

        return cls(**role)

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
    async def get_owner_permissions(mysql_driver: Database) -> list:
        permissions: Table = Table("permissions")
        query = MySQLQuery.from_(permissions).select(
            permissions.id, permissions.permission
        )

        permissions: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())
        if permissions:
            return [DBPermission(**permission) for permission in permissions]

    @classmethod
    async def get_admin_permissions(cls, mysql_driver: Database) -> list:
        admin_permissions = [
            "view_own_report",
            "invite_user",
            "kick_user",
            "generate_report",
            "view_report",
        ]
        return await cls.get_permission_by_name(mysql_driver, admin_permissions)

    @classmethod
    async def get_user_permissions(cls, mysql_driver: Database) -> list:
        user_permissions = ["view_own_report"]
        return await cls.get_permission_by_name(mysql_driver, user_permissions)

    @classmethod
    async def get_permission_by_name(
        cls, mysql_driver: Database, permission_name: list[str]
    ) -> list[DBPermission]:
        permissions: Table = Table("permissions")
        query = (
            MySQLQuery.from_(permissions)
            .select(permissions.id, permissions.permission)
            .where(permissions.permission.isin(Parameter(f":permissions")))
        )

        values = {
            "permissions": permission_name,
        }

        permissions: list[Mapping] = await mysql_driver.fetch_all(
            query.get_sql(), values
        )
        if permissions:
            if isinstance(permissions, list):
                return [DBPermission(**permission) for permission in permissions]

    @classmethod
    async def create_role_permission_pairs(
        cls,
        mysql_driver: Database,
        group_id: int,
        custom_roles_permissions: list[BaseGroupCustomRolePermissionCreate],
    ) -> list[dict]:
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.groups_id == Parameter(":group_id"))
        )
        values = {"group_id": group_id}

        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)

        futures = [
            DBRole.get_owner_permissions(mysql_driver),
            DBRole.get_admin_permissions(mysql_driver),
            DBRole.get_user_permissions(mysql_driver),
        ]
        result_futures: tuple = await asyncio.gather(*futures)
        owner_permissions, admin_permissions, user_permissions = result_futures

        final_role_permissions = []
        for role in roles:
            db_role: DBRole = cls(**role)
            match db_role.role:
                case Roles.OWNER.value:
                    for owner_permission in owner_permissions:
                        final_role_permissions.append(
                            {
                                "role_id": role["id"],
                                "permission_id": owner_permission.id,
                            }
                        )
                case Roles.ADMIN.value:
                    for admin_permission in admin_permissions:
                        final_role_permissions.append(
                            {
                                "role_id": role["id"],
                                "permission_id": admin_permission.id,
                            }
                        )
                case Roles.USER.value:
                    for user_permission in user_permissions:
                        final_role_permissions.append(
                            {
                                "role_id": role["id"],
                                "permission_id": user_permission.id,
                            }
                        )
                case _:
                    for custom_role_permission in custom_roles_permissions:
                        if custom_role_permission.role == db_role.role:
                            for permissions in custom_role_permission.permission:
                                for owner_permission in owner_permissions:
                                    if owner_permission.permission == permissions:
                                        final_role_permissions.append(
                                            {
                                                "role_id": db_role.id,
                                                "permission_id": owner_permission.id,
                                            }
                                        )
                                        break

        return final_role_permissions


class BaseRoleWrapper(BaseRole):
    pass


class BaseRoleResponse(ConfigModel):
    role: BaseRoleWrapper


class BaseRoleRequest(ConfigModel):
    role: str
