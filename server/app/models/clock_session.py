from datetime import datetime

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseClockSession(ConfigModel):
    start_at: datetime
    stop_at: datetime


class DBClockSession(DBCoreModel, BaseClockSession):
    class Meta:
        table_name: str = "clock_sessions"
