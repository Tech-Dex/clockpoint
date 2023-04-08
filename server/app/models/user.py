from __future__ import annotations

from datetime import datetime, timedelta

from databases import Database
from phonenumbers import PhoneNumberFormat, format_number, parse as parse_phone_number
from phonenumbers.phonenumberutil import NumberParseException
from pydantic.networks import EmailStr
from pymysql import Error as MySQLError
from pypika import MySQLQuery, Table

from app.core.security import (
    generate_salt,
    hash_password,
    validate_password,
    verify_password,
)
from app.exceptions import (
    auth as auth_exceptions,
    base as base_exceptions,
    user as user_exceptions,
)
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseUser(ConfigModel):
    email: EmailStr
    first_name: str
    second_name: str | None = None
    last_name: str
    username: str
    is_active: bool = False
    phone_number: str | None = None


class DBUser(DBCoreModel, BaseUser):
    salt: str = ""
    hashed_password: str = ""

    class Meta:
        table_name: str = "users"
        inactive_user_lifetime: int = 8  # days

    def verify_password(
        self, password: str, exc: base_exceptions.CustomBaseException | None = None
    ) -> None:
        if not verify_password(self.salt, password, self.hashed_password):
            raise exc or auth_exceptions.PasswordEmailNotMatchException()

    def change_password(self, password: str) -> None:
        if warnings := validate_password(password):
            raise auth_exceptions.UnsecurePasswordException(warnings=warnings)

        self.salt = generate_salt()
        self.hashed_password = hash_password(self.salt, password)

    def parse_phone_number(self, phone_number_country_name: str | None):
        if self.phone_number and phone_number_country_name:
            try:
                parsed_phone_number = parse_phone_number(
                    self.phone_number, phone_number_country_name
                )
                self.phone_number = format_number(
                    parsed_phone_number, PhoneNumberFormat.E164
                )
            except NumberParseException:
                raise user_exceptions.PhoneNumberFormatException()

    @classmethod
    async def remove_inactive_users(cls, mysql_driver: Database) -> None:
        now: datetime = datetime.utcnow()
        users: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(users)
            .delete()
            .where(users.is_active == False)
            .where(
                users.created_at < now - timedelta(days=cls.Meta.inactive_user_lifetime)
            )
        )

        try:
            await mysql_driver.execute(query.get_sql())
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])


class UserId(BaseUser):
    id: int


class UserToken(UserId):
    token: str | None = None


class DBUserToken(DBUser):
    token: str | None = None
