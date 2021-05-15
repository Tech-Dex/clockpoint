from datetime import timedelta

from fastapi import BackgroundTasks
from fastapi_mail import FastMail

from app.core.config import settings
from app.core.jwt import TokenUtils
from app.models.enums.token_subject import TokenSubject
from app.models.group import GroupDB, GroupInvite
from app.models.user import UserDB
from app.services.email import background_send_group_invite_email


async def process_invitation(
    background_tasks: BackgroundTasks,
    smtp_conn: FastMail,
    group_db: GroupDB,
    group_invite: GroupInvite,
    user_invited: UserDB,
    token_subject_role: TokenSubject,
    token_expires_delta_role: int,
):
    token_invite_expires_delta = timedelta(minutes=token_expires_delta_role)
    token_invite: str = await TokenUtils.wrap_user_db_data_into_token(
        user_invited,
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
