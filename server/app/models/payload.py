from app.models.config_model import ConfigModel
from app.models.group import BaseGroupResponse
from app.models.role import BaseRoleResponse
from app.models.user import BaseUserResponse


class PayloadGroupUserRoleWrapper(
    BaseUserResponse, BaseGroupResponse, BaseRoleResponse
):
    pass


class PayloadGroupUserRoleResponse(ConfigModel):
    payload: list[PayloadGroupUserRoleWrapper]
