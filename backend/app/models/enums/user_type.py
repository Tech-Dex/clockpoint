from enum import Enum
from typing import List


class UserType(str, Enum):
    ACTIVE: str = "ACTIVE"
    INACTIVE: str = "INACTIVE"
    GROUP_OWNER: str = "GROUP_OWNER"
    GROUP_USER: str = "GROUP_USER"
    ADMIN: str = "ADMIN"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, UserType))
