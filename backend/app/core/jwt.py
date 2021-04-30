from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header
from jwt import PyJWTError, decode, encode
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.models.enums.token_subject import TokenSubject
from app.models.token import TokenDB, TokenPayload
from app.models.user import UserDB, UserTokenWrapper
from app.repositories.token import save_token
from app.repositories.user import get_user_by_email


class TokenUtils:
    @classmethod
    async def wrap_user_db_data_into_token(
        cls, user_db: UserDB, subject: TokenSubject
    ) -> str:
        token_expires_delta: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token: str = await cls.create_token(
            data={
                "email": user_db.email,
                "username": user_db.username,
            },
            expires_delta=token_expires_delta,
            subject=subject,
        )

        return token

    @staticmethod
    async def create_token(
        *, data: dict, expires_delta: timedelta = None, subject: TokenSubject
    ) -> str:
        to_encode: dict = data.copy()
        expire_datetime: datetime = datetime.utcnow() + timedelta(minutes=10)
        if expires_delta:
            expire_datetime: datetime = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire_datetime, "subject": subject.value})

        encoded_jwt = encode(
            to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM
        )
        await save_token(
            TokenDB(
                **to_encode,
                token=encoded_jwt,
                created_at=datetime.utcnow(),
                expire_datetime=expire_datetime
            )
        )
        return encoded_jwt


def get_token(
    authorization: Optional[str] = Header(None),
    activation: Optional[str] = Header(None),
    recovery: Optional[str] = Header(None),
) -> str:
    token: str
    if authorization:
        prefix, token = authorization.split(" ")
        if settings.JWT_TOKEN_PREFIX != prefix:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid authorization"
            )
        return token
    if activation:
        prefix, token = activation.split(" ")
        if settings.JWT_TOKEN_PREFIX != prefix:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid activation"
            )
        return token
    if recovery:
        prefix, token = recovery.split(" ")
        if settings.JWT_TOKEN_PREFIX != prefix:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid recover"
            )
        return token

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Invalid header"
    )


async def get_current_user(
    conn: AsyncIOMotorClient = Depends(get_database),
    token: str = Depends(get_token),
) -> UserTokenWrapper:
    try:
        payload = decode(
            token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

    user_db = await get_user_by_email(conn, token_data.email)
    if not user_db:
        raise StarletteHTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="This user doesn't exist"
        )

    return UserTokenWrapper(**user_db.dict(), token=token)
