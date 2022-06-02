from datetime import datetime, timedelta
from typing import Optional

from databases import Database
from fastapi import Depends, Header
from jwt import PyJWTError, decode, encode
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.models.enums.token_subject import TokenSubject
from app.models.token import BaseTokenPayload, DBTokenPayload
from app.models.user import BaseUser, BaseUserTokenWrapper, DBUser


async def create_token(
    *, data: dict, expires_delta: timedelta = None, subject: str = TokenSubject.ACCESS
) -> str:
    to_encode: dict = data.copy()
    if expires_delta:
        expire: datetime = datetime.utcnow() + expires_delta
    else:
        expire: datetime = datetime.utcnow() + timedelta(minutes=15)

    if not to_encode["subject"]:
        to_encode["subject"] = subject

    to_encode.update({"expire": expire.isoformat(), "subject": to_encode["subject"]})
    jwt = encode(to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM)

    mysql_driver: Database = await get_mysql_driver()

    await DBTokenPayload(**data, token=jwt, expire=expire).save(mysql_driver)

    return jwt


def decode_token(token: str) -> dict:
    try:
        payload: dict = decode(
            token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM]
        )
        if datetime.fromisoformat(payload.get("expire")) < datetime.utcnow():
            raise PyJWTError()
        return payload
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Token is invalid"
        )


async def wrap_user_data_in_token(
    token_payload: BaseTokenPayload,
    expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
) -> str:
    return await create_token(data=token_payload.dict(), expires_delta=expires_delta)


async def get_token_from_authorization_header(
    authorization: str = Header(None),
    required: bool = True,
) -> Optional[str]:
    if authorization:
        prefix, token = authorization.split(" ")
        if token is None and required:
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        if prefix.lower() != "bearer":
            raise StarletteHTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        return token
    elif required:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )
    return None


async def get_current_user(
    mysql_driver: Database = Depends(get_mysql_driver),
    token: str = Depends(get_token_from_authorization_header),
) -> tuple[int, BaseUserTokenWrapper]:
    try:
        payload: dict = decode_token(token)
        token_payload: BaseTokenPayload = BaseTokenPayload(**payload)
    except PyJWTError:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Token is invalid"
        )

    if token_payload.subject == TokenSubject.ACCESS:
        db_user: DBUser = await DBUser.get_by(mysql_driver, "id", token_payload.user_id)
        user: BaseUser = BaseUser(**db_user.dict())

        if user is None:
            raise StarletteHTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="User not found"
            )
        return db_user.id, BaseUserTokenWrapper(**user.dict(), token=token)
    else:
        raise StarletteHTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
        )
