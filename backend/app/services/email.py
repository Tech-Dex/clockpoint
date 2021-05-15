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
    fallback_link["href"]: str = fallback_link["href"].replace(
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


async def background_send_recovery_email(
    smtp_conn: FastMail,
    background_tasks: BackgroundTasks,
    email: EmailStr,
    action_link: str,
    os: str,
    browser: str,
):
    with open("email-templates/recovery_account.html") as html_file:
        text: AnyStr = html_file.read()
        soup: BeautifulSoup = BeautifulSoup(text, "lxml")

    button_link: Union[Tag, NavigableString] = soup.find(id="button-link").find("a")
    button_link["href"] = button_link["href"].replace("{{action_link}}", action_link)

    fallback_link: Union[Tag, NavigableString] = soup.find(id="fallback-link").find("a")
    fallback_link["href"]: str = fallback_link["href"].replace(
        "{{action_link}}", action_link
    )
    fallback_link.string = action_link

    security_details: Union[Tag, NavigableString] = soup.find(id="security-details")
    security_details.contents[0].replace_with(
        security_details.contents[0]
        .replace("{{operating_system}}", os)
        .replace("{{browser_name}}", browser)
    )

    message_schema: MessageSchema = MessageSchema(
        subject="Clockpoint Account Recovery",
        recipients=[email],
        body=str(soup),
        subtype="html",
    )
    background_tasks.add_task(smtp_conn.send_message, message_schema)


async def background_send_user_invite_email(
    smtp_conn: FastMail,
    background_tasks: BackgroundTasks,
    email: EmailStr,
    action_link: str,
):
    with open("email-templates/user_invite.html") as html_file:
        text: AnyStr = html_file.read()
        soup: BeautifulSoup = BeautifulSoup(text, "lxml")

    button_link: Union[Tag, NavigableString] = soup.find(id="button-link").find("a")
    button_link["href"] = button_link["href"].replace("{{action_link}}", action_link)

    fallback_link: Union[Tag, NavigableString] = soup.find(id="fallback-link").find("a")
    fallback_link["href"]: str = fallback_link["href"].replace(
        "{{action_link}}", action_link
    )
    fallback_link.string = action_link

    message_schema: MessageSchema = MessageSchema(
        subject="Clockpoint Invitation",
        recipients=[email],
        body=str(soup),
        subtype="html",
    )
    background_tasks.add_task(smtp_conn.send_message, message_schema)


async def background_send_group_invite_email(
    smtp_conn: FastMail,
    background_tasks: BackgroundTasks,
    email: EmailStr,
    action_link: str,
    group_name: str,
):
    with open("email-templates/group_invite.html") as html_file:
        text: AnyStr = html_file.read()
        soup: BeautifulSoup = BeautifulSoup(text, "lxml")

    button_link: Union[Tag, NavigableString] = soup.find(id="button-link").find("a")
    button_link["href"] = button_link["href"].replace("{{action_link}}", action_link)

    fallback_link: Union[Tag, NavigableString] = soup.find(id="fallback-link").find("a")
    fallback_link["href"]: str = fallback_link["href"].replace(
        "{{action_link}}", action_link
    )
    fallback_link.string = action_link

    group_details: Union[Tag, NavigableString] = soup.find(id="group-details")
    group_details.contents[0].replace_with(
        group_details.contents[0].replace("{{group_name}}", group_name)
    )

    message_schema: MessageSchema = MessageSchema(
        subject="Clockpoint Group Invite",
        recipients=[email],
        body=str(soup),
        subtype="html",
    )
    background_tasks.add_task(smtp_conn.send_message, message_schema)
