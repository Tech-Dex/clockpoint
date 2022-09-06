from app.exceptions import base as base_exceptions


class DuplicateEmailOrUsernameException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="User with this email or username already exists")


class PasswordsNotMatchException(base_exceptions.UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Password or email is incorrect")
