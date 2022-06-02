from databases import Database
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import get_current_user
from app.models.group import BaseGroup, BaseGroupCreate, BaseGroupResponse, DBGroup
from app.models.group_user import DBGroupUser
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.user import BaseUserTokenWrapper

router: APIRouter = APIRouter()


@router.post(
    "/create",
    response_model=BaseGroupResponse,
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

        roles_permissions: list[dict] = await DBRole.create_role_permission_pairs(
            mysql_driver, db_group.id, group_create.custom_roles
        )

        await DBRolePermission.save_batch(mysql_driver, roles_permissions)

        return BaseGroupResponse(group=BaseGroup(**db_group.dict()))
