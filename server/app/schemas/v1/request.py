from __future__ import annotations

from pydantic import EmailStr

from app.models.config_model import ConfigModel


class UserLoginRequest(ConfigModel):
    email: EmailStr
    password: str


class UserRegisterRequest(UserLoginRequest):
    first_name: str
    second_name: str | None = None
    last_name: str
    username: str


class BaseGroupCustomRolePermissionCreateRequest(ConfigModel):
    role: str
    permissions: list[str]


class BaseGroupCreateRequest(ConfigModel):
    name: str
    description: str | None = None
    custom_roles: list[BaseGroupCustomRolePermissionCreateRequest] | None = []


class GroupInviteRequest(ConfigModel):
    name: str
    emails: list[EmailStr]


class GroupAssignRoleRequest(ConfigModel):
    name: str
    username: str
    role_name: str
