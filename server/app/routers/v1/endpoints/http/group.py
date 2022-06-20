import asyncio
from datetime import timedelta

import numpy as np
from databases import Database
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic.networks import EmailStr
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_200_OK

from app.core.config import settings
from app.core.database.mysql_driver import get_mysql_driver
from app.core.jwt import create_token
from app.models.enums.token_subject import TokenSubject
from app.models.group import BaseGroup, DBGroup
from app.models.group_user import DBGroupUser
from app.models.permission import DBPermission
from app.models.role import DBRole
from app.models.role_permission import DBRolePermission
from app.models.token import InviteGroupToken
from app.models.user import BaseUserTokenWrapper, DBUser
from app.schemas.v1.request import BaseGroupCreateRequest, GroupInviteRequest
from app.schemas.v1.response import BaseGroupResponse, PayloadGroupUserRoleResponse
from app.services.dependencies import (
    get_current_user,
    get_current_user_and_group_allowed_to_invite,
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
    bg_tasks: BackgroundTasks,
    id_user_token_group: tuple[int, BaseUserTokenWrapper, DBGroup] = Depends(
        get_current_user_and_group_allowed_to_invite
    ),
    mysql_driver: Database = Depends(get_mysql_driver),
) -> JSONResponse:
    async with mysql_driver.transaction():
        user_id: int
        db_group: DBGroup
        user_id, _, db_group = id_user_token_group

        users_invite: list[DBUser] | None = await DBUser.get_all_in(
            mysql_driver, "email", group_invite.emails, bypass_exception=True
        )
        invitation_receivers: list[EmailStr] = list(
            np.setdiff1d(group_invite.emails, [user.email for user in users_invite])
        )

        users_ids_invite: list[int] = [user.id for user in users_invite]
        users_ids_not_in_group: list[int] = []

        if users_invite:
            users_ids_in_group: list[int] = await DBGroupUser.are_users_in_group(
                mysql_driver, users_ids_invite, db_group.id
            )
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
                    mysql_driver=mysql_driver,
                    data=InviteGroupToken(
                        user_id=user_id,
                        user_email=invitation_receiver,
                        group_id=db_group.id,
                        subject=TokenSubject.GROUP_INVITE,
                    ).dict(),
                    expires_delta=timedelta(
                        minutes=settings.INVITE_TOKEN_EXPIRE_MINUTES
                    ),
                )
            )

        bg_tasks.add_task(
            send_group_invitation, invitation_receivers, db_group.name, tokens
        )

        return JSONResponse(
            status_code=HTTP_200_OK,
            content={"emails_bypassed": user_emails_bypassed},
        )


# Add link between token GROUP_INVITE and invited email - maybe use Redis, after 48 hours this one can be deleted
# Maybe move all tokens to Redis -> read aioredis docs
# Display all invitation ( JWT ) for a user ( /see_invites )
# Join a group with the JWT if not expired.
