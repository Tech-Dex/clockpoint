from __future__ import annotations

from pydantic.networks import EmailStr

from app.core.security import generate_salt, hash_password, verify_password
from app.exceptions import auth as auth_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseUser(ConfigModel):
    email: EmailStr
    first_name: str
    second_name: str | None = None
    last_name: str
    username: str
    is_active: bool = True


class DBUser(DBCoreModel, BaseUser):
    salt: str = ""
    hashed_password: str = ""

    class Meta:
        table_name: str = "users"

    def verify_password(self, password: str):
        if not verify_password(self.salt, password, self.hashed_password):
            raise auth_exceptions.PasswordsNotMatchException()

    def change_password(self, password: str) -> None:
        self.salt = generate_salt()
        self.hashed_password = hash_password(self.salt, password)


class UserToken(BaseUser):
    id: int
    token: str | None = None
