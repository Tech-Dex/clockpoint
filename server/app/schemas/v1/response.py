from __future__ import annotations

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.group import BaseGroup
from app.models.role import BaseRole, BaseRoleResponse
from app.models.user import BaseUser
from app.schemas.v1.wrapper import PayloadGroupUserRoleWrapper, PayloadRolePermissionsWrapper, \
    PayloadRolesPermissionWrapper


class GenericResponse(ConfigModel):
    message: str


class UserTokenResponse(BaseUser):
    token: str | None = None


class BaseUserResponse(ConfigModel):
    user: UserTokenResponse


class BaseGroupResponse(ConfigModel):
    group: BaseGroup


class PayloadGroupUserRoleResponse(ConfigModel):
    payload: list[PayloadGroupUserRoleWrapper]


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
