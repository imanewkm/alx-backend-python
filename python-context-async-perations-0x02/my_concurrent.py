import asyncio
import os
from mysql.connector.aio import connect

class ExecuteQuery():
    """handle opening and closing database connections automatically"""
    def __init__(self, db_host, db_user, db_password, db_name, query, param=None):
        print("Initializing ExecuteQuery")
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.conn = None
        self.query = query
        self.param = param

    async def __aenter__(self):
        
        print(f"DEBUG: Connecting with:")
        print(f"DEBUG: Host: {self.db_host}")
        print(f"DEBUG: User: {self.db_user}")
        print(f"DEBUG: Password: {'*' * len(self.db_password) if self.db_password else 'None/Empty'}")
        print(f"DEBUG: Database: {self.db_name}")
        print("_" * 20)

        try:
            self.conn = await connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
            )
            cursor = await self.conn.cursor()
            if self.param:
                await cursor.execute(self.query, self.param)
            else:
                await cursor.execute(self.query)
            result = await cursor.fetchall()
            await cursor.close()
            return result
                
        except connect.Error as err:
            print(f"Error executing query (\"{self.query}\", {self.param}): {err}")
            raise(err)
        
    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if self.conn is not None:
            await self.conn.close()


async def async_fetch_users():
    """fetches all users"""
    async with ExecuteQuery(
    os.environ.get("MY_DB_HOST"), 
    os.environ.get("MY_DB_USER"), 
    os.environ.get("MY_DB_PASSWORD"), 
    os.environ.get("MY_DB_NAME"),
    "SELECT * FROM user_data"
    ) as result:
        print(result)

async def async_fetch_older_users():
    """fetches users older than 40"""
    async with ExecuteQuery(
    os.environ.get("MY_DB_HOST"), 
    os.environ.get("MY_DB_USER"), 
    os.environ.get("MY_DB_PASSWORD"), 
    os.environ.get("MY_DB_NAME"),
    "SELECT * FROM user_data WHERE age > %s",
    (40,)
    ) as result:
        print(result)

async def fetch_concurrently():
    await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
asyncio.run(fetch_concurrently())