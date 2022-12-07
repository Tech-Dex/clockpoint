from __future__ import annotations

from enum import Enum


class NotificationScope(str, Enum):
    GROUP_INVITE: str = "group_invite"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, NotificationScope))
