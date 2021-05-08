from datetime import datetime
from typing import List

from app.core.config import settings
from app.core.database.mongodb import get_database
from app.core.scheduler.apscheduler import get_scheduler
from app.models.enums.token_subject import TokenSubject
from app.models.token import TokenDB, TokenUpdate
from app.models.user import UserDB, UserTokenWrapper
from app.repositories.token import get_tokens_by_subject_and_lt_datetime, update_token
from app.repositories.user import delete_user, get_user_by_email

DELETE_INACTIVE_USERS_ID = "delete_inactive_users"


class Scheduler:
    @classmethod
    async def start_scheduler(cls):
        get_scheduler().add_job(
            cls._delete_inactive_users,
            "interval",
            seconds=settings.SCHEDULER_INACTIVE_USERS,
            id=DELETE_INACTIVE_USERS_ID,
        )

    @classmethod
    async def stop_scheduler(cls):
        get_scheduler().remove_all_jobs()

    @staticmethod
    async def _delete_inactive_users():
        conn = await get_database()
        tokens_db: List[TokenDB] = await get_tokens_by_subject_and_lt_datetime(
            conn,
            subject=TokenSubject.ACTIVATE,
            needle_datetime=datetime.utcnow(),
            used=False,
        )
        for token_db in tokens_db:
            user_db: UserDB = await get_user_by_email(conn, token_db.email)
            await delete_user(conn, UserTokenWrapper(**user_db.dict()))
            await update_token(conn, TokenUpdate(token=token_db.token, deleted=True))
