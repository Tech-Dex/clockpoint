from datetime import time
from typing import Mapping

from aredis_om import Field, HashModel, get_redis_connection
from databases import Database
from pymysql import Error as MySQLError
from pypika import MySQLQuery, Parameter, Table

from app.core.config import settings
from app.exceptions import base as base_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseClockSchedule(ConfigModel):
    groups_users_id: int
    start_at: time
    stop_at: time
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False


class RedisClockSchedule(HashModel, ConfigModel):
    schedule_id: int = Field(index=True)

    class Meta:
        global_key_prefix = "clockpoint"
        database = get_redis_connection(
            url=settings.REDIS_DATA_URL, decode_responses=True
        )


class DBClockSchedule(DBCoreModel, BaseClockSchedule):
    class Meta:
        table_name: str = "clock_schedules"

    @classmethod
    async def get_by(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_value: str | int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> "DBClockSchedule":
        table: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(table)
            .select("*")
            .where(
                getattr(table, column_reflection_name)
                == Parameter(f":{column_reflection_name}")
            )
            .where(table.deleted_at.isnull())
        )
        values = {column_reflection_name: reflection_value}

        result: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        if not result:
            if bypass_exc:
                return None
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        dict_result = dict(result)
        dict_result["start_at"] = str(result["start_at"])
        dict_result["stop_at"] = str(result["stop_at"])
        return cls(**dict_result)

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

        if filters.get("groups_users_id"):
            query = query.where(
                clock_schedules.groups_users_id == Parameter(":groups_users_id")
            )
            values["groups_users_id"] = filters["groups_users_id"]

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

        formatted_results: list[DBClockSchedule] = []
        for result in results:
            formatted_results.append(
                DBClockSchedule(
                    **{
                        **result,
                        "start_at": str(result["start_at"]),
                        "stop_at": str(result["stop_at"]),
                    }
                )
            )

        return formatted_results
