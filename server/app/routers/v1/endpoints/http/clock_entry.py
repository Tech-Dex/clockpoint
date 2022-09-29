from datetime import datetime
from http import HTTPStatus

import aredis_om.model.model
from databases import Database
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token, decode_token
from app.exceptions import (
    base as base_exceptions,
    clock_entry as clock_entry_exceptions,
    group as group_exceptions,
    group_user as group_user_exceptions,
    permission as permission_exceptions,
    token as token_exceptions,
)
from app.models.clock_entry import DBClockEntry
from app.models.clock_group_user_entry import DBClockGroupUserEntry
from app.models.enums.clock_entry_type import ClockEntryType
from app.models.enums.token_subject import TokenSubject
from app.models.exception import CustomBaseException
from app.models.token import QRCodeClockEntryToken, RedisToken
from app.schemas.v1.response import (
    BaseGroupIdWrapper,
    GenericResponse,
    QRCodeClockEntryResponse,
)
from app.schemas.v1.wrapper import UserInGroupWrapper
from app.services.dependencies import (
    fetch_user_generate_report_permission_from_token_qp_id,
    fetch_user_in_group_from_token_qp_id,
)

base_responses = {
    400: {
        "description": base_exceptions.BadRequestException.description,
        "model": CustomBaseException,
    }
}
router: APIRouter = APIRouter()


@router.post(
    "/{group_id}",
    # response_model=any,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="Save clock entry",
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
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_id),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> any:
    try:
        redis_token: RedisToken = await RedisToken.find(
            RedisToken.token == clock_entry_token
        ).first()
    except aredis_om.model.model.NotFoundError:
        raise token_exceptions.NotFoundInviteTokenException()

    if not redis_token:
        raise token_exceptions.NotFoundInviteTokenException()

    if redis_token.users_id == user_in_group.user_token.id:
        raise clock_entry_exceptions.SelfClockEntryException()

    decode_token(clock_entry_token)
    async with mysql_driver.transaction():
        db_clock_entry: DBClockEntry = await DBClockEntry(
            datetime=datetime.utcnow(),
            type=redis_token.type,
        ).save(mysql_driver)

        await DBClockGroupUserEntry(
            clock_entries_id=db_clock_entry.id,
            groups_users_id=user_in_group.group_user.id,
        ).save(mysql_driver)

        await RedisToken.delete(redis_token.pk)

        return GenericResponse(message="Clock entry saved")


@router.get(
    "/{group_id}/qr",
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
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_generate_report_permission_from_token_qp_id
    ),
) -> QRCodeClockEntryResponse:
    token: str = await create_token(
        data=QRCodeClockEntryToken(
            users_id=user_in_group.user_token.id,
            subject=TokenSubject.QR_CODE_ENTRY,
            groups_id=user_in_group.group.id,
            type=entry_type,
        ).dict(),
        expire=settings.QR_CODE_CLOCK_ENTRY_TOKEN_EXPIRE_MINUTES,
    )

    return QRCodeClockEntryResponse(
        token=token, group=BaseGroupIdWrapper(**user_in_group.group.dict())
    )


# TODO:
# Think about how to handle the case in->out
# The admin/owner will be able to end a session -> all users that "IN" that session will get an "OUT"
# The user will be bypassed if he already got an out entry IN THAT DAY
