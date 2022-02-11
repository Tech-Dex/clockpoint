from typing import Mapping, Optional

from databases import Database
from pydantic.networks import EmailStr
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.security import generate_salt, hash_password, verify_password
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseUser(ConfigModel):
    email: EmailStr
    first_name: str
    second_name: Optional[str] = None
    last_name: str
    username: str
    is_active: bool = True


class DBUser(DBCoreModel, BaseUser):
    salt: str = ""
    hashed_password: str = ""

    def verify_password(self, password: str) -> bool:
        return verify_password(self.salt, password, self.hashed_password)

    def change_password(self, password: str) -> None:
        self.salt = generate_salt()
        self.hashed_password = hash_password(self.salt, password)

    @classmethod
    async def get_by_id(cls, mysql_driver: Database, user_id: int) -> "DBUser":
        users: Table = Table("users")
        query = MySQLQuery.from_(users).select("*").where(users.id == Parameter(":id")).where(users.is_deleted.isnull())
        values = {"id": user_id}

        user: Mapping = await mysql_driver.fetch_one(
            query=query.get_sql(), values=values
        )
        if user:
            return cls(**user)

        raise StarletteHTTPException(status_code=404, detail="User not found")

    @classmethod
    async def get_by_email(cls, mysql_driver, email) -> "DBUser":
        users: Table = Table("users")
        query = (
            MySQLQuery.from_(users)
            .select("*")
            .where(users.email == Parameter(":email")).where(users.is_deleted.isnull())
        )
        values = {"email": email}

        user: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)

        if user:
            return cls(**user)

        raise StarletteHTTPException(status_code=404, detail="User not found")

    async def save(self, mysql_driver: Database) -> "DBUser":
        async with mysql_driver.transaction():
            users: Table = Table("users")
            query = (
                MySQLQuery.into(users)
                .columns(
                    users.email,
                    users.first_name,
                    users.second_name,
                    users.last_name,
                    users.username,
                    users.is_active,
                    users.salt,
                    users.hashed_password,
                    users.created_at,
                    users.updated_at,
                    users.deleted_at,
                )
                .insert(
                    Parameter(":email"),
                    Parameter(":first_name"),
                    Parameter(":second_name"),
                    Parameter(":last_name"),
                    Parameter(":username"),
                    Parameter(":is_active"),
                    Parameter(":salt"),
                    Parameter(":hashed_password"),
                    Parameter(":created_at"),
                    Parameter(":updated_at"),
                    Parameter(":deleted_at"),
                )
            )

            values = {
                "email": self.email,
                "first_name": self.first_name,
                "second_name": self.second_name,
                "last_name": self.last_name,
                "username": self.username,
                "is_active": self.is_active,
                "salt": self.salt,
                "hashed_password": self.hashed_password,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "deleted_at": self.deleted_at,
            }

            try:
                row_id: int = await mysql_driver.execute(query.get_sql(), values)
                self.id = row_id
                return self
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    raise StarletteHTTPException(
                        status_code=409,
                        detail="User already exists",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )


class BaseUserTokenWrapper(BaseUser):
    token: Optional[str] = None


class BaseUserResponse(ConfigModel):
    user: BaseUserTokenWrapper


class UserLogin(ConfigModel):
    email: EmailStr
    password: str


class UserRegister(UserLogin):
    first_name: str
    second_name: Optional[str] = None
    last_name: str
    username: str
