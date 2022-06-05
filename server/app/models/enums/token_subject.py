from enum import Enum
from typing import List


class TokenSubject(str, Enum):
    ACCESS: str = "ACCESS"
    ACTIVATE: str = "ACTIVATE"
    RESET: str = "RESET"
    INVITE: str = "INVITE"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, TokenSubject))
