from __future__ import annotations

from databases import Database
from fastapi import Depends, Header

from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import decode_token
from app.exceptions import (
    group as group_exceptions,
    group_user as group_user_exceptions,
    permission as permission_exceptions,
    role as role_exceptions,
    token as token_exceptions,
    user as user_exceptions,
)
from app.models.enums.token_subject import TokenSubject
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import BaseToken
from app.models.user import DBUser, UserToken, DBUserToken
from app.schemas.v1.request import GroupAssignRoleRequest, GroupInviteRequest
from app.schemas.v1.wrapper import UserInGroupWithRoleAssignWrapper, UserInGroupWrapper


async def get_authorization_header(
    authorization: str = Header(None),
    required: bool = True,
) -> str | None:
    if authorization:
        prefix, token = authorization.split(" ")
        if token is None and required:
            raise token_exceptions.MissingTokenException()
        if prefix.lower() != "bearer":
            raise token_exceptions.BearTokenException()
        return token
    elif required:
        raise token_exceptions.MissingTokenException()
    return None


async def fetch_db_user_from_token(
    mysql_driver: Database = Depends(get_mysql_driver),
    token: str = Depends(get_authorization_header),
) -> DBUserToken:
    payload: dict = decode_token(token)
    token_payload: BaseToken = BaseToken(**payload)

    if token_payload.subject == TokenSubject.ACCESS:
        user: DBUser = await DBUser.get_by(
            mysql_driver,
            "id",
            token_payload.users_id,
            exc=user_exceptions.UserNotFoundException(),
        )
        return DBUserToken(**user.dict(), token=token)
    else:
        raise token_exceptions.AccessTokenException()


async def fetch_user_from_token(
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> UserToken:
    return UserToken(**db_user_token.dict())

async def fetch_user_in_group_from_token_qp_id(
    group_id: int,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    return await fetch_user_in_group_from_token(
        group_id=group_id,
        user_token=user_token,
        mysql_driver=mysql_driver,
    )


async def fetch_user_in_group_from_token_br_invite(
    group_invite: GroupInviteRequest,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    if not group_invite.emails:
        raise group_exceptions.GroupEmailInvitationException()
    return await fetch_user_in_group_from_token(
        group_invite=group_invite,
        user_token=user_token,
        mysql_driver=mysql_driver,
    )


async def fetch_user_in_group_from_token_br_assign_role(
    group_assign_role: GroupAssignRoleRequest,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    return await fetch_user_in_group_from_token(
        group_id=group_assign_role.group_id,
        user_token=user_token,
        mysql_driver=mysql_driver,
    )


async def fetch_user_in_group_from_token(
    user_token: UserToken,
    mysql_driver: Database,
    group_invite: GroupInviteRequest | None = None,
    group_id: int | None = None,
) -> UserInGroupWrapper:
    group_id: int = group_id or group_invite.group_id
    if not group_id:
        raise group_exceptions.GroupIDMissingException()

    group: DBGroup = await DBGroup.get_by(
        mysql_driver, "id", group_id, exc=group_exceptions.GroupNotFoundException()
    )

    group_user: DBGroupUser = await DBGroupUser.is_user_in_group(
        mysql_driver,
        user_token.id,
        group.id,
        exc=group_user_exceptions.UserNotInGroupException(),
    )

    return UserInGroupWrapper(user_token=user_token, group=group, group_user=group_user)


async def is_permission_granted(
    mysql_driver: Database, user_in_group: UserInGroupWrapper, permission: str
) -> dict[str, list[dict[str, any]] | any]:
    role_permissions = await DBRolePermission.get_role_permissions(
        mysql_driver, user_in_group.group_user.roles_id
    )

    if permission not in [
        permission["permission"]["permission"]
        for permission in role_permissions["permissions"]
    ]:
        raise permission_exceptions.NotAllowedToInviteUsersInGroupException()

    return role_permissions


async def fetch_user_invite_permission_from_token_br_invite(
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_in_group_from_token_br_invite
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    await is_permission_granted(mysql_driver, user_in_group, "invite_user")
    return user_in_group


async def fetch_user_invite_permission_from_token_qp_id(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_id),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    await is_permission_granted(mysql_driver, user_in_group, "invite_user")
    return user_in_group


async def fetch_user_assign_role_permission_from_token(
    group_assign_role: GroupAssignRoleRequest,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_in_group_from_token_br_assign_role
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWithRoleAssignWrapper:
    user_assign = await DBUser.get_by(
        mysql_driver,
        "username",
        group_assign_role.username,
        exc=user_exceptions.UserNotFoundException(),
    )

    user_assign_in_group: DBGroupUser = await DBGroupUser.is_user_in_group(
        mysql_driver,
        user_assign.id,
        user_in_group.group.id,
        exc=group_user_exceptions.UserNotInGroupException(),
    )

    if group_assign_role.username == user_in_group.user_token.username:
        raise group_user_exceptions.SelfAssignRoleException()

    group_roles: list[DBRole] = await DBRole.get_all_in(
        mysql_driver,
        "groups_id",
        [user_in_group.group.id],
        exc=role_exceptions.RoleNotFoundException(),
    )

    group_roles_permissions = await DBRolePermission.get_roles_permissions(
        mysql_driver, [group_role.id for group_role in group_roles]
    )

    role_assign: DBRole = await DBRole.get_role_type_by_group(
        mysql_driver,
        user_in_group.group.id,
        group_assign_role.role_name.lower(),
    )

    permissions_ids: list[int] = []
    permissions_current_ids: list[int] = []
    permissions_assign_ids: list[int] = []
    for group_role_permissions in group_roles_permissions.roles_permissions:
        if user_in_group.group_user.roles_id == group_role_permissions.role.id:
            if "assign_role" not in [
                permission.permission
                for permission in group_role_permissions.permissions
            ]:
                raise permission_exceptions.NotAllowedToAssignRoleInGroupException()
            permissions_ids = [
                permission.id for permission in group_role_permissions.permissions
            ]
        if user_assign_in_group.roles_id == group_role_permissions.role.id:
            permissions_current_ids = [
                permission.id for permission in group_role_permissions.permissions
            ]
        if role_assign.id == group_role_permissions.role.id:
            permissions_assign_ids = [
                permission.id for permission in group_role_permissions.permissions
            ]

    permissions_ids.sort()
    permissions_current_ids.sort()
    permissions_assign_ids.sort()

    if len(permissions_current_ids) >= len(permissions_ids):
        raise permission_exceptions.UserPermissionsAreHigherException()

    if permissions_assign_ids[-1] >= permissions_ids[-1]:
        raise permission_exceptions.UserPermissionsAreNotSufficientException()

    return UserInGroupWithRoleAssignWrapper(
        **user_in_group.dict(), role_assign=role_assign
    )
