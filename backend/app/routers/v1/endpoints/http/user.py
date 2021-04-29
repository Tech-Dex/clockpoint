from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from app.core.jwt import get_current_user
from app.models.user import UserResponse, UserTokenWrapper

router = APIRouter()


@router.get(
    "/",
    response_model=UserResponse,
    status_code=HTTP_200_OK,
    response_model_exclude_unset=True,
)
async def current_user(
    user_current: UserTokenWrapper = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(user=user_current)
