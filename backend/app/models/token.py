from datetime import datetime

from pydantic.networks import EmailStr

from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel


class TokenPayload(RWModel):
    email: EmailStr
    username: str


class TokenDB(DBModel, TokenPayload):
    token: str
    subject: str
    expire_datetime: datetime
