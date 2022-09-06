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
