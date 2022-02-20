from app.models.config_model import ConfigModel


class BasePermission(ConfigModel):
    permission: str


class BaseRoleWrapper(BasePermission):
    pass


class BasePermissionResponse(ConfigModel):
    permission: BaseRoleWrapper
