from __future__ import annotations

from datetime import datetime

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


class InviteGroupToken(BaseToken):
    user_email: str
    group_id: int
