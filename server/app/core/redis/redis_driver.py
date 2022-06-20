from aioredis import Redis


class RedisDriver:
    server: Redis = None


redis_driver: RedisDriver = RedisDriver()


async def get_redis_driver() -> Redis:
    return redis_driver.server
