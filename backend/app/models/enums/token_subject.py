from enum import Enum
from typing import List


class TokenSubject(str, Enum):
    ACCESS: str = "ACCESS"
    ACTIVATE: str = "ACTIVATE"
    RECOVER: str = "RECOVER"
    GROUP_INVITE_CO_OWNER: str = "GROUP-INVITE-CO-OWNER"
    GROUP_INVITE_MEMBER: str = "GROUP-INVITE-MEMBER"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, TokenSubject))
