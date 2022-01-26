from datetime import datetime

from databases import Database
from pydantic.networks import EmailStr
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseTokenPayload(ConfigModel):
    email: EmailStr
    username: str
    user_id: int
    subject: str = ""


class DBTokenPayload(DBCoreModel, BaseTokenPayload):
    token: str
    expire: datetime

    async def save(self, mysql_driver: Database) -> int:
        async with mysql_driver.transaction():
            tokens = Table("tokens")
            query = (
                MySQLQuery.into(tokens)
                .columns(
                    tokens.user_id,
                    tokens.subject,
                    tokens.expire,
                    tokens.token,
                    tokens.created_at,
                    tokens.updated_at,
                    tokens.deleted_at,
                )
                .insert(
                    Parameter(":user_id"),
                    Parameter(":subject"),
                    Parameter(":expire"),
                    Parameter(":token"),
                    Parameter(":created_at"),
                    Parameter(":updated_at"),
                    Parameter(":deleted_at"),
                )
            )
            values = {
                "user_id": self.user_id,
                "subject": self.subject,
                "expire": self.expire,
                "token": self.token,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "deleted_at": self.deleted_at,
            }

            try:
                row_id: int = await mysql_driver.execute(query.get_sql(), values)

                return row_id
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=400,
                        detail="Token already exists",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=400,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )
