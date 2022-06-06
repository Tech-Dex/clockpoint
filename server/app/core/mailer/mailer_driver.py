from __future__ import annotations

import smtplib


class Mailer:
    server: smtplib.SMTP


mailer: Mailer = Mailer()


async def get_mailer() -> smtplib.SMTP:
    return mailer.server
