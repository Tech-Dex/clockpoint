from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    client: AsyncIOMotorClient = None


database: Database = Database()


async def get_database() -> AsyncIOMotorClient:
    return database.client
