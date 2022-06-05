from datetime import datetime
from typing import Mapping, Optional

from databases import Database
from pydantic import BaseModel
from pymysql import Error as MySQLError
from pymysql.constants.ER import DUP_ENTRY
from pymysql.err import IntegrityError
from pypika import Field, MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException


class DBCoreModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = datetime.utcnow()
    updated_at: Optional[datetime] = datetime.utcnow()
    deleted_at: Optional[datetime] = None

    @classmethod
    async def get_all(
        cls, mysql_driver: Database, exception_detail: Optional[str] = None
    ) -> list["DBCoreModel"]:
        table: Table = Table(cls.Meta.table_name)
        query = MySQLQuery.from_(table).select("*").where(table.deleted_at.isnull())

        results: list[Mapping] = await mysql_driver.fetch_all(query.get_sql())

        if not results:
            raise StarletteHTTPException(status_code=404, detail=exception_detail)

        return [cls(**result) for result in results]

    @classmethod
    async def get_by(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_value: str | int,
        exception_detail: Optional[str] = None,
    ) -> any:
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
            raise StarletteHTTPException(status_code=404, detail=exception_detail)

        return cls(**result)

    @classmethod
    async def get_all_in(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_values: list[str] | list[int],
        exception_detail: Optional[str] = None,
    ) -> any:
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
            raise StarletteHTTPException(status_code=404, detail=exception_detail)

        return [cls(**result) for result in results]

    async def save(
        self, mysql_driver: Database, exception_detail: Optional[str] = None
    ) -> ["DBCoreModel", None]:
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
                    raise StarletteHTTPException(
                        status_code=409,
                        detail=exception_detail,
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

    async def update(
        self, mysql_driver: Database, exception_detail: Optional[str] = None, **kwargs
    ) -> ["DBCoreModel", None]:
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
                    raise StarletteHTTPException(
                        status_code=409,
                        detail=exception_detail,
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

    async def soft_delete(self, mysql_driver: Database) -> ["DBCoreModel", None]:
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
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )

    async def delete(self, mysql_driver: Database) -> ["DBCoreModel", None]:
        async with mysql_driver.transaction():
            table: Table = Table(self.Meta.table_name)
            query = (
                MySQLQuery.update(table).delete().where(table.id == Parameter(f":id"))
            )

            values = {
                "id": self.id,
            }

            try:
                await mysql_driver.execute(query.get_sql(), values)
                return self
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )
