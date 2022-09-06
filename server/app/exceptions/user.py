from app.exceptions import base as base_exceptions


class UserNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given user"

    def __init__(self):
        super().__init__(detail="User not found")
