from app.exceptions import base as base_exceptions


class DuplicateCaseScheduleException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="Session schedule already exists")
