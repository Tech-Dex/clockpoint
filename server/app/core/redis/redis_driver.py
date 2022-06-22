import redis.asyncio as redis

class RedisDriver:
    server: redis.Redis = None


redis_driver: RedisDriver = RedisDriver()


async def get_redis_driver() -> redis.Redis:
    return redis_driver.server
