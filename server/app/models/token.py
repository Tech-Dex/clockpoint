from __future__ import annotations

from datetime import datetime

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseTokenPayload(ConfigModel):
    user_id: int
    subject: str = ""


class DBTokenPayload(DBCoreModel, BaseTokenPayload):
    token: str
    expire: datetime

    class Meta:
        table_name: str = "tokens"


class InviteGroupTokenPayload(BaseTokenPayload):
    user_email: str
    group_id: int
