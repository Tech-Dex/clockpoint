from __future__ import annotations

from datetime import datetime

from aredis_om import Field, HashModel, get_redis_connection

from app.core.config import settings
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseToken(ConfigModel):
    user_id: int
    subject: str = ""


class DBToken(DBCoreModel, BaseToken):
    token: str
    expire: datetime

    class Meta:
        table_name: str = "tokens"


class RedisToken(HashModel, ConfigModel):
    user_id: int = Field(index=True)
    subject: str = Field(index=True)
    token: str = Field(index=True)
    group_id: int | None = Field(index=True, default=None)
    invite_user_email: str | None = Field(index=True, default=None)

    class Meta:
        global_key_prefix = "clockpoint"
        database = get_redis_connection(
            url=settings.REDIS_DATA_URL, decode_responses=True
        )


class InviteGroupToken(BaseToken):
    invite_user_email: str
    group_id: int
