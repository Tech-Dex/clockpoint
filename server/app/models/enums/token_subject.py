from __future__ import annotations

from enum import Enum


class TokenSubject(str, Enum):
    ACCESS: str = "ACCESS"
    ACTIVATE_ACCOUNT: str = "ACTIVATE_ACCOUNT"
    RESET: str = "RESET"
    GROUP_INVITE: str = "GROUP_INVITE"
    QR_CODE_GROUP_INVITE: str = "QR_CODE_GROUP_INVITE"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, TokenSubject))
