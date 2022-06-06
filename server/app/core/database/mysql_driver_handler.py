import logging

from databases import Database

from app.core.config import settings
from app.core.database.mysql_driver import mysql_driver


async def connect_to_mysql_driver():
    logging.info("Initializing MySQL driver...")
    mysql_driver.server = Database(
        url=settings.MYSQL_URL,
        min_size=settings.MYSQL_MIN_SIZE,
        max_size=settings.MYSQL_MAX_SIZE,
    )
    await mysql_driver.server.connect()
    logging.info("MySQL driver initialized.")


async def disconnect_from_mysql_driver():
    logging.info("Closing MySQL driver...")
    await mysql_driver.server.disconnect()
    logging.info("MySQL driver closed.")
