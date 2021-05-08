from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.status import HTTP_200_OK

from app.core.database.mongodb import get_database
from app.core.jwt import get_current_user
from app.models.group import GroupResponse
from app.models.user import UserTokenWrapper

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
    ...
    # TODO: A user will be able to visualize a group if he already part of it
