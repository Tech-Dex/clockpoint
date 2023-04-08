from aredis_om.model import NotFoundError
from databases import Database
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.database.mysql_driver import get_mysql_driver
from app.core.websocket.connection_manager import get_connection_manager
from app.models.enums.event_type import EventType
from app.models.enums.notification_scope import NotificationScope
from app.models.token import RedisToken

router: APIRouter = APIRouter()


@router.post(
    "/debug",
    status_code=HTTP_200_OK,
    name="debug",
)
async def debug(mysql_driver: Database = Depends(get_mysql_driver)):
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

    # return await DBGroup.get_by_reflection(mysql_driver, "id", 18)

    # return await DBRole.get_role_owner(mysql_driver)
    # return BaseUser(**(await DBUser.get_by(mysql_driver, "id", 1)).dict())
    # return [
    #     BaseUser(**user)
    #     for user in await DBGroupUser.get_group_users_by_role(
    #         mysql_driver, db_group.id, Roles.OWNER
    #     )
    # ]

    # return await DBUser.get_by_reflection(mysql_driver, "email", "aaa@test.com")

    # db_group = DBGroup(name="test name save 5", description="test description")
    # result = await db_group.save(mysql_driver)
    # print(type(result))
    # return {"payload": result}

    # return [
    #     BaseRole(**db_role.dict())
    #     for db_role in await DBRole.get_all_by_group_id(mysql_driver, 18)
    # ]
    # db_group = await DBGroup.get_by(mysql_driver, "id", 22)
    # return BaseGroup(**db_group.dict())
    # # await db_group.update(mysql_driver, name="aaaa", description="aaaa")
    # return BaseGroup(
    #     **(
    #         await db_group.update(mysql_driver, name="tesst", description="dessc")
    #     ).dict()
    # )
    # return 1


@router.post("/")
async def test():
    await get_connection_manager().send_personal_message_with_user_id(
        {"message": "test from endpoint"},
        16,
        EventType.NOTIFICATION,
        NotificationScope.GROUP_INVITE,
    )


@router.post("/customer")
async def save_customer(customer: RedisToken):
    # We can save the model to Redis by calling `save()`:
    result = await customer.save()
    await customer.expire(10)
    return result


@router.get("/customers")
async def list_customers():
    # To retrieve this customer with its primary key, we use `Customer.get()`:
    return {"customers": [pk async for pk in await RedisToken.all_pks()]}


@router.get("/customer/{pk}")
@cache(expire=10)
async def get_customer(pk: str):
    # To retrieve this customer with its primary key, we use `Customer.get()`:
    try:
        return await RedisToken.get(pk)
    except NotFoundError:
        raise StarletteHTTPException(status_code=404, detail="Customer not found")


@router.get("/customers/{subject}")
@cache(expire=10)
async def get_customer(subject: str):
    # To retrieve this customer with its primary key, we use `Customer.get()`:
    try:
        return await RedisToken.find(RedisToken.subject == subject).all()
    except NotFoundError:
        raise StarletteHTTPException(status_code=404, detail="Customer not found")


@router.get("/exceptions")
async def test_exceptions(
    mysql_driver: any = Depends(get_mysql_driver),
):
    from app.models.user import DBUser

    r = await DBUser.get_all(mysql_driver)

    return r


# TODO: WSS push notification:
# invites - DONE
# updates - I am not sure if we need it or what kind of updates
# friend request - Not implemented yet
# messages - Not implemented yet

# TODO: Unit tests
