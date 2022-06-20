from __future__ import annotations

from datetime import datetime, timedelta

from databases import Database
from fastapi import Header
from jwt import PyJWTError, decode, encode
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings
from app.models.enums.token_subject import TokenSubject
from app.models.token import DBToken


async def create_token(
    *,
    mysql_driver: Database,
    data: dict,
    expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    subject: str = TokenSubject.ACCESS,
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

    await DBToken(**data, token=jwt, expire=expire).save(mysql_driver)

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


async def get_token_from_authorization_header(
    authorization: str = Header(None),
    required: bool = True,
) -> str | None:
    if authorization:
        prefix, token = authorization.split(" ")
        if token is None and required:
            # TODO: create custom exceptions
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
