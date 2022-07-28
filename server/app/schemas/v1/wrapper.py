from app.models.config_model import ConfigModel
from app.models.group import DBGroup
from app.models.group_user import DBGroupUser
from app.models.role import DBRole
from app.models.user import UserToken


class UserInGroupWrapper(ConfigModel):
    user_token: UserToken
    group: DBGroup
    group_user: DBGroupUser


class UserInGroupWithRoleAssignWrapper(UserInGroupWrapper):
    role_assign: DBRole
