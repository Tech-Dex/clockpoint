from enum import Enum
from typing import List


class Roles(str, Enum):
    OWNER: str = "owner"
    ADMIN: str = "admin"
    USER: str = "user"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, Roles))
