import asyncio
from datetime import timedelta

from databases import Database
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.models.enums.token_subject import TokenSubject
from app.models.group import (
    BaseGroup,
    BaseGroupCreate,
    BaseGroupResponse,
    DBGroup,
    GroupInviteRequest,
)
from app.models.group_user import DBGroupUser
from app.models.payload import PayloadGroupUserRoleResponse
from app.models.permission import DBPermission
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import InviteGroupTokenPayload
from app.models.user import BaseUserTokenWrapper, DBUser
from app.services.dependencies import (
    get_current_user,
    get_current_user_and_group_allowed_to_invite,
)

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
    "/",
    response_model=PayloadGroupUserRoleResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="create",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def get_by_id(
    name: str,
    id_user_token: tuple[int, BaseUserTokenWrapper] = Depends(get_current_user),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUserRoleResponse:
    user_id: int
    user_id, _ = id_user_token
    db_group: DBGroup = await DBGroup.get_by(mysql_driver, "name", name)

    if not await DBGroupUser.is_user_in_group(mysql_driver, user_id, db_group.id):
        raise StarletteHTTPException(
            status_code=401, detail="You are not part of the group"
        )

    return PayloadGroupUserRoleResponse(
        payload=await DBGroupUser.get_group_user_by_reflection_with_id(
            mysql_driver, "groups_id", db_group.id
        )
    )


@router.post(
    "/invite",
    # response_model=JSONResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="invite",
    responses={
        400: {"description": "Invalid input"},
        409: {"description": "User already invited"},
    },
)
async def invite(
    group_invite: GroupInviteRequest,
    id_user_token_group: tuple[int, BaseUserTokenWrapper, DBGroup] = Depends(
        get_current_user_and_group_allowed_to_invite
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> JSONResponse:
    async with mysql_driver.transaction():
        user_id: int
        db_group: DBGroup
        user_id, _, db_group = id_user_token_group

        if user_invite := await DBUser.get_by(
            mysql_driver, "email", group_invite.email, bypass_exception=True
        ):
            if await DBGroupUser.is_user_in_group(
                mysql_driver, user_invite.id, db_group.id
            ):
                raise StarletteHTTPException(
                    status_code=409, detail="User already in group"
                )

        token: str = await create_token(
            data=InviteGroupTokenPayload(
                user_id=user_id,
                user_email=group_invite.email,
                group_id=db_group.id,
                subject=TokenSubject.INVITE,
            ).dict(),
            expires_delta=timedelta(minutes=settings.INVITE_TOKEN_EXPIRE_MINUTES),
        )

        # TODO: Send email with token
        return JSONResponse(
            status_code=HTTP_200_OK,
            content={"token": token},
        )


# TODO: Add option to add user to group if the inviter has permission, can't generate JWT if no permission
# Do it with JWT, generate a JWT with a new subject GROUP_INVITE
# Display all invitation ( JWT ) for a user ( /see_invites )
# Join a group with the JWT if not expired.
