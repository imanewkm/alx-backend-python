import sqlite3
import functools
from datetime import datetime

def log_queries(func):
    """
    Decorator that logs the SQL query before executing it.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The wrapper function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from args or kwargs
        query = kwargs.get('query')
        if query is None and args:
            # Try to find a string argument that looks like a query
            for arg in args:
                if isinstance(arg, str) and ('SELECT' in arg.upper() or 
                                            'INSERT' in arg.upper() or 
                                            'UPDATE' in arg.upper() or 
                                            'DELETE' in arg.upper()):
                    query = arg
                    break
        
        # Add timestamp to the log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if query:
            print(f"[{timestamp}] Executing query: {query}")
        else:
            print(f"[{timestamp}] Executing a query (could not determine the query string)")
            
        return func(*args, **kwargs)
    
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

# fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")