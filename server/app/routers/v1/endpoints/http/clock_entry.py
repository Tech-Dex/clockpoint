from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Mapping

import aredis_om
from databases import Database
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token, decode_token
from app.exceptions import (
    base as base_exceptions,
    clock_entry as clock_entry_exceptions,
    clock_session as clock_session_exceptions,
    group as group_exceptions,
    group_user as group_user_exceptions,
    permission as permission_exceptions,
    token as token_exceptions,
)
from app.models.clock_entry import DBClockEntry
from app.models.clock_group_user_session_entry import DBClockGroupUserSessionEntry
from app.models.clock_session import DBClockSession
from app.models.enums.clock_entry_type import ClockEntryType
from app.models.enums.token_subject import TokenSubject
from app.models.exception import CustomBaseException
from app.models.token import QRCodeClockEntryToken, RedisToken
from app.models.user import BaseUser, DBUserToken, UserToken
from app.schemas.v1.request import StartClockSessionRequest
from app.schemas.v1.response import (
    BaseGroupIdWrapper,
    GenericResponse,
    QRCodeClockEntryResponse,
    StartClockSessionResponse,
)
from app.schemas.v1.wrapper import UserInGroupWrapper
from app.services.dependencies import (
    fetch_db_user_from_token,
    fetch_user_generate_report_permission_from_token_qp_id,
    fetch_user_in_group_from_token,
)

base_responses = {
    400: {
        "description": base_exceptions.BadRequestException.description,
        "model": CustomBaseException,
    }
}
router: APIRouter = APIRouter()


@router.post(
    "/entry",
    response_model=GenericResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="Clock in/out",
    responses={
        **base_responses,
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def save_clock_entry(
    clock_entry_token: str,
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> GenericResponse:
    try:
        redis_token: RedisToken = await RedisToken.find(
            RedisToken.token == clock_entry_token
        ).first()
    except aredis_om.model.model.NotFoundError:
        raise token_exceptions.NotFoundInviteTokenException()

    if not redis_token:
        raise token_exceptions.NotFoundInviteTokenException()

    if redis_token.users_id == db_user_token.id:
        raise clock_entry_exceptions.SelfClockEntryException()

    decode_token(clock_entry_token)

    user_in_group: UserInGroupWrapper = await fetch_user_in_group_from_token(
        group_id=redis_token.groups_id,
        user_token=UserToken(**db_user_token.dict()),
        mysql_driver=mysql_driver,
    )

    db_session: DBClockSession = await DBClockSession.get_by(
        mysql_driver,
        "id",
        redis_token.clock_sessions_id,
        exc=clock_session_exceptions.ClockSessionNotFoundException(),
    )
    if datetime.utcnow() > db_session.stop_at:
        raise clock_session_exceptions.ClockSessionExpiredException()

    last_clock_entry: Mapping = await DBClockGroupUserSessionEntry.last_clock_entry(
        mysql_driver, user_in_group.group_user.id, db_session.id, bypass_exc=True
    )

    # If the above checks are passed, we can now save the clock entry
    # The user will be able to clock out only if he has clocked in for that session
    # The user will be able to clock in only if he has clocked out for that session
    if not last_clock_entry and redis_token.type == ClockEntryType.clock_out:
        raise clock_entry_exceptions.ClockOutWithoutClockInException()

    if last_clock_entry:
        if (
            redis_token.type == ClockEntryType.clock_in
            and last_clock_entry["type"] == ClockEntryType.clock_in
        ):
            raise clock_entry_exceptions.UserAlreadyClockedInException()

        if (
            redis_token.type == ClockEntryType.clock_out
            and last_clock_entry["type"] == ClockEntryType.clock_out
        ):
            raise clock_entry_exceptions.UserAlreadyClockedOutException()

    async with mysql_driver.transaction():
        db_clock_entry: DBClockEntry = await DBClockEntry(
            clock_at=datetime.utcnow(),
            type=redis_token.type,
        ).save(mysql_driver)

        await DBClockGroupUserSessionEntry(
            clock_sessions_id=db_session.id,
            groups_users_id=user_in_group.group_user.id,
            clock_entries_id=db_clock_entry.id,
        ).save(mysql_driver)

        await RedisToken.delete(redis_token.pk)

        return GenericResponse(message=f"Clock {redis_token.type} entry saved")


@router.post(
    "/{group_id}",
    response_model=StartClockSessionResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="Start a session",
    responses={
        **base_responses,
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def start_session(
    clock_session: StartClockSessionRequest,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_generate_report_permission_from_token_qp_id
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> StartClockSessionResponse:
    async with mysql_driver.transaction():
        start_at = datetime.utcnow()
        stop_at = start_at + timedelta(minutes=clock_session.duration)
        db_clock_session: DBClockSession = await DBClockSession(
            users_id=user_in_group.user_token.id,
            start_at=start_at,
            stop_at=stop_at,
        ).save(mysql_driver)

        await DBClockGroupUserSessionEntry(
            clock_sessions_id=db_clock_session.id,
            groups_users_id=user_in_group.group_user.id,
        ).save(mysql_driver)

        return StartClockSessionResponse(
            user=BaseUser(**user_in_group.user_token.dict()),
            group=BaseGroupIdWrapper(**user_in_group.group.dict()),
            **db_clock_session.dict(),
        )


@router.get(
    "/{group_id}/{session_id}/qr",
    response_model=QRCodeClockEntryResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="Generate QR Code Clock Entry",
    responses={
        **base_responses,
        403: {
            "description": permission_exceptions.NotAllowedToGenerateQRCodeEntryAndGenerateReportException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def generate_qr_code_clock_entry(
    entry_type: ClockEntryType,
    session_id: int,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_generate_report_permission_from_token_qp_id
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> QRCodeClockEntryResponse:
    db_session: DBClockSession = await DBClockSession.get_by(
        mysql_driver,
        "id",
        session_id,
        exc=clock_session_exceptions.ClockSessionNotFoundException(),
    )
    if datetime.utcnow() > db_session.stop_at:
        raise clock_session_exceptions.ClockSessionExpiredException()

    token: str = await create_token(
        data=QRCodeClockEntryToken(
            users_id=user_in_group.user_token.id,
            subject=TokenSubject.QR_CODE_ENTRY,
            groups_id=user_in_group.group.id,
            clock_sessions_id=session_id,
            type=entry_type,
        ).dict(),
        expire=settings.QR_CODE_CLOCK_ENTRY_TOKEN_EXPIRE_MINUTES,
    )

    return QRCodeClockEntryResponse(
        token=token, group=BaseGroupIdWrapper(**user_in_group.group.dict())
    )
