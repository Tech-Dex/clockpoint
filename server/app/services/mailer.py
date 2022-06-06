import logging
import os
import smtplib
from email.message import EmailMessage

from bs4 import BeautifulSoup
from fastapi import BackgroundTasks
from pydantic.networks import EmailStr

from app.core.config import settings


async def send_group_invitation(
    smtp_connection: smtplib.SMTP,
    bg_task: BackgroundTasks,
    receivers: list[EmailStr],
    group_name: str,
    token: str,
) -> bool:

    try:
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "../email-templates/minify-pages/GroupInvite.html",
            ),
            "r",
        ) as file:
            html_template = file.read()
            soup = BeautifulSoup(html_template, "lxml")
    except IOError:
        logging.critical(
            "Could not find GroupInvite.html in email-templates/minify-pages"
        )
        return False

    email_message = EmailMessage()
    email_message[
        "Subject"
    ] = f"You have been invited to join {group_name} in the Clockpoint application"
    email_message["From"] = settings.MAIL_SENDER
    email_message["To"] = receivers
    email_message.set_content(str(soup))

    bg_task.add_task(smtp_connection.send_message(email_message))

    return True
