from app.exceptions import base as base_exceptions


class DecodeTokenException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Token is invalid")


class ExpiredTokenException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Token is expired")


class AccessTokenException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Access token is invalid")


class MissingTokenException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Token is missing")


class BearTokenException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="Bearer token is invalid")


class NotFoundInviteTokenException(base_exceptions.NotFoundException):
    description = "Nothing matches the given invite token."

    def __init__(self):
        super().__init__(detail="Invite token is not found")


class InviteTokenNotAssociatedWithUserException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(detail="Invite token is not associated with user")


class NotFoundActivateAccountTokenException(base_exceptions.NotFoundException):
    description = "Nothing matches the given activate account token."

    def __init__(self):
        super().__init__(detail="Activate account token is not found")


class ActivateAccountTokenNotAssociatedWithUserException(
    base_exceptions.ForbiddenException
):
    def __init__(self):
        super().__init__(detail="Activate account token is not associated with user")
