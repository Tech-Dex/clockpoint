from datetime import datetime
from typing import Mapping, Optional

from databases import Database
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from pypika.terms import AggregateFunction
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.role import DBRole


class BaseGroup(ConfigModel):
    name: str
    description: Optional[str]


class DBGroup(DBCoreModel, BaseGroup):
    @classmethod
    async def get_by_id(cls, mysql_driver: Database, group_id: int) -> "DBGroup":
        """
        usage: BaseGroup(**(await DBGroup.get_by_id(mysql_driver, 1)).dict())
        """
        groups: Table = Table("groups")
        query = (
            MySQLQuery.from_(groups)
            .select("*")
            .where(groups.id == Parameter(":group_id"))
        )
        values = {"group_id": group_id}

        group: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if group:
            return cls(**group)

        raise StarletteHTTPException(status_code=404, detail="Group not found")

    @classmethod
    async def get_by_name(cls, mysql_driver: Database, group_name: str) -> "DBGroup":
        """
        usage: BaseGroup(**(await DBGroup.get_by_id(mysql_driver, "test")).dict())
        """
        groups: Table = Table("groups")
        query = (
            MySQLQuery.from_(groups)
            .select("*")
            .where(groups.name == Parameter(":group_name"))
        )
        values = {"group_name": group_name}

        group: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if group:
            return cls(**group)

        raise StarletteHTTPException(status_code=404, detail="Group not found")

    async def save(self, mysql_driver: Database, user_id: int) -> tuple[int, int]:
        """
        usage: await DBGroup(name="test", description="test").save(mysql_driver, 1)
        """
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
                self.id = row_id_group
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
        self, mysql_driver: Database, user_id: int, role_id: int
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
            "groups_id": self.id,
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

    async def add_user(self, mysql_driver: Database, user_id: int) -> int:
        """
        usage: await db_group.add_user(mysql_driver, group_id, 1)
        """
        async with mysql_driver.transaction():
            role_user: DBRole = await DBRole.get_role_user(mysql_driver)
            row_id_groups_users: int = await self.__create_groups_users(
                mysql_driver,
                user_id,
                role_user.id,
            )

            return row_id_groups_users

    async def remove_user(self, mysql_driver: Database, user_id: int) -> int:
        """
        usage: await db_group.remove_user(mysql_driver, 1)
        """
        async with mysql_driver.transaction():
            groups_users: Table = Table("groups_users")
            query = (
                MySQLQuery.update(groups_users)
                .set(groups_users.deleted_at, Parameter(":deleted_at"))
                .where(groups_users.groups_id == Parameter(":groups_id"))
                .where(groups_users.users_id == Parameter(":users_id"))
            )
            values = {
                "groups_id": self.id,
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

    async def get_users_and_roles(self, mysql_driver: Database) -> list[Mapping]:
        """
        usage: await DBGroup.get_users_and_roles(mysql_driver)
        format response:
        {"payload": [({"user": BaseUser(**json.loads(i)['user']), "role": BaseRole(**json.loads(i)['role'])})
         for rep in response for i in rep]}
        """
        groups_users: Table = Table("groups_users")
        users: Table = Table("users")
        roles: Table = Table("roles")
        query = (
            MySQLQuery.select(
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
                )
            )
            .from_(groups_users)
            .join(users)
            .on(groups_users.users_id == users.id)
            .join(roles)
            .on(groups_users.roles_id == roles.id)
            .where(groups_users.groups_id == Parameter(":groups_id"))
        )
        values = {"groups_id": self.id}

        try:
            users_and_roles: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )
        except MySQLError as mySQLError:
            raise StarletteHTTPException(
                status_code=500,
                detail=f"MySQL error: {mySQLError.args[1]}",
            )

        return users_and_roles
