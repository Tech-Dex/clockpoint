from datetime import datetime
from typing import Mapping, Optional

from databases import Database
from pydantic import BaseModel
from pypika import MySQLQuery, Parameter, Table
from starlette.exceptions import HTTPException as StarletteHTTPException


class DBCoreModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = datetime.utcnow()
    updated_at: Optional[datetime] = datetime.utcnow()
    deleted_at: Optional[datetime] = None

    @classmethod
    async def get_by_reflection(
        cls,
        mysql_driver: Database,
        column_reflection_name: str,
        reflection_value: str | int,
        exception_detail: Optional[str] = None,
    ) -> Optional[any]:
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
