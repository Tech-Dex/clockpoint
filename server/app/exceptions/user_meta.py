from app.exceptions import base as base_exceptions


class DoesNotHavePushNotificationsException(base_exceptions.BadRequestException):
    def __init__(self):
        super().__init__(detail="User does not have push notifications enabled")
