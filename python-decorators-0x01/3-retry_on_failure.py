import time
import sqlite3 
import functools

def with_db_connection(func):
    """automatically handles opening and closing database connections"""
    @functools.wraps(func) 
    def wrapper_with_db_connection(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            kwargs['conn'] = conn
            result = func(*args, **kwargs)
            conn.close() 
            return result
        except Exception as e:
            raise(e)

    return wrapper_with_db_connection

def retry_on_failure(retries=3, delay=2):
    """retries database operations if they fail due to transient errors"""
    def decorator_retry_on_failure(func):
        @functools.wraps(func)
        def wrapper_retry_on_failure(*args, **kwargs):
            tries = 0
            while tries < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(e)
                    tries += 1
                    time.sleep(delay)
                
        return wrapper_retry_on_failure
    return decorator_retry_on_failure

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

#### attempt to fetch users with automatic retry on failure
users = fetch_users_with_retry()
print(users)