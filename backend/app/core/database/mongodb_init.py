import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.database.mongodb import database


async def connect_to_mongo():
    logging.info("MongoDB: Start Connection...")
    database.client = AsyncIOMotorClient(
        str(settings.MONGODB_URL),
        maxPoolSize=settings.MAX_CONNECTIONS_COUNT,
        minPoolSize=settings.MIN_CONNECTIONS_COUNT,
    )
    logging.info("MongoDB: Connection Successful!")


async def close_mongo_connection():
    logging.info("MongoDB: Close Connection...")
    database.client.close()
    logging.info("MongoDB: Connection closed!")
