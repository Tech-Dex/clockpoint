from app.exceptions import base as base_exceptions


class DuplicateRoleInGroupException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="Role with this name already exists for this group")


class RoleNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given role"

    def __init__(self):
        super().__init__(detail="Role not found")
