from typing import Mapping

from databases import Database
from pymysql import Error as MySQLError
from pypika import JoinType, MySQLQuery, Order, Parameter, Table

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
    async def last_clock_entry(
        cls,
        mysql_driver: Database,
        groups_users_id: int,
        clock_sessions_id: int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> Mapping | None:
        clock_groups_users_sessions_entries: Table = Table(cls.Meta.table_name)
        clock_entries: Table = Table("clock_entries")
        query = (
            MySQLQuery.from_(clock_groups_users_sessions_entries)
            .select(
                clock_groups_users_sessions_entries.groups_users_id,
                clock_groups_users_sessions_entries.clock_entries_id,
                clock_entries.clock_at,
                clock_entries.type,
            )
            .join(clock_entries)
            .on(
                clock_groups_users_sessions_entries.clock_entries_id == clock_entries.id
            )
            .where(
                clock_groups_users_sessions_entries.groups_users_id
                == Parameter(":groups_users_id")
            )
            .where(
                clock_groups_users_sessions_entries.clock_sessions_id
                == Parameter(":clock_sessions_id")
            )
            .where(clock_groups_users_sessions_entries.deleted_at.isnull())
            .orderby(clock_entries.clock_at, order=Order.desc)
            .limit(1)
        )

        values = {
            "groups_users_id": groups_users_id,
            "clock_sessions_id": clock_sessions_id,
        }
        try:
            result: Mapping = await mysql_driver.fetch_one(query.get_sql(), values)
        except MySQLError as mySQLError:
            raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

        if not result:
            if bypass_exc:
                return None
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return result

    @classmethod
    async def filter(
        cls,
        mysql_driver: Database,
        groups_id: int,
        filters: dict,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[Mapping]:
        """
        Filter entries, the start and stop are applied on sessions, not on entries.
        Returns list order by:
        clock_groups_users_sessions_entries.clock_sessions_id
        clock_sessions.start_at
        clock_entries.clock_at

        We know that entries are grouped by the first order by, so we don't need to do a check
        when we process it.
        """
        clock_groups_users_sessions_entries: Table = Table(cls.Meta.table_name)
        clock_entries: Table = Table("clock_entries")
        clock_sessions: Table = Table("clock_sessions")
        groups_users: Table = Table("groups_users")
        groups: Table = Table("groups")
        users: Table = Table("users")

        query = (
            MySQLQuery.from_(clock_groups_users_sessions_entries)
            .select(
                users.username,
                users.email,
                users.first_name,
                users.last_name,
                groups.id.as_("groups_id"),
                groups.name.as_("groups_name"),
                clock_groups_users_sessions_entries.groups_users_id,
                clock_groups_users_sessions_entries.clock_entries_id,
                clock_groups_users_sessions_entries.clock_sessions_id,
                clock_entries.clock_at,
                clock_entries.type,
                clock_sessions.start_at,
                clock_sessions.stop_at,
            )
            .join(clock_entries, JoinType.left)
            .on(
                clock_groups_users_sessions_entries.clock_entries_id == clock_entries.id
            )
            .join(clock_sessions, JoinType.left)
            .on(
                clock_groups_users_sessions_entries.clock_sessions_id
                == clock_sessions.id
            )
            .join(groups_users, JoinType.left)
            .on(clock_groups_users_sessions_entries.groups_users_id == groups_users.id)
            .join(groups, JoinType.left)
            .on(groups_users.groups_id == groups.id)
            .join(users, JoinType.left)
            .on(groups_users.users_id == users.id)
            .where(groups.id == Parameter(":groups_id"))
            .orderby(clock_groups_users_sessions_entries.clock_sessions_id)
            .orderby(clock_sessions.start_at)
            .orderby(clock_entries.clock_at)
        )

        values = {
            "groups_id": groups_id,
        }

        if filters.get("start_at"):
            query = query.where(clock_sessions.start_at >= Parameter(":start_at"))
            values["start_at"] = filters["start_at"]

        if filters.get("stop_at"):
            query = query.where(clock_sessions.stop_at <= Parameter(":stop_at"))
            values["stop_at"] = filters["stop_at"]

        if filters.get("users_ids"):
            query = query.where(users.id.isin(Parameter(":users_ids")))
            values["users_ids"] = filters["users_ids"]

        if filters.get("emails"):
            query = query.where(users.email.isin(Parameter(":emails")))
            values["emails"] = filters["emails"]

        if filters.get("only_sessions"):
            query = query.where(
                clock_groups_users_sessions_entries.clock_entries_id.isnull()
            )

        if filters.get("only_entries"):
            query = query.where(
                clock_groups_users_sessions_entries.clock_entries_id.isnotnull()
            )

        if filters.get("clock_sessions_ids"):
            query = query.where(
                clock_groups_users_sessions_entries.clock_sessions_id.isin(
                    Parameter(":clock_sessions_ids")
                )
            )
            values["clock_sessions_ids"] = filters["clock_sessions_ids"]

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
