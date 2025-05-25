import sqlite3
import functools

def with_db_connection(func):
    """
    Decorator that opens a database connection, passes it to the function,
    and ensures the connection is closed afterward.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        connection = sqlite3.connect('database.db')  # You can change the database name
        try:
            # Call the original function with connection as first argument
            return func(connection, *args, **kwargs)
        finally:
            # Ensure connection is closed even if an exception occurs
            connection.close()
    return wrapper

@with_db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# Fetch user by ID with automatic connection handling
user = get_user_by_id(user_id=1)
print(user)
