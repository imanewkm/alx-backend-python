import sqlite3
from typing import List, Tuple

#!/usr/bin/env python3
"""
Context manager for handling database connections
"""


class DatabaseConnection:
    """
    A context manager for database connections
    """

    def __init__(self, db_name: str = "example.db"):
        """Initialize with database name"""
        self.db_name = db_name
        self.connection = None

    def __enter__(self):
        """
        Open database connection when entering context
        Returns the connection cursor
        """
        self.connection = sqlite3.connect(self.db_name)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close database connection when exiting context
        """
        if self.connection:
            if exc_type is None:
                # No exception occurred, commit changes
                self.connection.commit()
            else:
                # Exception occurred, rollback changes
                self.connection.rollback()
            self.connection.close()
        # Return False to allow any exceptions to be propagated
        return False


if __name__ == "__main__":
    # Example usage
    # First create a table and insert some data for demonstration
    with DatabaseConnection() as cursor:
        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
        ''')
        
        # Insert sample data
        cursor.execute("DELETE FROM users")  # Clear existing data
        users_data = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
            (3, "Charlie", "charlie@example.com")
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", users_data)
    
    # Now use the context manager to query and print data
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        print("Query results:")
        for row in results:
            print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")