from datetime import datetime
from typing import Optional

from databases import Database
from pymysql import Error as MySQLError
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseGroup(ConfigModel):
    name: str
    description: Optional[str]


class DBGroup(DBCoreModel, BaseGroup):
    class Meta:
        table_name: str = "groups"

    async def soft_remove_user(self, mysql_driver: Database, user_id: int) -> int:
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


class BaseGroupWrapper(BaseGroup):
    pass


class BaseGroupResponse(ConfigModel):
    group: BaseGroup


class BaseGroupRequest(ConfigModel):
    name: str
