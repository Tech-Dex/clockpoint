from databases import Database
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.exceptions import (
    auth as auth_exceptions,
    base as base_exceptions,
    user as user_exceptions,
)
from app.models.enums.token_subject import TokenSubject
from app.models.token import BaseToken
from app.models.user import DBUser, UserToken
from app.schemas.v1.request import UserLoginRequest, UserRegisterRequest
from app.schemas.v1.response import BaseUserResponse
from app.services.dependencies import fetch_user_from_token
from http import HTTPStatus
router: APIRouter = APIRouter()

base_responses = {400: {"description": base_exceptions.BadRequestException.description}}


@router.post(
    "/register",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="register",
    responses={
        **base_responses,
        409: {
            "description": auth_exceptions.DuplicateEmailOrUsernameException.description
        },
    },
)
async def register(
    user_register: UserRegisterRequest,
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUserResponse:
    """
    Register a new user.
    """

    user: DBUser = DBUser(**user_register.dict())
    user.change_password(user_register.password)
    await user.save(
        mysql_driver, exc=auth_exceptions.DuplicateEmailOrUsernameException()
    )
    token: str = await create_token(
        data=BaseToken(
            **user.dict(), users_id=user.id, subject=TokenSubject.ACCESS
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return BaseUserResponse(user=UserToken(**user.dict(), token=token))


@router.post(
    "/login",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="login",
    responses={
        400: {"description": base_exceptions.BadRequestException.description},
        401: {"description": base_exceptions.UnauthorizedException.description},
        404: {"description": user_exceptions.UserNotFoundException.description},
        409: {
            "description": auth_exceptions.DuplicateEmailOrUsernameException.description
        },
    },
)
async def login(
    user_login: UserLoginRequest, mysql_driver: Database = Depends(get_mysql_driver)
) -> BaseUserResponse:
    """
    Login a user.
    """

    user: DBUser = await DBUser.get_by(
        mysql_driver,
        "email",
        user_login.email,
        exc=user_exceptions.UserNotFoundException(),
    )

    user.verify_password(user_login.password)

    token: str = await create_token(
        data=BaseToken(
            **user.dict(), users_id=user.id, subject=TokenSubject.ACCESS
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return BaseUserResponse(user=UserToken(**user.dict(), token=token))


@router.get(
    "/refresh",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="refresh",
    responses={
        **base_responses,
        401: {"description": base_exceptions.UnauthorizedException.description},
        404: {"description": user_exceptions.UserNotFoundException.description},
    },
)
async def refresh(
    user_token: UserToken = Depends(fetch_user_from_token),
) -> BaseUserResponse:
    """
    Refresh a user token.
    """
    token: str = await create_token(
        data=BaseToken(
            **user_token.dict(), users_id=user_token.id, subject=TokenSubject.ACCESS
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    user_token.token = token
    return BaseUserResponse(user=UserToken(**user_token.dict()))
