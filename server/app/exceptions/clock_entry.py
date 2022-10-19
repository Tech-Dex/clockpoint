from app.exceptions import base as base_exceptions


class SelfClockEntryException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="You cannot clock yourself")


class UserAlreadyClockedInException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="User is already clocked in")


class UserAlreadyClockedOutException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="User is already clocked out")


class ClockOutWithoutClockInException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="User cannot clock out without clocking in")