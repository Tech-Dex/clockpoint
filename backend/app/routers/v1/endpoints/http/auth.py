from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.core.database.mongodb import get_database
from app.core.jwt import TokenUtils
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
from app.models.enums.token_subject import TokenSubject

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=HTTP_201_CREATED,
    response_model_exclude_unset=True,
)
async def register(
    user_create: UserCreate = Body(..., embed=True),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> UserResponse:
    await check_availability_username_and_email(
        conn, user_create.email, user_create.username
    )
    async with await conn.start_session() as session, session.start_transaction():
        user_db: UserDB = await create_user(conn, user_create)
        token: str = await TokenUtils.wrap_user_db_data_into_token(
            user_db, subject=TokenSubject.ACCESS
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
