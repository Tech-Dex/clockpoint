import json
import logging
from datetime import datetime
from typing import Mapping

from databases import Database
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from pypika.terms import AggregateFunction
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.database.mysql_driver import create_batch_insert_query
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseRolePermission(ConfigModel):
    role_id: int
    permission_id: int


class DBRolePermission(DBCoreModel, BaseRolePermission):
    class Meta:
        table_name: str = "roles_permissions"

    async def save(self, mysql_driver: Database) -> "DBRolePermission":
        async with mysql_driver.transaction():
            roles_permissions: Table = Table("roles_permissions")
            query = (
                MySQLQuery.into(roles_permissions)
                .columns(
                    roles_permissions.roles_id,
                    roles_permissions.permissions_id,
                    roles_permissions.created_at,
                    roles_permissions.updated_at,
                )
                .insert(
                    Parameter(":role_id"),
                    Parameter(":permission_id"),
                    Parameter(":created_at"),
                    Parameter(":updated_at"),
                )
            )

            values = {
                "role_id": self.role_id,
                "permission_id": self.permission_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }

            try:
                row_id: int = await mysql_driver.execute(query, values)
                self.id = row_id
                return self
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="Role already has permission",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

    @staticmethod
    async def save_batch(mysql_driver: Database, permissions: list[dict]) -> bool:
        async with mysql_driver.transaction():
            roles_permissions: str = "roles_permissions"
            columns = [
                "roles_id",
                "permissions_id",
                "created_at",
                "updated_at",
            ]
            now = datetime.now()
            values = [
                f"{permission['role_id']!r}, {permission['permission_id']},"
                f"{now.strftime('%Y-%m-%d %H:%M:%S')!r}, {now.strftime('%Y-%m-%d %H:%M:%S')!r}"
                for permission in permissions
            ]
            query: str = create_batch_insert_query(roles_permissions, columns, values)

            try:
                await mysql_driver.execute(query)
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="Role already has permission",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return True

    @staticmethod
    async def get_role_permissions(
        mysql_driver: Database, role_id: int
    ) -> list[Mapping]:
        roles_permissions: Table = Table("roles_permissions")
        roles: Table = Table("roles")
        permissions: Table = Table("permissions")
        query = (
            MySQLQuery.from_(roles_permissions)
            .select(
                AggregateFunction(
                    "json_object",
                    "role",
                    AggregateFunction(
                        "json_object",
                        "id",
                        roles.id,
                        "role",
                        roles.role,
                    ),
                    "permissions",
                    AggregateFunction(
                        "json_arrayagg",
                        MySQLQuery.from_(permissions)
                        .select(
                            AggregateFunction(
                                "json_object",
                                "id",
                                permissions.id,
                                "permission",
                                permissions.permission,
                            )
                        )
                        .where(permissions.id == roles_permissions.permissions_id),
                    ),
                )
            )
            .join(roles)
            .on(roles_permissions.roles_id == roles.id)
            .where(roles_permissions.roles_id == Parameter(":role_id"))
            .where(roles_permissions.deleted_at.isnull())
        )
        values = {"role_id": role_id}

        try:
            full_role_permissions: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        return [
            {
                "role": json.loads(json.loads(role_permission_mapper)["role"]),
                "permissions": [
                    {"permission": json.loads(permission)}
                    for permission in json.loads(role_permission_mapper)["permissions"]
                ],
            }
            for role_permission in full_role_permissions
            for role_permission_mapper in role_permission
        ]

    @staticmethod
    async def get_roles_permission(
        mysql_driver: Database, permission_id: int
    ) -> list[Mapping]:
        roles_permissions: Table = Table("roles_permissions")
        roles: Table = Table("roles")
        permissions: Table = Table("permissions")
        query = (
            MySQLQuery.from_(roles_permissions)
            .select(
                AggregateFunction(
                    "json_object",
                    "roles",
                    AggregateFunction(
                        "json_arrayagg",
                        MySQLQuery.from_(roles)
                        .select(
                            AggregateFunction(
                                "json_object",
                                "id",
                                roles.id,
                                "role",
                                roles.role,
                            )
                        )
                        .where(roles.id == roles_permissions.roles_id),
                    ),
                    "permission",
                    AggregateFunction(
                        "json_object",
                        "id",
                        permissions.id,
                        "permission",
                        permissions.permission,
                    ),
                )
            )
            .join(permissions)
            .on(roles_permissions.permissions_id == permissions.id)
            .where(roles_permissions.permissions_id == Parameter(":permission_id"))
            .where(roles_permissions.deleted_at.isnull())
        )
        values = {"permission_id": permission_id}

        try:
            full_roles_permission: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        logging.warning(full_roles_permission)
        return [
            {
                "roles": [
                    {"role": json.loads(permission)}
                    for permission in json.loads(role_permission_mapper)["roles"]
                ],
                "permission": json.loads(
                    json.loads(role_permission_mapper)["permission"]
                ),
            }
            for role_permission in full_roles_permission
            for role_permission_mapper in role_permission
        ]
