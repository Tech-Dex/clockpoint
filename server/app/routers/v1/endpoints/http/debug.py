from databases import Database
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from app.core.database.mysql_driver import get_mysql_driver
from app.models.group import DBGroup

router: APIRouter = APIRouter()


@router.post(
    "/debug",
    status_code=HTTP_200_OK,
    name="debug",
)
async def debug(mysql_driver: Database = Depends(get_mysql_driver)) -> any:
    """
    Debug controller
    """

    # return BaseRole(**(await DBRole.get_role_owner(mysql_driver)).dict())
    # return [BaseRole(**db_role.dict()) for db_role in await DBRole.get_all(mysql_driver)]
    # return await DBGroup(name="test", description="test").save(mysql_driver, 1)
    # group_id, db_group = await DBGroup.get_by_name(mysql_driver, "test")
    # return await db_group.add_user(mysql_driver, group_id, 1)
    # return await db_group.remove_user(mysql_driver, group_id, 1)
    # return await DBGroup.get_users_and_roles(mysql_driver, 1)