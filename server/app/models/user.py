from typing import Optional

from pydantic.networks import EmailStr

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

    class Meta:
        table_name: str = "users"

    def verify_password(self, password: str) -> bool:
        return verify_password(self.salt, password, self.hashed_password)

    def change_password(self, password: str) -> None:
        self.salt = generate_salt()
        self.hashed_password = hash_password(self.salt, password)


class BaseUserTokenWrapper(BaseUser):
    token: str = None


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
