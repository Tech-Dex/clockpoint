from app.exceptions import base as base_exceptions


class NotAllowedToInviteUsersInGroupException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(detail="Not allowed to invite users in group")


class NotAllowedToAssignRoleInGroupException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(detail="Not allowed to assign role in group")


class UserPermissionsAreHigherException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(
            detail="Not allowed to assign permissions to user with higher permissions"
        )


class UserPermissionsAreNotSufficientException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(
            detail="Not allowed to assign higher permissions without sufficient permissions"
        )


class PermissionNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given permission"

    def __init__(self):
        super().__init__(detail="Permission not found")
