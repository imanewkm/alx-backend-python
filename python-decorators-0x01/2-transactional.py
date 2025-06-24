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

def transactional(func):
    """ensures a function running a database operation is wrapped inside a transaction"""
    @functools.wraps(func)
    def wrapper_transactional(*args, **kwargs):
        conn = kwargs['conn']
        try:
            conn.isolation_level = None
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise(e)

    return wrapper_transactional

@with_db_connection 
@transactional 
def update_user_email(conn, user_id, new_email): 
    cursor = conn.cursor() 
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id)) 

#### Update user's email with automatic transaction handling 
update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')