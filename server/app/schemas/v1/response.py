from __future__ import annotations

from datetime import datetime, time

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.enums.clock_entry_type import ClockEntryType
from app.models.group import BaseGroup
from app.models.permission import BasePermissionResponse
from app.models.role import BaseRole, BaseRoleResponse
from app.models.user import BaseUser


class GenericResponse(ConfigModel):
    message: str


class WebsocketResponse(ConfigModel):
    scope: str
    payload: dict


class UserTokenResponse(BaseUser):
    token: str | None = None


class BaseUserResponse(ConfigModel):
    user: UserTokenResponse


class BaseGroupIdWrapper(BaseGroup):
    id: int


class BaseGroupResponse(ConfigModel):
    group: BaseGroupIdWrapper


class PayloadGroupUserRoleWrapper(
    BaseUserResponse, BaseGroupResponse, BaseRoleResponse
):
    pass


class PayloadRolePermissionsWrapper(BaseRoleResponse):
    permissions: list[BasePermissionResponse]


class PayloadRolesPermissionWrapper(BasePermissionResponse):
    roles: list[BaseRoleResponse]


class PayloadGroupUserRoleResponse(ConfigModel):
    payload: list[PayloadGroupUserRoleWrapper]


class PayloadUserRoleResponse(ConfigModel):
    user: BaseUser
    role: BaseRole


class PayloadGroupUsersRoleResponse(ConfigModel):
    group: BaseGroupIdWrapper
    users_role: list[PayloadUserRoleResponse]

    @classmethod
    def prepare_response(cls, group_users):
        return cls(
            group=group_users[0]["group"],
            users_role=[
                PayloadUserRoleResponse(
                    user=group_user["user"], role=group_user["role"]
                )
                for group_user in group_users
            ],
        )


class PayloadGroupsUsersRoleResponse(ConfigModel):
    payload: list[PayloadGroupUsersRoleResponse]


class PayloadRolePermissionsResponse(ConfigModel):
    payload: list[PayloadRolePermissionsWrapper]


class PayloadRolesPermissionResponse(ConfigModel):
    payload: list[PayloadRolesPermissionWrapper]


class GroupInviteResponse(BaseGroupIdWrapper):
    token: str


class InvitesGroupsResponse(ConfigModel):
    invites: list[GroupInviteResponse]


class BypassedInvitesGroupsResponse(ConfigModel):
    bypassed_invites: list[EmailStr]


class BaseRoleResponse(BaseRole):
    pass


class GroupRolesResponse(ConfigModel):
    roles: list[BaseRoleResponse]


class QRCodeInviteGroupResponse(ConfigModel):
    group: BaseGroupIdWrapper
    token: str


class BaseUserSearchResponse(BaseUser):
    pass


class BaseUsersSearchResponse(ConfigModel):
    users: list[BaseUserSearchResponse]


class RolePermissionsResponse(ConfigModel):
    role: str
    permissions: list[str]


class RolesPermissionsResponse(ConfigModel):
    roles_permissions: list[RolePermissionsResponse]


class QRCodeClockEntryResponse(ConfigModel):
    token: str
    group: BaseGroupIdWrapper


class StartClockSessionResponse(ConfigModel):
    user: BaseUser
    group: BaseGroupIdWrapper
    id: int
    start_at: datetime
    stop_at: datetime


class ScheduleClockSessionResponse(ConfigModel):
    id: int
    user: BaseUser
    group: BaseGroupIdWrapper
    start_at: time
    stop_at: time
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool


class SessionEntryResponse(ConfigModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    groups_id: int
    groups_name: str
    clock_sessions_id: int
    clock_at: datetime | None
    type: ClockEntryType | None
    start_at: datetime
    stop_at: datetime


class SessionEntriesResponse(ConfigModel):
    details: SessionEntryResponse
    entries: list[SessionEntryResponse]


class SessionsReportResponse(ConfigModel):
    sessions: list[SessionEntriesResponse]


class SessionSmartEntryResponse(ConfigModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    groups_id: int
    groups_name: str
    clock_in: datetime
    clock_out: datetime


class SessionSmartEntriesResponse(ConfigModel):
    details: SessionEntryResponse
    smart_entries: list[SessionSmartEntryResponse]


class SessionsSmartReportResponse(ConfigModel):
    sessions: list[SessionSmartEntriesResponse]

    @classmethod
    def prepare_response(cls, sessions):
        for session in sessions:
            in_out = {}
            session.update({"smart_entries": []})
            for entry in session["entries"]:
                if not in_out.get(entry["username"]):
                    in_out.update({entry["username"]: []})

                in_out[entry["username"]].append(entry)

            for k, v in in_out.items():
                if len(v) == 1:
                    out = dict(v[0])
                    out.update(
                        {
                            "type": ClockEntryType.clock_out.value,
                            "clock_at": out["stop_at"],
                        }
                    )
                    v.append(out)

                session["smart_entries"].append(
                    {
                        "username": v[0]["username"],
                        "email": v[0]["email"],
                        "first_name": v[0]["first_name"],
                        "last_name": v[0]["last_name"],
                        "groups_id": v[0]["groups_id"],
                        "groups_name": v[0]["groups_name"],
                        "clock_in": v[0]["clock_at"],
                        "clock_out": v[1]["clock_at"],
                    }
                )
                del session["entries"]

        return SessionsSmartReportResponse(
            sessions=[
                SessionSmartEntriesResponse(
                    details=SessionEntryResponse(**session["details"]),
                    smart_entries=[
                        SessionSmartEntryResponse(**smart_entry)
                        for smart_entry in session["smart_entries"]
                    ],
                )
                for session in sessions
            ]
        )


class GroupSessionResponse(ConfigModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    groups_id: int
    groups_name: str
    clock_sessions_id: int
    start_at: datetime
    stop_at: datetime


class GroupSessionsResponse(ConfigModel):
    sessions: list[GroupSessionResponse]
