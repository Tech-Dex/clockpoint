from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi_mail import FastMail
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.core.jwt import TokenUtils
from app.core.smtp.smtp import get_smtp
from app.models.enums.token_subject import TokenSubject
from app.models.user import (
    UserCreate,
    UserDB,
    UserLogin,
    UserResponse,
    UserTokenWrapper,
)
from app.repositories.user import (
    check_availability_username_and_email,
    create_user,
    get_user_by_email,
)
from app.services.email import background_send_new_account_email

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=HTTP_201_CREATED,
    response_model_exclude_unset=True,
)
async def register(
    background_tasks: BackgroundTasks,
    user_create: UserCreate = Body(..., embed=True),
    conn: AsyncIOMotorClient = Depends(get_database),
    smtp_conn: FastMail = Depends(get_smtp),
) -> UserResponse:
    await check_availability_username_and_email(
        conn, user_create.email, user_create.username
    )
    async with await conn.start_session() as session, session.start_transaction():
        user_db: UserDB = await create_user(conn, user_create)
        token: str = await TokenUtils.wrap_user_db_data_into_token(
            user_db, subject=TokenSubject.ACCESS
        )
        token_activation_expires_delta = timedelta(minutes=60 * 24 * 7)  # 7 days
        token_activation: str = await TokenUtils.wrap_user_db_data_into_token(
            user_db,
            subject=TokenSubject.ACTIVATE,
            token_expires_delta=token_activation_expires_delta,
        )

        action_link: str = f"{settings.FRONTEND_DNS}{settings.FRONTEND_ACTIVATION_PATH}?token={token_activation}"
        await background_send_new_account_email(
            smtp_conn, background_tasks, user_db.email, action_link
        )
        return UserResponse(user=UserTokenWrapper(**user_db.dict(), token=token))


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def login(
    user_login: UserLogin = Body(..., embed=True),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> UserResponse:
    user_db: UserDB = await get_user_by_email(
        conn, user_login.email, raise_bad_request=True
    )
    if not user_db.check_password(user_login.password):
        raise StarletteHTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )
    token: str = await TokenUtils.wrap_user_db_data_into_token(
        user_db, subject=TokenSubject.ACCESS
    )
    return UserResponse(user=UserTokenWrapper(**user_db.dict(), token=token))
