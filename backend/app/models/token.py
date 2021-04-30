from datetime import datetime

from pydantic.networks import EmailStr

from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel
from app.models.enums.token_subject import TokenSubject


class TokenPayload(RWModel):
    email: EmailStr
    username: str


class TokenDB(DBModel, TokenPayload):
    token: str
    subject: TokenSubject
    expire_datetime: datetime
