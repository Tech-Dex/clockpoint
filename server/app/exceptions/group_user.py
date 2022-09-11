from app.exceptions import base as base_exceptions


class DuplicateUserInGroupException(base_exceptions.DuplicateResourceException):
    def __init__(self):
        super().__init__(detail="User already in group")


class UserNotInGroupException(base_exceptions.UnprocessableEntityException):
    def __init__(self):
        super().__init__(detail="User not in group")


class NoGroupsFoundException(base_exceptions.NotFoundException):
    def __init__(self):
        super().__init__(detail="No groups found")


class OwnerCannotLeaveGroupException(base_exceptions.UnprocessableEntityException):
    def __init__(self):
        super().__init__(detail="Owner cannot leave group")


class SelfAssignRoleException(base_exceptions.ForbiddenException):
    def __init__(self):
        super().__init__(detail="You cannot assign yourself a role")
