from app.exceptions import base as base_exceptions


class ClockGroupUserEntryNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given request"

    def __init__(self):
        super().__init__(detail="Clock group user entry not found")


class ClockGroupUserReportTimeFilterException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(
            detail="The time filter must start with a session start time and end with a session end time"
        )


class InvalidStartAtAndStopAtException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="The start_at must be before the stop_at")
