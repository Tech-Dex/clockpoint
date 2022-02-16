from typing import Mapping, Optional

from databases import Database
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    async def get_default_owner_permissions(mysql_driver: Database) -> list:
        permissions: Table = Table("permissions")
        query = MySQLQuery.from_(permissions).select(
            permissions.id, permissions.permission
        )

        permissions: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())
        if permissions:
            return [permission["id"] for permission in permissions]

    @staticmethod
    async def create_roles_permissions(
        mysql_driver: Database, group_id: int, custom_roles_permissions: list[dict]
    ):
        roles: Table = Table("roles")
        permissions: Table = Table("permissions")
        query = (
            MySQLQuery.from_(roles)
            .select(roles.id, roles.role)
            .where(roles.groups_id == Parameter(":group_id"))
        )
        values = {"group_id": group_id}

        roles: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)
        if roles and set(
            [
                custom_role_permission["role"]
                for custom_role_permission in custom_roles_permissions
            ]
        ).issubset(set([role["role"] for role in roles])):
            query = MySQLQuery.from_(permissions).select(
                permissions.id, permissions.permission
            )

            permissions: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())

            if set(
                [
                    custom_role_permission["permission"]
                    for custom_role_permission in custom_roles_permissions
                ]
            ).issubset(set([permission["permission"] for permission in permissions])):
                final_custom_permissions: list = []

                owner_permissions: list = await DBRole.get_default_owner_permissions(
                    mysql_driver
                )
                for role in roles:
                    if role["role"] == Roles.OWNER.value:
                        for owner_permission in owner_permissions:
                            final_custom_permissions.append(
                                {
                                    "role_id": role["id"],
                                    "permission_id": owner_permission,
                                }
                            )
                    break

                for custom_role_permission in custom_roles_permissions:
                    for role in roles:
                        if role["role"] == custom_role_permission["role"]:
                            for permission in permissions:
                                if (
                                    permission["permission"]
                                    == custom_role_permission["permission"]
                                ):
                                    final_custom_permissions.append(
                                        {
                                            "role_id": role["id"],
                                            "permission_id": permission["id"],
                                        }
                                    )
                                    break
                            break

                if final_custom_permissions:
                    return final_custom_permissions

            raise StarletteHTTPException(
                status_code=422,
                detail="Permissions not found",
            )

        raise StarletteHTTPException(
            status_code=422,
            detail="Roles not found",
        )


class BaseRoleWrapper(BaseRole):
    pass


class BaseRoleResponse(ConfigModel):
    role: BaseRoleWrapper


class BaseRoleRequest(ConfigModel):
    role: str
