import json
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


class BaseGroupUser(ConfigModel):
    group_id: int
    user_id: int
    role_id: int


class DBGroupUser(DBCoreModel, BaseGroupUser):
    class Meta:
        table_name: str = "groups_users"

    @staticmethod
    async def save_batch(
        mysql_driver: Database, group_id: int, users_roles: list[dict]
    ) -> bool:
        async with mysql_driver.transaction():
            groups_users: str = "groups_users"
            columns: list = [
                "groups_id",
                "users_id",
                "roles_id",
                "created_at",
                "updated_at",
            ]
            now = datetime.now()
            values = [
                f"{group_id}, {user_role['user_id']}, {user_role['role_id']}, "
                f"{now.strftime('%Y-%m-%d %H:%M:%S')!r}, {now.strftime('%Y-%m-%d %H:%M:%S')!r}"
                for user_role in users_roles
            ]
            query: str = create_batch_insert_query(groups_users, columns, values)

            try:
                await mysql_driver.execute(query)
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="User already exists in group",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return True

    @staticmethod
    async def get_group_user_by_reflection_with_id(
        mysql_driver: Database, column_reflection_name: str, reflection_id: int
    ) -> list[Mapping]:
        """
        column_reflection_name: name of the column in the groups_users table
        reflection_id: id to match the column_reflection_name,
        column_reflection_name can be users_id, roles_id, groups_id

        column_reflection_name : reflection_id
        e.g. groups_id: 9, users_id: 1, roles_id: 3

        usage: await DBGroupUser.get_groups_user_by_reflection_with_id(mysql_driver, "groups_id", 9)
               await DBGroupUser.get_groups_user_by_reflection_with_id(mysql_driver, "users_id", 1)
        """
        groups_users: Table = Table("groups_users")
        groups: Table = Table("groups")
        users: Table = Table("users")
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(groups_users)
            .select(
                AggregateFunction(
                    "json_object",
                    "user",
                    AggregateFunction(
                        "json_object",
                        "id",
                        users.id,
                        "email",
                        users.email,
                        "username",
                        users.username,
                        "first_name",
                        users.first_name,
                        "last_name",
                        users.last_name,
                    ),
                    "role",
                    AggregateFunction(
                        "json_object",
                        "id",
                        roles.id,
                        "role",
                        roles.role,
                    ),
                    "group",
                    AggregateFunction(
                        "json_object",
                        "id",
                        groups.id,
                        "name",
                        groups.name,
                        "description",
                        groups.description,
                    ),
                )
            )
            .join(users)
            .on(groups_users.users_id == users.id)
            .join(roles)
            .on(groups_users.roles_id == roles.id)
            .join(groups)
            .on(groups_users.groups_id == groups.id)
            .where(
                getattr(groups_users, column_reflection_name)
                == Parameter(f":{column_reflection_name}")
            )
            .where(groups_users.deleted_at.isnull())
        )
        values = {column_reflection_name: reflection_id}

        try:
            groups_user_role: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        return [
            json.loads(group_user_role_mapper)
            for group_user_role in groups_user_role
            for group_user_role_mapper in group_user_role
        ]

    @staticmethod
    async def get_group_users_by_role(
        mysql_driver: Database, group_id: int, role: str
    ) -> list[Mapping]:
        groups_users: Table = Table("groups_users")
        users: Table = Table("users")
        roles: Table = Table("roles")
        query = (
            MySQLQuery.select(
                users.id,
                users.email,
                users.username,
                users.first_name,
                users.last_name,
            )
            .from_(groups_users)
            .join(users)
            .on(groups_users.users_id == users.id)
            .join(roles)
            .on(groups_users.roles_id == roles.id)
            .where(groups_users.groups_id == Parameter(":groups_id"))
            .where(roles.role == Parameter(":role"))
            .where(groups_users.deleted_at.isnull())
        )
        values = {"groups_id": group_id, "role": role}

        try:
            users_by_role: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        return users_by_role


class BaseGroupUserResponse(ConfigModel):
    groups_users: list[BaseGroupUser]