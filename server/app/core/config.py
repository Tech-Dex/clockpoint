import os
from binascii import hexlify
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, Formatter

from databases import DatabaseURL
from pydantic import BaseSettings
from pydantic.networks import EmailStr


class Settings(BaseSettings):
    APP_NAME: str
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:4200",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "https://localhost",
        "https://localhost:8000",
        "https://localhost:4200",
        "https://localhost:3000",
        "https://localhost:8080",
        "https://localhost:5173",
    ]

    JWT_TOKEN_PREFIX: str
    SECRET_KEY: bytes | None = None
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    VERIFY_ACCOUNT_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 3  # 3 days
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    INVITE_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 2  # 2 days
    QR_CODE_GROUP_INVITE_TOKEN_EXPIRE_MINUTES: int = 60 * 10  # 10 minutes
    QR_CODE_CLOCK_ENTRY_TOKEN_EXPIRE_MINUTES: int = 60 * 5  # 5 minutes
    DB_CLEANER_CRON_JOB_EVERY_MINUTES: int = 60 * 24 * 1  # 1 day
    CLOCK_SCHEDULER_CRON_JOB_EVERY_MINUTES: int = 60  # 1 minute
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    MYSQL_URL: DatabaseURL | None = None
    MYSQL_MIN_SIZE: int
    MYSQL_MAX_SIZE: int
    REDIS_HOST: str
    REDIS_DATA_PORT: int
    REDIS_CACHE_PORT: int
    REDIS_DATA_URL: str | None = None
    REDIS_CACHE_URL: str | None = None
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USER: str
    MAIL_PASSWORD: str
    MAIL_SENDER: EmailStr
    EMAIL_TEMPLATES_DIR: str = "app/email-templates/build"
    MAIL_FRONTEND_DNS: str
    MAIL_FRONTEND_VERIFY_ACCOUNT_PATH: str
    MAIL_FRONTEND_RESET_PASSWORD_PATH: str
    MAIL_CONTACT_PATH: str

    def __init__(self, **values: any):
        super().__init__(**values)
        if not self.SECRET_KEY:
            self.SECRET_KEY = hexlify(os.urandom(32))
        self.MYSQL_URL = DatabaseURL(
            f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:"
            f"{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
        self.REDIS_DATA_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_DATA_PORT}"
        self.REDIS_CACHE_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_CACHE_PORT}"


settings: Settings = Settings(
    _env_file=os.path.join(os.path.dirname(__file__), "../envs", ".env"),
    _env_file_encoding="utf-8",
)


class CustomFormatter(Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    blue: str = "\033[94m"
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
        DEBUG: blue + format + reset,
        INFO: green + format + reset,
        WARNING: yellow + format + reset,
        ERROR: red + format + reset,
        CRITICAL: bold_red + format + reset,
    }

    def format(self, record) -> str:
        log_fmt: str = self.FORMATS.get(record.levelno)
        formatter: Formatter = Formatter(log_fmt)
        return formatter.format(record)
