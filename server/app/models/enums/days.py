from __future__ import annotations

from enum import Enum


class Days(str, Enum):
    MONDAY: str = "monday"
    TUESDAY: str = "tuesday"
    WEDNESDAY: str = "wednesday"
    THURSDAY: str = "thursday"
    FRIDAY: str = "friday"
    SATURDAY: str = "saturday"
    SUNDAY: str = "sunday"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda c: c.value, Days))
