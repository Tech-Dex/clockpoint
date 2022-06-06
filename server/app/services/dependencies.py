from __future__ import annotations

from databases import Database
from fastapi import Depends
from jwt import PyJWTError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import decode_token, get_token_from_authorization_header
from app.models.enums.token_subject import TokenSubject
from app.models.group import DBGroup, GroupInviteRequest
from app.models.group_user import DBGroupUser
from app.models.role_permission import DBRolePermission
from app.models.token import BaseTokenPayload
from app.models.user import BaseUser, BaseUserTokenWrapper, DBUser


async def get_current_user(
    mysql_driver: Database = Depends(get_mysql_driver),
    token: str = Depends(get_token_from_authorization_header),
) -> tuple[int, BaseUserTokenWrapper]:
    try:
        payload: dict = decode_token(token)
        token_payload: BaseTokenPayload = BaseTokenPayload(**payload)
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Token is invalid"
        )

    if token_payload.subject == TokenSubject.ACCESS:
        db_user: DBUser = await DBUser.get_by(mysql_driver, "id", token_payload.user_id)
        user: BaseUser = BaseUser(**db_user.dict())

        if user is None:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="User not found"
            )
        return db_user.id, BaseUserTokenWrapper(**user.dict(), token=token)
    else:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )


async def get_current_user_and_group_allowed_to_invite(
    group_invite: GroupInviteRequest,
    id_user_token: tuple[int, BaseUserTokenWrapper] = Depends(get_current_user),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> tuple[int, BaseUserTokenWrapper, DBGroup]:
    user_id: int
    user_token: BaseUserTokenWrapper
    user_id, user_token = id_user_token
    db_group: DBGroup = await DBGroup.get_by(mysql_driver, "name", group_invite.name)

    db_group_user: DBGroupUser = (
        await DBGroupUser.get_group_user_by_group_id_and_user_id(
            mysql_driver, db_group.id, user_id
        )
    )
    if not db_group_user:
        raise StarletteHTTPException(
            status_code=401, detail="You are not part of the group"
        )

    db_role_permissions = await DBRolePermission.get_role_permissions(
        mysql_driver, db_group_user.role_id
    )

    if "invite_user" not in [
        permission["permission"]["permission"]
        for permission in db_role_permissions["permissions"]
    ]:
        raise StarletteHTTPException(
            status_code=401, detail="You are not allowed to invite users"
        )

    return user_id, user_token, db_group
