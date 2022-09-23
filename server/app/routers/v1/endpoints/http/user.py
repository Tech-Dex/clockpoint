from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from databases import Database

from app.core.jwt import create_token
from app.exceptions import ( base as base_exceptions, user as user_exceptions, )
from app.models.enums.token_subject import TokenSubject
from app.models.token import BaseToken
from app.models.user import DBUser, BaseUser, UserToken, DBUserToken
from app.schemas.v1.request import UserUpdateRequest
from app.schemas.v1.response import BaseUserResponse, BaseUserSearchResponse, BaseUsersSearchResponse, GenericResponse
from starlette.status import HTTP_200_OK
from app.models.exception import CustomBaseException
from app.services.dependencies import fetch_user_from_token, fetch_db_user_from_token

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
    status_code=HTTP_200_OK,
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

    await DBUser(**db_user_token.dict()).update(mysql_driver)

    token: str = await create_token(
        data=BaseToken(
            **db_user_token.dict(), users_id=db_user_token.id, subject=TokenSubject.ACCESS
        ).dict(),
        expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    db_user_token.token = token

    return BaseUserResponse(user=UserToken(**db_user_token.dict()))


@router.get(
    "/search/{identifier}",
    response_model=BaseUserSearchResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
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
        user = await DBUser.get_by(mysql_driver, "username", identifier, bypass_exc=True)
        if not user:
            user = await DBUser.get_by(mysql_driver, "email", identifier, exc=user_exceptions.UserNotFoundException())
    elif isinstance(identifier, int):
        user = await DBUser.get_by(mysql_driver, "id", identifier, exc=user_exceptions.UserNotFoundException())

    if not user:
        raise base_exceptions.BadRequestException(detail="Invalid identifier")
    return BaseUserSearchResponse(**user.dict())


@router.get(
    "/filter/{identifier}",
    response_model=BaseUsersSearchResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="search",
    responses={
        **base_responses,
    },
)
async def filter_users(
    identifier: str,
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUsersSearchResponse:
    users: list[DBUser]
    users = await DBUser.like(mysql_driver, "username", f"%{identifier}%", bypass_exc=True)
    if not users:
        users = await DBUser.like(mysql_driver, "email", f"%{identifier}%", bypass_exc=True)

    if not users:
        raise base_exceptions.BadRequestException(detail="Invalid identifier")

    return BaseUsersSearchResponse(users=[BaseUser(**user.dict()) for user in users])

