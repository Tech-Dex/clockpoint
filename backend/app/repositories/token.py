from datetime import datetime
from typing import List, Tuple, Union

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic.networks import EmailStr
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.models.enums.token_subject import TokenSubject
from app.models.token import TokenDB, TokenUpdate

COLLECTION_NAME = "tokens"


def check_token_object(
    token_object: dict, get_id: bool
) -> Union[Tuple[TokenDB, ObjectId], TokenDB]:
    if token_object:
        if get_id:
            return TokenDB(**token_object), token_object.get("_id")
        return TokenDB(**token_object)

    raise StarletteHTTPException(
        status_code=HTTP_404_NOT_FOUND, detail="This token doesn't exist"
    )


async def fetch_async_tokens(
    tokens_object: dict, get_ids
) -> List[Union[Tuple[TokenDB, ObjectId], TokenDB]]:
    if get_ids:
        tokens_db: List[Tuple[TokenDB, ObjectId]] = []
        async for token_object in tokens_object:
            token_db: Tuple[TokenDB, ObjectId] = check_token_object(
                token_object, get_id=get_ids
            )
            tokens_db.append(token_db)
        return tokens_db

    tokens_db: List[TokenDB] = []
    async for token_object in tokens_object:
        token_db: TokenDB = check_token_object(token_object, get_id=get_ids)
        tokens_db.append(token_db)
    return tokens_db


async def get_token(
    conn: AsyncIOMotorClient, token: str, get_id: bool = False
) -> TokenDB:
    token_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"token": token}
    )
    return check_token_object(token_object, get_id)


async def get_tokens_by_subject_and_lt_datetime(
    conn: AsyncIOMotorClient,
    subject: TokenSubject,
    needle_datetime: datetime,
    get_ids: bool = False,
    used: bool = True,
) -> List[Union[Tuple[TokenDB, ObjectId], TokenDB]]:
    tokens_object: dict = conn[settings.DATABASE_NAME][COLLECTION_NAME].find(
        {
            "subject": subject,
            "expire_datetime": {"$lt": needle_datetime},
            "deleted": False,
        }
    )
    if not used:
        del tokens_object
        tokens_object: dict = conn[settings.DATABASE_NAME][COLLECTION_NAME].find(
            {
                "subject": subject,
                "expire_datetime": {"$lt": needle_datetime},
                "used_at": None,
                "deleted": False,
            }
        )
    return await fetch_async_tokens(tokens_object, get_ids)


async def get_tokens_by_email(
    conn: AsyncIOMotorClient, email: EmailStr, get_ids: bool = False
) -> List[Union[Tuple[TokenDB, ObjectId], TokenDB]]:
    tokens_object: dict = conn[settings.DATABASE_NAME][COLLECTION_NAME].find(
        {"email": email}
    )
    return await fetch_async_tokens(tokens_object, get_ids)


async def save_token(token: TokenDB) -> TokenDB:
    conn: AsyncIOMotorClient = await get_database()
    await conn[settings.DATABASE_NAME][COLLECTION_NAME].insert_one(token.dict())
    return token


async def update_token(conn: AsyncIOMotorClient, token_update: TokenUpdate) -> TokenDB:
    token_db: TokenDB
    token_db_id: str
    token_db, token_db_id = await get_token(conn, token_update.token, get_id=True)

    token_db.updated_at = datetime.utcnow()
    token_db.used_at = token_update.used_at or token_db.used_at
    if token_db.deleted is not True and token_update.deleted is True:
        token_db.deleted = token_update.deleted

    await conn[settings.DATABASE_NAME][COLLECTION_NAME].update_one(
        {"_id": ObjectId(token_db_id)}, {"$set": token_db.dict()}
    )

    return token_db
