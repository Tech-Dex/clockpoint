import logging
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
        if result:
            return cls(**result)

        raise StarletteHTTPException(status_code=404, detail=exception_detail)

    async def save(self, mysql_driver: Database) -> ["DBCoreModel", None]:
        async with mysql_driver.transaction():
            table: Table = Table(self.Meta.table_name)
            logging.warning(vars(self))
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
                        detail="Group already exists",
                    )
            except MySQLError as mySQLError:
                raise StarletteHTTPException(
                    status_code=500,
                    detail=f"MySQL error: {mySQLError.args[1]}",
                )
