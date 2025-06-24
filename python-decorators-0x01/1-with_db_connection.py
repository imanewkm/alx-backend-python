import sqlite3 
import functools

def with_db_connection(func):
    """automatically handles opening and closing database connections"""
    @functools.wraps(func)
    def wrapper_with_db_connection(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            kwargs['conn'] = conn
            return func(*args, **kwargs)
        except Exception as e:
            raise(e)
        finally:
            conn.close() 
    return wrapper_with_db_connection

@with_db_connection 
def get_user_by_id(conn, user_id): 
    cursor = conn.cursor() 
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)) 
    return cursor.fetchone() 

#### Fetch user by ID with automatic connection handling 
user = get_user_by_id(user_id=1)
print(user)