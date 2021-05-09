from typing import Any, List, Optional

from pydantic.networks import EmailStr

from app.models.dbmodel import DBModel
from app.models.enums.group_role import GroupRole
from app.models.rwmodel import RWModel
from app.models.user import UserBase


class GroupBase(RWModel):
    name: str
    details: str
    owner: UserBase = None
    co_owners: List[UserBase] = []
    members: List[UserBase] = []


class GroupDB(DBModel, GroupBase):
    check_ins: List[Any] = []

    def add_co_owner(self, user: UserBase):
        if not self.user_is_co_owner(user):
            if self.user_is_member(user):
                self.remove_member(user)
            self.co_owners.append(user)

    def remove_co_owner(self, user: UserBase):
        if self.user_is_co_owner(user):
            self.co_owners.remove(user)

    def add_member(self, user: UserBase):
        if (
            not self.user_is_member(self)
            and not self.user_is_co_owner(user)
            and not self.user_is_owner(user)
        ):
            self.members.append(user)

    def remove_member(self, user: UserBase):
        if self.user_is_member(self):
            self.co_owners.remove(user)

    def user_in_group(self, user: UserBase):
        if self.user_is_owner(user):
            return True
        if self.user_is_co_owner(user):
            return True
        if self.user_is_member(user):
            return True

        return False

    def user_is_owner(self, user: UserBase):
        if self.owner == user:
            return True

        return False

    def user_is_co_owner(self, user: UserBase):
        return False

    def user_is_member(self, user: UserBase):
        return False


class GroupIdWrapper(GroupBase):
    id: Optional[str]


class GroupResponse(RWModel):
    group: GroupIdWrapper


class GroupsResponse(RWModel):
    groups: List[GroupIdWrapper]


class GroupCreate(RWModel):
    name: str
    details: str


class GroupUpdate(RWModel):
    name: Optional[str]
    details: Optional[str]
    co_owner: Optional[UserBase]
    member: UserBase


class GroupCheckIn(RWModel):
    check_in: Any


class GroupInvite(RWModel):
    group_id: str
    email: EmailStr
    role: GroupRole
