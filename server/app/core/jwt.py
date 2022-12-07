from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import WebSocketException
from jwt import PyJWTError, decode, encode

from app.core.config import settings
from app.exceptions import token as token_exceptions
from app.models.enums.token_subject import TokenSubject
from app.models.token import RedisToken


async def create_token(
    *,
    data: dict,
    expire: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    subject: str = TokenSubject.ACCESS,
) -> str:
    to_encode: dict = data.copy()
    expire_date: datetime
    if expire:
        expire_date: datetime = datetime.utcnow() + timedelta(minutes=expire)
    else:
        expire_date: datetime = datetime.utcnow() + timedelta(minutes=15)
        expire = 15 * 60

    if not to_encode["subject"]:
        to_encode["subject"] = subject

    to_encode.update(
        {"expire": expire_date.isoformat(), "subject": to_encode["subject"]}
    )
    jwt = encode(to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM)

    redis_token: RedisToken = await RedisToken(**data, token=jwt).save()
    await redis_token.expire(expire * 60)

    return jwt


def decode_token(token: str) -> dict:
    try:
        payload: dict = decode(
            token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM]
        )
        if datetime.fromisoformat(payload.get("expire")) < datetime.utcnow():
            raise token_exceptions.ExpiredTokenException()
        return payload
    except PyJWTError:
        raise token_exceptions.DecodeTokenException()


def ws_decode_token(token: str) -> dict:
    try:
        payload: dict = decode(
            token, str(settings.SECRET_KEY), algorithms=[settings.ALGORITHM]
        )
        if datetime.fromisoformat(payload.get("expire")) < datetime.utcnow():
            raise WebSocketException(
                token_exceptions.ExpiredTokenException().status_code,
                token_exceptions.ExpiredTokenException().detail,
            )
        return payload
    except PyJWTError:
        raise WebSocketException(
            token_exceptions.DecodeTokenException().status_code,
            token_exceptions.DecodeTokenException().detail,
        )
