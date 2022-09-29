from app.exceptions import base as base_exceptions


class SelfClockEntryException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="You cannot clock yourself")
