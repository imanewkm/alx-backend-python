import sqlite3 
import functools
from typing import Callable, Any

def with_db_connection(func: Callable) -> Callable:
    """
    Decorator that provides a database connection to the wrapped function.
    Automatically opens and closes the connection.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create connection to database
        conn = sqlite3.connect('example.db')
        
        try:
            # Call the original function with connection as first argument
            return func(conn, *args, **kwargs)
        finally:
            # Ensure connection is closed regardless of success or failure
            conn.close()
    
    return wrapper

def transactional(func: Callable) -> Callable:
    """
    Decorator that wraps a function in a database transaction.
    Commits if the function completes successfully or rolls back if an exception occurs.
    """
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            # Execute the function
            result = func(conn, *args, **kwargs)
            
            # If successful, commit the transaction
            conn.commit()
            
            return result
        except Exception as e:
            # If an error occurs, roll back the transaction
            conn.rollback()
            raise e  # Re-raise the exception after rollback
    
    return wrapper

@with_db_connection 
@transactional 
def update_user_email(conn, user_id, new_email): 
    cursor = conn.cursor() 
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id)) 
    # Update user's email with automatic transaction handling 

update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')
