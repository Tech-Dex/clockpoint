from databases import Database
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from app.core.database.mysql_driver import get_mysql_driver
from app.models.group import BaseGroup, DBGroup

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
    # return BaseGroup(**(await DBGroup.get_by_id(mysql_driver, 1)).dict())
    # return BaseGroup(**(await DBGroup.get_by_name(mysql_driver, "test")).dict())
    # return BaseRole(**(await DBRole.get_role_owner(mysql_driver)).dict())
    # return [BaseRole(**db_role.dict()) for db_role in await DBRole.get_all(mysql_driver)]
    db_group, db_groups_and_roles_id = await DBGroup(
        name="test", description="test"
    ).save(mysql_driver, 1)
    return {
        "payload": {
            "group": BaseGroup(**db_group.dict()),
            "groups_and_roles_id": db_groups_and_roles_id,
        }
    }
    # group_id, db_group = await DBGroup.get_by_name(mysql_driver, "test")
    # return await db_group.add_user(mysql_driver, group_id, 1)
    # return await db_group.remove_user(mysql_driver, 1)
    await DBGroup.get_users_and_roles(mysql_driver)

    # return {"payload": [({"user": BaseUser(**json.loads(i)['user']), "role": BaseRole(**json.loads(i)['role'])}) for rep in response for i in rep]}
    return 1
