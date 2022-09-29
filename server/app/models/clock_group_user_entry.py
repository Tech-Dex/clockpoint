from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseClockGroupUserEntry(ConfigModel):
    groups_users_id: int
    clock_entries_id: int


class DBClockGroupUserEntry(DBCoreModel, BaseClockGroupUserEntry):
    class Meta:
        table_name: str = "clock_groups_users_entries"
