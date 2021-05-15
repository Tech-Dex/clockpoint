from datetime import datetime
from typing import Optional

from pydantic.networks import EmailStr

from app.models.dbmodel import DBModel
from app.models.enums.token_subject import TokenSubject
from app.models.rwmodel import RWModel


class TokenPayload(RWModel):
    email: EmailStr
    username: str
    group_id: Optional[str]
    user_email_invited: Optional[str]


class TokenDB(DBModel, TokenPayload):
    token: str
    subject: TokenSubject
    expire_datetime: datetime
    used_at: Optional[datetime]


class TokenUpdate(RWModel):
    token: str
    deleted: Optional[bool] = None
    used_at: Optional[datetime] = None
