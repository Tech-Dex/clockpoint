from typing import List, Tuple

from bson.objectid import ObjectId
from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi_mail import FastMail
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.core.jwt import (
    get_current_user,
    get_group_invitation,
    get_user_from_invitation,
)
from app.core.smtp.smtp import get_smtp
from app.models.enums.group_role import GroupRole
from app.models.enums.token_subject import TokenSubject
from app.models.generic_response import GenericResponse, GenericStatus
from app.models.group import (
    GroupCreate,
    GroupDB,
    GroupIdWrapper,
    GroupInvite,
    GroupInviteQRCodeResponse,
    GroupKick,
    GroupResponse,
    GroupsResponse,
)
from app.models.user import UserBase, UserDB, UserTokenWrapper
from app.repositories.group import (
    create_group,
    get_group_by_id,
    get_groups_by_user,
    leave_group,
)
from app.repositories.user import get_user_by_email
from app.utils.group import process_invitation, process_invitation_qrcode, process_join

router = APIRouter()


@router.get(
    "/",
    response_model=GroupsResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def groups(
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupsResponse:
    groups_db: List[Tuple[GroupDB, ObjectId]] = await get_groups_by_user(
        conn, UserBase(**user_current.dict())
    )

    groups_id_wrapper: List[GroupIdWrapper] = []
    for group_db, group_db_id in groups_db:
        groups_id_wrapper.append(GroupIdWrapper(**group_db.dict(), id=str(group_db_id)))

    return GroupsResponse(groups=groups_id_wrapper)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def group_by_id(
    group_id: str,
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_id)
    if group_db.user_in_group(UserBase(**user_current.dict())):
        return GroupResponse(group=GroupIdWrapper(**group_db.dict(), id=group_id))

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="User is not in the group"
    )


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def create(
    group_create: GroupCreate = Body(..., embed=True),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    async with await conn.start_session() as session, session.start_transaction():
        group_db: GroupDB
        group_db_id: ObjectId
        group_db, group_db_id = await create_group(
            conn, group_create, UserBase(**user_current.dict())
        )
        return GroupResponse(
            group=GroupIdWrapper(**group_db.dict(), id=str(group_db_id))
        )


@router.post(
    "/invite",
    response_model=GenericResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def invite(
    background_tasks: BackgroundTasks,
    group_invite: GroupInvite = Body(..., embed=True),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
    smtp_conn: FastMail = Depends(get_smtp),
) -> GenericResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_invite.group_id)
    user_host: UserBase = UserBase(**user_current.dict())

    if group_db.user_is_owner(user_host) or group_db.user_is_co_owner(user_host):
        if group_invite.role == GroupRole.OWNER:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Owner role is unique"
            )

        # This is a mock that will be replace if there is a user with the desired email
        # TODO: FRONTEND will take care to register/login a user before joining a group
        user_invited: UserDB = UserDB(
            email=group_invite.email, first_name="", last_name="", username=""
        )
        try:
            user_invited: UserDB = await get_user_by_email(conn, group_invite.email)
        except StarletteHTTPException as exc:
            if not (exc.status_code == 404 and exc.detail == "This user doesn't exist"):
                raise exc

        # There will be no problem with mocked user_invited, because you can't be part
        # of any group if you are not registered.
        if group_db.user_in_group(user_invited):
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="User already in group"
            )

        if group_invite.role == GroupRole.CO_OWNER:
            if group_db.user_is_co_owner(user_host):
                raise StarletteHTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="User is not allowed to invite another co-owner",
                )
            await process_invitation(
                background_tasks,
                smtp_conn,
                group_db,
                group_invite,
                user_host,
                user_invited,
                TokenSubject.GROUP_INVITE_CO_OWNER,
                settings.GROUP_INVITE_CO_OWNER_TOKEN_EXPIRE_MINUTES,
            )

        if group_invite.role == GroupRole.MEMBER:
            await process_invitation(
                background_tasks,
                smtp_conn,
                group_db,
                group_invite,
                user_host,
                user_invited,
                TokenSubject.GROUP_INVITE_MEMBER,
                settings.GROUP_INVITE_MEMBER_TOKEN_EXPIRE_MINUTES,
            )

        return GenericResponse(
            status=GenericStatus.RUNNING,
            message="Group invite email has been processed",
        )

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="User is not allowed to invite"
    )


@router.post(
    "/join",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def join(
    user_invitation: UserTokenWrapper = Depends(get_user_from_invitation),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    if user_current.email == user_invitation.email:
        return await process_join(conn, user_invitation.token, user_current)

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="This user was not invited"
    )


@router.post(
    "/invite/qrcode",
    response_model=GroupInviteQRCodeResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def invite_qrcode(
    user_current: UserTokenWrapper = Depends(get_current_user),
    group_invite: GroupInvite = Body(..., embed=True),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupInviteQRCodeResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_invite.group_id)
    user_host: UserBase = UserBase(**user_current.dict())

    if group_db.user_is_owner(user_host) or group_db.user_is_co_owner(user_host):
        if group_invite.role == GroupRole.OWNER:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Owner role is unique"
            )

        if group_invite.role == GroupRole.CO_OWNER:
            if group_db.user_is_co_owner(user_host):
                raise StarletteHTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="User is not allowed to invite another co-owner",
                )
            return GroupInviteQRCodeResponse(
                invite_link=await process_invitation_qrcode(
                    group_invite,
                    user_host,
                    TokenSubject.GROUP_INVITE_CO_OWNER,
                    settings.GROUP_INVITE_CO_OWNER_TOKEN_EXPIRE_MINUTES,
                )
            )

        if group_invite.role == GroupRole.MEMBER:
            return GroupInviteQRCodeResponse(
                invite_link=await process_invitation_qrcode(
                    group_invite,
                    user_host,
                    TokenSubject.GROUP_INVITE_MEMBER,
                    settings.GROUP_INVITE_MEMBER_TOKEN_EXPIRE_MINUTES,
                )
            )

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="User is not allowed to invite"
    )


@router.post(
    "/join/qrcode",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def join_qrcode(
    token_invitation: str = Depends(get_group_invitation),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    return await process_join(conn, token_invitation, user_current)


@router.put(
    "/leave/{group_id}",
    response_model=GenericResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def leave(
    group_id: str,
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GenericResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_id)
    user_base: UserBase = UserBase(**user_current.dict())
    if group_db.user_in_group(user_base):
        group_id_wrapper: GroupIdWrapper = GroupIdWrapper(
            **group_db.dict(), id=str(group_id)
        )
        await leave_group(conn, group_id_wrapper, user_base)
        return GenericResponse(
            status=GenericStatus.COMPLETED,
            message="User left the group",
        )

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="User is not in the group"
    )


@router.put(
    "/kick",
    response_model=GenericResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def kick(
    group_kick: GroupKick = Body(..., embed=True),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GenericResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_kick.id)
    user_base: UserBase = UserBase(**user_current.dict())
    if group_db.user_in_group(user_base):
        user_base_is_owner: bool = group_db.user_is_owner(user_base)
        user_base_is_co_owner: bool = group_db.user_is_co_owner(user_base)
        if user_base_is_owner or user_base_is_co_owner:
            user_kick_db: UserDB = await get_user_by_email(conn, group_kick.email)
            user_kick: UserBase = UserBase(**user_kick_db.dict())
            if group_db.user_in_group(user_kick):
                if group_db.user_is_owner(user_kick):
                    raise StarletteHTTPException(
                        status_code=HTTP_403_FORBIDDEN,
                        detail="Owner of the group can't be kicked",
                    )
                if group_db.user_is_co_owner(user_kick) and user_base_is_co_owner:
                    raise StarletteHTTPException(
                        status_code=HTTP_403_FORBIDDEN,
                        detail="Co-owner is not allowed to kick other co-owner",
                    )
                group_id_wrapper: GroupIdWrapper = GroupIdWrapper(
                    **group_db.dict(), id=str(group_kick.id)
                )
                await leave_group(conn, group_id_wrapper, user_kick)
                return GenericResponse(
                    status=GenericStatus.COMPLETED,
                    message="User kick out of the group",
                )
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="User is not in the group"
            )
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User is not allowed to kick other members",
        )
    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Current user is not part of the group"
    )
