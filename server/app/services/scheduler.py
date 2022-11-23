import logging
import math
from datetime import datetime, timedelta

import aredis_om
from databases import Database

from app.core.database.mysql_driver import get_mysql_driver
from app.models.clock_group_user_session_entry import DBClockGroupUserSessionEntry
from app.models.clock_schedule import DBClockSchedule, RedisClockSchedule
from app.models.clock_session import DBClockSession


async def start_clock_session() -> None:
    logging.info("Start all clock sessions that are not started")
    mysql_driver: Database = await get_mysql_driver()
    now: datetime = datetime.utcnow()

    filters = {"day": now.strftime("%A").lower(), "future": now.time()}
    schedules: list[DBClockSchedule] = await DBClockSchedule.filter(
        mysql_driver, filters, bypass_exc=True
    )

    logging.info(f"Found {len(schedules)} schedules")
    for schedule in schedules:
        try:
            await RedisClockSchedule.find(RedisClockSchedule.schedule_id == schedule.id).first()
            logging.info(f"Schedule {schedule.id} already started")
        except aredis_om.model.model.NotFoundError:
            logging.info(f"Schedule {schedule.id} not started yet")
            redis_schedule: RedisClockSchedule = await RedisClockSchedule(
                schedule_id=schedule.id,
            ).save()

            start_at = datetime.combine(datetime.today(), schedule.start_at)
            stop_at: datetime = datetime.combine(
                datetime.today(), schedule.stop_at
            )
            if (datetime.combine(datetime.today(), schedule.stop_at) - datetime.combine(datetime.today(), schedule.start_at)).total_seconds() < 0:
                stop_at = datetime.combine(datetime.today(), schedule.stop_at) + timedelta(days=1)

            seconds_left = math.ceil((stop_at - now).total_seconds())
            await redis_schedule.expire(seconds_left)

            db_clock_session: DBClockSession = await DBClockSession(
                start_at=start_at,
                stop_at=stop_at,
            ).save(mysql_driver)

            await DBClockGroupUserSessionEntry(
                clock_sessions_id=db_clock_session.id,
                groups_users_id=schedule.groups_users_id
            ).save(mysql_driver)

