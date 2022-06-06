from __future__ import annotations

import logging
import smtplib

from app.core.config import settings
from app.core.mailer.mailer_driver import mailer


async def connect_to_mailer():
    logging.info("Initializing SMTP driver...")
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
        mailer.client = server
    logging.info("SMTP driver initialized.")


async def disconnect_from_mailer():
    logging.info("Closing SMTP driver...")
    try:
        mailer.server.quit()
    except AttributeError:
        pass
    logging.info("MySQL driver closed.")
