from datetime import datetime
from typing import Mapping, Optional, List, Dict

from databases import Database
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.role import BaseRole, DBRole
from app.models.user import BaseUser


class BaseGroup(ConfigModel):
    name: str
    description: Optional[str]


class DBGroup(DBCoreModel, BaseGroup):
    @classmethod
    async def get_by_id(
        cls, mysql_driver: Database, group_id: int
    ) -> tuple[int, "DBGroup"]:
        groups: Table = Table("groups")
        query = (
            MySQLQuery.from_(groups)
            .select("*")
            .where(groups.id == Parameter(":group_id"))
        )
        values = {"group_id": group_id}

        group: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if group:
            return group["id"], cls(**group)

        raise StarletteHTTPException(status_code=404, detail="Group not found")

    @classmethod
    async def get_by_name(
        cls, mysql_driver: Database, group_name: str
    ) -> tuple[int, "DBGroup"]:
        groups: Table = Table("groups")
        query = (
            MySQLQuery.from_(groups)
            .select("*")
            .where(groups.name == Parameter(":group_name"))
        )
        values = {"group_name": group_name}

        group: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if group:
            return group["id"], cls(**group)

        raise StarletteHTTPException(status_code=404, detail="Group not found")

    async def save(self, mysql_driver: Database, user_id: int) -> tuple[int, int]:
        async with mysql_driver.transaction():
            groups: Table = Table("groups")
            query = (
                MySQLQuery.into(groups)
                .columns(
                    groups.name,
                    groups.description,
                    groups.created_at,
                    groups.updated_at,
                    groups.deleted_at,
                )
                .insert(
                    Parameter(":group_name"),
                    Parameter(":group_description"),
                    Parameter(":created_at"),
                    Parameter(":updated_at"),
                    Parameter(":deleted_at"),
                )
            )
            values = {
                "group_name": self.name,
                "group_description": self.description,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "deleted_at": self.deleted_at,
            }
            try:
                row_id_group: int = await mysql_driver.execute(query.get_sql(), values)
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="Group already exists",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )
            row_id_groups_users: int = await self.__create_groups_users(
                mysql_driver,
                row_id_group,
                user_id,
                (await DBRole.get_role_owner(mysql_driver)).id,
            )
            if row_id_groups_users == -1:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"Something weird happened in transaction, contact the administrator",
                )
            return row_id_group, row_id_groups_users

    async def __create_groups_users(
        self, mysql_driver: Database, group_id: int, user_id: int, role_id: int
    ) -> int:
        groups_users: Table = Table("groups_users")
        query = (
            MySQLQuery.into(groups_users)
            .columns(
                groups_users.groups_id,
                groups_users.users_id,
                groups_users.roles_id,
                groups_users.created_at,
                groups_users.updated_at,
                groups_users.deleted_at,
            )
            .insert(
                Parameter(":groups_id"),
                Parameter(":users_id"),
                Parameter(":roles_id"),
                Parameter(":created_at"),
                Parameter(":updated_at"),
                Parameter(":deleted_at"),
            )
        )
        values = {
            "groups_id": group_id,
            "users_id": user_id,
            "roles_id": role_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

        row_id_groups_users = -1
        try:
            row_id_groups_users: int = await mysql_driver.execute(
                query.get_sql(), values
            )
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

        return row_id_groups_users

    async def add_user(
        self, mysql_driver: Database, group_id: int, user_id: int
    ) -> int:
        async with mysql_driver.transaction():
            role_user: DBRole = await DBRole.get_role_user(mysql_driver)
            row_id_groups_users: int = await self.__create_groups_users(
                mysql_driver,
                group_id,
                user_id,
                role_user.id,
            )

            return row_id_groups_users

    @staticmethod
    async def remove_user(mysql_driver: Database, group_id: int, user_id: int) -> int:
        async with mysql_driver.transaction():
            groups_users: Table = Table("groups_users")
            query = (
                MySQLQuery.update(groups_users)
                .set(groups_users.deleted_at, Parameter(":deleted_at"))
                .where(groups_users.groups_id == Parameter(":groups_id"))
                .where(groups_users.users_id == Parameter(":users_id"))
            )
            values = {
                "groups_id": group_id,
                "users_id": user_id,
                "deleted_at": datetime.utcnow(),
            }

            try:
                row_id_groups_users: int = await mysql_driver.execute(
                    query.get_sql(), values
                )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return row_id_groups_users

    @staticmethod
    async def get_users_and_roles(
        mysql_driver: Database, group_id: int
    ) -> list[dict[str, BaseUser | BaseRole]]:
        groups_users: Table = Table("groups_users")
        users: Table = Table("users")
        roles: Table = Table("roles")
        query = (
            MySQLQuery.select(
                users.id.as_("user_id"),
                users.email,
                users.username,
                users.first_name,
                users.last_name,
                roles.id,
                roles.role,
            )
            .from_(groups_users)
            .join(users)
            .on(groups_users.users_id == users.id)
            .join(roles)
            .on(groups_users.roles_id == roles.id)
            .where(groups_users.groups_id == Parameter(":groups_id"))
        )
        values = {"groups_id": group_id}

        try:
            users_and_roles: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        return [
            {"user": BaseUser(**user_and_role), "role": BaseRole(**user_and_role)}
            for user_and_role in users_and_roles
        ]
