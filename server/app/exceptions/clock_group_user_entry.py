from app.exceptions import base as base_exceptions


class ClockGroupUserEntryNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given request"

    def __init__(self):
        super().__init__(detail="Clock group user entry not found")
