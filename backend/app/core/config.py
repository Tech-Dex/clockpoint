import logging

from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    BACKEND_CORS_ORIGINS = (
        '["http://localhost", "http://localhost:4200", "http://localhost:3000", '
        '"http://localhost:8080", "https://localhost", "https://localhost:4200", '
        '"https://localhost:3000", "https://localhost:8080"] '
    )


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;1m"
    green = "\x1b[32;1m"
    yellow = "\x1b[33;1m"
    red = "\x1b[31;1m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(levelname)s: %(name)s - %(asctime)s [%(threadName)s] - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
