import logging
from datetime import datetime
from typing import Optional, Tuple, Union

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import EmailStr
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.core.config import settings
from app.models.user import UserCreate, UserDB, UserTokenWrapper, UserUpdate

COLLECTION_NAME = "users"


def check_user_object(
    user_object: dict, get_id: bool, raise_bad_request: bool
) -> Union[Tuple[UserDB, str], UserDB]:
    if user_object:
        if get_id:
            return Tuple[UserDB(**user_object), user_object.get("_id")]
        return UserDB(**user_object)

    if raise_bad_request:
        raise StarletteHTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )
    raise StarletteHTTPException(
        status_code=HTTP_404_NOT_FOUND, detail="This user doesn't exist"
    )


async def get_user_by_email(
    conn: AsyncIOMotorClient,
    email: EmailStr,
    get_id: bool = False,
    raise_bad_request: bool = False,
) -> Union[Tuple[UserDB, str], UserDB]:
    user_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"email": email}
    )
    return check_user_object(user_object, get_id, raise_bad_request)


async def get_user_by_username(
    conn: AsyncIOMotorClient,
    username: str,
    get_id: bool = False,
    raise_bad_request: bool = False,
) -> Union[Tuple[UserDB, str], UserDB]:
    user_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"username": username}
    )
    return check_user_object(user_object, get_id, raise_bad_request)


async def get_user_by_id(
    conn: AsyncIOMotorClient,
    object_id: str,
    get_id: bool = False,
    raise_bad_request: bool = False,
) -> Union[Tuple[UserDB, str], UserDB]:
    user_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"_id": ObjectId(object_id)}
    )
    return check_user_object(user_object, get_id, raise_bad_request)


async def create_user(conn: AsyncIOMotorClient, user_create: UserCreate) -> UserDB:
    user_db = UserDB(**user_create.dict())
    user_db.change_password(user_create.password)
    await conn[settings.DATABASE_NAME][COLLECTION_NAME].insert_one(user_db.dict())
    return user_db


async def update_user(
    conn: AsyncIOMotorClient, user_current: UserTokenWrapper, user_update: UserUpdate
) -> UserDB:
    user_db: UserDB
    user_db_id: str
    user_db, user_db_id = await get_user_by_email(conn, user_current.email, get_id=True)

    user_db.updated_at = datetime.utcnow()
    user_db.email = user_update.email or user_db.email
    user_db.first_name = user_update.first_name or user_db.first_name
    user_db.second_name = user_update.second_name or user_db.second_name
    user_db.last_name = user_update.last_name or user_db.last_name
    user_db.username = user_update.username or user_db.username

    if (
        user_db.is_active is False
        and user_update.is_active is not None
        and user_update.is_active is True
    ):
        user_db.activate()

    if user_update.password:
        user_db.change_password(user_update.password)

    await conn[settings.DATABASE_NAME][COLLECTION_NAME].update_one(
        {"_id": ObjectId(user_db_id)}, {"$set": user_db.dict()}
    )

    return user_db


async def delete_user(conn: AsyncIOMotorClient, user_current: UserTokenWrapper) -> bool:
    user_db_id: str
    _, user_db_id = await get_user_by_email(conn, user_current.email, get_id=True)

    result: any = await conn[settings.DATABASE_NAME][COLLECTION_NAME].delete_one(
        {"_id": ObjectId(user_db_id)},
    )
    if result.deleted_count:
        return True

    # This part of code shouldn't be reachable. In case of anything log the user_id
    logging.warning(f"Delete process failed\n" f"User_id: {user_db_id}")
    raise StarletteHTTPException(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Delete process failed"
    )


async def check_availability_username_and_email(
    conn: AsyncIOMotorClient,
    email: Optional[EmailStr] = None,
    username: Optional[str] = None,
):
    if email:
        try:
            await get_user_by_email(conn, email)
        except StarletteHTTPException:
            ...
        else:
            raise StarletteHTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this email already exists",
            )
    if username:
        try:
            await get_user_by_username(conn, username)
        except StarletteHTTPException:
            ...
        else:
            raise StarletteHTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this username already exists",
            )
