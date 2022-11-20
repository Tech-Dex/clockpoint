from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template
from pydantic.networks import EmailStr

from app.core.config import settings


async def send_email(receiver: EmailStr, subject: str, body: str):
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_SENDER
        msg["To"] = receiver
        msg.attach(MIMEText(body, "html"))
        server.starttls()
        server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
        server.send_message(msg)


async def send_register_email(receiver: EmailStr, token: str, username: str):
    try:
        with open(os.path.join(settings.EMAIL_TEMPLATES_DIR, "register.html")) as f:
            template = Template(f.read())
            body = template.render(
                project_name=settings.APP_NAME,
                username=username,
                verification_link=f"{settings.MAIL_FRONTEND_DNS}/"
                f"{settings.VERIFY_ACCOUNT_TOKEN_EXPIRE_MINUTES}?token={token}",
            )
            await send_email(receiver, "Verify your email", body)
    except IOError:
        logging.critical("Could not find register.html in email-templates")


async def send_recover_account_email(receiver: EmailStr, token: str, username: str):
    try:
        with open(os.path.join(settings.EMAIL_TEMPLATES_DIR, "recover.html")) as f:
            template = Template(f.read())
            body = template.render(
                project_name=settings.APP_NAME,
                username=username,
                contact_link=f"{settings.MAIL_FRONTEND_DNS}/{settings.MAIL_CONTACT_PATH}",
                reset_password_link=f"{settings.MAIL_FRONTEND_DNS}/"
                f"{settings.MAIL_FRONTEND_RESET_PASSWORD_PATH}"
                f"?token={token}",
            )
            await send_email(receiver, "Reset your password", body)
    except IOError:
        logging.critical("Could not find recover.html in email-templates")
