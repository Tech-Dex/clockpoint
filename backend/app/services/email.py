from typing import AnyStr, Union

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema
from pydantic.networks import EmailStr


async def background_send_new_account_email(
    smtp_conn: FastMail,
    background_tasks: BackgroundTasks,
    email: EmailStr,
    action_link: str,
):
    with open("email-templates/new_account.html") as html_file:
        text: AnyStr = html_file.read()
        soup: BeautifulSoup = BeautifulSoup(text, "lxml")

    button_link: Union[Tag, NavigableString] = soup.find(id="button-link").find("a")
    button_link["href"] = button_link["href"].replace("{{action_link}}", action_link)

    fallback_link: Union[Tag, NavigableString] = soup.find(id="fallback-link").find("a")
    fallback_link["href"] = fallback_link["href"].replace(
        "{{action_link}}", action_link
    )
    fallback_link.string = action_link

    message_schema: MessageSchema = MessageSchema(
        subject="Welcome to Clockpoint",
        recipients=[email],
        body=str(soup),
        subtype="html",
    )
    background_tasks.add_task(smtp_conn.send_message, message_schema)
