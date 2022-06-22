import logging

import redis.asyncio as redis
from app.core.config import settings
from app.core.redis.redis_driver import redis_driver


async def connect_to_redis_driver():
    logging.info("Initializing Redis driver...")
    redis_driver.server = redis.from_url(settings.REDIS_URL)
    logging.info("Redis driver initialized.")


async def disconnect_from_redis_driver():
    logging.info("Closing Redis driver...")
    await redis_driver.server.close()
    logging.info("Redis driver closed.")
