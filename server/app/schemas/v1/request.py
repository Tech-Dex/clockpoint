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


class UserUpdateRequest(ConfigModel):
    first_name: str | None = None
    second_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class UserResetPasswordRequest(ConfigModel):
    password: str
    confirm_password: str


class UserChangePasswordRequest(ConfigModel):
    password: str
    new_password: str
    confirm_new_password: str


class BaseGroupCustomRolePermissionCreateRequest(ConfigModel):
    role: str
    permissions: list[str]


class BaseGroupCreateRequest(ConfigModel):
    name: str
    description: str | None = None
    custom_roles: list[BaseGroupCustomRolePermissionCreateRequest] | None = []


class GroupInviteRequest(ConfigModel):
    group_id: int
    emails: list[EmailStr]


class GroupAssignRoleRequest(ConfigModel):
    group_id: int
    username: str
    role_name: str
