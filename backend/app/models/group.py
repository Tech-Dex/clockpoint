from typing import Any, List, Optional

from app.models.dbmodel import DBModel
from app.models.rwmodel import RWModel
from app.models.user import UserBase


# TODO: Create Check In entity
class GroupBase(RWModel):
    name: str
    details: str
    owner: UserBase
    co_owners: List[UserBase] = []
    members: List[UserBase] = []


class GroupDB(DBModel, GroupBase):
    check_ins: List[Any] = []

    def add_co_owner(self, user: UserBase):
        # TODO: Check if user already added as co_owner
        self.co_owners.append(user)

    def remove_co_owner(self, user: UserBase):
        self.co_owners.remove(user)

    def add_member(self, user: UserBase):
        # TODO: Check if user already added as member
        self.members.append(user)

    def remove_member(self, user: UserBase):
        self.co_owners.remove(user)

    def user_in_group(self, user: UserBase):
        ...


class GroupIdWrapper(GroupBase):
    id: Optional[str]


class GroupResponse(RWModel):
    group: GroupIdWrapper


class GroupCreate(RWModel):
    name: str
    details: str
    owner: UserBase


class GroupUpdate(RWModel):
    name: Optional[str]
    details: Optional[str]
    co_owner: Optional[UserBase]
    member: UserBase


class GroupCheckIn(RWModel):
    check_in: Any
