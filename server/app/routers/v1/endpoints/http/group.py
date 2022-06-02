import asyncio
import logging

from databases import Database
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import get_current_user
from app.models.group import BaseGroup, BaseGroupCreate, BaseGroupResponse, DBGroup
from app.models.group_user import DBGroupUser
from app.models.payload import PayloadGroupUserRoleResponse
from app.models.permission import DBPermission
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.user import BaseUserTokenWrapper

router: APIRouter = APIRouter()


@router.post(
    "/create",
    response_model=BaseGroupResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="create",
    responses={
        400: {"description": "Invalid input"},
        409: {"description": "Group already exists"},
    },
)
async def create(
        group_create: BaseGroupCreate,
        id_user_token: tuple[int, BaseUserTokenWrapper] = Depends(get_current_user),
        mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseGroupResponse:
    """
    Create a new group.
    """
    async with mysql_driver.transaction():
        user_id, user_token = id_user_token

        custom_roles = [
            custom_role_permission.role
            for custom_role_permission in group_create.custom_roles
        ]

        db_group: DBGroup = await DBGroup(
            name=group_create.name, description=group_create.description
        ).save(mysql_driver)

        await DBRole.save_batch(mysql_driver, db_group.id, custom_roles)

        await DBGroupUser.save_batch(
            mysql_driver,
            db_group.id,
            [
                {
                    "user_id": user_id,
                    "role_id": (
                        await DBRole.get_role_owner_by_group(mysql_driver, db_group.id)
                    ).id,
                }
            ],
        )

        futures = [
            DBPermission.get_owner_permissions(mysql_driver),
            DBPermission.get_admin_permissions(mysql_driver),
            DBPermission.get_user_permissions(mysql_driver),
        ]
        result_futures: tuple = await asyncio.gather(*futures)
        owner_permissions, admin_permissions, user_permissions = result_futures

        roles_permissions: list[dict] = await DBRole.create_role_permission_pairs(
            mysql_driver,
            owner_permissions,
            admin_permissions,
            user_permissions,
            db_group.id,
            group_create.custom_roles,
        )

        await DBRolePermission.save_batch(mysql_driver, roles_permissions)

        return BaseGroupResponse(group=BaseGroup(**db_group.dict()))


@router.get(
    "/{group_id}",
    response_model=PayloadGroupUserRoleResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="create",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def get_by_id(
        group_id: int,
        id_user_token: tuple[int, BaseUserTokenWrapper] = Depends(get_current_user),
        mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUserRoleResponse:
    user_id: int
    user_token: BaseUserTokenWrapper
    user_id, user_token = id_user_token

    if not await DBGroupUser.is_user_in_group(mysql_driver, user_id, group_id):
        raise StarletteHTTPException(status_code=401, detail="You are not part of the group")

    return PayloadGroupUserRoleResponse(
        payload=await DBGroupUser.get_group_user_by_reflection_with_id(
            mysql_driver, "groups_id", group_id
        )
    )
