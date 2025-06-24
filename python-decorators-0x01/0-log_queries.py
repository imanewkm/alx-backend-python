import sqlite3
import functools
from datetime import datetime

#### decorator to log SQL queries

def log_queries(func):
    def wrapper_log_queries(*args, **kwargs):
       current_time = datetime.now()
       print(f"{current_time.strftime("%H:%M:%S")}: Executing query: '{kwargs['query']}'")
       print(f"Results: {func(*args, **kwargs)}")
    return wrapper_log_queries

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")