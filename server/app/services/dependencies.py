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
from app.models.role_permission import DBRolePermission
from app.models.token import BaseToken
from app.models.user import BaseUser, UserToken, DBUser
from app.schemas.v1.request import GroupInviteRequest


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
        db_user: DBUser = await DBUser.get_by(mysql_driver, "id", token_payload.users_id)

        if db_user is None:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserToken(**db_user.dict(), token=token)
    else:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )


async def fetch_user_invite_permission_from_token(
    group_invite: GroupInviteRequest,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> tuple[int, UserToken, DBGroup]:
    db_group: DBGroup = await DBGroup.get_by(mysql_driver, "name", group_invite.name)

    db_group_user: DBGroupUser = (
        await DBGroupUser.get_group_user_by_group_id_and_user_id(
            mysql_driver, db_group.id, user_token.id
        )
    )
    if not db_group_user:
        raise StarletteHTTPException(
            status_code=401, detail="You are not part of the group"
        )

    db_role_permissions = await DBRolePermission.get_role_permissions(
        mysql_driver, db_group_user.roles_id
    )

    if "invite_user" not in [
        permission["permission"]["permission"]
        for permission in db_role_permissions["permissions"]
    ]:
        raise StarletteHTTPException(
            status_code=401, detail="You are not allowed to invite users"
        )

    return user_token.id, user_token, db_group
