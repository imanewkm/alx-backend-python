import sqlite3
from typing import List, Tuple, Any

#!/usr/bin/env python3
"""
Module for a context manager that executes a query
"""


class ExecuteQuery:
    """
    A context manager for executing SQL queries.
    """

    def __init__(self, query: str, params=None):
        """
        Initialize the ExecuteQuery context manager.

        Args:
            query: The SQL query to execute
            params: Parameters to use with the query
        """
        self.query = query
        self.params = params if params is not None else []
        self.connection = None
        self.cursor = None
        self.result = None

    def __enter__(self):
        """
        Set up the database connection and execute the query.
        Returns the query result.
        """
        self.connection = sqlite3.connect(":memory:")  # In-memory database for demo
        self.cursor = self.connection.cursor()
        
        # For demo purposes, create a users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        """)
        
        # Insert some sample data
        sample_data = [
            (1, "Alice", 22),
            (2, "Bob", 30),
            (3, "Charlie", 28),
            (4, "David", 20)
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO users VALUES (?, ?, ?)", 
            sample_data
        )
        
        # Execute the actual query
        self.cursor.execute(self.query, self.params)
        self.result = self.cursor.fetchall()
        
        return self.result

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources.
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        return False  # Don't suppress exceptions
