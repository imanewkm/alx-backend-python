import time
import sqlite3 
import functools


query_cache = {}

def with_db_connection(func):
    """automatically handles opening and closing database connections"""
    @functools.wraps(func) 
    def wrapper_with_db_connection(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            kwargs['conn'] = conn
            result = func(*args, **kwargs)
            return result
        finally:
            conn.close() 

    return wrapper_with_db_connection

def cache_query(func):
    """caches the results of a database queries inorder to avoid redundant calls"""
    @functools.wraps(func) 
    def wrapper_cache_query(*args, **kwargs):
        query = kwargs['query']

        if query in query_cache:
            return query_cache[query]
        
        else:
            result = func(*args, **kwargs)
            query_cache[query] = result
            return result

    return wrapper_cache_query

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")
print(users)
#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")
print(users_again)