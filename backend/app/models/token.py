from datetime import datetime

from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel


class TokenPayload(RWModel):
    email: str


class TokenDB(DBModel, TokenPayload):
    token: str
    scope: str
    expire_datetime: datetime
