from typing import Any, List, Optional, Union

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
        user_co_owner: Union[UserBase, bool] = self.user_is_co_owner(user)
        if not user_co_owner:
            user_member: Union[UserBase, bool] = self.user_is_member(user)
            if user_member:
                self.remove_member(user_member)
            self.co_owners.append(user)

    def remove_co_owner(self, user: UserBase):
        if self.user_is_co_owner(user):
            self.co_owners.remove(user)

    def add_member(self, user: UserBase):
        user_member: Union[UserBase, bool] = self.user_is_member(user)
        user_co_owner: Union[UserBase, bool] = self.user_is_co_owner(user)
        if not user_member and not user_co_owner and not self.user_is_owner(user):
            self.members.append(user)

    def remove_member(self, user: UserBase):
        if self.user_is_member(user):
            self.members.remove(user)

    def user_in_group(self, user: UserBase) -> bool:
        if self.user_is_owner(user):
            return True
        if self.user_is_co_owner(user):
            return True
        if self.user_is_member(user):
            return True

        return False

    def remove_user(self, user: UserBase):
        self.remove_co_owner(user)
        self.remove_member(user)

    def user_is_owner(self, user: UserBase) -> bool:
        if self.owner == user:
            return True

        return False

    def user_is_co_owner(self, user: UserBase) -> Union[UserBase, bool]:
        if [co_owner for co_owner in self.co_owners if co_owner.email == user.email]:
            return True
        return False

    def user_is_member(self, user: UserBase) -> Union[UserBase, bool]:
        member: Union[UserBase, bool] = self.member_object(user)
        if member:
            return member
        return False

    def member_object(self, user: UserBase) -> Union[UserBase, bool]:
        """
        We want to be able to delete a user from the List ( self.members ) with the .remove() method
        In order to be able to do that we want to store the reference (object id) of the queried object that
        was created on List __init__
        Even if the objects user and members[0] have the same values inside, they are different object
        and we will not be able to delete from self.members and object with an different reference (id)
        :param user: user entity that was created to query based on email
        :return: Object inside self.members or False
        """
        members: List[UserBase] = [
            member for member in self.members if member.email == user.email
        ]
        if len(members) == 1:
            return members[0]
        if not members:
            return False
        return None

    def co_owners_object(self, user: UserBase) -> Union[UserBase, bool]:
        """
        We want to be able to delete a user from the List ( self.co_owners ) with the .remove() method
        In order to be able to do that we want to store the reference (object id) of the queried object that
        was created on List __init__
        Even if the objects user and co_owners[0] have the same values inside, they are different object
        and we will not be able to delete from self.co_owners and object with an different reference (id)
        :param user: user entity that was created to query based on email
        :return: Object inside self.members or False
        """
        co_owners: List[UserBase] = [
            co_owner for co_owner in self.co_owners if co_owner.email == user.email
        ]
        if len(co_owners) == 1:
            return co_owners[0]
        if not co_owners:
            return False
        return None


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
    member: Optional[UserBase]


class GroupCheckIn(RWModel):
    check_in: Any


class GroupInvite(RWModel):
    group_id: str
    email: EmailStr
    role: GroupRole


class GroupKick(RWModel):
    id: str
    email: EmailStr
