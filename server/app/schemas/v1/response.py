from __future__ import annotations

from app.models.config_model import ConfigModel
from app.models.group import BaseGroup
from app.models.permission import BasePermissionResponse
from app.models.role import BaseRoleResponse
from app.models.user import BaseUserTokenWrapper


class BaseUserResponse(ConfigModel):
    user: BaseUserTokenWrapper


class BaseGroupResponse(ConfigModel):
    group: BaseGroup


class PayloadGroupUserRoleWrapper(
    BaseUserResponse, BaseGroupResponse, BaseRoleResponse
):
    pass


class PayloadGroupUserRoleResponse(ConfigModel):
    payload: list[PayloadGroupUserRoleWrapper]


class PayloadRolePermissionsWrapper(BaseRoleResponse):
    permissions: list[BasePermissionResponse]


class PayloadRolesPermissionWrapper(BasePermissionResponse):
    roles: list[BaseRoleResponse]


class PayloadRolePermissionsResponse(ConfigModel):
    payload: list[PayloadRolePermissionsWrapper]


class PayloadRolesPermissionResponse(ConfigModel):
    payload: list[PayloadRolesPermissionWrapper]
