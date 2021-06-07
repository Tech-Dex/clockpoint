from datetime import datetime, timedelta

from bson.objectid import ObjectId
from fastapi import BackgroundTasks
from fastapi_mail import FastMail
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings
from app.core.jwt import TokenUtils
from app.models.enums.token_subject import TokenSubject
from app.models.group import (
    GroupDB,
    GroupIdWrapper,
    GroupInvite,
    GroupResponse,
    GroupUpdate,
)
from app.models.token import TokenDB, TokenUpdate
from app.models.user import UserBase, UserDB, UserTokenWrapper
from app.services.email import background_send_group_invite_email
from repositories.group import get_group_by_id, update_group
from repositories.token import get_token, update_token


async def process_invitation(
    background_tasks: BackgroundTasks,
    smtp_conn: FastMail,
    group_db: GroupDB,
    group_invite: GroupInvite,
    user_host: UserDB,
    user_invited: UserDB,
    token_subject_role: TokenSubject,
    token_expires_delta_role: int,
):
    token_invite_expires_delta = timedelta(minutes=token_expires_delta_role)
    token_invite: str = await TokenUtils.wrap_user_db_data_into_token(
        user_db=user_host,
        user_email_invited=user_invited.email,
        group_id=group_invite.group_id,
        subject=token_subject_role,
        token_expires_delta=token_invite_expires_delta,
    )
    action_link: str = (
        f"{settings.FRONTEND_DNS}{settings.FRONTEND_GROUP_INVITE}?token={token_invite}"
    )
    await background_send_group_invite_email(
        smtp_conn,
        background_tasks,
        user_invited.email,
        action_link,
        group_db.name,
    )


async def process_invitation_qrcode(
    group_invite: GroupInvite,
    user_host: UserDB,
    token_subject_role: TokenSubject,
    token_expires_delta_role: int,
) -> str:
    token_invite_expires_delta = timedelta(minutes=token_expires_delta_role)
    token_invite: str = await TokenUtils.wrap_user_db_data_into_token(
        user_db=user_host,
        group_id=group_invite.group_id,
        subject=token_subject_role,
        token_expires_delta=token_invite_expires_delta,
    )
    return (
        f"{settings.FRONTEND_DNS}{settings.FRONTEND_GROUP_INVITE}?token={token_invite}"
    )


async def process_join(
    conn: AsyncIOMotorClient, invitation_token: str, user_current: UserTokenWrapper
):
    token_db: TokenDB = await get_token(conn, invitation_token)
    if token_db.used_at:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invitation token already used"
        )

    group_db: GroupDB
    group_db_id: str
    group_db, group_db_id = await get_group_by_id(conn, token_db.group_id, get_id=True)

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
