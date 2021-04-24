from datetime import datetime

from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel


class TokenPayload(RWModel):
    email: str
    username: str


class TokenDB(DBModel, TokenPayload):
    token: str
    subject: str
    expire_datetime: datetime
