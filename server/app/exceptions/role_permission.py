from app.exceptions import base as base_exceptions


class DuplicateRolePermissionException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="Role permission already exists")
