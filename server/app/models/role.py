from __future__ import annotations

from datetime import datetime
from typing import Mapping

from databases import Database
from databases.interfaces import Record
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table

from app.core.database.mysql_driver import create_batch_insert_query
from app.exceptions import base as base_exceptions, role as role_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.enums.roles import Roles
from app.models.permission import DBPermission
from app.schemas.v1.request import BaseGroupCustomRolePermissionCreateRequest


class BaseRole(ConfigModel):
    role: str


class DBRole(DBCoreModel, BaseRole):
    class Meta:
        table_name: str = "roles"

    @classmethod
    async def save_batch(
        cls,
        mysql_driver: Database,
        groups_id: int,
        group_roles: list,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> bool:
        async with mysql_driver.transaction():
            group_roles: list[dict] = DBRole.create_roles(group_roles)
            columns: list = ["role", "groups_id", "created_at", "updated_at"]
            now = datetime.now()
            values: list = [
                f"{role['role']!r}, {groups_id}, "
                f"{now.strftime('%Y-%m-%d %H:%M:%S')!r}, {now.strftime('%Y-%m-%d %H:%M:%S')!r}"
                for role in group_roles
            ]
            query: str = create_batch_insert_query(cls.Meta.table_name, columns, values)

            try:
                await mysql_driver.execute(query)
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    if bypass_exc:
                        return False
                    raise exc or base_exceptions.DuplicateResourceException(detail=msg)
            except MySQLError as mySQLError:
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

            return True

    @classmethod
    async def get_role_owner_by_group(
        cls, mysql_driver: Database, groups_id: int
    ) -> DBRole | None:
        return await cls.get_role_type_by_group(
            mysql_driver, groups_id, Roles.OWNER.value
        )

    @classmethod
    async def get_role_admin_by_group(
        cls, mysql_driver: Database, groups_id: int
    ) -> DBRole | None:
        return await cls.get_role_type_by_group(
            mysql_driver, groups_id, Roles.ADMIN.value
        )

    @classmethod
    async def get_role_user_by_group(
        cls, mysql_driver: Database, groups_id: int
    ) -> DBRole | None:
        return await cls.get_role_type_by_group(
            mysql_driver, groups_id, Roles.USER.value
        )

    @classmethod
    async def get_role_type_by_group(
        cls, mysql_driver: Database, groups_id: int, role: str
    ) -> DBRole | None:
        roles: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(roles)
            .select("*")
            .where(roles.deleted_at.isnull())
            .where(roles.groups_id == Parameter(f":groups_id"))
            .where(roles.role == Parameter(f":role"))
        )

        values = {"groups_id": groups_id, "role": role}
        role: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)

        if not role:
            raise role_exceptions.RoleNotFoundException()
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

    @classmethod
    async def create_role_permission_pairs(
        cls,
        mysql_driver: Database,
        owner_permissions: list[DBPermission],
        admin_permissions: list[DBPermission],
        user_permissions: list[DBPermission],
        groups_id: int,
        custom_roles_permissions: list[BaseGroupCustomRolePermissionCreateRequest],
    ) -> list[dict]:
        roles: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.groups_id == Parameter(":groups_id"))
        )
        values = {"groups_id": groups_id}

        test: Record
        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)

        final_role_permissions = []
        for role in roles:
            db_role: DBRole = cls(**role)
            match db_role.role:
                case Roles.OWNER.value:
                    for owner_permission in owner_permissions:
                        final_role_permissions.append(
                            {
                                "roles_id": role["id"],
                                "permissions_id": owner_permission.id,
                            }
                        )
                case Roles.ADMIN.value:
                    for admin_permission in admin_permissions:
                        final_role_permissions.append(
                            {
                                "roles_id": role["id"],
                                "permissions_id": admin_permission.id,
                            }
                        )
                case Roles.USER.value:
                    for user_permission in user_permissions:
                        final_role_permissions.append(
                            {
                                "roles_id": role["id"],
                                "permissions_id": user_permission.id,
                            }
                        )
                case _:
                    for custom_role_permission in custom_roles_permissions:
                        if custom_role_permission.role == db_role.role:
                            for permissions in custom_role_permission.permissions:
                                for owner_permission in owner_permissions:
                                    if owner_permission.permission == permissions:
                                        final_role_permissions.append(
                                            {
                                                "roles_id": db_role.id,
                                                "permissions_id": owner_permission.id,
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
