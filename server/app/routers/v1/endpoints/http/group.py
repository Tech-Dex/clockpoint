import asyncio
from typing import Mapping

import aredis_om.model.model
import numpy as np
from databases import Database
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi_cache.decorator import cache
from pydantic.networks import EmailStr
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token, decode_token
from app.exceptions import (
    base as base_exceptions,
    group as group_exceptions,
    group_user as group_user_exceptions,
    permission as permission_exceptions,
    role as role_exceptions,
    token as token_exceptions,
    user as user_exceptions,
)
from app.models.enums.roles import Roles
from app.models.enums.token_subject import TokenSubject
from app.models.exception import CustomBaseException
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.permission import DBPermission
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import InviteGroupToken, QRCodeInviteGroupToken, RedisToken
from app.models.user import BaseUser, DBUser, UserToken
from app.schemas.v1.request import (
    BaseGroupCreateRequest,
    GroupAssignRoleRequest,
    GroupInviteRequest,
)
from app.schemas.v1.response import (
    BaseGroupIdWrapper,
    BaseGroupResponse,
    BypassedInvitesGroupsResponse,
    GenericResponse,
    GroupInviteResponse,
    InvitesGroupsResponse,
    PayloadGroupsUsersRoleResponse,
    PayloadGroupUsersRoleResponse,
    QRCodeInviteGroupResponse,
    RolePermissionsResponse,
    RolesPermissionsResponse,
)
from app.schemas.v1.wrapper import UserInGroupWithRoleAssignWrapper, UserInGroupWrapper
from app.services.dependencies import (
    fetch_user_assign_role_permission_from_token,
    fetch_user_from_token,
    fetch_user_in_group_from_token_qp_id,
    fetch_user_invite_permission_from_token_br_invite,
    fetch_user_invite_permission_from_token_qp_id,
)
from app.services.mailer import send_group_invitation

router: APIRouter = APIRouter()

base_responses = {
    400: {
        "description": base_exceptions.BadRequestException.description,
        "model": CustomBaseException,
    }
}


@router.get(
    "/",
    response_model=PayloadGroupUsersRoleResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="get a group details",
    responses={
        **base_responses,
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def get_by_id(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_id),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUsersRoleResponse:
    return PayloadGroupUsersRoleResponse.prepare_response(
        await DBGroupUser.get_group_user_by_reflection_with_id(
            mysql_driver, "groups_id", user_in_group.group.id
        )
    )


@router.post(
    "/create",
    response_model=BaseGroupResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="create",
    responses={
        **base_responses,
        404: {
            "description": base_exceptions.NotFoundException.description,
            "model": CustomBaseException,
        },
        409: {
            "description": base_exceptions.DuplicateResourceException.description,
            "model": CustomBaseException,
        },
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

        for custom_role_permission in group_create.custom_roles:
            custom_role_permission.role = custom_role_permission.role.lower()

        group: DBGroup = await DBGroup(
            name=group_create.name, description=group_create.description
        ).save(mysql_driver)

        await DBRole.save_batch(
            mysql_driver,
            group.id,
            custom_roles,
            exc=role_exceptions.DuplicateRoleInGroupException(),
        )

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
            exc=group_user_exceptions.DuplicateUserInGroupException(),
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

        return BaseGroupResponse(group=BaseGroupIdWrapper(**group.dict()))


@router.get(
    "/my_groups",
    response_model_exclude_unset=True,
    response_model=PayloadGroupsUsersRoleResponse,
    status_code=HTTP_200_OK,
    name="get all groups of a user",
    responses={
        **base_responses,
        404: {
            "description": group_user_exceptions.NoGroupsFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def get_user_groups(
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupsUsersRoleResponse:
    groups: list[DBGroupUser] = await DBGroupUser.get_all_in(
        mysql_driver,
        "users_id",
        [user_token.id],
        exc=group_user_exceptions.NoGroupsFoundException(),
    )

    groups_user_role = await DBGroupUser.get_groups_user_by_reflection_with_ids(
        mysql_driver, "groups_id", [group.groups_id for group in groups]
    )
    payload = []

    for k, v in groups_user_role.items():
        payload.append(PayloadGroupUsersRoleResponse.prepare_response(v))

    return PayloadGroupsUsersRoleResponse(payload=payload)


@router.post(
    "/invite",
    response_model=BypassedInvitesGroupsResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="invite",
    responses={
        **base_responses,
        403: {
            "description": permission_exceptions.NotAllowedToInviteUsersInGroupException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def invite(
    group_invite: GroupInviteRequest,
    bg_tasks: BackgroundTasks,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_invite_permission_from_token_br_invite
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> BypassedInvitesGroupsResponse:
    async with mysql_driver.transaction():
        users_invite: list[DBUser] = await DBUser.get_all_in(
            mysql_driver, "email", group_invite.emails, bypass_exc=True
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

        tasks = []
        for invitation_receiver in invitation_receivers:
            tasks.append(
                create_token(
                    data=InviteGroupToken(
                        users_id=user_in_group.user_token.id,
                        invite_user_email=invitation_receiver,
                        groups_id=user_in_group.group.id,
                        subject=TokenSubject.GROUP_INVITE,
                    ).dict(),
                    expire=settings.INVITE_TOKEN_EXPIRE_MINUTES,
                )
            )

        tokens = await asyncio.gather(*tasks)

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
        **base_responses,
        404: {
            "description": base_exceptions.NotFoundException.description,
            "model": CustomBaseException,
        },
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
        raise token_exceptions.NotFoundInviteTokenException()

    groups: list[DBGroup] = await DBGroup.get_all_in(
        mysql_driver,
        "id",
        [redis_token.groups_id for redis_token in redis_tokens],
        exc=group_exceptions.GroupNotFoundException(),
    )

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
        **base_responses,
        403: {
            "description": token_exceptions.InviteTokenNotAssociatedWithUserException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": base_exceptions.NotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def join(
    invite_token: str,
    user_token: UserToken = Depends(fetch_user_from_token),
    mysql_driver: Database = Depends(get_mysql_driver),
):
    async with mysql_driver.transaction():
        if not invite_token:
            raise token_exceptions.MissingTokenException()

        try:
            redis_token: RedisToken = await RedisToken.find(
                RedisToken.token == invite_token
            ).first()
        except aredis_om.model.model.NotFoundError:
            raise token_exceptions.NotFoundInviteTokenException()

        if not redis_token:
            raise token_exceptions.NotFoundInviteTokenException()

        if (
            redis_token.invite_user_email
            and redis_token.invite_user_email != user_token.email
        ):
            raise token_exceptions.InviteTokenNotAssociatedWithUserException()

        decode_token(invite_token)

        if await DBGroupUser.is_user_in_group(
            mysql_driver, user_token.id, redis_token.groups_id, bypass_exc=True
        ):
            raise group_user_exceptions.DuplicateUserInGroupException()

        group: DBGroup = await DBGroup.get_by(
            mysql_driver,
            "id",
            redis_token.groups_id,
            exc=group_exceptions.GroupNotFoundException(),
        )

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

        return BaseGroupResponse(group=BaseGroupIdWrapper(**group.dict()))


@router.put(
    "/leave",
    response_model_exclude_unset=True,
    response_model=GenericResponse,
    status_code=HTTP_200_OK,
    name="leave",
    responses={
        **base_responses,
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
    },
)
async def leave(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_id),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> GenericResponse:
    async with mysql_driver.transaction():
        owners: list[Mapping] = await DBGroupUser.get_group_users_by_role(
            mysql_driver, user_in_group.group.id, Roles.OWNER
        )
        if user_in_group.user_token.id in [user["id"] for user in owners]:
            raise group_user_exceptions.OwnerCannotLeaveGroupException()

        await user_in_group.group_user.remove_entry(mysql_driver)

        return GenericResponse(message="You have left the group")


@router.get(
    "/roles",
    response_model_exclude_unset=True,
    response_model=RolesPermissionsResponse,
    status_code=HTTP_200_OK,
    name="get group roles",
    responses={
        **base_responses,
        404: {
            "description": base_exceptions.NotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": base_exceptions.UnprocessableEntityException.description,
            "model": CustomBaseException,
        },
    },
)
async def roles(
    user_in_group: UserInGroupWrapper = Depends(fetch_user_in_group_from_token_qp_id),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> RolesPermissionsResponse:
    group_roles: list[DBRole] = await DBRole.get_all_in(
        mysql_driver,
        "groups_id",
        [user_in_group.group.id],
        exc=role_exceptions.RoleNotFoundException(),
    )

    return RolesPermissionsResponse(
        roles_permissions=[
            RolePermissionsResponse(
                role=role_permissions.role.role,
                permissions=[
                    permission.permission for permission in role_permissions.permissions
                ],
            )
            for role_permissions in (
                await DBRolePermission.get_roles_permissions(
                    mysql_driver, [group_role.id for group_role in group_roles]
                )
            ).roles_permissions
        ]
    )


@router.post(
    "/role",
    response_model_exclude_unset=True,
    response_model=PayloadGroupUsersRoleResponse,
    status_code=HTTP_200_OK,
    name="assign a role to a user",
    responses={
        **base_responses,
        403: {
            "description": base_exceptions.ForbiddenException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": base_exceptions.NotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": base_exceptions.UnprocessableEntityException.description,
            "model": CustomBaseException,
        },
    },
)
async def assign_role(
    group_assign_role: GroupAssignRoleRequest,
    user_in_group_role_assign: UserInGroupWithRoleAssignWrapper = Depends(
        fetch_user_assign_role_permission_from_token
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> PayloadGroupUsersRoleResponse:
    async with mysql_driver.transaction():
        user_to_upgrade: DBUser = await DBUser.get_by(
            mysql_driver,
            "username",
            group_assign_role.username,
            exc=user_exceptions.UserNotFoundException(),
        )

        group_user_to_upgrade: DBGroupUser = await DBGroupUser.is_user_in_group(
            mysql_driver,
            user_to_upgrade.id,
            user_in_group_role_assign.group.id,
            exc=group_user_exceptions.UserNotInGroupException(),
        )

        group_user_to_upgrade.roles_id = user_in_group_role_assign.role_assign.id

        await group_user_to_upgrade.update(mysql_driver)

        return PayloadGroupUsersRoleResponse.prepare_response(
            await DBGroupUser.get_group_user_by_reflection_with_id(
                mysql_driver, "groups_id", user_in_group_role_assign.group.id
            )
        )


@router.post(
    "/{group_id}/qr/invite",
    response_model=QRCodeInviteGroupResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    name="invite by qr code",
    responses={
        **base_responses,
        403: {
            "description": permission_exceptions.NotAllowedToInviteUsersInGroupException.description,
            "model": CustomBaseException,
        },
        404: {
            "description": group_exceptions.GroupNotFoundException.description,
            "model": CustomBaseException,
        },
        422: {
            "description": group_user_exceptions.UserNotInGroupException.description,
            "model": CustomBaseException,
        },
    },
)
async def qr_code_invite(
    group_id: int,
    user_in_group: UserInGroupWrapper = Depends(
        fetch_user_invite_permission_from_token_qp_id
    ),
) -> QRCodeInviteGroupResponse:
    token: str = await create_token(
        data=QRCodeInviteGroupToken(
            users_id=user_in_group.user_token.id,
            groups_id=group_id,
            subject=TokenSubject.QR_CODE_GROUP_INVITE,
        ).dict(),
        expire=settings.QR_CODE_INVITE_TOKEN_EXPIRE_MINUTES,
    )

    return QRCodeInviteGroupResponse(
        token=token, group=BaseGroupIdWrapper(**user_in_group.group.dict())
    )
