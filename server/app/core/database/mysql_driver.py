from databases import Database


class MySQLDriver:
    server: Database = None


mysql_driver: MySQLDriver = MySQLDriver()


async def get_mysql_driver() -> Database:
    return mysql_driver.server


def create_batch_insert_query(table_name: str, columns: list, values: list) -> str:
    s_columns = ", ".join(columns)
    s_values = "(" + "), (".join(map(str, values)) + ")"
    query = f"INSERT INTO {table_name} ({s_columns}) VALUES {s_values}"
    return query
