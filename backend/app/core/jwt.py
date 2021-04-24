from datetime import datetime, timedelta

from fastapi import Header
from jwt import PyJWTError, decode, encode
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.models.token import TokenDB
from app.models.user import UserDB

COLLECTION_NAME = "tokens"


class TokenUtils:
    @staticmethod
    async def save_token(token: TokenDB):
        conn: AsyncIOMotorClient = await get_database()
        await conn[settings.DATABASE_NAME][COLLECTION_NAME].insert_one(token.dict())

    @staticmethod
    async def wrap_user_db_data_into_token(user_db: UserDB) -> str:
        token_expires_delta: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token: str = await create_token(
            data={
                "email": user_db.email,
                "username": user_db.username,
            },
            expires_delta=token_expires_delta,
            subject="access",
        )

        return token


async def create_token(
    *, data: dict, expires_delta: timedelta = None, subject: str
) -> str:
    to_encode: dict = data.copy()
    expire_datetime: datetime = datetime.utcnow() + timedelta(minutes=10)
    if expires_delta:
        expire_datetime: datetime = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire_datetime, "subject": subject})

    encoded_jwt = encode(
        to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM
    )
    await TokenUtils.save_token(
        TokenDB(
            **to_encode,
            token=encoded_jwt,
            created_at=datetime.utcnow(),
            expire_datetime=expire_datetime
        )
    )
    return encoded_jwt


def validate_token(token: str) -> str:
    try:
        decode(token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM])
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

    return token


def validate_x_token(x_token: str = Header(...)) -> str:
    return validate_token(x_token)
