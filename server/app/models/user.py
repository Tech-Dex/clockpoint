from __future__ import annotations

from pydantic.networks import EmailStr

from app.core.security import (
    generate_salt,
    hash_password,
    validate_password,
    verify_password,
)
from app.exceptions import auth as auth_exceptions, base as base_exceptions, user as user_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from phonenumbers import parse as parse_phone_number, PhoneNumberFormat, format_number
from phonenumbers.phonenumberutil import NumberParseException


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
        try:
            parsed_phone_number = parse_phone_number(self.phone_number, phone_number_country_name)
            self.phone_number = format_number(parsed_phone_number, PhoneNumberFormat.E164)
        except NumberParseException:
            raise user_exceptions.PhoneNumberFormatException()


class UserToken(BaseUser):
    id: int
    token: str | None = None


class DBUserToken(DBUser):
    token: str | None = None
