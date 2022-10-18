from typing import Mapping

from databases import Database
from pypika import MySQLQuery, Order, Parameter, Table

from app.exceptions import base as base_exceptions
from app.models.config_model import ConfigModel
from app.models.db_core_model import DBCoreModel


class BaseClockGroupUserSessionEntry(ConfigModel):
    groups_users_id: int
    clock_entries_id: int | None = None
    clock_sessions_id: int | None = None


class DBClockGroupUserSessionEntry(DBCoreModel, BaseClockGroupUserSessionEntry):
    class Meta:
        table_name: str = "clock_groups_users_sessions_entries"

    @classmethod
    async def filter(
        cls,
        mysql_driver: Database,
        groups_id: int,
        filters: dict,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[Mapping]:
        clock_groups_users_entries: Table = Table(cls.Meta.table_name)
        clock_entries: Table = Table("clock_entries")
        groups_users: Table = Table("groups_users")
        users: Table = Table("users")

        query = (
            MySQLQuery.from_(clock_groups_users_entries)
            .select(
                users.id,
                users.username,
                users.email,
                users.first_name,
                users.second_name,
                users.last_name,
                users.is_active,
                clock_entries.type,
                clock_entries.datetime.as_("entry_datetime"),
            )
            .join(clock_entries)
            .on(clock_groups_users_entries.clock_entries_id == clock_entries.id)
            .join(groups_users)
            .on(clock_groups_users_entries.groups_users_id == groups_users.id)
            .join(users)
            .on(groups_users.users_id == users.id)
            .where(groups_users.groups_id == Parameter(":groups_id"))
            .orderby(clock_entries.datetime, order=Order.asc)
            .orderby(users.id, order=Order.asc)
        )

        values = {"groups_id": groups_id}

        if filters.get("users_id"):
            query = query.where(groups_users.users_id.isin(Parameter(":users_id")))
            values.update({"users_id": filters.get("users_id")})
        if filters.get("start"):
            query = query.where(clock_entries.datetime >= Parameter(":start"))
            values.update({"start": filters.get("start")})
        if filters.get("end"):
            query = query.where(clock_entries.datetime <= Parameter(":end"))
            values.update({"end": filters.get("end")})

        results: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)

        if not results:
            if bypass_exc:
                return []
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return results
