from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseUserMeta(ConfigModel):
    user_id: int
    has_push_notifications: bool = True


class DBUserMeta(DBCoreModel, BaseUserMeta):
    class Meta:
        table_name: str = "users_meta"
