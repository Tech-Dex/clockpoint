from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BasePermission(ConfigModel):
    permission: str


class DBPermission(DBCoreModel, BasePermission):
    class Meta:
        table_name: str = "permissions"


class BaseRoleWrapper(BasePermission):
    pass


class BasePermissionResponse(ConfigModel):
    permission: BaseRoleWrapper
