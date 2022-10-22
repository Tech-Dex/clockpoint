from __future__ import annotations

import json
from datetime import datetime
from typing import Mapping

from databases import Database
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from pypika.terms import AggregateFunction

from app.core.database.mysql_driver import create_batch_insert_query
from app.exceptions import base as base_exceptions, group_user as group_user_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseGroupUser(ConfigModel):
    groups_id: int
    users_id: int
    roles_id: int


class DBGroupUser(DBCoreModel, BaseGroupUser):
    class Meta:
        table_name: str = "groups_users"

    @classmethod
    async def save_batch(
        cls,
        mysql_driver: Database,
        groups_id: int,
        users_roles: list[dict],
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> bool:
        async with mysql_driver.transaction():
            groups_users: str = cls.Meta.table_name
            columns: list = [
                "groups_id",
                "users_id",
                "roles_id",
                "created_at",
                "updated_at",
            ]
            now = datetime.now()
            values = [
                f"{groups_id}, {user_role['users_id']}, {user_role['roles_id']}, "
                f"{now.strftime('%Y-%m-%d %H:%M:%S')!r}, {now.strftime('%Y-%m-%d %H:%M:%S')!r}"
                for user_role in users_roles
            ]
            query: str = create_batch_insert_query(groups_users, columns, values)

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
    async def get_group_user_by_reflection_with_id(
        cls, mysql_driver: Database, column_reflection_name: str, reflection_id: int
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
        groups_users: Table = Table(cls.Meta.table_name)
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
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

        return [
            json.loads(group_user_role_mapper)
            for group_user_role in groups_user_role
            for group_user_role_mapper in group_user_role
        ]

    @classmethod
    async def get_groups_user_by_reflection_with_ids(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_ids: list[int],
    ) -> any:
        groups_users: Table = Table(cls.Meta.table_name)
        groups: Table = Table("groups")
        users: Table = Table("users")
        roles: Table = Table("roles")
        query = (
            MySQLQuery.from_(groups_users)
            .select(
                AggregateFunction(
                    "json_arrayagg",
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
                getattr(groups_users, column_reflection_name).isin(
                    Parameter(f":{column_reflection_name}")
                )
            )
            .where(groups_users.deleted_at.isnull())
        )
        values = {column_reflection_name: reflection_ids}

        try:
            groups_user_role: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])
        formatted_groups_user_role = {}
        for group_user_role_w in groups_user_role[0]:
            for group_user_role in json.loads(group_user_role_w):
                if (
                    group_user_role["group"]["id"]
                    not in formatted_groups_user_role.keys()
                ):
                    formatted_groups_user_role[group_user_role["group"]["id"]] = []
                formatted_groups_user_role[group_user_role["group"]["id"]].append(
                    group_user_role
                )

        return formatted_groups_user_role

    @classmethod
    async def get_group_users_by_role(
        cls,
        mysql_driver: Database,
        groups_id: int,
        role: str,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[Mapping]:
        groups_users: Table = Table(cls.Meta.table_name)
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
        values = {"groups_id": groups_id, "role": role}

        try:
            users_by_role: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError:
            raise exc or group_user_exceptions.UserNotInGroupException()

        return users_by_role

    async def remove_entry(self, mysql_driver: Database) -> int:
        """
        usage: await db_group.remove_user(mysql_driver, 1)
        """
        async with mysql_driver.transaction():
            groups_users: Table = Table(self.Meta.table_name)
            query = (
                MySQLQuery.from_(groups_users)
                .delete()
                .where(groups_users.groups_id == Parameter(":groups_id"))
                .where(groups_users.users_id == Parameter(":users_id"))
            )
            values = {
                "groups_id": self.groups_id,
                "users_id": self.users_id,
            }

            try:
                row_id_groups_users: int = await mysql_driver.execute(
                    query.get_sql(), values
                )
            except MySQLError as mySQLError:
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

            return row_id_groups_users

    @classmethod
    async def is_user_in_group(
        cls,
        mysql_driver: Database,
        users_id: int,
        groups_id: int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> DBGroupUser | None:
        groups_users: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(groups_users)
            .select("*")
            .where(groups_users.groups_id == Parameter(":groups_id"))
            .where(groups_users.users_id == Parameter(":users_id"))
        )
        values = {
            "groups_id": groups_id,
            "users_id": users_id,
        }

        try:
            group_user: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

        if not bypass_exc and not group_user:
            raise exc or group_user_exceptions.UserNotInGroupException()

        if not group_user and bypass_exc:
            return None

        return cls(**group_user)

    @classmethod
    async def are_users_in_group(
        cls, mysql_driver: Database, users_ids: list[int], groups_id: int
    ) -> list[DBGroupUser]:
        groups_users: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(groups_users)
            .select("*")
            .where(groups_users.groups_id == Parameter(":groups_id"))
            .where(groups_users.users_id.isin(Parameter(":users_id")))
        )
        values = {
            "groups_id": groups_id,
            "users_id": users_ids,
        }

        try:
            groups_users: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

        if not groups_users:
            return []

        return [cls(**group_users) for group_users in groups_users]

    @classmethod
    async def get_users_in_group_with_generate_report_permission(
        cls,
        mysql_driver: Database,
        groups_id: int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[Mapping]:
        groups_users: Table = Table(cls.Meta.table_name)
        users: Table = Table("users")
        roles: Table = Table("roles")
        permissions: Table = Table("permissions")
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
            .join(permissions)
            .on(roles.permissions_id == permissions.id)
            .where(groups_users.groups_id == Parameter(":groups_id"))
            .where(permissions.permission == "generate_report")
            .where(groups_users.deleted_at.isnull())
        )
        values = {"groups_id": groups_id}

        try:
            results: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
            if not results:
                if bypass_exc:
                    return []
                raise exc or group_user_exceptions.UserNotInGroupException()

            return results
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])
