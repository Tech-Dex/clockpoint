from http import HTTPStatus

import aredis_om
from databases import Database
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token, decode_token
from app.exceptions import (
    auth as auth_exceptions,
    base as base_exceptions,
    token as token_exceptions,
    user as user_exceptions,
)
from app.models.enums.token_subject import TokenSubject
from app.models.exception import CustomBaseException
from app.models.token import ActivateUserToken, BaseToken, RedisToken
from app.models.user import DBUser, DBUserToken, UserToken
from app.schemas.v1.request import (
    UserChangePasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.v1.response import BaseUserResponse, GenericResponse
from app.services.dependencies import fetch_db_user_from_token, fetch_user_from_token

router: APIRouter = APIRouter()

base_responses = {
    400: {
        "description": base_exceptions.BadRequestException.description,
        "model": CustomBaseException,
    }
}


@router.delete(
    "/",
    response_model=GenericResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="delete",
    responses={
        **base_responses,
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def delete(
    mysql_driver: Database = Depends(get_mysql_driver),
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> GenericResponse:
    await db_user_token.delete(mysql_driver)

    return GenericResponse(message="User deleted")


@router.patch(
    "/",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="password",
    responses={**base_responses},
)
async def password(
    change_password: UserChangePasswordRequest,
    mysql_driver: Database = Depends(get_mysql_driver),
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
) -> BaseUserResponse:
    db_user_token.verify_password(
        change_password.password, exc=auth_exceptions.PasswordNotMatchException()
    )

    if change_password.new_password != change_password.confirm_new_password:
        raise auth_exceptions.ChangePasswordException()

    db_user_token.change_password(change_password.new_password)

    delattr(db_user_token, "token")
    await db_user_token.update(mysql_driver)

    token: str = await create_token(
        data=BaseToken(
            **db_user_token.dict(),
            users_id=db_user_token.id,
            subject=TokenSubject.ACCESS
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    db_user_token.token = token

    return BaseUserResponse(user=UserToken(**db_user_token.dict()))


@router.post(
    "/register",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="register",
    responses={
        **base_responses,
        409: {
            "description": auth_exceptions.DuplicateEmailOrUsernameException.description,
            "model": CustomBaseException,
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

    activate_account_token: str = await create_token(
        data=ActivateUserToken(
            users_id=user.id, subject=TokenSubject.ACTIVATE_ACCOUNT
        ).dict(),
        expire=settings.ACTIVATE_ACCOUNT_TOKEN_EXPIRE_MINUTES,
    )
    # TODO send this token in email
    return BaseUserResponse(user=UserToken(**user.dict(), token=token))


@router.post(
    "/login",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="login",
    responses={
        **base_responses,
        401: {
            "description": auth_exceptions.PasswordEmailNotMatchException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
        409: {
            "description": auth_exceptions.DuplicateEmailOrUsernameException.description,
            "model": CustomBaseException,
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
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
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


@router.patch(
    "/activate",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.OK,
    name="activate",
    responses={
        **base_responses,
        404: {
            "description": user_exceptions.UserNotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def activate(
    activate_account_token: str,
    db_user_token: DBUserToken = Depends(fetch_db_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUserResponse:
    print(activate_account_token)
    async with mysql_driver.transaction():
        if not activate_account_token:
            raise token_exceptions.MissingTokenException()

        try:
            redis_token: RedisToken = await RedisToken.find(
                RedisToken.token == activate_account_token,
            ).first()
        except aredis_om.model.model.NotFoundError:
            raise token_exceptions.NotFoundActivateAccountTokenException()

        if not redis_token:
            raise token_exceptions.NotFoundActivateAccountTokenException()

        if redis_token.users_id != db_user_token.id:
            raise token_exceptions.ActivateAccountTokenNotAssociatedWithUserException()

        decode_token(activate_account_token)

        db_user_token.is_active = True

        delattr(db_user_token, "token")
        await db_user_token.update(mysql_driver)

        token: str = await create_token(
            data=BaseToken(
                **db_user_token.dict(),
                users_id=db_user_token.id,
                subject=TokenSubject.ACCESS
            ).dict(),
            expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        return BaseUserResponse(user=UserToken(**db_user_token.dict(), token=token))
