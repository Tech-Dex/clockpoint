from __future__ import annotations

from enum import Enum


class TokenSubject(str, Enum):
    ACCESS: str = "ACCESS"
    VERIFY_ACCOUNT: str = "VERIFY_ACCOUNT"
    RESET_PASSWORD: str = "RESET_PASSWORD"
    GROUP_INVITE: str = "GROUP_INVITE"
    QR_CODE_GROUP_INVITE: str = "QR_CODE_GROUP_INVITE"
    QR_CODE_ENTRY: str = "QR_CODE_ENTRY"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, TokenSubject))
