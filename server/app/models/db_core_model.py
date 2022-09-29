from __future__ import annotations

from datetime import datetime
from typing import Mapping

from databases import Database
from pydantic import BaseModel
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import Field, MySQLQuery, Parameter, Table

from app.exceptions import base as base_exceptions


class DBCoreModel(BaseModel):
    id: int | None = None
    created_at: datetime | None = datetime.utcnow()
    updated_at: datetime | None = datetime.utcnow()
    deleted_at: datetime | None = None

    @classmethod
    async def get_all(
        cls,
        mysql_driver: Database,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[DBCoreModel]:
        table: Table = Table(cls.Meta.table_name)
        query = MySQLQuery.from_(table).select("*").where(table.deleted_at.isnull())

        results: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())

        if not results:
            if bypass_exc:
                return []
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return [cls(**result) for result in results]

    @classmethod
    async def get_by(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_value: str | int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> DBCoreModel | None:
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

        return cls(**result)

    @classmethod
    async def get_all_in(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_values: list[str] | list[int],
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[DBCoreModel]:
        table: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(table)
            .select("*")
            .where(
                getattr(table, column_reflection_name).isin(
                    Parameter(f":{column_reflection_name}")
                )
            )
            .where(table.deleted_at.isnull())
        )

        values = {column_reflection_name: reflection_values}

        results: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)
        if not results:
            if bypass_exc:
                return []
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return [cls(**result) for result in results]

    @classmethod
    async def like(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_value: str | int,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> list[DBCoreModel]:
        table: Table = Table(cls.Meta.table_name)
        query = (
            MySQLQuery.from_(table)
            .select("*")
            .where(
                getattr(table, column_reflection_name).like(
                    Parameter(f":{column_reflection_name}")
                )
            )
        )

        values = {column_reflection_name: reflection_value}

        results: list[Mapping] = await mysql_driver.fetch_all(query.get_sql(), values)

        if not results:
            if bypass_exc:
                return []
            raise exc or base_exceptions.UnprocessableEntityException(
                detail=f"No {cls.Meta.table_name} found"
            )

        return [cls(**result) for result in results]

    async def save(
        self,
        mysql_driver: Database,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
    ) -> DBCoreModel | None:
        async with mysql_driver.transaction():
            table: Table = Table(self.Meta.table_name)
            filled_keys: list[str] = [
                key for key, value in self.dict().items() if value is not None
            ]
            values: dict = {key: getattr(self, key) for key in filled_keys}
            reflection_columns: list[Field] = [
                getattr(table, key) for key in filled_keys
            ]
            reflection_parameters: list[Parameter] = [
                Parameter(f":{key}") for key in filled_keys
            ]

            query = (
                MySQLQuery.into(table)
                .columns(reflection_columns)
                .insert(reflection_parameters)
            )

            try:
                row_id: int = await mysql_driver.execute(query.get_sql(), values)
                self.id = row_id
                return self
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    if bypass_exc:
                        return None
                    raise exc or base_exceptions.DuplicateResourceException(detail=msg)
            except MySQLError as mySQLError:
                print("here")
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

    async def update(
        self,
        mysql_driver: Database,
        bypass_exc: bool = False,
        exc: base_exceptions.CustomBaseException | None = None,
        **kwargs,
    ) -> DBCoreModel | None:
        async with mysql_driver.transaction():
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.updated_at = datetime.utcnow()

            table: Table = Table(self.Meta.table_name)
            filled_keys: list[str] = [
                key
                for key, value in self.dict().items()
                if value is not None or key == "id"
            ]
            values: dict = {key: getattr(self, key) for key in filled_keys}

            query = (
                MySQLQuery.update(table)
                .where(table.id == Parameter(f":id"))
                .where(table.deleted_at.isnull())
            )

            for key in filled_keys:
                query = query.set(getattr(table, key), Parameter(f":{key}"))

            try:
                await mysql_driver.execute(query.get_sql(), values)
                return self
            except IntegrityError as ignoredException:
                code, msg = ignoredException.args
                if code == DUP_ENTRY:
                    if bypass_exc:
                        return None
                    raise exc or base_exceptions.DuplicateResourceException(detail=msg)
            except MySQLError as mySQLError:
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

    async def soft_delete(self, mysql_driver: Database) -> DBCoreModel | None:
        async with mysql_driver.transaction():
            table: Table = Table(self.Meta.table_name)
            query = (
                MySQLQuery.update(table)
                .where(table.id == Parameter(f":id"))
                .where(table.deleted_at.isnull())
                .set(table.deleted_at, Parameter(f":deleted_at"))
            )
            values = {
                "id": self.id,
                "deleted_at": datetime.utcnow(),
            }

            try:
                await mysql_driver.execute(query.get_sql(), values)
                return self
            except MySQLError as mySQLError:
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])

    async def delete(self, mysql_driver: Database) -> DBCoreModel | None:
        async with mysql_driver.transaction():
            table: Table = Table(self.Meta.table_name)
            query = (
                MySQLQuery.from_(table).delete().where(table.id == Parameter(f":id"))
            )

            values = {
                "id": self.id,
            }

            try:
                await mysql_driver.execute(query.get_sql(), values)
                return self
            except MySQLError as mySQLError:
                raise base_exceptions.CustomBaseException(detail=mySQLError.args[1])
