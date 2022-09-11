from http import HTTPStatus

from starlette.exceptions import HTTPException as StarletteHTTPException


class CustomBaseException(StarletteHTTPException):
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    description: str = HTTPStatus.INTERNAL_SERVER_ERROR.description
    phrase: str = HTTPStatus.INTERNAL_SERVER_ERROR.phrase
    fields: dict = {}

    def __init__(
        self,
        detail: str,
        status: HTTPStatus = None,
        headers: dict = None,
        fields: dict = None,
    ):
        if status:
            super().__init__(status.value or self.status_code, detail, headers)
            self.status_code = status.value or self.status_code
            self.description = status.description or self.description
            self.phrase = status.phrase or self.phrase
            if status.value and not status.description:
                self.description = ""
        else:
            super().__init__(self.status_code, detail, headers)

        self.fields = fields or {}


class BadRequestException(CustomBaseException):
    status_code = HTTPStatus.BAD_REQUEST
    description = HTTPStatus.BAD_REQUEST.description
    phrase = HTTPStatus.BAD_REQUEST.phrase


class NotFoundException(CustomBaseException):
    status_code = HTTPStatus.NOT_FOUND
    description = HTTPStatus.NOT_FOUND.description
    phrase = HTTPStatus.NOT_FOUND.phrase


class UnauthorizedException(CustomBaseException):
    status_code = HTTPStatus.UNAUTHORIZED
    description = HTTPStatus.UNAUTHORIZED.description
    phrase = HTTPStatus.UNAUTHORIZED.phrase


class UnprocessableEntityException(CustomBaseException):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    description = HTTPStatus.UNPROCESSABLE_ENTITY.description
    phrase = HTTPStatus.UNPROCESSABLE_ENTITY.phrase


class DuplicateResourceException(CustomBaseException):
    status_code = HTTPStatus.CONFLICT
    description = HTTPStatus.CONFLICT.description
    phrase = HTTPStatus.CONFLICT.phrase


class ForbiddenException(CustomBaseException):
    status_code = HTTPStatus.FORBIDDEN
    description = HTTPStatus.FORBIDDEN.description
    phrase = HTTPStatus.FORBIDDEN.phrase


class NotImplementedException(CustomBaseException):
    status_code = HTTPStatus.NOT_IMPLEMENTED
    description = HTTPStatus.NOT_IMPLEMENTED.description
    phrase = HTTPStatus.NOT_IMPLEMENTED.phrase


class ServiceUnavailableException(CustomBaseException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    description = HTTPStatus.SERVICE_UNAVAILABLE.description
    phrase = HTTPStatus.SERVICE_UNAVAILABLE.phrase


class TooManyRequestsException(CustomBaseException):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    description = HTTPStatus.TOO_MANY_REQUESTS.description
    phrase = HTTPStatus.TOO_MANY_REQUESTS.phrase


class NotAllowedException(CustomBaseException):
    status_code = HTTPStatus.METHOD_NOT_ALLOWED
    description = HTTPStatus.METHOD_NOT_ALLOWED.description
    phrase = HTTPStatus.METHOD_NOT_ALLOWED.phrase
