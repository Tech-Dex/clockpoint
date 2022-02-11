from typing import Mapping, Optional

from databases import Database
from pypika import MySQLQuery, Parameter, Table

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.enums.roles import Roles


class BaseRole(ConfigModel):
    role: str


class DBRole(DBCoreModel, BaseRole):
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


class BaseRoleResponse(BaseRole):
    pass


class BaseRoleRequest(ConfigModel):
    role: str
