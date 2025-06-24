import mysql.connector
import os

class DatabaseConnection():
    """handle opening and closing database connections automatically"""
    def __init__(self, db_host, db_user, db_password, db_name):
        print("Initializing DatabaseConnection")
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        
        print(f"DEBUG: Connecting with:")
        print(f"DEBUG: Host: {self.db_host}")
        print(f"DEBUG: User: {self.db_user}")
        print(f"DEBUG: Password: {'*' * len(self.db_password) if self.db_password else 'None/Empty'}")
        print(f"DEBUG: Database: {self.db_name}")
        print("_" * 20)

        try:
            self.conn = mysql.connector.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
            )
            return self.conn
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL server: {err}")
            return None
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.conn is not None:
            self.conn.close()


with DatabaseConnection(os.environ.get("MY_DB_HOST"), os.environ.get("MY_DB_USER"), os.environ.get("MY_DB_PASSWORD"), os.environ.get("MY_DB_NAME")) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users") 
    print(cursor.fetchall())

