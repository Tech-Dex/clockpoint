from __future__ import annotations

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.group import BaseGroup
from app.models.permission import BasePermissionResponse
from app.models.role import BaseRole, BaseRoleResponse
from app.models.user import BaseUserTokenWrapper


class GenericResponse(ConfigModel):
    message: str


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


class GroupInviteResponse(BaseGroup):
    token: str


class InvitesGroupsResponse(ConfigModel):
    invites: list[GroupInviteResponse]


class BypassedInvitesGroupsResponse(ConfigModel):
    bypassed_invites: list[EmailStr]


class BaseRoleResponse(BaseRole):
    pass


class GroupRolesResponse(ConfigModel):
    roles: list[BaseRoleResponse]
