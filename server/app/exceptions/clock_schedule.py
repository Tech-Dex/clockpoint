from app.exceptions import base as base_exceptions


class DuplicateClockScheduleException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="Session schedule already exists")


class ClockScheduleNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given clock schedule"

    def __init__(self):
        super().__init__(detail="Session schedule not found")


class ClockScheduleUpdateRequestInvalidException(
    base_exceptions.UnprocessableEntityException
):
    def __init__(self):
        super().__init__(
            detail="Session schedule update request invalid. "
            "If you want to update the hour, please provide start time and duration"
        )
