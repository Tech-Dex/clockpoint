from __future__ import annotations

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.group import BaseGroup
from app.models.permission import BasePermission, BasePermissionResponse
from app.models.role import BaseRole, BaseRoleResponse
from app.models.user import BaseUser


class GenericResponse(ConfigModel):
    message: str


class UserTokenResponse(BaseUser):
    token: str | None = None


class BaseUserResponse(ConfigModel):
    user: UserTokenResponse


class BaseGroupIdWrapper(BaseGroup):
    id: int


class BaseGroupResponse(ConfigModel):
    group: BaseGroupIdWrapper


class PayloadGroupUserRoleWrapper(
    BaseUserResponse, BaseGroupResponse, BaseRoleResponse
):
    pass


class PayloadRolePermissionsWrapper(BaseRoleResponse):
    permissions: list[BasePermissionResponse]


class PayloadRolesPermissionWrapper(BasePermissionResponse):
    roles: list[BaseRoleResponse]


class RolePermissionsResponse(ConfigModel):
    role: BaseRole
    permissions: list[BasePermission]


class RolesPermissionsResponse(ConfigModel):
    roles_permissions: list[RolePermissionsResponse]


class PayloadGroupUserRoleResponse(ConfigModel):
    payload: list[PayloadGroupUserRoleWrapper]


class PayloadUserRoleResponse(ConfigModel):
    user: BaseUser
    role: BaseRole


class PayloadGroupUsersRoleResponse(ConfigModel):
    group: BaseGroupIdWrapper
    users_role: list[PayloadUserRoleResponse]

    @classmethod
    def prepare_response(cls, group_users):
        return cls(
            group=group_users[0]["group"],
            users_role=[
                PayloadUserRoleResponse(
                    user=group_user["user"], role=group_user["role"]
                )
                for group_user in group_users
            ],
        )


class PayloadGroupsUsersRoleResponse(ConfigModel):
    payload: list[PayloadGroupUsersRoleResponse]


class PayloadRolePermissionsResponse(ConfigModel):
    payload: list[PayloadRolePermissionsWrapper]


class PayloadRolesPermissionResponse(ConfigModel):
    payload: list[PayloadRolesPermissionWrapper]


class GroupInviteResponse(BaseGroupIdWrapper):
    token: str


class InvitesGroupsResponse(ConfigModel):
    invites: list[GroupInviteResponse]


class BypassedInvitesGroupsResponse(ConfigModel):
    bypassed_invites: list[EmailStr]


class BaseRoleResponse(BaseRole):
    pass


class GroupRolesResponse(ConfigModel):
    roles: list[BaseRoleResponse]


class QRCodeInviteGroupResponse(ConfigModel):
    group: BaseGroupIdWrapper
    token: str

class BaseUserSearchResponse(BaseUser):
    pass

class BaseUsersSearchResponse(ConfigModel):
    users: list[BaseUserSearchResponse]

class RolePermissionsResponse(ConfigModel):
    role: str
    permissions: list[str]


class RolesPermissionsResponse(ConfigModel):
    roles_permissions: list[RolePermissionsResponse]
