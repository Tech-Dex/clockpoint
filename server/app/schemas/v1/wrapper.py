from __future__ import annotations

from app.models.config_model import ConfigModel
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.permission import DBPermission
from app.models.role import DBRole
from app.models.user import UserToken


class UserInGroupWrapper(ConfigModel):
    user_token: UserToken
    group: DBGroup
    group_user: DBGroupUser


class UserInGroupWithRoleAssignWrapper(UserInGroupWrapper):
    role_assign: DBRole


class RolePermissionsWrapper(ConfigModel):
    role: DBRole
    permissions: list[DBPermission]


class RolesPermissionsWrapper(ConfigModel):
    roles_permissions: list[RolePermissionsWrapper]
