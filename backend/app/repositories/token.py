from typing import Tuple, Union

from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.models.token import TokenDB

COLLECTION_NAME = "tokens"


def check_token_object(
    token_object: dict, get_id: bool
) -> Union[Tuple[TokenDB, str], TokenDB]:
    if token_object:
        if get_id:
            return TokenDB(**token_object), token_object.get("_id")
        return TokenDB(**token_object)

    raise StarletteHTTPException(
        status_code=HTTP_404_NOT_FOUND, detail="This token doesn't exist"
    )


async def get_token(
    conn: AsyncIOMotorClient, token: str, get_id: bool = False
) -> TokenDB:
    token_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"token": token}
    )
    return check_token_object(token_object, get_id)


async def save_token(token: TokenDB) -> TokenDB:
    conn: AsyncIOMotorClient = await get_database()
    await conn[settings.DATABASE_NAME][COLLECTION_NAME].insert_one(token.dict())
    return token
