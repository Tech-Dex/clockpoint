from datetime import datetime
from typing import List, Tuple

from bson.objectid import ObjectId
from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi_mail import FastMail
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.core.jwt import get_current_user, get_user_from_invitation
from app.core.smtp.smtp import get_smtp
from app.models.enums.group_role import GroupRole
from app.models.enums.token_subject import TokenSubject
from app.models.generic_response import GenericResponse, GenericStatus
from app.models.group import (
    GroupCreate,
    GroupDB,
    GroupIdWrapper,
    GroupInvite,
    GroupResponse,
    GroupsResponse,
    GroupUpdate,
)
from app.models.token import TokenDB, TokenUpdate
from app.models.user import UserBase, UserDB, UserTokenWrapper
from app.repositories.group import (
    create_group,
    get_group_by_id,
    get_groups_by_user,
    update_group,
)
from app.repositories.token import get_token, update_token
from app.repositories.user import get_user_by_email
from app.utils.group import process_invitation

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
    user_inviting: UserBase = UserBase(**user_current.dict())

    if group_db.user_is_owner(user_inviting) or group_db.user_is_co_owner(
        user_inviting
    ):
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
            if exc.status_code == 404 and exc.detail == "This user doesn't exist":
                ...

        if group_db.user_in_group(user_invited):
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="User already in group"
            )

        if group_invite.role == GroupRole.CO_OWNER:
            if group_db.user_is_co_owner(user_inviting):
                raise StarletteHTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="User is not allowed to invite another co-owner",
                )
            await process_invitation(
                background_tasks,
                smtp_conn,
                group_db,
                group_invite,
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
        token_db: TokenDB = await get_token(conn, user_invitation.token)
        if token_db.used_at:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invitation token already used"
            )

        group_db: GroupDB
        group_db_id: str
        group_db, group_db_id = await get_group_by_id(
            conn, token_db.group_id, get_id=True
        )

        group_update: GroupUpdate = GroupUpdate(member=UserBase(**user_current.dict()))
        if token_db.subject == TokenSubject.GROUP_INVITE_CO_OWNER:
            group_update: GroupUpdate = GroupUpdate(
                co_owner=UserBase(**user_current.dict())
            )

        group_id_wrapper: GroupIdWrapper = GroupIdWrapper(
            **group_db.dict(), id=str(group_db_id)
        )
        group_db_updated: GroupDB
        group_db_id_updated: ObjectId
        group_db_updated, group_db_id_updated = await update_group(
            conn, group_id_wrapper, group_update
        )

        await update_token(
            conn, TokenUpdate(token=token_db.token, used_at=datetime.utcnow())
        )

        return GroupResponse(
            group=GroupIdWrapper(**group_db_updated.dict(), id=str(group_db_id_updated))
        )

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="This user was not invited"
    )
