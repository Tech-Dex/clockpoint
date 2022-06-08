from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from pydantic.networks import EmailStr

from app.core.config import settings


# TODO: Maybe move to FastAPI-Email library instead of using smtplib
async def send_email(receiver: EmailStr, subject: str, body: str):
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        email_message = EmailMessage()
        email_message["Subject"] = subject
        email_message["From"] = settings.MAIL_SENDER
        email_message["To"] = receiver
        email_message.set_content(str(body), subtype="html")
        server.starttls()
        server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
        server.send_message(email_message)


async def send_group_invitation(
    receivers: list[EmailStr],
    group_name: str,
    tokens: list[str],
):
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
        return

    for receiver, token in zip(receivers, tokens):
        action_link = f"{settings.MAIL_FRONTEND_DNS}/{settings.MAIL_FRONTEND_GROUP_INVITE_PATH}?token={token}"

        button_link: Tag | NavigableString = soup.find(id="button-link").find("a")
        button_link["href"] = button_link["href"].replace(
            "{{action_link}}", action_link
        )

        fallback_link: Tag | NavigableString = soup.find(id="fallback-link").find("a")
        fallback_link["href"]: str = fallback_link["href"].replace(
            "{{action_link}}", action_link
        )
        fallback_link.string = action_link

        group_details: Tag | NavigableString = soup.find(id="group-details")
        group_details.contents[0].replace_with(
            group_details.contents[0].replace("{{group_name}}", group_name)
        )

        subject: str = (
            f"You have been invited to join {group_name} in the Clockpoint application"
        )
        asyncio.create_task(send_email(receiver, subject, str(soup)))
