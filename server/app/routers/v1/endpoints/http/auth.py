from databases import Database
from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.models.enums.token_subject import TokenSubject
from app.models.token import BaseToken
from app.models.user import DBUser, UserToken
from app.schemas.v1.request import UserLoginRequest, UserRegisterRequest
from app.schemas.v1.response import BaseUserResponse
from app.services.dependencies import fetch_user_from_token

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
    user_register: UserRegisterRequest,
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseUserResponse:
    """
    Register a new user.
    """

    user: DBUser = DBUser(**user_register.dict())
    user.change_password(user_register.password)
    await user.save(mysql_driver)
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
    status_code=HTTP_200_OK,
    name="login",
    responses={
        400: {"description": "Invalid input"},
        401: {"description": "Invalid credentials"},
        404: {"description": "User not found"},
    },
)
async def login(
    user_login: UserLoginRequest, mysql_driver: Database = Depends(get_mysql_driver)
) -> BaseUserResponse:
    """
    Login a user.
    """

    user: DBUser = await DBUser.get_by(mysql_driver, "email", user_login.email)

    if not user.verify_password(user_login.password):
        raise StarletteHTTPException(status_code=401, detail="Invalid credentials")

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
    status_code=HTTP_200_OK,
    name="refresh",
    responses={
        401: {"description": "Invalid credentials"},
        404: {"description": "User not found"},
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
