from __future__ import annotations

from datetime import datetime

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from aredis_om import HashModel, Field
from aredis_om import get_redis_connection
from app.core.config import settings


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

    class Meta:
        global_key_prefix = "clockpoint"
        database = get_redis_connection(url=settings.REDIS_DATA_URL, decode_responses=True)


class InviteGroupToken(BaseToken):
    user_email: str
    group_id: int
