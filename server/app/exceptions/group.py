from app.exceptions import base as base_exceptions


class GroupIDMissingException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Group ID is missing")


class GroupNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given group"

    def __init__(self):
        super().__init__(detail="Group not found")


class GroupEmailInvitationException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Group email invitation is missing")
