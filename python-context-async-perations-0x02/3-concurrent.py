import asyncio
import aiosqlite

class ExecuteQuery():
    """connects to sqlite and executes a query"""
    def __init__(self, db_name, query, param=None):
        print("Initializing ExecuteQuery")
        self.db_name = db_name
        self.query = query
        self.param = param
        self.conn = None

    async def __aenter__(self):
        print(f"DEBUG: Connecting with:")
        print(f"DEBUG: Database: {self.db_name}")
        print("_" * 20)

        try:
            self.conn = await aiosqlite.connect(self.db_name)
            cursor = await self.conn.cursor()
            if self.param:
                await cursor.execute(self.query, self.param)
            else:
                await cursor.execute(self.query)
            result = await cursor.fetchall()
            await cursor.close()
            return result
                
        except Exception as err:
            print(f"Error executing query (\"{self.query}\", {self.param}): {err}")
            raise(err)
        
    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if self.conn is not None:
            await self.conn.close()


async def async_fetch_users():
    """fetches all users"""
    async with ExecuteQuery(
    "users.db",
    "SELECT * FROM user_data"
    ) as result:
        print(result)

async def async_fetch_older_users():
    """fetches users older than 40"""
    async with ExecuteQuery(
    "users.db",
    "SELECT * FROM user_data WHERE age > ?",
    (40,)
    ) as result:
        print(result)

async def fetch_concurrently():
    await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
asyncio.run(fetch_concurrently())