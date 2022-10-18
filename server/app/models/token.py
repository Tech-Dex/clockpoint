from __future__ import annotations

from datetime import datetime

from aredis_om import Field, HashModel, get_redis_connection

from app.core.config import settings
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.enums.clock_entry_type import ClockEntryType


class BaseToken(ConfigModel):
    users_id: int
    subject: str = ""


class DBToken(DBCoreModel, BaseToken):
    token: str
    expire: datetime

    class Meta:
        table_name: str = "tokens"


class RedisToken(HashModel, ConfigModel):
    users_id: int = Field(index=True)
    subject: str = Field(index=True)
    token: str = Field(index=True)
    groups_id: int | None = Field(index=True, default=0)
    clock_sessions_id: int | None = Field(index=True, default=0)
    invite_user_email: str | None = Field(index=True, default=None)
    type: str | None = Field(index=True, default=None)

    class Meta:
        global_key_prefix = "clockpoint"
        database = get_redis_connection(
            url=settings.REDIS_DATA_URL, decode_responses=True
        )


class InviteGroupToken(BaseToken):
    invite_user_email: str
    groups_id: int


class QRCodeInviteGroupToken(BaseToken):
    groups_id: int


class QRCodeClockEntryToken(BaseToken):
    groups_id: int
    clock_sessions_id: int
    type: ClockEntryType
