from datetime import datetime
from typing import Mapping

from databases import Database
from pymysql import Error as MySQLError
from pypika import MySQLQuery, Parameter, Table

from app.exceptions import base as base_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseClockSchedule(ConfigModel):
    groups_users_id: int
    start_at: datetime
    stop_at: datetime
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False


class DBClockSchedule(DBCoreModel, BaseClockSchedule):
    class Meta:
        table_name: str = "clock_schedules"

    @classmethod
    async def filter(
        cls,
        mysql_driver: Database,
        filters: dict,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list["DBClockSchedule"]:
        clock_schedules: Table = Table(cls.Meta.table_name)

        query = MySQLQuery.from_(clock_schedules).select("*")

        values = {}
        if filters.get("day"):
            query = query.where(getattr(clock_schedules, filters["day"]))

        if filters.get("past"):
            query = query.where(clock_schedules.stop_at < Parameter(":stop_at"))
            values["stop_at"] = filters["past"]

        if filters.get("future"):
            query = query.where(clock_schedules.start_at > Parameter(":start_at"))
            values["start_at"] = filters["future"]

        try:
            results: list[Mapping] = await mysql_driver.fetch_all(
                query.get_sql(), values
            )

        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

        if not results:
            if bypass_exc:
                return []
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return results
