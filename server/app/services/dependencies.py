from __future__ import annotations

from databases import Database
from fastapi import Depends, Header
from jwt import PyJWTError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import decode_token
from app.models.enums.token_subject import TokenSubject
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import BaseToken
from app.models.user import DBUser, UserToken
from app.schemas.v1.request import GroupAssignRoleRequest, GroupInviteRequest
from app.schemas.v1.wrapper import UserInGroupRoleAssignWrapper, UserInGroupWrapper


async def get_authorization_header(
    authorization: str = Header(None),
    required: bool = True,
) -> str | None:
    if authorization:
        prefix, token = authorization.split(" ")
        if token is None and required:
            # TODO: create custom exceptions
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Token is required"
            )
        if prefix.lower() != "bearer":
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Token type is not valid"
            )
        return token
    elif required:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Token is required"
        )
    return None


async def fetch_user_from_token(
    mysql_driver: Database = Depends(get_mysql_driver),
    token: str = Depends(get_authorization_header),
) -> UserToken:
    try:
        payload: dict = decode_token(token)
        token_payload: BaseToken = BaseToken(**payload)
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Token is invalid"
        )

    if token_payload.subject == TokenSubject.ACCESS:
        user: DBUser = await DBUser.get_by(mysql_driver, "id", token_payload.users_id)

        if user is None:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserToken(**user.dict(), token=token)
    else:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )


async def fetch_user_in_group_from_token_qp_name(
    name: str,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    return await fetch_user_in_group_from_token(
        name=name,
        user_token=user_token,
        mysql_driver=mysql_driver,
    )


async def fetch_user_in_group_from_token_br_invite(
    group_invite: GroupInviteRequest,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> UserInGroupWrapper:
    if not group_invite.emails:
        raise StarletteHTTPException(status_code=400, detail="No emails provided")
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
        name=group_assign_role.name,
        user_token=user_token,
        mysql_driver=mysql_driver,
    )


async def fetch_user_in_group_from_token(
    user_token: UserToken,
    mysql_driver: Database,
    group_invite: GroupInviteRequest | None = None,
    name: str | None = None,
) -> UserInGroupWrapper:
    if name:
        group: DBGroup = await DBGroup.get_by(mysql_driver, "name", name)
        if not group:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Group not found"
            )
    elif group_invite:
        group: DBGroup = await DBGroup.get_by(mysql_driver, "name", group_invite.name)
        if not group:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Group not found"
            )
    else:
        raise StarletteHTTPException(status_code=400, detail="Unknown error")

    group_user: DBGroupUser = await DBGroupUser.is_user_in_group(
        mysql_driver, user_token.id, group.id, bypass_exception=True
    )
    if not group_user:
        raise StarletteHTTPException(
            status_code=401, detail="You are not part of the group"
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
        raise StarletteHTTPException(
            status_code=401, detail="You are not allowed to invite users"
        )

    return role_permissions


async def fetch_user_invite_permission_from_token(
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_in_group_from_token_br_invite
    ),
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
) -> UserInGroupRoleAssignWrapper:
    role_permissions = await is_permission_granted(mysql_driver, user_in_group, "edit")
    permissions_ids: list[int] = [
        role_permission["permission"]["id"]
        for role_permission in role_permissions["permissions"]
    ]
    permissions_ids.sort()

    role_assign: DBRole = await DBRole.get_by(
        mysql_driver, "role", group_assign_role.role_name.lower()
    )

    if not role_assign:
        raise StarletteHTTPException(status_code=404, detail="No role found")

    permissions_assign = await DBRolePermission.get_role_permissions(
        mysql_driver, role_assign.id
    )

    permissions_assign_ids: list[int] = [
        permission["permission"]["id"]
        for permission in permissions_assign["permissions"]
    ]
    permissions_assign_ids.sort()

    if permissions_assign_ids[-1] > permissions_ids[-1]:
        raise StarletteHTTPException(
            status_code=403, detail="You can't assign a role that is higher than yours"
        )

    return UserInGroupRoleAssignWrapper(**user_in_group.dict(), role_assign=role_assign)
