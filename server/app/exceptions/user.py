from app.exceptions import base as base_exceptions


class UserNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given user"

    def __init__(self):
        super().__init__(detail="User not found")


class DuplicateUsernameException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="User with this email or username already exists")


class PhoneNumberFormatException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Phone number must be valid. Example: +1 123 456 7890 or send a country name")