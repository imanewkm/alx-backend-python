import asyncio
import aiosqlite

#!/usr/bin/env python3
"""
Concurrent database operations using asyncio.gather
"""


async def async_fetch_users():
    """
    Fetches all users from the database asynchronously.
    
    Returns:
        list: A list of user records
    """
    async with aiosqlite.connect('users.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users') as cursor:
            return await cursor.fetchall()


async def async_fetch_older_users():
    """
    Fetches users older than 40 from the database asynchronously.
    
    Returns:
        list: A list of user records where age > 40
    """
    async with aiosqlite.connect('users.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE age > 40') as cursor:
            return await cursor.fetchall()


async def fetch_concurrently():
    """
    Runs both database queries concurrently using asyncio.gather.
    
    Returns:
        tuple: A tuple containing the results of both queries
    """
    results = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
    all_users, older_users = results
    
    print(f"Total users: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}")
    
    return results


if __name__ == "__main__":
    # Run the concurrent fetch operation
    asyncio.run(fetch_concurrently())