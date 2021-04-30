from enum import Enum
from typing import Any, List

from models.rwmodel import RWModel


class GenericStatus(str, Enum):
    RUNNING: str = "RUNNING"
    COMPLETED: str = "COMPLETED"

    @classmethod
    def has_value(cls, value) -> bool:
        return value.upper() in cls._value2member_map_

    @classmethod
    def list(cls) -> List[str]:
        return list(map(lambda c: c.value, GenericStatus))


class GenericResponse(RWModel):
    status: GenericStatus = None
    message: Any = None
