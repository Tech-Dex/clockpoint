from databases import Database


class MySQLDriver:
    client: Database = None


mysql_driver: MySQLDriver = MySQLDriver()


async def get_mysql_driver() -> Database:
    return mysql_driver.client
