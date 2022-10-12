from __future__ import annotations

from datetime import datetime

from pydantic.networks import EmailStr

from app.models.config_model import ConfigModel
from app.models.enums.clock_entry_type import ClockEntryType
from app.models.group import BaseGroup
from app.models.permission import BasePermission, BasePermissionResponse
from app.models.role import BaseRole, BaseRoleResponse
from app.models.user import BaseUser, UserId


class GenericResponse(ConfigModel):
    message: str


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


class ClockEntryWrapper(ConfigModel):
    user: UserId
    entry_datetime: datetime
    type: str


class ClockEntriesReportResponse(ConfigModel):
    group: BaseGroupIdWrapper
    clock_entries: list[ClockEntryWrapper]


class ClockEntriesSmartReportStartStopWrapper(ConfigModel):
    user: UserId
    entry_datetime: datetime
    type: str


class ClockEntriesSmartResponseEntriesWrapper(ConfigModel):
    entry_datetime: datetime
    type: str


class ClockEntriesSmartReportUserEntriesWrapper(ConfigModel):
    user: UserId
    entries: list[ClockEntriesSmartResponseEntriesWrapper]


class ClockEntriesSmartReportResponse(ConfigModel):
    start: ClockEntriesSmartReportStartStopWrapper
    stop: ClockEntriesSmartReportStartStopWrapper
    clock_users_entries: list[ClockEntriesSmartReportUserEntriesWrapper]

    @classmethod
    def prepare_response(cls, entries_report) -> ClockEntriesSmartReportResponse:
        smart_report = {}
        sessions = []
        is_session_open = True
        session = {"entry": []}

        # Group entries in sessions
        for clock_entry in entries_report.clock_entries:
            if is_session_open:
                if clock_entry.type == ClockEntryType.entry_start.value:
                    session.update({"start": clock_entry})
                    is_session_open = False
            else:
                if clock_entry.type == ClockEntryType.entry_stop.value:
                    session.update({"stop": clock_entry})
                    is_session_open = True
                    sessions.append(session)
                    session = {"entry": []}
                elif clock_entry.type in [
                    ClockEntryType.entry_in,
                    ClockEntryType.entry_out,
                ]:
                    session["entry"].append(clock_entry)

        # For each session, group entries by user
        for session in sessions:
            smart_report.update({"start": session["start"]})
            smart_report.update({"stop": session["stop"]})
            for entry in session["entry"]:
                if smart_report.get(entry.user.id):
                    smart_report[entry.user.id]["entries"].append(
                        {"type": entry.type, "entry_datetime": entry.entry_datetime}
                    )
                else:
                    smart_report[entry.user.id] = {
                        "user": entry.user,
                        "entries": [
                            {"type": entry.type, "entry_datetime": entry.entry_datetime}
                        ],
                    }

        # Check if a user forgot to clock out.
        # Also check if in the response from db we have an out without an in, this is handled by an exception.
        users_entries = []
        for k, v in smart_report.items():
            if k not in ["start", "stop"]:
                in_count = out_count = 0
                for entry in v["entries"]:
                    if entry["type"] == ClockEntryType.entry_in.value:
                        in_count += 1
                    elif entry["type"] == ClockEntryType.entry_out.value:
                        out_count += 1
                if in_count > out_count:
                    v["entries"].append(
                        {
                            "type": ClockEntryType.entry_out.value,
                            "entry_datetime": smart_report["stop"].entry_datetime,
                        }
                    )
                elif in_count < out_count:
                    v["entries"].insert(
                        0,
                        {
                            "type": ClockEntryType.entry_in.value,
                            "entry_datetime": smart_report["start"].entry_datetime,
                        },
                    )
                users_entries.append(v)

        return cls(
            start=ClockEntriesSmartReportStartStopWrapper(
                **smart_report["start"].dict()
            ),
            stop=ClockEntriesSmartReportStartStopWrapper(**smart_report["stop"].dict()),
            clock_users_entries=(
                ClockEntriesSmartReportUserEntriesWrapper(
                    user=UserId(**user_entry["user"].dict()),
                    entries=[
                        ClockEntriesSmartResponseEntriesWrapper(**entry)
                        for entry in user_entry["entries"]
                    ],
                )
                for user_entry in users_entries
            ),
        )
