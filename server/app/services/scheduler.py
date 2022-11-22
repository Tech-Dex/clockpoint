import logging
from datetime import datetime

from databases import Database

from app.core.database.mysql_driver import get_mysql_driver
from app.models.clock_schedule import DBClockSchedule


async def start_clock_session() -> None:
    logging.info("Start all clock sessions that are not started")
    mysql_driver: Database = await get_mysql_driver()
    now: datetime = datetime.utcnow()

    filters = {"day": now.strftime("%A").lower(), "future": now}
    schedules: list[DBClockSchedule] = await DBClockSchedule.filter(
        mysql_driver, filters, bypass_exc=True
    )

    logging.info(f"Found {len(schedules)} schedules to start")
