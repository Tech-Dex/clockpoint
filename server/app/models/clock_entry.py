from datetime import datetime

from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel
from app.models.enums.clock_entry_type import ClockEntryType


class BaseClockEntry(ConfigModel):
    datetime: datetime
    type: ClockEntryType


class DBClockEntry(DBCoreModel, BaseClockEntry):
    class Meta:
        table_name: str = "clock_entries"
