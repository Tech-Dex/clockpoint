from app.exceptions import base as base_exceptions


class UserNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given user"

    def __init__(self):
        super().__init__(detail="User not found")


class DuplicateUsernameException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="User with this email or username already exists")
