import logging

from fastapi_mail import ConnectionConfig, FastMail

from app.core.config import settings
from app.core.smtp.smtp import smtp


async def connect_to_smtp():
    logging.info("FastMail: Start Connection...")
    smtp.client = FastMail(
        ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_TLS=settings.MAIL_TLS,
            MAIL_SSL=settings.MAIL_SSL,
            USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
        )
    )
    logging.info("FastMail: Connection Successful!")


async def close_smtp_connection():
    logging.info("FastMail: Close Connection...")
    logging.info("FastMail: Connection closed!")
