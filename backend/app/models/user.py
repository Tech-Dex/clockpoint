from typing import Optional

from pydantic import EmailStr

from app.core import security
from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel


class UserBase(RWModel):
    email: EmailStr
    first_name: str
    second_name: Optional[str]
    last_name: str
    username: str
    is_active: bool = False


class UserDB(DBModel, UserBase):
    salt: str = ""
    hashed_password: str = ""

    def check_password(self, password: str) -> bool:
        return security.verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str):
        self.salt = security.generate_salt()
        self.hashed_password = security.get_password_hash(self.salt + password)

    def activate(self):
        self.is_active = True

    def delete(self):
        self.deleted = True


class UserTokenWrapper(UserBase):
    token: Optional[str]


class UserResponse(RWModel):
    user: UserTokenWrapper


class UserLogin(RWModel):
    email: EmailStr
    password: str


class UserCreate(UserLogin):
    first_name: str
    second_name: Optional[str]
    last_name: str
    username: str


class UserUpdate(RWModel):
    deleted: Optional[bool] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    second_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserRecover(RWModel):
    password: str = None
