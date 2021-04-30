from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.database.mongodb import get_database
from app.core.jwt import get_current_user
from app.models.user import UserResponse, UserTokenWrapper, UserUpdate, UserDB
from app.repositories.user import check_availability_username_and_email, update_user
from app.models.token import TokenDB
from app.repositories.token import get_token
from app.models.enums.token_subject import TokenSubject

router = APIRouter()


@router.get(
    "/",
    response_model=UserResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def current_user(
    user_current: UserTokenWrapper = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(user=user_current)


@router.get(
    "/",
    response_model=UserResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def update_current_user(
    user_update: UserUpdate = Body(..., embed=True),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> UserResponse:
    user_update.username = (
        None if user_update.username == user_current.username else user_update.username
    )
    user_update.email = (
        None if user_update.email == user_current.email else user_update.email
    )

    await check_availability_username_and_email(
        conn, user_update.email, user_update.username
    )
    user_db: UserDB = await update_user(conn, user_current, user_update)

    return UserResponse(user=UserTokenWrapper(**user_db.dict()))


@router.patch(
    "/",
    response_model=UserResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def activate_user(
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
):
    token_db: TokenDB = await get_token(conn, user_current.token)
    if token_db.subject == TokenSubject.ACTIVATE:
        user_db: UserDB = await update_user(conn, user_current, UserUpdate(is_active=True))
        return UserResponse(user=UserTokenWrapper(**user_db.dict()))

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Invalid activation"
    )