from app.exceptions import base as base_exceptions


class PermissionException(base_exceptions.ForbiddenException):
    def __init__(self, permission: str):
        super().__init__(f"Permission {permission} not granted")


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
            detail="Not allowed to assign higher or equals permissions without sufficient permissions"
        )


class NotAllowedToGenerateQRCodeEntryAndGenerateReportException(
    base_exceptions.ForbiddenException
):
    def __init__(self):
        super().__init__(
            detail="Not allowed to generate QR code entry and generate report"
        )


class PermissionNotFoundException(base_exceptions.NotFoundException):
    description = "Nothing matches the given permission"

    def __init__(self):
        super().__init__(detail="Permission not found")
