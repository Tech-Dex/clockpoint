from databases import Database
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from app.core.database.mysql_driver import get_mysql_driver
from app.models.enums.roles import Roles
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.payload import PayloadGroupUserRoleResponse
from app.models.user import BaseUser

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
    # db_group, db_groups_and_roles_id = await DBGroup(
    #     name="test", description="test"
    # ).save(mysql_driver, 1)
    # return {
    #     "payload": {
    #         "group": BaseGroup(**db_group.dict()),
    #         "groups_and_roles_id": db_groups_and_roles_id,
    #     }
    # }
    # db_group = await DBGroup.get_by_name(mysql_driver, "test")
    # return await db_group.add_user(mysql_driver, group_id, 1)
    # return await db_group.remove_user(mysql_driver, 1)
    # await DBGroup.get_users_and_roles(mysql_driver)
    # db_group = await DBGroup.get_by_name(mysql_driver, "test")
    # return await db_group.make_user_admin(mysql_driver, 2)
    # db_group = await DBGroup.get_by_name(mysql_driver, "new_name")

    # db_group = await DBGroup.get_by_id(mysql_driver, 7)
    # return {"payload": [BaseUser(**user) for user in await db_group.get_users_by_role(mysql_driver, Roles.ADMIN)]}
    # return BaseGroup(**(await db_group.update(mysql_driver, name="tesst", description="dessc")).dict())
    # return {"payload": [({"user": BaseUser(**json.loads(i)['user']), "role": BaseRole(**json.loads(i)['role'])}) for rep in response for i in rep]}

    # async with mysql_driver.transaction():
    #     custom_roles = ["custom_role_1", "custom_role_2"]
    #     permissions = [
    #         {"role": custom_roles[0], "permission": "invite_user"},
    #         {"role": custom_roles[1], "permission": "generate_report"},
    #     ]
    #     user_id = 1
    #     db_group: DBGroup = await DBGroup(
    #         name="test name", description="test description"
    #     ).save(mysql_driver, DBRole.create_roles(custom_roles))
    #
    #     await DBRole.save_batch(mysql_driver, db_group.id, custom_roles)
    #
    #     await DBGroupUser.save_batch(
    #         mysql_driver,
    #         db_group.id,
    #         [
    #             {
    #                 "user_id": user_id,
    #                 "role_id": (await DBRole.get_role_owner(mysql_driver)).id,
    #             }
    #         ],
    #     )
    #
    #     await DBRolePermission.save_batch(
    #         mysql_driver,
    #         await DBRole.create_role_permission_pairs(
    #             mysql_driver, db_group.id, permissions
    #         ),
    #     )
    #
    #     return BaseGroup(**db_group.dict())

    # return PayloadGroupUserRoleResponse(
    #     payload=await DBGroupUser.get_group_user_by_reflection_with_id(
    #         mysql_driver, "groups_id", 18
    #     )
    # )

    # custom_roles = ["custom_role_1", "custom_role_2"]
    # permissions = [
    #     {"role": custom_roles[0], "permission": "invite_user"},
    #     {"role": custom_roles[1], "permission": "generate_report"},
    # ]
    # await DBRolePermission.save_batch(
    #     mysql_driver,
    #     await DBRole.create_role_permission_pairs(mysql_driver, 15, permissions),
    # )

    # return PayloadRolePermissionsResponse(
    #     payload=await DBRolePermission.get_role_permissions(mysql_driver, 67)
    # )
    #

    # return PayloadRolesPermissionResponse(
    #     payload=await DBRolePermission.get_roles_permission(mysql_driver, 4)
    # )

    db_group = await DBGroup.get_by_id(mysql_driver, 18)
    return [BaseUser(**user) for user in await DBGroupUser.get_group_users_by_role(mysql_driver, db_group.id, Roles.OWNER)]
    return 1
