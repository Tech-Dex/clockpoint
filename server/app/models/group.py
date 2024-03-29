from __future__ import annotations

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseGroup(ConfigModel):
    name: str
    description: str | None


class DBGroup(DBCoreModel, BaseGroup):
    class Meta:
        table_name: str = "groups"
