from enum import Enum
from typing import List


class GroupRole(str, Enum):
    OWNER: str = "OWNER"
    CO_OWNER: str = "CO-OWNER"
    MEMBER: str = "MEMBER"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, GroupRole))
