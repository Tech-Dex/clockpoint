from fastapi_mail import FastMail


class Smtp:
    client: FastMail


smtp = Smtp()


async def get_smtp() -> FastMail:
    return smtp.client
