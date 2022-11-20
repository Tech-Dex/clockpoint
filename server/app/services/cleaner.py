import logging

from databases import Database

from app.core.database.mysql_driver import get_mysql_driver
from app.models.user import DBUser


async def remove_inactive_users() -> None:
    logging.info("Remove inactive users")
    mysql_driver: Database = await get_mysql_driver()
    await DBUser.remove_inactive_users(mysql_driver)
