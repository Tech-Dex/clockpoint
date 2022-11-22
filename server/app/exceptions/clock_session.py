from app.exceptions import base as base_exceptions


class ClockSessionNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given clock session"

    def __init__(self):
        super().__init__(detail="Clock session not found")


class ClockSessionExpiredException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Clock session has expired")


class ClockSessionDurationTooLongException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(
            detail="Clock session duration is too long. The maximum duration is 16 hours"
        )
