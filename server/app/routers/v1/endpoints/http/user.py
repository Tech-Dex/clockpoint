from http import HTTPStatus

from databases import Database
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.exceptions import base as base_exceptions, user as user_exceptions
from app.models.enums.token_subject import TokenSubject
from app.models.exception import CustomBaseException
from app.models.token import BaseToken
from app.models.user import BaseUser, DBUser, DBUserToken, UserToken
from app.models.user_meta import DBUserMeta
from app.schemas.v1.request import UserMetaUpdateRequest, UserUpdateRequest
from app.schemas.v1.response import (
    BaseUserMetaResponse,
    BaseUserResponse,
    BaseUserSearchResponse,
    BaseUsersSearchResponse,
)
from app.services.dependencies import fetch_db_user_from_token

router: APIRouter = APIRouter()

base_responses = {
    400: {
        "description": base_exceptions.BadRequestException.description,
        "model": CustomBaseException,
    }
}


@router.put(
    "/",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="update",
    responses={
        **base_responses,
        409: {
            "description": user_exceptions.DuplicateUsernameException.description,
            "model": CustomBaseException,
        },
    },
)
async def update(
    user_update: UserUpdateRequest,
    mysql_driver: Database = Depends(get_mysql_driver),
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> BaseUserResponse:
    if user_update.username:
        if DBUser.get_by(mysql_driver, "username", user_update.username):
            raise user_exceptions.DuplicateUsernameException()
    db_user_token.username = user_update.username or db_user_token.username
    db_user_token.first_name = user_update.first_name or db_user_token.first_name
    db_user_token.second_name = user_update.second_name or db_user_token.second_name
    db_user_token.last_name = user_update.last_name or db_user_token.last_name
    db_user_token.phone_number = user_update.phone_number or db_user_token.phone_number

    await db_user_token.parse_phone_number(user_update.phone_number_country_name)

    delattr(db_user_token, "token")
    await db_user_token.update(mysql_driver)

    token: str = await create_token(
        data=BaseToken(
            **db_user_token.dict(),
            users_id=db_user_token.id,
            subject=TokenSubject.ACCESS,
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    db_user_token.token = token

    return BaseUserResponse(user=UserToken(**db_user_token.dict()))


@router.get(
    "/meta",
    response_model=BaseUserMetaResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="current user meta",
    responses={
        **base_responses,
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def get_meta(
    mysql_driver: Database = Depends(get_mysql_driver),
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> BaseUserMetaResponse:
    return BaseUserMetaResponse(
        user=BaseUser(**db_user_token.dict()),
        meta=(
            await DBUserMeta.get_by(mysql_driver, "user_id", db_user_token.id)
        ).dict(),
    )


@router.put(
    "/meta",
    response_model=BaseUserMetaResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="update current user meta",
    responses={
        **base_responses,
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def update_meta(
    user_meta_update: UserMetaUpdateRequest,
    mysql_driver: Database = Depends(get_mysql_driver),
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> BaseUserMetaResponse:
    db_user_meta: DBUserMeta = await DBUserMeta.get_by(
        mysql_driver, "user_id", db_user_token.id
    )
    if user_meta_update.has_push_notifications is not None:
        db_user_meta.has_push_notifications = user_meta_update.has_push_notifications

    await db_user_meta.update(mysql_driver)

    return BaseUserMetaResponse(
        user=BaseUser(**db_user_token.dict()),
        meta=db_user_meta.dict(),
    )


@router.get(
    "/search/{identifier}",
    response_model=BaseUserSearchResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="search",
    responses={
        **base_responses,
    },
)
async def search(
    identifier: int | str,
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUserSearchResponse:
    user: DBUser | None = None
    if isinstance(identifier, str):
        user = await DBUser.get_by(
            mysql_driver, "username", identifier, bypass_exc=True
        )
        if not user:
            user = await DBUser.get_by(
                mysql_driver,
                "email",
                identifier,
                exc=user_exceptions.UserNotFoundException(),
            )
    elif isinstance(identifier, int):
        user = await DBUser.get_by(
            mysql_driver, "id", identifier, exc=user_exceptions.UserNotFoundException()
        )

    if not user:
        raise base_exceptions.BadRequestException(detail="Invalid identifier")
    return BaseUserSearchResponse(**user.dict())


@router.get(
    "/filter/{identifier}",
    response_model=BaseUsersSearchResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="filter",
    responses={
        **base_responses,
    },
)
async def filter_users(
    identifier: str,
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUsersSearchResponse:
    users: list[DBUser]
    users = await DBUser.like(
        mysql_driver, "username", f"%{identifier}%", bypass_exc=True
    )
    if not users:
        users = await DBUser.like(
            mysql_driver, "email", f"%{identifier}%", bypass_exc=True
        )

    if not users:
        raise base_exceptions.BadRequestException(detail="Invalid identifier")

    return BaseUsersSearchResponse(users=[BaseUser(**user.dict()) for user in users])
