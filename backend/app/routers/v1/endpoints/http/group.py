from bson.objectid import ObjectId
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from app.core.database.mongodb import get_database
from app.core.jwt import get_current_user
from app.models.group import GroupCreate, GroupDB, GroupIdWrapper, GroupResponse
from app.models.user import UserBase, UserTokenWrapper
from app.repositories.group import create_group, get_group_by_id

router = APIRouter()


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def group_by_id(
    group_id: str,
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    group_db: GroupDB = await get_group_by_id(conn, group_id)
    if group_db.user_in_group(UserBase(**user_current.dict())):
        return GroupResponse(group=GroupIdWrapper(**group_db.dict(), id=group_id))

    raise StarletteHTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="User is not in the group"
    )


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def create(
    group_create: GroupCreate = Body(..., embed=True),
    user_current: UserTokenWrapper = Depends(get_current_user),
    conn: AsyncIOMotorClient = Depends(get_database),
) -> GroupResponse:
    async with await conn.start_session() as session, session.start_transaction():
        group_db: GroupDB
        group_db_id: ObjectId
        group_db, group_db_id = await create_group(
            conn, group_create, UserBase(**user_current.dict())
        )
        return GroupResponse(
            group=GroupIdWrapper(**group_db.dict(), id=str(group_db_id))
        )
