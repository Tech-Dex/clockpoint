from app.exceptions import base as base_exceptions


class DuplicateEmailOrUsernameException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="User with this email or username already exists")


class PasswordEmailNotMatchException(base_exceptions.UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Password or email is incorrect")


class PasswordNotMatchException(base_exceptions.UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Password is incorrect")


class ChangePasswordException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Password and confirm password must be the same")
