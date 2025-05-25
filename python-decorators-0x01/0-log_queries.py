import functools

#!/usr/bin/env python3
"""
Module that provides a decorator to log database queries
"""


def log_queries(func):
    """
    Decorator that logs the SQL query executed by the wrapped function.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The wrapper function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function that logs the query before executing it
        """
        print(f"Query: {args[0]}")
        return func(*args, **kwargs)
    return wrapper