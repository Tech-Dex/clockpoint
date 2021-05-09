from typing import Tuple, Union

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.core.config import settings
from app.models.group import GroupCreate, GroupDB
from app.models.user import UserBase

COLLECTION_NAME = "groups"


def check_group_object(
    group_object: dict, get_id: bool
) -> Union[Tuple[GroupDB, ObjectId], GroupDB]:
    if group_object:
        if get_id:
            return GroupDB(**group_object), group_object.get("_id")
        return GroupDB(**group_object)

    raise StarletteHTTPException(
        status_code=HTTP_404_NOT_FOUND, detail="This group doesn't exist"
    )


async def get_group_by_id(
    conn: AsyncIOMotorClient,
    group_id: str,
    get_id: bool = False,
) -> Union[Tuple[GroupDB, ObjectId], GroupDB]:
    group_object: dict = await conn[settings.DATABASE_NAME][COLLECTION_NAME].find_one(
        {"_id": ObjectId(group_id)}
    )
    return check_group_object(group_object, get_id)


async def create_group(
    conn: AsyncIOMotorClient,
    group_create: GroupCreate,
    user_base: UserBase,
) -> Tuple[GroupDB, ObjectId]:
    group_db: GroupDB = GroupDB(**group_create.dict())
    group_db.owner = user_base
    group_object = await conn[settings.DATABASE_NAME][COLLECTION_NAME].insert_one(
        group_db.dict()
    )
    return group_db, group_object.inserted_id
