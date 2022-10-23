from __future__ import annotations

from enum import Enum


class SmartEntriesFormat(str, Enum):
    JSON: str = "json"
    EXCEL: str = "excel"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, SmartEntriesFormat))
