import asyncio
from typing import Mapping

import numpy as np
from databases import Database
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi_cache.decorator import cache
from pydantic.networks import EmailStr
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token, decode_token
from app.models.enums.roles import Roles
from app.models.enums.token_subject import TokenSubject
from app.models.group import BaseGroup, DBGroup
from app.models.group_user import DBGroupUser
from app.models.permission import DBPermission
from app.models.role import BaseRole, DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import InviteGroupToken, RedisToken
from app.models.user import BaseUser, DBUser, UserToken
from app.schemas.v1.request import (
    BaseGroupCreateRequest,
    GroupAssignRoleRequest,
    GroupInviteRequest,
)
from app.schemas.v1.response import (
    BaseGroupResponse,
    BypassedInvitesGroupsResponse,
    GenericResponse,
    GroupInviteResponse,
    GroupRolesResponse,
    InvitesGroupsResponse,
    PayloadGroupUserRoleResponse,
)
from app.schemas.v1.wrapper import UserInGroupRoleWrapper, UserInGroupWrapper
from app.services.dependencies import (
    fetch_user_assign_role_permission_from_token,
    fetch_user_from_token,
    fetch_user_in_group_from_token_qp_name,
    fetch_user_invite_permission_from_token,
)
from app.services.mailer import send_group_invitation

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
    group_create: BaseGroupCreateRequest,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BaseGroupResponse:
    """
    Create a new group.
    """
    async with mysql_driver.transaction():
        custom_roles = [
            custom_role_permission.role.lower()
            for custom_role_permission in group_create.custom_roles
        ]

        group: DBGroup = await DBGroup(
            name=group_create.name, description=group_create.description
        ).save(mysql_driver)

        await DBRole.save_batch(mysql_driver, group.id, custom_roles)

        await DBGroupUser.save_batch(
            mysql_driver,
            group.id,
            [
                {
                    "users_id": user_token.id,
                    "roles_id": (
                        await DBRole.get_role_owner_by_group(mysql_driver, group.id)
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
            group.id,
            group_create.custom_roles,
        )

        await DBRolePermission.save_batch(mysql_driver, roles_permissions)

        return BaseGroupResponse(group=BaseGroup(**group.dict()))


@router.get(
    "/",
    response_model=PayloadGroupUserRoleResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="get a group details",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def get_by_name(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_name),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUserRoleResponse:
    return PayloadGroupUserRoleResponse(
        payload=await DBGroupUser.get_group_user_by_reflection_with_id(
            mysql_driver, "groups_id", user_in_group.group.id
        )
    )


@router.post(
    "/invite",
    response_model=BypassedInvitesGroupsResponse,
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
    bg_tasks: BackgroundTasks,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_invite_permission_from_token
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BypassedInvitesGroupsResponse:
    async with mysql_driver.transaction():
        users_invite: list[DBUser] | None = await DBUser.get_all_in(
            mysql_driver, "email", group_invite.emails, bypass_exception=True
        )
        invitation_receivers: list[EmailStr] = []
        users_ids_invite: list[int] = [user.id for user in users_invite]
        users_ids_not_in_group: list[int] = []

        if users_invite:
            users_ids_in_group: list[int] = [
                user_in_group.id
                for user_in_group in await DBGroupUser.are_users_in_group(
                    mysql_driver,
                    users_ids_invite,
                    user_in_group.group.id,
                )
            ]

            users_ids_not_in_group = list(
                np.setdiff1d(users_ids_invite, users_ids_in_group)
            )

        for user_invite in users_invite:
            if user_invite.id in users_ids_not_in_group:
                invitation_receivers.append(user_invite.email)

        user_emails_bypassed: list[EmailStr] = list(
            np.setdiff1d(group_invite.emails, invitation_receivers)
        )

        # TODO: When encode/databases fixes asyncio.gather(*functions) use it below
        tokens = []
        for invitation_receiver in invitation_receivers:
            tokens.append(
                await create_token(
                    data=InviteGroupToken(
                        users_id=user_in_group.user_token.id,
                        invite_user_email=invitation_receiver,
                        groups_id=user_in_group.group.id,
                        subject=TokenSubject.GROUP_INVITE,
                    ).dict(),
                    expire=settings.INVITE_TOKEN_EXPIRE_MINUTES,
                )
            )

        bg_tasks.add_task(
            send_group_invitation,
            invitation_receivers,
            user_in_group.group.name,
            tokens,
        )

        return BypassedInvitesGroupsResponse(bypassed_invites=user_emails_bypassed)


@router.get(
    "/invites",
    response_model_exclude_unset=True,
    response_model=InvitesGroupsResponse,
    status_code=HTTP_200_OK,
    name="user invites",
    responses={
        400: {"description": "Invalid input"},
    },
)
@cache(expire=300)
async def get_invites(
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> InvitesGroupsResponse:

    user: BaseUser = BaseUser(**user_token.dict())

    redis_tokens: list[RedisToken] = await RedisToken.find(
        RedisToken.invite_user_email == user.email
    ).all()

    if not redis_tokens:
        raise StarletteHTTPException(status_code=404, detail="No invites found")

    groups: list[DBGroup] | None = await DBGroup.get_all_in(
        mysql_driver, "id", [redis_token.groups_id for redis_token in redis_tokens]
    )

    if not groups:
        raise StarletteHTTPException(status_code=404, detail="No groups found")

    invites: list[GroupInviteResponse] = []
    for db_group in groups:
        for redis_token in redis_tokens:
            if redis_token.groups_id == db_group.id:
                invites.append(
                    GroupInviteResponse(**db_group.dict(), token=redis_token.token)
                )
                break

    return InvitesGroupsResponse(invites=invites)


@cache(expire=300)
@router.post(
    "/join",
    response_model_exclude_unset=True,
    response_model=BaseGroupResponse,
    status_code=HTTP_200_OK,
    name="join",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def join(
    invite_token: str,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
):
    if not invite_token:
        raise StarletteHTTPException(status_code=400, detail="Invalid input")

    redis_token: RedisToken = await RedisToken.find(
        RedisToken.token == invite_token
    ).first()
    if not redis_token:
        raise StarletteHTTPException(status_code=404, detail="No token found")

    if redis_token.invite_user_email != user_token.email:
        raise StarletteHTTPException(
            status_code=403, detail="This token is not associated with you"
        )

    decode_token(invite_token)

    if await DBGroupUser.is_user_in_group(
        mysql_driver, user_token.id, redis_token.groups_id, bypass_exception=True
    ):
        raise StarletteHTTPException(
            status_code=403, detail="You are already in this group"
        )

    group: DBGroup = await DBGroup.get_by(mysql_driver, "id", redis_token.groups_id)
    if not group:
        raise StarletteHTTPException(status_code=404, detail="No group found")

    await DBGroupUser.save_batch(
        mysql_driver,
        redis_token.groups_id,
        [
            {
                "users_id": user_token.id,
                "roles_id": (
                    await DBRole.get_role_user_by_group(
                        mysql_driver, redis_token.groups_id
                    )
                ).id,
            }
        ],
    )

    await RedisToken.delete(redis_token.pk)

    return BaseGroupResponse(group=BaseGroup(**group.dict()))


@router.put(
    "/leave",
    response_model_exclude_unset=True,
    response_model=GenericResponse,
    status_code=HTTP_200_OK,
    name="leave",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def leave(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_name),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> GenericResponse:
    async with mysql_driver.transaction():
        owners: list[Mapping] = await DBGroupUser.get_group_users_by_role(
            mysql_driver, user_in_group.group.id, Roles.OWNER
        )
        if user_in_group.user_token.id in [user["id"] for user in owners]:
            raise StarletteHTTPException(
                status_code=403, detail="You can't leave a group you own"
            )

        await user_in_group.group_user.remove_entry(mysql_driver)

        return GenericResponse(message="You have left the group")


@router.get(
    "/roles",
    response_model_exclude_unset=True,
    response_model=GroupRolesResponse,
    status_code=HTTP_200_OK,
    name="get group roles",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def roles(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_name),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> GroupRolesResponse:
    async with mysql_driver.transaction():
        # TODO: Add in Role_permissions a query to fetch all roles with permissions for a group
        return GroupRolesResponse(
            roles=[
                BaseRole(**role.dict())
                for role in (
                    await DBRole.get_all_by_group_id(
                        mysql_driver, user_in_group.group.id
                    )
                )
            ]
        )


@router.post(
    "/role",
    response_model_exclude_unset=True,
    response_model=PayloadGroupUserRoleResponse,
    status_code=HTTP_200_OK,
    name="assign a role to a user",
    responses={
        400: {"description": "Invalid input"},
    },
)
async def assign_role(
    group_assign_role: GroupAssignRoleRequest,
    user_in_group_role: UserInGroupRoleWrapper = Depends(
        fetch_user_assign_role_permission_from_token
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUserRoleResponse:
    #TODO: Try to reduce the number of queries to DB, you have like 12 queries here
    async with mysql_driver.transaction():
        role: DBRole = user_in_group_role.role
        if not role:
            raise StarletteHTTPException(status_code=404, detail="No role found")

        user_to_upgrade: DBUser = await DBUser.get_by(
            mysql_driver, "username", group_assign_role.username
        )
        if not user_to_upgrade:
            raise StarletteHTTPException(status_code=404, detail="No user found")

        group_user_to_upgrade: DBGroupUser = await DBGroupUser.is_user_in_group(
            mysql_driver, user_to_upgrade.id, user_in_group_role.group.id
        )

        if not group_user_to_upgrade:
            raise StarletteHTTPException(
                status_code=403, detail="User is not in this group"
            )

        permission_to_invite = await DBPermission.get_by(
            mysql_driver, "permission", "invite_user"
        )

        roles_with_permission_to_invite = await DBRolePermission.get_roles_permission(
            mysql_driver, permission_to_invite.id
        )
        if user_in_group_role.group_user.roles_id not in [
            role_with_permission_to_invite["role"]["id"]
            for role_with_permission_to_invite in roles_with_permission_to_invite[
                "roles"
            ]
        ]:
            raise StarletteHTTPException(
                status_code=403, detail="You don't have permission to invite users"
            )

        group_user_to_upgrade.roles_id = role.id

        await group_user_to_upgrade.update(mysql_driver)

        return PayloadGroupUserRoleResponse(
            payload=await DBGroupUser.get_group_user_by_reflection_with_id(
                mysql_driver, "groups_id", user_in_group_role.group.id
            )
        )