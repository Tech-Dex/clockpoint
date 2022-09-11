from __future__ import annotations

from typing import Mapping

from databases import Database
from pypika import MySQLQuery, Parameter, Table

from app.exceptions import base as base_exceptions, permission as permission_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BasePermission(ConfigModel):
    permission: str


class DBPermission(DBCoreModel, BasePermission):
    class Meta:
        table_name: str = "permissions"

    @classmethod
    async def get_owner_permissions(cls, mysql_driver: Database) -> list[DBPermission]:
        permissions: Table = Table(cls.Meta.table_name)
        query = MySQLQuery.from_(permissions).select(
            permissions.id, permissions.permission
        )

        permissions: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())
        if not permissions:
            raise permission_exceptions.PermissionNotFoundException()

        return [DBPermission(**permission) for permission in permissions]

    @classmethod
    async def get_admin_permissions(cls, mysql_driver: Database) -> list[DBPermission]:
        admin_permissions = [
            "view_own_report",
            "invite_user",
            "kick_user",
            "generate_report",
            "view_report",
            "assign_role",
        ]
        return await cls.get_permissions_by_name(mysql_driver, admin_permissions)

    @classmethod
    async def get_user_permissions(cls, mysql_driver: Database) -> list[DBPermission]:
        user_permissions = ["view_own_report"]
        return await cls.get_permissions_by_name(mysql_driver, user_permissions)

    @classmethod
    async def get_permissions_by_name(
        cls, mysql_driver: Database, permission_name: list[str]
    ) -> list[DBPermission]:
        permissions: Table = Table(cls.Meta.table_name)
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
        if not permissions:
            raise permission_exceptions.PermissionNotFoundException()

        if not isinstance(permissions, list):
            raise base_exceptions.CustomBaseException(detail="Unexpected error")

        return [DBPermission(**permission) for permission in permissions]


class BaseRoleWrapper(BasePermission):
    pass


class BasePermissionResponse(ConfigModel):
    permission: BaseRoleWrapper
