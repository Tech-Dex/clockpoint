from __future__ import annotations

from enum import Enum


class ClockEntryType(str, Enum):
    clock_in: str = "in"
    clock_out: str = "out"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, ClockEntryType))
