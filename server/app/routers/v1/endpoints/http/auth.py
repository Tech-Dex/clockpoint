from datetime import timedelta

from databases import Database
from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.models.enums.token_subject import TokenSubject
from app.models.token import BaseTokenPayload
from app.models.user import (
    BaseUser,
    BaseUserResponse,
    BaseUserTokenWrapper,
    DBUser,
    UserLogin,
    UserRegister,
)
from app.services.dependencies import get_current_user

router: APIRouter = APIRouter()


@router.post(
    "/register",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="register",
    responses={
        400: {"description": "Invalid input"},
        409: {"description": "User already exists"},
    },
)
async def register(
    user_register: UserRegister, mysql_driver: Database = Depends(get_mysql_driver)
) -> BaseUserResponse:
    """
    Register a new user.
    """

    user: DBUser = DBUser(**user_register.dict())
    user.change_password(user_register.password)
    await user.save(mysql_driver)
    token: str = await create_token(
        data=BaseTokenPayload(
            **user.dict(), user_id=user.id, subject=TokenSubject.ACCESS
        ).dict(),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return BaseUserResponse(user=BaseUserTokenWrapper(**user.dict(), token=token))


@router.post(
    "/login",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="login",
    responses={
        400: {"description": "Invalid input"},
        401: {"description": "Invalid credentials"},
        404: {"description": "User not found"},
    },
)
async def login(
    user_login: UserLogin, mysql_driver: Database = Depends(get_mysql_driver)
) -> BaseUserResponse:
    """
    Login a user.
    """

    db_user: DBUser = await DBUser.get_by(mysql_driver, "email", user_login.email)

    if not db_user.verify_password(user_login.password):
        raise StarletteHTTPException(status_code=401, detail="Invalid credentials")

    user: BaseUser = BaseUser(**db_user.dict())
    token: str = await create_token(
        data=BaseTokenPayload(
            **user.dict(), user_id=db_user.id, subject=TokenSubject.ACCESS
        ).dict(),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return BaseUserResponse(user=BaseUserTokenWrapper(**user.dict(), token=token))


@router.get(
    "/refresh",
    response_model=BaseUserResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="refresh",
    responses={
        401: {"description": "Invalid credentials"},
        404: {"description": "User not found"},
    },
)
async def refresh(
    id_user_token: tuple[int, BaseUserTokenWrapper] = Depends(get_current_user)
) -> BaseUserResponse:
    """
    Refresh a user token.
    """

    user_id: int
    user_token: BaseUserTokenWrapper
    user_id, user_token = id_user_token

    user: BaseUser = BaseUser(**user_token.dict())
    token: str = await create_token(
        data=BaseTokenPayload(
            **user.dict(), user_id=user_id, subject=TokenSubject.ACCESS
        ).dict(),
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return BaseUserResponse(user=BaseUserTokenWrapper(**user.dict(), token=token))
