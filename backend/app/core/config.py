import os
from binascii import hexlify
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, Formatter
from typing import Any, Optional

from databases import DatabaseURL
from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    BACKEND_CORS_ORIGINS: str = (
        '["http://localhost", "http://localhost:4200", "http://localhost:3000", '
        '"http://localhost:8080", "https://localhost", "https://localhost:4200", '
        '"https://localhost:3000", "https://localhost:8080"] '
    )
    JWT_TOKEN_PREFIX: str
    SECRET_KEY: Optional[bytes]
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 8
    )  # 60 minutes * 24 hours * 8 days = 8 days
    ACTIVATE_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 7
    )  # 60 minutes * 24 hours * 7 days = 7 days
    RECOVER_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 1
    )  # 60 minutes * 24 hours * 1 day = 1 day
    USER_INVITE_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 1
    )  # 60 minutes * 24 hours * 1 day = 1 day
    GROUP_INVITE_CO_OWNER_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 1
    )  # 60 minutes * 24 hours * 1 day = 1 day
    GROUP_INVITE_MEMBER_TOKEN_EXPIRE_MINUTES: int = (
        60 * 24 * 1
    )  # 60 minutes * 24 hours * 1 day = 1 day
    SCHEDULER_INACTIVE_USERS: int = 60 * 1  # 60 seconds * 1 minute = 1 minute
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_DB: str
    MONGODB_URL: Optional[DatabaseURL]
    DATABASE_NAME: Optional[str]
    MAX_CONNECTIONS_COUNT: str
    MIN_CONNECTIONS_COUNT: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool
    MAIL_USE_CREDENTIALS: bool
    FRONTEND_DNS: str
    FRONTEND_ACTIVATION_PATH: str
    FRONTEND_RECOVERY_PATH: str
    FRONTEND_GROUP_INVITE: str

    def __init__(self, **values: Any):
        super().__init__(**values)
        if not self.SECRET_KEY:
            self.SECRET_KEY = hexlify(os.urandom(32))
        self.MONGODB_URL = DatabaseURL(
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASS}@{self.MONGO_HOST}:"
            f"{self.MONGO_PORT}/{self.MONGO_DB}?authSource=admin"
        )
        self.DATABASE_NAME = self.MONGO_DB


settings: Settings = Settings()


class CustomFormatter(Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey: str = "\x1b[38;1m"
    green: str = "\x1b[32;1m"
    yellow: str = "\x1b[33;1m"
    red: str = "\x1b[31;1m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"
    format: str = (
        "%(levelname)s: "
        "%(asctime)s [%(threadName)s] - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        DEBUG: grey + format + reset,
        INFO: green + format + reset,
        WARNING: yellow + format + reset,
        ERROR: red + format + reset,
        CRITICAL: bold_red + format + reset,
    }

    def format(self, record) -> str:
        log_fmt: str = self.FORMATS.get(record.levelno)
        formatter: Formatter = Formatter(log_fmt)
        return formatter.format(record)
