from datetime import datetime
from typing import Mapping, Optional

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
            .where(groups.deleted_at.isnull())
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
            .where(groups.deleted_at.isnull())
        )
        values = {"group_name": group_name}

        group: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if group:
            return cls(**group)

        raise StarletteHTTPException(status_code=404, detail="Group not found")

    """
            {"roles_id": 1, "permissions_id": 1},
            {"roles_id": 1, "permissions_id": 2},
            {"roles_id": 1, "permissions_id": 3},
            {"roles_id": 1, "permissions_id": 4},
            {"roles_id": 1, "permissions_id": 5},
            {"roles_id": 1, "permissions_id": 6},
            {"roles_id": 1, "permissions_id": 7},
            {"roles_id": 1, "permissions_id": 8},
            {"roles_id": 1, "permissions_id": 9},
            {"roles_id": 2, "permissions_id": 1},
            {"roles_id": 2, "permissions_id": 2},
            {"roles_id": 2, "permissions_id": 3},
            {"roles_id": 2, "permissions_id": 4},
            {"roles_id": 2, "permissions_id": 5},
            {"roles_id": 3, "permissions_id": 1},
    """

    async def save(
        self, mysql_driver: Database, user_id: int, roles: list
    ) -> "DBGroup":
        """
        usage: db_group, db_groups_and_roles_id = await DBGroup(name="test", description="test").save(mysql_driver, 1)
        format response: {"payload":
         {"group": BaseGroup(**db_group.dict()), "groups_and_roles_id": db_groups_and_roles_id}
        }
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
            if await self.__create_roles(mysql_driver, roles):
                if await self.__create_groups_users(
                    mysql_driver,
                    user_id,
                    (await DBRole.get_role_owner(mysql_driver)).id,
                ):
                    return self

    async def __create_groups_users(
        self, mysql_driver: Database, user_id: int, role_id: int
    ) -> bool:
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

        try:
            await mysql_driver.execute(query.get_sql(), values)
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

    async def __create_roles(self, mysql_driver: Database, group_roles: list) -> bool:
        roles: str = "roles"
        columns: list = ["role", "groups_id", "created_at", "updated_at"]
        now = datetime.now()
        values: list = [
            f"{role['role']!r}, {self.id}, "
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

    async def create_roles_permissions_for_group(
        self, mysql_driver: Database, permissions: list[dict]
    ) -> bool:
        async with mysql_driver.transaction():
            roles_permissions: str = "roles_permissions"
            columns = [
                "roles_id",
                "permissions_id",
                "groups_id",
                "created_at",
                "updated_at",
            ]
            now = datetime.now()
            values = [
                f"{permission['role_id']!r}, {permission['permission_id']}, {self.id},"
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
                        detail="Permission already exists in group",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return True

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

    async def make_user_admin(self, mysql_driver: Database, user_id: int) -> int:
        """
        usage: await db_group.make_user_admin(mysql_driver, 1)
        """
        async with mysql_driver.transaction():
            role_admin: DBRole = await DBRole.get_role_admin(mysql_driver)
            row_id_groups_users: int = await self.__create_groups_users(
                mysql_driver,
                user_id,
                role_admin.id,
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
        format response:{"payload":
         [({"user": BaseUser(**json.loads(i)['user']), "role": BaseRole(**json.loads(i)['role'])})
         for rep in response for i in rep]
        }
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
            .where(groups_users.deleted_at.isnull())
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

    async def update(self, mysql_driver: Database, **kwargs) -> "DBGroup":
        """
        usage: await db_group.update(mysql_driver, name="new_name", description="new_description")
        """
        async with mysql_driver.transaction():
            self.name = kwargs.get("name", self.name)
            self.description = kwargs.get("description", self.description)

            groups: Table = Table("groups")
            query = (
                MySQLQuery.update(groups)
                .set(groups.name, Parameter(":name"))
                .set(groups.description, Parameter(":description"))
                .where(groups.id == Parameter(":id"))
                .where(groups.deleted_at.isnull())
            )
            values = {"id": self.id, "name": self.name, "description": self.description}

            try:
                await mysql_driver.execute(query.get_sql(), values)
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return self

    async def delete(self, mysql_driver: Database) -> "DBGroup":
        """
        usage: await db_group.delete(mysql_driver)
        """
        async with mysql_driver.transaction():
            groups: Table = Table("groups")
            query = (
                MySQLQuery.update(groups)
                .from_(groups)
                .set(groups.deleted_at, Parameter(":deleted_at"))
                .where(groups.id == Parameter(":id"))
            )
            values = {"id": self.id, "deleted_at": datetime.now()}

            try:
                await mysql_driver.execute(query.get_sql(), values)
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

            return self

    async def get_users_by_role(
        self, mysql_driver: Database, role: str
    ) -> list[Mapping]:
        """
        usage: await db_group.get_users_by_role(mysql_driver, role=Roles.ADMIN)
        format response: {"payload":
        [BaseUser(**user) for user in await db_group.get_users_by_role(mysql_driver, Roles.ADMIN)]
        }
        """
        async with mysql_driver.transaction():
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
            values = {"groups_id": self.id, "role": role}

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


class BaseGroupResponse(BaseGroup):
    pass


class BaseGroupRequest(ConfigModel):
    name: str
