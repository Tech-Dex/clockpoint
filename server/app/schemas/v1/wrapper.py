from __future__ import annotations

from app.models.config_model import ConfigModel
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.permission import BasePermissionResponse
from app.models.role import DBRole, BaseRoleResponse
from app.models.user import UserToken
from app.schemas.v1.response import BaseUserResponse, BaseGroupResponse, BaseRoleResponse


class UserInGroupWrapper(ConfigModel):
    user_token: UserToken
    group: DBGroup
    group_user: DBGroupUser


class UserInGroupWithRoleAssignWrapper(UserInGroupWrapper):
    role_assign: DBRole


class PayloadGroupUserRoleWrapper(
    BaseUserResponse, BaseGroupResponse, BaseRoleResponse
):
    pass


class PayloadRolePermissionsWrapper(BaseRoleResponse):
    permissions: list[BasePermissionResponse]


class PayloadRolesPermissionWrapper(BasePermissionResponse):
    roles: list[BaseRoleResponse]
